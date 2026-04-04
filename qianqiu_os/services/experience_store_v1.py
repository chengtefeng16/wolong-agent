# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
# Project: AgentOS / Wolong Agent System
# ================================================================
"""
经验积累库 V1 — 让 AI 越用越聪明

职责：
  1. 存储：每次回复（AI建议 + 人类审核结果 + 修改内容）
  2. 检索：根据当前场景找到最相关的历史成功案例
  3. 统计：追踪哪类回复效果好，哪类需要改进
  4. 回流：将优质经验注入 LLM prompt，提升下次回复质量

存储结构（JSON 文件，无需外部 DB）：
  qianqiu_os/data/experience_db/
    ├── entries/          每条经验记录（一个 JSON 文件）
    ├── index.json        快速索引（关键词 + 分类统计）
    └── summary.json      全局统计摘要

经验记录字段：
  - id, timestamp
  - customer_msg        客户消息
  - ai_suggested        AI 初始建议
  - human_approved      人类是否采纳（true/false）
  - final_reply         最终发送的回复（可能是人类修改后的）
  - category            客户类型
  - country             目标国家
  - outcome             结果（positive/neutral/negative/unknown）
  - quality_score       人类评分（1-5，可选）
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = PROJECT_ROOT / "qianqiu_os" / "data" / "experience_db"
ENTRIES_DIR = DB_DIR / "entries"
INDEX_PATH = DB_DIR / "index.json"
SUMMARY_PATH = DB_DIR / "summary.json"


def _ensure_dirs():
    ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_experience(
    customer_msg: str,
    ai_suggested: str,
    final_reply: str,
    human_approved: bool,
    category: str = "",
    country: str = "",
    outcome: str = "unknown",
    quality_score: Optional[int] = None,
    extra: Dict = None,
) -> str:
    """
    保存一条回复经验。
    返回经验 ID。
    """
    _ensure_dirs()

    entry_id = str(uuid.uuid4())[:8]
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    # 提取关键词（简单分词）
    keywords = _extract_keywords(customer_msg)

    entry = {
        "id": entry_id,
        "timestamp": ts,
        "customer_msg": customer_msg,
        "ai_suggested": ai_suggested,
        "human_approved": human_approved,
        "human_modified": final_reply != ai_suggested,
        "final_reply": final_reply,
        "category": category,
        "country": country,
        "outcome": outcome,
        "quality_score": quality_score,
        "keywords": keywords,
        **(extra or {}),
    }

    # 保存条目
    entry_path = ENTRIES_DIR / f"{entry_id}.json"
    _write_json(entry_path, entry)

    # 更新索引
    _update_index(entry)

    # 更新摘要
    _update_summary(entry)

    return entry_id


def retrieve_similar(
    customer_msg: str,
    category: str = "",
    country: str = "",
    top_k: int = 3,
    only_approved: bool = True,
) -> List[Dict]:
    """
    根据当前场景检索最相关的成功经验。
    用关键词匹配（后续可升级为向量检索）。
    """
    _ensure_dirs()
    index = _read_json(INDEX_PATH, {"entries": []})
    entries_meta = index.get("entries", [])

    if not entries_meta:
        return []

    keywords = set(_extract_keywords(customer_msg))
    scored = []

    for meta in entries_meta:
        if only_approved and not meta.get("human_approved", False):
            continue

        # 关键词重叠分数
        entry_kw = set(meta.get("keywords", []))
        kw_overlap = len(keywords & entry_kw)

        # 国家匹配加分
        country_bonus = 2 if meta.get("country") == country else 0

        # 分类匹配加分
        cat_bonus = 1 if meta.get("category") == category else 0

        score = kw_overlap + country_bonus + cat_bonus
        if score > 0:
            scored.append((score, meta))

    # 按分数降序，取 top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    top_entries = scored[:top_k]

    # 加载完整条目
    results = []
    for _, meta in top_entries:
        entry_path = ENTRIES_DIR / f"{meta['id']}.json"
        entry = _read_json(entry_path, meta)
        results.append({
            "customer_msg": entry.get("customer_msg", ""),
            "approved_reply": entry.get("final_reply", ""),
            "category": entry.get("category", ""),
            "country": entry.get("country", ""),
            "outcome": entry.get("outcome", "unknown"),
            "quality_score": entry.get("quality_score"),
        })

    return results


def get_summary() -> Dict[str, Any]:
    """返回全局经验统计摘要"""
    return _read_json(SUMMARY_PATH, {
        "total_entries": 0,
        "approved_count": 0,
        "modified_count": 0,
        "approval_rate": 0.0,
        "by_category": {},
        "by_country": {},
        "top_keywords": [],
        "last_updated": None,
    })


def get_recent_entries(limit: int = 10) -> List[Dict]:
    """返回最近 N 条经验（用于展示/审计）"""
    _ensure_dirs()
    index = _read_json(INDEX_PATH, {"entries": []})
    entries_meta = index.get("entries", [])

    # 按时间倒序
    sorted_meta = sorted(entries_meta, key=lambda x: x.get("timestamp", ""), reverse=True)
    recent = sorted_meta[:limit]

    results = []
    for meta in recent:
        entry_path = ENTRIES_DIR / f"{meta['id']}.json"
        entry = _read_json(entry_path, meta)
        results.append(entry)

    return results


def mark_outcome(entry_id: str, outcome: str, quality_score: int = None):
    """标记某条经验的最终效果（如客户回复了 → positive）"""
    entry_path = ENTRIES_DIR / f"{entry_id}.json"
    if not entry_path.exists():
        return False

    entry = _read_json(entry_path, {})
    entry["outcome"] = outcome
    if quality_score is not None:
        entry["quality_score"] = quality_score
    _write_json(entry_path, entry)

    # 重新生成摘要
    _rebuild_summary()
    return True


# ── 内部工具函数 ──

def _extract_keywords(text: str) -> List[str]:
    """简单关键词提取"""
    if not text:
        return []

    # 常见业务关键词
    business_kw = [
        "suv", "sedan", "pickup", "van", "truck", "car", "vehicle",
        "price", "cost", "quote", "how much", "budget",
        "quantity", "units", "pieces", "bulk", "monthly", "regularly",
        "ship", "delivery", "logistics", "freight",
        "dealer", "resale", "wholesale", "import",
        "hello", "hi", "good morning",
        "toyota", "honda", "nissan", "bmw", "mercedes", "lexus",
        "left hand", "right hand", "steering",
        "diesel", "petrol", "electric", "hybrid",
    ]

    text_lower = text.lower()
    found = [kw for kw in business_kw if kw in text_lower]

    # 数量词
    import re
    numbers = re.findall(r'\b(\d+)\s*(units?|cars?|vehicles?|台|辆)', text_lower)
    if numbers:
        found.append("quantity_mentioned")

    return found


def _update_index(entry: Dict):
    """更新快速索引"""
    index = _read_json(INDEX_PATH, {"entries": []})
    entries = index.get("entries", [])

    # 更新或添加条目元数据
    meta = {
        "id": entry["id"],
        "timestamp": entry["timestamp"],
        "human_approved": entry["human_approved"],
        "category": entry.get("category", ""),
        "country": entry.get("country", ""),
        "keywords": entry.get("keywords", []),
        "outcome": entry.get("outcome", "unknown"),
    }

    existing_ids = [e["id"] for e in entries]
    if entry["id"] in existing_ids:
        idx = existing_ids.index(entry["id"])
        entries[idx] = meta
    else:
        entries.insert(0, meta)  # 最新的放前面

    # 只保留最近 500 条的索引
    index["entries"] = entries[:500]
    _write_json(INDEX_PATH, index)


def _update_summary(entry: Dict):
    """更新摘要统计"""
    summary = _read_json(SUMMARY_PATH, {
        "total_entries": 0,
        "approved_count": 0,
        "modified_count": 0,
        "by_category": {},
        "by_country": {},
        "keyword_freq": {},
    })

    summary["total_entries"] = summary.get("total_entries", 0) + 1
    if entry.get("human_approved"):
        summary["approved_count"] = summary.get("approved_count", 0) + 1
    if entry.get("human_modified"):
        summary["modified_count"] = summary.get("modified_count", 0) + 1

    # 分类统计
    cat = entry.get("category", "unknown")
    by_cat = summary.get("by_category", {})
    by_cat[cat] = by_cat.get(cat, 0) + 1
    summary["by_category"] = by_cat

    # 国家统计
    cntry = entry.get("country", "unknown")
    by_cntry = summary.get("by_country", {})
    by_cntry[cntry] = by_cntry.get(cntry, 0) + 1
    summary["by_country"] = by_cntry

    # 关键词频次
    kw_freq = summary.get("keyword_freq", {})
    for kw in entry.get("keywords", []):
        kw_freq[kw] = kw_freq.get(kw, 0) + 1
    summary["keyword_freq"] = kw_freq

    # 计算采纳率
    total = summary["total_entries"]
    if total > 0:
        summary["approval_rate"] = round(summary["approved_count"] / total, 3)

    summary["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # top 关键词
    sorted_kw = sorted(kw_freq.items(), key=lambda x: x[1], reverse=True)
    summary["top_keywords"] = [{"keyword": k, "count": v} for k, v in sorted_kw[:10]]

    _write_json(SUMMARY_PATH, summary)


def _rebuild_summary():
    """从所有条目重建摘要（用于 mark_outcome 后更新）"""
    _ensure_dirs()
    entries = list(ENTRIES_DIR.glob("*.json"))

    summary = {
        "total_entries": 0,
        "approved_count": 0,
        "modified_count": 0,
        "by_category": {},
        "by_country": {},
        "keyword_freq": {},
    }

    for ep in entries:
        try:
            entry = _read_json(ep, {})
            summary["total_entries"] += 1
            if entry.get("human_approved"):
                summary["approved_count"] += 1
            if entry.get("human_modified"):
                summary["modified_count"] += 1

            cat = entry.get("category", "unknown")
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1

            cntry = entry.get("country", "unknown")
            summary["by_country"][cntry] = summary["by_country"].get(cntry, 0) + 1

            for kw in entry.get("keywords", []):
                summary["keyword_freq"][kw] = summary["keyword_freq"].get(kw, 0) + 1
        except Exception:
            continue

    total = summary["total_entries"]
    summary["approval_rate"] = round(summary["approved_count"] / total, 3) if total > 0 else 0.0
    summary["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

    sorted_kw = sorted(summary["keyword_freq"].items(), key=lambda x: x[1], reverse=True)
    summary["top_keywords"] = [{"keyword": k, "count": v} for k, v in sorted_kw[:10]]

    _write_json(SUMMARY_PATH, summary)
