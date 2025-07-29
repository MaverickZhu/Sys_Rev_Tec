#!/usr/bin/env python3
"""
系统维护API端点

提供系统维护相关的RESTful API接口:
1. 系统状态监控
2. 数据库清理
3. 日志轮转
4. 系统备份
5. 健康检查
6. 维护计划管理
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import require_permission
from app.core.system_maintenance import system_maintenance
from app.models.user import User

router = APIRouter()


# Pydantic模型
class SystemStatusResponse(BaseModel):
    """系统状态响应模型"""
    timestamp: str
    system: Dict[str, Any]
    database: Dict[str, Any]
    application: Dict[str, Any]
    storage: Dict[str, Any]
    logs: Dict[str, Any]


class DatabaseCleanupRequest(BaseModel):
    """数据库清理请求模型"""
    cleanup_audit_logs: bool = Field(default=True, description="清理审计日志")
    audit_log_retention_days: int = Field(default=90, ge=1, le=365, description="审计日志保留天数")
    cleanup_expired_sessions: bool = Field(default=True, description="清理过期会话")
    cleanup_temp_files: bool = Field(default=True, description="清理临时文件")
    temp_file_retention_days: int = Field(default=7, ge=1, le=30, description="临时文件保留天数")
    vacuum_analyze: bool = Field(default=True, description="执行VACUUM ANALYZE")


class DatabaseCleanupResponse(BaseModel):
    """数据库清理响应模型"""
    status: str
    timestamp: str
    operations: List[Dict[str, Any]]
    error: Optional[str] = None


class LogRotationRequest(BaseModel):
    """日志轮转请求模型"""
    max_size_mb: int = Field(default=100, ge=1, le=1000, description="最大文件大小(MB)")
    max_files: int = Field(default=10, ge=1, le=100, description="最大文件数量")
    compress: bool = Field(default=True, description="是否压缩")


class LogRotationResponse(BaseModel):
    """日志轮转响应模型"""
    status: str
    timestamp: str
    rotated_files: List[Dict[str, Any]]
    cleaned_files: List[str]
    error: Optional[str] = None


class SystemBackupRequest(BaseModel):
    """系统备份请求模型"""
    backup_database: bool = Field(default=True, description="备份数据库")
    backup_config: bool = Field(default=True, description="备份配置文件")
    backup_uploads: bool = Field(default=True, description="备份上传文件")


class SystemBackupResponse(BaseModel):
    """系统备份响应模型"""
    status: str
    backup_name: Optional[str] = None
    backup_path: Optional[str] = None
    timestamp: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    overall_status: str
    timestamp: str
    checks: List[Dict[str, Any]]
    error: Optional[str] = None


class MaintenanceScheduleResponse(BaseModel):
    """维护计划响应模型"""
    status: str
    schedule: Dict[str, Any]
    timestamp: str
    error: Optional[str] = None


@router.get("/status", response_model=SystemStatusResponse)
@require_permission("admin:system:maintenance:read")
async def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统状态"""
    try:
        status_data = await system_maintenance.get_system_status()
        return SystemStatusResponse(**status_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )


@router.post("/database/cleanup", response_model=DatabaseCleanupResponse)
@require_permission("admin:system:maintenance:write")
async def cleanup_database(
    request: DatabaseCleanupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行数据库清理"""
    try:
        cleanup_options = request.dict()
        result = await system_maintenance.cleanup_database(cleanup_options)
        return DatabaseCleanupResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库清理失败: {str(e)}"
        )


@router.post("/logs/rotate", response_model=LogRotationResponse)
@require_permission("admin:system:maintenance:write")
async def rotate_logs(
    request: LogRotationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行日志轮转"""
    try:
        rotation_options = request.dict()
        result = await system_maintenance.rotate_logs(rotation_options)
        return LogRotationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"日志轮转失败: {str(e)}"
        )


@router.post("/backup", response_model=SystemBackupResponse)
@require_permission("admin:system:maintenance:write")
async def backup_system(
    request: SystemBackupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行系统备份"""
    try:
        backup_options = request.dict()
        result = await system_maintenance.backup_system(backup_options)
        return SystemBackupResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"系统备份失败: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
@require_permission("admin:system:maintenance:read")
async def health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行健康检查"""
    try:
        result = await system_maintenance.run_health_check()
        return HealthCheckResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )


