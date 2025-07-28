"""错误追踪和报警系统"""

import asyncio
import json
import smtplib
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Set

import aiohttp

from app.core.config import settings
from app.core.logging import get_structured_logger

logger = get_structured_logger(__name__)


class ErrorSeverity(str, Enum):
    """错误严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """报警渠道"""

    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"
    CONSOLE = "console"


@dataclass
class ErrorEvent:
    """错误事件"""

    id: str
    timestamp: datetime
    error_type: str
    error_code: str
    message: str
    severity: ErrorSeverity
    path: str
    method: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    traceback: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["first_seen"] = self.first_seen.isoformat() if self.first_seen else None
        data["last_seen"] = self.last_seen.isoformat() if self.last_seen else None
        return data


@dataclass
class AlertRule:
    """报警规则"""

    name: str
    error_types: Set[str]  # 匹配的错误类型
    severity_threshold: ErrorSeverity  # 严重程度阈值
    frequency_threshold: int  # 频率阈值（次数）
    time_window: int  # 时间窗口（秒）
    channels: List[AlertChannel]  # 报警渠道
    enabled: bool = True
    cooldown: int = 300  # 冷却时间（秒）
    last_triggered: Optional[datetime] = None

    def should_trigger(self, error_event: ErrorEvent, recent_count: int) -> bool:
        """判断是否应该触发报警"""
        if not self.enabled:
            return False

        # 检查错误类型匹配
        if self.error_types and error_event.error_type not in self.error_types:
            return False

        # 检查严重程度
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if (
            severity_levels[error_event.severity]
            < severity_levels[self.severity_threshold]
        ):
            return False

        # 检查频率阈值
        if recent_count < self.frequency_threshold:
            return False

        # 检查冷却时间
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(seconds=self.cooldown)
            if datetime.utcnow() < cooldown_end:
                return False

        return True


class ErrorTracker:
    """错误追踪器"""

    def __init__(self):
        self._errors: Dict[str, ErrorEvent] = {}  # 错误事件存储
        self._error_history: deque = deque(maxlen=10000)  # 错误历史记录
        self._error_counts: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )  # 错误计数
        self._alert_rules: List[AlertRule] = []
        self._lock = Lock()
        self._setup_default_rules()

    def _setup_default_rules(self):
        """设置默认报警规则"""
        # 关键错误立即报警
        self._alert_rules.append(
            AlertRule(
                name="critical_errors",
                error_types=set(),  # 所有错误类型
                severity_threshold=ErrorSeverity.CRITICAL,
                frequency_threshold=1,
                time_window=60,
                channels=[AlertChannel.EMAIL, AlertChannel.LOG],
                cooldown=60,
            )
        )

        # 高频错误报警
        self._alert_rules.append(
            AlertRule(
                name="high_frequency_errors",
                error_types=set(),
                severity_threshold=ErrorSeverity.MEDIUM,
                frequency_threshold=10,
                time_window=300,  # 5分钟内10次
                channels=[AlertChannel.EMAIL, AlertChannel.LOG],
                cooldown=600,  # 10分钟冷却
            )
        )

        # 数据库错误报警
        self._alert_rules.append(
            AlertRule(
                name="database_errors",
                error_types={"DATABASE_ERROR"},
                severity_threshold=ErrorSeverity.LOW,
                frequency_threshold=5,
                time_window=300,
                channels=[AlertChannel.EMAIL, AlertChannel.LOG],
                cooldown=300,
            )
        )

    def track_error(self, error_event: ErrorEvent) -> None:
        """追踪错误事件"""
        with self._lock:
            error_key = self._generate_error_key(error_event)

            # 更新或创建错误事件
            if error_key in self._errors:
                existing_error = self._errors[error_key]
                existing_error.count += 1
                existing_error.last_seen = error_event.timestamp
                # 更新详细信息（保留最新的）
                if error_event.details:
                    existing_error.details = error_event.details
                if error_event.traceback:
                    existing_error.traceback = error_event.traceback
            else:
                self._errors[error_key] = error_event

            # 添加到历史记录
            self._error_history.append(error_event)

            # 更新计数
            self._error_counts[error_key].append(error_event.timestamp)

            # 检查报警规则
            self._check_alert_rules(error_event, error_key)

    def _generate_error_key(self, error_event: ErrorEvent) -> str:
        """生成错误事件的唯一键"""
        return f"{error_event.error_type}:{error_event.error_code}:{error_event.path}"

    def _check_alert_rules(self, error_event: ErrorEvent, error_key: str) -> None:
        """检查报警规则"""
        current_time = datetime.utcnow()

        for rule in self._alert_rules:
            # 计算时间窗口内的错误次数
            window_start = current_time - timedelta(seconds=rule.time_window)
            recent_errors = [
                ts for ts in self._error_counts[error_key] if ts >= window_start
            ]

            if rule.should_trigger(error_event, len(recent_errors)):
                rule.last_triggered = current_time
                # 尝试在异步环境中发送报警，如果不在异步环境中则记录日志
                try:
                    asyncio.create_task(
                        self._send_alert(rule, error_event, len(recent_errors))
                    )
                except RuntimeError:
                    # 不在异步环境中，使用同步方式记录报警
                    self._log_alert_sync(rule, error_event, len(recent_errors))

    def _log_alert_sync(
        self, rule: AlertRule, error_event: ErrorEvent, count: int
    ) -> None:
        """同步方式记录报警"""
        alert_data = {
            "rule_name": rule.name,
            "error_event": error_event.to_dict(),
            "count": count,
            "time_window": rule.time_window,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 记录到日志
        logger.warning(
            f"ALERT TRIGGERED: {rule.name} - {error_event.error_type} "
            f"occurred {count} times in {rule.time_window} seconds",
            extra={"alert_data": alert_data},
        )

        # 输出到控制台
        print(f"🚨 报警触发: {rule.name}")
        print(f"   错误类型: {error_event.error_type}")
        print(f"   错误消息: {error_event.message}")
        print(f"   发生次数: {count} 次")
        print(f"   时间窗口: {rule.time_window} 秒")
        print(f"   严重程度: {error_event.severity}")
        print(f"   路径: {error_event.path}")
        print()

    async def _send_alert(
        self, rule: AlertRule, error_event: ErrorEvent, count: int
    ) -> None:
        """发送报警"""
        alert_data = {
            "rule_name": rule.name,
            "error_event": error_event.to_dict(),
            "count": count,
            "time_window": rule.time_window,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for channel in rule.channels:
            try:
                if channel == AlertChannel.EMAIL:
                    await self._send_email_alert(alert_data)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(alert_data)
                elif channel == AlertChannel.LOG:
                    await self._send_log_alert(alert_data)
                elif channel == AlertChannel.CONSOLE:
                    await self._send_console_alert(alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")

    async def _send_email_alert(self, alert_data: Dict[str, Any]) -> None:
        """发送邮件报警"""
        if not hasattr(settings, "SMTP_HOST") or not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email alert")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = getattr(settings, "SMTP_FROM", "noreply@example.com")
            msg["To"] = getattr(settings, "ALERT_EMAIL", "admin@example.com")
            msg["Subject"] = (
                f"[ALERT] {alert_data['rule_name']} - {alert_data['error_event']['error_type']}"
            )

            body = self._format_email_body(alert_data)
            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(
                settings.SMTP_HOST, getattr(settings, "SMTP_PORT", 587)
            )
            if getattr(settings, "SMTP_TLS", True):
                server.starttls()
            if hasattr(settings, "SMTP_USER") and settings.SMTP_USER:
                server.login(settings.SMTP_USER, getattr(settings, "SMTP_PASSWORD", ""))

            server.send_message(msg)
            server.quit()

            logger.info(f"Email alert sent for rule: {alert_data['rule_name']}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, alert_data: Dict[str, Any]) -> None:
        """发送Webhook报警"""
        # 这里可以集成Slack、Discord、钉钉等Webhook
        webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None)
        if not webhook_url:
            logger.warning("Webhook URL not configured, skipping webhook alert")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=alert_data) as response:
                    if response.status == 200:
                        logger.info(
                            f"Webhook alert sent for rule: {alert_data['rule_name']}"
                        )
                    else:
                        logger.error(
                            f"Webhook alert failed with status: {response.status}"
                        )
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    async def _send_log_alert(self, alert_data: Dict[str, Any]) -> None:
        """发送日志报警"""
        logger.critical(
            f"ALERT TRIGGERED: {alert_data['rule_name']}",
            extra={"alert_data": alert_data, "alert_type": "error_tracking"},
        )

    async def _send_console_alert(self, alert_data: Dict[str, Any]) -> None:
        """发送控制台报警"""
        print(f"\n{'=' * 50}")
        print(f"🚨 ALERT: {alert_data['rule_name']}")
        print(
            f"Error: {alert_data['error_event']['error_type']} - {alert_data['error_event']['message']}"
        )
        print(
            f"Count: {alert_data['count']} times in {alert_data['time_window']} seconds"
        )
        print(f"Path: {alert_data['error_event']['path']}")
        print(f"Time: {alert_data['timestamp']}")
        print(f"{'=' * 50}\n")

    def _format_email_body(self, alert_data: Dict[str, Any]) -> str:
        """格式化邮件内容"""
        error_event = alert_data["error_event"]
        return f"""
        <html>
        <body>
            <h2>🚨 Error Alert: {alert_data["rule_name"]}</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Error Type</strong></td><td>{error_event["error_type"]}</td></tr>
                <tr><td><strong>Error Code</strong></td><td>{error_event["error_code"]}</td></tr>
                <tr><td><strong>Message</strong></td><td>{error_event["message"]}</td></tr>
                <tr><td><strong>Severity</strong></td><td>{error_event["severity"]}</td></tr>
                <tr><td><strong>Path</strong></td><td>{error_event["path"]}</td></tr>
                <tr><td><strong>Method</strong></td><td>{error_event["method"]}</td></tr>
                <tr><td><strong>Count</strong></td><td>{alert_data["count"]} times in {alert_data["time_window"]} seconds</td></tr>
                <tr><td><strong>First Seen</strong></td><td>{error_event["first_seen"]}</td></tr>
                <tr><td><strong>Last Seen</strong></td><td>{error_event["last_seen"]}</td></tr>
                <tr><td><strong>Client IP</strong></td><td>{error_event.get("client_ip", "Unknown")}</td></tr>
                <tr><td><strong>Request ID</strong></td><td>{error_event.get("request_id", "N/A")}</td></tr>
            </table>

            {f"<h3>Traceback</h3><pre>{error_event['traceback']}</pre>" if error_event.get("traceback") else ""}

            {f"<h3>Details</h3><pre>{json.dumps(error_event.get('details', {}), indent=2)}</pre>" if error_event.get("details") else ""}
        </body>
        </html>
        """

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计信息"""
        with self._lock:
            current_time = datetime.utcnow()
            start_time = current_time - timedelta(hours=hours)

            # 过滤时间范围内的错误
            recent_errors = [
                error for error in self._error_history if error.timestamp >= start_time
            ]

            # 统计信息
            stats = {
                "total_errors": len(recent_errors),
                "unique_errors": len(
                    {self._generate_error_key(e) for e in recent_errors}
                ),
                "error_by_type": defaultdict(int),
                "error_by_severity": defaultdict(int),
                "error_by_path": defaultdict(int),
                "top_errors": [],
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": current_time.isoformat(),
                    "hours": hours,
                },
            }

            # 按类型统计
            for error in recent_errors:
                stats["error_by_type"][error.error_type] += 1
                stats["error_by_severity"][error.severity] += 1
                stats["error_by_path"][error.path] += 1

            # 获取最频繁的错误
            error_counts = defaultdict(int)
            for error in recent_errors:
                key = self._generate_error_key(error)
                error_counts[key] += 1

            stats["top_errors"] = [
                {
                    "error_key": key,
                    "count": count,
                    "error_info": (
                        self._errors.get(key, {}).to_dict()
                        if key in self._errors
                        else {}
                    ),
                }
                for key, count in sorted(
                    error_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            return dict(stats)

    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加报警规则"""
        with self._lock:
            self._alert_rules.append(rule)

    def remove_alert_rule(self, rule_name: str) -> bool:
        """移除报警规则"""
        with self._lock:
            for i, rule in enumerate(self._alert_rules):
                if rule.name == rule_name:
                    del self._alert_rules[i]
                    return True
            return False

    def get_alert_rules(self) -> List[AlertRule]:
        """获取所有报警规则"""
        with self._lock:
            return self._alert_rules.copy()

    def clear_old_errors(self, days: int = 7) -> int:
        """清理旧的错误记录"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # 清理错误事件
            old_keys = [
                key
                for key, error in self._errors.items()
                if error.last_seen < cutoff_time
            ]

            for key in old_keys:
                del self._errors[key]
                if key in self._error_counts:
                    del self._error_counts[key]

            # 清理历史记录
            original_length = len(self._error_history)
            self._error_history = deque(
                [
                    error
                    for error in self._error_history
                    if error.timestamp >= cutoff_time
                ],
                maxlen=self._error_history.maxlen,
            )

            cleaned_count = len(old_keys) + (original_length - len(self._error_history))
            logger.info(
                f"Cleaned {cleaned_count} old error records older than {days} days"
            )

            return cleaned_count


# 全局错误追踪器实例
error_tracker = ErrorTracker()


def track_error(
    error_type: str,
    error_code: str,
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    path: str = "/",
    method: str = "GET",
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    traceback: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """追踪错误的便捷函数"""
    error_event = ErrorEvent(
        id=f"{error_type}_{error_code}_{int(time.time())}",
        timestamp=datetime.utcnow(),
        error_type=error_type,
        error_code=error_code,
        message=message,
        severity=severity,
        path=path,
        method=method,
        user_id=user_id,
        request_id=request_id,
        client_ip=client_ip,
        traceback=traceback,
        details=details,
    )

    error_tracker.track_error(error_event)


def get_error_stats(hours: int = 24) -> Dict[str, Any]:
    """获取错误统计信息的便捷函数"""
    return error_tracker.get_error_statistics(hours)
