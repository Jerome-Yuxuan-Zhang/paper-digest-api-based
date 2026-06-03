# 安全说明

## API Key

请通过系统环境变量或本地 `.env` 配置 API Key。不要把 `.env` 或任何密钥提交到公开仓库。

支持的变量名：

```text
API_KEY
API_BASE_URL
TEXT_MODEL
OCR_MODEL
```

同时兼容旧变量名 `DASHSCOPE_API_KEY`、`QWEN_API_KEY`、`OPENAI_API_KEY`、`QWEN_BASE_URL`、`QWEN_TEXT_MODEL`、`QWEN_OCR_MODEL`。

## 文件与隐私

程序会读取用户选择的本地文件，并把文件内容发送给配置的 OpenAI-compatible API 用于分析。请不要处理你无权上传到第三方 API 的文件。

程序不会主动上传到 GitHub、云盘或其他服务；但模型 API 调用本身会把被分析文本发送给模型服务商。

## 报告输出

生成的 `outputs/`、`logs/` 和 `input_pdfs/` 默认被 `.gitignore` 忽略。开源或提交前请确认这些目录没有进入版本控制。

## 漏洞反馈

如果发现密钥泄露、路径泄露、误上传用户文件等安全问题，请先私下通知维护者，不要在公开 issue 中贴出敏感内容。
