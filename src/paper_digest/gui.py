from __future__ import annotations

import os
import platform
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .aggregator import aggregate_outputs, load_cards
from .config import DEFAULT_OCR_MODEL, DEFAULT_TEXT_MODEL, Settings, load_settings, require_api_key
from .document_reader import supported_files
from .extractor import extract_paper_card, save_card, validation_error_message
from .folder_reports import run_folder_reports
from .ocr import ocr_bad_pages
from .pdf_parser import bad_page_numbers, detect_bad_extraction, extract_text_with_pymupdf, save_parsed_markdown
from .api_client import ApiClient
from .utils import ensure_dir, make_paper_id, write_failed


APP_TITLE = "Paper Digest API Based"
FOLDER_MODE = "资料夹报告（PDF/HTML/TXT/MD）"
FULL_PAPER_MODE = "论文卡片完整运行"
PARSE_MODE = "只解析 PDF"
EXTRACT_MODE = "只生成论文卡片"
AGGREGATE_MODE = "只汇总论文卡片"


class PaperDigestGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1220x780")
        self.minsize(1080, 700)

        self.project_dir = Path.cwd()
        self.input_dir = tk.StringVar(value=str(self.project_dir / "input_pdfs"))
        self.output_dir = tk.StringVar(value=str(self.project_dir / "outputs"))
        self.topic = tk.StringVar()
        self.api_key = tk.StringVar()
        self.base_url = tk.StringVar(value="https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.text_model = tk.StringVar(value=DEFAULT_TEXT_MODEL)
        self.ocr_model = tk.StringVar(value=DEFAULT_OCR_MODEL)
        self.use_ocr = tk.BooleanVar(value=True)
        self.max_file_mb = tk.DoubleVar(value=50.0)
        self.skip_existing = tk.BooleanVar(value=True)
        self.mode = tk.StringVar(value=FOLDER_MODE)
        self.progress_text = tk.StringVar(value="就绪")
        self.progress_value = tk.DoubleVar(value=0)
        self.selected_files: dict[str, bool] = {}
        self.file_paths: dict[str, Path] = {}
        self.worker: threading.Thread | None = None
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        self._load_env_values()
        self._build_style()
        self._build_layout()
        self._refresh_file_list()
        self._refresh_reports()
        self.after(150, self._drain_events)

    def _load_env_values(self) -> None:
        settings = load_settings()
        self.api_key.set(settings.dashscope_api_key)
        self.base_url.set(settings.api_base_url)
        self.text_model.set(settings.text_model)
        self.ocr_model.set(settings.ocr_model)

    def _build_style(self) -> None:
        self.configure(bg="#f6f7fb")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f7fb")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f6f7fb", foreground="#1f2937", font=("Microsoft YaHei UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1f2937", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background="#f6f7fb", foreground="#111827", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Hint.TLabel", background="#f6f7fb", foreground="#6b7280", font=("Microsoft YaHei UI", 9))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(10, 6))
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff")
        style.configure("Treeview", font=("Microsoft YaHei UI", 9), rowheight=28)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"))
        style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10), padding=(16, 8))

    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=(18, 16, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="选择一个文件夹，批量读取 PDF、HTML、TXT、MD；每个文件单独 API 上下文，最后生成检索 JSON 和 Markdown 总结",
            style="Hint.TLabel",
        ).pack(side="left", padx=(18, 0), pady=(8, 0))

        main = ttk.Frame(self, padding=(18, 8, 18, 14))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(main, style="Panel.TFrame", padding=16)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        sidebar.columnconfigure(1, weight=1)
        self._build_sidebar(sidebar)

        notebook = ttk.Notebook(main)
        notebook.grid(row=0, column=1, sticky="nsew")
        self.files_tab = ttk.Frame(notebook, padding=12)
        self.reports_tab = ttk.Frame(notebook, padding=12)
        self.outputs_tab = ttk.Frame(notebook, padding=12)
        self.logs_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.files_tab, text="文件队列")
        notebook.add(self.reports_tab, text="报告预览")
        notebook.add(self.outputs_tab, text="输出文件")
        notebook.add(self.logs_tab, text="运行日志")
        self._build_files_tab()
        self._build_reports_tab()
        self._build_outputs_tab()
        self._build_logs_tab()

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="任务配置", style="Panel.TLabel", font=("Microsoft YaHei UI", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )
        self._path_row(parent, 1, "资料文件夹", self.input_dir, self._choose_input)
        self._path_row(parent, 3, "输出文件夹", self.output_dir, self._choose_output)

        ttk.Label(parent, text="分析主题", style="Panel.TLabel").grid(row=5, column=0, columnspan=3, sticky="w", pady=(12, 4))
        ttk.Entry(parent, textvariable=self.topic, width=42).grid(row=6, column=0, columnspan=3, sticky="ew")

        ttk.Label(parent, text="运行模式", style="Panel.TLabel").grid(row=7, column=0, sticky="w", pady=(14, 4))
        modes = [FOLDER_MODE, FULL_PAPER_MODE, PARSE_MODE, EXTRACT_MODE, AGGREGATE_MODE]
        ttk.Combobox(parent, textvariable=self.mode, values=modes, state="readonly").grid(row=8, column=0, columnspan=3, sticky="ew")
        ttk.Checkbutton(parent, text="PDF 低质量页面启用 OCR", variable=self.use_ocr).grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )
        ttk.Label(parent, text="跳过超过 MB", style="Panel.TLabel").grid(row=10, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(parent, from_=0, to=999, increment=5, textvariable=self.max_file_mb, width=8).grid(
            row=10, column=1, sticky="w", pady=(8, 0)
        )
        ttk.Checkbutton(parent, text="跳过已有报告（断点续跑）", variable=self.skip_existing).grid(
            row=11, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        ttk.Separator(parent).grid(row=12, column=0, columnspan=3, sticky="ew", pady=16)
        ttk.Label(parent, text="API 配置", style="Panel.TLabel", font=("Microsoft YaHei UI", 12, "bold")).grid(
            row=13, column=0, columnspan=3, sticky="w"
        )
        self._entry_row(parent, 14, "API Key", self.api_key, show="*")
        self._entry_row(parent, 15, "Base URL", self.base_url)
        self._combo_row(
            parent,
            16,
            "文本模型",
            self.text_model,
            ["qwen3.6-plus", "qwen3.5-plus", "qwen-plus-latest", "qwen-max-latest", "qwen-turbo-latest"],
        )
        self._combo_row(parent, 17, "OCR 模型", self.ocr_model, ["qwen-vl-ocr-latest"])
        ttk.Button(parent, text="保存 .env 配置", command=self._save_env).grid(row=18, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Button(parent, text="重新读取系统环境变量", command=self._reload_env).grid(
            row=19, column=0, columnspan=3, sticky="ew", pady=(8, 0)
        )

        ttk.Separator(parent).grid(row=20, column=0, columnspan=3, sticky="ew", pady=16)
        self.run_button = ttk.Button(parent, text="开始运行", style="Accent.TButton", command=self._start_worker)
        self.run_button.grid(row=21, column=0, columnspan=3, sticky="ew")
        ttk.Button(parent, text="刷新文件列表", command=self._refresh_all).grid(row=22, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Button(parent, text="打开输出文件夹", command=lambda: open_path(Path(self.output_dir.get()))).grid(
            row=23, column=0, columnspan=3, sticky="ew", pady=(8, 0)
        )

        ttk.Label(parent, textvariable=self.progress_text, style="Panel.TLabel").grid(row=24, column=0, columnspan=3, sticky="w", pady=(18, 5))
        ttk.Progressbar(parent, variable=self.progress_value, maximum=100).grid(row=25, column=0, columnspan=3, sticky="ew")

    def _path_row(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar, command) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 4))
        ttk.Entry(parent, textvariable=var, width=34).grid(row=row + 1, column=0, columnspan=2, sticky="ew")
        ttk.Button(parent, text="选择", command=command).grid(row=row + 1, column=2, sticky="e", padx=(6, 0))

    def _entry_row(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar, show: str | None = None) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(parent, textvariable=var, show=show, width=32).grid(row=row, column=1, columnspan=2, sticky="ew", pady=(8, 0))

    def _combo_row(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar, values: list[str]) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(parent, textvariable=var, values=values, width=30).grid(
            row=row, column=1, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_files_tab(self) -> None:
        toolbar = ttk.Frame(self.files_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="全选", command=lambda: self._set_all_files(True)).pack(side="left")
        ttk.Button(toolbar, text="全不选", command=lambda: self._set_all_files(False)).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="反选", command=self._invert_files).pack(side="left", padx=(8, 0))
        ttk.Label(toolbar, text="提示：双击某一行可以勾选/取消。").pack(side="left", padx=(16, 0))

        self.file_tree = ttk.Treeview(self.files_tab, columns=("selected", "name", "type", "size", "path"), show="headings")
        for key, title, width in [
            ("selected", "处理", 60),
            ("name", "文件名", 260),
            ("type", "类型", 80),
            ("size", "大小", 90),
            ("path", "路径", 560),
        ]:
            self.file_tree.heading(key, text=title)
            self.file_tree.column(key, width=width, anchor="w")
        self.file_tree.bind("<Double-1>", self._toggle_selected_file)
        self.file_tree.pack(fill="both", expand=True)

    def _build_reports_tab(self) -> None:
        self.reports_tab.columnconfigure(0, weight=1)
        self.reports_tab.columnconfigure(1, weight=2)
        self.reports_tab.rowconfigure(0, weight=1)
        self.report_tree = ttk.Treeview(self.reports_tab, columns=("id", "name", "title"), show="headings")
        for key, title, width in [("id", "报告 ID", 180), ("name", "文件名", 240), ("title", "标题", 300)]:
            self.report_tree.heading(key, text=title)
            self.report_tree.column(key, width=width, anchor="w")
        self.report_tree.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.report_tree.bind("<<TreeviewSelect>>", self._show_selected_report)
        self.report_detail = tk.Text(self.reports_tab, wrap="word", font=("Microsoft YaHei UI", 10), relief="flat", padx=12, pady=12)
        self.report_detail.grid(row=0, column=1, sticky="nsew")

    def _build_outputs_tab(self) -> None:
        outputs = [
            ("检索 JSON", "search_index.json"),
            ("Markdown 总结", "folder_summary.md"),
            ("单文件 JSON 报告", "document_reports_json"),
            ("单文件 Markdown 报告", "document_reports_md"),
            ("文献卡片 JSONL", "literature_cards.jsonl"),
            ("Excel 文献矩阵", "literature_matrix.xlsx"),
            ("证据库 Markdown", "evidence_bank.md"),
            ("二次综合提示词", "synthesis_prompt.md"),
        ]
        for row, (title, relative) in enumerate(outputs):
            ttk.Label(self.outputs_tab, text=title).grid(row=row, column=0, sticky="w", pady=8)
            ttk.Button(self.outputs_tab, text="打开", command=lambda rel=relative: open_path(Path(self.output_dir.get()) / rel)).grid(
                row=row, column=1, sticky="w", padx=10
            )

    def _build_logs_tab(self) -> None:
        self.log_text = tk.Text(self.logs_tab, wrap="word", font=("Consolas", 10), relief="flat", padx=12, pady=12)
        self.log_text.pack(fill="both", expand=True)

    def _choose_input(self) -> None:
        selected = filedialog.askdirectory(title="选择资料文件夹")
        if selected:
            self.input_dir.set(selected)
            self._refresh_file_list()

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(title="选择输出文件夹")
        if selected:
            self.output_dir.set(selected)
            self._refresh_reports()

    def _save_env(self) -> None:
        env_text = "\n".join(
            [
                f"API_KEY={self.api_key.get().strip()}",
                f"API_BASE_URL={self.base_url.get().strip()}",
                f"TEXT_MODEL={self.text_model.get().strip()}",
                f"OCR_MODEL={self.ocr_model.get().strip()}",
                "",
            ]
        )
        (self.project_dir / ".env").write_text(env_text, encoding="utf-8")
        messagebox.showinfo("保存成功", ".env 配置已保存。")

    def _reload_env(self) -> None:
        self._load_env_values()
        messagebox.showinfo("读取成功", "已重新读取系统环境变量和 .env。")

    def _refresh_all(self) -> None:
        self._refresh_file_list()
        self._refresh_reports()

    def _refresh_file_list(self) -> None:
        self.file_tree.delete(*self.file_tree.get_children())
        self.file_paths.clear()
        for path in supported_files(Path(self.input_dir.get())):
            key = str(path)
            self.file_paths[key] = path
            self.selected_files.setdefault(key, True)
            size_mb = path.stat().st_size / 1024 / 1024
            self.file_tree.insert(
                "",
                "end",
                iid=key,
                values=("是" if self.selected_files[key] else "否", path.name, path.suffix.lower(), f"{size_mb:.2f} MB", str(path)),
            )

    def _toggle_selected_file(self, _event=None) -> None:
        selection = self.file_tree.selection()
        if not selection:
            return
        key = selection[0]
        self.selected_files[key] = not self.selected_files.get(key, True)
        self._update_file_row(key)

    def _set_all_files(self, value: bool) -> None:
        for key in self.file_paths:
            self.selected_files[key] = value
            self._update_file_row(key)

    def _invert_files(self) -> None:
        for key in self.file_paths:
            self.selected_files[key] = not self.selected_files.get(key, True)
            self._update_file_row(key)

    def _update_file_row(self, key: str) -> None:
        if not self.file_tree.exists(key):
            return
        values = list(self.file_tree.item(key, "values"))
        values[0] = "是" if self.selected_files.get(key, True) else "否"
        self.file_tree.item(key, values=values)

    def _refresh_reports(self) -> None:
        if not hasattr(self, "report_tree"):
            return
        self.report_tree.delete(*self.report_tree.get_children())
        reports_dir = Path(self.output_dir.get()) / "document_reports_json"
        if reports_dir.exists():
            for path in sorted(reports_dir.glob("*.json")):
                text = path.read_text(encoding="utf-8")
                import json

                data = json.loads(text)
                self.report_tree.insert("", "end", iid=data["document_id"], values=(data["document_id"], data["file_name"], data.get("title", "")))
        cards_dir = Path(self.output_dir.get()) / "cards_json"
        if cards_dir.exists():
            for card in load_cards(cards_dir):
                self.report_tree.insert("", "end", iid=card.paper_id, values=(card.paper_id, card.file_name, card.title))

    def _show_selected_report(self, _event=None) -> None:
        selection = self.report_tree.selection()
        if not selection:
            return
        output_dir = Path(self.output_dir.get())
        candidates = [
            output_dir / "document_reports_json" / f"{selection[0]}.json",
            output_dir / "cards_json" / f"{selection[0]}.json",
        ]
        for path in candidates:
            if path.exists():
                self.report_detail.delete("1.0", "end")
                self.report_detail.insert("1.0", path.read_text(encoding="utf-8"))
                return

    def _start_worker(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("任务正在运行", "当前已有任务在运行。")
            return
        if self.mode.get() != FOLDER_MODE and self.mode.get() != PARSE_MODE and not self.topic.get().strip():
            messagebox.showwarning("缺少分析主题", "请先填写分析主题。")
            return
        self.run_button.configure(state="disabled")
        self.progress_value.set(0)
        self._log("任务启动。")
        self.worker = threading.Thread(target=self._run_task, daemon=True)
        self.worker.start()

    def _run_task(self) -> None:
        try:
            mode = self.mode.get()
            if mode == FOLDER_MODE:
                self._run_folder_reports()
            else:
                if mode in {FULL_PAPER_MODE, PARSE_MODE}:
                    self._parse_pdfs()
                if mode in {FULL_PAPER_MODE, EXTRACT_MODE}:
                    self._extract_cards()
                if mode in {FULL_PAPER_MODE, AGGREGATE_MODE}:
                    self._aggregate()
            self.events.put(("done", "任务完成。"))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _settings_and_client(self) -> tuple[Settings, ApiClient]:
        loaded = load_settings(self.project_dir / ".env")
        settings = Settings(
            api_key=self.api_key.get().strip() or loaded.api_key,
            api_base_url=self.base_url.get().strip() or loaded.api_base_url,
            text_model=self.text_model.get().strip() or loaded.text_model,
            ocr_model=self.ocr_model.get().strip() or loaded.ocr_model,
            max_paper_chars=loaded.max_paper_chars,
            chunk_chars=loaded.chunk_chars,
            api_timeout_seconds=loaded.api_timeout_seconds,
        )
        require_api_key(settings)
        client = ApiClient(
            settings.api_key,
            settings.api_base_url,
            settings.text_model,
            settings.ocr_model,
            timeout=settings.api_timeout_seconds,
        )
        return settings, client

    def _run_folder_reports(self) -> None:
        settings, client = self._settings_and_client()
        input_dir = Path(self.input_dir.get())
        output_dir = Path(self.output_dir.get())
        files = supported_files(input_dir)
        selected = [self.file_paths[key] for key, chosen in self.selected_files.items() if chosen and key in self.file_paths]
        files = selected or files
        if not files:
            self.events.put(("log", f"在 {input_dir} 中没有找到 pdf/html/txt/md 文件。"))
            return
        max_file_mb = self.max_file_mb.get()

        def progress(index: int, total: int, path: Path, status: str = "done") -> None:
            self.events.put(("status", f"正在处理：{path.name}"))
            self.events.put(("progress", index / total * 100))
            label = "已跳过" if status == "skipped" else "已存在，跳过" if status == "existing" else "已完成单文件报告"
            self.events.put(("log", f"[{index}/{total}] {label}：{path.name}"))

        reports = run_folder_reports(
            client,
            settings,
            input_dir,
            output_dir,
            self.topic.get().strip(),
            progress=progress,
            files=files,
            max_file_mb=None if max_file_mb <= 0 else max_file_mb,
            skip_existing=self.skip_existing.get(),
        )
        self.events.put(("log", f"已生成 {len(reports)} 个单文件报告。"))
        self.events.put(("log", f"检索 JSON：{output_dir / 'search_index.json'}"))
        self.events.put(("log", f"Markdown 总结：{output_dir / 'folder_summary.md'}"))

    def _parse_pdfs(self) -> None:
        input_dir = Path(self.input_dir.get())
        parsed_dir = ensure_dir(Path(self.output_dir.get()) / "parsed_text")
        pdf_paths = sorted(input_dir.glob("*.pdf"))
        if not pdf_paths:
            self.events.put(("log", f"在 {input_dir} 中没有找到 PDF 文件。"))
            return
        _, client = self._settings_and_client() if self.use_ocr.get() else (None, None)
        for index, pdf_path in enumerate(pdf_paths, start=1):
            paper_id = make_paper_id(index, pdf_path)
            self.events.put(("status", f"正在解析：{pdf_path.name}"))
            try:
                parsed = extract_text_with_pymupdf(pdf_path)
                page_texts = parsed["page_texts"]
                if client and detect_bad_extraction(page_texts):
                    pages = bad_page_numbers(page_texts) or list(page_texts)
                    self.events.put(("log", f"{pdf_path.name} 文本质量偏低，启用 OCR：{pages}"))
                    page_texts.update(ocr_bad_pages(client, pdf_path, pages))
                save_parsed_markdown(paper_id, parsed["metadata"], page_texts, parsed_dir / f"{paper_id}.md")
                self.events.put(("log", f"已解析：{pdf_path.name}"))
            except Exception as exc:
                write_failed(Path("logs"), paper_id, pdf_path.name, "parse", str(exc))
                self.events.put(("log", f"解析失败：{pdf_path.name}；{exc}"))
            self.events.put(("progress", index / len(pdf_paths) * 35))

    def _extract_cards(self) -> None:
        output_dir = Path(self.output_dir.get())
        parsed_dir = output_dir / "parsed_text"
        cards_dir = ensure_dir(output_dir / "cards_json")
        md_paths = sorted(parsed_dir.glob("*.md"))
        if not md_paths:
            self.events.put(("log", f"在 {parsed_dir} 中没有找到解析文本。"))
            return
        settings, client = self._settings_and_client()
        for index, path in enumerate(md_paths, start=1):
            self.events.put(("status", f"正在生成文献卡片：{path.name}"))
            try:
                card = extract_paper_card(client, settings, path, self.topic.get().strip(), paper_id=path.stem, file_name=path.name)
                save_card(card, cards_dir / f"{card.paper_id}.json")
                self.events.put(("log", f"已生成卡片：{card.paper_id}"))
            except Exception as exc:
                message = validation_error_message(exc) if hasattr(exc, "errors") else str(exc)
                write_failed(Path("logs"), path.stem, path.name, "extract", message)
                self.events.put(("log", f"生成卡片失败：{path.name}；{message}"))
            self.events.put(("progress", 35 + index / len(md_paths) * 55))

    def _aggregate(self) -> None:
        output_dir = Path(self.output_dir.get())
        self.events.put(("status", "正在汇总输出文件"))
        cards = aggregate_outputs(output_dir / "cards_json", output_dir, self.topic.get().strip())
        self.events.put(("progress", 100))
        self.events.put(("log", f"已汇总 {len(cards)} 张文献卡片。"))

    def _drain_events(self) -> None:
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._log(str(value))
            elif kind == "status":
                self.progress_text.set(str(value))
            elif kind == "progress":
                self.progress_value.set(float(value))
            elif kind == "done":
                self._log(str(value))
                self.progress_text.set("完成")
                self.progress_value.set(100)
                self.run_button.configure(state="normal")
                self._refresh_all()
            elif kind == "error":
                self._log(f"任务异常：{value}")
                self.progress_text.set("任务异常")
                self.run_button.configure(state="normal")
                messagebox.showerror("任务异常", str(value))
        self.after(150, self._drain_events)

    def _log(self, message: str) -> None:
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")


def open_path(path: Path) -> None:
    if not path.exists():
        messagebox.showwarning("文件不存在", f"路径不存在：{path}")
        return
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def main() -> None:
    app = PaperDigestGui()
    app.mainloop()


if __name__ == "__main__":
    main()
