"""缓存配置管理模块

提供动态缓存配置管理、参数调优和配置持久化功能。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.cache_config import (
    CacheSystemConfig,
    get_cache_config_for_environment,
    load_cache_config_from_file,
    save_cache_config_to_file
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheConfigManager:
    """缓存配置管理器"""
    
    def __init__(self):
        self.current_config: Optional[CacheSystemConfig] = None
        self.config_history: List[Dict] = []
        self.config_file_path = Path("cache_config.json")
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def load_config(self) -> CacheSystemConfig:
        """加载缓存配置"""
        try:
            # 尝试从文件加载配置
            if self.config_file_path.exists():
                self.current_config = load_cache_config_from_file(str(self.config_file_path))
                logger.info("Loaded cache config from file")
            else:
                # 使用环境默认配置
                self.current_config = get_cache_config_for_environment(settings.ENVIRONMENT)
                logger.info(f"Using default config for environment: {settings.ENVIRONMENT}")
            
            return self.current_config
            
        except Exception as e:
            logger.error(f"Failed to load cache config: {e}")
            # 回退到默认配置
            self.current_config = get_cache_config_for_environment("development")
            return self.current_config
    
    async def save_config(self, config: CacheSystemConfig, backup: bool = True) -> bool:
        """保存缓存配置"""
        try:
            # 创建备份
            if backup and self.config_file_path.exists():
                await self._create_backup()
            
            # 保存新配置
            save_cache_config_to_file(config, str(self.config_file_path))
            
            # 记录配置变更历史
            self._record_config_change(config)
            
            self.current_config = config
            logger.info("Cache config saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache config: {e}")
            return False
    
    async def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新缓存配置"""
        try:
            if not self.current_config:
                await self.load_config()
            
            # 创建配置副本
            config_dict = self.current_config.to_dict()
            
            # 应用更新
            self._apply_updates(config_dict, updates)
            
            # 验证配置
            if not self._validate_config(config_dict):
                logger.error("Invalid config updates")
                return False
            
            # 重新创建配置对象
            updated_config = self._dict_to_config(config_dict)
            
            # 保存更新后的配置
            return await self.save_config(updated_config)
            
        except Exception as e:
            logger.error(f"Failed to update cache config: {e}")
            return False
    
    def get_current_config(self) -> Optional[CacheSystemConfig]:
        """获取当前配置"""
        return self.current_config
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        if self.current_config:
            return self.current_config.to_dict()
        return {}
    
    def get_config_history(self, limit: int = 10) -> List[Dict]:
        """获取配置变更历史"""
        return self.config_history[-limit:]
    
    async def reset_to_default(self, environment: str = None) -> bool:
        """重置为默认配置"""
        try:
            env = environment or settings.ENVIRONMENT
            default_config = get_cache_config_for_environment(env)
            
            return await self.save_config(default_config)
            
        except Exception as e:
            logger.error(f"Failed to reset config to default: {e}")
            return False
    
    async def restore_from_backup(self, backup_file: str) -> bool:
        """从备份恢复配置"""
        try:
            backup_path = self.backup_dir / backup_file
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # 加载备份配置
            backup_config = load_cache_config_from_file(str(backup_path))
            
            # 保存为当前配置
            return await self.save_config(backup_config)
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份文件"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.json"):
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size
                })
            
            # 按创建时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    async def optimize_config_for_workload(self, workload_stats: Dict) -> Dict[str, Any]:
        """根据工作负载优化配置"""
        try:
            if not self.current_config:
                await self.load_config()
            
            recommendations = {}
            
            # 分析工作负载特征
            hit_rate = workload_stats.get("hit_rate", 0.8)
            avg_response_time = workload_stats.get("avg_response_time", 50)
            memory_usage = workload_stats.get("memory_usage", 0.6)
            request_rate = workload_stats.get("request_rate", 100)
            
            # 基于分析结果生成建议
            if hit_rate < 0.7:
                recommendations["session_cache_ttl"] = min(
                    self.current_config.default_strategies.session_cache.ttl * 1.5,
                    3600
                )
                recommendations["api_response_cache_ttl"] = min(
                    self.current_config.default_strategies.api_response_cache.ttl * 1.2,
                    1800
                )
            
            if avg_response_time > 100:
                recommendations["redis_pool_size"] = min(
                    self.current_config.redis_settings.pool_size * 1.2,
                    50
                )
            
            if memory_usage > 0.8:
                recommendations["session_cache_max_size"] = max(
                    self.current_config.default_strategies.session_cache.max_size * 0.8,
                    1000
                )
            
            if request_rate > 1000:
                recommendations["enable_batch_operations"] = True
                recommendations["batch_size"] = 100
            
            return {
                "recommendations": recommendations,
                "analysis": {
                    "hit_rate": hit_rate,
                    "avg_response_time": avg_response_time,
                    "memory_usage": memory_usage,
                    "request_rate": request_rate
                },
                "confidence": self._calculate_confidence(workload_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize config for workload: {e}")
            return {"error": str(e)}
    
    def _apply_updates(self, config_dict: Dict, updates: Dict):
        """应用配置更新"""
        for key, value in updates.items():
            if "." in key:
                # 处理嵌套键
                keys = key.split(".")
                current = config_dict
                
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                current[keys[-1]] = value
            else:
                config_dict[key] = value
    
    def _validate_config(self, config_dict: Dict) -> bool:
        """验证配置有效性"""
        try:
            # 基本验证
            required_keys = ["redis_settings", "default_strategies"]
            
            for key in required_keys:
                if key not in config_dict:
                    logger.error(f"Missing required config key: {key}")
                    return False
            
            # 验证数值范围
            redis_settings = config_dict.get("redis_settings", {})
            
            if "pool_size" in redis_settings:
                if not (1 <= redis_settings["pool_size"] <= 100):
                    logger.error("Invalid pool_size value")
                    return False
            
            if "timeout" in redis_settings:
                if not (1 <= redis_settings["timeout"] <= 300):
                    logger.error("Invalid timeout value")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False
    
    def _dict_to_config(self, config_dict: Dict) -> CacheSystemConfig:
        """将字典转换为配置对象"""
        # 这里需要实现从字典重建CacheSystemConfig对象的逻辑
        # 暂时返回当前配置
        return self.current_config
    
    async def _create_backup(self):
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"cache_config_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # 复制当前配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            logger.info(f"Created config backup: {backup_filename}")
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    def _record_config_change(self, config: CacheSystemConfig):
        """记录配置变更"""
        try:
            change_record = {
                "timestamp": datetime.now().isoformat(),
                "config_summary": {
                    "redis_host": config.redis_settings.host,
                    "redis_port": config.redis_settings.port,
                    "pool_size": config.redis_settings.pool_size,
                    "session_cache_ttl": config.default_strategies.session_cache.ttl,
                    "api_cache_ttl": config.default_strategies.api_response_cache.ttl
                }
            }
            
            self.config_history.append(change_record)
            
            # 保持历史记录在合理范围内
            if len(self.config_history) > 50:
                self.config_history = self.config_history[-25:]
            
        except Exception as e:
            logger.error(f"Failed to record config change: {e}")
    
    def _calculate_confidence(self, workload_stats: Dict) -> float:
        """计算优化建议的置信度"""
        try:
            # 基于数据完整性和样本大小计算置信度
            required_metrics = ["hit_rate", "avg_response_time", "memory_usage", "request_rate"]
            available_metrics = sum(1 for metric in required_metrics if metric in workload_stats)
            
            completeness_score = available_metrics / len(required_metrics)
            
            # 基于请求数量计算样本置信度
            total_requests = workload_stats.get("total_requests", 0)
            sample_score = min(total_requests / 10000, 1.0)  # 10000个请求为满分
            
            # 综合置信度
            confidence = (completeness_score * 0.6 + sample_score * 0.4)
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.5


# 全局配置管理器实例
_cache_config_manager: Optional[CacheConfigManager] = None


def get_cache_config_manager() -> CacheConfigManager:
    """获取缓存配置管理器实例"""
    global _cache_config_manager
    if _cache_config_manager is None:
        _cache_config_manager = CacheConfigManager()
    return _cache_config_manager


async def load_cache_config() -> CacheSystemConfig:
    """加载缓存配置"""
    manager = get_cache_config_manager()
    return await manager.load_config()


async def update_cache_config(updates: Dict[str, Any]) -> bool:
    """更新缓存配置"""
    manager = get_cache_config_manager()
    return await manager.update_config(updates)