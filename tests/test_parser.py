from paper_digest.pdf_parser import detect_bad_extraction


def test_detect_bad_extraction_for_empty_pages() -> None:
    assert detect_bad_extraction({1: "", 2: "   "}) is True


def test_detect_bad_extraction_for_rich_pages() -> None:
    rich = "This is a normal academic page with enough readable text. " * 50
    assert detect_bad_extraction({1: rich, 2: rich}) is False

