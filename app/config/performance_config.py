#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控配置
定义性能监控的阈值、告警规则和配置参数
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AlertThresholds:
    """
    告警阈值配置
    """
    # 响应时间阈值（秒）
    response_time_warning: float = 1.0
    response_time_critical: float = 3.0
    
    # CPU使用率阈值（百分比）
    cpu_usage_warning: float = 70.0
    cpu_usage_critical: float = 90.0
    
    # 内存使用率阈值（百分比）
    memory_usage_warning: float = 80.0
    memory_usage_critical: float = 95.0
    
    # 磁盘使用率阈值（百分比）
    disk_usage_warning: float = 85.0
    disk_usage_critical: float = 95.0
    
    # 错误率阈值（百分比）
    error_rate_warning: float = 5.0
    error_rate_critical: float = 10.0
    
    # 缓存命中率阈值（百分比）
    cache_hit_rate_warning: float = 80.0
    cache_hit_rate_critical: float = 60.0
    
    # 数据库连接数阈值
    db_connections_warning: int = 80
    db_connections_critical: int = 95
    
    # API吞吐量阈值（请求/秒）
    api_throughput_warning: float = 100.0
    api_throughput_critical: float = 50.0


@dataclass
class MonitoringConfig:
    """
    监控系统配置
    """
    # 指标收集间隔（秒）
    metrics_collection_interval: int = 30
    
    # 性能数据保留时间（小时）
    performance_data_retention_hours: int = 24
    
    # 告警检查间隔（秒）
    alert_check_interval: int = 60
    
    # 慢请求阈值（秒）
    slow_request_threshold: float = 2.0
    
    # 启用的监控功能
    enable_system_monitoring: bool = True
    enable_api_monitoring: bool = True
    enable_database_monitoring: bool = True
    enable_cache_monitoring: bool = True
    enable_business_monitoring: bool = True
    
    # Prometheus配置
    prometheus_enabled: bool = True
    prometheus_port: int = 8000
    prometheus_path: str = "/metrics"
    
    # 告警配置
    enable_alerts: bool = True
    alert_webhook_url: str = ""
    alert_email_enabled: bool = False
    alert_email_recipients: List[str] = field(default_factory=list)
    
    # 日志配置
    performance_log_level: str = "INFO"
    performance_log_file: str = "logs/performance.log"
    
    # 排除的监控路径
    excluded_paths: List[str] = field(default_factory=lambda: [
        "/metrics",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
        "/favicon.ico"
    ])
    
    # 业务指标配置
    business_metrics_enabled: bool = True
    track_user_sessions: bool = True
    track_document_processing: bool = True
    track_ocr_operations: bool = True
    track_project_operations: bool = True


