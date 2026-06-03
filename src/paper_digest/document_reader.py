from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from .pdf_parser import extract_text_with_pymupdf


SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".html", ".htm", ".txt", ".md"}
GENERATED_DIR_NAMES = {
    "document_reports_json",
    "document_reports_md",
    "parsed_text",
    "cards_json",
    "__pycache__",
    ".pytest_cache",
}
GENERATED_FILE_NAMES = {
    "folder_summary.md",
    "synthesis_prompt.md",
    "evidence_bank.md",
}


class _HtmlTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

    def text(self) -> str:
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line)


def supported_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
        and not _is_generated_path(path)
    )


def _is_generated_path(path: Path) -> bool:
    names = {part.lower() for part in path.parts}
    return bool(names & GENERATED_DIR_NAMES) or path.name.lower() in GENERATED_FILE_NAMES


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        parsed = extract_text_with_pymupdf(path)
        lines = [f"# {path.name}", ""]
        for page_number, page_text in sorted(parsed["page_texts"].items()):
            lines.extend([f"## Page {page_number}", "", page_text or "[NO TEXT]", ""])
        return "\n".join(lines)
    if suffix in {".html", ".htm"}:
        parser = _HtmlTextParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        return f"# {path.name}\n\n{parser.text()}"
    return f"# {path.name}\n\n{path.read_text(encoding='utf-8', errors='ignore')}"