@router.get("/schedule", response_model=MaintenanceScheduleResponse)
@require_permission("admin:system:maintenance:read")
async def get_maintenance_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取维护计划"""
    try:
        result = await system_maintenance.get_maintenance_schedule()
        return MaintenanceScheduleResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取维护计划失败: {str(e)}"
        )


@router.get("/database/status")
@require_permission("admin:system:maintenance:read")
async def get_database_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库详细状态"""
    try:
        status_data = await system_maintenance.get_system_status()
        return {
            "status": "success",
            "database": status_data.get("database", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库状态失败: {str(e)}"
        )


@router.get("/storage/status")
@require_permission("admin:system:maintenance:read")
async def get_storage_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取存储状态"""
    try:
        status_data = await system_maintenance.get_system_status()
        return {
            "status": "success",
            "storage": status_data.get("storage", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取存储状态失败: {str(e)}"
        )


@router.get("/logs/status")
@require_permission("admin:system:maintenance:read")
async def get_logs_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取日志状态"""
    try:
        status_data = await system_maintenance.get_system_status()
        return {
            "status": "success",
            "logs": status_data.get("logs", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志状态失败: {str(e)}"
        )


@router.get("/system/resources")
@require_permission("admin:system:maintenance:read")
async def get_system_resources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统资源使用情况"""
    try:
        status_data = await system_maintenance.get_system_status()
        return {
            "status": "success",
            "system": status_data.get("system", {}),
            "application": status_data.get("application", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统资源失败: {str(e)}"
        )


@router.post("/database/vacuum")
@require_permission("admin:system:maintenance:write")
async def vacuum_database(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行数据库VACUUM操作"""
    try:
        cleanup_options = {
            "cleanup_audit_logs": False,
            "cleanup_expired_sessions": False,
            "cleanup_temp_files": False,
            "vacuum_analyze": True
        }
        result = await system_maintenance.cleanup_database(cleanup_options)
        return {
            "status": "success",
            "message": "数据库VACUUM操作完成",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库VACUUM操作失败: {str(e)}"
        )


@router.get("/backups/list")
@require_permission("admin:system:maintenance:read")
async def list_backups(
    limit: int = Query(default=20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出系统备份"""
    try:
        import os
        from pathlib import Path
        
        backup_dir = Path("./backups")
        if not backup_dir.exists():
            return {
                "status": "success",
                "backups": [],
                "total": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        backups = []
        for backup_path in sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if backup_path.is_dir() and backup_path.name.startswith("system_backup_"):
                manifest_file = backup_path / "manifest.json"
                if manifest_file.exists():
                    try:
                        import json
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        # 计算备份大小
                        total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                        
                        backups.append({
                            "name": backup_path.name,
                            "path": str(backup_path),
                            "timestamp": manifest.get("timestamp"),
                            "size": total_size,
                            "size_human": system_maintenance._format_bytes(total_size),
                            "manifest": manifest
                        })
                    except Exception as e:
                        # 如果读取manifest失败，仍然列出备份
                        stat = backup_path.stat()
                        backups.append({
                            "name": backup_path.name,
                            "path": str(backup_path),
                            "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "size": 0,
                            "size_human": "unknown",
                            "error": f"读取manifest失败: {str(e)}"
                        })
                
                if len(backups) >= limit:
                    break
        
        return {
            "status": "success",
            "backups": backups,
            "total": len(backups),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出备份失败: {str(e)}"
        )


@router.delete("/backups/{backup_name}")
@require_permission("admin:system:maintenance:write")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除指定备份"""
    try:
        import shutil
        from pathlib import Path
        
        backup_dir = Path("./backups")
        backup_path = backup_dir / backup_name
        
        if not backup_path.exists() or not backup_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"备份 {backup_name} 不存在"
            )
        
        # 安全检查：确保是备份目录
        if not backup_name.startswith("system_backup_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的备份名称"
            )
        
        # 删除备份目录
        shutil.rmtree(backup_path)
        
        return {
            "status": "success",
            "message": f"备份 {backup_name} 已删除",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除备份失败: {str(e)}"
        )


@router.get("/metrics")
@require_permission("admin:system:maintenance:read")
async def get_maintenance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取维护指标"""
    try:
        # 获取系统状态
        status_data = await system_maintenance.get_system_status()
        
        # 获取健康检查结果
        health_data = await system_maintenance.run_health_check()
        
        # 计算关键指标
        metrics = {
            "system_health": health_data.get("overall_status", "unknown"),
            "cpu_usage": status_data.get("system", {}).get("cpu_usage", 0),
            "memory_usage": status_data.get("system", {}).get("memory", {}).get("percent", 0),
            "disk_usage": status_data.get("system", {}).get("disk", {}).get("percent", 0),
            "database_size": status_data.get("database", {}).get("size_bytes", 0),
            "active_connections": status_data.get("database", {}).get("active_connections", 0),
            "log_files_count": status_data.get("logs", {}).get("total_files", 0),
            "log_files_size": status_data.get("logs", {}).get("total_size", 0),
            "uptime": status_data.get("system", {}).get("uptime", "unknown")
        }
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取维护指标失败: {str(e)}"
        )