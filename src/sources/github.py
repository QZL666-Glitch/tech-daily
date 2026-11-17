"""GitHub 仓库搜索：按主题抓取近期活跃项目。"""
import time
from datetime import datetime, timedelta, timezone

from .base import SourceItem, http_get


def fetch(cfg: dict) -> list:
    gh = cfg["sources"]["github"]
    token = gh.get("token") or ""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    days = cfg["run"].get("days_back", 7)
    date_str = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    items = []
    for topic in gh.get("topics", []):
        query = f"topic:{topic} pushed:>={date_str}"
        try:
            r = http_get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "updated", "order": "desc",
                        "per_page": gh.get("per_topic", 5)},
                headers=headers,
            )
            for repo in r.json().get("items", []):
                name = repo.get("full_name", "")
                if name.endswith(".github.io"):
                    continue  # 跳过个人主页类仓库
                desc = repo.get("description") or ""
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language") or "?"
                topics = ",".join(repo.get("topics") or [])
                items.append(SourceItem(
                    title=name,
                    url=repo.get("html_url", ""),
                    summary=f"{desc} | ⭐{stars} | 语言:{lang} | 主题:{topics}",
                    source="GitHub",
                    published_at=repo.get("updated_at", ""),
                    extra={"stars": stars, "language": lang},
                ))
        except Exception as e:
            print(f"[GitHub] 主题 {topic} 抓取失败: {e}")
        time.sleep(2)  # 未认证搜索限速 10 次/分钟
    return items
