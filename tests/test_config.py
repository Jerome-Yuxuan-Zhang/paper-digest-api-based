from paper_digest.config import load_settings
from paper_digest.config import DEFAULT_QWEN_TEXT_MODEL


def test_load_settings_accepts_qwen_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("QWEN_API_KEY", "qwen-key")

    settings = load_settings(tmp_path / "missing.env")

    assert settings.dashscope_api_key == "qwen-key"


def test_default_text_model_is_long_document_friendly(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("QWEN_TEXT_MODEL", raising=False)

    settings = load_settings(tmp_path / "missing.env")

    assert settings.qwen_text_model == DEFAULT_QWEN_TEXT_MODEL
