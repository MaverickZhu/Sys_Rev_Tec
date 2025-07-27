from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
import psutil
import os
from typing import Dict, Any

from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """
    基础健康检查端点
    返回应用程序的基本状态信息
    """
    try:
        # 获取进程信息
        process = psutil.Process(os.getpid())
        
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage('/')
        except:
            disk = psutil.disk_usage('C:\\')
        
        # 进程指标
        process_memory = process.memory_info()
        
        health_data = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "uptime_seconds": int(time.time() - process.create_time()),
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "environment": settings.ENVIRONMENT,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // 1024 // 1024,
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free // 1024 // 1024 // 1024
            }
        }
        
        return {
            "code": 200,
            "message": "API is running normally",
            "data": health_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "code": 503,
                "message": "Health check failed",
                "error": {
                    "message": f"Health check failed: {str(e)}"
                }
            }
        )


@router.get("/ready")
async def readiness_check(db: Session = Depends(deps.get_db)):
    """
    就绪检查端点
    检查应用程序是否准备好接收流量
    包括数据库连接、外部服务等关键依赖项的检查
    """
    checks = {}
    overall_status = "ready"
    
    try:
        # 数据库连接检查
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            checks["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            overall_status = "not_ready"
        
        # 检查关键目录是否存在
        upload_dir = getattr(settings, 'UPLOAD_DIR', 'uploads')
        if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
            checks["upload_directory"] = {
                "status": "healthy",
                "message": "Upload directory is accessible"
            }
        else:
            checks["upload_directory"] = {
                "status": "unhealthy",
                "message": "Upload directory is not accessible"
            }
            overall_status = "not_ready"
        
        # 检查日志目录
        log_dir = "logs"
        if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
            checks["log_directory"] = {
                "status": "healthy",
                "message": "Log directory is accessible"
            }
        else:
            checks["log_directory"] = {
                "status": "warning",
                "message": "Log directory is not accessible"
            }
        
        # 内存使用检查
        memory = psutil.virtual_memory()
        if memory.percent < 90:
            checks["memory"] = {
                "status": "healthy",
                "message": f"Memory usage: {memory.percent}%"
            }
        else:
            checks["memory"] = {
                "status": "warning",
                "message": f"High memory usage: {memory.percent}%"
            }
        
        # 磁盘空间检查
        disk = psutil.disk_usage('/')
        if disk.percent < 90:
            checks["disk_space"] = {
                "status": "healthy",
                "message": f"Disk usage: {disk.percent}%"
            }
        else:
            checks["disk_space"] = {
                "status": "warning",
                "message": f"High disk usage: {disk.percent}%"
            }
        
        readiness_data = {
            "status": overall_status,
            "timestamp": int(time.time()),
            "checks": checks
        }
        
        # 如果不是ready状态，返回503
        if overall_status != "ready":
            raise HTTPException(
                status_code=503,
                detail="Application is not ready"
            )
        
        return {
            "code": 200,
            "message": "Application is ready",
            "data": readiness_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/metrics")
async def metrics_endpoint():
    """
    指标端点
    返回应用程序的详细指标信息，用于监控系统
    """
    try:
        # 获取进程信息
        process = psutil.Process(os.getpid())
        
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage('/')
        except:
            disk = psutil.disk_usage('C:\\')
        
        # 进程指标
        process_memory = process.memory_info()
        
        metrics_data = {
            "timestamp": int(time.time()),
            "system": {
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "memory_total_mb": memory.total // 1024 // 1024,
                "memory_available_mb": memory.available // 1024 // 1024,
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total // 1024 // 1024 // 1024,
                "disk_free_gb": disk.free // 1024 // 1024 // 1024,
                "disk_percent": disk.percent
            },
            "process": {
                "pid": process.pid,
                "memory_rss_mb": process_memory.rss // 1024 // 1024,
                "memory_vms_mb": process_memory.vms // 1024 // 1024,
                "cpu_percent": process.cpu_percent(interval=None),
                "num_threads": process.num_threads(),
                "create_time": process.create_time(),
                "uptime_seconds": int(time.time() - process.create_time())
            },
            "application": {
                "version": getattr(settings, 'VERSION', '1.0.0'),
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            }
        }
        
        return {
            "code": 200,
            "message": "Metrics retrieved successfully",
            "data": metrics_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )