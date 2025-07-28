"""合规性检查数据模型

定义合规性检查相关的数据结构和枚举类型
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ComplianceLevel(str, Enum):
    """合规性等级"""
    COMPLIANT = "compliant"          # 合规
    WARNING = "warning"              # 警告
    VIOLATION = "violation"          # 违规
    CRITICAL = "critical"            # 严重违规


class RuleCategory(str, Enum):
    """规则类别"""
    LEGAL = "legal"                  # 法律法规
    PROCEDURE = "procedure"          # 程序规范
    DOCUMENT = "document"            # 文档规范
    CONTENT = "content"              # 内容要求
    FORMAT = "format"                # 格式要求
    APPROVAL = "approval"            # 审批流程


class ComplianceRule(BaseModel):
    """合规性规则"""
    rule_id: str = Field(description="规则ID")
    name: str = Field(description="规则名称")
    category: RuleCategory = Field(description="规则类别")
    description: str = Field(description="规则描述")
    
    # 检查条件
    required_keywords: List[str] = Field(default_factory=list, description="必须包含的关键词")
    forbidden_keywords: List[str] = Field(default_factory=list, description="禁止包含的关键词")
    required_fields: List[str] = Field(default_factory=list, description="必需字段")
    format_pattern: Optional[str] = Field(default=None, description="格式正则表达式")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="规则检查条件")
    
    # 规则配置
    severity: ComplianceLevel = Field(default=ComplianceLevel.WARNING, description="违规严重程度")
    weight: float = Field(default=1.0, ge=0, le=10, description="规则权重")
    enabled: bool = Field(default=True, description="是否启用")
    
    # 元数据
    legal_basis: Optional[str] = Field(default=None, description="法律依据")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ComplianceResult(BaseModel):
    """合规性检查结果"""
    rule_id: str = Field(description="规则ID")
    rule_name: str = Field(description="规则名称")
    category: RuleCategory = Field(description="规则类别")
    
    # 检查结果
    is_compliant: bool = Field(description="是否合规")
    compliance_level: ComplianceLevel = Field(description="合规等级")
    score: float = Field(ge=0, le=100, description="合规得分")
    
    # 详细信息
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    evidence: List[str] = Field(default_factory=list, description="证据/匹配内容")
    
    # 元数据
    checked_at: datetime = Field(default_factory=datetime.now)
    check_duration: float = Field(default=0.0, description="检查耗时(秒)")


class DocumentCompliance(BaseModel):
    """文档合规性报告"""
    document_id: str = Field(description="文档ID")
    document_name: str = Field(description="文档名称")
    document_type: Optional[str] = Field(default=None, description="文档类型")
    
    # 总体结果
    overall_compliance: ComplianceLevel = Field(description="总体合规等级")
    compliance_score: float = Field(ge=0, le=100, description="合规得分")
    
    # 详细结果
    rule_results: List[ComplianceResult] = Field(default_factory=list, description="规则检查结果")
    
    # 统计信息
    total_rules: int = Field(default=0, description="检查规则总数")
    passed_rules: int = Field(default=0, description="通过规则数")
    warning_rules: int = Field(default=0, description="警告规则数")
    violation_rules: int = Field(default=0, description="违规规则数")
    
    # 元数据
    checked_at: datetime = Field(default_factory=datetime.now)
    check_duration: float = Field(default=0.0, description="检查耗时(秒)")
    
    def update_statistics(self):
        """更新统计信息"""
        self.total_rules = len(self.rule_results)
        self.passed_rules = len([r for r in self.rule_results if r.is_compliant])
        self.warning_rules = len([r for r in self.rule_results if r.compliance_level == ComplianceLevel.WARNING])
        self.violation_rules = len([r for r in self.rule_results if r.compliance_level in [ComplianceLevel.VIOLATION, ComplianceLevel.CRITICAL]])


class ComplianceReport(BaseModel):
    """项目合规性报告"""
    project_id: str = Field(description="项目ID")
    project_name: str = Field(description="项目名称")
    
    # 总体结果
    overall_compliance: ComplianceLevel = Field(description="总体合规等级")
    compliance_score: float = Field(ge=0, le=100, description="合规得分")
    
    # 文档合规性
    document_reports: List[DocumentCompliance] = Field(default_factory=list, description="文档合规性报告")
    
    # 汇总统计
    total_documents: int = Field(default=0, description="文档总数")
    compliant_documents: int = Field(default=0, description="合规文档数")
    warning_documents: int = Field(default=0, description="警告文档数")
    violation_documents: int = Field(default=0, description="违规文档数")
    
    # 关键问题
    critical_issues: List[str] = Field(default_factory=list, description="关键问题")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    
    # 元数据
    generated_at: datetime = Field(default_factory=datetime.now)
    check_duration: float = Field(default=0.0, description="检查耗时(秒)")
    
    def update_statistics(self):
        """更新统计信息"""
        self.total_documents = len(self.document_reports)
        self.compliant_documents = len([d for d in self.document_reports if d.overall_compliance == ComplianceLevel.COMPLIANT])
        self.warning_documents = len([d for d in self.document_reports if d.overall_compliance == ComplianceLevel.WARNING])
        self.violation_documents = len([d for d in self.document_reports if d.overall_compliance in [ComplianceLevel.VIOLATION, ComplianceLevel.CRITICAL]])


class ComplianceConfig(BaseModel):
    """合规性检查配置"""
    # 规则配置
    rules_file_path: str = Field(default="rules/compliance_rules.json", description="规则文件路径")
    enable_all_categories: bool = Field(default=True, description="启用所有类别")
    enabled_categories: List[RuleCategory] = Field(default_factory=list, description="启用的类别")
    
    # 检查配置
    strict_mode: bool = Field(default=False, description="严格模式")
    auto_fix: bool = Field(default=False, description="自动修复")
    max_check_time: float = Field(default=30.0, description="最大检查时间(秒)")
    
    # 评分配置
    legal_weight: float = Field(default=0.4, description="法律法规权重")
    procedure_weight: float = Field(default=0.3, description="程序规范权重")
    document_weight: float = Field(default=0.2, description="文档规范权重")
    content_weight: float = Field(default=0.1, description="内容要求权重")
    
    # 阈值配置
    compliant_threshold: float = Field(default=90.0, description="合规阈值")
    warning_threshold: float = Field(default=70.0, description="警告阈值")
    violation_threshold: float = Field(default=50.0, description="违规阈值")