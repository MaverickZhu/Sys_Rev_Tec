"""简化的风险评估服务模块

专为单机版项目审计系统设计，提供：
- 文档质量审计
- 合规性检查
- 完整性验证
- 一致性分析
"""

from .risk_models import (
    RiskLevel,
    AuditCategory,
    AuditResult,
    DocumentAudit,
    ProjectAudit,
    AuditConfig,
)

from .risk_calculator import SimpleRiskCalculator
from .risk_analyzer import SimpleRiskAnalyzer

__all__ = [
    # 审计模型
    "RiskLevel",
    "AuditCategory", 
    "AuditResult",
    "DocumentAudit",
    "ProjectAudit",
    "AuditConfig",
    
    # 审计服务
    "SimpleRiskCalculator",
    "SimpleRiskAnalyzer",
]