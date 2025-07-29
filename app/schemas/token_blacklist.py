from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenBlacklistBase(BaseModel):
    """Token黑名单基础模式"""
    jti: str = Field(..., description="JWT ID")
    token_hash: str = Field(..., description="Token哈希值")
    user_id: Optional[int] = Field(None, description="用户ID")
    token_type: str = Field("access", description="Token类型")
    expires_at: datetime = Field(..., description="Token过期时间")
    reason: Optional[str] = Field(None, description="加入黑名单原因")
    user_agent: Optional[str] = Field(None, description="用户代理")
    ip_address: Optional[str] = Field(None, description="IP地址")


class TokenBlacklistCreate(TokenBlacklistBase):
    """创建Token黑名单"""
    pass


class TokenBlacklistUpdate(BaseModel):
    """更新Token黑名单"""
    reason: Optional[str] = Field(None, description="更新原因")


class TokenBlacklistInDBBase(TokenBlacklistBase):
    """数据库中的Token黑名单基础模式"""
    id: int
    created_at: datetime
    blacklisted_at: datetime

    class Config:
        from_attributes = True


class TokenBlacklist(TokenBlacklistInDBBase):
    """Token黑名单响应模式"""
    pass


class TokenBlacklistInDB(TokenBlacklistInDBBase):
    """数据库中的Token黑名单完整模式"""
    pass


class TokenBlacklistQuery(BaseModel):
    """Token黑名单查询参数"""
    user_id: Optional[int] = Field(None, description="用户ID")
    token_type: Optional[str] = Field(None, description="Token类型")
    reason: Optional[str] = Field(None, description="原因")
    ip_address: Optional[str] = Field(None, description="IP地址")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    skip: int = Field(0, ge=0, description="跳过记录数")
    limit: int = Field(100, ge=1, le=1000, description="限制记录数")


class TokenValidationRequest(BaseModel):
    """Token验证请求"""
    token: str = Field(..., description="要验证的Token")


class TokenValidationResponse(BaseModel):
    """Token验证响应"""
    is_blacklisted: bool = Field(..., description="是否在黑名单中")
    reason: Optional[str] = Field(None, description="黑名单原因")
    blacklisted_at: Optional[datetime] = Field(None, description="加入黑名单时间")


class TokenBlacklistStats(BaseModel):
    """Token黑名单统计"""
    total_blacklisted: int = Field(..., description="总黑名单数量")
    access_tokens: int = Field(..., description="访问令牌数量")
    refresh_tokens: int = Field(..., description="刷新令牌数量")
    today_blacklisted: int = Field(..., description="今日新增数量")
    expired_tokens: int = Field(..., description="已过期令牌数量")