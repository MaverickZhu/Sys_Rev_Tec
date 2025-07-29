#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限配置管理API接口

提供权限系统配置管理相关的API端点
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_active_user
from app.core.permission_config_manager import (
    get_permission_config_manager,
    get_permission_config,
    ConfigLevel,
    PermissionConfig
)
from app.core.permissions import require_permission
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 请求/响应模型 ====================

class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    level: str = Field(..., description="配置级别")
    updates: Dict[str, Any] = Field(..., description="更新的配置项")


class ConfigExportRequest(BaseModel):
    """配置导出请求"""
    level: Optional[str] = Field(None, description="配置级别，为空则导出合并配置")
    include_metadata: bool = Field(True, description="是否包含元数据")


class ConfigImportRequest(BaseModel):
    """配置导入请求"""
    level: str = Field(..., description="配置级别")
    config_data: Dict[str, Any] = Field(..., description="配置数据")
    validate_only: bool = Field(False, description="仅验证不保存")


# ==================== 配置查询API ====================

@router.get(
    "/config",
    summary="获取权限配置",
    description="获取当前的权限系统配置"
)
@require_permission("admin:system:config:read")
def get_permission_system_config(
    level: Optional[str] = Query(None, description="配置级别"),
    current_user: User = Depends(get_current_active_user)
):
    """获取权限配置
    
    Args:
        level: 配置级别
        current_user: 当前用户
        
    Returns:
        Dict: 配置信息
    """
    try:
        config_manager = get_permission_config_manager()
        
        if level:
            try:
                config_level = ConfigLevel(level)
                config = config_manager.get_config_by_level(config_level)
                config_data = config_manager.export_config(config_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的配置级别: {level}"
                )
        else:
            config = config_manager.get_config()
            config_data = config_manager.export_config()
        
        logger.info(
            f"用户 {current_user.id} 获取权限配置: level={level or 'merged'}"
        )
        
        return {
            "success": True,
            "data": {
                "config": config_data,
                "level": level or "merged",
                "retrieved_at": datetime.now().isoformat()
            },
            "message": "配置获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限配置失败: {str(e)}"
        )


@router.get(
    "/config/summary",
    summary="获取配置摘要",
    description="获取权限系统配置摘要信息"
)
@require_permission("admin:system:config:read")
def get_config_summary(
    current_user: User = Depends(get_current_active_user)
):
    """获取配置摘要
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict: 配置摘要
    """
    try:
        config_manager = get_permission_config_manager()
        summary = config_manager.get_config_summary()
        
        logger.info(f"用户 {current_user.id} 获取配置摘要")
        
        return {
            "success": True,
            "data": summary,
            "message": "配置摘要获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取配置摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置摘要失败: {str(e)}"
        )


@router.get(
    "/config/levels",
    summary="获取配置级别",
    description="获取所有可用的配置级别"
)
@require_permission("admin:system:config:read")
def get_config_levels(
    current_user: User = Depends(get_current_active_user)
):
    """获取配置级别
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict: 配置级别列表
    """
    try:
        levels = [
            {
                "value": level.value,
                "name": level.name,
                "description": {
                    "system": "系统级配置 - 核心系统设置",
                    "application": "应用级配置 - 应用程序设置",
                    "user": "用户级配置 - 用户个性化设置",
                    "runtime": "运行时配置 - 动态运行时设置"
                }.get(level.value, "")
            }
            for level in ConfigLevel
        ]
        
        return {
            "success": True,
            "data": {
                "levels": levels,
                "total_count": len(levels)
            },
            "message": "配置级别获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取配置级别失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置级别失败: {str(e)}"
        )


# ==================== 配置管理API ====================

