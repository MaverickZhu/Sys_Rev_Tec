# OCR 服务 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    pkg-config \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制OCR服务相关的Python依赖
COPY docker/ocr/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制OCR服务代码
COPY ocr_service.py /app/
COPY app/ /app/app/

# 创建必要的目录
RUN mkdir -p /app/uploads /app/temp /app/logs

# 设置权限
RUN chmod -R 755 /app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 暴露端口（如果OCR服务有HTTP接口）
EXPOSE 8001

# 启动OCR服务
CMD ["python", "ocr_service.py"]