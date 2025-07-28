#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析引擎
政府采购项目智能分析服务

功能概述:
- 项目风险智能评估
- 合规性自动检查
- 异常模式识别
- 智能报告生成

主要模块:
- risk_assessment: 风险评估模块
- compliance_check: 合规检查模块
- anomaly_detection: 异常检测模块
- intelligent_reporting: 智能报告模块

作者: AI开发团队
创建时间: 2025-07-28
版本: 1.0.0
"""

from .main import AnalysisService, AnalysisRequest, AnalysisResponse, BatchAnalysisRequest, ReportGenerationRequest

# 风险评估模块
from .risk_assessment import (
    RiskAnalyzer, RiskAssessmentResult, RiskFactor, RiskLevel,
    RiskCategory, RiskMetrics, RiskThreshold, RiskScore
)

# 合规检查模块
from .compliance_check import (
    ComplianceEngine, ComplianceRule, ComplianceRuleSet,
    ComplianceResult, ComplianceStatus, ComplianceCategory,
    ComplianceMetrics, ComplianceReport
)

# 异常检测模块
from .anomaly_detection import (
    AnomalyDetector, AnomalyResult, AnomalyType, AnomalySeverity,
    AnomalyStatus, DetectionMethod, AnomalyPattern, DetectionConfig,
    AnomalyMetrics, AnomalyReport
)

# 智能报告模块
from .intelligent_reporting import (
    ReportGenerator, ReportRequest, ReportResult, ReportMetadata,
    ReportSection, ReportChart, ReportTemplate, ChartConfig,
    ReportStatus, ReportFormat, TemplateType, ChartType,
    ReportPriority, ReportDeliveryMethod
)

__version__ = "1.0.0"
__author__ = "AI开发团队"
__description__ = "政府采购项目智能分析引擎"

__all__ = [
    # 核心服务
    "AnalysisService",
    "AnalysisRequest",
    "AnalysisResponse",
    "BatchAnalysisRequest",
    "ReportGenerationRequest",
    
    # 风险评估
    "RiskAnalyzer",
    "RiskAssessmentResult",
    "RiskFactor",
    "RiskLevel",
    "RiskCategory",
    "RiskMetrics",
    "RiskThreshold",
    "RiskScore",
    
    # 合规检查
    "ComplianceEngine",
    "ComplianceRule",
    "ComplianceRuleSet",
    "ComplianceResult",
    "ComplianceStatus",
    "ComplianceCategory",
    "ComplianceMetrics",
    "ComplianceReport",
    
    # 异常检测
    "AnomalyDetector",
    "AnomalyResult",
    "AnomalyType",
    "AnomalySeverity",
    "AnomalyStatus",
    "DetectionMethod",
    "AnomalyPattern",
    "DetectionConfig",
    "AnomalyMetrics",
    "AnomalyReport",
    
    # 智能报告
    "ReportGenerator",
    "ReportRequest",
    "ReportResult",
    "ReportMetadata",
    "ReportSection",
    "ReportChart",
    "ReportTemplate",
    "ChartConfig",
    "ReportStatus",
    "ReportFormat",
    "TemplateType",
    "ChartType",
    "ReportPriority",
    "ReportDeliveryMethod"
]