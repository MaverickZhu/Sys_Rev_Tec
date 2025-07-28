#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测数据模型
定义异常检测相关的数据结构和枚举

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import numpy as np


class AnomalyType(Enum):
    """异常类型"""
    STATISTICAL = "statistical"  # 统计异常
    BEHAVIORAL = "behavioral"  # 行为异常
    TEMPORAL = "temporal"  # 时间异常
    PATTERN = "pattern"  # 模式异常
    OUTLIER = "outlier"  # 离群值
    TREND = "trend"  # 趋势异常
    SEASONAL = "seasonal"  # 季节性异常
    CORRELATION = "correlation"  # 相关性异常
    THRESHOLD = "threshold"  # 阈值异常
    CUSTOM = "custom"  # 自定义异常


class AnomalySeverity(Enum):
    """异常严重程度"""
    CRITICAL = "critical"  # 严重异常
    HIGH = "high"  # 高风险异常
    MEDIUM = "medium"  # 中等异常
    LOW = "low"  # 低风险异常
    INFO = "info"  # 信息性异常


class AnomalyStatus(Enum):
    """异常状态"""
    DETECTED = "detected"  # 已检测
    CONFIRMED = "confirmed"  # 已确认
    FALSE_POSITIVE = "false_positive"  # 误报
    RESOLVED = "resolved"  # 已解决
    INVESTIGATING = "investigating"  # 调查中
    IGNORED = "ignored"  # 已忽略


class DetectionMethod(Enum):
    """检测方法"""
    Z_SCORE = "z_score"  # Z分数
    IQR = "iqr"  # 四分位距
    ISOLATION_FOREST = "isolation_forest"  # 孤立森林
    ONE_CLASS_SVM = "one_class_svm"  # 单类SVM
    LOCAL_OUTLIER_FACTOR = "lof"  # 局部离群因子
    DBSCAN = "dbscan"  # 密度聚类
    AUTOENCODER = "autoencoder"  # 自编码器
    LSTM = "lstm"  # 长短期记忆网络
    ARIMA = "arima"  # ARIMA模型
    PROPHET = "prophet"  # Prophet预测
    CUSTOM_RULE = "custom_rule"  # 自定义规则


@dataclass
class AnomalyPattern:
    """异常模式"""
    pattern_id: str
    pattern_name: str
    pattern_type: AnomalyType
    description: str
    indicators: List[str]
    threshold_config: Dict[str, Any]
    detection_method: DetectionMethod
    severity_mapping: Dict[str, AnomalySeverity]
    confidence_threshold: float = 0.7
    enabled: bool = True
    created_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionConfig:
    """检测配置"""
    # 基础配置
    sensitivity: float = 0.8  # 敏感度 (0-1)
    confidence_threshold: float = 0.7  # 置信度阈值
    max_anomalies_per_check: int = 100  # 每次检查最大异常数
    
    # 统计检测配置
    z_score_threshold: float = 3.0  # Z分数阈值
    iqr_multiplier: float = 1.5  # IQR倍数
    percentile_threshold: float = 0.95  # 百分位阈值
    
    # 机器学习配置
    contamination_rate: float = 0.1  # 污染率
    n_estimators: int = 100  # 估计器数量
    random_state: int = 42  # 随机种子
    
    # 时间序列配置
    window_size: int = 30  # 滑动窗口大小
    seasonal_period: int = 7  # 季节性周期
    trend_threshold: float = 0.05  # 趋势阈值
    
    # 行为分析配置
    behavior_window_days: int = 30  # 行为分析窗口天数
    min_samples_for_pattern: int = 10  # 模式识别最小样本数
    
    # 性能配置
    parallel_processing: bool = True  # 并行处理
    max_workers: int = 4  # 最大工作线程数
    timeout_seconds: int = 300  # 超时时间
    
    # 缓存配置
    enable_caching: bool = True  # 启用缓存
    cache_ttl_minutes: int = 60  # 缓存生存时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sensitivity": self.sensitivity,
            "confidence_threshold": self.confidence_threshold,
            "max_anomalies_per_check": self.max_anomalies_per_check,
            "z_score_threshold": self.z_score_threshold,
            "iqr_multiplier": self.iqr_multiplier,
            "percentile_threshold": self.percentile_threshold,
            "contamination_rate": self.contamination_rate,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "window_size": self.window_size,
            "seasonal_period": self.seasonal_period,
            "trend_threshold": self.trend_threshold,
            "behavior_window_days": self.behavior_window_days,
            "min_samples_for_pattern": self.min_samples_for_pattern,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "timeout_seconds": self.timeout_seconds,
            "enable_caching": self.enable_caching,
            "cache_ttl_minutes": self.cache_ttl_minutes
        }


