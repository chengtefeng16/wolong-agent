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
import sys
from datetime import datetime
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.runtime_whatsapp_h5_sync_v1 import sync as sync_runtime_views

BASE_DIR = Path(__file__).resolve().parents[1]

ACTIVE_CONFIG_PATH = BASE_DIR / "runtime_governance" / "delegation_active_config.json"
PREVIEW_FILE_PATH = BASE_DIR / "services" / "h5_delegation_active_config_preview_v1.py"

INDEX_PATH = BASE_DIR / "runtime_sessions" / "whatsapp" / "conversation_index.json"
DASHBOARD_PATH = BASE_DIR / "runtime_views" / "h5_dashboard_whatsapp.json"
CONTROL_SNAPSHOT_PATH = BASE_DIR / "runtime_views" / "whatsapp_control_snapshot.json"

DELIVERY_LOGS_DIR = BASE_DIR / "runtime_governance" / "delivery_logs"
TAKEOVER_DIR = BASE_DIR / "runtime_governance" / "manual_takeover_tickets"

MEMORY_DIR = BASE_DIR / "memory" / "customer_profiles"
CRM_EXPORT_PATH = BASE_DIR / "runtime_exports" / "crm" / "crm_export_latest.json"
ALERT_LATEST_PATH = BASE_DIR / "runtime_alerts" / "runtime_alerts_latest.json"
REFLECTION_LATEST_PATH = BASE_DIR / "runtime_learning" / "reflection" / "reflection_learning_latest.json"
SELF_HEALING_LATEST_PATH = BASE_DIR / "runtime_healing" / "self_healing_latest.json"
KNOWLEDGE_GRAPH_LATEST_PATH = BASE_DIR / "runtime_knowledge" / "knowledge_graph_latest.json"

REGRESSION_OUTPUT_PATH = BASE_DIR / "runtime_governance" / "regression" / "runtime_regression_result_v1.json"


