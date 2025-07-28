"""合规性自动检查模块

本模块提供政府采购项目的合规性自动检查功能，包括：
- 法规符合性检查
- 程序合规性验证
- 文档规范性检查
- 内容完整性验证
"""

from .compliance_models import (
    ComplianceRule,
    ComplianceResult,
    ComplianceReport,
    ComplianceLevel,
    RuleCategory,
)

from .compliance_engine import ComplianceEngine
from .rule_loader import RuleLoader

__all__ = [
    "ComplianceRule",
    "ComplianceResult", 
    "ComplianceReport",
    "ComplianceLevel",
    "RuleCategory",
    "ComplianceEngine",
    "RuleLoader",
]