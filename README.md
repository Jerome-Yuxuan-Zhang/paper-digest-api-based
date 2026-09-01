# paper-digest-api-based

> 本地批量资料分析工具 · Local batch document analysis tool

`paper-digest-api-based` 是一个在本地运行的资料夹批量分析工具。它读取一个文件夹里的 **PDF / HTML / TXT / MD** 文件，为每个文件单独调用一次 API 生成独立报告，最后自动汇总成便于检索和阅读的总文件。

`paper-digest-api-based` is a local batch document analysis tool. It reads **PDF / HTML / TXT / MD** files in a folder, calls the API separately for each file to produce an independent report, then aggregates everything into searchable, readable summary files.

---

## 它能做什么 · What it does

**中文**

- 批量分析一个文件夹里的 PDF / HTML / TXT / MD 文件。
- 每个文件使用独立的 API 上下文，避免把所有资料塞进同一个上下文窗口。
- 自动生成两个总文件：`search_index.json`（结构化检索索引）与 `folder_summary.md`（Markdown 总结）。
- 提供中文图形界面（GUI），并保留论文卡片流程（PDF 解析、文献卡片、Excel 文献矩阵、证据库）。
- 支持 2~100 路并发分析，每路独立进度条，文件少于路数时自动调节。

**English**

- Batch-analyze PDF / HTML / TXT / MD files in a folder.
- Each file runs in its own API context, so materials are never crammed into a single context window.
- Auto-generates two summary files: `search_index.json` (structured search index) and `folder_summary.md` (Markdown summary).
- Ships a Chinese GUI, plus a paper-card pipeline (PDF parsing, literature cards, Excel matrix, evidence bank).
- Supports 2–100 concurrent lanes, each with its own progress bar, auto-adjusted when there are fewer files than lanes.

---

## 快速开始 · Quick Start

### 方式一：免安装版（推荐）· Option 1: Portable EXE (recommended)

**中文**

