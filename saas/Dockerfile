# 卧龙 SaaS — Railway Dockerfile
# Stage 1: 构建前端
FROM node:20-slim AS frontend-builder
WORKDIR /build/frontend
COPY saas/frontend/package*.json ./
RUN npm ci
COPY saas/frontend/ ./
# 构建时注入环境变量（Railway 在 build 阶段通过 --build-arg 传入）
ARG VITE_API_BASE=https://api.wolong.ai
ARG VITE_META_APP_ID
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_META_APP_ID=${VITE_META_APP_ID}
RUN npm run build

# Stage 2: Python 后端
FROM python:3.11-slim
WORKDIR /app

COPY saas/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || true

# 复制后端源码
COPY saas/__init__.py ./saas/__init__.py
COPY saas/backend/ ./saas/backend/
COPY qianqiu_os/ ./qianqiu_os/

# 复制前端 build 产物（FastAPI 作为静态文件服务）
COPY --from=frontend-builder /build/frontend/dist/ ./frontend/dist/

ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000
CMD ["uvicorn", "saas.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
