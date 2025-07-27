#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务主应用
提供向量化、智能搜索和AI增强功能的FastAPI服务
"""

import os
import sys
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_service.config import get_settings
from ai_service.database import get_vector_db, close_vector_db
from ai_service.utils.cache import get_cache_manager, close_cache_manager
from ai_service.utils.logging import setup_logging, StructuredLogger
from ai_service.vectorization import get_vectorization_service
from ai_service.search import get_search_service
from ai_service.api import vectorization, search, health

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# Prometheus指标
REQUEST_COUNT = Counter(
    'ai_service_requests_total',
    'Total AI service requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'ai_service_request_duration_seconds',
    'AI service request duration',
    ['method', 'endpoint']
)

VECTORIZATION_COUNT = Counter(
    'ai_service_vectorization_total',
    'Total vectorization operations',
    ['model', 'status']
)

SEARCH_COUNT = Counter(
    'ai_service_search_total',
    'Total search operations',
    ['search_type', 'status']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动AI服务...")
    
    # 启动时初始化
    settings = get_settings()
    
    try:
        # 初始化数据库连接
        vector_db = await get_vector_db()
        logger.info("✅ 向量数据库连接成功")
        
        # 初始化缓存管理器
        cache_manager = await get_cache_manager()
        logger.info("✅ 缓存管理器初始化成功")
        
        # 初始化服务
        vectorization_service = get_vectorization_service()
        search_service = get_search_service()
        
        # 预热模型（如果启用）
        if settings.AI_MODEL_PRELOAD:
            logger.info("🔥 预热AI模型...")
            try:
                await vectorization_service.preload_models()
                logger.info("✅ AI模型预热完成")
            except Exception as e:
                logger.warning(f"⚠️ AI模型预热失败: {e}")
        
        # 启动Prometheus指标服务器
        if settings.PROMETHEUS_ENABLED:
            start_http_server(settings.PROMETHEUS_PORT)
            logger.info(f"📊 Prometheus指标服务器启动在端口 {settings.PROMETHEUS_PORT}")
        
        logger.info("🎉 AI服务启动完成")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ AI服务启动失败: {e}")
        raise
    
    # 关闭时清理
    logger.info("🛑 关闭AI服务...")
    
    try:
        # 关闭数据库连接
        if 'vector_db' in locals():
            await vector_db.close()
            logger.info("✅ 向量数据库连接已关闭")
        
        # 关闭缓存管理器
        await close_cache_manager()
        logger.info("✅ 缓存管理器已关闭")
        
        logger.info("✅ AI服务关闭完成")
        
    except Exception as e:
        logger.error(f"❌ AI服务关闭时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="AI服务",
    description="系统评审技术平台 - AI向量化和智能搜索服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 获取配置
settings = get_settings()

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)




@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """请求指标中间件"""
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 记录指标
    duration = time.time() - start_time
    method = request.method
    endpoint = request.url.path
    status = str(response.status_code)
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    # 记录请求
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 记录响应
    duration = time.time() - start_time
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {duration:.3f}s"
    )
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(
        f"❌ HTTP异常: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        f"💥 未处理异常: {type(exc).__name__}: {str(exc)} - "
        f"Path: {request.url.path}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误",
                "timestamp": time.time(),
                "path": str(request.url.path)
            }
        }
    )


# 注册路由
app.include_router(health.router, prefix="", tags=["健康检查"])
app.include_router(vectorization.router, prefix="/api/v1/vectorization", tags=["向量化"])
app.include_router(search.router, prefix="/api/v1/search", tags=["智能搜索"])


@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "AI服务",
        "version": "1.0.0",
        "description": "系统评审技术平台 - AI向量化和智能搜索服务",
        "status": "运行中",
        "timestamp": time.time(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/metrics",
            "vectorization": "/api/v1/vectorization",
            "search": "/api/v1/search"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AI_SERVICE_PORT", "8001"))
    workers = int(os.getenv("AI_SERVICE_WORKERS", "1"))
    
    logger.info(f"🚀 启动AI服务在 {host}:{port}")
    
    uvicorn.run(
        "ai_service.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )