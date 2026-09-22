# 卧龙 SaaS — Railway Dockerfile
# 构建上下文：saas/（rootDirectory=saas）

# Stage 1: 构建 React 前端
FROM node:20-slim AS saas-frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE
ARG VITE_META_APP_ID
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_META_APP_ID=${VITE_META_APP_ID}
RUN npm run build

# Stage 2: Python 后端
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制 saas 包（rootDirectory=saas 时 COPY 路径相对于 saas/）
COPY __init__.py ./saas/__init__.py
COPY backend/ ./saas/backend/

# 前端 build 产物
COPY --from=saas-frontend-builder /build/frontend/dist/ ./frontend/dist/

ENV PYTHONPATH=/app
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "saas.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
