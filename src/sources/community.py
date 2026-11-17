"""Reddit 与 Hacker News 社区热帖（大陆访问需代理）。"""
from datetime import datetime, timezone

from .base import SourceItem, http_get


def fetch_reddit(cfg: dict) -> list:
    rc = cfg["sources"]["reddit"]
    subs = rc.get("subreddits", [])
    limit = rc.get("limit", 5)
    headers = {"User-Agent": "wx-tech-daily/1.0 (personal learning bot)"}
    items = []
    for s in subs:
        try:
            r = http_get(f"https://www.reddit.com/r/{s}/top.json",
                         params={"t": "week", "limit": limit}, headers=headers)
            for c in r.json().get("data", {}).get("children", []):
                d = c.get("data", {})
                if d.get("stickied"):
                    continue
                created = d.get("created_utc", 0)
                items.append(SourceItem(
                    title=d.get("title", ""),
                    url="https://www.reddit.com" + d.get("permalink", ""),
                    summary=(d.get("selftext") or "")[:2000],
                    source="Reddit",
                    published_at=datetime.fromtimestamp(created, tz=timezone.utc).isoformat() if created else "",
                    extra={"score": d.get("score", 0), "sub": s},
                ))
        except Exception as e:
            print(f"[Reddit] r/{s} 抓取失败: {e}")
    return items


def fetch_hn(cfg: dict) -> list:
    hn = cfg["sources"]["hn"]
    kws = hn.get("keywords", [])
    limit = hn.get("limit", 5)
    items = []
    for kw in kws:
        try:
            r = http_get("https://hn.algolia.com/api/v1/search_by_date",
                         params={"query": kw, "tags": "story", "hitsPerPage": limit})
            for h in r.json().get("hits", []):
                title = h.get("title") or h.get("story_title") or ""
                url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                items.append(SourceItem(
                    title=title,
                    url=url,
                    summary="",
                    source="HackerNews",
                    published_at=h.get("created_at", ""),
                    extra={"points": h.get("points", 0)},
                ))
        except Exception as e:
            print(f"[HackerNews] {kw} 抓取失败: {e}")
    return items
