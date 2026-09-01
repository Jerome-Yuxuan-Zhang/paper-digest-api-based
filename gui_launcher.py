import sys
import traceback
from pathlib import Path


def _error_log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "paper_digest_error.log"
    return Path.cwd() / "paper_digest_error.log"


def _record_error(exc: BaseException) -> None:
    try:
        with _error_log_path().open("a", encoding="utf-8") as handle:
            handle.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
            handle.write("\n")
    except Exception:
        pass


def _show_error(exc: BaseException) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Paper Digest 启动失败",
            f"{exc}\n\n错误详情已写入：{_error_log_path()}",
        )
        root.destroy()
    except Exception:
        pass


def main() -> int:
    try:
        from paper_digest.gui import main as gui_main

        gui_main()
        return 0
    except Exception as exc:  # noqa: BLE001
        _record_error(exc)
        _show_error(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