@dataclass
class PerformanceConfig:
    """
    性能监控完整配置
    """
    alert_thresholds: AlertThresholds = field(default_factory=AlertThresholds)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        """
        从环境变量加载配置
        
        Returns:
            PerformanceConfig: 配置实例
        """
        config = cls()
        
        # 告警阈值配置
        config.alert_thresholds.response_time_warning = float(
            os.getenv('PERF_RESPONSE_TIME_WARNING', config.alert_thresholds.response_time_warning)
        )
        config.alert_thresholds.response_time_critical = float(
            os.getenv('PERF_RESPONSE_TIME_CRITICAL', config.alert_thresholds.response_time_critical)
        )
        config.alert_thresholds.cpu_usage_warning = float(
            os.getenv('PERF_CPU_WARNING', config.alert_thresholds.cpu_usage_warning)
        )
        config.alert_thresholds.cpu_usage_critical = float(
            os.getenv('PERF_CPU_CRITICAL', config.alert_thresholds.cpu_usage_critical)
        )
        config.alert_thresholds.memory_usage_warning = float(
            os.getenv('PERF_MEMORY_WARNING', config.alert_thresholds.memory_usage_warning)
        )
        config.alert_thresholds.memory_usage_critical = float(
            os.getenv('PERF_MEMORY_CRITICAL', config.alert_thresholds.memory_usage_critical)
        )
        config.alert_thresholds.error_rate_warning = float(
            os.getenv('PERF_ERROR_RATE_WARNING', config.alert_thresholds.error_rate_warning)
        )
        config.alert_thresholds.error_rate_critical = float(
            os.getenv('PERF_ERROR_RATE_CRITICAL', config.alert_thresholds.error_rate_critical)
        )
        
        # 监控配置
        config.monitoring.metrics_collection_interval = int(
            os.getenv('PERF_COLLECTION_INTERVAL', config.monitoring.metrics_collection_interval)
        )
        config.monitoring.slow_request_threshold = float(
            os.getenv('PERF_SLOW_REQUEST_THRESHOLD', config.monitoring.slow_request_threshold)
        )
        config.monitoring.enable_alerts = os.getenv('PERF_ENABLE_ALERTS', 'true').lower() == 'true'
        config.monitoring.alert_webhook_url = os.getenv('PERF_ALERT_WEBHOOK_URL', '')
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict: 配置字典
        """
        return {
            'alert_thresholds': {
                'response_time_warning': self.alert_thresholds.response_time_warning,
                'response_time_critical': self.alert_thresholds.response_time_critical,
                'cpu_usage_warning': self.alert_thresholds.cpu_usage_warning,
                'cpu_usage_critical': self.alert_thresholds.cpu_usage_critical,
                'memory_usage_warning': self.alert_thresholds.memory_usage_warning,
                'memory_usage_critical': self.alert_thresholds.memory_usage_critical,
                'disk_usage_warning': self.alert_thresholds.disk_usage_warning,
                'disk_usage_critical': self.alert_thresholds.disk_usage_critical,
                'error_rate_warning': self.alert_thresholds.error_rate_warning,
                'error_rate_critical': self.alert_thresholds.error_rate_critical,
                'cache_hit_rate_warning': self.alert_thresholds.cache_hit_rate_warning,
                'cache_hit_rate_critical': self.alert_thresholds.cache_hit_rate_critical,
                'db_connections_warning': self.alert_thresholds.db_connections_warning,
                'db_connections_critical': self.alert_thresholds.db_connections_critical,
                'api_throughput_warning': self.alert_thresholds.api_throughput_warning,
                'api_throughput_critical': self.alert_thresholds.api_throughput_critical,
            },
            'monitoring': {
                'metrics_collection_interval': self.monitoring.metrics_collection_interval,
                'performance_data_retention_hours': self.monitoring.performance_data_retention_hours,
                'alert_check_interval': self.monitoring.alert_check_interval,
                'slow_request_threshold': self.monitoring.slow_request_threshold,
                'enable_system_monitoring': self.monitoring.enable_system_monitoring,
                'enable_api_monitoring': self.monitoring.enable_api_monitoring,
                'enable_database_monitoring': self.monitoring.enable_database_monitoring,
                'enable_cache_monitoring': self.monitoring.enable_cache_monitoring,
                'enable_business_monitoring': self.monitoring.enable_business_monitoring,
                'prometheus_enabled': self.monitoring.prometheus_enabled,
                'prometheus_port': self.monitoring.prometheus_port,
                'prometheus_path': self.monitoring.prometheus_path,
                'enable_alerts': self.monitoring.enable_alerts,
                'alert_webhook_url': self.monitoring.alert_webhook_url,
                'alert_email_enabled': self.monitoring.alert_email_enabled,
                'alert_email_recipients': self.monitoring.alert_email_recipients,
                'performance_log_level': self.monitoring.performance_log_level,
                'performance_log_file': self.monitoring.performance_log_file,
                'excluded_paths': self.monitoring.excluded_paths,
                'business_metrics_enabled': self.monitoring.business_metrics_enabled,
                'track_user_sessions': self.monitoring.track_user_sessions,
                'track_document_processing': self.monitoring.track_document_processing,
                'track_ocr_operations': self.monitoring.track_ocr_operations,
                'track_project_operations': self.monitoring.track_project_operations,
            }
        }
    
    def update_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        更新告警阈值
        
        Args:
            thresholds: 新的阈值配置
        """
        for key, value in thresholds.items():
            if hasattr(self.alert_thresholds, key):
                setattr(self.alert_thresholds, key, value)
    
    def get_threshold(self, metric_name: str, level: str = 'warning') -> float:
        """
        获取指定指标的阈值
        
        Args:
            metric_name: 指标名称
            level: 告警级别 ('warning' 或 'critical')
            
        Returns:
            float: 阈值
        """
        threshold_attr = f"{metric_name}_{level}"
        return getattr(self.alert_thresholds, threshold_attr, 0.0)
    
    def is_metric_enabled(self, metric_type: str) -> bool:
        """
        检查指定类型的监控是否启用
        
        Args:
            metric_type: 监控类型
            
        Returns:
            bool: 是否启用
        """
        enable_attr = f"enable_{metric_type}_monitoring"
        return getattr(self.monitoring, enable_attr, False)


