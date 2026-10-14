#!/bin/bash
# launchd 每周"内容自动更新"：先提炼(王利杰源 → 待导入CSV)，再导入(CSV → 素材库)。
# 由 io.dingxin.distill launchd 任务在每周一 09:30 调用。
# 写法参照 cncar/scripts/auto_story_cron.sh（修 PATH + source .env 拿 GEMINI_KEY/代理 + venv python）。

PROJECT_DIR="/Users/cheng/autogen_gemini_gui_test/short_video_agent"
VENV_PYTHON="$PROJECT_DIR/../venv/bin/python3"
LOG_FILE="$PROJECT_DIR/logs/distill_source.log"

mkdir -p "$PROJECT_DIR/logs"

# launchd 不继承 shell 的 PATH，手动补齐
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# 载入 .env（GEMINI_KEY、代理 HTTP(S)_PROXY 等；set -a 全部导出）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

RUN_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$RUN_TIME] ▶ 内容自动更新开始（distill → import）" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit 1

# 1) 提炼：王利杰源 → 待导入CSV（放进收件箱）
"$VENV_PYTHON" tools/distill_source.py >> "$LOG_FILE" 2>&1
echo "[$RUN_TIME] — 提炼结束 rc=$?，开始导入" >> "$LOG_FILE"

# 2) 导入：收件箱所有 待导入-*.csv → 素材库
"$VENV_PYTHON" tools/import_inbox.py >> "$LOG_FILE" 2>&1
echo "[$RUN_TIME] ◀ 全流程结束 rc=$?" >> "$LOG_FILE"
