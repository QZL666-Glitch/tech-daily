"""来源公共类型与 HTTP 工具。"""
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


class FetchError(Exception):
    pass


@dataclass
class SourceItem:
    title: str
    url: str
    summary: str = ""
    content: str = ""
    source: str = ""
    published_at: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def text(self, limit: int = 4000) -> str:
        parts = [self.summary, self.content]
        joined = "\n\n".join(p for p in parts if p and p.strip()).strip()
        if not joined:
            joined = self.title
        return joined[:limit]


def http_get(url: str, params: Optional[dict] = None,
             headers: Optional[dict] = None, timeout: int = 20, retries: int = 2):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    last_err: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_err = e
            time.sleep(1.5 * (i + 1))
    raise FetchError(f"请求失败 {url}: {last_err}")
