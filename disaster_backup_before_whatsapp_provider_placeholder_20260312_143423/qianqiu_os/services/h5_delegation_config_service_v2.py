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
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
RUNTIME_DIR = BASE_DIR / "runtime_governance"
RUNTIME_DIR.mkdir(exist_ok=True)

ACTIVE_CONFIG_PATH = RUNTIME_DIR / "delegation_active_config.json"
AUDIT_DIR = RUNTIME_DIR / "audit_logs"
SNAPSHOT_DIR = RUNTIME_DIR / "rollback_snapshots"
AUDIT_DIR.mkdir(exist_ok=True)
SNAPSHOT_DIR.mkdir(exist_ok=True)

CONFIG_MODULE_DIR = CONFIG_DIR
if str(CONFIG_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(CONFIG_MODULE_DIR))

from h5_delegation_config_loader_v1 import build_config


class H5DelegationConfigServiceV2:
    def _now_str(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_config(self, payload: dict):
        payload = payload or {}
        operator_id = payload.get("operator_id") or "unknown_operator"
        operator_name = payload.get("operator_name") or "unknown_operator"
        change_reason = payload.get("change_reason") or "no_reason_provided"
        config_version = payload.get("config_version") or self._now_str()
        applied_preset = payload.get("applied_preset")

        if applied_preset:
            merged = build_config(preset_key=applied_preset)
            delegation_policy = merged.get("delegation_policy", {}) or {}
        else:
            delegation_policy = payload.get("delegation_policy") or {}

        rollback_snapshot_path = None
        if ACTIVE_CONFIG_PATH.exists():
            rollback_snapshot_path = SNAPSHOT_DIR / f"delegation_active_config_{self._now_str()}.json"
            shutil.copy2(ACTIVE_CONFIG_PATH, rollback_snapshot_path)

        active_config = {
            "config_name": "delegation_active_config",
            "config_version": config_version,
            "saved_at": self._now_str(),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "change_reason": change_reason,
            "applied_preset": applied_preset,
            "delegation_policy": delegation_policy,
        }
        self._write_json(ACTIVE_CONFIG_PATH, active_config)

        audit_record = {
            "audit_type": "delegation_config_save",
            "saved_at": self._now_str(),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "change_reason": change_reason,
            "config_version": config_version,
            "applied_preset": applied_preset,
            "active_config_path": str(ACTIVE_CONFIG_PATH),
            "rollback_snapshot_path": str(rollback_snapshot_path) if rollback_snapshot_path else None,
        }
        audit_record_path = AUDIT_DIR / f"delegation_config_save_{self._now_str()}.json"
        self._write_json(audit_record_path, audit_record)

        return {
            "success": True,
            "message": "delegation config saved",
            "saved_config_path": str(ACTIVE_CONFIG_PATH),
            "audit_record_path": str(audit_record_path),
            "rollback_snapshot_path": str(rollback_snapshot_path) if rollback_snapshot_path else None,
            "applied_preset": applied_preset,
            "config_version": config_version,
        }


if __name__ == "__main__":
    demo_payload = {
        "operator_id": "demo_operator_v2",
        "operator_name": "demo_operator_v2",
        "change_reason": "save_full_preset_config",
        "config_version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "applied_preset": "L3_small_autonomy_safe"
    }
    service = H5DelegationConfigServiceV2()
    result = service.save_config(demo_payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
