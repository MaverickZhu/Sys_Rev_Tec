# AI服务 Dockerfile
# 基于 Python 3.11 构建，包含向量化和智能搜索功能

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-ai.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-ai.txt

# 复制应用代码
COPY app/ ./app/
COPY ai_service/ ./ai_service/
COPY docker/ai/entrypoint.sh ./entrypoint.sh

# 创建必要的目录
RUN mkdir -p /app/uploads /app/temp /app/models /app/logs

# 设置权限
RUN chmod +x ./entrypoint.sh

# 创建非root用户
RUN groupadd -r aiuser && useradd -r -g aiuser aiuser
RUN chown -R aiuser:aiuser /app
USER aiuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 暴露端口
EXPOSE 8001

# 启动命令
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]