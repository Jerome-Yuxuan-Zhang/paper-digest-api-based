from paper_digest.gui import APP_TITLE


def test_gui_title_is_chinese() -> None:
    assert "文献" in APP_TITLE

