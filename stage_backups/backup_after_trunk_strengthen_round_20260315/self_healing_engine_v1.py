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
REFLECTION_LATEST_PATH = BASE_DIR / "runtime_learning" / "reflection" / "reflection_learning_latest.json"
ALERT_LATEST_PATH = BASE_DIR / "runtime_alerts" / "runtime_alerts_latest.json"
REGRESSION_RESULT_PATH = BASE_DIR / "runtime_governance" / "regression" / "runtime_regression_result_v1.json"
HEALING_DIR = BASE_DIR / "runtime_healing"


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


class SelfHealingEngineV1:
    def _load_inputs(self):
        reflection = _read_json(REFLECTION_LATEST_PATH, {})
        alerts = _read_json(ALERT_LATEST_PATH, {})
        regression = _read_json(REGRESSION_RESULT_PATH, {})
        return reflection, alerts, regression

    def _build_actions(self, reflection: Dict[str, Any], alerts: Dict[str, Any], regression: Dict[str, Any]) -> List[Dict[str, Any]]:
        metrics = reflection.get("metrics", {}) or {}
        bucket_counts = reflection.get("bucket_counts", {}) or {}
        alert_items = alerts.get("items", []) if isinstance(alerts, dict) else []

        actions: List[Dict[str, Any]] = []

        if regression.get("overall_status") != "passed":
            actions.append({
                "priority": "P0",
                "type": "stabilize_trunk",
                "title": "先稳主干再扩展",
                "reason": "当前回归未完全通过，必须先修复主干再继续加新能力。",
                "suggested_fix": "先修复 regression 失败项，再继续推进其他模块。",
            })

        delivery_blocked_count = len([
            x for x in alert_items
            if isinstance(x, dict) and x.get("type") == "delivery_blocked"
        ])
        if delivery_blocked_count > 0:
            actions.append({
                "priority": "P0",
                "type": "readonly_blocked_send_followup",
                "title": "处理 readonly 拦截外发案例",
                "reason": f"当前检测到 {delivery_blocked_count} 条被治理层拦截的外发记录。",
                "suggested_fix": "保留 readonly 策略不动，把这些客户全部转人工接管，不要误判成发送故障。",
            })

        if metrics.get("manual_review_count", 0) > 0:
            actions.append({
                "priority": "P1",
                "type": "manual_queue_strengthen",
                "title": "加强人工接管队列",
                "reason": f"当前有 {metrics.get('manual_review_count', 0)} 个客户需要人工查看。",
                "suggested_fix": "优先把高优先级客户推入 H5 预警中心和人工接管列表。",
            })

        if metrics.get("quote_ready_count", 0) > 0:
            actions.append({
                "priority": "P1",
                "type": "quote_pipeline_strengthen",
                "title": "加强报价准备闭环",
                "reason": f"当前有 {metrics.get('quote_ready_count', 0)} 个客户已经进入报价准备阶段。",
                "suggested_fix": "优先补强报价流转、CRM 跟进和物流条件确认。",
            })

        weak_count = metrics.get("judgement_weak_count", 0)
        if weak_count > 0 or bucket_counts.get("待判断", 0) > 0:
            actions.append({
                "priority": "P1",
                "type": "judgement_rule_expand",
                "title": "继续补强客户判断规则",
                "reason": f"当前仍有 {weak_count} 个弱判断样本或待判断样本。",
                "suggested_fix": "继续补车型词、国家词、批量采购词、个人自用词，并减少待判断占比。",
            })

        high_alert_count = metrics.get("high_alert_count", 0)
        if high_alert_count > 0:
            actions.append({
                "priority": "P1",
                "type": "high_alert_first",
                "title": "高优先级预警优先处理",
                "reason": f"当前存在 {high_alert_count} 条高优先级预警。",
                "suggested_fix": "H5 先展示高优先级预警，并让人工优先处理这些客户。",
            })

        actions.append({
            "priority": "P2",
            "type": "next_stage_plan",
            "title": "进入下一批主干补强",
            "reason": "当前记忆、预警、反思、自愈主干骨架已开始形成。",
            "suggested_fix": "下一步继续补知识图谱层和测试回归加强版。",
        })

        return actions

    def run(self) -> Dict[str, Any]:
        reflection, alerts, regression = self._load_inputs()
        actions = self._build_actions(reflection, alerts, regression)

        payload = {
            "generated_at": _now_str(),
            "healing_name": "self_healing_latest",
            "source": {
                "reflection": str(REFLECTION_LATEST_PATH),
                "alerts": str(ALERT_LATEST_PATH),
                "regression": str(REGRESSION_RESULT_PATH),
            },
            "action_count": len(actions),
            "actions": actions,
        }

        latest_path = HEALING_DIR / "self_healing_latest.json"
        dated_path = HEALING_DIR / f"self_healing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        _write_json(latest_path, payload)
        _write_json(dated_path, payload)

        return {
            "success": True,
            "self_healing_latest_path": str(latest_path),
            "dated_self_healing_path": str(dated_path),
            "action_count": len(actions),
        }


if __name__ == "__main__":
    print(json.dumps(SelfHealingEngineV1().run(), ensure_ascii=False, indent=2))
