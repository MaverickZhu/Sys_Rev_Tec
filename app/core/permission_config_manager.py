#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限配置管理器

提供权限系统的配置管理、动态配置更新和配置验证功能
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigLevel(Enum):
    """配置级别"""
    SYSTEM = "system"  # 系统级配置
    APPLICATION = "application"  # 应用级配置
    USER = "user"  # 用户级配置
    RUNTIME = "runtime"  # 运行时配置


@dataclass
class PermissionConfig:
    """权限配置数据类"""
    # 查询优化配置
    enable_query_optimization: bool = True
    enable_batch_optimization: bool = True
    enable_preload_optimization: bool = True
    max_batch_size: int = 100
    preload_cache_ttl: int = 300  # 秒
    
    # 缓存配置
    enable_permission_cache: bool = True
    cache_ttl: int = 600  # 秒
    cache_max_size: int = 10000
    cache_strategy: str = "lru"  # lru, lfu, fifo
    
    # 性能监控配置
    enable_performance_monitoring: bool = True
    slow_query_threshold: float = 1.0  # 秒
    max_history_size: int = 10000
    stats_window_minutes: int = 60
    
    # 索引优化配置
    enable_auto_index_creation: bool = True
    enable_index_analysis: bool = True
    index_maintenance_interval: int = 3600  # 秒
    
    # 安全配置
    enable_permission_audit: bool = True
    max_permission_depth: int = 10
    enable_role_inheritance: bool = True
    max_role_depth: int = 5
    
    # 资源权限配置
    enable_resource_permissions: bool = True
    default_resource_permission_level: str = "read"
    enable_resource_inheritance: bool = True
    
    # API配置
    enable_permission_api: bool = True
    api_rate_limit: int = 1000  # 每分钟请求数
    enable_api_authentication: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    enable_query_logging: bool = False
    enable_performance_logging: bool = True
    log_retention_days: int = 30


