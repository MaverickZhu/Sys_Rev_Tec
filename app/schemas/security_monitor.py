"""安全监控相关的Pydantic模式

定义安全监控、审计日志、威胁检测等功能的数据模式
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ThreatLevel(str, Enum):
    """威胁级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventStatus(str, Enum):
    """安全事件状态"""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AuditLogSearch(BaseModel):
    """审计日志搜索参数"""

    user_id: Optional[int] = None
    username: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "action": "login",
                "status": "failed",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-31T23:59:59Z",
                "limit": 50,
            }
        }
    }


class SecurityEventSearch(BaseModel):
    """安全事件搜索参数"""

    event_type: Optional[str] = None
    level: Optional[str] = None
    source_ip: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    is_resolved: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_type": "login_failed",
                "level": "high",
                "is_resolved": False,
                "limit": 50,
            }
        }
    }


class SecurityMetrics(BaseModel):
    """安全指标"""

    total_audit_logs: int = Field(..., description="审计日志总数")
    failed_logins: int = Field(..., description="失败登录次数")
    security_events: int = Field(..., description="安全事件总数")
    critical_events: int = Field(..., description="严重安全事件数")
    active_users: int = Field(..., description="活跃用户数")
    unique_ips: int = Field(..., description="唯一IP数")
    threat_level: str = Field(..., description="当前威胁级别")
    system_health_score: int = Field(..., ge=0, le=100, description="系统健康评分")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_audit_logs": 1250,
                "failed_logins": 23,
                "security_events": 5,
                "critical_events": 1,
                "active_users": 45,
                "unique_ips": 67,
                "threat_level": "medium",
                "system_health_score": 85,
            }
        }
    }


class SecurityAlert(BaseModel):
    """安全警报"""

    id: int
    event_type: str = Field(..., description="事件类型")
    level: str = Field(..., description="严重级别")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    source_ip: Optional[str] = Field(None, description="源IP地址")
    user_id: Optional[int] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    is_resolved: bool = Field(..., description="是否已解决")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "event_type": "brute_force",
                "level": "high",
                "title": "检测到暴力破解攻击",
                "description": "来自IP 192.168.1.100的多次失败登录尝试",
                "source_ip": "192.168.1.100",
                "user_id": None,
                "created_at": "2024-01-15T10:30:00Z",
                "is_resolved": False,
            }
        }
    }


class SecurityTrend(BaseModel):
    """安全趋势"""

    trend_date: date = Field(..., description="日期")
    security_events: int = Field(..., description="安全事件数")
    failed_logins: int = Field(..., description="失败登录数")
    threat_score: int = Field(..., ge=0, le=100, description="威胁评分")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trend_date": "2024-01-15",
                "security_events": 3,
                "failed_logins": 12,
                "threat_score": 45,
            }
        }
    }


class UserActivitySummary(BaseModel):
    """用户活动摘要"""

    user_id: int
    username: str
    total_actions: int = Field(..., description="总操作数")
    unique_ips: int = Field(..., description="唯一IP数")
    last_activity: datetime = Field(..., description="最后活动时间")
    risk_score: int = Field(..., ge=0, le=100, description="风险评分")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "username": "admin",
                "total_actions": 156,
                "unique_ips": 3,
                "last_activity": "2024-01-15T14:30:00Z",
                "risk_score": 25,
            }
        }
    }


class SystemHealthStatus(BaseModel):
    """系统健康状态"""

    cpu_usage: float = Field(..., ge=0, le=100, description="CPU使用率")
    memory_usage: float = Field(..., ge=0, le=100, description="内存使用率")
    disk_usage: float = Field(..., ge=0, le=100, description="磁盘使用率")
    network_status: str = Field(..., description="网络状态")
    database_status: str = Field(..., description="数据库状态")
    service_status: str = Field(..., description="服务状态")
    last_backup: Optional[datetime] = Field(None, description="最后备份时间")
    uptime_hours: int = Field(..., ge=0, description="运行时间（小时）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "cpu_usage": 45.2,
                "memory_usage": 67.8,
                "disk_usage": 34.5,
                "network_status": "healthy",
                "database_status": "healthy",
                "service_status": "healthy",
                "last_backup": "2024-01-15T02:00:00Z",
                "uptime_hours": 168,
            }
        }
    }


