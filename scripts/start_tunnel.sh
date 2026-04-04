#!/bin/bash
# localhost.run SSH 隧道 - 公网暴露本地 8765 端口
# 用专用密钥保证子域名尽量稳定
ssh -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -i ~/.ssh/localhost_run_key \
    -R 80:localhost:8765 \
    nokey@localhost.run
