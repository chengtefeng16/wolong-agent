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
from datetime import datetime
from pathlib import Path

ACTIVE_DIR = Path("knowledge/policies/countries")
DRAFT_DIR = Path("knowledge/policies/drafts/countries")

def run():
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for p in ACTIVE_DIR.glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("policy_meta", {})
        data["policy_meta"]["draft_generated_at"] = now
        out = DRAFT_DIR / p.name
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Draft generated:", out)

    print("\nDONE. Drafts are ready. Please review drafts before promoting to active.")

if __name__ == "__main__":
    run()
