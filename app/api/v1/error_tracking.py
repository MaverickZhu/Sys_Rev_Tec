from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.logging import get_structured_logger

"""
错误追踪API端点
"""

from app.core.error_tracking import (
    AlertChannel,
    AlertRule,
    ErrorSeverity,
    error_tracker,
    get_error_stats,
)

logger = get_structured_logger(__name__)

router = APIRouter(prefix="/error-tracking", tags=["error-tracking"])


class ErrorStatsResponse(BaseModel):
    """错误统计响应"""

    total_errors: int
    unique_errors: int
    error_by_type: Dict[str, int]
    error_by_severity: Dict[str, int]
    error_by_path: Dict[str, int]
    top_errors: List[Dict[str, Any]]
    time_range: Dict[str, Any]


class AlertRuleRequest(BaseModel):
    """报警规则请求"""

    name: str = Field(..., description="规则名称")
    error_types: List[str] = Field(default_factory=list, description="匹配的错误类型")
    severity_threshold: ErrorSeverity = Field(..., description="严重程度阈值")
    frequency_threshold: int = Field(..., ge=1, description="频率阈值")
    time_window: int = Field(..., ge=60, description="时间窗口（秒）")
    channels: List[AlertChannel] = Field(..., description="报警渠道")
    enabled: bool = Field(default=True, description="是否启用")
    cooldown: int = Field(default=300, ge=60, description="冷却时间（秒）")


class AlertRuleResponse(BaseModel):
    """报警规则响应"""

    name: str
    error_types: List[str]
    severity_threshold: ErrorSeverity
    frequency_threshold: int
    time_window: int
    channels: List[AlertChannel]
    enabled: bool
    cooldown: int
    last_triggered: Optional[datetime]


@router.get("/stats", response_model=ErrorStatsResponse)
async def get_error_statistics(
    hours: int = Query(default=24, ge=1, le=168, description="统计时间范围（小时）"),
    # admin_user = Depends(get_current_admin_user)  # 需要管理员权限
):
    """获取错误统计信息"""
    try:
        stats = get_error_stats(hours=hours)
        return ErrorStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get error statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve error statistics"
        )


@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    # admin_user = Depends(get_current_admin_user)
):
    """获取所有报警规则"""
    try:
        rules = error_tracker.get_alert_rules()
        return [
            AlertRuleResponse(
                name=rule.name,
                error_types=list(rule.error_types),
                severity_threshold=rule.severity_threshold,
                frequency_threshold=rule.frequency_threshold,
                time_window=rule.time_window,
                channels=rule.channels,
                enabled=rule.enabled,
                cooldown=rule.cooldown,
                last_triggered=rule.last_triggered,
            )
            for rule in rules
        ]
    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert rules")


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_request: AlertRuleRequest,
    # admin_user = Depends(get_current_admin_user)
):
    """创建报警规则"""
    try:
        # 检查规则名称是否已存在
        existing_rules = error_tracker.get_alert_rules()
        if any(rule.name == rule_request.name for rule in existing_rules):
            raise HTTPException(
                status_code=400, detail="Alert rule with this name already exists"
            )

        # 创建新规则
        new_rule = AlertRule(
            name=rule_request.name,
            error_types=set(rule_request.error_types),
            severity_threshold=rule_request.severity_threshold,
            frequency_threshold=rule_request.frequency_threshold,
            time_window=rule_request.time_window,
            channels=rule_request.channels,
            enabled=rule_request.enabled,
            cooldown=rule_request.cooldown,
        )

        error_tracker.add_alert_rule(new_rule)

        logger.info(f"Created alert rule: {rule_request.name}")

        return AlertRuleResponse(
            name=new_rule.name,
            error_types=list(new_rule.error_types),
            severity_threshold=new_rule.severity_threshold,
            frequency_threshold=new_rule.frequency_threshold,
            time_window=new_rule.time_window,
            channels=new_rule.channels,
            enabled=new_rule.enabled,
            cooldown=new_rule.cooldown,
            last_triggered=new_rule.last_triggered,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")


@router.delete("/rules/{rule_name}")
async def delete_alert_rule(
    rule_name: str,
    # admin_user = Depends(get_current_admin_user)
):
    """删除报警规则"""
    try:
        success = error_tracker.remove_alert_rule(rule_name)
        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        logger.info(f"Deleted alert rule: {rule_name}")
        return {"message": "Alert rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")


@router.post("/cleanup")
async def cleanup_old_errors(
    days: int = Query(default=7, ge=1, le=30, description="清理多少天前的错误记录"),
    # admin_user = Depends(get_current_admin_user)
):
    """清理旧的错误记录"""
    try:
        count = error_tracker.cleanup_old_errors(days=days)
        logger.info(f"Cleaned up {count} old error records")
        return {"message": f"Successfully cleaned up {count} error records"}
    except Exception as e:
        logger.error(f"Failed to cleanup old errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old errors")


@router.get("/health")
async def error_tracking_health():
    """错误追踪系统健康检查"""
    try:
        # 检查错误追踪系统状态
        status_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "total_rules": len(error_tracker.get_alert_rules()),
            "active_rules": len(
                [r for r in error_tracker.get_alert_rules() if r.enabled]
            ),
        }
        return status_info
    except Exception as e:
        logger.error(f"Error tracking health check failed: {e}")
        raise HTTPException(
            status_code=500, detail="Error tracking system health check failed"
        )
