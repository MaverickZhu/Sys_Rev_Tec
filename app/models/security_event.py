"""安全事件模型

记录系统中的安全事件和威胁
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SecurityEventType(enum.Enum):
    """安全事件类型"""

    LOGIN_FAILED = "login_failed"  # 登录失败
    BRUTE_FORCE = "brute_force"  # 暴力破解
    SUSPICIOUS_LOGIN = "suspicious_login"  # 可疑登录
    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授权访问
    PRIVILEGE_ESCALATION = "privilege_escalation"  # 权限提升
    DATA_BREACH = "data_breach"  # 数据泄露
    MALWARE_DETECTED = "malware_detected"  # 恶意软件检测
    DDOS_ATTACK = "ddos_attack"  # DDoS攻击
    SQL_INJECTION = "sql_injection"  # SQL注入
    XSS_ATTACK = "xss_attack"  # XSS攻击
    CSRF_ATTACK = "csrf_attack"  # CSRF攻击
    FILE_UPLOAD_THREAT = "file_upload_threat"  # 文件上传威胁
    ACCOUNT_TAKEOVER = "account_takeover"  # 账户接管
    INSIDER_THREAT = "insider_threat"  # 内部威胁
    COMPLIANCE_VIOLATION = "compliance_violation"  # 合规违规
    SYSTEM_ANOMALY = "system_anomaly"  # 系统异常
    NETWORK_INTRUSION = "network_intrusion"  # 网络入侵
    API_ABUSE = "api_abuse"  # API滥用
    CONFIGURATION_CHANGE = "configuration_change"  # 配置变更
    OTHER = "other"  # 其他


class SecurityEventLevel(enum.Enum):
    """安全事件级别"""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


class SecurityEvent(Base):
    """安全事件模型"""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)

    # 事件基本信息
    event_type = Column(Enum(SecurityEventType), nullable=False, index=True)
    level = Column(Enum(SecurityEventLevel), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 来源信息
    source_ip = Column(String(45), nullable=True, index=True)  # 源IP地址
    source_port = Column(Integer, nullable=True)  # 源端口
    target_ip = Column(String(45), nullable=True)  # 目标IP地址
    target_port = Column(Integer, nullable=True)  # 目标端口

    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)  # 冗余字段

    # 请求信息
    user_agent = Column(Text, nullable=True)  # 用户代理
    request_method = Column(String(10), nullable=True)  # HTTP方法
    request_url = Column(String(500), nullable=True)  # 请求URL
    request_headers = Column(Text, nullable=True)  # 请求头（JSON格式）
    request_body = Column(Text, nullable=True)  # 请求体

    # 检测信息
    detection_method = Column(String(100), nullable=True)  # 检测方法
    detection_rule = Column(String(200), nullable=True)  # 检测规则
    confidence_score = Column(Integer, nullable=True)  # 置信度分数（0-100）

    # 详细信息
    details = Column(Text, nullable=True)  # 详细信息（JSON格式）
    evidence = Column(Text, nullable=True)  # 证据信息
    impact_assessment = Column(Text, nullable=True)  # 影响评估

    # 处理状态
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(Text, nullable=True)  # 解决说明

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 额外信息
    session_id = Column(String(100), nullable=True, index=True)  # 会话ID
    trace_id = Column(String(100), nullable=True, index=True)  # 追踪ID
    correlation_id = Column(String(100), nullable=True, index=True)  # 关联ID

    # 关联关系
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="security_events"
    )
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type='{self.event_type.value}', level='{self.level.value}', created_at='{self.created_at}')>"

    @property
    def severity_score(self) -> int:
        """计算严重性分数（0-100）"""
        base_scores = {
            SecurityEventLevel.LOW: 25,
            SecurityEventLevel.MEDIUM: 50,
            SecurityEventLevel.HIGH: 75,
            SecurityEventLevel.CRITICAL: 100,
        }

        score = base_scores.get(self.level, 50)

        # 根据事件类型调整分数
        high_risk_types = {
            SecurityEventType.DATA_BREACH,
            SecurityEventType.ACCOUNT_TAKEOVER,
            SecurityEventType.PRIVILEGE_ESCALATION,
            SecurityEventType.MALWARE_DETECTED,
        }

        if self.event_type in high_risk_types:
            score = min(100, score + 10)

        # 根据置信度调整
        if self.confidence_score:
            confidence_factor = self.confidence_score / 100
            score = int(score * confidence_factor)

        return score

    @property
    def is_critical(self) -> bool:
        """判断是否为严重事件"""
        return self.level == SecurityEventLevel.CRITICAL or self.severity_score >= 90

    @property
    def requires_immediate_attention(self) -> bool:
        """判断是否需要立即处理"""
        if self.is_critical:
            return True

        # 某些类型的事件需要立即处理
        immediate_types = {
            SecurityEventType.DATA_BREACH,
            SecurityEventType.ACCOUNT_TAKEOVER,
            SecurityEventType.DDOS_ATTACK,
            SecurityEventType.MALWARE_DETECTED,
        }

        return self.event_type in immediate_types

    def get_response_time_sla(self) -> int:
        """获取响应时间SLA（分钟）"""
        sla_mapping = {
            SecurityEventLevel.CRITICAL: 15,  # 15分钟
            SecurityEventLevel.HIGH: 60,  # 1小时
            SecurityEventLevel.MEDIUM: 240,  # 4小时
            SecurityEventLevel.LOW: 1440,  # 24小时
        }

        return sla_mapping.get(self.level, 240)

    def is_sla_breached(self) -> bool:
        """判断是否违反SLA"""
        if self.is_resolved:
            return False

        sla_minutes = self.get_response_time_sla()
        elapsed_minutes = (datetime.utcnow() - self.created_at).total_seconds() / 60

        return elapsed_minutes > sla_minutes
