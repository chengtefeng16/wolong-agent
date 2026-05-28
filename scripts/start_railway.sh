#!/bin/bash
# 启动 API 服务器，再启动 ngrok

# 下载 ngrok（如果不存在）
if [ ! -f /usr/local/bin/ngrok ]; then
    echo "[ngrok] 安装 ngrok..."
    curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar xz -C /usr/local/bin/
fi

# 先启动 API 服务器（后台）
echo "[API] 启动 API 服务器..."
python3 scripts/api_server.py &
API_PID=$!

# 等待 API 服务器真正绑定端口
echo "[API] 等待服务器就绪..."
sleep 8

# 再启动 ngrok
if [ -n "$NGROK_AUTHTOKEN" ]; then
    ngrok config add-authtoken $NGROK_AUTHTOKEN
    echo "[ngrok] 启动固定域名隧道..."
    ngrok http ${PORT:-8765} --url=porter-unsimultaneous-nonopprobriously.ngrok-free.dev --log=stdout > /tmp/ngrok.log 2>&1 &
    sleep 3
    echo "[ngrok] 隧道已启动"
else
    echo "[ngrok] 未配置 NGROK_AUTHTOKEN，跳过"
fi

# 等待 API 服务器进程（保持容器运行）
wait $API_PID
