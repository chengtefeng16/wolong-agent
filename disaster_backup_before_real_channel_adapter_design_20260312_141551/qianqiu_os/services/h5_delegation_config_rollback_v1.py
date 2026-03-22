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
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = BASE_DIR / "runtime_governance"
ACTIVE_CONFIG_PATH = RUNTIME_DIR / "delegation_active_config.json"
AUDIT_DIR = RUNTIME_DIR / "audit_logs"
SNAPSHOT_DIR = RUNTIME_DIR / "rollback_snapshots"
AUDIT_DIR.mkdir(exist_ok=True)
SNAPSHOT_DIR.mkdir(exist_ok=True)

class H5DelegationConfigRollbackV1:
    def _now_str(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _write_json(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def rollback_to_snapshot(self, snapshot_path: str, operator_id="unknown_operator", operator_name="unknown_operator", change_reason="rollback_active_config"):
        snapshot = Path(snapshot_path)
        if not snapshot.exists():
            return {
                "success": False,
                "message": "snapshot not found",
                "snapshot_path": str(snapshot),
            }

        pre_rollback_backup = None
        if ACTIVE_CONFIG_PATH.exists():
            pre_rollback_backup = SNAPSHOT_DIR / f"delegation_active_config_pre_rollback_{self._now_str()}.json"
            shutil.copy2(ACTIVE_CONFIG_PATH, pre_rollback_backup)

        shutil.copy2(snapshot, ACTIVE_CONFIG_PATH)

        audit_record = {
            "audit_type": "delegation_config_rollback",
            "rolled_back_at": self._now_str(),
            "operator_id": operator_id,
            "operator_name": operator_name,
            "change_reason": change_reason,
            "restored_from_snapshot": str(snapshot),
            "active_config_path": str(ACTIVE_CONFIG_PATH),
            "pre_rollback_backup_path": str(pre_rollback_backup) if pre_rollback_backup else None,
        }
        audit_record_path = AUDIT_DIR / f"delegation_config_rollback_{self._now_str()}.json"
        self._write_json(audit_record_path, audit_record)

        return {
            "success": True,
            "message": "rollback completed",
            "restored_from_snapshot": str(snapshot),
            "active_config_path": str(ACTIVE_CONFIG_PATH),
            "pre_rollback_backup_path": str(pre_rollback_backup) if pre_rollback_backup else None,
            "audit_record_path": str(audit_record_path),
        }

if __name__ == "__main__":
    snapshots = sorted(SNAPSHOT_DIR.glob("delegation_active_config_*.json"))
    snapshots = [p for p in snapshots if "pre_rollback" not in p.name]
    if not snapshots:
        print(json.dumps({
            "success": False,
            "message": "no rollback snapshot found",
            "snapshot_dir": str(SNAPSHOT_DIR)
        }, ensure_ascii=False, indent=2))
    else:
        latest = snapshots[-1]
        service = H5DelegationConfigRollbackV1()
        result = service.rollback_to_snapshot(
            snapshot_path=str(latest),
            operator_id="demo_rollback_operator",
            operator_name="demo_rollback_operator",
            change_reason="rollback_to_latest_snapshot"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
