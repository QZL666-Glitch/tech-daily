"""文章生成编排：润色 → AI 解读 → 汇总 Markdown。"""
import re

from . import prompts
from .client import LLM


def _split_title(raw: str):
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    title = ""
    body_start = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^标题[:：]\s*(.+)$", ln)
        if m:
            title = m.group(1).strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:])
    return title, body


def generate(item, cfg: dict) -> dict:
    llm = LLM(cfg["llm"])

    rewrite_msgs = [
        {"role": "system", "content": prompts.REWRITE_SYSTEM},
        {"role": "user", "content": prompts.REWRITE_USER.format(
            source=item.source, title=item.title, url=item.url, content=item.text())},
    ]
    raw = llm.chat(rewrite_msgs)
    title, body = _split_title(raw)
    if not title:
        title = item.title
    if not body:
        body = raw

    explain_msgs = [
        {"role": "system", "content": prompts.EXPLAIN_SYSTEM},
        {"role": "user", "content": prompts.EXPLAIN_USER.format(title=title, body=body)},
    ]
    explain = llm.chat(explain_msgs, temperature=0.3)

    md = _assemble(title, body, explain, item)
    return {"title": title, "markdown": md, "item": item}


def _assemble(title: str, body: str, explain: str, item) -> str:
    source_line = f"来源：{item.source}"
    if item.published_at:
        source_line += f" · {item.published_at[:10]}"
    return "\n\n".join([
        f"# {title}",
        f"*{source_line}*",
        body,
        "---",
        explain,
        "---",
        "**参考来源**",
        f"- {item.title}：{item.url}",
    ])
