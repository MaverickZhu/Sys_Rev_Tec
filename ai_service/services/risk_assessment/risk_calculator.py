"""简化的风险计算器 - 适用于单机版项目审计系统"""

from typing import Dict, List
from datetime import datetime

from .risk_models import (
    AuditCategory,
    AuditResult,
    DocumentAudit,
    ProjectAudit,
    RiskLevel,
    AuditConfig,
)


class SimpleRiskCalculator:
    """简化的风险计算器"""
    
    def __init__(self, config: AuditConfig = None):
        """初始化计算器"""
        self.config = config or AuditConfig()
    
    def calculate_document_score(self, audit_results: List[AuditResult]) -> float:
        """计算文档总分"""
        if not audit_results:
            return 0.0
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for result in audit_results:
            weight = self._get_category_weight(result.category)
            weighted_score += result.score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def determine_risk_level(self, score: float) -> RiskLevel:
        """根据分数确定风险等级"""
        if score >= self.config.high_risk_threshold:
            return RiskLevel.HIGH
        elif score >= self.config.medium_risk_threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def calculate_project_score(self, document_audits: List[DocumentAudit]) -> float:
        """计算项目总分"""
        if not document_audits:
            return 0.0
        
        total_score = sum(doc.overall_score for doc in document_audits)
        return total_score / len(document_audits)
    
    def generate_audit_summary(self, audit_results: List[AuditResult]) -> str:
        """生成审计摘要"""
        if not audit_results:
            return "未发现明显问题"
        
        issues_count = sum(len(result.issues) for result in audit_results)
        high_risk_count = len([r for r in audit_results if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        
        if high_risk_count > 0:
            return f"发现 {high_risk_count} 个高风险项目，共 {issues_count} 个问题需要关注"
        elif issues_count > 0:
            return f"发现 {issues_count} 个问题，建议进行改进"
        else:
            return "文档质量良好，符合审计要求"
    
    def generate_project_recommendations(self, document_audits: List[DocumentAudit]) -> List[str]:
        """生成项目建议"""
        recommendations = []
        
        # 统计问题类型
        all_issues = []
        for doc in document_audits:
            for result in doc.audit_results:
                all_issues.extend(result.issues)
        
        # 高风险文档数量
        high_risk_docs = [d for d in document_audits if d.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        if high_risk_docs:
            recommendations.append(f"优先处理 {len(high_risk_docs)} 个高风险文档")
        
        # 常见问题建议
        if any("格式" in issue for issue in all_issues):
            recommendations.append("统一文档格式规范")
        
        if any("完整" in issue for issue in all_issues):
            recommendations.append("补充缺失的必要信息")
        
        if any("合规" in issue for issue in all_issues):
            recommendations.append("确保所有文档符合合规要求")
        
        if not recommendations:
            recommendations.append("继续保持良好的文档质量")
        
        return recommendations
    
    def _get_category_weight(self, category: AuditCategory) -> float:
        """获取类别权重"""
        weights = {
            AuditCategory.DOCUMENT_QUALITY: self.config.document_quality_weight,
            AuditCategory.COMPLIANCE: self.config.compliance_weight,
            AuditCategory.COMPLETENESS: self.config.completeness_weight,
            AuditCategory.CONSISTENCY: self.config.consistency_weight,
        }
        return weights.get(category, 0.1)
    
    def create_document_audit(
        self, 
        document_id: str, 
        document_name: str, 
        audit_results: List[AuditResult]
    ) -> DocumentAudit:
        """创建文档审计结果"""
        overall_score = self.calculate_document_score(audit_results)
        overall_risk = self.determine_risk_level(overall_score)
        summary = self.generate_audit_summary(audit_results)
        
        return DocumentAudit(
            document_id=document_id,
            document_name=document_name,
            overall_score=overall_score,
            overall_risk=overall_risk,
            audit_results=audit_results,
            summary=summary,
            audited_at=datetime.now()
        )
    
    def create_project_audit(
        self, 
        project_id: str, 
        project_name: str, 
        document_audits: List[DocumentAudit]
    ) -> ProjectAudit:
        """创建项目审计结果"""
        overall_score = self.calculate_project_score(document_audits)
        overall_risk = self.determine_risk_level(overall_score)
        recommendations = self.generate_project_recommendations(document_audits)
        
        # 生成项目摘要
        total_docs = len(document_audits)
        high_risk_docs = len([d for d in document_audits if d.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        
        if high_risk_docs > 0:
            summary = f"项目包含 {total_docs} 个文档，其中 {high_risk_docs} 个存在高风险"
        else:
            summary = f"项目包含 {total_docs} 个文档，整体质量良好"
        
        return ProjectAudit(
            project_id=project_id,
            project_name=project_name,
            overall_score=overall_score,
            overall_risk=overall_risk,
            document_audits=document_audits,
            summary=summary,
            recommendations=recommendations,
            audited_at=datetime.now()
        )