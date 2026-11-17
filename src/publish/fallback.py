"""手动发布兜底：把每篇文章落盘为 .md / .html / .txt。"""
import re
from datetime import datetime
from pathlib import Path

from .html import to_wechat_html


def _safe_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("_")
    return (name[:40] or "article")


def save_article(article: dict, output_dir: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    base = _safe_filename(article["title"])
    out = Path(output_dir) / today
    out.mkdir(parents=True, exist_ok=True)

    md_path = out / f"{base}.md"
    html_path = out / f"{base}.html"
    txt_path = out / f"{base}.txt"

    md_path.write_text(article["markdown"], encoding="utf-8")
    html_path.write_text(to_wechat_html(article["markdown"]), encoding="utf-8")
    txt_path.write_text(article["markdown"], encoding="utf-8")

    return {"md": str(md_path), "html": str(html_path), "txt": str(txt_path)}
