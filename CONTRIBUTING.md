# 贡献指南

感谢你愿意改进 `paper-digest-qwen`。

## 本地开发

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python -m pytest -q
```

macOS 或 Linux：

```bash
source .venv/bin/activate
```

## 开发约定

- 不要提交 `.env`、API Key、个人 PDF、生成报告、`build/`、`dist/` 或 `.exe`。
- 新增功能时尽量补测试。
- GUI、CLI 和 README 面向中文用户，新增用户可见文案请优先使用中文。
- 涉及模型名称、API 地址或平台规则时，请以官方文档为准。

## 提交前检查

```bash
python -m pytest -q
rg -n "sk-|DASHSCOPE_API_KEY=.+|OPENAI_API_KEY=.+|QWEN_API_KEY=.+" .
```

第二条命令用于粗略检查是否误提交密钥。它可能有误报，请人工确认。