class ThreatDetectionResult(BaseModel):
    """威胁检测结果"""

    scan_status: str = Field(..., description="扫描状态")
    threats_detected: int = Field(..., description="检测到的威胁数")
    high_risk_threats: int = Field(..., description="高风险威胁数")
    medium_risk_threats: int = Field(..., description="中风险威胁数")
    low_risk_threats: int = Field(..., description="低风险威胁数")
    last_scan: Optional[datetime] = Field(None, description="最后扫描时间")
    next_scan: Optional[datetime] = Field(None, description="下次扫描时间")

    model_config = {
        "json_schema_extra": {
            "example": {
                "scan_status": "completed",
                "threats_detected": 3,
                "high_risk_threats": 1,
                "medium_risk_threats": 2,
                "low_risk_threats": 0,
                "last_scan": "2024-01-15T12:00:00Z",
                "next_scan": "2024-01-16T12:00:00Z",
            }
        }
    }


class SecurityRecommendation(BaseModel):
    """安全建议"""

    id: int
    recommendation_type: str = Field(..., description="建议类型")
    priority: str = Field(..., description="优先级")
    title: str = Field(..., description="标题")
    description: str = Field(..., description="描述")
    action_required: bool = Field(..., description="是否需要采取行动")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "recommendation_type": "password_policy",
                "priority": "high",
                "title": "加强密码策略",
                "description": "建议启用更严格的密码复杂度要求",
                "action_required": True,
            }
        }
    }


class SecurityDashboardData(BaseModel):
    """安全监控仪表板数据"""

    metrics: SecurityMetrics = Field(..., description="安全指标")
    alerts: List[SecurityAlert] = Field(..., description="安全警报")
    trends: List[SecurityTrend] = Field(..., description="安全趋势")
    user_activities: List[UserActivitySummary] = Field(..., description="用户活动摘要")
    system_health: SystemHealthStatus = Field(..., description="系统健康状态")
    threat_detection: ThreatDetectionResult = Field(..., description="威胁检测结果")
    recommendations: List[SecurityRecommendation] = Field(..., description="安全建议")
    last_updated: datetime = Field(..., description="最后更新时间")

    model_config = {
        "json_schema_extra": {"example": {"last_updated": "2024-01-15T15:00:00Z"}}
    }


class AuditLogCreate(BaseModel):
    """创建审计日志"""

    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str = Field(..., description="操作类型")
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    status: str = Field("success", description="操作状态")
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "username": "admin",
                "action": "login",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "status": "success",
            }
        }
    }


class SecurityEventCreate(BaseModel):
    """创建安全事件"""

    event_type: str = Field(..., description="事件类型")
    level: str = Field(..., description="严重级别")
    title: str = Field(..., description="标题")
    description: Optional[str] = None
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    target_ip: Optional[str] = None
    target_port: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    detection_method: Optional[str] = None
    detection_rule: Optional[str] = None
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    details: Optional[Dict[str, Any]] = None
    evidence: Optional[str] = None
    impact_assessment: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_type": "login_failed",
                "level": "medium",
                "title": "多次登录失败",
                "description": "用户在短时间内多次登录失败",
                "source_ip": "192.168.1.100",
                "user_id": 1,
                "confidence_score": 85,
            }
        }
    }


class SecurityEventUpdate(BaseModel):
    """更新安全事件"""

    level: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    impact_assessment: Optional[str] = None
    is_resolved: Optional[bool] = None
    resolution_note: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_resolved": True,
                "resolution_note": "已确认为误报，已添加白名单",
            }
        }
    }


class SecurityStatistics(BaseModel):
    """安全统计信息"""

    total_events: int = Field(..., description="总事件数")
    events_by_level: Dict[str, int] = Field(..., description="按级别分组的事件数")
    events_by_type: Dict[str, int] = Field(..., description="按类型分组的事件数")
    resolved_events: int = Field(..., description="已解决事件数")
    pending_events: int = Field(..., description="待处理事件数")
    avg_resolution_time: float = Field(..., description="平均解决时间（小时）")
    top_source_ips: List[Dict[str, Union[str, int]]] = Field(..., description="Top源IP")
    top_users: List[Dict[str, Union[str, int]]] = Field(..., description="Top用户")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_events": 150,
                "events_by_level": {"low": 80, "medium": 50, "high": 15, "critical": 5},
                "events_by_type": {
                    "login_failed": 60,
                    "brute_force": 20,
                    "suspicious_login": 30,
                },
                "resolved_events": 120,
                "pending_events": 30,
                "avg_resolution_time": 2.5,
                "top_source_ips": [{"ip": "192.168.1.100", "count": 25}],
                "top_users": [{"username": "admin", "count": 15}],
            }
        }
    }
