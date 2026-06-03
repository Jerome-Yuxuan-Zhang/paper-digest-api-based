from pathlib import Path

from paper_digest.document_reader import supported_files


def test_supported_files_detects_expected_extensions(tmp_path: Path) -> None:
    for name in ["a.pdf", "b.html", "c.htm", "d.txt", "e.md", "f.docx"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    names = [path.name for path in supported_files(tmp_path)]

    assert names == ["a.pdf", "b.html", "c.htm", "d.txt", "e.md"]


def test_supported_files_ignores_generated_outputs(tmp_path: Path) -> None:
    (tmp_path / "source.pdf").write_text("x", encoding="utf-8")
    reports = tmp_path / "document_reports_md"
    reports.mkdir()
    (reports / "generated.md").write_text("x", encoding="utf-8")
    (tmp_path / "folder_summary.md").write_text("x", encoding="utf-8")

    names = [path.name for path in supported_files(tmp_path)]

    assert names == ["source.pdf"]
