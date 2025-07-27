from fastapi import APIRouter

from app.api.v1.endpoints import login, users, projects, documents, vector
from app.api.v1 import health, ocr, cache

api_router = APIRouter()

# 健康检查相关路由（无需认证）
api_router.include_router(
    health.router,
    tags=["🏥 健康检查"],
    responses={
        503: {"description": "服务不可用"}
    }
)

# 用户认证相关路由
api_router.include_router(
    login.router, 
    tags=["🔐 用户认证"],
    responses={
        400: {"description": "认证失败"},
        401: {"description": "未授权访问"}
    }
)

# 用户管理相关路由
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["👥 用户管理"],
    responses={
        400: {"description": "请求参数错误"},
        409: {"description": "用户已存在"}
    }
)

# 项目管理相关路由
api_router.include_router(
    projects.router, 
    prefix="/projects", 
    tags=["📋 项目管理"],
    responses={
        401: {"description": "需要登录认证"},
        404: {"description": "项目不存在"}
    }
)

# 文档管理相关路由
api_router.include_router(
    documents.router, 
    prefix="/documents", 
    tags=["📄 文档管理"],
    responses={
        401: {"description": "需要登录认证"},
        404: {"description": "文档不存在"},
        413: {"description": "文件过大"},
        415: {"description": "不支持的文件类型"}
    }
)

# OCR文字识别相关路由
api_router.include_router(
    ocr.router, 
    prefix="/ocr", 
    tags=["🔍 OCR文字识别"],
    responses={
        401: {"description": "需要登录认证"},
        404: {"description": "文档不存在"},
        500: {"description": "OCR处理失败"}
    }
)

# 缓存管理相关路由
api_router.include_router(
    cache.router, 
    prefix="/cache", 
    tags=["🗄️ 缓存管理"],
    responses={
        401: {"description": "需要登录认证"},
        404: {"description": "缓存项不存在"}
    }
)

# AI向量化和智能分析相关路由
api_router.include_router(
    vector.router, 
    prefix="/vector", 
    tags=["🤖 AI向量化"],
    responses={
        401: {"description": "需要登录认证"},
        404: {"description": "文档不存在"},
        500: {"description": "AI处理失败"}
    }
)