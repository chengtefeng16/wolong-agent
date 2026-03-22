# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

#!/bin/bash
set -e

PROJECT_ROOT="/Users/cheng/autogen_gemini_gui_test"
EXPORT_DIR="$PROJECT_ROOT/agentos_full_source_export"
TXT_FILE="$EXPORT_DIR/AgentOS_完整源代码汇总.txt"
ZIP_FILE="$PROJECT_ROOT/AgentOS_完整源代码包.zip"

rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"

echo "AgentOS 完整源代码汇总" > "$TXT_FILE"
echo "导出时间: $(date)" >> "$TXT_FILE"
echo "" >> "$TXT_FILE"

if [ -d "$PROJECT_ROOT/qianqiu_os" ]; then
  find "$PROJECT_ROOT/qianqiu_os" \
    \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.txt" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" \) \
    -not -path "*/__pycache__/*" \
    -not -path "*/logs/*" \
    -not -path "*/data/*" \
    | sort | while read -r file; do
        rel="${file#$PROJECT_ROOT/}"
        echo "==================================================" >> "$TXT_FILE"
        echo "FILE: $rel" >> "$TXT_FILE"
        echo "==================================================" >> "$TXT_FILE"
        cat "$file" >> "$TXT_FILE"
        echo "" >> "$TXT_FILE"
        echo "" >> "$TXT_FILE"
      done
fi

if [ -d "$PROJECT_ROOT/memory" ]; then
  find "$PROJECT_ROOT/memory" \
    \( -name "*.txt" -o -name "*.md" -o -name "*.json" \) \
    | sort | while read -r file; do
        rel="${file#$PROJECT_ROOT/}"
        echo "==================================================" >> "$TXT_FILE"
        echo "FILE: $rel" >> "$TXT_FILE"
        echo "==================================================" >> "$TXT_FILE"
        cat "$file" >> "$TXT_FILE"
        echo "" >> "$TXT_FILE"
        echo "" >> "$TXT_FILE"
      done
fi

rm -f "$ZIP_FILE"

cd "$PROJECT_ROOT"
zip -r "$ZIP_FILE" qianqiu_os memory \
  -x "*/__pycache__/*" \
  -x "*/logs/*" \
  -x "*/data/*" >/dev/null

echo "已生成:"
echo "$TXT_FILE"
echo "$ZIP_FILE"
