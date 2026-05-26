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

# 切换到项目目录（很重要）
cd /Users/cheng/autogen_gemini_gui || exit 1

# 激活虚拟环境
source venv/bin/activate

# 启动 Gradio
python3 ui_gradio.py

