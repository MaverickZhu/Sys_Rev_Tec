"""审计日志CRUD操作

提供审计日志的创建、查询、统计等功能
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.schemas.security_monitor import AuditLogCreate


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, Dict[str, Any]]):
    """审计日志CRUD操作类"""

    def create_log(
        self,
        db: Session,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_url: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> AuditLog:
        """创建审计日志"""
        # 将details转换为JSON字符串
        details_json = None
        if details:
            import json

            details_json = json.dumps(details, ensure_ascii=False)

        db_obj = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            status=status,
            status_code=status_code,
            error_message=error_message,
            duration_ms=duration_ms,
            session_id=session_id,
            trace_id=trace_id,
            created_at=datetime.utcnow(),
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def search(
        self,
        db: Session,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[AuditLog]:
        """搜索审计日志"""
        query = db.query(self.model)

        # 添加过滤条件
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)

        if username:
            query = query.filter(self.model.username.ilike(f"%{username}%"))

        if action:
            query = query.filter(self.model.action.ilike(f"%{action}%"))

        if resource_type:
            query = query.filter(self.model.resource_type == resource_type)

        if resource_id:
            query = query.filter(self.model.resource_id == resource_id)

        if ip_address:
            query = query.filter(self.model.ip_address == ip_address)

        if status:
            query = query.filter(self.model.status == status)

        if session_id:
            query = query.filter(self.model.session_id == session_id)

        if trace_id:
            query = query.filter(self.model.trace_id == trace_id)

        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)

        if end_time:
            query = query.filter(self.model.created_at <= end_time)

        # 排序
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(self.model.created_at))

        return query.offset(skip).limit(limit).all()

    def count(
        self,
        db: Session,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> int:
        """统计符合条件的审计日志数量"""
        query = db.query(self.model)

        # 添加过滤条件（与search方法相同的过滤逻辑）
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)

        if username:
            query = query.filter(self.model.username.ilike(f"%{username}%"))

        if action:
            query = query.filter(self.model.action.ilike(f"%{action}%"))

        if resource_type:
            query = query.filter(self.model.resource_type == resource_type)

        if resource_id:
            query = query.filter(self.model.resource_id == resource_id)

        if ip_address:
            query = query.filter(self.model.ip_address == ip_address)

        if status:
            query = query.filter(self.model.status == status)

        if session_id:
            query = query.filter(self.model.session_id == session_id)

        if trace_id:
            query = query.filter(self.model.trace_id == trace_id)

        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)

        if end_time:
            query = query.filter(self.model.created_at <= end_time)

        return query.count()

    def get_statistics(
        self,
        db: Session,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取审计日志统计信息"""
        query = db.query(self.model)

        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)

        if end_time:
            query = query.filter(self.model.created_at <= end_time)

        # 总数统计
        total_logs = query.count()

        # 按状态统计
        status_stats = (
            query.with_entities(
                self.model.status, func.count(self.model.id).label("count")
            )
            .group_by(self.model.status)
            .all()
        )

        # 按操作类型统计
        action_stats = (
            query.with_entities(
                self.model.action, func.count(self.model.id).label("count")
            )
            .group_by(self.model.action)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # 按用户统计
        user_stats = (
            query.filter(self.model.user_id.isnot(None))
            .with_entities(
                self.model.user_id,
                self.model.username,
                func.count(self.model.id).label("count"),
            )
            .group_by(self.model.user_id, self.model.username)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # 按IP统计
        ip_stats = (
            query.filter(self.model.ip_address.isnot(None))
            .with_entities(
                self.model.ip_address, func.count(self.model.id).label("count")
            )
            .group_by(self.model.ip_address)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # 失败操作统计
        failed_logs = query.filter(self.model.status.in_(["failed", "error"])).count()

        # 安全相关操作统计
        security_actions = [
            "login",
            "logout",
            "login_failed",
            "password_change",
            "permission_change",
            "role_change",
            "account_locked",
        ]
        security_logs = query.filter(self.model.action.in_(security_actions)).count()

        return {
            "total_logs": total_logs,
            "failed_logs": failed_logs,
            "security_logs": security_logs,
            "status_distribution": {stat.status: stat.count for stat in status_stats},
            "top_actions": [
                {"action": stat.action, "count": stat.count} for stat in action_stats
            ],
            "top_users": [
                {
                    "user_id": stat.user_id,
                    "username": stat.username,
                    "count": stat.count,
                }
                for stat in user_stats
            ],
            "top_ips": [
                {"ip_address": stat.ip_address, "count": stat.count}
                for stat in ip_stats
            ],
        }

    def get_user_activity(
        self,
        db: Session,
        *,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取特定用户的活动统计"""
        query = db.query(self.model).filter(self.model.user_id == user_id)

        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)

        if end_time:
            query = query.filter(self.model.created_at <= end_time)

        # 总活动数
        total_activities = query.count()

        # 失败操作数
        failed_activities = query.filter(
            self.model.status.in_(["failed", "error"])
        ).count()

        # 唯一IP数
        unique_ips = query.with_entities(self.model.ip_address).distinct().count()

        # 最后活动时间
        last_activity = query.order_by(desc(self.model.created_at)).first()

        # 按操作类型统计
        action_stats = (
            query.with_entities(
                self.model.action, func.count(self.model.id).label("count")
            )
            .group_by(self.model.action)
            .order_by(desc("count"))
            .all()
        )

        # 按小时统计活动分布
        hourly_stats = (
            query.with_entities(
                func.extract("hour", self.model.created_at).label("hour"),
                func.count(self.model.id).label("count"),
            )
            .group_by("hour")
            .order_by("hour")
            .all()
        )

        return {
            "user_id": user_id,
            "total_activities": total_activities,
            "failed_activities": failed_activities,
            "unique_ips": unique_ips,
            "last_activity": last_activity.created_at if last_activity else None,
            "action_distribution": {stat.action: stat.count for stat in action_stats},
            "hourly_distribution": {
                int(stat.hour): stat.count for stat in hourly_stats
            },
        }

    def get_security_events(
        self,
        db: Session,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取安全相关的审计日志"""
        security_actions = [
            "login_failed",
            "password_change",
            "permission_change",
            "role_change",
            "account_locked",
            "account_unlocked",
            "password_reset",
            "two_factor_enabled",
            "two_factor_disabled",
        ]

        query = db.query(self.model).filter(
            or_(
                self.model.action.in_(security_actions),
                self.model.status.in_(["failed", "error"]),
            )
        )

        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)

        if end_time:
            query = query.filter(self.model.created_at <= end_time)

        return query.order_by(desc(self.model.created_at)).limit(limit).all()

    def get_failed_login_attempts(
        self,
        db: Session,
        *,
        ip_address: Optional[str] = None,
        username: Optional[str] = None,
        hours: int = 24,
    ) -> List[AuditLog]:
        """获取失败的登录尝试"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        query = db.query(self.model).filter(
            and_(
                self.model.action == "login",
                self.model.status == "failed",
                self.model.created_at >= start_time,
            )
        )

        if ip_address:
            query = query.filter(self.model.ip_address == ip_address)

        if username:
            query = query.filter(self.model.username == username)

        return query.order_by(desc(self.model.created_at)).all()

    def detect_suspicious_activity(
        self, db: Session, *, hours: int = 24
    ) -> Dict[str, Any]:
        """检测可疑活动"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 检测暴力破解攻击（同一IP多次失败登录）
        brute_force_ips = (
            db.query(
                self.model.ip_address,
                func.count(self.model.id).label("failed_attempts"),
            )
            .filter(
                and_(
                    self.model.action == "login",
                    self.model.status == "failed",
                    self.model.created_at >= start_time,
                    self.model.ip_address.isnot(None),
                )
            )
            .group_by(self.model.ip_address)
            .having(func.count(self.model.id) >= 5)  # 5次以上失败登录
            .order_by(desc("failed_attempts"))
            .all()
        )

        # 检测异常用户活动（用户从多个IP登录）
        suspicious_users = (
            db.query(
                self.model.user_id,
                self.model.username,
                func.count(func.distinct(self.model.ip_address)).label("unique_ips"),
            )
            .filter(
                and_(
                    self.model.action == "login",
                    self.model.status == "success",
                    self.model.created_at >= start_time,
                    self.model.user_id.isnot(None),
                )
            )
            .group_by(self.model.user_id, self.model.username)
            .having(
                func.count(func.distinct(self.model.ip_address)) >= 3  # 3个以上不同IP
            )
            .order_by(desc("unique_ips"))
            .all()
        )

        # 检测深夜活动
        night_activities = (
            db.query(self.model)
            .filter(
                and_(
                    self.model.created_at >= start_time,
                    or_(
                        func.extract("hour", self.model.created_at) < 6,
                        func.extract("hour", self.model.created_at) > 22,
                    ),
                )
            )
            .count()
        )

        return {
            "brute_force_ips": [
                {"ip_address": ip.ip_address, "failed_attempts": ip.failed_attempts}
                for ip in brute_force_ips
            ],
            "suspicious_users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "unique_ips": user.unique_ips,
                }
                for user in suspicious_users
            ],
            "night_activities": night_activities,
        }

    def cleanup_old_logs(self, db: Session, *, days: int = 90) -> int:
        """清理旧的审计日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 删除指定天数之前的日志
        deleted_count = (
            db.query(self.model).filter(self.model.created_at < cutoff_date).delete()
        )

        db.commit()
        return deleted_count


# 创建全局实例
audit_log = CRUDAuditLog(AuditLog)
