from pathlib import Path

from paper_digest.config import Settings
from paper_digest.folder_reports import run_folder_reports


class FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        return {"title": "标题", "summary": "摘要"}


def _settings() -> Settings:
    return Settings(api_key="k", api_base_url="u", text_model="m", ocr_model="o")


def test_concurrent_adjusts_lanes_to_file_count(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for i in range(5):
        (input_dir / f"doc{i}.txt").write_text(f"content {i}", encoding="utf-8")

    client = FakeClient()
    lane_events: list[tuple[int, str, int, int]] = []

    reports = run_folder_reports(
        client,
        _settings(),
        input_dir,
        output_dir,
        "topic",
        concurrency=50,
        lane_progress=lambda lane, path, pos, total: lane_events.append((lane, path.name, pos, total)),
        max_file_mb=None,
    )

    assert len(reports) == 5
    assert client.calls == 5
    # 设置 50 路但只有 5 个文件 -> 自动调节为 5 路
    lanes_used = {event[0] for event in lane_events}
    assert lanes_used == {0, 1, 2, 3, 4}


def test_concurrent_reports_keep_input_order(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    for i in range(6):
        (input_dir / f"doc{i}.txt").write_text(f"content {i}", encoding="utf-8")

    client = FakeClient()
    reports = run_folder_reports(client, _settings(), input_dir, output_dir, "topic", concurrency=3, max_file_mb=None)

    assert [r.document_id for r in reports] == [f"doc_{i:03d}_doc{i - 1}" for i in range(1, 7)]
    assert (output_dir / "search_index.json").exists()
    assert (output_dir / "folder_summary.md").exists()


def test_sequential_default_concurrency_still_works(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("x", encoding="utf-8")

    client = FakeClient()
    reports = run_folder_reports(client, _settings(), input_dir, output_dir, "topic", max_file_mb=None)

    assert len(reports) == 1
    assert client.calls == 1
