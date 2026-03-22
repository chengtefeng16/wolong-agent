# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

SOURCE_CANDIDATES = [
    ROOT / "qianqiu_os" / "runtime_views" / "business_judgement" / "wolong_business_judgement_v1.json",
    ROOT / "runtime" / "wolong_business_judgement_v1.json",
    ROOT / "runtime" / "data" / "wolong_business_judgement_v1.json",
    ROOT / "wolong_business_judgement_v1.json",
]

OUTPUT_PATH = ROOT / "runtime" / "views" / "h5_business_judgement_snapshot.json"


def load_source():
    for path in SOURCE_CANDIDATES:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), path
    raise FileNotFoundError(
        "Cannot find wolong_business_judgement_v1.json in expected locations."
    )


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    if isinstance(value, int):
        return value != 0
    return False


def ensure_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [str(value)]


def normalize_customer(item):
    if not isinstance(item, dict):
        item = {}

    return {
        "customer_name": item.get("customer_name")
        or item.get("name")
        or item.get("customer")
        or "Unknown",
        "customer_type": item.get("customer_type", "unknown"),
        "business_stage": item.get("business_stage", "unknown"),
        "risk_level": item.get("risk_level", "unknown"),
        "next_best_action": item.get("next_best_action", "unknown"),
        "handoff_recommended": normalize_bool(
            item.get("handoff_recommended", False)
        ),
        "follow_up_questions": ensure_list(item.get("follow_up_questions", [])),
        "reason_keywords": ensure_list(item.get("reason_keywords", [])),
    }


def extract_customer_list(raw):
    if isinstance(raw, dict):
        if isinstance(raw.get("customers"), list):
            return raw["customers"]
        if isinstance(raw.get("items"), list):
            return raw["items"]
        if isinstance(raw.get("results"), list):
            return raw["results"]

        # 兼容按客户名为 key 的 dict 结构
        dict_values = [v for v in raw.values() if isinstance(v, dict)]
        if dict_values:
            return dict_values

        return [raw]

    if isinstance(raw, list):
        return raw

    return []


def main():
    raw, source_path = load_source()
    customer_list = extract_customer_list(raw)
    normalized = [normalize_customer(item) for item in customer_list]

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(source_path.relative_to(ROOT)),
        "customer_count": len(normalized),
        "customers": normalized,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
