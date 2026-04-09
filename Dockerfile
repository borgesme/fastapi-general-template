# ============ Stage 1: Builder ============
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 安装所有依赖（包含 alembic）
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============ Stage 2: Production ============
FROM python:3.12-slim

# 安全：非 root 运行
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# 安装运行时依赖（无 gcc）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制已安装的包（包含 alembic）
COPY --from=builder /install /usr/local

# 复制应用代码
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup entrypoint.sh ./

# 创建日志目录并授权
RUN mkdir -p /app/logs && chown appuser:appgroup /app/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# 切换非 root 用户
USER appuser

# 默认环境变量（可被 docker-compose 或运行时 -e 覆盖）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=false

EXPOSE 8000

# 启动脚本：先跑迁移，再启动 uvicorn
ENTRYPOINT ["bash", "entrypoint.sh"]

