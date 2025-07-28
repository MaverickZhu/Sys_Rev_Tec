"""简化的风险分析器 - 适用于单机版项目审计系统"""

import re
from typing import Dict, List, Optional
from datetime import datetime

from .risk_models import (
    AuditCategory,
    AuditResult,
    DocumentAudit,
    ProjectAudit,
    RiskLevel,
    AuditConfig,
)
from .risk_calculator import SimpleRiskCalculator


class SimpleRiskAnalyzer:
    """简化的风险分析器"""
    
    def __init__(self, config: AuditConfig = None):
        """初始化分析器"""
        self.config = config or AuditConfig()
        self.calculator = SimpleRiskCalculator(self.config)
        self._init_check_rules()
    
    def _init_check_rules(self):
        """初始化检查规则"""
        # 必需字段检查
        self.required_fields = {
            "项目名称", "项目编号", "预算金额", "开始时间", "结束时间",
            "负责人", "联系方式", "项目描述", "采购方式"
        }
        
        # 文件格式检查
        self.allowed_formats = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
        
        # 命名规范检查
        self.naming_patterns = {
            "项目计划书": r".*计划.*\.(pdf|doc|docx)$",
            "预算表": r".*预算.*\.(xls|xlsx)$",
            "合同文件": r".*合同.*\.(pdf|doc|docx)$",
        }
        
        # 合规性关键词
        self.compliance_keywords = {
            "必须包含": ["法律依据", "审批流程", "监督机制", "验收标准"],
            "禁止包含": ["内定", "指定供应商", "排他性条款"],
        }
    
    def analyze_document(self, document_data: Dict) -> DocumentAudit:
        """分析单个文档"""
        document_id = document_data.get("id", "")
        document_name = document_data.get("name", "")
        
        audit_results = []
        
        # 文档质量检查
        if self.config.check_required_fields:
            quality_result = self._check_document_quality(document_data)
            audit_results.append(quality_result)
        
        # 合规性检查
        compliance_result = self._check_compliance(document_data)
        audit_results.append(compliance_result)
        
        # 完整性检查
        if self.config.check_content_completeness:
            completeness_result = self._check_completeness(document_data)
            audit_results.append(completeness_result)
        
        # 一致性检查
        consistency_result = self._check_consistency(document_data)
        audit_results.append(consistency_result)
        
        return self.calculator.create_document_audit(
            document_id, document_name, audit_results
        )
    
    def analyze_project(self, project_data: Dict, documents_data: List[Dict]) -> ProjectAudit:
        """分析整个项目"""
        project_id = project_data.get("id", "")
        project_name = project_data.get("name", "")
        
        # 分析所有文档
        document_audits = []
        for doc_data in documents_data:
            doc_audit = self.analyze_document(doc_data)
            document_audits.append(doc_audit)
        
        return self.calculator.create_project_audit(
            project_id, project_name, document_audits
        )
    
    def _check_document_quality(self, document_data: Dict) -> AuditResult:
        """检查文档质量"""
        issues = []
        suggestions = []
        score = 100.0
        
        # 检查文件格式
        if self.config.check_file_formats:
            file_path = document_data.get("file_path", "")
            if file_path:
                file_ext = "." + file_path.split(".")[-1].lower() if "." in file_path else ""
                if file_ext not in self.allowed_formats:
                    issues.append(f"文件格式不符合要求: {file_ext}")
                    suggestions.append(f"请使用标准格式: {', '.join(self.allowed_formats)}")
                    score -= 20
        
        # 检查命名规范
        if self.config.check_naming_conventions:
            file_name = document_data.get("name", "")
            doc_type = document_data.get("type", "")
            
            if doc_type in self.naming_patterns:
                pattern = self.naming_patterns[doc_type]
                if not re.match(pattern, file_name, re.IGNORECASE):
                    issues.append(f"文件命名不符合规范: {file_name}")
                    suggestions.append(f"建议按照规范命名: {doc_type}相关文件")
                    score -= 15
        
        # 检查文件大小
        file_size = document_data.get("size", 0)
        if file_size == 0:
            issues.append("文件为空或无法读取")
            suggestions.append("请检查文件是否损坏")
            score -= 30
        elif file_size > 50 * 1024 * 1024:  # 50MB
            issues.append("文件过大，可能影响处理效率")
            suggestions.append("建议压缩文件或分割为多个文件")
            score -= 10
        
        # 确保评分不低于0
        score = max(0.0, score)
        risk_level = self.calculator.determine_risk_level(100 - score)
        
        return AuditResult(
            category=AuditCategory.DOCUMENT_QUALITY,
            risk_level=risk_level,
            score=score,
            issues=issues,
            suggestions=suggestions,
            checked_at=datetime.now()
        )
    
    def _check_compliance(self, document_data: Dict) -> AuditResult:
        """检查合规性"""
        issues = []
        suggestions = []
        score = 100.0
        
        content = document_data.get("content", "")
        
        # 检查必须包含的关键词
        missing_keywords = []
        for keyword in self.compliance_keywords["必须包含"]:
            if keyword not in content:
                missing_keywords.append(keyword)
        
        if missing_keywords:
            issues.append(f"缺少必要的合规性内容: {', '.join(missing_keywords)}")
            suggestions.append("请补充相关合规性说明")
            score -= len(missing_keywords) * 15
        
        # 检查禁止包含的关键词
        forbidden_found = []
        for keyword in self.compliance_keywords["禁止包含"]:
            if keyword in content:
                forbidden_found.append(keyword)
        
        if forbidden_found:
            issues.append(f"包含不合规内容: {', '.join(forbidden_found)}")
            suggestions.append("请移除或修改相关内容以确保合规")
            score -= len(forbidden_found) * 25
        
        # 检查是否有审批信息
        approval_keywords = ["审批", "批准", "签字", "盖章"]
        has_approval = any(keyword in content for keyword in approval_keywords)
        if not has_approval:
            issues.append("未发现审批相关信息")
            suggestions.append("请确保文档包含必要的审批流程")
            score -= 20
        
        # 确保评分不低于0
        score = max(0.0, score)
        risk_level = self.calculator.determine_risk_level(100 - score)
        
        return AuditResult(
            category=AuditCategory.COMPLIANCE,
            risk_level=risk_level,
            score=score,
            issues=issues,
            suggestions=suggestions,
            checked_at=datetime.now()
        )
    
    def _check_completeness(self, document_data: Dict) -> AuditResult:
        """检查完整性"""
        issues = []
        suggestions = []
        score = 100.0
        
        # 检查必需字段
        missing_fields = []
        for field in self.required_fields:
            if field not in document_data or not document_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            issues.append(f"缺少必需字段: {', '.join(missing_fields)}")
            suggestions.append("请补充所有必需的项目信息")
            score -= len(missing_fields) * 10
        
        # 检查内容长度
        content = document_data.get("content", "")
        if len(content) < 100:
            issues.append("文档内容过于简短")
            suggestions.append("请提供更详细的项目描述")
            score -= 20
        
        # 检查是否有联系信息
        contact_keywords = ["电话", "邮箱", "地址", "联系人"]
        has_contact = any(keyword in content for keyword in contact_keywords)
        if not has_contact:
            issues.append("缺少联系信息")
            suggestions.append("请提供完整的联系方式")
            score -= 15
        
        # 确保评分不低于0
        score = max(0.0, score)
        risk_level = self.calculator.determine_risk_level(100 - score)
        
        return AuditResult(
            category=AuditCategory.COMPLETENESS,
            risk_level=risk_level,
            score=score,
            issues=issues,
            suggestions=suggestions,
            checked_at=datetime.now()
        )
    
    def _check_consistency(self, document_data: Dict) -> AuditResult:
        """检查一致性"""
        issues = []
        suggestions = []
        score = 100.0
        
        # 检查日期一致性
        start_date = document_data.get("start_date")
        end_date = document_data.get("end_date")
        
        if start_date and end_date:
            try:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                if start_date >= end_date:
                    issues.append("开始时间不能晚于或等于结束时间")
                    suggestions.append("请检查并修正项目时间安排")
                    score -= 25
            except (ValueError, TypeError):
                issues.append("日期格式不正确")
                suggestions.append("请使用标准日期格式")
                score -= 15
        
        # 检查金额格式
        budget = document_data.get("budget")
        if budget:
            try:
                budget_value = float(str(budget).replace(',', '').replace('￥', '').replace('元', ''))
                if budget_value <= 0:
                    issues.append("预算金额必须大于0")
                    suggestions.append("请输入有效的预算金额")
                    score -= 20
            except (ValueError, TypeError):
                issues.append("预算金额格式不正确")
                suggestions.append("请使用数字格式输入预算")
                score -= 15
        
        # 检查项目编号格式
        project_code = document_data.get("project_code", "")
        if project_code and not re.match(r'^[A-Z0-9-]+$', project_code):
            issues.append("项目编号格式不规范")
            suggestions.append("建议使用大写字母、数字和连字符")
            score -= 10
        
        # 确保评分不低于0
        score = max(0.0, score)
        risk_level = self.calculator.determine_risk_level(100 - score)
        
        return AuditResult(
            category=AuditCategory.CONSISTENCY,
            risk_level=risk_level,
            score=score,
            issues=issues,
            suggestions=suggestions,
            checked_at=datetime.now()
        )
    
    def get_audit_summary(self, project_audit: ProjectAudit) -> Dict:
        """获取审计摘要"""
        return {
            "project_name": project_audit.project_name,
            "overall_score": project_audit.overall_score,
            "overall_risk": project_audit.overall_risk.value,
            "total_documents": project_audit.total_documents,
            "high_risk_documents": project_audit.high_risk_documents,
            "recommendations": project_audit.recommendations,
            "summary": project_audit.summary,
            "audited_at": project_audit.audited_at.isoformat(),
        }