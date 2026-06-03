# paper-digest-api-based

`paper-digest-api-based` 是一个本地运行的资料夹批量分析工具。它可以读取一个文件夹中的 PDF、HTML、TXT、MD 文件，并且每个文件都会使用单独的 API 上下文生成一份独立报告，避免把所有资料塞进同一个 context window。

项目目标是接入**任意高性能、长上下文、OpenAI-compatible API**。默认配置以 DashScope/Qwen 为示例，但你可以改成其他兼容 OpenAI Chat Completions API 的模型服务。

全部文件处理完成后，程序会自动生成两个核心总文件：

- `outputs/search_index.json`：方便检索、二次处理和程序读取的结构化 JSON。
- `outputs/folder_summary.md`：方便人工阅读、复制给 AI 或继续写作的 Markdown 总结。

项目也保留论文卡片流程：PDF 解析、文献卡片、Excel 文献矩阵、证据库和综述提示词。

## 开源前提醒

- 不要提交 `.env`、API Key、个人 PDF、生成报告、日志或 exe 构建产物。
- 默认 `.gitignore` 已忽略 `input_pdfs/`、`outputs/`、`logs/`、`build/`、`dist/`、`.env` 和 `*.exe`。
- 程序会把被分析文本发送到你配置的 API。请只处理你有权发送给第三方模型服务的文件。
- 当前项目适合先作为 `v0.1.0-alpha` 使用；超长文件处理仍以截断/跳过为主，不是完整长文 map-reduce。

## 安装

需要 Python 3.11 或更高版本。

```bash
git clone https://github.com/Jerome-Yuxuan-Zhang/paper-digest-api-based.git
cd paper-digest-api-based
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

macOS 或 Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

## 配置 API

如果你已经把 API Key 注入系统环境变量，可以不创建 `.env`。程序会优先读取系统环境变量。

推荐变量名：

```env
API_KEY=你的key
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_MODEL=qwen3.5-plus
OCR_MODEL=qwen-vl-ocr-latest
```

兼容旧变量名：

```env
DASHSCOPE_API_KEY=你的key
QWEN_API_KEY=你的key
OPENAI_API_KEY=你的key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_TEXT_MODEL=qwen3.5-plus
QWEN_OCR_MODEL=qwen-vl-ocr-latest
```

不要把 API Key 写死进代码。模型名称和 `base_url` 会从系统环境变量、`.env` 或 GUI 当前输入读取。

默认模型只是示例：

- `TEXT_MODEL=qwen3.5-plus`：适合资料夹报告、长文档分析和结构化 JSON 抽取。
- `OCR_MODEL=qwen-vl-ocr-latest`：适合 OCR。

你可以换成任何兼容 OpenAI Chat Completions API 的长上下文模型。

## 中文 GUI

启动中文桌面界面：

```bash
python -m paper_digest.gui
```

或安装后运行：

```bash
paper-digest-gui
```

GUI 支持：

- 资料文件夹、输出文件夹、分析主题、运行模式、OCR 开关。
- API 配置：默认读取系统环境变量，也可以手动保存到 `.env`。
- 文件队列：显示 PDF、HTML、TXT、MD 的文件名、类型、大小和路径。
- 运行控制：资料夹报告、论文卡片完整运行、只解析 PDF、只生成论文卡片、只汇总论文卡片。
- 文件勾选：全选、全不选、反选，双击某行切换处理状态。
- 跳过大文件：默认跳过超过 50 MB 的文件。
- 断点续跑：默认跳过已经存在的单文件报告。
- 实时进度与中文日志。
- 报告预览和输出文件快捷打开。

默认模式是：

```text
资料夹报告（PDF/HTML/TXT/MD）
```

## 命令行运行

资料夹报告流程：

```bash
python -m paper_digest.cli folder --input input_pdfs --output outputs --topic "你的分析主题"
```

支持格式：

```text
pdf, html, htm, txt, md
```

跳过超大文件：

```bash
python -m paper_digest.cli folder --input input_pdfs --output outputs --max-file-mb 50
```

强制重跑已有报告：

```bash
python -m paper_digest.cli folder --input input_pdfs --output outputs --rerun-existing
```

单文件报告会保存到：

```text
outputs/document_reports_json/
outputs/document_reports_md/
```

最终两个总文件：

```text
outputs/search_index.json
outputs/folder_summary.md
```

论文卡片完整流程：

```bash
python -m paper_digest.cli run --input input_pdfs --output outputs --topic "你的研究主题"
```

只解析 PDF：

```bash
python -m paper_digest.cli parse --input input_pdfs --output outputs/parsed_text
```

只从解析文本生成 JSON 卡片：

```bash
python -m paper_digest.cli extract --parsed outputs/parsed_text --output outputs/cards_json --topic "你的研究主题"
```

只汇总现有卡片：

```bash
python -m paper_digest.cli aggregate --cards outputs/cards_json --output outputs --topic "你的研究主题"
```

清理生成文件，但不删除输入文件：

```bash
python -m paper_digest.cli clean
```

## 输出文件

`outputs/document_reports_json/`
: 每个输入文件一个独立 JSON 报告。每个报告来自一次单独 API 上下文。

`outputs/document_reports_md/`
: 每个输入文件一个独立 Markdown 报告。

`outputs/search_index.json`
: 所有单文件报告汇总后的检索 JSON，适合搜索、筛选、二次程序处理。

`outputs/folder_summary.md`
: 所有单文件报告汇总后的 Markdown 总结，适合阅读、复制给 AI、继续写作。

`outputs/parsed_text/`
: 每篇论文一个 Markdown 文件，保留 `## Page 1` 这样的页码标题，方便后续证据定位。

`outputs/cards_json/{paper_id}.json`
: 每篇论文一个通过 Pydantic 校验的结构化文献卡片。

`outputs/literature_matrix.xlsx`
: 文献矩阵，便于横向比较。

失败记录写入：

```text
logs/failed_papers.csv
```

某一篇文件失败不会中断整个批处理。

## 控制成本和卡顿

- 先少量文件试跑。
- GUI 中可设置“跳过超过 MB”，默认跳过超过 50 MB 的文件，避免完整教材或超大报告卡住批处理。
- GUI 默认启用“跳过已有报告（断点续跑）”，中断后重开可以继续跑后面的文件。
- 通过 `API_TIMEOUT_SECONDS=300` 控制单次 API 调用等待时间。
- 如果 PDF 都是可选中文本，可以关闭 OCR。
- 重跑前先查看 `logs/failed_papers.csv`。

## Windows exe 入口

仓库不提交 exe。你可以本地生成一个轻量启动器：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_launcher_exe.ps1
```

生成的 `PaperDigestApiBased.exe` 需要本机已有 Python 环境。

完整 PyInstaller 打包：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

