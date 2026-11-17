"""微信公众平台接口封装。

重要前提：自 2025 年 7 月起，微信已回收「个人主体账号、企业主体未认证账号
及不支持认证的账号」的发布能力接口权限，个人订阅号调用会返回
48001（api unauthorized）。本模块保留完整实现，只有「已认证的企业主体
公众号（蓝V）」才能走通；个人号请使用 fallback 手动发布。
"""
import time

import requests


class WeChatError(Exception):
    pass


class WeChatClient:
    def __init__(self, cfg: dict):
        w = cfg["wechat"]
        self.appid = w.get("appid", "")
        self.appsecret = w.get("appsecret", "")
        self.author = w.get("author", "") or "AI 科技日报"
        self.thumb_image = w.get("thumb_image", "")
        self.need_open_comment = int(w.get("need_open_comment", 0))
        self._token = None
        self._expire = 0.0

    def get_token(self) -> str:
        if self._token and time.time() < self._expire - 120:
            return self._token
        if not self.appid or not self.appsecret:
            raise WeChatError("未配置 wechat.appid / wechat.appsecret")
        r = requests.get("https://api.weixin.qq.com/cgi-bin/token", params={
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret,
        }, timeout=20)
        data = r.json()
        if "access_token" not in data:
            raise WeChatError(f"获取 access_token 失败: {data}")
        self._token = data["access_token"]
        self._expire = time.time() + int(data.get("expires_in", 7200))
        return self._token

    def _post(self, path: str, payload: dict) -> dict:
        token = self.get_token()
        r = requests.post(f"https://api.weixin.qq.com{path}",
                          params={"access_token": token}, json=payload, timeout=30)
        data = r.json()
        if data.get("errcode", 0) != 0:
            raise WeChatError(f"{path} 调用失败: {data}")
        return data

    def upload_thumb(self, image_path: str) -> str:
        token = self.get_token()
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://api.weixin.qq.com/cgi-bin/material/add_material",
                params={"access_token": token},
                data={"type": "image"},
                files={"media": f},
                timeout=60,
            )
        data = r.json()
        if "media_id" not in data:
            raise WeChatError(f"上传封面失败: {data}")
        return data["media_id"]

    def publish_article(self, title: str, content_html: str, digest: str = "") -> dict:
        if not self.thumb_image:
            raise WeChatError("自动发布需要配置 wechat.thumb_image（封面图本地路径）")
        thumb_media_id = self.upload_thumb(self.thumb_image)
        article = {
            "title": title,
            "author": self.author,
            "digest": (digest or title)[:120],
            "content": content_html,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": self.need_open_comment,
            "only_fans_can_comment": 0,
        }
        media_id = self._post("/cgi-bin/draft/add", {"articles": [article]})["media_id"]
        return self._post("/cgi-bin/freepublish/submit", {"media_id": media_id})
