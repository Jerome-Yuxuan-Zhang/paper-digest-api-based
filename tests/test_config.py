from paper_digest.config import load_settings
from paper_digest.config import DEFAULT_TEXT_MODEL


def test_load_settings_accepts_generic_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("API_KEY", "generic-key")

    settings = load_settings(tmp_path / "missing.env")

    assert settings.api_key == "generic-key"


def test_default_text_model_is_long_document_friendly(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("QWEN_TEXT_MODEL", raising=False)
    monkeypatch.delenv("TEXT_MODEL", raising=False)

    settings = load_settings(tmp_path / "missing.env")

    assert settings.text_model == DEFAULT_TEXT_MODEL
