"""配置加载：config.yaml + 环境变量覆盖（便于 GitHub Actions / 云服务器）。"""
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "run": {
        "mode": "generate",
        "max_items": 6,
        "days_back": 7,
        "output_dir": str(ROOT / "output"),
        "data_dir": str(ROOT / "data"),
    },
    "llm": {
        "base_url": "https://api.deepseek.com",
        "api_key": "",
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 120,
    },
    "sources": {
        "github": {
            "enabled": True,
            "token": "",
            "topics": ["stm32", "esp32", "embedded", "biomedical",
                       "medical-device", "3d-printing", "wearable", "bioinformatics"],
            "per_topic": 5,
        },
        "gitee": {
            "enabled": True,
            "access_token": "",
            "keywords": ["stm32", "esp32", "嵌入式", "3d打印", "生物医学"],
            "per_keyword": 5,
        },
        "arxiv": {
            "enabled": True,
            "categories": ["physics.med-ph", "q-bio.QM", "eess.SP", "eess.IV"],
            "max_results": 15,
        },
        "rss": {
            "enabled": False,
            "feeds": ["https://sspai.com/feed", "https://36kr.com/feed"],
        },
        "reddit": {
            "enabled": False,
            "subreddits": ["embedded", "esp32", "3Dprinting", "BiomedicalEngineers"],
            "limit": 5,
        },
        "hn": {
            "enabled": False,
            "keywords": ["stm32", "esp32", "embedded", "3d printing", "biomedical"],
            "limit": 5,
        },
    },
    "wechat": {
        "enabled": False,
        "appid": "",
        "appsecret": "",
        "author": "",
        "thumb_image": "",
        "need_open_comment": 0,
    },
    "schedule": {"enabled": True, "hour": 8, "minute": 0},
    "site": {
        "title": "我的专业科技日报",
        "subtitle": "生物医学工程 · 嵌入式 STM32/ESP32 · 3D打印 · 开源项目",
        "output_dir": str(ROOT / "site"),
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def load_config() -> dict:
    cfg = DEFAULTS
    path = ROOT / "config.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(DEFAULTS, user_cfg)

    # 环境变量覆盖（密钥不要写进文件、不要提交到 Git）
    if os.environ.get("LLM_API_KEY"):
        cfg["llm"]["api_key"] = os.environ["LLM_API_KEY"]
    if os.environ.get("LLM_BASE_URL"):
        cfg["llm"]["base_url"] = os.environ["LLM_BASE_URL"]
    if os.environ.get("LLM_MODEL"):
        cfg["llm"]["model"] = os.environ["LLM_MODEL"]
    if os.environ.get("WECHAT_APPID"):
        cfg["wechat"]["appid"] = os.environ["WECHAT_APPID"]
    if os.environ.get("WECHAT_APPSECRET"):
        cfg["wechat"]["appsecret"] = os.environ["WECHAT_APPSECRET"]
    if os.environ.get("WECHAT_ENABLED"):
        cfg["wechat"]["enabled"] = _to_bool(os.environ["WECHAT_ENABLED"])
    if os.environ.get("GITHUB_TOKEN"):
        cfg["sources"]["github"]["token"] = os.environ["GITHUB_TOKEN"]

    for key in ("output_dir", "data_dir"):
        cfg["run"][key] = str(Path(cfg["run"][key]).expanduser())
    cfg["site"]["output_dir"] = str(Path(cfg["site"]["output_dir"]).expanduser())
    return cfg
