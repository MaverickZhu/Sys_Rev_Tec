"""OAuth2授权服务器核心逻辑

实现OAuth2授权码流程、客户端凭证流程等核心功能
"""

from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, create_refresh_token
from app.core.config import settings
from app.crud.crud_oauth2_client import oauth2_authorization_code, oauth2_client
from app.crud.crud_user import user as crud_user
from app.models.oauth2_client import OAuth2Client
from app.models.user import User
from app.schemas.oauth2 import (
    OAuth2AuthorizeRequest,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
)


class OAuth2Server:
    """OAuth2授权服务器"""

    # 支持的授权类型
    SUPPORTED_GRANT_TYPES = [
        "authorization_code",
        "client_credentials",
        "refresh_token",
        "password",
    ]

    # 支持的响应类型
    SUPPORTED_RESPONSE_TYPES = ["code", "token"]

    # 默认权限范围
    DEFAULT_SCOPES = {"read": "读取权限", "write": "写入权限", "admin": "管理员权限"}

    def __init__(self):
        self.authorization_code_expires_in = 600  # 10分钟
        self.access_token_expires_in = (
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )  # 转换为秒
        self.refresh_token_expires_in = (
            settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )  # 转换为秒

    def authorize(
        self, db: Session, request: OAuth2AuthorizeRequest, current_user: User
    ) -> Tuple[str, Optional[str]]:
        """处理授权请求

        Args:
            db: 数据库会话
            request: 授权请求
            current_user: 当前用户

        Returns:
            Tuple[str, Optional[str]]: (重定向URL, 错误信息)
        """
        try:
            # 验证客户端
            client = oauth2_client.get_by_client_id(db, client_id=request.client_id)
            if not client or not client.is_active:
                return self._build_error_redirect(
                    request.redirect_uri,
                    "invalid_client",
                    "无效的客户端",
                    request.state,
                )

            # 验证重定向URI
            if not client.check_redirect_uri(request.redirect_uri):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="无效的重定向URI"
                )

            # 验证响应类型
            if not client.check_response_type(request.response_type):
                return self._build_error_redirect(
                    request.redirect_uri,
                    "unsupported_response_type",
                    "不支持的响应类型",
                    request.state,
                )

            # 验证权限范围
            scopes = self._parse_scopes(request.scope)
            if not self._validate_scopes(client, scopes):
                return self._build_error_redirect(
                    request.redirect_uri,
                    "invalid_scope",
                    "无效的权限范围",
                    request.state,
                )

            # 处理不同的响应类型
            if request.response_type == "code":
                return self._handle_authorization_code_flow(
                    db, client, current_user, request, scopes
                )
            elif request.response_type == "token":
                return self._handle_implicit_flow(
                    db, client, current_user, request, scopes
                )

        except Exception as e:
            return self._build_error_redirect(
                request.redirect_uri, "server_error", str(e), request.state
            )

    def token(self, db: Session, request: OAuth2TokenRequest) -> OAuth2TokenResponse:
        """处理令牌请求

        Args:
            db: 数据库会话
            request: 令牌请求

        Returns:
            OAuth2TokenResponse: 令牌响应
        """
        if request.grant_type == "authorization_code":
            return self._handle_authorization_code_grant(db, request)
        elif request.grant_type == "client_credentials":
            return self._handle_client_credentials_grant(db, request)
        elif request.grant_type == "refresh_token":
            return self._handle_refresh_token_grant(db, request)
        elif request.grant_type == "password":
            return self._handle_password_grant(db, request)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的授权类型"
            )

    def _handle_authorization_code_flow(
        self,
        db: Session,
        client: OAuth2Client,
        user: User,
        request: OAuth2AuthorizeRequest,
        scopes: List[str],
    ) -> Tuple[str, None]:
        """处理授权码流程"""
        # 创建授权码
        auth_code = oauth2_authorization_code.create_authorization_code(
            db,
            client_id=client.client_id,
            user_id=user.id,
            redirect_uri=request.redirect_uri,
            scopes=scopes,
            expires_in=self.authorization_code_expires_in,
        )

        # 构建重定向URL
        params = {"code": auth_code.code}
        if request.state:
            params["state"] = request.state

        redirect_url = f"{request.redirect_uri}?{urlencode(params)}"
        return redirect_url, None

    def _handle_implicit_flow(
        self,
        db: Session,
        client: OAuth2Client,
        user: User,
        request: OAuth2AuthorizeRequest,
        scopes: List[str],
    ) -> Tuple[str, None]:
        """处理隐式流程"""
        # 创建访问令牌
        access_token_data = {
            "sub": str(user.id),
            "client_id": client.client_id,
            "scopes": scopes,
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(seconds=self.access_token_expires_in),
        )

        # 构建重定向URL（使用fragment）
        params = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": str(self.access_token_expires_in),
        }
        if request.scope:
            params["scope"] = request.scope
        if request.state:
            params["state"] = request.state

        redirect_url = f"{request.redirect_uri}#{urlencode(params)}"
        return redirect_url, None

    def _handle_authorization_code_grant(
        self, db: Session, request: OAuth2TokenRequest
    ) -> OAuth2TokenResponse:
        """处理授权码授权"""
        # 验证必需参数
        if not all([request.code, request.redirect_uri, request.client_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少必需参数"
            )

        # 验证客户端
        client = None
        if request.client_secret:
            client = oauth2_client.authenticate_client(
                db, client_id=request.client_id, client_secret=request.client_secret
            )
        else:
            client = oauth2_client.get_by_client_id(db, client_id=request.client_id)
            if client and client.is_confidential:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="机密客户端需要提供密钥",
                )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="客户端认证失败"
            )

        # 使用授权码
        auth_code = oauth2_authorization_code.use_authorization_code(
            db,
            code=request.code,
            client_id=request.client_id,
            redirect_uri=request.redirect_uri,
        )

        if not auth_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的授权码"
            )

        # 获取用户信息
        user = crud_user.get(db, id=auth_code.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在"
            )

        # 创建令牌
        return self._create_tokens(user, client, auth_code.scopes)

    def _handle_client_credentials_grant(
        self, db: Session, request: OAuth2TokenRequest
    ) -> OAuth2TokenResponse:
        """处理客户端凭证授权"""
        # 验证客户端
        if not all([request.client_id, request.client_secret]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少客户端凭证"
            )

        client = oauth2_client.authenticate_client(
            db, client_id=request.client_id, client_secret=request.client_secret
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="客户端认证失败"
            )

        # 验证授权类型
        if not client.check_grant_type("client_credentials"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="客户端不支持此授权类型"
            )

        # 解析权限范围
        scopes = self._parse_scopes(request.scope)
        if not self._validate_scopes(client, scopes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的权限范围"
            )

        # 创建访问令牌（客户端凭证流程不需要刷新令牌）
        access_token_data = {
            "sub": f"client:{client.client_id}",
            "client_id": client.client_id,
            "scopes": scopes,
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(seconds=self.access_token_expires_in),
        )

        return OAuth2TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expires_in,
            scope=" ".join(scopes) if scopes else None,
        )

    def _handle_refresh_token_grant(
        self, db: Session, request: OAuth2TokenRequest
    ) -> OAuth2TokenResponse:
        """处理刷新令牌授权"""
        # 验证刷新令牌
        if not request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少刷新令牌"
            )

        # 这里需要实现刷新令牌的验证逻辑
        # 暂时抛出未实现异常
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="刷新令牌功能尚未实现"
        )

    def _handle_password_grant(
        self, db: Session, request: OAuth2TokenRequest
    ) -> OAuth2TokenResponse:
        """处理密码授权"""
        # 验证必需参数
        if not all([request.username, request.password, request.client_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少必需参数"
            )

        # 验证客户端
        client = oauth2_client.get_by_client_id(db, client_id=request.client_id)
        if not client or not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的客户端"
            )

        # 验证授权类型
        if not client.check_grant_type("password"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="客户端不支持此授权类型"
            )

        # 验证用户凭证
        user = crud_user.authenticate(
            db, email=request.username, password=request.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户认证失败"
            )

        # 解析权限范围
        scopes = self._parse_scopes(request.scope)
        if not self._validate_scopes(client, scopes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的权限范围"
            )

        # 创建令牌
        return self._create_tokens(user, client, scopes)

    def _create_tokens(
        self, user: User, client: OAuth2Client, scopes: List[str]
    ) -> OAuth2TokenResponse:
        """创建访问令牌和刷新令牌"""
        # 创建访问令牌
        access_token_data = {
            "sub": str(user.id),
            "client_id": client.client_id,
            "scopes": scopes,
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(seconds=self.access_token_expires_in),
        )

        # 创建刷新令牌
        refresh_token_data = {
            "sub": str(user.id),
            "client_id": client.client_id,
            "type": "refresh",
        }
        refresh_token = create_refresh_token(
            data=refresh_token_data,
            expires_delta=timedelta(seconds=self.refresh_token_expires_in),
        )

        return OAuth2TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expires_in,
            refresh_token=refresh_token,
            scope=" ".join(scopes) if scopes else None,
        )

    def _parse_scopes(self, scope_string: Optional[str]) -> List[str]:
        """解析权限范围字符串"""
        if not scope_string:
            return []
        return scope_string.split()

    def _validate_scopes(self, client: OAuth2Client, scopes: List[str]) -> bool:
        """验证权限范围"""
        if not scopes:
            return True

        for scope in scopes:
            if not client.check_scope(scope):
                return False
        return True

    def _build_error_redirect(
        self,
        redirect_uri: str,
        error: str,
        error_description: str,
        state: Optional[str] = None,
    ) -> Tuple[str, str]:
        """构建错误重定向URL"""
        params = {"error": error, "error_description": error_description}
        if state:
            params["state"] = state

        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        return redirect_url, error_description

    def get_supported_scopes(self) -> Dict[str, str]:
        """获取支持的权限范围"""
        return self.DEFAULT_SCOPES.copy()


# 创建OAuth2服务器实例
oauth2_server = OAuth2Server()
