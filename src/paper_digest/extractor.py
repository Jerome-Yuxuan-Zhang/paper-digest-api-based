from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from .config import Settings
from .prompts import (
    CHUNK_ANALYSIS_PROMPT,
    PAPER_ANALYSIS_SYSTEM_PROMPT,
    REDUCE_ANALYSIS_PROMPT,
    paper_prompt,
)
from .api_client import ApiClient
from .schemas import PAPER_CARD_JSON_SCHEMA, PaperCard
from .utils import write_text


def split_text_by_pages(text: str, chunk_chars: int) -> list[str]:
    blocks = text.split("\n## Page ")
    chunks: list[str] = []
    current = blocks[0]
    for block in blocks[1:]:
        page_block = "\n## Page " + block
        if len(current) + len(page_block) > chunk_chars and current.strip():
            chunks.append(current)
            current = page_block
        else:
            current += page_block
    if current.strip():
        chunks.append(current)
    return chunks


def _validate_card(raw: dict, paper_id: str, file_name: str) -> PaperCard:
    raw.setdefault("paper_id", paper_id)
    raw.setdefault("file_name", file_name)
    return PaperCard.model_validate(raw)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def _chat_json_and_validate(
    client: ApiClient,
    messages: list[dict],
    paper_id: str,
    file_name: str,
    max_tokens: int,
) -> PaperCard:
    raw = client.chat_json(messages, max_tokens=max_tokens)
    return _validate_card(raw, paper_id, file_name)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def _chat_json_notes(client: ApiClient, messages: list[dict], max_tokens: int) -> dict:
    return client.chat_json(messages, max_tokens=max_tokens)


def extract_paper_card(
    client: ApiClient,
    settings: Settings,
    parsed_markdown_path: Path,
    topic: str,
    paper_id: str | None = None,
    file_name: str | None = None,
) -> PaperCard:
    paper_text = parsed_markdown_path.read_text(encoding="utf-8")
    paper_id = paper_id or parsed_markdown_path.stem
    file_name = file_name or parsed_markdown_path.name

    if len(paper_text) <= settings.max_paper_chars:
        return _chat_json_and_validate(
            client,
            [
                {"role": "system", "content": PAPER_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": paper_prompt(topic, paper_id, file_name, paper_text)},
            ],
            paper_id,
            file_name,
            max_tokens=8192,
        )

    chunk_notes = []
    for idx, chunk in enumerate(split_text_by_pages(paper_text, settings.chunk_chars), start=1):
        note = _chat_json_notes(
            client,
            [
                {"role": "system", "content": PAPER_ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": CHUNK_ANALYSIS_PROMPT.format(
                        topic=topic,
                        paper_id=paper_id,
                        file_name=file_name,
                        chunk_text=chunk,
                    ),
                },
            ],
            max_tokens=4096,
        )
        chunk_notes.append({"chunk": idx, "notes": note})

    return _chat_json_and_validate(
        client,
        [
            {"role": "system", "content": PAPER_ANALYSIS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REDUCE_ANALYSIS_PROMPT.format(
                    schema=PAPER_CARD_JSON_SCHEMA,
                    topic=topic,
                    paper_id=paper_id,
                    file_name=file_name,
                    chunk_notes=json.dumps(chunk_notes, ensure_ascii=False),
                ),
            },
        ],
        paper_id,
        file_name,
        max_tokens=8192,
    )


def save_card(card: PaperCard, output_path: Path) -> None:
    write_text(output_path, card.model_dump_json(indent=2))


def validation_error_message(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors())
