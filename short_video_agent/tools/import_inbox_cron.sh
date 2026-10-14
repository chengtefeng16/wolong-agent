#!/bin/bash
# launchd 每周运行器：素材收件箱导入 → 日志（脚本内部再发 macOS 通知）
# 由 io.dingxin.import_inbox launchd 任务在每周一 09:30 调用。
# 写法参照 cncar/scripts/auto_story_cron.sh（PATH 修复 + source .env 拿代理）。

PROJECT_DIR="/Users/cheng/autogen_gemini_gui_test/short_video_agent"
VENV_PYTHON="$PROJECT_DIR/../venv/bin/python3"
LOG_FILE="$PROJECT_DIR/logs/import_inbox.log"

mkdir -p "$PROJECT_DIR/logs"

# launchd 不继承 shell 的 PATH，手动补齐
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# 载入 .env（代理 HTTP(S)_PROXY、密钥等；与 cncar 一致，set -a 全部导出）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

RUN_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$RUN_TIME] ▶ import_inbox 开始" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1
"$VENV_PYTHON" tools/import_inbox.py >> "$LOG_FILE" 2>&1
RC=$?

echo "[$RUN_TIME] ◀ import_inbox 结束 rc=$RC" >> "$LOG_FILE"
exit $RC
