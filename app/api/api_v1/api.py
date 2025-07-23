from fastapi import APIRouter

from app.api.api_v1.endpoints import login, users, projects, documents, ocr
from app.core.config import settings

api_router = APIRouter()

# 认证相关路由
api_router.include_router(login.router, tags=["login"])

# 用户管理路由
api_router.include_router(
    users.router, prefix="/users", tags=["users"]
)

# 项目管理路由
api_router.include_router(
    projects.router, prefix="/projects", tags=["projects"]
)

# 文档管理路由
api_router.include_router(
    documents.router, prefix="/documents", tags=["documents"]
)

# OCR处理路由
api_router.include_router(
    ocr.router, prefix="/ocr", tags=["ocr"]
)