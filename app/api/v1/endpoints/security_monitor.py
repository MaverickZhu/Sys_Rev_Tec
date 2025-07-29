"""安全监控仪表板API

提供安全监控、审计日志、异常检测等功能
"""

import logging
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.api.deps import get_db, get_current_user
from app.core.permissions import require_permission, Permissions
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.security_event import SecurityEvent, SecurityEventType, SecurityEventLevel
from app.crud.crud_audit_log import audit_log as audit_log_crud
from app.crud.crud_security_event import security_event as security_event_crud
from app.schemas.security_monitor import (
    SecurityDashboardData, SecurityMetrics, SecurityAlert,
    AuditLogSearch, SecurityEventSearch,
    SecurityTrend, UserActivitySummary, SystemHealthStatus,
    ThreatDetectionResult, SecurityRecommendation
)
from app.core.security.threat_detector import ThreatDetector
from app.core.security.security_analyzer import SecurityAnalyzer
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=SecurityDashboardData)
@require_permission(Permissions.SYSTEM_MONITOR)
async def get_security_dashboard(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    time_range: int = Query(24, description="时间范围（小时）")
):
    """获取安全监控仪表板数据"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range)
        
        # 获取安全指标
        metrics = await _get_security_metrics(db, start_time, end_time)
        
        # 获取安全警报
        alerts = await _get_security_alerts(db, start_time, end_time)
        
        # 获取安全趋势
        trends = await _get_security_trends(db, start_time, end_time)
        
        # 获取用户活动摘要
        user_activities = await _get_user_activity_summary(db, start_time, end_time)
        
        # 获取系统健康状态
        system_health = await _get_system_health_status(db)
        
        # 获取威胁检测结果
        threat_detection = await _get_threat_detection_results(db, start_time, end_time)
        
        # 获取安全建议
        recommendations = await _get_security_recommendations(db)
        
        return SecurityDashboardData(
            metrics=metrics,
            alerts=alerts,
            trends=trends,
            user_activities=user_activities,
            system_health=system_health,
            threat_detection=threat_detection,
            recommendations=recommendations,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"获取安全监控仪表板数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全监控仪表板数据失败"
        )


@router.get("/audit-logs", response_model=Dict[str, Any])
@require_permission(Permissions.AUDIT_READ)
async def get_audit_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: AuditLogSearch = Depends()
):
    """获取审计日志（带分页）"""
    try:
        # 获取总数
        total = audit_log_crud.count(
            db,
            user_id=search.user_id,
            username=search.username,
            action=search.action,
            resource_type=search.resource_type,
            resource_id=search.resource_id,
            start_time=search.start_time,
            end_time=search.end_time,
            ip_address=search.ip_address,
            status=search.status
        )
        
        # 获取日志列表
        logs = audit_log_crud.search(
            db,
            user_id=search.user_id,
            username=search.username,
            action=search.action,
            resource_type=search.resource_type,
            resource_id=search.resource_id,
            start_time=search.start_time,
            end_time=search.end_time,
            ip_address=search.ip_address,
            status=search.status,
            skip=search.skip,
            limit=search.limit
        )
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "request_method": log.request_method,
                    "request_url": log.request_url,
                    "created_at": log.created_at,
                    "status": log.status,
                    "status_code": log.status_code,
                    "error_message": log.error_message,
                    "duration_ms": log.duration_ms,
                    "session_id": log.session_id,
                    "trace_id": log.trace_id
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"获取审计日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取审计日志失败"
        )


@router.get("/security-events", response_model=List[Dict[str, Any]])
@require_permission(Permissions.SYSTEM_MONITOR)
async def get_security_events(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: SecurityEventSearch = Depends()
):
    """获取安全事件"""
    try:
        events = security_event_crud.search(
            db,
            event_type=search.event_type,
            level=search.level,
            source_ip=search.source_ip,
            user_id=search.user_id,
            start_time=search.start_time,
            end_time=search.end_time,
            is_resolved=search.is_resolved,
            skip=search.skip,
            limit=search.limit
        )
        
        return [
            {
                "id": event.id,
                "event_type": event.event_type.value,
                "level": event.level.value,
                "title": event.title,
                "description": event.description,
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "username": event.user.username if event.user else None,
                "details": event.details,
                "is_resolved": event.is_resolved,
                "resolved_by": event.resolved_by,
                "resolved_at": event.resolved_at,
                "created_at": event.created_at
            }
            for event in events
        ]
    except Exception as e:
        logger.error(f"获取安全事件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全事件失败"
        )


@router.post("/security-events/{event_id}/resolve")
@require_permission(Permissions.SYSTEM_MONITOR)
async def resolve_security_event(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    event_id: int,
    resolution_note: str = Query(..., description="解决说明")
):
    """解决安全事件"""
    try:
        event = security_event_crud.get(db, id=event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="安全事件不存在"
            )
        
        if event.is_resolved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="安全事件已经解决"
            )
        
        # 解决事件
        security_event_crud.resolve_event(
            db,
            event_id=event_id,
            resolved_by=current_user.id,
            resolution_note=resolution_note
        )
        
        logger.info(f"用户 {current_user.username} 解决了安全事件 {event_id}")
        return {"message": "安全事件已解决"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决安全事件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解决安全事件失败"
        )


@router.post("/threat-detection/scan")
@require_permission(Permissions.SYSTEM_MONITOR)
async def run_threat_detection(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    scan_type: str = Query("full", description="扫描类型: quick, full, custom")
):
    """运行威胁检测扫描"""
    try:
        # 启动后台威胁检测任务
        background_tasks.add_task(
            _run_threat_detection_task,
            db,
            current_user.id,
            scan_type
        )
        
        logger.info(f"用户 {current_user.username} 启动了威胁检测扫描: {scan_type}")
        return {"message": "威胁检测扫描已启动", "scan_type": scan_type}
    except Exception as e:
        logger.error(f"启动威胁检测扫描失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动威胁检测扫描失败"
        )


@router.get("/audit-logs/export")
@require_permission(Permissions.AUDIT_READ)
async def export_audit_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: AuditLogSearch = Depends(),
    format: str = Query("csv", description="导出格式: csv, excel")
):
    """导出审计日志"""
    try:
        # 获取所有符合条件的日志（不分页）
        logs = audit_log_crud.search(
            db,
            user_id=search.user_id,
            username=search.username,
            action=search.action,
            resource_type=search.resource_type,
            start_time=search.start_time,
            end_time=search.end_time,
            ip_address=search.ip_address,
            status=search.status,
            skip=0,
            limit=10000  # 限制最大导出数量
        )
        
        if format.lower() == "csv":
            # 生成CSV内容
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                "ID", "用户ID", "用户名", "操作类型", "资源类型", "资源ID",
                "描述", "IP地址", "用户代理", "请求方法", "请求URL",
                "状态", "状态码", "错误信息", "耗时(ms)", "会话ID", "跟踪ID", "创建时间"
            ])
            
            # 写入数据
            for log in logs:
                writer.writerow([
                    log.id,
                    log.user_id,
                    log.user.username if log.user else "",
                    log.action,
                    log.resource_type or "",
                    log.resource_id or "",
                    log.description or "",
                    log.ip_address or "",
                    log.user_agent or "",
                    log.request_method or "",
                    log.request_url or "",
                    log.status,
                    log.status_code or "",
                    log.error_message or "",
                    log.duration_ms or "",
                    log.session_id or "",
                    log.trace_id or "",
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ])
            
            content = output.getvalue()
            output.close()
            
            # 记录导出操作
            audit_log_crud.create_log(
                db,
                user_id=current_user.id,
                action="export_audit_logs",
                resource_type="audit_log",
                description=f"导出审计日志，格式: {format}, 数量: {len(logs)}",
                ip_address=getattr(current_user, 'ip_address', None)
            )
            
            return Response(
                content=content.encode('utf-8-sig'),  # 使用UTF-8 BOM以支持中文
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的导出格式"
            )
            
    except Exception as e:
        logger.error(f"导出审计日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出审计日志失败"
        )


@router.get("/audit-logs/statistics")
@require_permission(Permissions.AUDIT_READ)
async def get_audit_log_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间")
):
    """获取审计日志统计信息"""
    try:
        stats = audit_log_crud.get_statistics(
            db,
            start_time=start_time,
            end_time=end_time
        )
        return stats
    except Exception as e:
        logger.error(f"获取审计日志统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取审计日志统计失败"
        )


@router.get("/user-activities")
@require_permission(Permissions.AUDIT_READ)
async def get_user_activities(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: Optional[int] = Query(None, description="用户ID"),
    hours: int = Query(24, description="时间范围（小时）")
):
    """获取用户活动统计"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query = db.query(AuditLog).filter(
            AuditLog.created_at.between(start_time, end_time)
        )
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        # 按用户分组统计
        user_stats = query.with_entities(
            AuditLog.user_id,
            func.count(AuditLog.id).label('total_actions'),
            func.count(func.distinct(AuditLog.ip_address)).label('unique_ips'),
            func.max(AuditLog.created_at).label('last_activity')
        ).group_by(AuditLog.user_id).all()
        
        activities = []
        for stat in user_stats:
            user = db.query(User).filter(User.id == stat.user_id).first()
            activities.append({
                "user_id": stat.user_id,
                "username": user.username if user else "未知用户",
                "total_actions": stat.total_actions,
                "unique_ips": stat.unique_ips,
                "last_activity": stat.last_activity
            })
        
        return activities
    except Exception as e:
        logger.error(f"获取用户活动统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户活动统计失败"
        )


