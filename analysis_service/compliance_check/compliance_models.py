# Compliance Models
# 合规检查数据模型 - 定义合规相关的数据结构

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ComplianceStatus(Enum):
    """合规状态枚举"""
    COMPLIANT = "合规"
    NON_COMPLIANT = "不合规"
    PARTIAL_COMPLIANT = "部分合规"
    PENDING_REVIEW = "待审核"
    UNKNOWN = "未知"
    
    @property
    def color(self) -> str:
        """获取状态对应的颜色"""
        color_map = {
            ComplianceStatus.COMPLIANT: "#28a745",        # 绿色
            ComplianceStatus.NON_COMPLIANT: "#dc3545",    # 红色
            ComplianceStatus.PARTIAL_COMPLIANT: "#ffc107", # 黄色
            ComplianceStatus.PENDING_REVIEW: "#6c757d",   # 灰色
            ComplianceStatus.UNKNOWN: "#17a2b8"          # 蓝色
        }
        return color_map[self]
    
    @property
    def priority(self) -> int:
        """获取状态优先级（数值越大优先级越高）"""
        priority_map = {
            ComplianceStatus.NON_COMPLIANT: 5,
            ComplianceStatus.PARTIAL_COMPLIANT: 4,
            ComplianceStatus.PENDING_REVIEW: 3,
            ComplianceStatus.UNKNOWN: 2,
            ComplianceStatus.COMPLIANT: 1
        }
        return priority_map[self]

class ViolationSeverity(Enum):
    """违规严重程度枚举"""
    CRITICAL = "严重"
    HIGH = "高"
    MEDIUM = "中等"
    LOW = "轻微"
    INFO = "提示"
    
    @property
    def score(self) -> float:
        """获取严重程度对应的评分"""
        score_map = {
            ViolationSeverity.CRITICAL: 1.0,
            ViolationSeverity.HIGH: 0.8,
            ViolationSeverity.MEDIUM: 0.6,
            ViolationSeverity.LOW: 0.4,
            ViolationSeverity.INFO: 0.2
        }
        return score_map[self]

class RuleCategory(Enum):
    """规则类别枚举"""
    PROCUREMENT_LAW = "采购法规"
    BUDGET_REGULATION = "预算规定"
    DOCUMENT_REQUIREMENT = "文档要求"
    PROCESS_COMPLIANCE = "流程合规"
    VENDOR_QUALIFICATION = "供应商资质"
    CONTRACT_TERMS = "合同条款"
    TRANSPARENCY = "透明度要求"
    ANTI_CORRUPTION = "反腐败规定"

@dataclass
class ComplianceViolation:
    """合规违规记录"""
    rule_id: str                           # 规则ID
    rule_name: str                         # 规则名称
    category: RuleCategory                 # 规则类别
    severity: ViolationSeverity            # 严重程度
    description: str                       # 违规描述
    evidence: Optional[Dict[str, Any]] = None  # 证据数据
    recommendation: Optional[str] = None       # 整改建议
    legal_reference: Optional[str] = None      # 法规依据
    detected_at: datetime = field(default_factory=datetime.now)
    
    @property
    def risk_score(self) -> float:
        """违规风险评分"""
        return self.severity.score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'category': self.category.value,
            'severity': self.severity.value,
            'description': self.description,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'legal_reference': self.legal_reference,
            'detected_at': self.detected_at.isoformat(),
            'risk_score': self.risk_score
        }

@dataclass
class ComplianceResult:
    """单项合规检查结果"""
    rule_id: str                           # 规则ID
    rule_name: str                         # 规则名称
    category: RuleCategory                 # 规则类别
    status: ComplianceStatus               # 合规状态
    score: float                           # 合规评分 (0-1)
    violations: List[ComplianceViolation] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    check_time: datetime = field(default_factory=datetime.now)
    
    @property
    def violation_count(self) -> int:
        """违规数量"""
        return len(self.violations)
    
    @property
    def critical_violations(self) -> List[ComplianceViolation]:
        """严重违规列表"""
        return [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
    
    @property
    def has_critical_violations(self) -> bool:
        """是否存在严重违规"""
        return len(self.critical_violations) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'category': self.category.value,
            'status': self.status.value,
            'score': self.score,
            'violation_count': self.violation_count,
            'violations': [v.to_dict() for v in self.violations],
            'passed_checks': self.passed_checks,
            'warnings': self.warnings,
            'check_time': self.check_time.isoformat(),
            'has_critical_violations': self.has_critical_violations
        }

