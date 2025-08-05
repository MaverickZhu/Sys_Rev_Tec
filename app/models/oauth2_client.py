"""OAuth2客户端模型

定义OAuth2客户端的数据结构和关系
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base_class import Base


class OAuth2Client(Base):
    """OAuth2客户端模型

    存储OAuth2客户端的基本信息和配置
    """

    __tablename__ = "oauth2_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(
        String(255), unique=True, index=True, nullable=False, comment="客户端ID"
    )
    client_secret = Column(String(255), nullable=False, comment="客户端密钥")
    client_name = Column(String(255), nullable=False, comment="客户端名称")
    client_description = Column(Text, comment="客户端描述")

    # OAuth2配置
    grant_types = Column(
        JSON, default=["authorization_code", "refresh_token"], comment="支持的授权类型"
    )
    response_types = Column(JSON, default=["code"], comment="支持的响应类型")
    redirect_uris = Column(JSON, default=[], comment="重定向URI列表")
    scopes = Column(JSON, default=["read"], comment="客户端权限范围")

    # 客户端状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_confidential = Column(Boolean, default=True, comment="是否为机密客户端")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    def __repr__(self):
        return (
            f"<OAuth2Client(client_id='{self.client_id}', name='{self.client_name}')>"
        )

    def check_grant_type(self, grant_type: str) -> bool:
        """检查是否支持指定的授权类型"""
        return grant_type in (self.grant_types or [])

    def check_response_type(self, response_type: str) -> bool:
        """检查是否支持指定的响应类型"""
        return response_type in (self.response_types or [])

    def check_redirect_uri(self, redirect_uri: str) -> bool:
        """检查重定向URI是否有效"""
        return redirect_uri in (self.redirect_uris or [])

    def check_scope(self, scope: str) -> bool:
        """检查是否有指定权限范围"""
        return scope in (self.scopes or [])


class OAuth2AuthorizationCode(Base):
    """OAuth2授权码模型

    存储授权码的信息和状态
    """

    __tablename__ = "oauth2_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(255), unique=True, index=True, nullable=False, comment="授权码"
    )
    client_id = Column(String(255), nullable=False, comment="客户端ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    redirect_uri = Column(String(500), nullable=False, comment="重定向URI")
    scopes = Column(JSON, default=[], comment="授权范围")

    # 授权码状态
    is_used = Column(Boolean, default=False, comment="是否已使用")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )

    def __repr__(self):
        return f"<OAuth2AuthorizationCode(code='{self.code[:8]}...', client_id='{self.client_id}')>"

    def is_expired(self) -> bool:
        """检查授权码是否已过期"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """检查授权码是否有效"""
        return not self.is_used and not self.is_expired()
