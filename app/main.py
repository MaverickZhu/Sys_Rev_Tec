from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
import os

# 创建FastAPI应用实例
app = FastAPI(
    title="政府采购项目审查分析系统",
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
    
    **技术栈**: FastAPI + MongoDB + Docker
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件目录（如果不存在）
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code}
    )

# 根路径 - 重定向到前端页面
@app.get(
    "/",
    summary="系统首页",
    description="访问系统前端界面",
    tags=["系统信息"]
)
async def root():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

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

# 健康检查端点
@app.get(
    "/health",
    summary="系统健康检查",
    description="检查系统运行状态和各组件健康状况",
    tags=["系统信息"]
)
async def health_check():
    return {
        "status": "healthy", 
        "message": "系统运行正常",
        "timestamp": "2024-01-01T00:00:00Z",
        "components": {
            "database": "connected",
            "ocr_engines": "available",
            "api": "running"
        }
    }

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)