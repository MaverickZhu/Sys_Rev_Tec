"""认证中间件

处理JWT令牌验证、用户认证和权限检查
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.auth import auth_manager
from app.crud.crud_token_blacklist import token_blacklist
from app.crud.crud_user import user as user_crud
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件

    自动处理JWT令牌验证，并将用户信息注入到请求上下文中
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # 不需要认证的路径
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/login/json",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/metrics",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求"""
        # 检查是否为排除路径
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # 提取并验证令牌
        user = await self._authenticate_request(request)

        # 将用户信息注入到请求状态中
        request.state.user = user

        # 继续处理请求
        response = await call_next(request)
        return response

    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中"""
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """认证请求"""
        try:
            # 从请求头中提取Authorization
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None

            # 解析认证方案和令牌
            scheme, token = get_authorization_scheme_param(authorization)
            if not token or scheme.lower() != "bearer":
                return None

            # 验证令牌
            payload = auth_manager.verify_token(token, "access")
            user_id = payload.get("sub")
            jti = payload.get("jti")

            if not user_id:
                return None

            # 检查token是否在黑名单中
            db = SessionLocal()
            try:
                if jti and token_blacklist.is_token_blacklisted(db, jti=jti):
                    logger.warning(f"Token {jti} is blacklisted")
                    return None
            finally:
                db.close()

            # 查询用户
            db = SessionLocal()
            try:
                user = user_crud.get(db, id=int(user_id))
                if user and user_crud.is_active(user):
                    return user
            finally:
                db.close()

            return None

        except Exception as e:
            logger.warning(f"认证失败: {e}")
            return None


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """强制认证中间件

    要求所有请求都必须通过认证（除了排除路径）
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # 不需要认证的路径
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/login/json",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/metrics",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求"""
        # 检查是否为排除路径
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # 提取并验证令牌
        user = await self._authenticate_request(request)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败，请先登录",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将用户信息注入到请求状态中
        request.state.user = user

        # 继续处理请求
        response = await call_next(request)
        return response

    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中"""
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """认证请求"""
        try:
            # 从请求头中提取Authorization
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None

            # 解析认证方案和令牌
            scheme, token = get_authorization_scheme_param(authorization)
            if not token or scheme.lower() != "bearer":
                return None

            # 验证令牌
            payload = auth_manager.verify_token(token, "access")
            user_id = payload.get("sub")
            jti = payload.get("jti")

            if not user_id:
                return None

            # 查询用户
            db = SessionLocal()
            try:
                # 检查token是否在黑名单中
                if jti and token_blacklist.is_token_blacklisted(db, jti=jti):
                    logger.warning(f"Token {jti} is blacklisted")
                    return None

                user = user_crud.get(db, id=int(user_id))
                if user and user_crud.is_active(user):
                    return user
            finally:
                db.close()

            return None

        except Exception as e:
            logger.warning(f"认证失败: {e}")
            return None


def get_current_user_from_request(request: Request) -> Optional[User]:
    """从请求中获取当前用户

    Args:
        request: FastAPI请求对象

    Returns:
        Optional[User]: 当前用户对象或None
    """
    return getattr(request.state, "user", None)
