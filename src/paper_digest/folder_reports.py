from __future__ import annotations

import json
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed

from .config import Settings
from .document_reader import read_document, supported_files
from .qwen_client import QwenClient
from .schemas import DOCUMENT_REPORT_JSON_SCHEMA, DocumentReport
from .utils import ensure_dir, slugify, write_failed, write_text


REPORT_SYSTEM_PROMPT = """你是严谨的资料分析助手。
你每次只处理一个文件，必须只基于当前文件内容生成报告。
不得引用其他文件，不得假设文件外信息，不得编造事实。
如果信息没有出现，写 "not stated" 或空列表。
输出必须是严格 JSON。"""


REPORT_USER_PROMPT = """请为下面这个文件生成一个结构化中文报告。

用户主题：
{topic}

要求：
1. 只分析当前文件，不要引用其他文件。
2. 提取摘要、关键点、重要细节、实体、日期或时期、方法或框架、数据或证据。
3. 给出与用户主题的关系。
4. 给出标签和检索关键词，方便后续搜索。
5. 标出不确定性、缺失信息或需要回原文核验的位置。
6. 如果是 PDF，尽量保留 Page 页码线索。
7. 只返回 JSON，不要 Markdown，不要解释。

JSON schema：
{schema}

文件 ID：{document_id}
文件名：{file_name}
文件类型：{file_type}

文件内容：
{content}
"""


MAX_DOCUMENT_CHARS = 80_000


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
def generate_document_report(
    client: QwenClient,
    path: Path,
    topic: str,
    document_id: str,
) -> DocumentReport:
    content = read_document(path)
    warnings: list[str] = []
    if len(content) > MAX_DOCUMENT_CHARS:
        content = content[:MAX_DOCUMENT_CHARS]
        warnings.append("文件内容超过单文件上限，已截取前部内容；建议拆分长文件后重跑。")
    raw = client.chat_json(
        [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REPORT_USER_PROMPT.format(
                    topic=topic or "not stated",
                    schema=json.dumps(DOCUMENT_REPORT_JSON_SCHEMA, ensure_ascii=False),
                    document_id=document_id,
                    file_name=path.name,
                    file_type=path.suffix.lower().lstrip("."),
                    content=content,
                ),
            },
        ],
        max_tokens=8192,
    )
    raw.setdefault("document_id", document_id)
    raw.setdefault("file_name", path.name)
    raw.setdefault("file_type", path.suffix.lower().lstrip("."))
    report = DocumentReport.model_validate(raw)
    if warnings:
        report.uncertainty_or_limits.extend(warnings)
    return report


def document_id_for(index: int, path: Path) -> str:
    return f"doc_{index:03d}_{slugify(path.stem)}"


def save_individual_report(report: DocumentReport, output_dir: Path) -> None:
    json_dir = ensure_dir(output_dir / "document_reports_json")
    md_dir = ensure_dir(output_dir / "document_reports_md")
    write_text(json_dir / f"{report.document_id}.json", report.model_dump_json(indent=2))
    write_text(md_dir / f"{report.document_id}.md", report_to_markdown(report))


def report_to_markdown(report: DocumentReport) -> str:
    def lines(title: str, values: list[str]) -> list[str]:
        if not values:
            return [f"## {title}", "", "- not stated", ""]
        return [f"## {title}", "", *[f"- {value}" for value in values], ""]

    content = [
        f"# {report.title}",
        "",
        f"- 文件 ID：{report.document_id}",
        f"- 文件名：{report.file_name}",
        f"- 文件类型：{report.file_type}",
        "",
        "## 摘要",
        "",
        report.summary,
        "",
        "## 与主题的关系",
        "",
        report.relation_to_user_topic,
        "",
    ]
    for title, values in [
        ("关键点", report.key_points),
        ("重要细节", report.important_details),
        ("实体", report.entities),
        ("日期或时期", report.dates_or_periods),
        ("方法或框架", report.methods_or_frameworks),
        ("数据或证据", report.data_or_evidence),
        ("可引用位置或线索", report.useful_quotes_or_locations),
        ("标签", report.tags),
        ("检索关键词", report.search_keywords),
        ("不确定性与限制", report.uncertainty_or_limits),
    ]:
        content.extend(lines(title, values))
    return "\n".join(content)


def write_search_json(reports: list[DocumentReport], output_path: Path) -> None:
    data = {
        "count": len(reports),
        "documents": [report.model_dump() for report in reports],
    }
    write_text(output_path, json.dumps(data, ensure_ascii=False, indent=2))


def write_summary_markdown(reports: list[DocumentReport], output_path: Path, topic: str) -> None:
    lines = [
        "# 资料夹自动总结",
        "",
        f"用户主题：{topic or 'not stated'}",
        "",
        f"共处理文件：{len(reports)} 个",
        "",
        "## 总览",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"### {report.document_id}: {report.title}",
                "",
                f"- 文件：{report.file_name}",
                f"- 类型：{report.file_type}",
                f"- 摘要：{report.summary}",
                f"- 与主题关系：{report.relation_to_user_topic}",
                f"- 标签：{', '.join(report.tags) if report.tags else 'not stated'}",
                f"- 检索关键词：{', '.join(report.search_keywords) if report.search_keywords else 'not stated'}",
                "",
            ]
        )
        if report.key_points:
            lines.extend(["关键点：", *[f"- {point}" for point in report.key_points], ""])
        if report.uncertainty_or_limits:
            lines.extend(["不确定性与限制：", *[f"- {item}" for item in report.uncertainty_or_limits], ""])
    write_text(output_path, "\n".join(lines))


def run_folder_reports(
    client: QwenClient,
    settings: Settings,
    input_dir: Path,
    output_dir: Path,
    topic: str,
    log_dir: Path = Path("logs"),
    progress=None,
    files: list[Path] | None = None,
    max_file_mb: float | None = 50.0,
    skip_existing: bool = True,
) -> list[DocumentReport]:
    del settings
    ensure_dir(output_dir)
    files = files if files is not None else supported_files(input_dir)
    reports: list[DocumentReport] = []
    for index, path in enumerate(files, start=1):
        document_id = document_id_for(index, path)
        existing_report = output_dir / "document_reports_json" / f"{document_id}.json"
        if skip_existing and existing_report.exists():
            reports.append(DocumentReport.model_validate_json(existing_report.read_text(encoding="utf-8")))
            if progress:
                progress(index, len(files), path, "existing")
            continue
        try:
            size_mb = path.stat().st_size / 1024 / 1024
            if max_file_mb is not None and size_mb > max_file_mb:
                write_failed(log_dir, document_id, path.name, "folder_report", f"文件过大，已跳过：{size_mb:.2f} MB > {max_file_mb:.2f} MB")
                if progress:
                    progress(index, len(files), path, "skipped")
                continue
            report = generate_document_report(client, path, topic, document_id)
            save_individual_report(report, output_dir)
            reports.append(report)
        except Exception as exc:
            write_failed(log_dir, document_id, path.name, "folder_report", str(exc))
        if progress:
            progress(index, len(files), path, "done")
    write_search_json(reports, output_dir / "search_index.json")
    write_summary_markdown(reports, output_dir / "folder_summary.md", topic)
    return reports
