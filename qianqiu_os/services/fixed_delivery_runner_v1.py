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

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from qianqiu_os.services.daily_layers_export_generator_v1 import generate as generate_daily
from qianqiu_os.services.nightly_checkpoint_generator_v1 import generate as generate_nightly
from qianqiu_os.services.agentos_weekly_report_generator_v1 import generate as generate_agentos_weekly
from qianqiu_os.services.wolong_weekly_report_generator_v1 import generate as generate_wolong_weekly


BASE_DIR = Path(__file__).resolve().parents[1]
EXPORT_ROOT = BASE_DIR / "runtime_exports"
STATE_PATH = EXPORT_ROOT / "fixed_delivery_state_v1.json"
TZ = ZoneInfo("Asia/Shanghai")


def now_shanghai() -> datetime:
    return datetime.now(TZ)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "latest_daily_date": None,
            "latest_nightly_date": None,
            "latest_weekly_iso_week": None,
            "latest_weekly_date": None,
            "history": [],
        }
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {
            "latest_daily_date": None,
            "latest_nightly_date": None,
            "latest_weekly_iso_week": None,
            "latest_weekly_date": None,
            "history": [],
        }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_history(state: dict, item: dict) -> None:
    history = state.setdefault("history", [])
    history.append(item)
    state["history"] = history[-50:]


def current_date_str(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d")


def current_iso_week(ts: datetime) -> str:
    iso = ts.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def should_run_daily(ts: datetime, state: dict) -> bool:
    return ts.hour >= 16 and state.get("latest_daily_date") != current_date_str(ts)


def should_run_nightly(ts: datetime, state: dict) -> bool:
    return ts.hour >= 23 and state.get("latest_nightly_date") != current_date_str(ts)


def should_run_weekly(ts: datetime, state: dict) -> bool:
    return ts.weekday() == 4 and ts.hour >= 17 and state.get("latest_weekly_iso_week") != current_iso_week(ts)


def run_daily(ts: datetime, state: dict, reason: str) -> dict:
    result = generate_daily()
    state["latest_daily_date"] = current_date_str(ts)
    append_history(state, {
        "kind": "daily_layers_export",
        "reason": reason,
        "ran_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
    })
    return result


def run_nightly(ts: datetime, state: dict, reason: str) -> dict:
    result = generate_nightly()
    state["latest_nightly_date"] = current_date_str(ts)
    append_history(state, {
        "kind": "nightly_checkpoint",
        "reason": reason,
        "ran_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
    })
    return result


def run_weekly(ts: datetime, state: dict, reason: str) -> dict:
    agentos_result = generate_agentos_weekly()
    wolong_result = generate_wolong_weekly()
    state["latest_weekly_iso_week"] = current_iso_week(ts)
    state["latest_weekly_date"] = current_date_str(ts)
    append_history(state, {
        "kind": "weekly_reports",
        "reason": reason,
        "ran_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "agentos_result": agentos_result,
        "wolong_result": wolong_result,
    })
    return {
        "agentos": agentos_result,
        "wolong": wolong_result,
    }


def build_status(ts: datetime, state: dict) -> dict:
    return {
        "now": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Shanghai",
        "today": current_date_str(ts),
        "iso_week": current_iso_week(ts),
        "latest_daily_date": state.get("latest_daily_date"),
        "latest_nightly_date": state.get("latest_nightly_date"),
        "latest_weekly_iso_week": state.get("latest_weekly_iso_week"),
        "due_daily_now": should_run_daily(ts, state),
        "due_nightly_now": should_run_nightly(ts, state),
        "due_weekly_now": should_run_weekly(ts, state),
        "history_count": len(state.get("history", [])),
        "state_path": str(STATE_PATH),
    }


def tick(ts: datetime, state: dict) -> dict:
    actions = []
    results = {}

    if should_run_daily(ts, state):
        results["daily"] = run_daily(ts, state, reason="auto_tick")
        actions.append("daily")

    if should_run_nightly(ts, state):
        results["nightly"] = run_nightly(ts, state, reason="auto_tick")
        actions.append("nightly")

    if should_run_weekly(ts, state):
        results["weekly"] = run_weekly(ts, state, reason="auto_tick")
        actions.append("weekly")

    save_state(state)

    return {
        "mode": "tick",
        "actions": actions,
        "results": results,
        "status": build_status(ts, state),
    }


def run_manual(ts: datetime, state: dict, include_daily: bool, include_nightly: bool, include_weekly: bool, reason: str) -> dict:
    results = {}
    actions = []

    if include_daily:
        results["daily"] = run_daily(ts, state, reason=reason)
        actions.append("daily")

    if include_nightly:
        results["nightly"] = run_nightly(ts, state, reason=reason)
        actions.append("nightly")

    if include_weekly:
        results["weekly"] = run_weekly(ts, state, reason=reason)
        actions.append("weekly")

    save_state(state)

    return {
        "mode": "manual",
        "actions": actions,
        "results": results,
        "status": build_status(ts, state),
    }


def main():
    parser = argparse.ArgumentParser(description="Fixed delivery runner for AgentOS / Wolong")
    parser.add_argument("--status", action="store_true", help="Only print current delivery status")
    parser.add_argument("--tick", action="store_true", help="Run only if current time windows are due")
    parser.add_argument("--run-now", action="store_true", help="Force selected jobs immediately")
    parser.add_argument("--include-daily", action="store_true", help="Include daily layers export")
    parser.add_argument("--include-nightly", action="store_true", help="Include nightly checkpoint")
    parser.add_argument("--include-weekly", action="store_true", help="Include Friday weekly reports")
    parser.add_argument("--reason", default="manual_run", help="Reason recorded in state history")
    args = parser.parse_args()

    ts = now_shanghai()
    state = load_state()

    if args.status:
        print(json.dumps(build_status(ts, state), ensure_ascii=False, indent=2))
        return

    if args.tick:
        print(json.dumps(tick(ts, state), ensure_ascii=False, indent=2))
        return

    if args.run_now:
        include_daily = args.include_daily
        include_nightly = args.include_nightly
        include_weekly = args.include_weekly

        if not any([include_daily, include_nightly, include_weekly]):
            include_daily = True
            include_nightly = True
            include_weekly = True

        print(json.dumps(
            run_manual(
                ts=ts,
                state=state,
                include_daily=include_daily,
                include_nightly=include_nightly,
                include_weekly=include_weekly,
                reason=args.reason,
            ),
            ensure_ascii=False,
            indent=2,
        ))
        return

    print(json.dumps(build_status(ts, state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
