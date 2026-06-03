from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_TEXT_MODEL = "qwen3.5-plus"
DEFAULT_OCR_MODEL = "qwen-vl-ocr-latest"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass(frozen=True)
class Settings:
    api_key: str
    api_base_url: str
    text_model: str
    ocr_model: str
    max_paper_chars: int = 90_000
    chunk_chars: int = 24_000
    api_timeout_seconds: float = 300.0


def load_settings(env_path: Path | None = None) -> Settings:
    load_dotenv(env_path, override=False)
    return Settings(
        api_key=_first_env("API_KEY", "DASHSCOPE_API_KEY", "QWEN_API_KEY", "OPENAI_API_KEY"),
        api_base_url=_first_env("API_BASE_URL", "QWEN_BASE_URL") or DEFAULT_BASE_URL,
        text_model=_first_env("TEXT_MODEL", "QWEN_TEXT_MODEL") or DEFAULT_TEXT_MODEL,
        ocr_model=_first_env("OCR_MODEL", "QWEN_OCR_MODEL") or DEFAULT_OCR_MODEL,
        max_paper_chars=int(os.getenv("MAX_PAPER_CHARS", "90000")),
        chunk_chars=int(os.getenv("PAPER_CHUNK_CHARS", "24000")),
        api_timeout_seconds=float(os.getenv("API_TIMEOUT_SECONDS", "300")),
    )


def require_api_key(settings: Settings) -> None:
    if not settings.api_key:
        raise RuntimeError("没有找到 API Key。请在系统环境变量或 .env 中设置 API_KEY。")


DEFAULT_QWEN_TEXT_MODEL = DEFAULT_TEXT_MODEL
DEFAULT_QWEN_OCR_MODEL = DEFAULT_OCR_MODEL


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""
