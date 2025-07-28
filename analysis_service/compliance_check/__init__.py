# Compliance Check Module
# 合规检查模块 - 政府采购合规性验证

"""
合规检查模块

本模块提供政府采购项目的合规性检查功能，包括：
- 法规合规性验证
- 文档完整性检查
- 流程合规性审核
- 合规报告生成

主要组件：
- ComplianceChecker: 合规检查器
- ComplianceRule: 合规规则定义
- ComplianceReport: 合规报告
- DocumentValidator: 文档验证器
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "政府采购合规检查模块"

from .compliance_checker import ComplianceChecker
from .compliance_rules import ComplianceRule, ComplianceRuleSet, RuleCategory
from .compliance_models import (
    ComplianceResult,
    ComplianceStatus,
    ComplianceViolation,
    ComplianceReport
)
from .document_validator import DocumentValidator

__all__ = [
    'ComplianceChecker',
    'ComplianceRule',
    'ComplianceRuleSet', 
    'RuleCategory',
    'ComplianceResult',
    'ComplianceStatus',
    'ComplianceViolation',
    'ComplianceReport',
    'DocumentValidator'
]