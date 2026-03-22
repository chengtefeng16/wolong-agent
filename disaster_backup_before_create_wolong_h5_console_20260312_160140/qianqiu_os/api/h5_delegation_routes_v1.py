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
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qianqiu_os.services.h5_delegation_config_service_v2 import H5DelegationConfigServiceV2
from qianqiu_os.services.h5_delegation_active_config_preview_v1 import build_preview
from qianqiu_os.services.h5_delegation_config_rollback_v1 import H5DelegationConfigRollbackV1

BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = BASE_DIR / "runtime_governance"
ACTIVE_CONFIG_PATH = RUNTIME_DIR / "delegation_active_config.json"
SNAPSHOT_DIR = RUNTIME_DIR / "rollback_snapshots"


def api_save_delegation_config(payload: dict):
    service = H5DelegationConfigServiceV2()
    return service.save_config(payload)


def api_get_active_delegation_preview():
    if not ACTIVE_CONFIG_PATH.exists():
        return {
            "success": False,
            "message": "active config not found",
            "path": str(ACTIVE_CONFIG_PATH),
        }

    with open(ACTIVE_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    preview = build_preview(data)
    return {
        "success": True,
        "message": "active preview loaded",
        "data": preview,
    }


def api_list_delegation_snapshots():
    snapshots = sorted(SNAPSHOT_DIR.glob("delegation_active_config_*.json"))
    snapshots = [p for p in snapshots if "pre_rollback" not in p.name]
    return {
        "success": True,
        "message": "snapshot list loaded",
        "items": [str(p) for p in snapshots],
    }


def api_rollback_delegation_config(payload: dict):
    payload = payload or {}
    snapshot_path = payload.get("snapshot_path")
    operator_id = payload.get("operator_id") or "unknown_operator"
    operator_name = payload.get("operator_name") or "unknown_operator"
    change_reason = payload.get("change_reason") or "rollback_from_api"

    service = H5DelegationConfigRollbackV1()
    return service.rollback_to_snapshot(
        snapshot_path=snapshot_path,
        operator_id=operator_id,
        operator_name=operator_name,
        change_reason=change_reason,
    )


if __name__ == "__main__":
    demo_save_payload = {
        "operator_id": "api_demo_admin",
        "operator_name": "API Demo Admin",
        "change_reason": "api_demo_save_l3",
        "config_version": "api_demo_v1",
        "applied_preset": "L3_small_autonomy_safe"
    }

    print("==== DEMO SAVE ====")
    print(json.dumps(api_save_delegation_config(demo_save_payload), ensure_ascii=False, indent=2))

    print()
    print("==== DEMO PREVIEW ====")
    print(json.dumps(api_get_active_delegation_preview(), ensure_ascii=False, indent=2))

    print()
    print("==== DEMO SNAPSHOT LIST ====")
    print(json.dumps(api_list_delegation_snapshots(), ensure_ascii=False, indent=2))
