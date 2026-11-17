"""OpenAI 兼容大模型客户端（默认 DeepSeek）。"""
import time

import requests


class LLMError(Exception):
    pass


class LLM:
    def __init__(self, cfg: dict):
        self.base_url = cfg["base_url"].rstrip("/")
        self.api_key = cfg.get("api_key", "")
        self.model = cfg.get("model", "deepseek-chat")
        self.temperature = cfg.get("temperature", 0.3)
        self.max_tokens = cfg.get("max_tokens", 4000)
        self.timeout = cfg.get("timeout", 120)

    def chat(self, messages: list, temperature=None, max_tokens=None) -> str:
        if not self.api_key:
            raise LLMError("未配置 llm.api_key，请在 config.yaml 或环境变量 LLM_API_KEY 中填写")

        url = self.base_url + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        last = None
        for attempt in range(4):
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                if r.status_code == 429 or r.status_code >= 500:
                    last = r.text
                    time.sleep(2 ** attempt)
                    continue
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            except requests.RequestException as e:
                last = str(e)
                time.sleep(2 ** attempt)
        raise LLMError(f"大模型调用失败: {last}")
