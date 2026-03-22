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
from typing import Dict, Any, Optional

BASE = Path("knowledge")

def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def policy_check(destination_country: str, vehicle: Dict[str, Any]) -> Dict[str, Any]:
    """
    政策校验接口（预留）：
    - 未来会根据 destination_country + vehicle 字段做判断
    - 现在先返回 unknown，不影响现有系统稳定
    """
    key = destination_country.strip().lower().replace(" ", "_") or "default"
    data = _read_json(BASE / "policies" / f"{key}.json") or _read_json(BASE / "policies" / "default.json") or {}

    # 先只返回占位结构（以后再填规则）
    return {
        "status": data.get("status", "unknown"),     # compliant / restricted / unknown
        "notes": data.get("notes", "policy rules not configured yet")
    }

def estimate_domestic_logistics(origin_city: str, export_hub: str, units: int = 1) -> Dict[str, Any]:
    """
    国内物流费用接口（预留）：
    - 例如：上海 -> 霍尔果斯 / 上海港
    - 现在返回占位，不做真实推断
    """
    data = _read_json(BASE / "costs" / "domestic" / "default.json") or {}
    return {
        "currency": data.get("currency", "CNY"),
        "estimate": data.get("estimate", None),      # None 表示暂不估价
        "notes": data.get("notes", "domestic logistics pricing not configured yet"),
        "params": {"origin_city": origin_city, "export_hub": export_hub, "units": units}
    }

def estimate_international_logistics(route: str, units: int = 1) -> Dict[str, Any]:
    """
    国际物流费用接口（预留）：
    - 例如：上海港 -> 阿尔及尔 / 霍尔果斯 -> 阿拉木图
    - 现在返回占位
    """
    data = _read_json(BASE / "costs" / "international" / "default.json") or {}
    return {
        "currency": data.get("currency", "USD"),
        "estimate": data.get("estimate", None),
        "notes": data.get("notes", "international logistics pricing not configured yet"),
        "params": {"route": route, "units": units}
    }

def estimate_customs_and_export_fees(destination_country: str, units: int = 1) -> Dict[str, Any]:
    """
    报关 / 清关 / 检测等费用接口（预留）：
    - 例如：报关代理费、检测费、文件费等
    - 现在返回占位
    """
    key = destination_country.strip().lower().replace(" ", "_") or "default"
    data = _read_json(BASE / "costs" / "customs" / f"{key}.json") or _read_json(BASE / "costs" / "customs" / "default.json") or {}
    return {
        "currency": data.get("currency", "USD"),
        "estimate": data.get("estimate", None),
        "notes": data.get("notes", "customs/export fees not configured yet"),
        "params": {"destination_country": destination_country, "units": units}
    }

def export_context(destination_country: str, vehicle: Dict[str, Any], units: int = 1) -> Dict[str, Any]:
    """
    L8.1 统一出口因素接口（四大模块汇总）
    """
    return {
        "policy": policy_check(destination_country, vehicle),
        "domestic_logistics": estimate_domestic_logistics(origin_city="Shanghai", export_hub="Shanghai Port", units=units),
        "international_logistics": estimate_international_logistics(route="TBD", units=units),
        "customs_export_fees": estimate_customs_and_export_fees(destination_country=destination_country, units=units)
    }


