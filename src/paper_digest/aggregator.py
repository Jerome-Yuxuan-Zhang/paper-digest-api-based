from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .schemas import PaperCard
from .utils import ensure_dir, write_text


MATRIX_COLUMNS = [
    "paper_id",
    "title",
    "authors",
    "year",
    "journal_or_source",
    "research_question",
    "core_argument",
    "data_source",
    "sample_period",
    "sample_scope",
    "methodology",
    "identification_strategy",
    "main_findings",
    "relationship_to_user_topic",
    "usable_for",
    "citation_risk",
    "citation_risk_reason",
]


def load_cards(cards_dir: Path) -> list[PaperCard]:
    cards: list[PaperCard] = []
    for path in sorted(cards_dir.glob("*.json")):
        cards.append(PaperCard.model_validate_json(path.read_text(encoding="utf-8")))
    return cards


def write_jsonl(cards: list[PaperCard], output_path: Path) -> None:
    lines = [card.model_dump_json() for card in cards]
    write_text(output_path, "\n".join(lines) + ("\n" if lines else ""))


def write_excel(cards: list[PaperCard], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    rows = []
    for card in cards:
        data = card.model_dump()
        rows.append(
            {
                column: "; ".join(data[column]) if isinstance(data.get(column), list) else data.get(column, "")
                for column in MATRIX_COLUMNS
            }
        )
    df = pd.DataFrame(rows, columns=MATRIX_COLUMNS)
    df.to_excel(output_path, index=False)


def write_evidence_bank(cards: list[PaperCard], output_path: Path) -> None:
    lines = ["# Evidence Bank", ""]
    for card in cards:
        lines.extend([f"## {card.paper_id}: {card.title}", ""])
        if not card.key_evidence:
            lines.extend(["No key evidence extracted.", ""])
            continue
        for idx, item in enumerate(card.key_evidence, start=1):
            lines.extend(
                [
                    f"### Claim {idx}",
                    f"- Claim: {item.claim}",
                    f"- Evidence: {item.evidence_text}",
                    f"- Page: {item.page}",
                    f"- How to use: {item.how_to_use}",
                    f"- Verification needed: {item.verification_needed}",
                    "",
                ]
            )
    write_text(output_path, "\n".join(lines))


def _compact_card(card: PaperCard) -> dict:
    return {
        "paper_id": card.paper_id,
        "title": card.title,
        "authors": card.authors,
        "year": card.year,
        "research_question": card.research_question,
        "core_argument": card.core_argument,
        "theoretical_framework": card.theoretical_framework,
        "data_source": card.data_source,
        "methodology": card.methodology,
        "identification_strategy": card.identification_strategy,
        "main_findings": card.main_findings,
        "limitations": card.limitations,
        "relationship_to_user_topic": card.relationship_to_user_topic,
        "usable_for": card.usable_for,
        "citation_risk": card.citation_risk,
        "key_evidence": [item.model_dump() for item in card.key_evidence],
    }


def write_synthesis_prompt(cards: list[PaperCard], output_path: Path, topic: str) -> None:
    compact_cards = json.dumps([_compact_card(card) for card in cards], ensure_ascii=False, indent=2)
    prompt = f"""# Literature Synthesis Prompt

You are an academic literature synthesis assistant. Use only the literature cards below.
Do not invent facts, citations, methods, findings, or bibliographic details outside these cards.

User research topic:
{topic}

Tasks:
1. Compare the papers horizontally across research questions, theory, data, methods, identification strategies, variables, findings, and limitations.
2. Identify research gaps.
3. Group papers by theory.
4. Group papers by method.
5. Identify evidence conflicts and explain what would need verification in the original PDFs.
6. Propose a writing framework for a literature review or thesis section.
7. Flag papers with medium or high citation risk and explain how to use them cautiously.

Literature cards:
{compact_cards}
"""
    write_text(output_path, prompt)


def aggregate_outputs(cards_dir: Path, output_dir: Path, topic: str = "") -> list[PaperCard]:
    ensure_dir(output_dir)
    cards = load_cards(cards_dir)
    write_jsonl(cards, output_dir / "literature_cards.jsonl")
    write_excel(cards, output_dir / "literature_matrix.xlsx")
    write_evidence_bank(cards, output_dir / "evidence_bank.md")
    write_synthesis_prompt(cards, output_dir / "synthesis_prompt.md", topic)
    return cards

