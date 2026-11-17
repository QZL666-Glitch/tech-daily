"""通用 RSS 抓取。"""
import re
from datetime import datetime, timedelta, timezone

import feedparser

from .base import SourceItem


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "").strip()


def _parse_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        v = entry.get(key)
        if v:
            return datetime(*v[:6], tzinfo=timezone.utc)
    return None


def fetch(cfg: dict) -> list:
    feeds = cfg["sources"]["rss"].get("feeds", [])
    days = cfg["run"].get("days_back", 7)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    items = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:20]:
                pub = _parse_time(e)
                if pub and pub < cutoff:
                    continue
                items.append(SourceItem(
                    title=(e.get("title") or "").strip(),
                    url=e.get("link", ""),
                    summary=_strip_html(e.get("summary") or e.get("description") or ""),
                    source="RSS",
                    published_at=pub.isoformat() if pub else "",
                ))
        except Exception as e:
            print(f"[RSS] {url} 抓取失败: {e}")
    return items
