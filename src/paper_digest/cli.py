from __future__ import annotations

import shutil
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from tqdm import tqdm

from .aggregator import aggregate_outputs
from .config import load_settings, require_api_key
from .document_reader import supported_files
from .extractor import extract_paper_card, save_card, validation_error_message
from .folder_reports import run_folder_reports
from .ocr import ocr_bad_pages
from .pdf_parser import bad_page_numbers, detect_bad_extraction, extract_text_with_pymupdf, save_parsed_markdown
from .qwen_client import QwenClient
from .utils import ensure_dir, make_paper_id, write_failed

app = typer.Typer(help="中文本地资料分析工具：批量读取 PDF、HTML、TXT、MD，并调用 Qwen 生成报告。")
console = Console()


def build_client() -> QwenClient:
    settings = load_settings()
    require_api_key(settings)
    return QwenClient(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        text_model=settings.qwen_text_model,
        ocr_model=settings.qwen_ocr_model,
        timeout=settings.api_timeout_seconds,
    )


@app.command()
def folder(
    input: Path = typer.Option(Path("input_pdfs"), "--input", help="资料文件夹，支持 pdf/html/txt/md。"),
    output: Path = typer.Option(Path("outputs"), "--output", help="输出文件夹。"),
    topic: str = typer.Option("", "--topic", help="分析主题，可为空。"),
    max_file_mb: float = typer.Option(50.0, "--max-file-mb", help="超过该大小的文件自动跳过；设为 0 表示不限制。"),
    rerun_existing: bool = typer.Option(False, "--rerun-existing", help="重新生成已经存在的单文件报告。"),
) -> None:
    """读取一个文件夹内所有支持文件，每个文件单独 API 上下文生成报告，最后自动汇总。"""
    settings = load_settings()
    require_api_key(settings)
    client = build_client()
    files = supported_files(input)
    console.print(f"找到 {len(files)} 个支持文件。")

    def progress(index: int, total: int, path: Path, status: str = "done") -> None:
        label = "已跳过" if status == "skipped" else "已存在" if status == "existing" else "已处理"
        console.print(f"[{index}/{total}] {label}：{path.name}")

    reports = run_folder_reports(
        client,
        settings,
        input,
        output,
        topic,
        progress=progress,
        max_file_mb=None if max_file_mb <= 0 else max_file_mb,
        skip_existing=not rerun_existing,
    )
    console.print(f"完成：生成 {len(reports)} 个单文件报告。")
    console.print(f"检索 JSON：{output / 'search_index.json'}")
    console.print(f"Markdown 总结：{output / 'folder_summary.md'}")


@app.command()
def parse(
    input: Path = typer.Option(Path("input_pdfs"), "--input", help="PDF 输入文件夹。"),
    output: Path = typer.Option(Path("outputs/parsed_text"), "--output", help="解析后 Markdown 输出文件夹。"),
    use_ocr: bool = typer.Option(True, "--ocr/--no-ocr", help="对低质量解析页面启用 Qwen OCR。"),
) -> None:
    ensure_dir(output)
    pdf_paths = sorted(input.glob("*.pdf"))
    if not pdf_paths:
        console.print(f"在 {input} 中没有找到 PDF 文件。")
        return

    client = build_client() if use_ocr else None
    log_dir = Path("logs")
    for idx, pdf_path in enumerate(tqdm(pdf_paths, desc="正在解析 PDF"), start=1):
        paper_id = make_paper_id(idx, pdf_path)
        try:
            parsed = extract_text_with_pymupdf(pdf_path)
            page_texts = parsed["page_texts"]
            if use_ocr and client and detect_bad_extraction(page_texts):
                pages = bad_page_numbers(page_texts) or list(page_texts)
                logger.warning("{} 文本抽取质量偏低，OCR 页码：{}", pdf_path.name, pages)
                page_texts.update(ocr_bad_pages(client, pdf_path, pages))
            save_parsed_markdown(paper_id, parsed["metadata"], page_texts, output / f"{paper_id}.md")
        except Exception as exc:
            write_failed(log_dir, paper_id, pdf_path.name, "parse", str(exc))
            logger.exception("解析失败：{}", pdf_path)


@app.command()
def extract(
    parsed: Path = typer.Option(Path("outputs/parsed_text"), "--parsed", help="解析后 Markdown 文件夹。"),
    output: Path = typer.Option(Path("outputs/cards_json"), "--output", help="PaperCard JSON 输出文件夹。"),
    topic: str = typer.Option(..., "--topic", help="你的研究主题。"),
) -> None:
    ensure_dir(output)
    settings = load_settings()
    require_api_key(settings)
    client = build_client()
    md_paths = sorted(parsed.glob("*.md"))
    if not md_paths:
        console.print(f"在 {parsed} 中没有找到解析后的 Markdown 文件。")
        return

    for path in tqdm(md_paths, desc="正在生成文献卡片"):
        paper_id = path.stem
        try:
            card = extract_paper_card(client, settings, path, topic, paper_id=paper_id, file_name=path.name)
            save_card(card, output / f"{card.paper_id}.json")
        except Exception as exc:
            message = validation_error_message(exc) if hasattr(exc, "errors") else str(exc)
            write_failed(Path("logs"), paper_id, path.name, "extract", message)
            logger.exception("生成卡片失败：{}", path)


@app.command()
def aggregate(
    cards: Path = typer.Option(Path("outputs/cards_json"), "--cards", help="PaperCard JSON 文件夹。"),
    output: Path = typer.Option(Path("outputs"), "--output", help="汇总文件输出文件夹。"),
    topic: str = typer.Option("", "--topic", help="写入 synthesis_prompt.md 的研究主题。"),
) -> None:
    result = aggregate_outputs(cards, output, topic)
    console.print(f"已汇总 {len(result)} 张文献卡片到 {output}")


@app.command()
def run(
    input: Path = typer.Option(Path("input_pdfs"), "--input", help="PDF 输入文件夹。"),
    output: Path = typer.Option(Path("outputs"), "--output", help="总输出文件夹。"),
    topic: str = typer.Option(..., "--topic", help="你的研究主题。"),
    use_ocr: bool = typer.Option(True, "--ocr/--no-ocr", help="对低质量解析页面启用 Qwen OCR。"),
) -> None:
    parsed_dir = output / "parsed_text"
    cards_dir = output / "cards_json"
    parse(input=input, output=parsed_dir, use_ocr=use_ocr)
    extract(parsed=parsed_dir, output=cards_dir, topic=topic)
    aggregate(cards=cards_dir, output=output, topic=topic)


@app.command()
def clean(
    output: Path = typer.Option(Path("outputs"), "--output", help="需要清理的输出文件夹。"),
    logs: Path = typer.Option(Path("logs"), "--logs", help="需要清理的日志文件夹。"),
) -> None:
    for path in [
        output / "parsed_text",
        output / "cards_json",
        output / "document_reports_json",
        output / "document_reports_md",
        output / "literature_cards.jsonl",
        output / "literature_matrix.xlsx",
        output / "evidence_bank.md",
        output / "synthesis_prompt.md",
        output / "search_index.json",
        output / "folder_summary.md",
        logs / "failed_papers.csv",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
            ensure_dir(path)
            (path / ".gitkeep").touch()
        elif path.exists():
            path.unlink()
    console.print("已清理生成文件。输入文件夹未被删除。")


if __name__ == "__main__":
    app()