@router.put(
    "/config",
    summary="更新权限配置",
    description="更新指定级别的权限系统配置"
)
@require_permission("admin:system:config:write")
def update_permission_config(
    request: ConfigUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """更新权限配置
    
    Args:
        request: 配置更新请求
        current_user: 当前用户
        
    Returns:
        Dict: 更新结果
    """
    try:
        # 验证配置级别
        try:
            config_level = ConfigLevel(request.level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的配置级别: {request.level}"
            )
        
        config_manager = get_permission_config_manager()
        
        # 更新配置
        success = config_manager.update_config(config_level, request.updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置更新失败"
            )
        
        # 获取更新后的配置
        updated_config = config_manager.export_config(config_level)
        
        logger.info(
            f"用户 {current_user.id} 更新权限配置: "
            f"level={request.level}, updates={list(request.updates.keys())}"
        )
        
        return {
            "success": True,
            "data": {
                "updated_config": updated_config,
                "updated_fields": list(request.updates.keys()),
                "updated_at": datetime.now().isoformat()
            },
            "message": "配置更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新权限配置失败: {str(e)}"
        )


@router.post(
    "/config/reload",
    summary="重新加载配置",
    description="重新加载权限系统配置"
)
@require_permission("admin:system:config:manage")
def reload_permission_config(
    current_user: User = Depends(get_current_active_user)
):
    """重新加载配置
    
    Args:
        current_user: 当前用户
        
    Returns:
        Dict: 重新加载结果
    """
    try:
        config_manager = get_permission_config_manager()
        success = config_manager.reload_config()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置重新加载失败"
            )
        
        # 获取重新加载后的配置摘要
        summary = config_manager.get_config_summary()
        
        logger.info(f"用户 {current_user.id} 重新加载权限配置")
        
        return {
            "success": True,
            "data": {
                "config_summary": summary,
                "reloaded_at": datetime.now().isoformat()
            },
            "message": "配置重新加载成功"
        }
        
    except Exception as e:
        logger.error(f"重新加载权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载权限配置失败: {str(e)}"
        )


# ==================== 配置导入导出API ====================

