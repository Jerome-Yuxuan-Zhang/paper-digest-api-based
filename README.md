# paper-digest-qwen

`paper-digest-qwen` 是一个本地运行的资料夹批量分析工具。它可以读取一个文件夹中的 PDF、HTML、TXT、MD 文件，并且每个文件都会使用单独的 API 上下文生成一份独立报告，避免把所有资料塞进同一个 context window。

全部文件处理完成后，程序会自动生成两个核心总文件：

- `outputs/search_index.json`：方便检索、二次处理和程序读取的结构化 JSON。
- `outputs/folder_summary.md`：方便人工阅读、复制给 AI 或继续写作的 Markdown 总结。

项目仍然保留原来的论文卡片流程：PDF 解析、文献卡片、Excel 文献矩阵、证据库和综述提示词。

## 开源前提醒

- 不要提交 `.env`、API Key、个人 PDF、生成报告、日志或 exe 构建产物。
- 默认 `.gitignore` 已忽略 `input_pdfs/`、`outputs/`、`logs/`、`build/`、`dist/`、`.env` 和 `*.exe`。
- 程序会把被分析文本发送到你配置的 Qwen API。请只处理你有权发送给第三方模型服务的文件。
- 当前项目适合先作为 `v0.1.0-alpha` 使用；超长文件处理仍以截断/跳过为主，不是完整长文 map-reduce。

它不是普通 PDF 摘要工具。输出重点是研究问题、理论框架、数据来源、方法、识别策略、变量、发现、局限、关键证据页码和引用风险。

## 安装

需要 Python 3.11 或更高版本。

```bash
cd paper-digest-qwen
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

macOS 或 Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

## 配置

如果你已经把 Qwen / DashScope API Key 注入系统环境变量，可以不创建 `.env`。程序会优先读取系统环境变量。

推荐变量名：

```env
DASHSCOPE_API_KEY=你的key
```

兼容变量名：

```env
QWEN_API_KEY=你的key
OPENAI_API_KEY=你的key
```

如果你不想配置系统环境变量，也可以复制 `.env.example` 为 `.env`：

```env
DASHSCOPE_API_KEY=你的key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_TEXT_MODEL=qwen3.5-plus
QWEN_OCR_MODEL=qwen-vl-ocr-latest
```

不要把 API Key 写死进代码。模型名称和 `base_url` 会从系统环境变量、`.env` 或 GUI 当前输入读取，后续可以直接切换其他 Qwen 模型。

默认模型建议：

- `QWEN_TEXT_MODEL=qwen3.5-plus`：推荐用于资料夹报告、长文档分析和结构化 JSON 抽取。
- `QWEN_OCR_MODEL=qwen-vl-ocr-latest`：推荐用于 OCR，始终跟随 Qwen OCR 最新版。

可选文本模型：

- `qwen-plus-latest`：通用平衡方案。
- `qwen-max-latest`：更强但成本更高，适合复杂推理。
- `qwen-turbo-latest`：更便宜更快，适合轻量资料。
- `qwen-long`：旧的长上下文方案；当前默认不再优先使用。

## 中文 GUI

启动高级中文桌面界面：

```bash
python -m paper_digest.gui
```

或安装后运行：

```bash
paper-digest-gui
```

GUI 支持：

- 中文配置面板：资料文件夹、输出文件夹、分析主题、运行模式、OCR 开关。
- Qwen API 配置：默认读取系统环境变量；也可以手动保存到 `.env`。
- 文件队列：显示 PDF、HTML、TXT、MD 的文件名、类型、大小和路径。
- 运行控制：资料夹报告、论文卡片完整运行、只解析 PDF、只生成论文卡片、只汇总论文卡片。
- 实时进度与中文日志。
- 报告预览：直接查看每个文件生成的 JSON 报告。
- 输出文件入口：快速打开检索 JSON、Markdown 总结、单文件报告、JSONL、Excel、证据库和综合提示词。

默认模式是：

```text
资料夹报告（PDF/HTML/TXT/MD）
```

这个模式会读取所选文件夹中的所有支持文件，每个文件单独调用一次 Qwen 文本模型，生成独立报告，然后自动汇总。

## 命令行运行

资料夹报告流程：

```bash
python -m paper_digest.cli folder --input input_pdfs --output outputs --topic "你的分析主题"
```

该命令支持：

```text
pdf, html, htm, txt, md
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

完整流程：

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

清理生成文件，但不删除 `input_pdfs`：

```bash
python -m paper_digest.cli clean
```

## 放置资料文件

把 PDF、HTML、TXT、MD 放入：

```text
input_pdfs/
```

资料夹报告模式会递归扫描该目录下的 `*.pdf`、`*.html`、`*.htm`、`*.txt`、`*.md` 文件。

## 输出文件

`outputs/parsed_text/`
: 每篇论文一个 Markdown 文件，保留 `## Page 1` 这样的页码标题，方便后续证据定位。

`outputs/document_reports_json/`
: 每个输入文件一个独立 JSON 报告。每个报告来自一次单独 API 上下文。

`outputs/document_reports_md/`
: 每个输入文件一个独立 Markdown 报告。

`outputs/search_index.json`
: 所有单文件报告汇总后的检索 JSON，适合搜索、筛选、二次程序处理。

`outputs/folder_summary.md`
: 所有单文件报告汇总后的 Markdown 总结，适合阅读、复制给 AI、继续写作。

`outputs/cards_json/{paper_id}.json`
: 每篇论文一个通过 Pydantic 校验的结构化文献卡片。

`outputs/literature_cards.jsonl`
: 每行一个 `PaperCard` JSON 对象。

`outputs/literature_matrix.xlsx`
: 文献矩阵，便于横向比较。

`outputs/evidence_bank.md`
: 按论文分组的关键证据库。

`outputs/synthesis_prompt.md`
: 可直接复制给 ChatGPT、Claude 或其他 AI 的二次综合提示词。

失败记录写入：

```text
logs/failed_papers.csv
```

某一篇论文失败不会中断整个批处理。

## 为什么先本地抽取，失败后再 OCR

PyMuPDF 本地抽取速度快、成本低。只有当文本过短、乱码比例高、页面平均文本过少或疑似扫描版时，才对低质量页面调用 Qwen OCR。这样可以降低 API 成本，同时兼容扫描版或编码异常的 PDF。

## 控制 API 成本

- 先运行“只解析 PDF”，检查 `outputs/parsed_text` 质量。
- 如果 PDF 都是可选中文本，可以关闭 OCR。
- 先放少量 PDF 试跑。
- 通过 `.env` 中的 `MAX_PAPER_CHARS` 和 `PAPER_CHUNK_CHARS` 控制长文处理。
- 通过 `API_TIMEOUT_SECONDS=300` 控制单次 API 调用等待时间。
- GUI 中可设置“跳过超过 MB”，默认跳过超过 50 MB 的文件，避免完整教材或超大报告卡住批处理。
- GUI 默认启用“跳过已有报告（断点续跑）”，中断后重开可以继续跑后面的文件。
- 重跑前先查看 `logs/failed_papers.csv`。

## 交给其他 AI 做文献综述

运行完成后打开 `outputs/synthesis_prompt.md`，复制给 ChatGPT、Claude 或其他 AI。该文件包含研究主题和压缩后的文献卡片，并要求 AI 做横向比较、研究缺口、理论分组、方法分组、证据冲突和写作框架。

正式引用前，请务必回到原 PDF 核验页码证据。
