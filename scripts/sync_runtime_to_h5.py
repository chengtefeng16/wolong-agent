# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================
"""
runtime 数据同步脚本 V1
将 qianqiu_os/runtime_views/ 的最新数据同步到 wolong_h5_console/public/runtime/views/
供 H5 前端实时读取。

用法：
  python3 scripts/sync_runtime_to_h5.py          # 单次同步
  python3 scripts/sync_runtime_to_h5.py --watch  # 持续监听（每 5 秒）
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_VIEWS   = PROJECT_ROOT / "qianqiu_os" / "runtime_views"
DST_VIEWS   = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "views"
SRC_ALERTS  = PROJECT_ROOT / "qianqiu_os" / "runtime_alerts"
DST_ALERTS  = PROJECT_ROOT / "wolong_h5_console" / "public" / "runtime" / "alerts"

# 需要同步的文件映射 src文件名 -> dst文件名
VIEW_FILES = [
    "h5_dashboard_whatsapp.json",
    "h5_dashboard_facebook.json",
    "h5_dashboard_facebook_feed.json",
    "whatsapp_control_snapshot.json",
    "manual_takeover_workbench.json",
    "h5_business_judgement_snapshot.json",
]

ALERT_FILES = [
    "runtime_alerts_latest.json",
]


def sync_once() -> dict:
    DST_VIEWS.mkdir(parents=True, exist_ok=True)
    DST_ALERTS.mkdir(parents=True, exist_ok=True)

    synced = []
    skipped = []

    for fname in VIEW_FILES:
        src = SRC_VIEWS / fname
        dst = DST_VIEWS / fname
        if src.exists():
            shutil.copy2(src, dst)
            synced.append(fname)
        else:
            skipped.append(fname)

    for fname in ALERT_FILES:
        src = SRC_ALERTS / fname
        dst = DST_ALERTS / fname
        if src.exists():
            shutil.copy2(src, dst)
            synced.append(fname)
        else:
            skipped.append(fname)

    return {"synced": synced, "skipped": skipped}


def main():
    watch_mode = "--watch" in sys.argv

    if watch_mode:
        print("[sync] 启动持续监听模式（每 5 秒同步一次）按 Ctrl+C 停止...")
        while True:
            try:
                result = sync_once()
                ts = time.strftime("%H:%M:%S")
                if result["synced"]:
                    print(f"[{ts}] 已同步: {', '.join(result['synced'])}")
                if result["skipped"]:
                    print(f"[{ts}] 后端无数据（跳过）: {', '.join(result['skipped'])}")
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n[sync] 已停止。")
                break
    else:
        result = sync_once()
        print("同步完成:")
        if result["synced"]:
            print(f"  已同步: {', '.join(result['synced'])}")
        if result["skipped"]:
            print(f"  后端无数据（跳过）: {', '.join(result['skipped'])}")


if __name__ == "__main__":
    main()
