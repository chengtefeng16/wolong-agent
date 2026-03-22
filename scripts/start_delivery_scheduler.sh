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

PROJECT_DIR="/Users/cheng/autogen_gemini_gui_test"
PYTHON_BIN="$PROJECT_DIR/.venv_pdf/bin/python"

cd "$PROJECT_DIR"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "ERROR: .venv_pdf python not found: $PYTHON_BIN"
  exit 1
fi

exec "$PYTHON_BIN" qianqiu_os/services/runtime_delivery_scheduler_v1.py --loop --interval 10
