import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    BaseAPIException,
    base_api_exception_handler,
    general_exception_handler,
    http_exception_handler,
    response_validation_exception_handler,
    validation_exception_handler,
)
from app.db.session import SessionLocal, get_db
from app.middleware.monitoring import (
    MonitoringMiddleware,
    setup_monitoring,
)
from app.middleware.enhanced_monitoring import (
    EnhancedMonitoringMiddleware,
    start_enhanced_monitoring,
    stop_enhanced_monitoring,
)
from app.middleware.request_id import RequestIDMiddleware
from app.services.cache_init import initialize_cache_system, shutdown_cache_system

# 设置日志
settings.setup_logging()
logger = logging.getLogger(__name__)

# 设置监控系统
setup_monitoring()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting application...")
    
    # 初始化缓存系统
    if settings.CACHE_ENABLED:
        logger.info("Initializing cache system...")
        cache_init_success = await initialize_cache_system()
        if cache_init_success:
            logger.info("Cache system initialized successfully")
        else:
            logger.warning("Cache system initialization failed, continuing without cache")
    else:
        logger.info("Cache system disabled")
    
    # 启动增强监控系统
    logger.info("Starting enhanced monitoring system...")
    try:
        await start_enhanced_monitoring()
        logger.info("Enhanced monitoring system started successfully")
    except Exception as e:
        logger.error(f"Failed to start enhanced monitoring system: {e}")
    
    logger.info("Application startup completed")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down application...")
    
    # 停止增强监控系统
    logger.info("Stopping enhanced monitoring system...")
    try:
        await stop_enhanced_monitoring()
        logger.info("Enhanced monitoring system stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop enhanced monitoring system: {e}")
    
    # 关闭缓存系统
    if settings.CACHE_ENABLED:
        logger.info("Shutting down cache system...")
        await shutdown_cache_system()
        logger.info("Cache system shutdown completed")
    
    logger.info("Application shutdown completed")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    description="""
    ## 政府采购项目审查分析系统 API

    这是一个专为政府采购项目审查设计的智能分析系统，提供以下核心功能：

    ### 🔍 OCR文字识别
    - 多引擎智能选择（PaddleOCR、EasyOCR、TesseractOCR）
    - 中文文档优化识别
    - 手写文字识别支持
    - 批量文档处理

    ### 📋 项目管理
    - 项目创建和管理
    - 文档上传和组织
    - 审查流程跟踪

    ### 👥 用户管理
    - 用户注册和管理
    - 简化的用户系统

    ### 📊 数据分析
    - OCR处理统计
    - 项目审查报告
    - 系统使用分析

    **技术栈**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
    """,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    contact={"name": "系统管理员", "email": "admin@gov-procurement.com"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS.split(","),
    allow_headers=(
        settings.ALLOWED_HEADERS.split(",")
        if settings.ALLOWED_HEADERS != "*"
        else ["*"]
    ),
)

# 添加请求ID中间件（应该在最前面）
app.add_middleware(RequestIDMiddleware)

# 添加增强监控中间件
app.add_middleware(EnhancedMonitoringMiddleware)

# 添加基础监控中间件
app.add_middleware(MonitoringMiddleware)

# 创建静态文件目录（如果不存在）
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 全局异常处理
# 注册全局异常处理器
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(
    ResponseValidationError, response_validation_exception_handler
)
app.add_exception_handler(Exception, general_exception_handler)


# 根路径 - 重定向到前端页面
@app.get("/", summary="系统首页", description="访问系统前端界面", tags=["系统信息"])
async def root():
    """系统首页"""
    static_file_path = os.path.join(os.getcwd(), "static", "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    else:
        raise HTTPException(status_code=404, detail="Index file not found")


# 性能监控仪表板
@app.get(
    "/dashboard",
    summary="性能监控仪表板",
    description="访问系统性能监控仪表板",
    tags=["系统信息"],
)
async def performance_dashboard():
    """性能监控仪表板"""
    dashboard_file_path = os.path.join(os.getcwd(), "frontend", "performance-dashboard.html")
    if os.path.exists(dashboard_file_path):
        return FileResponse(dashboard_file_path)
    else:
        raise HTTPException(status_code=404, detail="Performance dashboard not found")


# API信息端点
@app.get(
    "/api/info",
    summary="API信息",
    description="获取API基本信息和文档链接",
    tags=["系统信息"],
)
async def api_info():
    """API信息"""
    return {
        "message": "政府采购项目审查分析系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_test": "/static/api-test.html",
        "dashboard": "/dashboard",
        "features": ["OCR文字识别", "项目管理", "用户管理", "数据分析", "性能监控"],
    }


# 健康检查端点
@app.get(
    settings.HEALTH_CHECK_PATH,
    summary="系统健康检查",
    description="检查系统运行状态和各组件健康状况",
    tags=["系统信息"],
)
async def health_check(db: SessionLocal = Depends(get_db)):
    """系统健康检查端点"""
    try:
        # 检查数据库连接
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db_error = None
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        logger.error(f"Database health check failed: {e}")

    # 检查上传目录
    upload_dir_exists = os.path.exists(settings.UPLOAD_DIR)

    # 检查日志目录
    log_dir_exists = os.path.exists(os.path.dirname(settings.LOG_FILE))
    
    # 检查缓存系统状态
    cache_status = "disabled"
    cache_error = None
    if settings.CACHE_ENABLED:
        try:
            from app.services.cache_init import get_cache_system_status
            cache_system_status = get_cache_system_status()
            cache_status = "healthy" if cache_system_status["initialized"] else "unhealthy"
        except Exception as e:
            cache_status = "error"
            cache_error = str(e)
            logger.error(f"Cache system health check failed: {e}")

    # 整体健康状态
    is_healthy = (
        db_status == "connected" 
        and upload_dir_exists 
        and (not settings.CACHE_ENABLED or cache_status in ["healthy", "disabled"])
    )

    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error,
            },
            "upload_directory": {
                "status": "exists" if upload_dir_exists else "missing",
                "path": settings.UPLOAD_DIR,
            },
            "log_directory": {
                "status": "exists" if log_dir_exists else "missing",
                "path": os.path.dirname(settings.LOG_FILE),
            },
            "cache_system": {
                "status": cache_status,
                "enabled": settings.CACHE_ENABLED,
                "error": cache_error,
            },
        },
    }

    status_code = 200 if is_healthy else 503
    return Response(
        content=str(health_data), status_code=status_code, media_type="application/json"
    )


# Prometheus监控指标端点
@app.get("/metrics", summary="监控指标", tags=["系统信息"])
async def metrics():
    """Prometheus监控指标"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
