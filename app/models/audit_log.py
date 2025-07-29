"""审计日志模型

记录系统中所有重要操作的审计日志
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)  # 冗余字段，便于查询
    
    # 操作信息
    action = Column(String(100), nullable=False, index=True)  # 操作类型：login, logout, create, update, delete等
    resource_type = Column(String(100), nullable=True, index=True)  # 资源类型：user, report, system等
    resource_id = Column(String(100), nullable=True, index=True)  # 资源ID
    
    # 操作详情
    description = Column(String(500), nullable=True)  # 操作描述
    details = Column(Text, nullable=True)  # 详细信息（JSON格式）
    
    # 请求信息
    ip_address = Column(String(45), nullable=True, index=True)  # 支持IPv6
    user_agent = Column(Text, nullable=True)  # 用户代理
    request_method = Column(String(10), nullable=True)  # HTTP方法
    request_url = Column(String(500), nullable=True)  # 请求URL
    
    # 结果信息
    status = Column(String(20), nullable=False, default="success", index=True)  # success, failed, error
    status_code = Column(Integer, nullable=True)  # HTTP状态码
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)  # 操作耗时（毫秒）
    
    # 额外信息
    session_id = Column(String(100), nullable=True, index=True)  # 会话ID
    trace_id = Column(String(100), nullable=True, index=True)  # 追踪ID
    
    # 关联关系
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', created_at='{self.created_at}')>"
    
    @property
    def is_security_relevant(self) -> bool:
        """判断是否为安全相关的操作"""
        security_actions = {
            "login", "logout", "login_failed", "password_change", 
            "permission_change", "role_change", "account_locked", 
            "account_unlocked", "password_reset", "two_factor_enabled",
            "two_factor_disabled", "api_key_created", "api_key_deleted"
        }
        return self.action in security_actions
    
    @property
    def is_failed_operation(self) -> bool:
        """判断是否为失败的操作"""
        return self.status in ["failed", "error"]
    
    @property
    def risk_score(self) -> int:
        """计算风险评分（0-100）"""
        score = 0
        
        # 基于操作类型
        if self.action in ["login_failed", "permission_change", "role_change"]:
            score += 30
        elif self.action in ["password_change", "account_locked"]:
            score += 20
        elif self.action in ["login", "logout"]:
            score += 5
        
        # 基于状态
        if self.status == "failed":
            score += 20
        elif self.status == "error":
            score += 15
        
        # 基于时间（深夜操作风险更高）
        if self.created_at:
            hour = self.created_at.hour
            if hour < 6 or hour > 22:  # 深夜时间
                score += 10
        
        return min(100, score)