class RuntimeRegressionSuiteV1:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _read_json(self, path: Path):
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _count_memory_profiles(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        return len(list(MEMORY_DIR.glob("*.json")))

    def run(self):
        checks = []

        active_config = self._read_json(ACTIVE_CONFIG_PATH)
        checks.append({
            "name": "active_config_exists",
            "passed": active_config is not None,
            "detail": str(ACTIVE_CONFIG_PATH),
        })

        whatsapp_control = (active_config or {}).get("whatsapp_control", {}) or {}
        checks.append({
            "name": "whatsapp_control_exists",
            "passed": bool(whatsapp_control),
            "detail": "whatsapp_control found" if whatsapp_control else "whatsapp_control missing",
        })

        checks.append({
            "name": "readonly_baseline",
            "passed": whatsapp_control.get("ingress_mode") == "readonly"
                      and whatsapp_control.get("auto_reply") is False
                      and whatsapp_control.get("auto_dispatch") is False,
            "detail": {
                "ingress_mode": whatsapp_control.get("ingress_mode"),
                "auto_reply": whatsapp_control.get("auto_reply"),
                "auto_dispatch": whatsapp_control.get("auto_dispatch"),
            },
        })

        checks.append({
            "name": "preview_module_exists",
            "passed": PREVIEW_FILE_PATH.exists(),
            "detail": str(PREVIEW_FILE_PATH),
        })

        checks.append({
            "name": "runtime_index_exists",
            "passed": INDEX_PATH.exists(),
            "detail": str(INDEX_PATH),
        })

        sync_result = sync_runtime_views()
        checks.append({
            "name": "runtime_views_sync_runs",
            "passed": bool(sync_result.get("success")),
            "detail": sync_result,
        })

        dashboard = self._read_json(DASHBOARD_PATH) or {}
        control_snapshot = self._read_json(CONTROL_SNAPSHOT_PATH) or {}

        checks.append({
            "name": "dashboard_exists",
            "passed": DASHBOARD_PATH.exists(),
            "detail": str(DASHBOARD_PATH),
        })

        checks.append({
            "name": "control_snapshot_exists",
            "passed": CONTROL_SNAPSHOT_PATH.exists(),
            "detail": str(CONTROL_SNAPSHOT_PATH),
        })

        checks.append({
            "name": "control_snapshot_matches_active_config",
            "passed": control_snapshot.get("ingress_mode") == whatsapp_control.get("ingress_mode")
                      and control_snapshot.get("auto_reply") == whatsapp_control.get("auto_reply")
                      and control_snapshot.get("auto_dispatch") == whatsapp_control.get("auto_dispatch"),
            "detail": {
                "active": whatsapp_control,
                "snapshot": control_snapshot,
            },
        })

        customers = dashboard.get("customers", []) if isinstance(dashboard, dict) else []
        checks.append({
            "name": "dashboard_has_runtime_customers",
            "passed": isinstance(customers, list) and len(customers) > 0,
            "detail": {"customer_count": len(customers) if isinstance(customers, list) else 0},
        })

        checks.append({
            "name": "delivery_logs_dir_exists",
            "passed": DELIVERY_LOGS_DIR.exists(),
            "detail": str(DELIVERY_LOGS_DIR),
        })

        checks.append({
            "name": "manual_takeover_dir_exists",
            "passed": TAKEOVER_DIR.exists(),
            "detail": str(TAKEOVER_DIR),
        })

        memory_count = self._count_memory_profiles()
        checks.append({
            "name": "customer_memory_exists",
            "passed": memory_count > 0,
            "detail": {"memory_profile_count": memory_count},
        })

        crm_export = self._read_json(CRM_EXPORT_PATH) or {}
        checks.append({
            "name": "crm_export_exists",
            "passed": CRM_EXPORT_PATH.exists(),
            "detail": str(CRM_EXPORT_PATH),
        })
        checks.append({
            "name": "crm_export_has_items",
            "passed": isinstance(crm_export.get("items"), list) and len(crm_export.get("items", [])) > 0,
            "detail": {"crm_export_count": len(crm_export.get("items", [])) if isinstance(crm_export.get("items"), list) else 0},
        })

        alert_latest = self._read_json(ALERT_LATEST_PATH) or {}
        checks.append({
            "name": "alert_latest_exists",
            "passed": ALERT_LATEST_PATH.exists(),
            "detail": str(ALERT_LATEST_PATH),
        })
        checks.append({
            "name": "alert_latest_has_items",
            "passed": isinstance(alert_latest.get("items"), list) and len(alert_latest.get("items", [])) > 0,
            "detail": {"alert_count": len(alert_latest.get("items", [])) if isinstance(alert_latest.get("items"), list) else 0},
        })

        reflection_latest = self._read_json(REFLECTION_LATEST_PATH) or {}
        checks.append({
            "name": "reflection_latest_exists",
            "passed": REFLECTION_LATEST_PATH.exists(),
            "detail": str(REFLECTION_LATEST_PATH),
        })
        checks.append({
            "name": "reflection_has_learning_points",
            "passed": isinstance(reflection_latest.get("learning_points"), list) and len(reflection_latest.get("learning_points", [])) > 0,
            "detail": {"learning_count": len(reflection_latest.get("learning_points", [])) if isinstance(reflection_latest.get("learning_points"), list) else 0},
        })

        self_healing_latest = self._read_json(SELF_HEALING_LATEST_PATH) or {}
        checks.append({
            "name": "self_healing_latest_exists",
            "passed": SELF_HEALING_LATEST_PATH.exists(),
            "detail": str(SELF_HEALING_LATEST_PATH),
        })
        checks.append({
            "name": "self_healing_has_actions",
            "passed": isinstance(self_healing_latest.get("actions"), list) and len(self_healing_latest.get("actions", [])) > 0,
            "detail": {"action_count": len(self_healing_latest.get("actions", [])) if isinstance(self_healing_latest.get("actions"), list) else 0},
        })

        knowledge_graph_latest = self._read_json(KNOWLEDGE_GRAPH_LATEST_PATH) or {}
        checks.append({
            "name": "knowledge_graph_latest_exists",
            "passed": KNOWLEDGE_GRAPH_LATEST_PATH.exists(),
            "detail": str(KNOWLEDGE_GRAPH_LATEST_PATH),
        })
        checks.append({
            "name": "knowledge_graph_has_nodes_and_edges",
            "passed": knowledge_graph_latest.get("node_count", 0) > 0 and knowledge_graph_latest.get("edge_count", 0) > 0,
            "detail": {
                "node_count": knowledge_graph_latest.get("node_count", 0),
                "edge_count": knowledge_graph_latest.get("edge_count", 0),
            },
        })

        passed_count = len([c for c in checks if c["passed"]])
        failed_count = len(checks) - passed_count
        overall_status = "passed" if failed_count == 0 else "failed"

        result = {
            "checked_at": self._now_str(),
            "suite_name": "runtime_regression_suite_v1",
            "overall_status": overall_status,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "checks": checks,
        }

        self._write_json(REGRESSION_OUTPUT_PATH, result)
        return result


if __name__ == "__main__":
    suite = RuntimeRegressionSuiteV1()
    print(json.dumps(suite.run(), ensure_ascii=False, indent=2))
