# 卧龙 Agent — Railway 生产 Dockerfile

FROM node:20-slim AS h5-builder
WORKDIR /build/wolong_h5_console
COPY wolong_h5_console/package.json wolong_h5_console/package-lock.json ./
RUN npm ci
COPY wolong_h5_console/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true
COPY scripts/ ./scripts/
COPY qianqiu_os/ ./qianqiu_os/
COPY --from=h5-builder /build/wolong_h5_console/dist/ ./wolong_h5_console/dist/
COPY wolong_h5_console/public/ ./wolong_h5_console/public/
ENV PYTHONPATH=/app
ENV PORT=8765
EXPOSE 8765
COPY scripts/start_railway.sh ./scripts/
CMD ["bash", "scripts/start_railway.sh"]
