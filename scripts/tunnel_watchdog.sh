#!/bin/bash
# tunnel_watchdog.sh - 监控隧道URL变化，自动重启隧道并更新 Meta webhook
# 用法: bash scripts/tunnel_watchdog.sh

source "$(dirname "$0")/../.env" 2>/dev/null || true

APP_ID="${WHATSAPP_APP_ID:-941216881630307}"
APP_SECRET="${WHATSAPP_APP_SECRET:-528757903896e0b3aeef95ce4cced4d9}"
VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-wolong_webhook_token}"
KEY_FILE="$HOME/.ssh/localhost_run_key"
LAST_URL=""

update_meta_webhook() {
  local url="$1"
  local callback="${url}/webhook"
  # Get app access token
  local TOKEN=$(curl -s "https://graph.facebook.com/oauth/access_token?client_id=${APP_ID}&client_secret=${APP_SECRET}&grant_type=client_credentials" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
  if [ -z "$TOKEN" ]; then
    echo "[watchdog] ⚠️  无法获取 App Token，跳过自动更新"
    echo "[watchdog] 📋 请手动更新 Meta Webhook 地址为: $callback"
    return
  fi
  # Try to update subscription
  local RESULT=$(curl -s -X POST "https://graph.facebook.com/v19.0/${APP_ID}/subscriptions" \
    --data-urlencode "object=whatsapp_business_account" \
    --data-urlencode "callback_url=${callback}" \
    --data-urlencode "verify_token=${VERIFY_TOKEN}" \
    --data-urlencode "fields=messages" \
    --data-urlencode "access_token=${TOKEN}" 2>/dev/null)
  echo "[watchdog] Meta API 响应: $RESULT"
  echo "[watchdog] 📋 新地址: $callback （请确认 Meta Developer Console 已更新）"
}

start_tunnel() {
  # Kill existing
  pkill -f "nokey@localhost.run" 2>/dev/null
  sleep 1
  # Start fresh
  nohup ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=10 \
    -o ServerAliveCountMax=6 \
    -o ExitOnForwardFailure=yes \
    -i "$KEY_FILE" \
    -R 80:localhost:8765 \
    nokey@localhost.run > /tmp/tunnel.log 2>&1 &
  echo "[watchdog] 隧道已重启 (PID $!)"
}

echo "[watchdog] 🚀 启动隧道守护进程..."
start_tunnel

while true; do
  sleep 5
  # Get latest URL from log
  CURRENT_URL=$(grep -oE 'https://[a-zA-Z0-9_-]+\.lhr\.life' /tmp/tunnel.log 2>/dev/null | tail -1)
  
  if [ -z "$CURRENT_URL" ]; then
    echo "[watchdog] ⚠️  未检测到隧道URL，重启中..."
    start_tunnel
    sleep 8
    continue
  fi
  
  # Test if it's alive
  RESP=$(curl -s --max-time 3 "${CURRENT_URL}/webhook?hub.mode=subscribe&hub.verify_token=${VERIFY_TOKEN}&hub.challenge=PING" 2>&1)
  
  if [ "$RESP" != "PING" ]; then
    echo "[watchdog] ⚠️  隧道无响应，重启中..."
    start_tunnel
    sleep 8
    continue
  fi
  
  # Check if URL changed
  if [ "$CURRENT_URL" != "$LAST_URL" ]; then
    TS=$(date '+%H:%M:%S')
    echo "[$TS] 🔄 隧道URL变化: $CURRENT_URL"
    update_meta_webhook "$CURRENT_URL"
    LAST_URL="$CURRENT_URL"
  fi
done
