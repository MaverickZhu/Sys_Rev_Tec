#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报告生成模块
政府采购项目智能报告生成系统

功能概述:
- 自动化报告生成
- 多格式报告导出
- 智能数据可视化
- 报告模板管理
- 个性化报告定制

主要组件:
- ReportGenerator: 报告生成器
- ReportTemplate: 报告模板
- DataVisualizer: 数据可视化
- ReportExporter: 报告导出器
- ReportScheduler: 报告调度器

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

from .report_generator import ReportGenerator
from .report_models import (
    ReportRequest, ReportResult, ReportMetadata, ReportSection,
    ReportChart, ReportTemplate, ChartConfig, ReportStatus,
    ReportFormat, TemplateType, ChartType, ReportPriority,
    ReportDeliveryMethod
)

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "政府采购项目智能报告生成系统"

__all__ = [
    # 核心组件
    "ReportGenerator",
    
    # 数据模型
    "ReportRequest",
    "ReportResult",
    "ReportMetadata",
    "ReportSection",
    "ReportChart",
    "ReportTemplate",
    "ChartConfig",
    
    # 枚举类型
    "TemplateType",
    "ChartType",
    "ReportFormat",
    "ReportStatus",
    "ReportPriority",
    "ReportDeliveryMethod"
]