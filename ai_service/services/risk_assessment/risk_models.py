"""简化的风险评估数据模型 - 适用于单机版项目审计系统"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"          # 低风险
    MEDIUM = "medium"    # 中等风险
    HIGH = "high"        # 高风险
    CRITICAL = "critical" # 严重风险


class AuditCategory(str, Enum):
    """审计类别"""
    DOCUMENT_QUALITY = "document_quality"    # 文档质量
    COMPLIANCE = "compliance"                # 合规性
    COMPLETENESS = "completeness"            # 完整性
    CONSISTENCY = "consistency"              # 一致性


class AuditResult(BaseModel):
    """审计结果"""
    category: AuditCategory
    risk_level: RiskLevel
    score: float = Field(ge=0, le=100, description="评分(0-100)")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    checked_at: datetime = Field(default_factory=datetime.now)


class DocumentAudit(BaseModel):
    """文档审计结果"""
    document_id: str
    document_name: str
    overall_score: float = Field(ge=0, le=100)
    overall_risk: RiskLevel
    audit_results: List[AuditResult] = Field(default_factory=list)
    summary: str = ""
    audited_at: datetime = Field(default_factory=datetime.now)


class ProjectAudit(BaseModel):
    """项目审计结果"""
    project_id: str
    project_name: str
    overall_score: float = Field(ge=0, le=100)
    overall_risk: RiskLevel
    document_audits: List[DocumentAudit] = Field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = Field(default_factory=list)
    audited_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def total_documents(self) -> int:
        """文档总数"""
        return len(self.document_audits)
    
    @property
    def high_risk_documents(self) -> int:
        """高风险文档数量"""
        return len([d for d in self.document_audits if d.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]])


class AuditConfig(BaseModel):
    """审计配置"""
    # 评分权重
    document_quality_weight: float = 0.3
    compliance_weight: float = 0.4
    completeness_weight: float = 0.2
    consistency_weight: float = 0.1
    
    # 风险阈值
    high_risk_threshold: float = 70.0
    medium_risk_threshold: float = 40.0
    
    # 检查项目
    check_required_fields: bool = True
    check_file_formats: bool = True
    check_naming_conventions: bool = True
    check_content_completeness: bool = True