@dataclass
class AnomalyResult:
    """异常检测结果"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    confidence_score: float  # 置信度分数 (0-1)
    anomaly_score: float  # 异常分数
    
    # 基本信息
    title: str
    description: str
    affected_fields: List[str]
    detection_method: DetectionMethod
    
    # 时间信息
    detection_time: datetime
    anomaly_time_range: Optional[tuple] = None  # (start_time, end_time)
    
    # 数据信息
    original_value: Any = None
    expected_value: Any = None
    deviation: float = 0.0
    threshold_value: Any = None
    
    # 上下文信息
    context_data: Dict[str, Any] = field(default_factory=dict)
    related_anomalies: List[str] = field(default_factory=list)
    
    # 状态和处理
    status: AnomalyStatus = AnomalyStatus.DETECTED
    investigation_notes: str = ""
    resolution_action: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_critical(self) -> bool:
        """是否为严重异常"""
        return self.severity == AnomalySeverity.CRITICAL
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """是否为高置信度异常"""
        return self.confidence_score >= threshold
    
    def get_risk_level(self) -> str:
        """获取风险等级"""
        if self.severity == AnomalySeverity.CRITICAL:
            return "极高风险"
        elif self.severity == AnomalySeverity.HIGH:
            return "高风险"
        elif self.severity == AnomalySeverity.MEDIUM:
            return "中等风险"
        elif self.severity == AnomalySeverity.LOW:
            return "低风险"
        else:
            return "信息提示"


@dataclass
class AnomalyMetrics:
    """异常检测指标"""
    # 基础统计
    total_anomalies: int = 0
    critical_anomalies: int = 0
    high_anomalies: int = 0
    medium_anomalies: int = 0
    low_anomalies: int = 0
    info_anomalies: int = 0
    
    # 类型分布
    statistical_anomalies: int = 0
    behavioral_anomalies: int = 0
    temporal_anomalies: int = 0
    pattern_anomalies: int = 0
    outlier_anomalies: int = 0
    
    # 质量指标
    average_confidence: float = 0.0
    average_anomaly_score: float = 0.0
    detection_accuracy: float = 0.0
    false_positive_rate: float = 0.0
    
    # 性能指标
    detection_time_seconds: float = 0.0
    data_points_analyzed: int = 0
    processing_rate: float = 0.0  # 每秒处理的数据点数
    
    # 趋势指标
    anomaly_trend: str = "stable"  # stable, increasing, decreasing
    trend_change_percentage: float = 0.0
    
    def get_severity_distribution(self) -> Dict[str, int]:
        """获取严重程度分布"""
        return {
            "critical": self.critical_anomalies,
            "high": self.high_anomalies,
            "medium": self.medium_anomalies,
            "low": self.low_anomalies,
            "info": self.info_anomalies
        }
    
    def get_type_distribution(self) -> Dict[str, int]:
        """获取类型分布"""
        return {
            "statistical": self.statistical_anomalies,
            "behavioral": self.behavioral_anomalies,
            "temporal": self.temporal_anomalies,
            "pattern": self.pattern_anomalies,
            "outlier": self.outlier_anomalies
        }
    
    def calculate_risk_score(self) -> float:
        """计算综合风险分数"""
        if self.total_anomalies == 0:
            return 0.0
        
        # 加权计算风险分数
        weighted_score = (
            self.critical_anomalies * 1.0 +
            self.high_anomalies * 0.8 +
            self.medium_anomalies * 0.6 +
            self.low_anomalies * 0.4 +
            self.info_anomalies * 0.2
        )
        
        # 归一化到0-1范围
        max_possible_score = self.total_anomalies * 1.0
        return weighted_score / max_possible_score if max_possible_score > 0 else 0.0


@dataclass
class AnomalyReport:
    """异常检测报告"""
    report_id: str
    project_id: str
    detection_time: datetime
    detection_duration: timedelta
    
    # 检测结果
    anomalies: List[AnomalyResult]
    metrics: AnomalyMetrics
    
    # 配置信息
    detection_config: DetectionConfig
    patterns_used: List[AnomalyPattern]
    
    # 数据信息
    data_source: str
    data_time_range: tuple  # (start_time, end_time)
    data_quality_score: float = 1.0
    
    # 分析结果
    overall_risk_level: str = "低风险"
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_critical_anomalies(self) -> List[AnomalyResult]:
        """获取严重异常"""
        return [a for a in self.anomalies if a.severity == AnomalySeverity.CRITICAL]
    
    def get_high_confidence_anomalies(self, threshold: float = 0.8) -> List[AnomalyResult]:
        """获取高置信度异常"""
        return [a for a in self.anomalies if a.confidence_score >= threshold]
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[AnomalyResult]:
        """按类型获取异常"""
        return [a for a in self.anomalies if a.anomaly_type == anomaly_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取报告摘要"""
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "detection_time": self.detection_time.isoformat(),
            "total_anomalies": len(self.anomalies),
            "critical_count": len(self.get_critical_anomalies()),
            "high_confidence_count": len(self.get_high_confidence_anomalies()),
            "overall_risk_level": self.overall_risk_level,
            "average_confidence": self.metrics.average_confidence,
            "detection_duration_seconds": self.detection_duration.total_seconds(),
            "data_quality_score": self.data_quality_score
        }
    
    def export_summary_text(self) -> str:
        """导出文本摘要"""
        summary = f"""
异常检测报告摘要
==================

项目ID: {self.project_id}
检测时间: {self.detection_time.strftime('%Y-%m-%d %H:%M:%S')}
检测耗时: {self.detection_duration.total_seconds():.2f}秒

检测结果:
- 总异常数: {len(self.anomalies)}
- 严重异常: {self.metrics.critical_anomalies}
- 高风险异常: {self.metrics.high_anomalies}
- 中等异常: {self.metrics.medium_anomalies}
- 低风险异常: {self.metrics.low_anomalies}

风险评估:
- 整体风险等级: {self.overall_risk_level}
- 平均置信度: {self.metrics.average_confidence:.2%}
- 综合风险分数: {self.metrics.calculate_risk_score():.2%}

关键发现:
"""
        for i, finding in enumerate(self.key_findings, 1):
            summary += f"{i}. {finding}\n"
        
        if self.recommendations:
            summary += "\n建议措施:\n"
            for i, rec in enumerate(self.recommendations, 1):
                summary += f"{i}. {rec}\n"
        
        return summary


