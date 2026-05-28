# ================================================================
# 卧龙 Agent — Railway 生产 Dockerfile
# 单容器：Python API 服务器 + Vite H5（预构建静态文件）
# ================================================================

# Stage 1: 构建 H5（Node 环境）
FROM node:20-slim AS h5-builder

WORKDIR /build/wolong_h5_console
COPY wolong_h5_console/package.json wolong_h5_console/package-lock.json ./
RUN npm ci

COPY wolong_h5_console/ ./
RUN npm run build

# Stage 2: Python API 服务器（运行时）
FROM python:3.11-slim

# 基础工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖（仅 anthropic SDK，其余标准库）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true

# 复制项目代码
COPY scripts/ ./scripts/
COPY qianqiu_os/ ./qianqiu_os/

# 复制 H5 build 产物（来自 Stage 1）
COPY --from=h5-builder /build/wolong_h5_console/dist/ ./wolong_h5_console/dist/

# 复制 H5 public 目录（runtime 静态数据 fallback）
COPY wolong_h5_console/public/ ./wolong_h5_console/public/

# 将项目根加入 Python 路径
ENV PYTHONPATH=/app

# Railway 注入 PORT 环境变量
ENV PORT=8765

# 暴露端口（文档用，Railway 实际用 $PORT）
EXPOSE 8765

# 启动 API 服务器（自动读取 $PORT）
COPY scripts/start_railway.sh ./scripts/
CMD ["bash", "scripts/start_railway.sh"]
