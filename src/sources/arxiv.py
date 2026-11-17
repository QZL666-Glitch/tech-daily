"""arXiv 论文抓取（生物医学工程相关分类）。"""
import urllib.parse

import feedparser

from .base import SourceItem


def _clean(s: str) -> str:
    return " ".join((s or "").split())


def fetch(cfg: dict) -> list:
    a = cfg["sources"]["arxiv"]
    cats = a.get("categories", [])
    q = " OR ".join(f"cat:{c}" for c in cats)
    params = {
        "search_query": q,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": a.get("max_results", 15),
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries:
        authors = ", ".join(auth.get("name", "") for auth in e.get("authors", []))
        items.append(SourceItem(
            title=_clean(e.get("title", "")),
            url=e.get("id", e.get("link", "")),
            summary=_clean(e.get("summary", "")),
            source="arXiv",
            published_at=e.get("published", ""),
            extra={"authors": authors},
        ))
    return items
