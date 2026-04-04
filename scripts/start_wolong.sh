#!/bin/bash
# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================
#
# 卧龙 Agent 一键启动脚本
# 同时启动：
#   1. H5 前端（Vite dev server，端口 5173）
#   2. 后端 API 服务器（端口 8765）
#   3. Runtime 数据同步监听（每 5 秒同步一次）
#   4. ngrok 永久隧道（公网 Webhook 接收，固定域名）
#   5. WABA 订阅激活（确保 Meta 推送真实消息到 Webhook）
#
# 用法：
#   chmod +x scripts/start_wolong.sh
#   ./scripts/start_wolong.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
H5_DIR="$PROJECT_ROOT/wolong_h5_console"

# ── Python 环境：优先 .venv_delivery（含 google-genai / Gemini SDK）──
VENV_PYTHON="$PROJECT_ROOT/.venv_delivery/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="$(which python3)"
    echo "[WARNING] .venv_delivery 未找到，使用系统 python3: $VENV_PYTHON"
fi
echo "[Python] 使用: $VENV_PYTHON"

echo "================================================================"
echo " 卧龙 Agent 系统启动（Gemini API 已启用）"
echo " 项目根目录: $PROJECT_ROOT"
echo "================================================================"

# 检查 node_modules
if [ ! -d "$H5_DIR/node_modules" ]; then
    echo "[H5] 安装前端依赖..."
    cd "$H5_DIR" && npm install
    cd "$PROJECT_ROOT"
fi

# 先做一次同步
echo "[sync] 初始化 runtime 数据..."
"$VENV_PYTHON" "$SCRIPT_DIR/sync_runtime_to_h5.py"

# 启动后端 API 服务器（后台，使用 venv_delivery 以获得 Gemini SDK）
echo "[API] 启动后端 API 服务器（端口 8765，Gemini 已接入）..."
PYTHONPATH="$PROJECT_ROOT" "$VENV_PYTHON" "$SCRIPT_DIR/api_server.py" &
API_PID=$!
echo "[API] PID: $API_PID"

# 启动 runtime 同步监听（后台）
echo "[sync] 启动 runtime 数据同步监听..."
"$VENV_PYTHON" "$SCRIPT_DIR/sync_runtime_to_h5.py" --watch &
SYNC_PID=$!
echo "[sync] PID: $SYNC_PID"

# 启动 H5 前端（前台，Ctrl+C 时会停止所有）
echo "[H5] 启动卧龙 H5 控制台（端口 5173）..."
echo ""
echo "================================================================"
echo " 启动完成后访问: http://localhost:5173"
echo " API 服务器地址: http://localhost:8765"
echo " 按 Ctrl+C 停止所有服务"
echo "================================================================"
echo ""

# 启动 ngrok 永久隧道（固定域名，重启不变）
echo "[tunnel] 启动 ngrok 永久隧道..."
pkill -f "ngrok" 2>/dev/null
pkill -f "cloudflared" 2>/dev/null
sleep 1
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy \
  nohup ngrok http 8765 --url=porter-unsimultaneous-nonopprobriously.ngrok-free.dev --log=stdout \
  > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
echo "[tunnel] PID: $NGROK_PID"
sleep 5
if grep -q "started tunnel" /tmp/ngrok.log 2>/dev/null; then
    echo "[tunnel] ✅ 永久隧道已连接"
else
    echo "[tunnel] ⚠️  隧道启动中，请稍候..."
fi
echo ""
echo "  Webhook 永久地址: https://porter-unsimultaneous-nonopprobriously.ngrok-free.dev/webhook"
echo "  验证口令: wolong_webhook_token"
echo ""

# 激活 WABA 订阅（确保 Meta 把真实 WhatsApp 消息推送到本 App 的 Webhook）
echo "[WABA] 激活 Meta WhatsApp 订阅..."
WABA_ID="2817262535309287"
WHATSAPP_TOKEN="${WHATSAPP_ACCESS_TOKEN:-}"
if [ -n "$WHATSAPP_TOKEN" ]; then
    SUBSCRIBE_RESULT=$(env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy \
        curl -s -X POST \
        "https://graph.facebook.com/v20.0/${WABA_ID}/subscribed_apps" \
        -H "Authorization: Bearer ${WHATSAPP_TOKEN}" \
        2>/dev/null)
    if echo "$SUBSCRIBE_RESULT" | grep -q '"success":true'; then
        echo "[WABA] ✅ WABA 订阅已激活（Meta 将推送真实消息到 Webhook）"
    else
        echo "[WABA] ⚠️  WABA 订阅激活失败，请检查 WHATSAPP_ACCESS_TOKEN"
        echo "[WABA]    返回: $SUBSCRIBE_RESULT"
    fi
else
    echo "[WABA] ⚠️  未设置 WHATSAPP_ACCESS_TOKEN，跳过 WABA 订阅激活"
    echo "[WABA]    请在 .env 中配置，或执行: export WHATSAPP_ACCESS_TOKEN=<token>"
fi
echo ""

# 注册退出时清理
trap "echo '正在停止所有服务...'; kill $API_PID $SYNC_PID $NGROK_PID 2>/dev/null; exit 0" INT TERM

cd "$H5_DIR" && npm run dev
