"""OAuth2相关的Pydantic模式

定义OAuth2客户端、授权码等的数据验证和序列化模式
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


# OAuth2客户端模式
class OAuth2ClientBase(BaseModel):
    """OAuth2客户端基础模式"""
    client_name: str = Field(..., min_length=1, max_length=255, description="客户端名称")
    client_description: Optional[str] = Field(None, description="客户端描述")
    grant_types: List[str] = Field(default=["authorization_code", "refresh_token"], description="支持的授权类型")
    response_types: List[str] = Field(default=["code"], description="支持的响应类型")
    redirect_uris: List[str] = Field(default=[], description="重定向URI列表")
    scopes: List[str] = Field(default=["read"], description="客户端权限范围")
    is_confidential: bool = Field(default=True, description="是否为机密客户端")
    
    @validator('grant_types')
    def validate_grant_types(cls, v):
        """验证授权类型"""
        allowed_types = [
            "authorization_code", 
            "client_credentials", 
            "refresh_token", 
            "password",
            "implicit"
        ]
        for grant_type in v:
            if grant_type not in allowed_types:
                raise ValueError(f"不支持的授权类型: {grant_type}")
        return v
    
    @validator('response_types')
    def validate_response_types(cls, v):
        """验证响应类型"""
        allowed_types = ["code", "token"]
        for response_type in v:
            if response_type not in allowed_types:
                raise ValueError(f"不支持的响应类型: {response_type}")
        return v
    
    @validator('redirect_uris')
    def validate_redirect_uris(cls, v):
        """验证重定向URI"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for uri in v:
            if not url_pattern.match(uri):
                raise ValueError(f"无效的重定向URI: {uri}")
        return v


class OAuth2ClientCreate(OAuth2ClientBase):
    """创建OAuth2客户端的模式"""
    pass


class OAuth2ClientUpdate(BaseModel):
    """更新OAuth2客户端的模式"""
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    client_description: Optional[str] = None
    grant_types: Optional[List[str]] = None
    response_types: Optional[List[str]] = None
    redirect_uris: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    is_confidential: Optional[bool] = None
    is_active: Optional[bool] = None


class OAuth2ClientInDB(OAuth2ClientBase):
    """数据库中的OAuth2客户端模式"""
    id: int
    client_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OAuth2ClientResponse(BaseModel):
    """OAuth2客户端响应模式"""
    id: int
    client_id: str
    client_name: str
    client_description: Optional[str]
    grant_types: List[str]
    response_types: List[str]
    redirect_uris: List[str]
    scopes: List[str]
    is_confidential: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OAuth2ClientWithSecret(OAuth2ClientResponse):
    """包含密钥的OAuth2客户端响应模式（仅在创建时返回）"""
    client_secret: str


# OAuth2授权相关模式
class OAuth2AuthorizeRequest(BaseModel):
    """OAuth2授权请求模式"""
    response_type: str = Field(..., description="响应类型")
    client_id: str = Field(..., description="客户端ID")
    redirect_uri: str = Field(..., description="重定向URI")
    scope: Optional[str] = Field(None, description="权限范围")
    state: Optional[str] = Field(None, description="状态参数")
    
    @validator('response_type')
    def validate_response_type(cls, v):
        if v not in ["code", "token"]:
            raise ValueError("不支持的响应类型")
        return v


class OAuth2AuthorizeResponse(BaseModel):
    """OAuth2授权响应模式"""
    code: Optional[str] = Field(None, description="授权码")
    access_token: Optional[str] = Field(None, description="访问令牌")
    token_type: Optional[str] = Field(None, description="令牌类型")
    expires_in: Optional[int] = Field(None, description="过期时间")
    scope: Optional[str] = Field(None, description="权限范围")
    state: Optional[str] = Field(None, description="状态参数")


class OAuth2TokenRequest(BaseModel):
    """OAuth2令牌请求模式"""
    grant_type: str = Field(..., description="授权类型")
    code: Optional[str] = Field(None, description="授权码")
    redirect_uri: Optional[str] = Field(None, description="重定向URI")
    client_id: Optional[str] = Field(None, description="客户端ID")
    client_secret: Optional[str] = Field(None, description="客户端密钥")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    scope: Optional[str] = Field(None, description="权限范围")
    
    @validator('grant_type')
    def validate_grant_type(cls, v):
        allowed_types = [
            "authorization_code", 
            "client_credentials", 
            "refresh_token", 
            "password"
        ]
        if v not in allowed_types:
            raise ValueError(f"不支持的授权类型: {v}")
        return v


class OAuth2TokenResponse(BaseModel):
    """OAuth2令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    scope: Optional[str] = Field(None, description="权限范围")


class OAuth2ErrorResponse(BaseModel):
    """OAuth2错误响应模式"""
    error: str = Field(..., description="错误代码")
    error_description: Optional[str] = Field(None, description="错误描述")
    error_uri: Optional[str] = Field(None, description="错误信息URI")
    state: Optional[str] = Field(None, description="状态参数")


# 授权码相关模式
class OAuth2AuthorizationCodeInDB(BaseModel):
    """数据库中的授权码模式"""
    id: int
    code: str
    client_id: str
    user_id: int
    redirect_uri: str
    scopes: List[str]
    is_used: bool
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# OAuth2权限范围模式
class OAuth2Scope(BaseModel):
    """OAuth2权限范围模式"""
    name: str = Field(..., description="权限范围名称")
    description: str = Field(..., description="权限范围描述")


class OAuth2ScopeList(BaseModel):
    """OAuth2权限范围列表模式"""
    scopes: List[OAuth2Scope] = Field(..., description="权限范围列表")