from __future__ import annotations

import csv
import re
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(value: str, fallback: str = "paper") -> str:
    stem = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("_.")
    return stem or fallback


def make_paper_id(index: int, pdf_path: Path) -> str:
    return f"paper_{index:03d}_{slugify(pdf_path.stem)}"


def write_failed(log_dir: Path, paper_id: str, file_name: str, stage: str, error: str) -> None:
    ensure_dir(log_dir)
    log_path = log_dir / "failed_papers.csv"
    is_new = not log_path.exists()
    with log_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(["paper_id", "file_name", "stage", "error"])
        writer.writerow([paper_id, file_name, stage, error])


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")

