# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    build-essential \
    # 图像处理依赖
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    libtesseract-dev \
    # PDF处理
    poppler-utils \
    # PostgreSQL客户端
    libpq-dev \
    postgresql-client \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --no-cache-dir --upgrade pip

# 先复制并安装基础依赖（这些很少变化，可以有效利用缓存）
COPY requirements-base.txt* ./
RUN if [ -f requirements-base.txt ]; then pip install --no-cache-dir -r requirements-base.txt; fi

# 复制并安装主要依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装额外的生产依赖（这些很少变化）
RUN pip install --no-cache-dir \
    gunicorn \
    uvicorn[standard] \
    psycopg2-binary \
    redis \
    prometheus-client

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads temp static backups

# 设置权限
RUN chmod +x scripts/*.py

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]