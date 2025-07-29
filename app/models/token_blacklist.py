from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base_class import Base


class TokenBlacklist(Base):
    """Token黑名单模型"""

    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    
    # Token信息
    jti = Column(String(255), unique=True, index=True, nullable=False, comment="JWT ID")
    token_hash = Column(String(255), index=True, nullable=False, comment="Token哈希值")
    user_id = Column(Integer, index=True, comment="用户ID")
    
    # Token详情
    token_type = Column(String(50), default="access", comment="Token类型: access, refresh")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="Token过期时间")
    reason = Column(String(100), comment="加入黑名单原因")
    
    # 元数据
    user_agent = Column(Text, comment="用户代理")
    ip_address = Column(String(45), comment="IP地址")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入黑名单时间")