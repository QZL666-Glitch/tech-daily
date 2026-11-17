"""Gitee 仓库搜索（国内可直接访问）。"""
import time

from .base import SourceItem, http_get


def fetch(cfg: dict) -> list:
    g = cfg["sources"].get("gitee", {})
    keywords = g.get("keywords", [])
    per = g.get("per_keyword", 5)
    access_token = g.get("access_token", "")

    items = []
    for kw in keywords:
        try:
            params = {"q": kw, "sort": "stars_count", "order": "desc", "per_page": per}
            if access_token:
                params["access_token"] = access_token
            r = http_get(
                "https://gitee.com/api/v5/search/repositories",
                params=params,
            )
            for repo in r.json() or []:
                desc = repo.get("description") or ""
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language") or "?"
                items.append(SourceItem(
                    title=repo.get("full_name", repo.get("name", "")),
                    url=repo.get("html_url", ""),
                    summary=f"{desc} | ⭐{stars} | 语言:{lang}",
                    source="Gitee",
                    published_at=repo.get("pushed_at") or repo.get("updated_at") or "",
                    extra={"stars": stars},
                ))
        except Exception as e:
            print(f"[Gitee] {kw} 抓取失败: {e}")
        time.sleep(1)
    return items
