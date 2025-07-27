from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.middleware import SecurityHeadersMiddleware, HTTPSRedirectMiddleware, RequestLoggingMiddleware, RequestIDMiddleware, RateLimitMiddleware
from app.middleware.monitoring import MonitoringMiddleware
from app.core.monitoring import monitor, setup_monitoring, PROMETHEUS_AVAILABLE
from app.core.exceptions import (
    BaseAPIException,
    base_api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
import os
import logging
from datetime import datetime, timezone
from sqlalchemy import text

# 设置日志
settings.setup_logging()
logger = logging.getLogger(__name__)

# 设置监控系统
setup_monitoring()

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
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
    - 用户注册和认证
    - JWT令牌安全认证
    - 权限控制
    
    ### 📊 数据分析
    - OCR处理统计
    - 项目审查报告
    - 系统使用分析
    
    **技术栈**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
    """,
    version=settings.VERSION,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    contact={
        "name": "系统管理员",
        "email": "admin@gov-procurement.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS.split(","),
    allow_headers=settings.ALLOWED_HEADERS.split(",") if settings.ALLOWED_HEADERS != "*" else ["*"],
)

# 添加请求ID中间件（应该在最前面）
app.add_middleware(RequestIDMiddleware)

# 添加安全中间件
if getattr(settings, 'ENABLE_SECURITY_HEADERS', True):
    app.add_middleware(SecurityHeadersMiddleware)

if settings.is_production and getattr(settings, 'FORCE_HTTPS', False):
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(RequestLoggingMiddleware)

# 添加限流中间件
app.add_middleware(RateLimitMiddleware)

# 添加监控中间件
app.add_middleware(MonitoringMiddleware)

# 创建静态文件目录（如果不存在）
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 全局异常处理
# 注册自定义异常处理器
app.add_exception_handler(BaseAPIException, base_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 根路径 - 重定向到前端页面
@app.get(
    "/",
    summary="系统首页",
    description="访问系统前端界面",
    tags=["系统信息"]
)
async def root():
    from fastapi.responses import FileResponse
    import os
    static_file_path = os.path.join(os.getcwd(), 'static', 'index.html')
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    else:
        raise HTTPException(status_code=404, detail="Index file not found")

# API信息端点
@app.get(
    "/api/info",
    summary="API信息",
    description="获取API基本信息和文档链接",
    tags=["系统信息"]
)
async def api_info():
    return {
        "message": "政府采购项目审查分析系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_test": "/static/api-test.html",
        "features": [
            "OCR文字识别",
            "项目管理",
            "用户认证",
            "数据分析"
        ]
    }

# 数据库连接检查
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 健康检查端点
@app.get(
    settings.HEALTH_CHECK_PATH,
    summary="系统健康检查",
    description="检查系统运行状态和各组件健康状况",
    tags=["系统信息"]
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
    
    # 整体健康状态
    is_healthy = db_status == "connected" and upload_dir_exists
    
    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "message": "系统运行正常" if is_healthy else "系统存在问题",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "components": {
            "database": {
                "status": db_status,
                "error": db_error
            },
            "file_system": {
                "upload_dir": upload_dir_exists,
                "log_dir": log_dir_exists
            },
            "api": "running"
        }
    }
    
    return health_data

# 就绪检查端点
@app.get(
    "/ready",
    summary="就绪检查",
    description="检查系统是否准备好接收请求",
    tags=["系统信息"]
)
async def readiness_check(db: SessionLocal = Depends(get_db)):
    """就绪检查端点"""
    try:
        # 检查数据库连接
        db.execute(text("SELECT 1"))
        
        # 检查必要目录
        if not os.path.exists(settings.UPLOAD_DIR):
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        return {
            "status": "ready",
            "message": "系统已准备就绪",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="系统未就绪")

# Prometheus指标端点 (如果启用)
if settings.ENABLE_METRICS and PROMETHEUS_AVAILABLE:
    @app.get(
        settings.METRICS_PATH,
        summary="Prometheus指标",
        description="获取系统监控指标",
        tags=["监控"]
    )
    async def metrics():
        """Prometheus指标端点"""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi import Response
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
elif settings.ENABLE_METRICS:
    @app.get(
        settings.METRICS_PATH,
        summary="Prometheus指标",
        description="获取系统监控指标",
        tags=["监控"]
    )
    async def metrics():
        """Prometheus指标端点 - 未安装prometheus_client"""
        return {"message": "Metrics endpoint - prometheus_client库未安装"}

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)