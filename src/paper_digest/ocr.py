from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import fitz

from .qwen_client import QwenClient


OCR_PROMPT = """Extract this PDF page into Markdown.
Requirements:
- Preserve heading hierarchy.
- Preserve table structure as much as possible.
- Write formulas in LaTeX when visible.
- Do not invent missing content.
- Mark unclear text as [UNCLEAR].
- Output Markdown only."""


def render_pdf_page_to_image(pdf_path: Path, page_number: int, dpi: int = 200) -> Path:
    output_dir = Path(tempfile.mkdtemp(prefix="paper_digest_ocr_"))
    image_path = output_dir / f"{pdf_path.stem}_page_{page_number}.png"
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        pix = page.get_pixmap(dpi=dpi)
        pix.save(image_path)
    return image_path


def image_to_data_url(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def call_qwen_ocr(client: QwenClient, image_path: Path, prompt: str = OCR_PROMPT) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
            ],
        }
    ]
    return client.chat_text(messages, model=client.ocr_model, temperature=0.0, max_tokens=4096)


def ocr_bad_pages(client: QwenClient, pdf_path: Path, bad_page_numbers: list[int]) -> dict[int, str]:
    results: dict[int, str] = {}
    for page_number in bad_page_numbers:
        image_path = render_pdf_page_to_image(pdf_path, page_number)
        try:
            results[page_number] = call_qwen_ocr(client, image_path)
        except Exception as exc:
            results[page_number] = f"[OCR_FAILED: {exc}]"
    return results

