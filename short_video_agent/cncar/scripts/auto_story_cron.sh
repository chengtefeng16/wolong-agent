#!/bin/bash
# launchd daily runner: --auto-story → log → macOS notification
# Called by io.cncar.auto_story launchd job at 07:00 local time

PROJECT_DIR="/Users/cheng/autogen_gemini_gui_test/short_video_agent"
VENV_PYTHON="$PROJECT_DIR/../venv/bin/python3"
LOG_FILE="$PROJECT_DIR/cncar/logs/auto_story.log"
NOTIFY_FILE="$PROJECT_DIR/cncar/logs/pending_notify.txt"

# ── Fix PATH for launchd (doesn't inherit shell PATH) ──────────────────
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# ── Load GEMINI_KEY (and other keys) from .env ─────────────────────────
set -a
# shellcheck disable=SC1091
source "$PROJECT_DIR/.env"
set +a

RUN_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$RUN_TIME] ▶ auto_story start" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

# ── Send macOS notification (Python writes .scpt to avoid shell escaping) ──
_send_notification() {
    local msg_env="$1"   # passed as env var, not inline, to avoid any quoting issues
    local title="$2"
    CNCAR_NOTIF_MSG="$msg_env" \
    CNCAR_NOTIF_TITLE="$title" \
    "$VENV_PYTHON" - << 'PYEOF'
import subprocess, os, tempfile

msg   = os.environ.get("CNCAR_NOTIF_MSG",   "生成完成").replace('"', "'")
title = os.environ.get("CNCAR_NOTIF_TITLE", "CNcar").replace('"', "'")
subtitle = "运行 --list 查看所有 pending"

script = (
    f'display notification "{msg}" '
    f'with title "{title}" '
    f'subtitle "{subtitle}"'
)

tf = tempfile.NamedTemporaryFile(suffix=".scpt", mode="w",
                                  delete=False, encoding="utf-8")
tf.write(script)
tf.close()

result = subprocess.run(["osascript", tf.name],
                        capture_output=True, text=True)
os.unlink(tf.name)

if result.returncode != 0:
    print(f"[notify] osascript exit {result.returncode}: {result.stderr.strip()}", flush=True)
else:
    print("[notify] ✅ 通知已发送", flush=True)
PYEOF
}

# ── Run pipeline ────────────────────────────────────────────────────────
if "$VENV_PYTHON" cncar/main.py --auto-story >> "$LOG_FILE" 2>&1; then

    # Get latest pending entry info
    PENDING_INFO=$("$VENV_PYTHON" - << 'EOF'
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

    # Backup indicator: overwrite notify file so user can always check
    echo "$RUN_TIME  ✅ 新视频待审" >  "$NOTIFY_FILE"
    echo "$PENDING_INFO"             >> "$NOTIFY_FILE"
    echo "运行: cd short_video_agent && ../venv/bin/python3 cncar/main.py --list" >> "$NOTIFY_FILE"

    _send_notification "$PENDING_INFO" "CNcar 新视频待审"

else
    echo "[$RUN_TIME] ❌ 失败 — 见上方日志" >> "$LOG_FILE"

    echo "$RUN_TIME  ❌ 生成失败"             >  "$NOTIFY_FILE"
    echo "查看: $LOG_FILE"                    >> "$NOTIFY_FILE"

    _send_notification "查看 cncar/logs/auto_story.log" "CNcar 生成失败"
fi
