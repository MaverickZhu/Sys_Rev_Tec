"""威胁检测模块

提供实时威胁检测、异常行为分析、攻击模式识别等功能
"""

import ipaddress
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.crud.crud_security_event import security_event as security_event_crud
from app.models.audit_log import AuditLog
from app.models.security_event import (
    SecurityEvent,
    SecurityEventLevel,
    SecurityEventType,
)
from app.models.user import User

logger = logging.getLogger(__name__)


class ThreatDetector:
    """威胁检测器"""

    def __init__(self, db: Session):
        self.db = db
        self.detection_rules = self._load_detection_rules()
        self.ip_whitelist = self._load_ip_whitelist()
        self.user_whitelist = self._load_user_whitelist()

    def _load_detection_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载检测规则"""
        return {
            "brute_force": {
                "threshold": 5,  # 失败次数阈值
                "time_window": 300,  # 时间窗口（秒）
                "level": SecurityEventLevel.HIGH,
            },
            "suspicious_login": {
                "max_ips_per_user": 3,  # 用户最大IP数
                "time_window": 3600,  # 时间窗口（秒）
                "level": SecurityEventLevel.MEDIUM,
            },
            "privilege_escalation": {
                "sensitive_actions": [
                    "role_change",
                    "permission_change",
                    "user_create",
                ],
                "level": SecurityEventLevel.HIGH,
            },
            "night_activity": {
                "start_hour": 22,  # 晚上10点
                "end_hour": 6,  # 早上6点
                "level": SecurityEventLevel.LOW,
            },
            "api_abuse": {
                "request_threshold": 100,  # 请求数阈值
                "time_window": 60,  # 时间窗口（秒）
                "level": SecurityEventLevel.MEDIUM,
            },
            "data_exfiltration": {
                "download_threshold": 1000,  # 下载次数阈值
                "time_window": 3600,  # 时间窗口（秒）
                "level": SecurityEventLevel.HIGH,
            },
        }

    def _load_ip_whitelist(self) -> List[str]:
        """加载IP白名单"""
        # 这里可以从配置文件或数据库加载
        return ["127.0.0.1", "::1", "192.168.1.0/24", "10.0.0.0/8"]  # 内网IP段

    def _load_user_whitelist(self) -> List[str]:
        """加载用户白名单"""
        # 系统用户或服务账户
        return ["system", "service", "monitor"]

    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """检查IP是否在白名单中"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for whitelist_entry in self.ip_whitelist:
                if "/" in whitelist_entry:
                    # CIDR网段
                    network = ipaddress.ip_network(whitelist_entry, strict=False)
                    if ip in network:
                        return True
                else:
                    # 单个IP
                    if str(ip) == whitelist_entry:
                        return True
            return False
        except ValueError:
            return False

    def is_user_whitelisted(self, username: str) -> bool:
        """检查用户是否在白名单中"""
        return username in self.user_whitelist

    async def run_scan(self, scan_type: str = "full") -> List[Dict[str, Any]]:
        """运行威胁检测扫描"""
        logger.info(f"开始威胁检测扫描: {scan_type}")

        threats = []

        if scan_type in ["quick", "full"]:
            # 快速扫描：检测最近的威胁
            threats.extend(await self.detect_brute_force_attacks())
            threats.extend(await self.detect_suspicious_logins())
            threats.extend(await self.detect_failed_operations())

        if scan_type in ["full", "custom"]:
            # 完整扫描：包含更多检测项
            threats.extend(await self.detect_privilege_escalation())
            threats.extend(await self.detect_night_activities())
            threats.extend(await self.detect_api_abuse())
            threats.extend(await self.detect_data_exfiltration())
            threats.extend(await self.detect_account_anomalies())
            threats.extend(await self.detect_injection_attempts())

        # 去重和排序
        unique_threats = self._deduplicate_threats(threats)
        sorted_threats = sorted(
            unique_threats, key=lambda x: x.get("severity", 0), reverse=True
        )

        logger.info(f"威胁检测扫描完成，发现 {len(sorted_threats)} 个威胁")
        return sorted_threats

    async def detect_brute_force_attacks(self, hours: int = 1) -> List[Dict[str, Any]]:
        """检测暴力破解攻击"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 查询失败登录记录
        failed_logins = (
            self.db.query(
                AuditLog.ip_address,
                AuditLog.username,
                func.count(AuditLog.id).label("failed_count"),
                func.max(AuditLog.created_at).label("last_attempt"),
            )
            .filter(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "failed",
                    AuditLog.created_at >= start_time,
                    AuditLog.ip_address.isnot(None),
                )
            )
            .group_by(AuditLog.ip_address, AuditLog.username)
            .all()
        )

        rule = self.detection_rules["brute_force"]

        for login in failed_logins:
            if login.failed_count >= rule["threshold"]:
                # 检查IP是否在白名单中
                if self.is_ip_whitelisted(login.ip_address):
                    continue

                # 检查是否已经存在相同的安全事件
                existing_event = (
                    self.db.query(SecurityEvent)
                    .filter(
                        and_(
                            SecurityEvent.event_type == SecurityEventType.BRUTE_FORCE,
                            SecurityEvent.source_ip == login.ip_address,
                            SecurityEvent.username == login.username,
                            SecurityEvent.created_at >= start_time,
                            SecurityEvent.is_resolved == False,
                        )
                    )
                    .first()
                )

                if not existing_event:
                    # 创建安全事件
                    event = security_event_crud.create_event(
                        self.db,
                        event_type=SecurityEventType.BRUTE_FORCE,
                        level=rule["level"],
                        title=f"检测到暴力破解攻击",
                        description=f"IP {login.ip_address} 对用户 {login.username} 进行了 {login.failed_count} 次失败登录尝试",
                        source_ip=login.ip_address,
                        username=login.username,
                        detection_method="statistical_analysis",
                        detection_rule="brute_force",
                        confidence_score=min(100, login.failed_count * 20),
                        details={
                            "failed_attempts": login.failed_count,
                            "time_window": hours,
                            "last_attempt": login.last_attempt.isoformat(),
                        },
                    )

                    threats.append(
                        {
                            "id": event.id,
                            "type": "brute_force",
                            "severity": event.severity_score,
                            "source_ip": login.ip_address,
                            "username": login.username,
                            "failed_attempts": login.failed_count,
                        }
                    )

        return threats

    async def detect_suspicious_logins(self, hours: int = 24) -> List[Dict[str, Any]]:
        """检测可疑登录"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 查询成功登录记录，按用户分组
        user_logins = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                func.count(func.distinct(AuditLog.ip_address)).label("unique_ips"),
                func.array_agg(func.distinct(AuditLog.ip_address)).label("ip_list"),
            )
            .filter(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "success",
                    AuditLog.created_at >= start_time,
                    AuditLog.user_id.isnot(None),
                )
            )
            .group_by(AuditLog.user_id, AuditLog.username)
            .all()
        )

        rule = self.detection_rules["suspicious_login"]

        for login in user_logins:
            if login.unique_ips >= rule["max_ips_per_user"]:
                # 检查用户是否在白名单中
                if self.is_user_whitelisted(login.username):
                    continue

                # 检查是否已经存在相同的安全事件
                existing_event = (
                    self.db.query(SecurityEvent)
                    .filter(
                        and_(
                            SecurityEvent.event_type
                            == SecurityEventType.SUSPICIOUS_LOGIN,
                            SecurityEvent.user_id == login.user_id,
                            SecurityEvent.created_at >= start_time,
                            SecurityEvent.is_resolved == False,
                        )
                    )
                    .first()
                )

                if not existing_event:
                    # 创建安全事件
                    event = security_event_crud.create_event(
                        self.db,
                        event_type=SecurityEventType.SUSPICIOUS_LOGIN,
                        level=rule["level"],
                        title=f"检测到可疑登录行为",
                        description=f"用户 {login.username} 在 {hours} 小时内从 {login.unique_ips} 个不同IP登录",
                        user_id=login.user_id,
                        username=login.username,
                        detection_method="behavioral_analysis",
                        detection_rule="suspicious_login",
                        confidence_score=min(100, login.unique_ips * 25),
                        details={
                            "unique_ips": login.unique_ips,
                            "time_window": hours,
                            "ip_addresses": (
                                login.ip_list if hasattr(login, "ip_list") else []
                            ),
                        },
                    )

                    threats.append(
                        {
                            "id": event.id,
                            "type": "suspicious_login",
                            "severity": event.severity_score,
                            "user_id": login.user_id,
                            "username": login.username,
                            "unique_ips": login.unique_ips,
                        }
                    )

        return threats

    async def detect_privilege_escalation(
        self, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """检测权限提升"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        rule = self.detection_rules["privilege_escalation"]
        sensitive_actions = rule["sensitive_actions"]

        # 查询敏感操作
        sensitive_ops = (
            self.db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.action.in_(sensitive_actions),
                    AuditLog.created_at >= start_time,
                    AuditLog.status == "success",
                )
            )
            .all()
        )

        for op in sensitive_ops:
            # 检查操作者是否有足够权限（这里简化处理）
            user = self.db.query(User).filter(User.id == op.user_id).first()
            if user and not user.is_superuser:
                # 非超级用户执行敏感操作
                event = security_event_crud.create_event(
                    self.db,
                    event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                    level=rule["level"],
                    title=f"检测到权限提升行为",
                    description=f"用户 {op.username} 执行了敏感操作: {op.action}",
                    user_id=op.user_id,
                    username=op.username,
                    source_ip=op.ip_address,
                    detection_method="rule_based",
                    detection_rule="privilege_escalation",
                    confidence_score=80,
                    details={
                        "action": op.action,
                        "resource_type": op.resource_type,
                        "resource_id": op.resource_id,
                        "user_role": user.role.value if user.role else None,
                    },
                )

                threats.append(
                    {
                        "id": event.id,
                        "type": "privilege_escalation",
                        "severity": event.severity_score,
                        "user_id": op.user_id,
                        "username": op.username,
                        "action": op.action,
                    }
                )

        return threats

    async def detect_night_activities(self, hours: int = 24) -> List[Dict[str, Any]]:
        """检测深夜活动"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        rule = self.detection_rules["night_activity"]

        # 查询深夜活动
        night_activities = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                func.count(AuditLog.id).label("activity_count"),
            )
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    or_(
                        func.extract("hour", AuditLog.created_at) >= rule["start_hour"],
                        func.extract("hour", AuditLog.created_at) <= rule["end_hour"],
                    ),
                    AuditLog.user_id.isnot(None),
                )
            )
            .group_by(AuditLog.user_id, AuditLog.username)
            .having(func.count(AuditLog.id) >= 10)  # 深夜活动超过10次
            .all()
        )

        for activity in night_activities:
            # 检查用户是否在白名单中
            if self.is_user_whitelisted(activity.username):
                continue

            event = security_event_crud.create_event(
                self.db,
                event_type=SecurityEventType.SYSTEM_ANOMALY,
                level=rule["level"],
                title=f"检测到深夜异常活动",
                description=f"用户 {activity.username} 在深夜进行了 {activity.activity_count} 次操作",
                user_id=activity.user_id,
                username=activity.username,
                detection_method="temporal_analysis",
                detection_rule="night_activity",
                confidence_score=min(100, activity.activity_count * 5),
                details={
                    "activity_count": activity.activity_count,
                    "time_window": hours,
                    "night_hours": f"{rule['start_hour']}:00-{rule['end_hour']}:00",
                },
            )

            threats.append(
                {
                    "id": event.id,
                    "type": "night_activity",
                    "severity": event.severity_score,
                    "user_id": activity.user_id,
                    "username": activity.username,
                    "activity_count": activity.activity_count,
                }
            )

        return threats

    async def detect_api_abuse(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """检测API滥用"""
        threats = []
        start_time = datetime.utcnow() - timedelta(minutes=minutes)

        rule = self.detection_rules["api_abuse"]

        # 查询API请求频率
        api_requests = (
            self.db.query(
                AuditLog.ip_address,
                AuditLog.user_id,
                AuditLog.username,
                func.count(AuditLog.id).label("request_count"),
            )
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    AuditLog.request_url.ilike("/api/%"),
                    AuditLog.ip_address.isnot(None),
                )
            )
            .group_by(AuditLog.ip_address, AuditLog.user_id, AuditLog.username)
            .having(func.count(AuditLog.id) >= rule["request_threshold"])
            .all()
        )

        for request in api_requests:
            # 检查IP是否在白名单中
            if self.is_ip_whitelisted(request.ip_address):
                continue

            event = security_event_crud.create_event(
                self.db,
                event_type=SecurityEventType.API_ABUSE,
                level=rule["level"],
                title=f"检测到API滥用",
                description=f"IP {request.ip_address} 在 {minutes} 分钟内发起了 {request.request_count} 次API请求",
                source_ip=request.ip_address,
                user_id=request.user_id,
                username=request.username,
                detection_method="rate_limiting",
                detection_rule="api_abuse",
                confidence_score=min(100, request.request_count // 10),
                details={
                    "request_count": request.request_count,
                    "time_window": minutes,
                    "threshold": rule["request_threshold"],
                },
            )

            threats.append(
                {
                    "id": event.id,
                    "type": "api_abuse",
                    "severity": event.severity_score,
                    "source_ip": request.ip_address,
                    "request_count": request.request_count,
                }
            )

        return threats

    async def detect_data_exfiltration(self, hours: int = 24) -> List[Dict[str, Any]]:
        """检测数据泄露"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        rule = self.detection_rules["data_exfiltration"]

        # 查询大量下载操作
        download_activities = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                AuditLog.ip_address,
                func.count(AuditLog.id).label("download_count"),
            )
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    AuditLog.action.in_(["download", "export", "view"]),
                    AuditLog.resource_type.in_(["report", "data", "file"]),
                    AuditLog.status == "success",
                )
            )
            .group_by(AuditLog.user_id, AuditLog.username, AuditLog.ip_address)
            .having(func.count(AuditLog.id) >= rule["download_threshold"])
            .all()
        )

        for activity in download_activities:
            event = security_event_crud.create_event(
                self.db,
                event_type=SecurityEventType.DATA_BREACH,
                level=rule["level"],
                title=f"检测到可能的数据泄露",
                description=f"用户 {activity.username} 在 {hours} 小时内进行了 {activity.download_count} 次数据下载",
                source_ip=activity.ip_address,
                user_id=activity.user_id,
                username=activity.username,
                detection_method="volume_analysis",
                detection_rule="data_exfiltration",
                confidence_score=min(100, activity.download_count // 100),
                details={
                    "download_count": activity.download_count,
                    "time_window": hours,
                    "threshold": rule["download_threshold"],
                },
            )

            threats.append(
                {
                    "id": event.id,
                    "type": "data_exfiltration",
                    "severity": event.severity_score,
                    "user_id": activity.user_id,
                    "username": activity.username,
                    "download_count": activity.download_count,
                }
            )

        return threats

    async def detect_failed_operations(self, hours: int = 1) -> List[Dict[str, Any]]:
        """检测失败操作"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 查询失败操作
        failed_ops = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                AuditLog.ip_address,
                AuditLog.action,
                func.count(AuditLog.id).label("failed_count"),
            )
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    AuditLog.status.in_(["failed", "error"]),
                    AuditLog.action != "login",  # 登录失败单独处理
                )
            )
            .group_by(
                AuditLog.user_id,
                AuditLog.username,
                AuditLog.ip_address,
                AuditLog.action,
            )
            .having(func.count(AuditLog.id) >= 10)  # 失败次数阈值
            .all()
        )

        for op in failed_ops:
            event = security_event_crud.create_event(
                self.db,
                event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
                level=SecurityEventLevel.MEDIUM,
                title=f"检测到大量失败操作",
                description=f"用户 {op.username} 的 {op.action} 操作失败了 {op.failed_count} 次",
                source_ip=op.ip_address,
                user_id=op.user_id,
                username=op.username,
                detection_method="failure_analysis",
                detection_rule="failed_operations",
                confidence_score=min(100, op.failed_count * 10),
                details={
                    "action": op.action,
                    "failed_count": op.failed_count,
                    "time_window": hours,
                },
            )

            threats.append(
                {
                    "id": event.id,
                    "type": "failed_operations",
                    "severity": event.severity_score,
                    "user_id": op.user_id,
                    "username": op.username,
                    "action": op.action,
                    "failed_count": op.failed_count,
                }
            )

        return threats

    async def detect_account_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """检测账户异常"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 检测账户创建异常
        account_creations = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                func.count(AuditLog.id).label("creation_count"),
            )
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    AuditLog.action == "user_create",
                    AuditLog.status == "success",
                )
            )
            .group_by(AuditLog.user_id, AuditLog.username)
            .having(func.count(AuditLog.id) >= 5)  # 创建5个以上账户
            .all()
        )

        for creation in account_creations:
            event = security_event_crud.create_event(
                self.db,
                event_type=SecurityEventType.INSIDER_THREAT,
                level=SecurityEventLevel.MEDIUM,
                title=f"检测到异常账户创建",
                description=f"用户 {creation.username} 在 {hours} 小时内创建了 {creation.creation_count} 个账户",
                user_id=creation.user_id,
                username=creation.username,
                detection_method="behavioral_analysis",
                detection_rule="account_anomalies",
                confidence_score=min(100, creation.creation_count * 20),
                details={
                    "creation_count": creation.creation_count,
                    "time_window": hours,
                },
            )

            threats.append(
                {
                    "id": event.id,
                    "type": "account_anomalies",
                    "severity": event.severity_score,
                    "user_id": creation.user_id,
                    "username": creation.username,
                    "creation_count": creation.creation_count,
                }
            )

        return threats

    async def detect_injection_attempts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """检测注入攻击尝试"""
        threats = []
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # SQL注入模式
        sql_patterns = [
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"'\s*OR\s*1\s*=\s*1",
            r"UNION\s+SELECT",
            r"DROP\s+TABLE",
            r"INSERT\s+INTO",
            r"UPDATE\s+.*SET",
            r"DELETE\s+FROM",
        ]

        # XSS模式
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
        ]

        # 查询可疑请求
        suspicious_requests = (
            self.db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.created_at >= start_time,
                    AuditLog.request_url.isnot(None),
                    AuditLog.status.in_(["failed", "error"]),
                )
            )
            .all()
        )

        for request in suspicious_requests:
            request_data = f"{request.request_url} {request.details or ''}"

            # 检测SQL注入
            for pattern in sql_patterns:
                if re.search(pattern, request_data, re.IGNORECASE):
                    event = security_event_crud.create_event(
                        self.db,
                        event_type=SecurityEventType.SQL_INJECTION,
                        level=SecurityEventLevel.HIGH,
                        title=f"检测到SQL注入尝试",
                        description=f"来自IP {request.ip_address} 的请求包含SQL注入模式",
                        source_ip=request.ip_address,
                        user_id=request.user_id,
                        username=request.username,
                        request_url=request.request_url,
                        detection_method="pattern_matching",
                        detection_rule="sql_injection",
                        confidence_score=85,
                        details={
                            "pattern": pattern,
                            "request_data": request_data[:500],  # 限制长度
                        },
                    )

                    threats.append(
                        {
                            "id": event.id,
                            "type": "sql_injection",
                            "severity": event.severity_score,
                            "source_ip": request.ip_address,
                            "pattern": pattern,
                        }
                    )
                    break

            # 检测XSS攻击
            for pattern in xss_patterns:
                if re.search(pattern, request_data, re.IGNORECASE):
                    event = security_event_crud.create_event(
                        self.db,
                        event_type=SecurityEventType.XSS_ATTACK,
                        level=SecurityEventLevel.MEDIUM,
                        title=f"检测到XSS攻击尝试",
                        description=f"来自IP {request.ip_address} 的请求包含XSS攻击模式",
                        source_ip=request.ip_address,
                        user_id=request.user_id,
                        username=request.username,
                        request_url=request.request_url,
                        detection_method="pattern_matching",
                        detection_rule="xss_attack",
                        confidence_score=75,
                        details={
                            "pattern": pattern,
                            "request_data": request_data[:500],
                        },
                    )

                    threats.append(
                        {
                            "id": event.id,
                            "type": "xss_attack",
                            "severity": event.severity_score,
                            "source_ip": request.ip_address,
                            "pattern": pattern,
                        }
                    )
                    break

        return threats

    def _deduplicate_threats(
        self, threats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重威胁"""
        seen = set()
        unique_threats = []

        for threat in threats:
            # 创建唯一标识
            key = (
                threat.get("type"),
                threat.get("source_ip"),
                threat.get("user_id"),
                threat.get("username"),
            )

            if key not in seen:
                seen.add(key)
                unique_threats.append(threat)

        return unique_threats

    async def get_threat_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取威胁摘要"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 统计各类威胁数量
        threat_counts = (
            self.db.query(
                SecurityEvent.event_type, func.count(SecurityEvent.id).label("count")
            )
            .filter(SecurityEvent.created_at >= start_time)
            .group_by(SecurityEvent.event_type)
            .all()
        )

        # 统计威胁级别分布
        level_counts = (
            self.db.query(
                SecurityEvent.level, func.count(SecurityEvent.id).label("count")
            )
            .filter(SecurityEvent.created_at >= start_time)
            .group_by(SecurityEvent.level)
            .all()
        )

        # 获取Top威胁源IP
        top_ips = (
            self.db.query(
                SecurityEvent.source_ip, func.count(SecurityEvent.id).label("count")
            )
            .filter(
                and_(
                    SecurityEvent.created_at >= start_time,
                    SecurityEvent.source_ip.isnot(None),
                )
            )
            .group_by(SecurityEvent.source_ip)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        return {
            "time_window": hours,
            "threat_types": {
                threat.event_type.value: threat.count for threat in threat_counts
            },
            "threat_levels": {level.level.value: level.count for level in level_counts},
            "top_source_ips": [
                {"ip": ip.source_ip, "count": ip.count} for ip in top_ips
            ],
            "total_threats": sum(threat.count for threat in threat_counts),
        }
