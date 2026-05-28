#!/bin/bash
# 先启动 API 服务器，确认端口就绪后再启动 ngrok

# 下载 ngrok（如果不存在）
if [ ! -f /usr/local/bin/ngrok ]; then
    echo "[ngrok] 安装 ngrok..."
    curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar xz -C /usr/local/bin/
fi

# 启动 API 服务器（后台）
echo "[API] 启动 API 服务器..."
python3 scripts/api_server.py &
API_PID=$!

# 等待端口真正就绪（最多等 5 分钟）
TARGET_PORT=${PORT:-8765}
echo "[API] 等待端口 $TARGET_PORT 就绪..."
for i in $(seq 1 60); do
    if nc -z localhost $TARGET_PORT 2>/dev/null; then
        echo "[API] 端口 $TARGET_PORT 已就绪（${i}秒）"
        break
    fi
    sleep 5
done

# 启动 ngrok
if [ -n "$NGROK_AUTHTOKEN" ]; then
    ngrok config add-authtoken $NGROK_AUTHTOKEN
    echo "[ngrok] 启动固定域名隧道（端口 $TARGET_PORT）..."
    ngrok http $TARGET_PORT --url=porter-unsimultaneous-nonopprobriously.ngrok-free.dev --log=stdout > /tmp/ngrok.log 2>&1 &
    sleep 3
    echo "[ngrok] 隧道已启动"
else
    echo "[ngrok] 未配置 NGROK_AUTHTOKEN，跳过"
fi

# 保持容器运行
wait $API_PID
