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
from datetime import datetime

POLICY_DIR = Path("knowledge/policies/countries")


def _today_date():
    return datetime.utcnow().date()


def _today_ymd():
    return datetime.utcnow().strftime("%Y-%m-%d")


def _parse_euro(emission_standard):
    if not emission_standard:
        return None
    s = emission_standard.strip().lower().replace(" ", "").replace("_", "")
    if "euro" not in s:
        return None
    idx = s.find("euro")
    tail = s[idx + 4 :]
    digits = "".join(ch for ch in tail if ch.isdigit())
    return int(digits) if digits else None


def load_policy(country_code_or_name):
    key = (country_code_or_name or "").strip().lower()

    candidates = [
        f"{key}.json",
        "ru.json" if key in ("russia", "россия", "рф", "russian federation") else None,
        "dz.json" if key in ("algeria",) else None,
        "gh.json" if key in ("ghana",) else None,
    ]
    candidates = [c for c in candidates if c]

    for name in candidates:
        p = POLICY_DIR / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))

    # === 强制过期提示机制 ===
    if policy_health.get("is_outdated"):
        warnings.append("⚠ 当前政策数据已超过复核周期。")
        warnings.append("⚠ 本判断仅供参考，必须人工复核确认。")

    # 风险等级升级
        if risk_level == "low":
            risk_level = "medium"
        elif risk_level == "medium":
            risk_level = "high"
    return {
        "policy_meta": {
            "schema_version": "9.4",
            "data_status": "unknown",
            "last_verified_at": None,
            "last_checked_at": None,
            "next_review_due": None,
            "small_update_cycle_days": 3,
            "major_update_cycle_days": 7,
            "confidence_level": 0.0,
            "notes": ["No country policy configured yet."]
        },
        "country": {"name": country_code_or_name},
        "enforcement_mode": "soft",
        "rules": {},
        "legal_basis": []
    }


def _risk_bucket(status, warnings, reasons):
    if status == "block":
        return ("high", "high", "high")

    flags = len(warnings) + len(reasons)
    if flags >= 3:
        return ("high", "high", "high")
    if flags >= 1:
        return ("medium", "medium", "medium")
    return ("low", "low", "low")


def check_policy(country_code_or_name, vehicle):

    policy = load_policy(country_code_or_name)

    meta = policy.get("policy_meta", {})
    country = policy.get("country", {})
    rules = policy.get("rules", {})
    enforcement_mode = policy.get("enforcement_mode", "soft")

    status = "allow"
    reasons = []
    warnings = []

    today = _today_date()

    # -------------------------
    # 自动周期检测逻辑
    # -------------------------
    last_checked_str = meta.get("last_checked_at")
    last_verified_str = meta.get("last_verified_at")
    small_cycle = meta.get("small_update_cycle_days", 3)
    major_cycle = meta.get("major_update_cycle_days", 7)

    days_since_last_checked = None
    small_update_needed = False
    major_update_needed = False

    if last_checked_str:
        last_checked_date = datetime.strptime(last_checked_str, "%Y-%m-%d").date()
        days_since_last_checked = (today - last_checked_date).days
        if days_since_last_checked >= small_cycle:
            small_update_needed = True

    if last_verified_str:
        last_verified_date = datetime.strptime(last_verified_str, "%Y-%m-%d").date()
        days_since_verified = (today - last_verified_date).days
        if days_since_verified >= major_cycle:
            major_update_needed = True

    # -------------------------
    # 过期检测
    # -------------------------
    next_review_str = meta.get("next_review_due")
    is_outdated = False
    days_until_review = None

    if next_review_str:
        next_review_date = datetime.strptime(next_review_str, "%Y-%m-%d").date()
        delta = (next_review_date - today).days
        days_until_review = delta
        if delta < 0:
            is_outdated = True
            warnings.append("Policy data review overdue.")

    # -------------------------
    # 年龄规则
    # -------------------------
    vehicle_year = vehicle.get("year")
    current_year = datetime.utcnow().year
    age_rule = rules.get("age")

    if age_rule and isinstance(vehicle_year, int):
        age = current_year - vehicle_year
        soft_warn = age_rule.get("params", {}).get("soft_warn_over_years")
        if isinstance(soft_warn, int) and age > soft_warn:
            warnings.append(f"Vehicle age {age}y may increase cost or complexity.")

    # -------------------------
    # 风险评估
    # -------------------------
    risk_level, compliance_complexity, cost_risk = _risk_bucket(status, warnings, reasons)

    # =========================
    # 强制过期责任机制（核心）
    # =========================
    if is_outdated:
        warnings.append("⚠ 当前政策数据已超过复核周期。")
        warnings.append("⚠ 本判断仅供参考，必须人工复核确认。")

        if risk_level == "low":
            risk_level = "medium"
        elif risk_level == "medium":
            risk_level = "high"

    return {
        "status": status,
        "risk_level": risk_level,
        "compliance_complexity": compliance_complexity,
        "cost_risk": cost_risk,
        "reasons": reasons,
        "warnings": warnings,
        "policy_meta": meta,
        "policy_country": country,
        "policy_health": {
            "is_outdated": is_outdated,
            "days_until_review": days_until_review,
            "days_since_last_checked": days_since_last_checked,
            "small_update_needed": small_update_needed,
            "major_update_needed": major_update_needed
        }
    }

def generate_policy_reply(policy_result: dict) -> str:
    """
    将结构化政策判断结果，转为专业+朋友式表达
    """

    status = policy_result.get("status")
    risk_level = policy_result.get("risk_level")
    warnings = policy_result.get("warnings", [])
    reasons = policy_result.get("reasons", [])
    health = policy_result.get("policy_health", {})

    lines = []

    # 开场：朋友式
    lines.append("我帮您看了一下当前的政策情况：")

    # 状态表达
    if status == "allow":
        lines.append("✅ 当前条件下原则上是可以操作的。")
    elif status == "block":
        lines.append("⛔ 当前条件下存在明确限制，暂不建议操作。")
    else:
        lines.append("ℹ 当前情况需要进一步确认。")

    # 风险等级说明
    if risk_level == "high":
        lines.append("⚠ 风险等级较高，建议谨慎评估。")
    elif risk_level == "medium":
        lines.append("⚠ 存在一定风险，需要注意细节。")
    else:
        lines.append("风险整体可控。")

    # 具体警告
    if warnings:
        lines.append("\n具体需要注意：")
        for w in warnings:
            lines.append(f"- {w}")

    # 过期责任提示（强化表达）
    if health.get("is_outdated"):
        lines.append(
            "\n当前政策数据已超过复核周期，建议在最终执行前进行人工确认。"
        )

    # 结尾：朋友式但专业
    lines.append(
        "\n如果您需要，我可以帮您进一步拆解操作流程或风险细节。"
    )

    return "\n".join(lines)


