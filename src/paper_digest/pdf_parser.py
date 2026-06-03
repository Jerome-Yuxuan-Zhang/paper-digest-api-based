from __future__ import annotations

from pathlib import Path

import fitz
import pdfplumber

from .utils import write_text


def extract_text_with_pymupdf(pdf_path: Path) -> dict:
    page_texts: dict[int, str] = {}
    metadata: dict[str, str] = {}
    with fitz.open(pdf_path) as doc:
        metadata = {k: str(v or "") for k, v in (doc.metadata or {}).items()}
        for page_index, page in enumerate(doc, start=1):
            page_texts[page_index] = page.get_text("text").strip()
    _append_pdfplumber_tables(pdf_path, page_texts)
    return {"metadata": metadata, "page_texts": page_texts, "page_count": len(page_texts)}


def _append_pdfplumber_tables(pdf_path: Path, page_texts: dict[int, str]) -> None:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables() or []
                if not tables:
                    continue
                table_markdown = [_table_to_markdown(table) for table in tables if table]
                if table_markdown:
                    page_texts[page_index] = "\n\n".join(
                        part for part in [page_texts.get(page_index, ""), "### Extracted Tables", *table_markdown] if part
                    )
    except Exception:
        return


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [["" if cell is None else str(cell).replace("\n", " ").strip() for cell in row] for row in table]
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    separator = ["---"] * width
    body = rows[1:]
    all_rows = [header, separator, *body]
    return "\n".join("| " + " | ".join(row) + " |" for row in all_rows)


def _bad_text_ratio(text: str) -> float:
    if not text:
        return 1.0
    bad = sum(1 for char in text if char == "\ufffd" or ord(char) < 32 and char not in "\n\t\r")
    return bad / max(len(text), 1)


def detect_bad_extraction(page_texts: dict[int, str]) -> bool:
    if not page_texts:
        return True
    all_text = "\n".join(page_texts.values())
    avg_page_chars = len(all_text) / max(len(page_texts), 1)
    blank_pages = sum(1 for text in page_texts.values() if len(text.strip()) < 80)
    blank_ratio = blank_pages / max(len(page_texts), 1)
    return len(all_text.strip()) < 1200 or avg_page_chars < 450 or blank_ratio > 0.35 or _bad_text_ratio(all_text) > 0.03


def bad_page_numbers(page_texts: dict[int, str]) -> list[int]:
    return [
        page
        for page, text in page_texts.items()
        if len(text.strip()) < 120 or _bad_text_ratio(text) > 0.03
    ]


def save_parsed_markdown(
    paper_id: str,
    metadata: dict[str, str],
    page_texts: dict[int, str],
    output_path: Path,
) -> None:
    title = metadata.get("title") or paper_id
    lines = [f"# {title}", "", f"- paper_id: {paper_id}"]
    for key in ("author", "creationDate", "modDate"):
        if metadata.get(key):
            lines.append(f"- {key}: {metadata[key]}")
    lines.append("")
    for page_number in sorted(page_texts):
        lines.extend([f"## Page {page_number}", "", page_texts[page_number].strip() or "[NO TEXT]", ""])
    write_text(output_path, "\n".join(lines))