@router.post(
    "/config/export",
    summary="导出权限配置",
    description="导出权限系统配置数据"
)
@require_permission("admin:system:config:export")
def export_permission_config(
    request: ConfigExportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """导出权限配置
    
    Args:
        request: 配置导出请求
        current_user: 当前用户
        
    Returns:
        Dict: 导出的配置数据
    """
    try:
        config_manager = get_permission_config_manager()
        
        # 确定导出级别
        config_level = None
        if request.level:
            try:
                config_level = ConfigLevel(request.level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的配置级别: {request.level}"
                )
        
        # 导出配置
        config_data = config_manager.export_config(config_level)
        
        # 处理元数据
        if not request.include_metadata:
            config_data = {k: v for k, v in config_data.items() 
                          if not k.startswith('_')}
        
        logger.info(
            f"用户 {current_user.id} 导出权限配置: "
            f"level={request.level or 'merged'}"
        )
        
        return {
            "success": True,
            "data": {
                "config_data": config_data,
                "export_info": {
                    "level": request.level or "merged",
                    "include_metadata": request.include_metadata,
                    "exported_by": current_user.id,
                    "exported_at": datetime.now().isoformat()
                }
            },
            "message": "配置导出成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出权限配置失败: {str(e)}"
        )


@router.post(
    "/config/import",
    summary="导入权限配置",
    description="导入权限系统配置数据"
)
@require_permission("admin:system:config:import")
def import_permission_config(
    request: ConfigImportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """导入权限配置
    
    Args:
        request: 配置导入请求
        current_user: 当前用户
        
    Returns:
        Dict: 导入结果
    """
    try:
        # 验证配置级别
        try:
            config_level = ConfigLevel(request.level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的配置级别: {request.level}"
            )
        
        config_manager = get_permission_config_manager()
        
        if request.validate_only:
            # 仅验证配置
            try:
                config_manager._validate_config(request.config_data, config_level)
                validation_result = "配置验证通过"
            except Exception as e:
                validation_result = f"配置验证失败: {str(e)}"
            
            return {
                "success": True,
                "data": {
                    "validation_result": validation_result,
                    "validated_at": datetime.now().isoformat()
                },
                "message": "配置验证完成"
            }
        else:
            # 导入配置
            success = config_manager.import_config(config_level, request.config_data)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="配置导入失败"
                )
            
            # 获取导入后的配置
            imported_config = config_manager.export_config(config_level)
            
            logger.info(
                f"用户 {current_user.id} 导入权限配置: level={request.level}"
            )
            
            return {
                "success": True,
                "data": {
                    "imported_config": imported_config,
                    "imported_at": datetime.now().isoformat()
                },
                "message": "配置导入成功"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入权限配置失败: {str(e)}"
        )


# ==================== 配置验证API ====================

@router.post(
    "/config/validate",
    summary="验证权限配置",
    description="验证权限系统配置的有效性"
)
@require_permission("admin:system:config:read")
def validate_permission_config(
    config_data: Dict[str, Any] = Body(..., description="要验证的配置数据"),
    level: str = Query("application", description="配置级别"),
    current_user: User = Depends(get_current_active_user)
):
    """验证权限配置
    
    Args:
        config_data: 要验证的配置数据
        level: 配置级别
        current_user: 当前用户
        
    Returns:
        Dict: 验证结果
    """
    try:
        # 验证配置级别
        try:
            config_level = ConfigLevel(level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的配置级别: {level}"
            )
        
        config_manager = get_permission_config_manager()
        
        # 验证配置
        validation_errors = []
        validation_warnings = []
        
        try:
            validated_data = config_manager._validate_config(config_data, config_level)
            
            # 检查是否有字段被修正
            for key, original_value in config_data.items():
                if key in validated_data and validated_data[key] != original_value:
                    validation_warnings.append(
                        f"字段 {key} 的值从 {original_value} 修正为 {validated_data[key]}"
                    )
            
        except Exception as e:
            validation_errors.append(str(e))
        
        is_valid = len(validation_errors) == 0
        
        logger.info(
            f"用户 {current_user.id} 验证权限配置: "
            f"level={level}, valid={is_valid}"
        )
        
        return {
            "success": True,
            "data": {
                "is_valid": is_valid,
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "validated_data": validated_data if is_valid else None,
                "validated_at": datetime.now().isoformat()
            },
            "message": "配置验证完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证权限配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证权限配置失败: {str(e)}"
        )


# ==================== 配置模板API ====================

@router.get(
    "/config/template",
    summary="获取配置模板",
    description="获取指定级别的权限配置模板"
)
@require_permission("admin:system:config:read")
def get_config_template(
    level: str = Query("application", description="配置级别"),
    current_user: User = Depends(get_current_active_user)
):
    """获取配置模板
    
    Args:
        level: 配置级别
        current_user: 当前用户
        
    Returns:
        Dict: 配置模板
    """
    try:
        # 验证配置级别
        try:
            config_level = ConfigLevel(level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的配置级别: {level}"
            )
        
        config_manager = get_permission_config_manager()
        
        # 获取默认配置作为模板
        template_config = config_manager._get_default_config(config_level)
        template_data = config_manager.export_config(config_level)
        
        # 添加字段说明
        field_descriptions = {
            "enable_query_optimization": "是否启用查询优化",
            "enable_batch_optimization": "是否启用批量优化",
            "enable_preload_optimization": "是否启用预加载优化",
            "max_batch_size": "最大批量处理大小",
            "preload_cache_ttl": "预加载缓存TTL（秒）",
            "enable_permission_cache": "是否启用权限缓存",
            "cache_ttl": "缓存TTL（秒）",
            "cache_max_size": "缓存最大大小",
            "cache_strategy": "缓存策略（lru/lfu/fifo）",
            "enable_performance_monitoring": "是否启用性能监控",
            "slow_query_threshold": "慢查询阈值（秒）",
            "max_history_size": "最大历史记录大小",
            "stats_window_minutes": "统计时间窗口（分钟）",
            "enable_auto_index_creation": "是否启用自动索引创建",
            "enable_index_analysis": "是否启用索引分析",
            "index_maintenance_interval": "索引维护间隔（秒）",
            "enable_permission_audit": "是否启用权限审计",
            "max_permission_depth": "最大权限深度",
            "enable_role_inheritance": "是否启用角色继承",
            "max_role_depth": "最大角色深度",
            "enable_resource_permissions": "是否启用资源权限",
            "default_resource_permission_level": "默认资源权限级别",
            "enable_resource_inheritance": "是否启用资源继承",
            "enable_permission_api": "是否启用权限API",
            "api_rate_limit": "API速率限制（每分钟）",
            "enable_api_authentication": "是否启用API认证",
            "log_level": "日志级别",
            "enable_query_logging": "是否启用查询日志",
            "enable_performance_logging": "是否启用性能日志",
            "log_retention_days": "日志保留天数"
        }
        
        return {
            "success": True,
            "data": {
                "template": template_data,
                "field_descriptions": field_descriptions,
                "level": level,
                "generated_at": datetime.now().isoformat()
            },
            "message": "配置模板获取成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置模板失败: {str(e)}"
        )