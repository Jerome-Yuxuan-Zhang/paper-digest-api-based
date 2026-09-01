# Paper Digest API Based — 使用说明

感谢使用！这是一个本地批量资料分析工具，可读取 **PDF / HTML / TXT / MD** 文件，调用 OpenAI-compatible API 为每个文件生成独立报告，最后汇总成检索 JSON 和 Markdown 总结。

---

## 第 1 步：把程序放到单独的文件夹

请把这个 `PaperDigestApiBased.exe` 放在一个**单独的文件夹**里，例如：

```
D:\PaperDigest\PaperDigestApiBased.exe
```

不要直接放在桌面，也不要和其它大量文件混在一起。

> 原因：程序运行后会在 exe 所在文件夹自动创建 `input_pdfs`、`outputs`、`logs` 等子目录，并把 API 配置保存为 `.env`。单独放一个文件夹更整洁、更好管理。

## 第 2 步：双击运行

双击 `PaperDigestApiBased.exe`。

- 首次启动会先解压（约几秒到几十秒），请耐心等待，不要重复双击。
- 若 Windows 弹出「Windows 已保护你的电脑」（SmartScreen），点「更多信息」→「仍要运行」。

## 第 3 步：配置 API Key

在左侧「API 配置」区域填写：

| 项目 | 值 |
|------|-----|
| API Key | 你的 DashScope / Qwen API Key |
| Base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 文本模型 | `qwen3.8-flash`（默认） |
| OCR 模型 | `qwen-vl-ocr-latest` |

> 可点「保存 .env 配置」保存到本地，下次启动自动读取；也可点「重新读取系统环境变量」读取系统环境变量。

## 第 4 步：放入文件并开始

1. 把要分析的 PDF / HTML / TXT / MD 文件放进 `input_pdfs` 文件夹（或点「资料文件夹」选择其它文件夹）。
2. 填写「分析主题」（可留空）。
3. 选择「运行模式」（默认「资料夹报告」即可）。
4. 如需提速，可调大「并发路数（2~100）」。
5. 点「开始运行」。

## 第 5 步：查看结果

结果在 `outputs` 文件夹：

| 文件 / 文件夹 | 说明 |
|---------------|------|
| `search_index.json` | 结构化检索索引 |
| `folder_summary.md` | Markdown 总结（适合阅读 / 复制给 AI） |
| `document_reports_json/` | 每个文件的独立 JSON 报告 |
| `document_reports_md/` | 每个文件的独立 Markdown 报告 |

---

## 常见问题

- **文件太多 / 太大**：左侧可设置「跳过超过 MB」；也可关闭 OCR（若 PDF 是可选中文本）。
- **想断点续跑**：勾选「跳过已有报告」，中断后重开可接着跑。
- **某个文件失败**：不影响其它文件，失败记录见 `logs\failed_papers.csv`。
- **程序崩溃**：会在 exe 旁生成 `paper_digest_error.log`，便于排查。

## 许可证

本项目以 MIT 许可证开源；第三方组件许可证清单见 `THIRD_PARTY_NOTICES.md`。其中 PyMuPDF 为 AGPL-3.0 或商业授权（双许可）。