@router.get("/security-trends")
@require_permission(Permissions.SYSTEM_MONITOR)
async def get_security_trends(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, description="天数")
):
    """获取安全趋势数据"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        trends = await _get_security_trends(db, start_time, end_time)
        return trends
    except Exception as e:
        logger.error(f"获取安全趋势数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全趋势数据失败"
        )


# 辅助函数
async def _get_security_metrics(db: Session, start_time: datetime, end_time: datetime) -> SecurityMetrics:
    """获取安全指标"""
    # 统计审计日志
    total_audit_logs = db.query(AuditLog).filter(
        AuditLog.created_at.between(start_time, end_time)
    ).count()
    
    failed_logins = db.query(AuditLog).filter(
        and_(
            AuditLog.created_at.between(start_time, end_time),
            AuditLog.action == "login",
            AuditLog.status == "failed"
        )
    ).count()
    
    # 统计安全事件
    security_events = db.query(SecurityEvent).filter(
        SecurityEvent.created_at.between(start_time, end_time)
    ).count()
    
    critical_events = db.query(SecurityEvent).filter(
        and_(
            SecurityEvent.created_at.between(start_time, end_time),
            SecurityEvent.level == SecurityEventLevel.CRITICAL
        )
    ).count()
    
    # 统计活跃用户
    active_users = db.query(AuditLog.user_id).filter(
        AuditLog.created_at.between(start_time, end_time)
    ).distinct().count()
    
    # 统计唯一IP
    unique_ips = db.query(AuditLog.ip_address).filter(
        AuditLog.created_at.between(start_time, end_time)
    ).distinct().count()
    
    return SecurityMetrics(
        total_audit_logs=total_audit_logs,
        failed_logins=failed_logins,
        security_events=security_events,
        critical_events=critical_events,
        active_users=active_users,
        unique_ips=unique_ips,
        threat_level="medium",  # 可以根据实际情况计算
        system_health_score=85  # 可以根据实际情况计算
    )


async def _get_security_alerts(db: Session, start_time: datetime, end_time: datetime) -> List[SecurityAlert]:
    """获取安全警报"""
    events = db.query(SecurityEvent).filter(
        and_(
            SecurityEvent.created_at.between(start_time, end_time),
            SecurityEvent.level.in_([SecurityEventLevel.HIGH, SecurityEventLevel.CRITICAL]),
            SecurityEvent.is_resolved == False
        )
    ).order_by(desc(SecurityEvent.created_at)).limit(10).all()
    
    alerts = []
    for event in events:
        alerts.append(SecurityAlert(
            id=event.id,
            type=event.event_type.value,
            level=event.level.value,
            title=event.title,
            description=event.description,
            source_ip=event.source_ip,
            user_id=event.user_id,
            created_at=event.created_at,
            is_resolved=event.is_resolved
        ))
    
    return alerts


@router.post("/audit-logs/search")
@require_permission(Permissions.AUDIT_READ)
async def search_audit_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search_params: Dict[str, Any]
):
    """搜索审计日志"""
    try:
        # 提取搜索参数
        user_id = search_params.get('user_id')
        username = search_params.get('username')
        action = search_params.get('action')
        resource_type = search_params.get('resource_type')
        resource_id = search_params.get('resource_id')
        ip_address = search_params.get('ip_address')
        status = search_params.get('status')
        start_time = search_params.get('start_time')
        end_time = search_params.get('end_time')
        skip = search_params.get('skip', 0)
        limit = search_params.get('limit', 20)
        
        # 获取总数
        total = audit_log_crud.count(
            db,
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status=status,
            start_time=start_time,
            end_time=end_time
        )
        
        # 获取数据
        logs = audit_log_crud.search(
            db,
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status=status,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "request_method": log.request_method,
                    "request_url": log.request_url,
                    "status": log.status,
                    "error_message": log.error_message,
                    "session_id": log.session_id,
                    "trace_id": log.trace_id,
                    "created_at": log.created_at,
                    "additional_data": log.additional_data
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"搜索审计日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索审计日志失败"
        )


@router.get("/audit-logs/user/{user_id}/history")
@require_permission(Permissions.AUDIT_READ)
async def get_user_operation_history(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int,
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(20, description="返回记录数")
):
    """获取用户操作历史"""
    try:
        # 获取总数
        total = audit_log_crud.count(db, user_id=user_id)
        
        # 获取数据
        logs = audit_log_crud.search(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"获取用户操作历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户操作历史失败"
        )


@router.get("/audit-logs/resource/{resource_type}/{resource_id}")
@require_permission(Permissions.AUDIT_READ)
async def get_resource_access_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resource_type: str,
    resource_id: str,
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(20, description="返回记录数")
):
    """获取资源访问日志"""
    try:
        # 获取总数
        total = audit_log_crud.count(
            db,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        # 获取数据
        logs = audit_log_crud.search(
            db,
            resource_type=resource_type,
            resource_id=resource_id,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"获取资源访问日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源访问日志失败"
        )


@router.get("/audit-logs/failed-operations")
@require_permission(Permissions.AUDIT_READ)
async def get_failed_operations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(20, description="返回记录数"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间")
):
    """获取失败操作日志"""
    try:
        # 获取总数
        total = audit_log_crud.count(
            db,
            status="FAILED",
            start_time=start_time,
            end_time=end_time
        )
        
        # 获取数据
        logs = audit_log_crud.search(
            db,
            status="FAILED",
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit
        )
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "error_message": log.error_message,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"获取失败操作日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取失败操作日志失败"
        )


@router.get("/audit-logs/high-risk-operations")
@require_permission(Permissions.AUDIT_READ)
async def get_high_risk_operations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(20, description="返回记录数"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间")
):
    """获取高风险操作日志"""
    try:
        # 定义高风险操作
        high_risk_actions = ['DELETE', 'PERMISSION_CHANGE', 'ROLE_CHANGE', 'USER_DELETE']
        
        # 构建查询
        query = db.query(AuditLog).filter(
            AuditLog.action.in_(high_risk_actions)
        )
        
        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)
        if end_time:
            query = query.filter(AuditLog.created_at <= end_time)
        
        # 获取总数
        total = query.count()
        
        # 获取数据
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"获取高风险操作日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取高风险操作日志失败"
        )


async def _get_security_trends(db: Session, start_time: datetime, end_time: datetime) -> List[SecurityTrend]:
    """获取安全趋势"""
    # 按天统计
    trends = []
    current_time = start_time
    
    while current_time < end_time:
        next_time = current_time + timedelta(days=1)
        
        # 统计当天的安全事件
        events_count = db.query(SecurityEvent).filter(
            SecurityEvent.created_at.between(current_time, next_time)
        ).count()
        
        # 统计当天的失败登录
        failed_logins = db.query(AuditLog).filter(
            and_(
                AuditLog.created_at.between(current_time, next_time),
                AuditLog.action == "login",
                AuditLog.status == "failed"
            )
        ).count()
        
        trends.append(SecurityTrend(
            date=current_time.date(),
            security_events=events_count,
            failed_logins=failed_logins,
            threat_score=min(100, (events_count * 10 + failed_logins * 5))  # 简单的威胁评分
        ))
        
        current_time = next_time
    
    return trends


async def _get_user_activity_summary(db: Session, start_time: datetime, end_time: datetime) -> List[UserActivitySummary]:
    """获取用户活动摘要"""
    user_stats = db.query(
        AuditLog.user_id,
        func.count(AuditLog.id).label('total_actions'),
        func.count(func.distinct(AuditLog.ip_address)).label('unique_ips'),
        func.max(AuditLog.created_at).label('last_activity')
    ).filter(
        AuditLog.created_at.between(start_time, end_time)
    ).group_by(AuditLog.user_id).order_by(desc('total_actions')).limit(10).all()
    
    summaries = []
    for stat in user_stats:
        user = db.query(User).filter(User.id == stat.user_id).first()
        summaries.append(UserActivitySummary(
            user_id=stat.user_id,
            username=user.username if user else "未知用户",
            total_actions=stat.total_actions,
            unique_ips=stat.unique_ips,
            last_activity=stat.last_activity,
            risk_score=min(100, stat.unique_ips * 20)  # 简单的风险评分
        ))
    
    return summaries


async def _get_system_health_status(db: Session) -> SystemHealthStatus:
    """获取系统健康状态"""
    # 这里可以添加更多的系统健康检查
    return SystemHealthStatus(
        cpu_usage=45.2,
        memory_usage=67.8,
        disk_usage=34.5,
        network_status="healthy",
        database_status="healthy",
        service_status="healthy",
        last_backup=datetime.utcnow() - timedelta(hours=6),
        uptime_hours=168
    )


async def _get_threat_detection_results(db: Session, start_time: datetime, end_time: datetime) -> ThreatDetectionResult:
    """获取威胁检测结果"""
    # 这里可以集成实际的威胁检测逻辑
    return ThreatDetectionResult(
        scan_status="completed",
        threats_detected=3,
        high_risk_threats=1,
        medium_risk_threats=2,
        low_risk_threats=0,
        last_scan=datetime.utcnow() - timedelta(hours=2),
        next_scan=datetime.utcnow() + timedelta(hours=22)
    )


async def _get_security_recommendations(db: Session) -> List[SecurityRecommendation]:
    """获取安全建议"""
    recommendations = [
        SecurityRecommendation(
            id=1,
            type="password_policy",
            priority="high",
            title="加强密码策略",
            description="建议启用更严格的密码复杂度要求",
            action_required=True
        ),
        SecurityRecommendation(
            id=2,
            type="access_control",
            priority="medium",
            title="审查用户权限",
            description="定期审查和清理不必要的用户权限",
            action_required=False
        )
    ]
    
    return recommendations


async def _run_threat_detection_task(db: Session, user_id: int, scan_type: str):
    """运行威胁检测任务（后台任务）"""
    try:
        detector = ThreatDetector(db)
        results = await detector.run_scan(scan_type)
        
        # 记录扫描结果
        logger.info(f"威胁检测扫描完成: {scan_type}, 发现 {len(results)} 个威胁")
        
        # 可以在这里保存扫描结果到数据库
        
    except Exception as e:
        logger.error(f"威胁检测任务失败: {e}")