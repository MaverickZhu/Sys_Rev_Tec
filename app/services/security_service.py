"""安全监控服务模块

提供安全监控、威胁检测、审计日志管理等服务
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.security.threat_detector import ThreatDetector
from app.crud.crud_audit_log import audit_log as audit_log_crud
from app.crud.crud_security_event import security_event as security_event_crud
from app.models.audit_log import AuditLog
from app.models.security_event import (
    SecurityEvent,
    SecurityEventLevel,
)
from app.models.user import User
from app.schemas.security_monitor import (
    SecurityAlert,
    SecurityDashboardData,
    SecurityMetrics,
    SecurityRecommendation,
    SecurityStatistics,
    SecurityTrend,
    SystemHealthStatus,
    ThreatDetectionResult,
    ThreatLevel,
    UserActivitySummary,
)

logger = logging.getLogger(__name__)


class SecurityService:
    """安全监控服务"""

    def __init__(self, db: Session):
        self.db = db
        self.threat_detector = ThreatDetector(db)

    async def get_security_dashboard_data(self) -> SecurityDashboardData:
        """获取安全监控仪表板数据"""
        logger.info("获取安全监控仪表板数据")

        # 并行获取各项数据
        tasks = [
            self.get_security_metrics(),
            self.get_security_alerts(),
            self.get_security_trends(),
            self.get_user_activity_summary(),
            self.get_system_health_status(),
            self.get_threat_detection_results(),
            self.get_security_recommendations(),
        ]

        results = await asyncio.gather(*tasks)

        return SecurityDashboardData(
            metrics=results[0],
            alerts=results[1],
            trends=results[2],
            user_activity=results[3],
            system_health=results[4],
            threat_detection=results[5],
            recommendations=results[6],
            last_updated=datetime.utcnow(),
        )

    async def get_security_metrics(self) -> SecurityMetrics:
        """获取安全指标"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # 今日威胁数量
        today_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(SecurityEvent.created_at >= today_start)
            .scalar()
            or 0
        )

        # 本周威胁数量
        week_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(SecurityEvent.created_at >= week_start)
            .scalar()
            or 0
        )

        # 活跃威胁数量（未解决）
        active_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(SecurityEvent.is_resolved == False)
            .scalar()
            or 0
        )

        # 高危威胁数量
        critical_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(
                and_(
                    SecurityEvent.level == SecurityEventLevel.CRITICAL,
                    SecurityEvent.is_resolved == False,
                )
            )
            .scalar()
            or 0
        )

        # 今日登录失败次数
        today_failed_logins = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "failed",
                    AuditLog.created_at >= today_start,
                )
            )
            .scalar()
            or 0
        )

        # 今日活跃用户数
        today_active_users = (
            self.db.query(func.count(func.distinct(AuditLog.user_id)))
            .filter(
                and_(AuditLog.created_at >= today_start, AuditLog.user_id.isnot(None))
            )
            .scalar()
            or 0
        )

        # 系统可用性（简化计算）
        total_requests = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.created_at >= today_start)
            .scalar()
            or 1
        )

        failed_requests = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.created_at >= today_start,
                    AuditLog.status.in_(["failed", "error"]),
                )
            )
            .scalar()
            or 0
        )

        system_availability = (
            (total_requests - failed_requests) / total_requests
        ) * 100

        # 威胁趋势（与上周比较）
        prev_week_start = week_start - timedelta(days=7)
        prev_week_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(
                and_(
                    SecurityEvent.created_at >= prev_week_start,
                    SecurityEvent.created_at < week_start,
                )
            )
            .scalar()
            or 1
        )

        threat_trend = ((week_threats - prev_week_threats) / prev_week_threats) * 100

        return SecurityMetrics(
            total_threats_today=today_threats,
            total_threats_week=week_threats,
            active_threats=active_threats,
            critical_threats=critical_threats,
            failed_logins_today=today_failed_logins,
            active_users_today=today_active_users,
            system_availability=round(system_availability, 2),
            threat_trend_percentage=round(threat_trend, 2),
        )

    async def get_security_alerts(self, limit: int = 10) -> List[SecurityAlert]:
        """获取安全警报"""
        # 获取最新的未解决安全事件
        events = (
            self.db.query(SecurityEvent)
            .filter(SecurityEvent.is_resolved == False)
            .order_by(
                desc(SecurityEvent.severity_score), desc(SecurityEvent.created_at)
            )
            .limit(limit)
            .all()
        )

        alerts = []
        for event in events:
            # 确定威胁级别
            if event.level == SecurityEventLevel.CRITICAL:
                threat_level = ThreatLevel.CRITICAL
            elif event.level == SecurityEventLevel.HIGH:
                threat_level = ThreatLevel.HIGH
            elif event.level == SecurityEventLevel.MEDIUM:
                threat_level = ThreatLevel.MEDIUM
            else:
                threat_level = ThreatLevel.LOW

            alerts.append(
                SecurityAlert(
                    id=event.id,
                    title=event.title,
                    description=event.description,
                    threat_level=threat_level,
                    source_ip=event.source_ip,
                    affected_user=event.username,
                    detection_time=event.created_at,
                    is_resolved=event.is_resolved,
                    confidence_score=event.confidence_score,
                )
            )

        return alerts

    async def get_security_trends(self, days: int = 30) -> List[SecurityTrend]:
        """获取安全趋势数据"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # 按日期统计威胁数量
        daily_threats = (
            self.db.query(
                func.date(SecurityEvent.created_at).label("date"),
                func.count(SecurityEvent.id).label("count"),
            )
            .filter(func.date(SecurityEvent.created_at) >= start_date)
            .group_by(func.date(SecurityEvent.created_at))
            .all()
        )

        # 按日期统计失败登录
        daily_failed_logins = (
            self.db.query(
                func.date(AuditLog.created_at).label("date"),
                func.count(AuditLog.id).label("count"),
            )
            .filter(
                and_(
                    func.date(AuditLog.created_at) >= start_date,
                    AuditLog.action == "login",
                    AuditLog.status == "failed",
                )
            )
            .group_by(func.date(AuditLog.created_at))
            .all()
        )

        # 创建日期到数量的映射
        threats_map = {threat.date: threat.count for threat in daily_threats}
        failed_logins_map = {login.date: login.count for login in daily_failed_logins}

        # 生成完整的日期序列
        trends = []
        current_date = start_date
        while current_date <= end_date:
            trends.append(
                SecurityTrend(
                    date=current_date,
                    threat_count=threats_map.get(current_date, 0),
                    failed_login_count=failed_logins_map.get(current_date, 0),
                    incident_count=0,  # 可以根据需要添加事件统计
                )
            )
            current_date += timedelta(days=1)

        return trends

    async def get_user_activity_summary(
        self, hours: int = 24
    ) -> List[UserActivitySummary]:
        """获取用户活动摘要"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 统计用户活动
        user_activities = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                func.count(AuditLog.id).label("total_actions"),
                func.count(func.distinct(AuditLog.ip_address)).label("unique_ips"),
                func.max(AuditLog.created_at).label("last_activity"),
                func.sum(
                    func.case([(AuditLog.status.in_(["failed", "error"]), 1)], else_=0)
                ).label("failed_actions"),
            )
            .filter(
                and_(AuditLog.created_at >= start_time, AuditLog.user_id.isnot(None))
            )
            .group_by(AuditLog.user_id, AuditLog.username)
            .order_by(desc("total_actions"))
            .limit(20)
            .all()
        )

        summaries = []
        for activity in user_activities:
            # 计算风险评分
            risk_score = 0
            if activity.failed_actions and activity.total_actions:
                failure_rate = activity.failed_actions / activity.total_actions
                risk_score += failure_rate * 30

            if activity.unique_ips > 3:
                risk_score += (activity.unique_ips - 3) * 10

            if activity.total_actions > 1000:
                risk_score += 20

            risk_score = min(100, max(0, risk_score))

            summaries.append(
                UserActivitySummary(
                    user_id=activity.user_id,
                    username=activity.username,
                    total_actions=activity.total_actions,
                    failed_actions=activity.failed_actions or 0,
                    unique_ips=activity.unique_ips,
                    last_activity=activity.last_activity,
                    risk_score=round(risk_score, 1),
                )
            )

        return summaries

    async def get_system_health_status(self) -> SystemHealthStatus:
        """获取系统健康状态"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # 系统负载（基于请求数量）
        recent_requests = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.created_at >= hour_ago)
            .scalar()
            or 0
        )

        # 错误率
        recent_errors = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.created_at >= hour_ago,
                    AuditLog.status.in_(["failed", "error"]),
                )
            )
            .scalar()
            or 0
        )

        error_rate = (recent_errors / max(recent_requests, 1)) * 100

        # 活跃连接数（基于唯一IP）
        active_connections = (
            self.db.query(func.count(func.distinct(AuditLog.ip_address)))
            .filter(
                and_(AuditLog.created_at >= hour_ago, AuditLog.ip_address.isnot(None))
            )
            .scalar()
            or 0
        )

        # 数据库连接状态（简化）
        try:
            self.db.execute("SELECT 1")
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"

        # 确定整体状态
        if error_rate > 10 or database_status == "unhealthy":
            overall_status = "critical"
        elif error_rate > 5 or recent_requests > 1000:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return SystemHealthStatus(
            overall_status=overall_status,
            cpu_usage=0.0,  # 需要系统监控集成
            memory_usage=0.0,  # 需要系统监控集成
            disk_usage=0.0,  # 需要系统监控集成
            network_status="healthy",
            database_status=database_status,
            active_connections=active_connections,
            error_rate=round(error_rate, 2),
            last_check=now,
        )

    async def get_threat_detection_results(self) -> ThreatDetectionResult:
        """获取威胁检测结果"""
        # 运行威胁检测
        threats = await self.threat_detector.run_scan("quick")

        # 获取威胁摘要
        await self.threat_detector.get_threat_summary(24)

        # 分类威胁
        threat_categories = defaultdict(int)
        for threat in threats:
            threat_categories[threat.get("type", "unknown")] += 1

        return ThreatDetectionResult(
            scan_time=datetime.utcnow(),
            total_threats_detected=len(threats),
            high_priority_threats=len(
                [t for t in threats if t.get("severity", 0) >= 70]
            ),
            threat_categories=dict(threat_categories),
            scan_duration=1.5,  # 模拟扫描时间
            last_scan_status="completed",
        )

    async def get_security_recommendations(self) -> List[SecurityRecommendation]:
        """获取安全建议"""
        recommendations = []
        now = datetime.utcnow()

        # 检查是否有未解决的高危威胁
        critical_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(
                and_(
                    SecurityEvent.level == SecurityEventLevel.CRITICAL,
                    SecurityEvent.is_resolved == False,
                )
            )
            .scalar()
            or 0
        )

        if critical_threats > 0:
            recommendations.append(
                SecurityRecommendation(
                    id="critical_threats",
                    title="处理高危威胁",
                    description=f"系统中有 {critical_threats} 个未解决的高危威胁，建议立即处理",
                    priority="high",
                    category="threat_management",
                    action_required=True,
                    estimated_impact="high",
                )
            )

        # 检查失败登录次数
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        failed_logins = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "failed",
                    AuditLog.created_at >= today_start,
                )
            )
            .scalar()
            or 0
        )

        if failed_logins > 100:
            recommendations.append(
                SecurityRecommendation(
                    id="high_failed_logins",
                    title="加强登录安全",
                    description=f"今日失败登录次数达到 {failed_logins} 次，建议启用账户锁定策略",
                    priority="medium",
                    category="access_control",
                    action_required=True,
                    estimated_impact="medium",
                )
            )

        # 检查长时间未更新密码的用户
        old_password_users = (
            self.db.query(func.count(User.id))
            .filter(
                or_(
                    User.updated_at < now - timedelta(days=90),
                    User.updated_at.is_(None),
                )
            )
            .scalar()
            or 0
        )

        if old_password_users > 0:
            recommendations.append(
                SecurityRecommendation(
                    id="password_policy",
                    title="密码策略优化",
                    description=f"有 {old_password_users} 个用户长时间未更新密码，建议强制密码更新",
                    priority="low",
                    category="password_policy",
                    action_required=False,
                    estimated_impact="medium",
                )
            )

        # 检查权限过度分配
        superusers = (
            self.db.query(func.count(User.id)).filter(User.is_superuser).scalar() or 0
        )

        total_users = self.db.query(func.count(User.id)).scalar() or 1
        superuser_ratio = (superusers / total_users) * 100

        if superuser_ratio > 10:
            recommendations.append(
                SecurityRecommendation(
                    id="privilege_review",
                    title="权限审查",
                    description=f"超级用户比例过高（{superuser_ratio:.1f}%），建议审查用户权限分配",
                    priority="medium",
                    category="access_control",
                    action_required=True,
                    estimated_impact="high",
                )
            )

        # 如果没有特殊建议，添加一般性建议
        if not recommendations:
            recommendations.append(
                SecurityRecommendation(
                    id="general_security",
                    title="定期安全检查",
                    description="系统安全状态良好，建议继续保持定期安全检查和监控",
                    priority="low",
                    category="monitoring",
                    action_required=False,
                    estimated_impact="low",
                )
            )

        return recommendations

    async def get_security_statistics(self, days: int = 30) -> SecurityStatistics:
        """获取安全统计数据"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 威胁统计
        total_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(SecurityEvent.created_at >= start_date)
            .scalar()
            or 0
        )

        resolved_threats = (
            self.db.query(func.count(SecurityEvent.id))
            .filter(
                and_(
                    SecurityEvent.created_at >= start_date,
                    SecurityEvent.is_resolved,
                )
            )
            .scalar()
            or 0
        )

        # 威胁类型分布
        threat_types = (
            self.db.query(
                SecurityEvent.event_type, func.count(SecurityEvent.id).label("count")
            )
            .filter(SecurityEvent.created_at >= start_date)
            .group_by(SecurityEvent.event_type)
            .all()
        )

        # 威胁级别分布
        threat_levels = (
            self.db.query(
                SecurityEvent.level, func.count(SecurityEvent.id).label("count")
            )
            .filter(SecurityEvent.created_at >= start_date)
            .group_by(SecurityEvent.level)
            .all()
        )

        # 用户活动统计
        total_logins = (
            self.db.query(func.count(AuditLog.id))
            .filter(and_(AuditLog.action == "login", AuditLog.created_at >= start_date))
            .scalar()
            or 0
        )

        failed_logins = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                and_(
                    AuditLog.action == "login",
                    AuditLog.status == "failed",
                    AuditLog.created_at >= start_date,
                )
            )
            .scalar()
            or 0
        )

        unique_users = (
            self.db.query(func.count(func.distinct(AuditLog.user_id)))
            .filter(
                and_(AuditLog.created_at >= start_date, AuditLog.user_id.isnot(None))
            )
            .scalar()
            or 0
        )

        return SecurityStatistics(
            period_days=days,
            total_threats=total_threats,
            resolved_threats=resolved_threats,
            active_threats=total_threats - resolved_threats,
            threat_resolution_rate=round(
                (resolved_threats / max(total_threats, 1)) * 100, 2
            ),
            threat_types_distribution={
                threat.event_type.value: threat.count for threat in threat_types
            },
            threat_levels_distribution={
                level.level.value: level.count for level in threat_levels
            },
            total_login_attempts=total_logins,
            failed_login_attempts=failed_logins,
            login_success_rate=round(
                ((total_logins - failed_logins) / max(total_logins, 1)) * 100, 2
            ),
            unique_active_users=unique_users,
            average_threats_per_day=round(total_threats / max(days, 1), 2),
        )

    async def create_audit_log(self, **kwargs) -> AuditLog:
        """创建审计日志"""
        return audit_log_crud.create_log(self.db, **kwargs)

    async def create_security_event(self, **kwargs) -> SecurityEvent:
        """创建安全事件"""
        return security_event_crud.create_event(self.db, **kwargs)

    async def resolve_security_event(
        self, event_id: int, resolved_by: int, resolution_notes: str = None
    ) -> SecurityEvent:
        """解决安全事件"""
        return security_event_crud.resolve_event(
            self.db,
            event_id=event_id,
            resolved_by=resolved_by,
            resolution_notes=resolution_notes,
        )

    async def run_threat_detection(
        self, scan_type: str = "quick"
    ) -> List[Dict[str, Any]]:
        """运行威胁检测"""
        return await self.threat_detector.run_scan(scan_type)

    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """清理旧数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 清理旧的审计日志
        deleted_logs = audit_log_crud.cleanup_old_logs(self.db, cutoff_date)

        # 清理旧的已解决安全事件
        deleted_events = security_event_crud.cleanup_old_events(self.db, cutoff_date)

        return {
            "deleted_audit_logs": deleted_logs,
            "deleted_security_events": deleted_events,
        }
