from __future__ import annotations

import json

from .schemas import PAPER_CARD_JSON_SCHEMA


PAPER_ANALYSIS_SYSTEM_PROMPT = """你是严谨的学术论文审稿人与文献综述助手。
你只能基于用户提供的论文文本进行分析。
不得用常识补全缺失信息，不得编造作者、年份、期刊、数据、方法或结论。
如果原文没有明确说明，必须写 "not stated" 或空列表。
你的任务不是泛泛总结，而是提取后续学术写作可用的结构化信息。"""


PAPER_ANALYSIS_USER_PROMPT = """下面是一篇学术论文的解析文本。
用户研究主题：

{topic}

只返回严格 JSON。不要输出 Markdown、解释文字或代码块。
JSON 必须符合以下 schema：

{schema}

必须提取：
1. 论文基本信息：题目、作者、年份、期刊或来源。
2. 研究问题。
3. 核心论点。
4. 理论框架、机制或分析框架。
5. 数据来源。
6. 样本时间。
7. 样本范围，例如国家、行业、企业或样本量。
8. 方法论。
9. 识别策略；如果没有，写 "not stated"。
10. 变量设计。
11. 主要发现，并尽量区分作者声称与数据支持的结果。
12. 稳健性检验；如果没有，写空列表。
13. 机制分析；如果没有，写空列表。
14. 作者承认的局限，以及可从文本直接判断的局限。
15. 与用户研究主题的关系。
16. 可用于论文哪些部分，例如 introduction、literature review、methodology、discussion、background、counterargument。
17. 不适合引用的地方，例如样本不匹配、方法较弱、结论过泛。
18. 3 到 8 条可回原文核验的关键证据，尽量标注页码。
19. 引用风险：low、medium 或 high，并说明原因。

论文 ID：{paper_id}
文件名：{file_name}

论文文本：

{paper_text}"""


CHUNK_ANALYSIS_PROMPT = """请从这段论文文本中提取与用户研究主题相关的局部证据。
返回 JSON，字段包括：basic_info, claims, methods, data, variables, findings, limitations, evidence。
保留类似 "## Page 3" 的页码来源。不得编造信息。

主题：{topic}
论文 ID：{paper_id}
文件名：{file_name}

文本块：
{chunk_text}"""


REDUCE_ANALYSIS_PROMPT = """请把这些分块笔记综合成一个 PaperCard JSON 对象。
只能使用这里提供的分块笔记。保留页码来源。如果字段没有说明，写 "not stated" 或 []。
只返回 JSON，并符合以下 schema：

{schema}

主题：{topic}
论文 ID：{paper_id}
文件名：{file_name}

分块笔记：
{chunk_notes}"""


def paper_prompt(topic: str, paper_id: str, file_name: str, paper_text: str) -> str:
    return PAPER_ANALYSIS_USER_PROMPT.format(
        topic=topic,
        schema=json.dumps(PAPER_CARD_JSON_SCHEMA, ensure_ascii=False),
        paper_id=paper_id,
        file_name=file_name,
        paper_text=paper_text,
    )