@dataclass
class ComplianceReport:
    """合规检查报告"""
    project_id: str                        # 项目ID
    project_name: str                      # 项目名称
    check_date: datetime                   # 检查日期
    overall_status: ComplianceStatus       # 总体合规状态
    overall_score: float                   # 总体合规评分
    results: List[ComplianceResult]        # 检查结果列表
    summary: Dict[str, Any]                # 摘要信息
    checker_version: str                   # 检查器版本
    
    @property
    def total_violations(self) -> int:
        """总违规数量"""
        return sum(result.violation_count for result in self.results)
    
    @property
    def critical_violations(self) -> List[ComplianceViolation]:
        """所有严重违规"""
        violations = []
        for result in self.results:
            violations.extend(result.critical_violations)
        return violations
    
    @property
    def category_scores(self) -> Dict[str, float]:
        """各类别合规评分"""
        category_results = {}
        for result in self.results:
            category = result.category.value
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result.score)
        
        # 计算各类别平均分
        category_scores = {}
        for category, scores in category_results.items():
            category_scores[category] = sum(scores) / len(scores) if scores else 0.0
        
        return category_scores
    
    @property
    def compliance_rate(self) -> float:
        """合规率"""
        if not self.results:
            return 0.0
        
        compliant_count = sum(1 for result in self.results 
                            if result.status == ComplianceStatus.COMPLIANT)
        return compliant_count / len(self.results)
    
    def get_violations_by_severity(self, severity: ViolationSeverity) -> List[ComplianceViolation]:
        """按严重程度获取违规列表"""
        violations = []
        for result in self.results:
            violations.extend([v for v in result.violations if v.severity == severity])
        return violations
    
    def get_results_by_category(self, category: RuleCategory) -> List[ComplianceResult]:
        """按类别获取检查结果"""
        return [result for result in self.results if result.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'check_date': self.check_date.isoformat(),
            'overall_status': self.overall_status.value,
            'overall_score': self.overall_score,
            'total_violations': self.total_violations,
            'critical_violations_count': len(self.critical_violations),
            'compliance_rate': self.compliance_rate,
            'category_scores': self.category_scores,
            'results': [result.to_dict() for result in self.results],
            'summary': self.summary,
            'checker_version': self.checker_version
        }

@dataclass
class ComplianceMetrics:
    """合规指标统计"""
    total_projects: int
    compliant_projects: int
    non_compliant_projects: int
    partial_compliant_projects: int
    average_compliance_score: float
    total_violations: int
    critical_violations: int
    
    @property
    def compliance_rate(self) -> float:
        """总体合规率"""
        if self.total_projects == 0:
            return 0.0
        return self.compliant_projects / self.total_projects
    
    @property
    def violation_rate(self) -> float:
        """违规率"""
        if self.total_projects == 0:
            return 0.0
        return self.non_compliant_projects / self.total_projects
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'total_projects': self.total_projects,
            'compliant_projects': self.compliant_projects,
            'non_compliant_projects': self.non_compliant_projects,
            'partial_compliant_projects': self.partial_compliant_projects,
            'compliance_rate': self.compliance_rate,
            'violation_rate': self.violation_rate,
            'average_compliance_score': self.average_compliance_score,
            'total_violations': self.total_violations,
            'critical_violations': self.critical_violations
        }

@dataclass
class DocumentCheckResult:
    """文档检查结果"""
    document_type: str                     # 文档类型
    document_name: str                     # 文档名称
    is_present: bool                       # 是否存在
    is_valid: bool                         # 是否有效
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def status(self) -> ComplianceStatus:
        """文档合规状态"""
        if not self.is_present:
            return ComplianceStatus.NON_COMPLIANT
        elif not self.is_valid:
            return ComplianceStatus.PARTIAL_COMPLIANT
        elif self.warnings:
            return ComplianceStatus.PARTIAL_COMPLIANT
        else:
            return ComplianceStatus.COMPLIANT
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'document_type': self.document_type,
            'document_name': self.document_name,
            'is_present': self.is_present,
            'is_valid': self.is_valid,
            'status': self.status.value,
            'validation_errors': self.validation_errors,
            'warnings': self.warnings,
            'metadata': self.metadata
        }