@dataclass
class AnomalyThreshold:
    """异常阈值配置"""
    field_name: str
    threshold_type: str  # "upper", "lower", "range", "percentage"
    threshold_value: Union[float, tuple]  # 单值或范围
    severity: AnomalySeverity
    description: str = ""
    enabled: bool = True
    
    def check_threshold(self, value: float) -> bool:
        """检查是否超过阈值"""
        if not self.enabled:
            return False
        
        if self.threshold_type == "upper":
            return value > self.threshold_value
        elif self.threshold_type == "lower":
            return value < self.threshold_value
        elif self.threshold_type == "range":
            min_val, max_val = self.threshold_value
            return value < min_val or value > max_val
        elif self.threshold_type == "percentage":
            # 百分比变化检查
            return abs(value) > self.threshold_value
        
        return False


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metadata": self.metadata
        }


@dataclass
class BehaviorProfile:
    """行为画像"""
    entity_id: str  # 实体ID（供应商、项目等）
    entity_type: str  # 实体类型
    profile_period: tuple  # 画像时间范围
    
    # 行为特征
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    statistical_features: Dict[str, float] = field(default_factory=dict)
    temporal_features: Dict[str, Any] = field(default_factory=dict)
    
    # 异常历史
    anomaly_history: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    
    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_risk_score(self, new_anomalies: List[AnomalyResult]):
        """更新风险分数"""
        if not new_anomalies:
            return
        
        # 基于新异常更新风险分数
        severity_weights = {
            AnomalySeverity.CRITICAL: 1.0,
            AnomalySeverity.HIGH: 0.8,
            AnomalySeverity.MEDIUM: 0.6,
            AnomalySeverity.LOW: 0.4,
            AnomalySeverity.INFO: 0.2
        }
        
        new_risk = sum(
            severity_weights.get(anomaly.severity, 0.0) * anomaly.confidence_score
            for anomaly in new_anomalies
        ) / len(new_anomalies)
        
        # 使用指数移动平均更新风险分数
        alpha = 0.3  # 平滑因子
        self.risk_score = alpha * new_risk + (1 - alpha) * self.risk_score
        self.last_updated = datetime.now()