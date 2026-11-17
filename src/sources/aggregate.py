"""汇总所有来源 + 相关性评分 + 去重 + 过滤历史。"""
from .. import storage
from . import arxiv, community, github, gitee, rss

KEYWORDS = {
    "生物医学工程": ["生物医学", "医疗", "医学成像", "脑机接口", "可穿戴", "传感器",
                     "假肢", "植入", "组织工程", "biomedical", "medical", "wearable",
                     "implant", "bio", "eeg", "ecg", "mri", "ultrasound", "bme"],
    "嵌入式": ["stm32", "esp32", "嵌入式", "单片机", "mcu", "rtos", "freertos", "arm",
               "固件", "gpio", "adc", "pwm", "embedded", "microcontroller", "firmware"],
    "3D打印/硬件": ["3d打印", "3d printing", "增材制造", "cad", "fdm", "sla", "prusa",
                    "voron", "pcb", "外壳", "机械"],
    "AI/模型": ["深度学习", "神经网络", "大模型", "模型", "算法", "dataset", "llm", "transformer"],
}


def _score(item) -> int:
    title = (item.title or "").lower()
    body = ((item.summary or "") + " " + (item.content or "")).lower()
    score = 0
    for kws in KEYWORDS.values():
        for kw in kws:
            if kw in title:
                score += 3
            elif kw in body:
                score += 1
    # arXiv 来源本身已限定在生物医学工程分类，给基础分避免被关键词误过滤
    if (item.source or "") == "arXiv":
        score += 3
    return score


def collect(cfg: dict) -> list:
    data_dir = cfg["run"]["data_dir"]
    storage.init_db(data_dir)

    all_items = []
    src = cfg["sources"]
    if src.get("github", {}).get("enabled"):
        all_items += github.fetch(cfg)
    if src.get("gitee", {}).get("enabled"):
        all_items += gitee.fetch(cfg)
    if src.get("arxiv", {}).get("enabled"):
        all_items += arxiv.fetch(cfg)
    if src.get("rss", {}).get("enabled"):
        all_items += rss.fetch(cfg)
    if src.get("reddit", {}).get("enabled"):
        all_items += community.fetch_reddit(cfg)
    if src.get("hn", {}).get("enabled"):
        all_items += community.fetch_hn(cfg)

    seen_keys = set()
    candidates = []
    for it in all_items:
        key = it.url or ("h:" + (it.title or ""))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if storage.is_seen(data_dir, it):
            continue
        candidates.append(it)

    candidates.sort(key=lambda x: (_score(x), x.published_at or ""), reverse=True)
    max_items = cfg["run"].get("max_items", 6)
    # 先按相关性排序，再限制单一来源占比，避免 arXiv/GitHub 某一家刷屏
    cap = max(2, max_items // 2)
    final = []
    counts = {}
    for c in candidates:
        if _score(c) < 2:
            continue
        s = c.source or "other"
        if counts.get(s, 0) >= cap:
            continue
        counts[s] = counts.get(s, 0) + 1
        final.append(c)
        if len(final) >= max_items:
            return final
    # 若来源偏少，第二遍补齐剩余名额
    chosen_ids = {id(c) for c in final}
    for c in candidates:
        if _score(c) < 2 or id(c) in chosen_ids:
            continue
        final.append(c)
        if len(final) >= max_items:
            break
    return final
