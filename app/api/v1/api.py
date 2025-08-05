from fastapi import APIRouter

from app.api.v1 import (
    cache,
    cache_optimization,
    database_optimization,
    health,
    ocr,
    performance,
    system_maintenance,
)
from app.api.v1.endpoints import (
    auth,
    cache_management,
    documents,
    oauth2,
    projects,
    security_monitor,
    token_blacklist,
    users,
    vector,
)

api_router = APIRouter()


# 健康检查相关路由（无需认证）

api_router.include_router(
    health.router, tags=["🏥 健康检查"], responses={503: {"description": "服务不可用"}}
)


# 认证相关路由（无需认证）

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["🔐 用户认证"],
    responses={
        401: {"description": "认证失败"},
        400: {"description": "请求参数错误"},
    },
)


# OAuth2授权服务器相关路由

api_router.include_router(
    oauth2.router,
    prefix="/oauth2",
    tags=["🔑 OAuth2授权"],
    responses={
        400: {"description": "请求参数错误"},
        401: {"description": "客户端认证失败"},
        403: {"description": "权限不足"},
        404: {"description": "客户端不存在"},
    },
)


# 用户管理相关路由

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["👥 用户管理"],
    responses={
        400: {"description": "请求参数错误"},
        409: {"description": "用户已存在"},
    },
)


# Token黑名单管理相关路由

api_router.include_router(
    token_blacklist.router,
    prefix="/token-blacklist",
    tags=["🚫 Token黑名单"],
    responses={
        400: {"description": "请求参数错误"},
        404: {"description": "Token不存在"},
        403: {"description": "权限不足"},
    },
)


# 项目管理相关路由

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["📋 项目管理"],
    responses={
        404: {"description": "项目不存在"},
    },
)


# 文档管理相关路由

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["📄 文档管理"],
    responses={
        404: {"description": "文档不存在"},
        413: {"description": "文件过大"},
        415: {"description": "不支持的文件类型"},
    },
)


# OCR文字识别相关路由

api_router.include_router(
    ocr.router,
    prefix="/ocr",
    tags=["🔍 OCR文字识别"],
    responses={
        404: {"description": "文档不存在"},
        500: {"description": "OCR处理失败"},
    },
)


# 缓存管理相关路由

api_router.include_router(
    cache.router,
    prefix="/cache",
    tags=["🗄️ 缓存管理"],
    responses={
        404: {"description": "缓存项不存在"},
    },
)

# 缓存监控和管理相关路由

api_router.include_router(
    cache_management.router,
    prefix="/cache-management",
    tags=["📊 缓存监控"],
    responses={
        403: {"description": "权限不足"},
        500: {"description": "缓存操作失败"},
    },
)


# AI向量化和智能分析相关路由

api_router.include_router(
    vector.router,
    prefix="/vector",
    tags=["🤖 AI向量化"],
    responses={
        404: {"description": "文档不存在"},
        500: {"description": "AI处理失败"},
    },
)


# 性能监控相关路由

api_router.include_router(
    performance.router,
    prefix="/performance",
    tags=["📊 性能监控"],
    responses={
        500: {"description": "监控数据获取失败"},
        403: {"description": "权限不足"},
    },
)


# 缓存优化相关路由

api_router.include_router(
    cache_optimization.router,
    prefix="/cache-optimization",
    tags=["⚡ 缓存优化"],
    responses={
        404: {"description": "缓存策略不存在"},
        500: {"description": "优化任务执行失败"},
        403: {"description": "权限不足"},
    },
)


# 数据库优化相关路由

api_router.include_router(
    database_optimization.router,
    prefix="/database-optimization",
    tags=["🗃️ 数据库优化"],
    responses={
        404: {"description": "优化策略不存在"},
        500: {"description": "数据库优化失败"},
        403: {"description": "权限不足"},
    },
)





# 系统维护相关路由

api_router.include_router(
    system_maintenance.router,
    prefix="/system-maintenance",
    tags=["🔧 系统维护"],
    responses={
        400: {"description": "请求参数错误"},
        500: {"description": "系统维护操作失败"},
        403: {"description": "权限不足"},
    },
)


# 安全监控相关路由

api_router.include_router(
    security_monitor.router,
    prefix="/security-monitor",
    tags=["🔒 安全监控"],
    responses={
        400: {"description": "请求参数错误"},
        500: {"description": "安全监控操作失败"},
        403: {"description": "权限不足"},
    },
)
