from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_QWEN_TEXT_MODEL = "qwen3.5-plus"
DEFAULT_QWEN_OCR_MODEL = "qwen-vl-ocr-latest"


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str
    qwen_base_url: str
    qwen_text_model: str
    qwen_ocr_model: str
    max_paper_chars: int = 90_000
    chunk_chars: int = 24_000
    api_timeout_seconds: float = 300.0


def load_settings(env_path: Path | None = None) -> Settings:
    load_dotenv(env_path, override=False)
    return Settings(
        dashscope_api_key=_first_env("DASHSCOPE_API_KEY", "QWEN_API_KEY", "OPENAI_API_KEY"),
        qwen_base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        qwen_text_model=os.getenv("QWEN_TEXT_MODEL", DEFAULT_QWEN_TEXT_MODEL),
        qwen_ocr_model=os.getenv("QWEN_OCR_MODEL", DEFAULT_QWEN_OCR_MODEL),
        max_paper_chars=int(os.getenv("MAX_PAPER_CHARS", "90000")),
        chunk_chars=int(os.getenv("PAPER_CHUNK_CHARS", "24000")),
        api_timeout_seconds=float(os.getenv("API_TIMEOUT_SECONDS", "300")),
    )


def require_api_key(settings: Settings) -> None:
    if not settings.dashscope_api_key:
        raise RuntimeError("没有找到 Qwen API Key。请在系统环境变量或 .env 中设置 DASHSCOPE_API_KEY。")


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""
