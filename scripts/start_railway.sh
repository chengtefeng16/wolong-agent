#!/bin/bash
# 直接启动 API 服务器，使用 Railway 自带公网域名

echo "[API] 启动 API 服务器..."
exec python3 scripts/api_server.py