# 全局配置实例
performance_config = PerformanceConfig.from_env()


# 配置验证函数
def validate_config(config: PerformanceConfig) -> List[str]:
    """
    验证配置的有效性
    
    Args:
        config: 配置实例
        
    Returns:
        List[str]: 验证错误列表
    """
    errors = []
    
    # 验证阈值范围
    if config.alert_thresholds.response_time_warning >= config.alert_thresholds.response_time_critical:
        errors.append("响应时间警告阈值应小于严重阈值")
    
    if config.alert_thresholds.cpu_usage_warning >= config.alert_thresholds.cpu_usage_critical:
        errors.append("CPU使用率警告阈值应小于严重阈值")
    
    if config.alert_thresholds.memory_usage_warning >= config.alert_thresholds.memory_usage_critical:
        errors.append("内存使用率警告阈值应小于严重阈值")
    
    if config.alert_thresholds.error_rate_warning >= config.alert_thresholds.error_rate_critical:
        errors.append("错误率警告阈值应小于严重阈值")
    
    # 验证收集间隔
    if config.monitoring.metrics_collection_interval <= 0:
        errors.append("指标收集间隔必须大于0")
    
    if config.monitoring.alert_check_interval <= 0:
        errors.append("告警检查间隔必须大于0")
    
    # 验证日志文件路径
    log_dir = Path(config.monitoring.performance_log_file).parent
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            errors.append(f"无法创建日志目录: {log_dir}")
    
    return errors


# 配置加载和验证
def load_and_validate_config() -> PerformanceConfig:
    """
    加载并验证配置
    
    Returns:
        PerformanceConfig: 验证后的配置
        
    Raises:
        ValueError: 配置验证失败
    """
    config = PerformanceConfig.from_env()
    errors = validate_config(config)
    
    if errors:
        raise ValueError(f"配置验证失败: {'; '.join(errors)}")
    
    return config


if __name__ == "__main__":
    # 测试配置
    print("测试性能监控配置...")
    
    try:
        config = load_and_validate_config()
        print("✅ 配置验证通过")
        
        print("\n📊 当前配置:")
        config_dict = config.to_dict()
        
        print(f"- 响应时间告警阈值: {config.alert_thresholds.response_time_warning}s / {config.alert_thresholds.response_time_critical}s")
        print(f"- CPU使用率告警阈值: {config.alert_thresholds.cpu_usage_warning}% / {config.alert_thresholds.cpu_usage_critical}%")
        print(f"- 内存使用率告警阈值: {config.alert_thresholds.memory_usage_warning}% / {config.alert_thresholds.memory_usage_critical}%")
        print(f"- 错误率告警阈值: {config.alert_thresholds.error_rate_warning}% / {config.alert_thresholds.error_rate_critical}%")
        print(f"- 指标收集间隔: {config.monitoring.metrics_collection_interval}秒")
        print(f"- 慢请求阈值: {config.monitoring.slow_request_threshold}秒")
        print(f"- 告警功能: {'启用' if config.monitoring.enable_alerts else '禁用'}")
        
        print("\n🔧 测试阈值获取:")
        print(f"- CPU警告阈值: {config.get_threshold('cpu_usage', 'warning')}%")
        print(f"- 内存严重阈值: {config.get_threshold('memory_usage', 'critical')}%")
        
        print("\n📈 监控功能状态:")
        print(f"- 系统监控: {'启用' if config.is_metric_enabled('system') else '禁用'}")
        print(f"- API监控: {'启用' if config.is_metric_enabled('api') else '禁用'}")
        print(f"- 数据库监控: {'启用' if config.is_metric_enabled('database') else '禁用'}")
        print(f"- 缓存监控: {'启用' if config.is_metric_enabled('cache') else '禁用'}")
        
    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
    
    print("\n测试完成")