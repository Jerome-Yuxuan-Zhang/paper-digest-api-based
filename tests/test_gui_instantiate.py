import pytest


def test_gui_instantiates_and_loads_settings_without_error() -> None:
    tk = pytest.importorskip("tkinter")
    try:
        from paper_digest.gui import PaperDigestGui

        app = PaperDigestGui()
        app.withdraw()
        app.update_idletasks()
        app.destroy()
    except tk.TclError as exc:
        pytest.skip(f"Tk 不可用（无显示环境）：{exc}")
