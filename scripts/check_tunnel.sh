#!/bin/bash
# 检查当前有效的 localhost.run 隧道 URL
LATEST_URL=$(grep -oE 'https://[a-zA-Z0-9_-]+\.lhr\.life' /tmp/tunnel.log | tail -1)
if [ -z "$LATEST_URL" ]; then
  echo "❌ 未找到隧道 URL"
  exit 1
fi
# 测试是否可用
RESULT=$(curl -s --max-time 4 "${LATEST_URL}/webhook?hub.mode=subscribe&hub.verify_token=wolong_webhook_token&hub.challenge=PING" 2>&1)
if [ "$RESULT" = "PING" ]; then
  echo "✅ 当前有效隧道: ${LATEST_URL}/webhook"
else
  # 尝试所有 URL
  for url in $(grep -oE 'https://[a-zA-Z0-9_-]+\.lhr\.life' /tmp/tunnel.log | sort -u); do
    R=$(curl -s --max-time 3 "${url}/webhook?hub.mode=subscribe&hub.verify_token=wolong_webhook_token&hub.challenge=PING" 2>&1)
    if [ "$R" = "PING" ]; then
      echo "✅ 当前有效隧道: ${url}/webhook"
      exit 0
    fi
  done
  echo "❌ 所有已知隧道均不可用，请重启隧道"
fi
