#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测模块
政府采购项目异常模式识别和检测

本模块提供:
- 异常模式识别
- 统计异常检测
- 行为异常分析
- 时间序列异常检测
- 异常评分和报告

主要组件:
- AnomalyDetector: 核心异常检测器
- AnomalyModels: 异常检测数据模型
- StatisticalDetector: 统计异常检测器
- BehaviorAnalyzer: 行为异常分析器
- TimeSeriesDetector: 时间序列异常检测器

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

from .anomaly_detector import AnomalyDetector
from .anomaly_models import (
    AnomalyType, AnomalySeverity, AnomalyStatus,
    AnomalyResult, AnomalyReport, AnomalyPattern,
    AnomalyMetrics, DetectionConfig
)
from .statistical_detector import StatisticalDetector
from .behavior_analyzer import BehaviorAnalyzer
from .timeseries_detector import TimeSeriesDetector

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "政府采购项目异常检测模块"

__all__ = [
    "AnomalyDetector",
    "AnomalyType", "AnomalySeverity", "AnomalyStatus",
    "AnomalyResult", "AnomalyReport", "AnomalyPattern",
    "AnomalyMetrics", "DetectionConfig",
    "StatisticalDetector",
    "BehaviorAnalyzer",
    "TimeSeriesDetector"
]