class PermissionConfigManager:
    """权限配置管理器
    
    提供配置加载、保存、验证和动态更新功能
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "config")
        self.config_dir.mkdir(exist_ok=True)
        
        # 配置文件路径
        self.system_config_file = self.config_dir / "permission_system.json"
        self.app_config_file = self.config_dir / "permission_app.json"
        self.user_config_file = self.config_dir / "permission_user.json"
        self.runtime_config_file = self.config_dir / "permission_runtime.json"
        
        # 配置缓存
        self._config_cache: Dict[ConfigLevel, PermissionConfig] = {}
        self._merged_config: Optional[PermissionConfig] = None
        self._config_watchers: List[callable] = []
        
        # 加载配置
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件"""
        try:
            # 加载各级配置
            self._config_cache[ConfigLevel.SYSTEM] = self._load_config(
                self.system_config_file, ConfigLevel.SYSTEM
            )
            self._config_cache[ConfigLevel.APPLICATION] = self._load_config(
                self.app_config_file, ConfigLevel.APPLICATION
            )
            self._config_cache[ConfigLevel.USER] = self._load_config(
                self.user_config_file, ConfigLevel.USER
            )
            self._config_cache[ConfigLevel.RUNTIME] = self._load_config(
                self.runtime_config_file, ConfigLevel.RUNTIME
            )
            
            # 合并配置
            self._merge_configs()
            
            logger.info("权限配置加载完成")
            
        except Exception as e:
            logger.error(f"加载权限配置失败: {e}")
            # 使用默认配置
            self._merged_config = PermissionConfig()
    
    def _load_config(self, config_file: Path, level: ConfigLevel) -> PermissionConfig:
        """加载单个配置文件
        
        Args:
            config_file: 配置文件路径
            level: 配置级别
            
        Returns:
            PermissionConfig: 配置对象
        """
        if not config_file.exists():
            # 创建默认配置文件
            default_config = self._get_default_config(level)
            self._save_config(config_file, default_config)
            return default_config
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置
            validated_data = self._validate_config(config_data, level)
            
            # 创建配置对象
            config = PermissionConfig(**validated_data)
            
            logger.debug(f"加载配置文件: {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_file}: {e}")
            return self._get_default_config(level)
    
    def _get_default_config(self, level: ConfigLevel) -> PermissionConfig:
        """获取默认配置
        
        Args:
            level: 配置级别
            
        Returns:
            PermissionConfig: 默认配置
        """
        base_config = PermissionConfig()
        
        # 根据配置级别调整默认值
        if level == ConfigLevel.SYSTEM:
            # 系统级配置 - 保守设置
            base_config.enable_query_optimization = True
            base_config.enable_performance_monitoring = True
            base_config.enable_permission_audit = True
            
        elif level == ConfigLevel.APPLICATION:
            # 应用级配置 - 平衡设置
            base_config.max_batch_size = 100
            base_config.cache_ttl = 600
            base_config.slow_query_threshold = 1.0
            
        elif level == ConfigLevel.USER:
            # 用户级配置 - 个性化设置
            base_config.log_level = "INFO"
            base_config.enable_query_logging = False
            
        elif level == ConfigLevel.RUNTIME:
            # 运行时配置 - 动态设置
            base_config.enable_performance_monitoring = True
            base_config.stats_window_minutes = 60
        
        return base_config
    
    def _validate_config(self, config_data: Dict[str, Any], level: ConfigLevel) -> Dict[str, Any]:
        """验证配置数据
        
        Args:
            config_data: 配置数据
            level: 配置级别
            
        Returns:
            Dict[str, Any]: 验证后的配置数据
        """
        validated_data = {}
        default_config = self._get_default_config(level)
        
        # 获取默认配置的字段
        default_fields = asdict(default_config)
        
        for field_name, default_value in default_fields.items():
            if field_name in config_data:
                value = config_data[field_name]
                
                # 类型验证
                if not isinstance(value, type(default_value)):
                    logger.warning(
                        f"配置字段 {field_name} 类型错误，使用默认值: {default_value}"
                    )
                    validated_data[field_name] = default_value
                    continue
                
                # 值范围验证
                if self._validate_field_value(field_name, value):
                    validated_data[field_name] = value
                else:
                    logger.warning(
                        f"配置字段 {field_name} 值无效，使用默认值: {default_value}"
                    )
                    validated_data[field_name] = default_value
            else:
                validated_data[field_name] = default_value
        
        return validated_data
    
    def _validate_field_value(self, field_name: str, value: Any) -> bool:
        """验证字段值
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            bool: 是否有效
        """
        # 数值范围验证
        if field_name == "max_batch_size":
            return 1 <= value <= 1000
        elif field_name == "cache_ttl":
            return 60 <= value <= 86400  # 1分钟到1天
        elif field_name == "cache_max_size":
            return 100 <= value <= 100000
        elif field_name == "slow_query_threshold":
            return 0.1 <= value <= 60.0
        elif field_name == "max_history_size":
            return 1000 <= value <= 100000
        elif field_name == "stats_window_minutes":
            return 1 <= value <= 1440  # 1分钟到1天
        elif field_name == "max_permission_depth":
            return 1 <= value <= 20
        elif field_name == "max_role_depth":
            return 1 <= value <= 10
        elif field_name == "api_rate_limit":
            return 10 <= value <= 10000
        elif field_name == "log_retention_days":
            return 1 <= value <= 365
        
        # 字符串值验证
        elif field_name == "cache_strategy":
            return value in ["lru", "lfu", "fifo"]
        elif field_name == "default_resource_permission_level":
            return value in ["read", "write", "admin", "owner"]
        elif field_name == "log_level":
            return value in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        return True
    
    def _merge_configs(self) -> None:
        """合并各级配置"""
        # 按优先级合并配置：RUNTIME > USER > APPLICATION > SYSTEM
        merged_data = asdict(self._config_cache[ConfigLevel.SYSTEM])
        
        for level in [ConfigLevel.APPLICATION, ConfigLevel.USER, ConfigLevel.RUNTIME]:
            level_data = asdict(self._config_cache[level])
            for key, value in level_data.items():
                if value is not None:  # 只覆盖非空值
                    merged_data[key] = value
        
        self._merged_config = PermissionConfig(**merged_data)
        
        # 通知配置观察者
        self._notify_config_watchers()
    
    def _save_config(self, config_file: Path, config: PermissionConfig) -> None:
        """保存配置文件
        
        Args:
            config_file: 配置文件路径
            config: 配置对象
        """
        try:
            config_data = asdict(config)
            config_data['_updated_at'] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"保存配置文件: {config_file}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败 {config_file}: {e}")
    
    def get_config(self) -> PermissionConfig:
        """获取合并后的配置
        
        Returns:
            PermissionConfig: 合并后的配置
        """
        if self._merged_config is None:
            self._load_all_configs()
        
        return self._merged_config
    
    def get_config_by_level(self, level: ConfigLevel) -> PermissionConfig:
        """获取指定级别的配置
        
        Args:
            level: 配置级别
            
        Returns:
            PermissionConfig: 指定级别的配置
        """
        return self._config_cache.get(level, PermissionConfig())
    
    def update_config(self, level: ConfigLevel, updates: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            level: 配置级别
            updates: 更新的配置项
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取当前配置
            current_config = self._config_cache.get(level, PermissionConfig())
            current_data = asdict(current_config)
            
            # 验证更新数据
            validated_updates = self._validate_config(updates, level)
            
            # 应用更新
            current_data.update(validated_updates)
            
            # 创建新配置对象
            new_config = PermissionConfig(**current_data)
            
            # 保存配置
            config_file = self._get_config_file(level)
            self._save_config(config_file, new_config)
            
            # 更新缓存
            self._config_cache[level] = new_config
            
            # 重新合并配置
            self._merge_configs()
            
            logger.info(f"更新 {level.value} 级配置成功")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def _get_config_file(self, level: ConfigLevel) -> Path:
        """获取配置文件路径
        
        Args:
            level: 配置级别
            
        Returns:
            Path: 配置文件路径
        """
        file_map = {
            ConfigLevel.SYSTEM: self.system_config_file,
            ConfigLevel.APPLICATION: self.app_config_file,
            ConfigLevel.USER: self.user_config_file,
            ConfigLevel.RUNTIME: self.runtime_config_file
        }
        return file_map[level]
    
    def reload_config(self) -> bool:
        """重新加载配置
        
        Returns:
            bool: 是否重新加载成功
        """
        try:
            self._load_all_configs()
            logger.info("权限配置重新加载成功")
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def add_config_watcher(self, callback: callable) -> None:
        """添加配置观察者
        
        Args:
            callback: 回调函数
        """
        self._config_watchers.append(callback)
    
    def remove_config_watcher(self, callback: callable) -> None:
        """移除配置观察者
        
        Args:
            callback: 回调函数
        """
        if callback in self._config_watchers:
            self._config_watchers.remove(callback)
    
    def _notify_config_watchers(self) -> None:
        """通知配置观察者"""
        for callback in self._config_watchers:
            try:
                callback(self._merged_config)
            except Exception as e:
                logger.error(f"通知配置观察者失败: {e}")
    
    def export_config(self, level: Optional[ConfigLevel] = None) -> Dict[str, Any]:
        """导出配置
        
        Args:
            level: 配置级别，None表示导出合并后的配置
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        if level is None:
            config = self.get_config()
        else:
            config = self.get_config_by_level(level)
        
        config_data = asdict(config)
        config_data['_exported_at'] = datetime.now().isoformat()
        config_data['_level'] = level.value if level else 'merged'
        
        return config_data
    
    def import_config(self, level: ConfigLevel, config_data: Dict[str, Any]) -> bool:
        """导入配置
        
        Args:
            level: 配置级别
            config_data: 配置数据
            
        Returns:
            bool: 是否导入成功
        """
        try:
            # 移除元数据字段
            clean_data = {k: v for k, v in config_data.items() 
                         if not k.startswith('_')}
            
            # 更新配置
            return self.update_config(level, clean_data)
            
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        config = self.get_config()
        
        return {
            "optimization_enabled": {
                "query_optimization": config.enable_query_optimization,
                "batch_optimization": config.enable_batch_optimization,
                "preload_optimization": config.enable_preload_optimization,
                "permission_cache": config.enable_permission_cache
            },
            "performance_settings": {
                "monitoring_enabled": config.enable_performance_monitoring,
                "slow_query_threshold": config.slow_query_threshold,
                "max_batch_size": config.max_batch_size,
                "cache_ttl": config.cache_ttl
            },
            "security_settings": {
                "audit_enabled": config.enable_permission_audit,
                "max_permission_depth": config.max_permission_depth,
                "role_inheritance_enabled": config.enable_role_inheritance,
                "max_role_depth": config.max_role_depth
            },
            "api_settings": {
                "api_enabled": config.enable_permission_api,
                "rate_limit": config.api_rate_limit,
                "authentication_enabled": config.enable_api_authentication
            },
            "logging_settings": {
                "log_level": config.log_level,
                "query_logging": config.enable_query_logging,
                "performance_logging": config.enable_performance_logging,
                "retention_days": config.log_retention_days
            }
        }


# 全局配置管理器实例
_config_manager: Optional[PermissionConfigManager] = None


def get_permission_config_manager() -> PermissionConfigManager:
    """获取权限配置管理器实例
    
    Returns:
        PermissionConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = PermissionConfigManager()
    return _config_manager


def get_permission_config() -> PermissionConfig:
    """获取权限配置
    
    Returns:
        PermissionConfig: 权限配置
    """
    return get_permission_config_manager().get_config()