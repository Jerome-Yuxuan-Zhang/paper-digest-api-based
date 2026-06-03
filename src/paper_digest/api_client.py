from __future__ import annotations

import json
from typing import Any

from loguru import logger
from openai import APIError, APITimeoutError, OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class ApiClient:
    def __init__(self, api_key: str, base_url: str, text_model: str, ocr_model: str, timeout: float = 300.0):
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.text_model = text_model
        self.ocr_model = ocr_model
        self.token_usage: list[dict[str, Any]] = []

    @retry(
        retry=retry_if_exception_type((APIError, APITimeoutError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _chat(self, **kwargs: Any) -> Any:
        response = self.client.chat.completions.create(**kwargs)
        usage = getattr(response, "usage", None)
        if usage:
            self.token_usage.append(usage.model_dump() if hasattr(usage, "model_dump") else dict(usage))
            logger.info("Token usage: {}", self.token_usage[-1])
        return response

    def chat_json(self, messages: list[dict[str, Any]], temperature: float = 0.1, max_tokens: int = 4096) -> dict[str, Any]:
        kwargs = {
            "model": self.text_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        try:
            response = self._chat(**kwargs)
        except Exception:
            kwargs.pop("response_format", None)
            messages = [*messages, {"role": "user", "content": "Return only a valid JSON object. No Markdown."}]
            response = self._chat(**{**kwargs, "messages": messages})
        content = response.choices[0].message.content or "{}"
        return json.loads(_strip_json_fences(content))

    def chat_text(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> str:
        response = self._chat(
            model=model or self.text_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


def _strip_json_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