1. 从 [Releases](https://github.com/Jerome-Yuxuan-Zhang/paper-digest-api-based/releases) 页面下载最新的 `PaperDigestApiBased.exe`。
2. 把 `PaperDigestApiBased.exe` 放到一个**单独的文件夹**里（程序会在旁边自动创建 `input_pdfs`、`outputs`、`logs` 等目录）。
3. 双击运行。首次启动会稍作解压，请耐心等待。
4. 在左侧「API 配置」填入 API Key，然后把要分析的文件放进 `input_pdfs` 文件夹。
5. 点击「开始运行」。

**English**

1. Download the latest `PaperDigestApiBased.exe` from the [Releases](https://github.com/Jerome-Yuxuan-Zhang/paper-digest-api-based/releases) page.
2. Put the exe into its **own folder** (the program auto-creates `input_pdfs`, `outputs`, `logs`, etc. next to it).
3. Double-click to run. The first launch unpacks for a while — please be patient.
4. Enter your API Key under "API 配置" (API configuration), then drop your files into the `input_pdfs` folder.
5. Click "开始运行" (Start).

> 提示：若 Windows SmartScreen 弹出「Windows 已保护你的电脑」，点「更多信息」→「仍要运行」。
> Tip: If Windows SmartScreen says "Windows protected your PC", click "More info" → "Run anyway".

### 方式二：从源码运行（需要 Python 3.11+）· Option 2: Run from source (Python 3.11+ required)

```bash
pip install -r requirements.txt
python -m paper_digest.gui
```

> 命令行用法与开发/打包说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。
> See [CONTRIBUTING.md](CONTRIBUTING.md) for CLI usage and development/packaging instructions.

---

## 配置 API · API Configuration

**中文**

本项目默认推荐 **Qwen / DashScope**（OpenAI-compatible，中文能力强，适合长文档），也兼容任何 OpenAI Chat Completions API 的长上下文模型。在 GUI 左侧「API 配置」中填写：

| 项目 | 值 |
|------|-----|
| API Key | 你的 DashScope / Qwen API Key |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 文本模型 | `qwen3.8-flash`（默认） |
| OCR 模型 | `qwen-vl-ocr-latest` |

- 可点「保存 .env 配置」把配置存到本地，下次启动自动读取；也可点「重新读取系统环境变量」读取系统环境变量。
- 若你的账号暂未开放 `qwen3.8-flash`，可改用 `qwen3.6-plus`、`qwen3.5-plus` 或 `qwen-plus-latest`。

**English**

This project defaults to **Qwen / DashScope** (OpenAI-compatible, strong Chinese, long-document friendly). Any long-context model compatible with the OpenAI Chat Completions API also works. Fill in the left "API 配置" (API configuration) panel:

| Item | Value |
|------|-------|
| API Key | Your DashScope / Qwen API Key |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Text model | `qwen3.8-flash` (default) |
| OCR model | `qwen-vl-ocr-latest` |

- Click "保存 .env 配置" (Save .env) to persist the config locally; or click "重新读取系统环境变量" (Reload env) to read from system environment variables.
- If `qwen3.8-flash` is not available for your account, use `qwen3.6-plus`, `qwen3.5-plus`, or `qwen-plus-latest` instead.

---

## 输出文件 · Output Files

**中文**

| 文件 / 文件夹 | 说明 |
|---------------|------|
| `outputs/search_index.json` | 所有报告汇总后的结构化检索索引 |
| `outputs/folder_summary.md` | 所有报告汇总后的 Markdown 总结 |
| `outputs/document_reports_json/` | 每个文件的独立 JSON 报告 |
| `outputs/document_reports_md/` | 每个文件的独立 Markdown 报告 |
| `outputs/parsed_text/` | 每篇论文的解析文本（保留页码） |
| `outputs/cards_json/` | 每篇论文的结构化文献卡片 |
| `outputs/literature_matrix.xlsx` | 文献矩阵（Excel） |
| `logs/failed_papers.csv` | 失败记录 |

单个文件失败不会中断整个批处理。

**English**

| File / Folder | Description |
|---------------|-------------|
| `outputs/search_index.json` | Structured search index of all reports |
| `outputs/folder_summary.md` | Markdown summary of all reports |
| `outputs/document_reports_json/` | One independent JSON report per file |
| `outputs/document_reports_md/` | One independent Markdown report per file |
| `outputs/parsed_text/` | Parsed text per paper (page numbers preserved) |
| `outputs/cards_json/` | One structured literature card per paper |
| `outputs/literature_matrix.xlsx` | Literature matrix (Excel) |
| `logs/failed_papers.csv` | Failure log |

A single failed file never aborts the whole batch.

---

## 使用建议 · Tips

**中文**

- 先拿少量文件试跑，确认配置正常。
- 文件较多时可调大「并发路数（2~100）」提速。
- 默认会跳过超过 50 MB 的文件，避免超大文件卡住批处理。
- 默认启用「跳过已有报告（断点续跑）」，中断后重开可接着跑。
- 若 PDF 都是可选中文本，可关闭 OCR 以降低成本。
- 可通过环境变量 `API_TIMEOUT_SECONDS` 控制单次 API 等待时间。

**English**

- Try a few files first to confirm the setup works.
- Raise "并发路数" (concurrency, 2–100) to speed things up with many files.
- Files over 50 MB are skipped by default to avoid stalling the batch.
- "跳过已有报告" (skip existing / resume) is on by default, so you can resume after interruption.
- If your PDFs have selectable text, turn OCR off to cut cost.
- Use the `API_TIMEOUT_SECONDS` env var to control the per-call API timeout.

---

## 许可证 · License

**中文**

本项目以 [MIT 许可证](LICENSE) 开源。第三方组件许可证清单见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

**English**

This project is open source under the [MIT License](LICENSE). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for third-party licenses.

---

## 支持作者 · Support

**中文**

如果这个工具帮到了你，欢迎请作者喝杯咖啡 ☕：

<div align="center">
  <img src="docs/sponsor/wechat.jpg" alt="微信赞赏" width="220" />
  &nbsp;&nbsp;
  <img src="docs/sponsor/alipay.jpg" alt="支付宝" width="220" />
</div>

**English**

If this tool helps you, consider buying the author a coffee ☕:

<div align="center">
  <img src="docs/sponsor/wechat.jpg" alt="WeChat Pay" width="220" />
  &nbsp;&nbsp;
  <img src="docs/sponsor/alipay.jpg" alt="Alipay" width="220" />
</div>
