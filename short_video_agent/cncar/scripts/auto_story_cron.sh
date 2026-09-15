#!/bin/bash
# launchd daily runner: --auto-story → log → macOS notification
# Called by io.cncar.auto_story launchd job at 07:00 local time

PROJECT_DIR="/Users/cheng/autogen_gemini_gui_test/short_video_agent"
VENV_PYTHON="$PROJECT_DIR/../venv/bin/python3"
LOG_FILE="$PROJECT_DIR/cncar/logs/auto_story.log"
PENDING_FILE="$PROJECT_DIR/cncar/pending.json"

# Load GEMINI_KEY from .env
set -a
# shellcheck disable=SC1091
source "$PROJECT_DIR/.env"
set +a

RUN_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$RUN_TIME] ▶ auto_story start" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

if "$VENV_PYTHON" cncar/main.py --auto-story >> "$LOG_FILE" 2>&1; then
    # Extract latest pending entry for notification
    PENDING_INFO=$("$VENV_PYTHON" - <<'EOF'
import json, pathlib, sys
f = pathlib.Path("cncar/pending.json")
if not f.exists():
    print("生成完成，请运行 --list 查看")
    sys.exit(0)
data = json.loads(f.read_text())
pending = [x for x in data if x.get("status") == "pending"]
if not pending:
    print("无待审记录")
    sys.exit(0)
latest = pending[-1]
mood = latest.get("mood", "?")
title = latest.get("title", "")[:40]
vid_id = latest.get("id", "?")
print(f"ID:{vid_id} [{mood}] {title}")
EOF
)
    echo "[$RUN_TIME] ✅ 成功 — $PENDING_INFO" >> "$LOG_FILE"
    osascript -e "display notification \"$PENDING_INFO\" with title \"CNcar 新视频待审\" subtitle \"运行 --list 查看所有 pending\""
else
    echo "[$RUN_TIME] ❌ 失败 — 见上方日志" >> "$LOG_FILE"
    osascript -e "display notification \"查看 cncar/logs/auto_story.log\" with title \"CNcar 生成失败\" subtitle \"$RUN_TIME\""
fi
