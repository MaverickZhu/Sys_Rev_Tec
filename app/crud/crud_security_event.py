"""安全事件CRUD操作

提供安全事件的创建、查询、更新、统计等功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from app.crud.base import CRUDBase
from app.models.security_event import SecurityEvent, SecurityEventType, SecurityEventLevel
from app.schemas.security_monitor import SecurityEventCreate, SecurityEventUpdate


class CRUDSecurityEvent(CRUDBase[SecurityEvent, SecurityEventCreate, SecurityEventUpdate]):
    """安全事件CRUD操作类"""
    
    def create_event(
        self,
        db: Session,
        *,
        event_type: SecurityEventType,
        level: SecurityEventLevel,
        title: str,
        description: Optional[str] = None,
        source_ip: Optional[str] = None,
        source_port: Optional[int] = None,
        target_ip: Optional[str] = None,
        target_port: Optional[int] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_url: Optional[str] = None,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[str] = None,
        detection_method: Optional[str] = None,
        detection_rule: Optional[str] = None,
        confidence_score: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        evidence: Optional[str] = None,
        impact_assessment: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> SecurityEvent:
        """创建安全事件"""
        # 将字典转换为JSON字符串
        import json
        
        details_json = None
        if details:
            details_json = json.dumps(details, ensure_ascii=False)
        
        headers_json = None
        if request_headers:
            headers_json = json.dumps(request_headers, ensure_ascii=False)
        
        db_obj = SecurityEvent(
            event_type=event_type,
            level=level,
            title=title,
            description=description,
            source_ip=source_ip,
            source_port=source_port,
            target_ip=target_ip,
            target_port=target_port,
            user_id=user_id,
            username=username,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            request_headers=headers_json,
            request_body=request_body,
            detection_method=detection_method,
            detection_rule=detection_rule,
            confidence_score=confidence_score,
            details=details_json,
            evidence=evidence,
            impact_assessment=impact_assessment,
            session_id=session_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def search(
        self,
        db: Session,
        *,
        event_type: Optional[SecurityEventType] = None,
        level: Optional[SecurityEventLevel] = None,
        source_ip: Optional[str] = None,
        target_ip: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        detection_method: Optional[str] = None,
        correlation_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[SecurityEvent]:
        """搜索安全事件"""
        query = db.query(self.model)
        
        # 添加过滤条件
        if event_type is not None:
            query = query.filter(self.model.event_type == event_type)
        
        if level is not None:
            query = query.filter(self.model.level == level)
        
        if source_ip:
            query = query.filter(self.model.source_ip == source_ip)
        
        if target_ip:
            query = query.filter(self.model.target_ip == target_ip)
        
        if user_id is not None:
            query = query.filter(self.model.user_id == user_id)
        
        if username:
            query = query.filter(self.model.username.ilike(f"%{username}%"))
        
        if is_resolved is not None:
            query = query.filter(self.model.is_resolved == is_resolved)
        
        if detection_method:
            query = query.filter(self.model.detection_method == detection_method)
        
        if correlation_id:
            query = query.filter(self.model.correlation_id == correlation_id)
        
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
    
    def resolve_event(
        self,
        db: Session,
        *,
        event_id: int,
        resolved_by: int,
        resolution_note: Optional[str] = None
    ) -> Optional[SecurityEvent]:
        """解决安全事件"""
        event = db.query(self.model).filter(self.model.id == event_id).first()
        if not event:
            return None
        
        event.is_resolved = True
        event.resolved_by = resolved_by
        event.resolved_at = datetime.utcnow()
        event.resolution_note = resolution_note
        event.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(event)
        return event
    
    def get_statistics(
        self,
        db: Session,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取安全事件统计信息"""
        query = db.query(self.model)
        
        # 时间范围过滤
        if start_time:
            query = query.filter(self.model.created_at >= start_time)
        
        if end_time:
            query = query.filter(self.model.created_at <= end_time)
        
        # 总数统计
        total_events = query.count()
        
        # 按级别统计
        level_stats = query.with_entities(
            self.model.level,
            func.count(self.model.id).label('count')
        ).group_by(self.model.level).all()
        
        # 按类型统计
        type_stats = query.with_entities(
            self.model.event_type,
            func.count(self.model.id).label('count')
        ).group_by(self.model.event_type).order_by(desc('count')).limit(10).all()
        
        # 解决状态统计
        resolved_events = query.filter(self.model.is_resolved == True).count()
        pending_events = query.filter(self.model.is_resolved == False).count()
        
        # 严重事件统计
        critical_events = query.filter(
            self.model.level == SecurityEventLevel.CRITICAL
        ).count()
        
        high_events = query.filter(
            self.model.level == SecurityEventLevel.HIGH
        ).count()
        
        # 按源IP统计
        source_ip_stats = query.filter(self.model.source_ip.isnot(None)).with_entities(
            self.model.source_ip,
            func.count(self.model.id).label('count')
        ).group_by(self.model.source_ip).order_by(desc('count')).limit(10).all()
        
        # 按用户统计
        user_stats = query.filter(self.model.user_id.isnot(None)).with_entities(
            self.model.user_id,
            self.model.username,
            func.count(self.model.id).label('count')
        ).group_by(self.model.user_id, self.model.username).order_by(desc('count')).limit(10).all()
        
        # 平均解决时间
        resolved_query = query.filter(
            and_(
                self.model.is_resolved == True,
                self.model.resolved_at.isnot(None)
            )
        )
        
        avg_resolution_time = 0
        if resolved_events > 0:
            resolution_times = []
            for event in resolved_query.all():
                if event.resolved_at and event.created_at:
                    duration = (event.resolved_at - event.created_at).total_seconds() / 3600  # 小时
                    resolution_times.append(duration)
            
            if resolution_times:
                avg_resolution_time = sum(resolution_times) / len(resolution_times)
        
        return {
            "total_events": total_events,
            "resolved_events": resolved_events,
            "pending_events": pending_events,
            "critical_events": critical_events,
            "high_events": high_events,
            "avg_resolution_time": round(avg_resolution_time, 2),
            "level_distribution": {stat.level.value: stat.count for stat in level_stats},
            "type_distribution": {stat.event_type.value: stat.count for stat in type_stats},
            "top_source_ips": [
                {"ip_address": stat.source_ip, "count": stat.count}
                for stat in source_ip_stats
            ],
            "top_users": [
                {"user_id": stat.user_id, "username": stat.username, "count": stat.count}
                for stat in user_stats
            ]
        }
    
    def get_critical_events(
        self,
        db: Session,
        *,
        hours: int = 24,
        limit: int = 50
    ) -> List[SecurityEvent]:
        """获取严重安全事件"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        return db.query(self.model).filter(
            and_(
                self.model.level.in_([
                    SecurityEventLevel.CRITICAL,
                    SecurityEventLevel.HIGH
                ]),
                self.model.created_at >= start_time
            )
        ).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def get_unresolved_events(
        self,
        db: Session,
        *,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """获取未解决的安全事件"""
        return db.query(self.model).filter(
            self.model.is_resolved == False
        ).order_by(
            desc(self.model.level),
            desc(self.model.created_at)
        ).limit(limit).all()
    
    def get_events_by_correlation(
        self,
        db: Session,
        *,
        correlation_id: str
    ) -> List[SecurityEvent]:
        """根据关联ID获取相关事件"""
        return db.query(self.model).filter(
            self.model.correlation_id == correlation_id
        ).order_by(self.model.created_at).all()
    
    def detect_attack_patterns(
        self,
        db: Session,
        *,
        hours: int = 24
    ) -> Dict[str, Any]:
        """检测攻击模式"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 检测暴力破解攻击
        brute_force_attacks = db.query(
            self.model.source_ip,
            func.count(self.model.id).label('attack_count')
        ).filter(
            and_(
                self.model.event_type.in_([
                    SecurityEventType.LOGIN_FAILED,
                    SecurityEventType.BRUTE_FORCE
                ]),
                self.model.created_at >= start_time,
                self.model.source_ip.isnot(None)
            )
        ).group_by(self.model.source_ip).having(
            func.count(self.model.id) >= 5
        ).order_by(desc('attack_count')).all()
        
        # 检测DDoS攻击
        ddos_attacks = db.query(self.model).filter(
            and_(
                self.model.event_type == SecurityEventType.DDOS_ATTACK,
                self.model.created_at >= start_time
            )
        ).count()
        
        # 检测注入攻击
        injection_attacks = db.query(self.model).filter(
            and_(
                self.model.event_type.in_([
                    SecurityEventType.SQL_INJECTION,
                    SecurityEventType.XSS_ATTACK
                ]),
                self.model.created_at >= start_time
            )
        ).count()
        
        # 检测内部威胁
        insider_threats = db.query(self.model).filter(
            and_(
                self.model.event_type == SecurityEventType.INSIDER_THREAT,
                self.model.created_at >= start_time
            )
        ).count()
        
        # 检测账户接管
        account_takeovers = db.query(self.model).filter(
            and_(
                self.model.event_type == SecurityEventType.ACCOUNT_TAKEOVER,
                self.model.created_at >= start_time
            )
        ).count()
        
        return {
            "brute_force_attacks": [
                {"source_ip": attack.source_ip, "attack_count": attack.attack_count}
                for attack in brute_force_attacks
            ],
            "ddos_attacks": ddos_attacks,
            "injection_attacks": injection_attacks,
            "insider_threats": insider_threats,
            "account_takeovers": account_takeovers
        }
    
    def get_sla_breached_events(
        self,
        db: Session
    ) -> List[SecurityEvent]:
        """获取违反SLA的事件"""
        events = db.query(self.model).filter(
            self.model.is_resolved == False
        ).all()
        
        breached_events = []
        for event in events:
            if event.is_sla_breached():
                breached_events.append(event)
        
        return breached_events
    
    def create_correlation_group(
        self,
        db: Session,
        *,
        event_ids: List[int],
        correlation_id: str
    ) -> int:
        """创建事件关联组"""
        updated_count = db.query(self.model).filter(
            self.model.id.in_(event_ids)
        ).update(
            {"correlation_id": correlation_id, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        db.commit()
        return updated_count
    
    def cleanup_old_events(
        self,
        db: Session,
        *,
        days: int = 365
    ) -> int:
        """清理旧的安全事件"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 只删除已解决的旧事件
        deleted_count = db.query(self.model).filter(
            and_(
                self.model.created_at < cutoff_date,
                self.model.is_resolved == True
            )
        ).delete()
        
        db.commit()
        return deleted_count


# 创建全局实例
security_event = CRUDSecurityEvent(SecurityEvent)