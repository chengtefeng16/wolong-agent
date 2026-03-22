# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"
ALERT_LATEST_PATH = BASE_DIR / "runtime_alerts" / "runtime_alerts_latest.json"
REGRESSION_RESULT_PATH = BASE_DIR / "runtime_governance" / "regression" / "runtime_regression_result_v1.json"
LEARNING_DIR = BASE_DIR / "runtime_learning" / "reflection"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ReflectionLearningEngineV1:
    def _load_profiles(self) -> List[Dict[str, Any]]:
        profiles = []
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        for path in MEMORY_DIR.glob("*.json"):
            data = _read_json(path, {})
            if isinstance(data, dict) and data:
                profiles.append(data)
        return profiles

    def _count_buckets(self, profiles: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {
            "准车商": 0,
            "疑似车商": 0,
            "个人客户": 0,
            "待判断": 0,
            "沟通无效": 0,
        }
        for profile in profiles:
            latest = profile.get("latest_profile", {}) or {}
            bucket = latest.get("bucket", "待判断")
            if bucket not in counts:
                counts["待判断"] += 1
            else:
                counts[bucket] += 1
        return counts

    def _collect_metrics(self, profiles: List[Dict[str, Any]], alerts: Dict[str, Any], regression: Dict[str, Any]) -> Dict[str, Any]:
        manual_review_count = 0
        quote_ready_count = 0
        high_priority_count = 0
        judgement_weak_count = 0

        for profile in profiles:
            latest = profile.get("latest_profile", {}) or {}
            if latest.get("needs_human_review"):
                manual_review_count += 1
            if latest.get("business_stage") == "已进入报价准备":
                quote_ready_count += 1
            if latest.get("priority") == "high":
                high_priority_count += 1
            if latest.get("bucket") in ["待判断", "沟通无效"]:
                judgement_weak_count += 1

        alert_items = alerts.get("items", []) if isinstance(alerts, dict) else []
        high_alert_count = len([x for x in alert_items if isinstance(x, dict) and x.get("level") == "high"])
        medium_alert_count = len([x for x in alert_items if isinstance(x, dict) and x.get("level") == "medium"])
        delivery_blocked_count = len([x for x in alert_items if isinstance(x, dict) and x.get("type") == "delivery_blocked"])

        return {
            "profile_count": len(profiles),
            "manual_review_count": manual_review_count,
            "quote_ready_count": quote_ready_count,
            "high_priority_count": high_priority_count,
            "judgement_weak_count": judgement_weak_count,
            "alert_count": len(alert_items),
            "high_alert_count": high_alert_count,
            "medium_alert_count": medium_alert_count,
            "delivery_blocked_count": delivery_blocked_count,
            "regression_status": regression.get("overall_status", "unknown"),
            "regression_passed_count": regression.get("passed_count", 0),
            "regression_failed_count": regression.get("failed_count", 0),
        }

    def _build_reflections(self, metrics: Dict[str, Any], bucket_counts: Dict[str, int]) -> List[str]:
        reflections: List[str] = []

        if metrics["regression_status"] == "passed":
            reflections.append("当前主干回归已通过，说明接入、真源、预警、记忆、导出等核心链路当前是稳定的。")
        else:
            reflections.append("当前主干回归未完全通过，说明应先稳主干，再继续扩展新能力。")

        if metrics["delivery_blocked_count"] > 0:
            reflections.append("当前存在外发被治理层拦截的记录，这在 readonly 阶段属于预期现象，不应误判为系统发送故障。")

        if metrics["manual_review_count"] > 0:
            reflections.append(f"当前有 {metrics['manual_review_count']} 个客户需要人工查看，说明人工监管仍是主干关键能力，不能被弱化。")

        if metrics["quote_ready_count"] > 0:
            reflections.append(f"当前已有 {metrics['quote_ready_count']} 个客户进入报价准备阶段，说明系统已经具备从线索识别走向业务推进的能力。")

        if bucket_counts.get("待判断", 0) > 0:
            reflections.append("仍存在待判断客户，说明客户判断引擎还要继续补关键词、补规则、补上下文。")

        if bucket_counts.get("沟通无效", 0) > 0:
            reflections.append("存在沟通无效客户，后续可继续加强线索过滤与低价值线索识别。")

        if metrics["high_alert_count"] > 0:
            reflections.append(f"当前存在 {metrics['high_alert_count']} 条高优先级预警，说明预警层已经开始真正参与主干治理。")

        return reflections

    def _build_learning_points(self, metrics: Dict[str, Any], bucket_counts: Dict[str, int]) -> List[str]:
        learning_points: List[str] = []

        learning_points.append("好的做法要保持：先让消息进主干，再统一真源，再做判断、记忆、预警、导出。")
        learning_points.append("只读观察阶段的正确原则要保持：先观察、不扰动、不自动外发。")

        if bucket_counts.get("准车商", 0) + bucket_counts.get("疑似车商", 0) > 0:
            learning_points.append("当前客户判断链已经能识别高意向客户，后续要继续把判断结果反哺到人工接管和 CRM 跟进里。")

        if metrics["judgement_weak_count"] > 0:
            learning_points.append("当前仍有判断偏弱样本，后续要继续补充判断关键词、车型词、国家词、批量采购词。")

        if metrics["quote_ready_count"] > 0:
            learning_points.append("业务上下文层已能识别报价准备阶段，后续要继续把报价、物流、付款条件也纳入上下文。")

        return learning_points

    def _build_next_actions(self, metrics: Dict[str, Any], bucket_counts: Dict[str, int]) -> List[str]:
        actions: List[str] = []

        if bucket_counts.get("待判断", 0) > 0:
            actions.append("继续补强客户判断引擎，减少“待判断”占比。")

        if metrics["manual_review_count"] > 0:
            actions.append("继续补强人工接管工作台，让高意向客户能更快进入人工处理。")

        if metrics["quote_ready_count"] > 0:
            actions.append("继续补强 CRM 导出和报价流转，让“报价准备”客户尽快进入业务推进。")

        if metrics["delivery_blocked_count"] > 0:
            actions.append("继续保留 readonly 治理闸门，同时把被拦截案例纳入人工处理闭环。")

        actions.append("下一阶段继续补知识图谱层、自愈层与测试回归加强版。")

        return actions

    def build_reflection_learning(self) -> Dict[str, Any]:
        profiles = self._load_profiles()
        alerts = _read_json(ALERT_LATEST_PATH, {})
        regression = _read_json(REGRESSION_RESULT_PATH, {})

        bucket_counts = self._count_buckets(profiles)
        metrics = self._collect_metrics(profiles, alerts, regression)
        reflections = self._build_reflections(metrics, bucket_counts)
        learning_points = self._build_learning_points(metrics, bucket_counts)
        next_actions = self._build_next_actions(metrics, bucket_counts)

        payload = {
            "generated_at": _now_str(),
            "reflection_name": "reflection_learning_latest",
            "metrics": metrics,
            "bucket_counts": bucket_counts,
            "reflections": reflections,
            "learning_points": learning_points,
            "next_actions": next_actions,
        }

        latest_path = LEARNING_DIR / "reflection_learning_latest.json"
        dated_path = LEARNING_DIR / f"reflection_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        _write_json(latest_path, payload)
        _write_json(dated_path, payload)

        return {
            "success": True,
            "reflection_latest_path": str(latest_path),
            "dated_reflection_path": str(dated_path),
            "reflection_count": len(reflections),
            "learning_count": len(learning_points),
            "next_action_count": len(next_actions),
        }


if __name__ == "__main__":
    print(json.dumps(ReflectionLearningEngineV1().build_reflection_learning(), ensure_ascii=False, indent=2))
