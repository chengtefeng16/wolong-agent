#!/bin/bash
# 安装并启动 ngrok，然后启动 API 服务器

# 下载 ngrok
if [ ! -f /usr/local/bin/ngrok ]; then
    echo "[ngrok] 安装 ngrok..."
    curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar xz -C /usr/local/bin/
fi

# 配置 ngrok authtoken
if [ -n "$NGROK_AUTHTOKEN" ]; then
    ngrok config add-authtoken $NGROK_AUTHTOKEN
    echo "[ngrok] 启动固定域名隧道..."
    ngrok http 8765 --url=porter-unsimultaneous-nonopprobriously.ngrok-free.dev --log=stdout > /tmp/ngrok.log 2>&1 &
    sleep 3
    echo "[ngrok] 隧道已启动"
else
    echo "[ngrok] 未配置 NGROK_AUTHTOKEN，跳过"
fi

# 启动 API 服务器
exec python3 scripts/api_server.py
