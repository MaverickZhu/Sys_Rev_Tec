# Compliance Rules
# 合规规则定义 - 政府采购合规规则库

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

from .compliance_models import RuleCategory, ViolationSeverity, ComplianceStatus

logger = logging.getLogger(__name__)

@dataclass
class ComplianceRule:
    """合规规则定义"""
    rule_id: str                           # 规则唯一标识
    name: str                              # 规则名称
    category: RuleCategory                 # 规则类别
    description: str                       # 规则描述
    severity: ViolationSeverity            # 违规严重程度
    legal_reference: str                   # 法规依据
    check_function: Callable[[Dict], bool] # 检查函数
    error_message: str                     # 错误消息模板
    recommendation: str                    # 整改建议
    enabled: bool = True                   # 是否启用
    weight: float = 1.0                    # 权重
    tags: List[str] = field(default_factory=list)  # 标签
    created_at: datetime = field(default_factory=datetime.now)
    
    def check(self, project_data: Dict[str, Any]) -> bool:
        """执行规则检查
        
        Args:
            project_data: 项目数据
            
        Returns:
            bool: True表示合规，False表示违规
        """
        try:
            if not self.enabled:
                return True
            
            return self.check_function(project_data)
        except Exception as e:
            logger.error(f"规则{self.rule_id}检查失败: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'severity': self.severity.value,
            'legal_reference': self.legal_reference,
            'error_message': self.error_message,
            'recommendation': self.recommendation,
            'enabled': self.enabled,
            'weight': self.weight,
            'tags': self.tags,
            'created_at': self.created_at.isoformat()
        }

class ComplianceRuleSet:
    """合规规则集合"""
    
    def __init__(self):
        self.rules: Dict[str, ComplianceRule] = {}
        self._initialize_default_rules()
    
    def add_rule(self, rule: ComplianceRule) -> None:
        """添加规则"""
        self.rules[rule.rule_id] = rule
        logger.info(f"添加合规规则: {rule.rule_id} - {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除合规规则: {rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: RuleCategory) -> List[ComplianceRule]:
        """按类别获取规则"""
        return [rule for rule in self.rules.values() if rule.category == category]
    
    def get_enabled_rules(self) -> List[ComplianceRule]:
        """获取启用的规则"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def _initialize_default_rules(self) -> None:
        """初始化默认规则"""
        # 预算相关规则
        self._add_budget_rules()
        
        # 文档相关规则
        self._add_document_rules()
        
        # 流程相关规则
        self._add_process_rules()
        
        # 供应商相关规则
        self._add_vendor_rules()
        
        # 合同相关规则
        self._add_contract_rules()
        
        # 透明度相关规则
        self._add_transparency_rules()
    
    def _add_budget_rules(self) -> None:
        """添加预算相关规则"""
        
        # 预算审批规则
        budget_approval_rule = ComplianceRule(
            rule_id="BUDGET_001",
            name="预算审批文件完整性",
            category=RuleCategory.BUDGET_REGULATION,
            description="项目必须具备完整的预算审批文件",
            severity=ViolationSeverity.CRITICAL,
            legal_reference="《政府采购法》第七条",
            check_function=lambda data: 'budget_approval' in data.get('documents', []),
            error_message="缺少预算审批文件",
            recommendation="请提供完整的预算审批文件",
            tags=["预算", "审批", "文档"]
        )
        self.add_rule(budget_approval_rule)
        
        # 预算金额合理性规则
        budget_amount_rule = ComplianceRule(
            rule_id="BUDGET_002",
            name="预算金额合理性",
            category=RuleCategory.BUDGET_REGULATION,
            description="项目预算金额必须在合理范围内",
            severity=ViolationSeverity.HIGH,
            legal_reference="《政府采购法实施条例》第十五条",
            check_function=lambda data: self._check_budget_reasonableness(data),
            error_message="预算金额超出合理范围",
            recommendation="请重新评估项目预算的合理性",
            tags=["预算", "金额", "合理性"]
        )
        self.add_rule(budget_amount_rule)
    
    def _add_document_rules(self) -> None:
        """添加文档相关规则"""
        
        # 采购计划规则
        procurement_plan_rule = ComplianceRule(
            rule_id="DOC_001",
            name="采购计划完整性",
            category=RuleCategory.DOCUMENT_REQUIREMENT,
            description="必须提供完整的采购计划文件",
            severity=ViolationSeverity.CRITICAL,
            legal_reference="《政府采购法》第七条",
            check_function=lambda data: 'procurement_plan' in data.get('documents', []),
            error_message="缺少采购计划文件",
            recommendation="请提供完整的采购计划文件",
            tags=["文档", "采购计划"]
        )
        self.add_rule(procurement_plan_rule)
        
        # 技术规格书规则
        tech_specs_rule = ComplianceRule(
            rule_id="DOC_002",
            name="技术规格书完整性",
            category=RuleCategory.DOCUMENT_REQUIREMENT,
            description="技术类项目必须提供详细的技术规格书",
            severity=ViolationSeverity.HIGH,
            legal_reference="《政府采购货物和服务招标投标管理办法》第十七条",
            check_function=lambda data: self._check_tech_specs(data),
            error_message="技术类项目缺少技术规格书",
            recommendation="请提供详细的技术规格书",
            tags=["文档", "技术规格"]
        )
        self.add_rule(tech_specs_rule)
    
    def _add_process_rules(self) -> None:
        """添加流程相关规则"""
        
        # 公开招标门槛规则
        public_bidding_threshold_rule = ComplianceRule(
            rule_id="PROC_001",
            name="公开招标门槛要求",
            category=RuleCategory.PROCESS_COMPLIANCE,
            description="达到公开招标门槛的项目必须采用公开招标方式",
            severity=ViolationSeverity.CRITICAL,
            legal_reference="《政府采购法》第二十六条",
            check_function=lambda data: self._check_public_bidding_threshold(data),
            error_message="项目金额达到公开招标门槛但未采用公开招标",
            recommendation="请采用公开招标方式进行采购",
            tags=["流程", "公开招标", "门槛"]
        )
        self.add_rule(public_bidding_threshold_rule)
        
        # 采购方式合规性规则
        procurement_method_rule = ComplianceRule(
            rule_id="PROC_002",
            name="采购方式合规性",
            category=RuleCategory.PROCESS_COMPLIANCE,
            description="采购方式必须符合法规要求",
            severity=ViolationSeverity.HIGH,
            legal_reference="《政府采购法》第二十六条至第三十一条",
            check_function=lambda data: self._check_procurement_method(data),
            error_message="采购方式不符合法规要求",
            recommendation="请选择符合法规要求的采购方式",
            tags=["流程", "采购方式"]
        )
        self.add_rule(procurement_method_rule)
    
    def _add_vendor_rules(self) -> None:
        """添加供应商相关规则"""
        
        # 供应商资质规则
        vendor_qualification_rule = ComplianceRule(
            rule_id="VENDOR_001",
            name="供应商资质要求",
            category=RuleCategory.VENDOR_QUALIFICATION,
            description="参与投标的供应商必须具备相应资质",
            severity=ViolationSeverity.HIGH,
            legal_reference="《政府采购法》第二十二条",
            check_function=lambda data: self._check_vendor_qualifications(data),
            error_message="供应商资质不符合要求",
            recommendation="请确保所有供应商具备相应资质",
            tags=["供应商", "资质"]
        )
        self.add_rule(vendor_qualification_rule)
        
        # 供应商数量规则
        vendor_count_rule = ComplianceRule(
            rule_id="VENDOR_002",
            name="供应商数量要求",
            category=RuleCategory.VENDOR_QUALIFICATION,
            description="投标供应商数量必须满足最低要求",
            severity=ViolationSeverity.MEDIUM,
            legal_reference="《政府采购货物和服务招标投标管理办法》第四十三条",
            check_function=lambda data: self._check_vendor_count(data),
            error_message="投标供应商数量不足",
            recommendation="请确保有足够数量的合格供应商参与投标",
            tags=["供应商", "数量"]
        )
        self.add_rule(vendor_count_rule)
    
    def _add_contract_rules(self) -> None:
        """添加合同相关规则"""
        
        # 合同条款完整性规则
        contract_terms_rule = ComplianceRule(
            rule_id="CONTRACT_001",
            name="合同条款完整性",
            category=RuleCategory.CONTRACT_TERMS,
            description="政府采购合同必须包含法定条款",
            severity=ViolationSeverity.HIGH,
            legal_reference="《政府采购法》第四十三条",
            check_function=lambda data: self._check_contract_terms(data),
            error_message="合同缺少必要条款",
            recommendation="请补充完善合同条款",
            tags=["合同", "条款"]
        )
        self.add_rule(contract_terms_rule)
    
    def _add_transparency_rules(self) -> None:
        """添加透明度相关规则"""
        
        # 信息公开规则
        info_disclosure_rule = ComplianceRule(
            rule_id="TRANS_001",
            name="采购信息公开",
            category=RuleCategory.TRANSPARENCY,
            description="采购信息必须按规定公开",
            severity=ViolationSeverity.MEDIUM,
            legal_reference="《政府采购法》第十三条",
            check_function=lambda data: self._check_info_disclosure(data),
            error_message="采购信息未按规定公开",
            recommendation="请按规定公开采购信息",
            tags=["透明度", "信息公开"]
        )
        self.add_rule(info_disclosure_rule)
    
    # 检查函数实现
    def _check_budget_reasonableness(self, data: Dict[str, Any]) -> bool:
        """检查预算合理性"""
        budget = data.get('budget', 0)
        project_type = data.get('project_type', '').lower()
        
        # 简化的预算合理性检查
        if budget <= 0:
            return False
        
        # 基于项目类型的预算上限（示例）
        budget_limits = {
            'software': 10000000,  # 1000万
            'hardware': 5000000,   # 500万
            'service': 2000000,    # 200万
            'construction': 50000000  # 5000万
        }
        
        for ptype, limit in budget_limits.items():
            if ptype in project_type and budget > limit:
                return False
        
        return True
    
    def _check_tech_specs(self, data: Dict[str, Any]) -> bool:
        """检查技术规格书"""
        project_type = data.get('project_type', '').lower()
        documents = data.get('documents', [])
        
        # 技术类项目需要技术规格书
        tech_types = ['software', 'hardware', 'it', 'system']
        is_tech_project = any(ttype in project_type for ttype in tech_types)
        
        if is_tech_project:
            return 'technical_specs' in documents
        
        return True
    
    def _check_public_bidding_threshold(self, data: Dict[str, Any]) -> bool:
        """检查公开招标门槛"""
        budget = data.get('budget', 0)
        procurement_method = data.get('procurement_method', '').lower()
        
        # 简化的公开招标门槛（实际应根据最新法规）
        public_bidding_threshold = 2000000  # 200万
        
        if budget >= public_bidding_threshold:
            return 'public' in procurement_method or '公开' in procurement_method
        
        return True
    
    def _check_procurement_method(self, data: Dict[str, Any]) -> bool:
        """检查采购方式"""
        procurement_method = data.get('procurement_method', '')
        budget = data.get('budget', 0)
        
        # 检查采购方式是否为空
        if not procurement_method:
            return False
        
        # 检查采购方式是否合规（简化检查）
        valid_methods = ['公开招标', '邀请招标', '竞争性谈判', '单一来源', '询价']
        return any(method in procurement_method for method in valid_methods)
    
    def _check_vendor_qualifications(self, data: Dict[str, Any]) -> bool:
        """检查供应商资质"""
        vendors = data.get('vendors', [])
        
        if not vendors:
            return False
        
        # 检查是否所有供应商都有资质信息
        for vendor in vendors:
            if not vendor.get('qualified', False):
                return False
        
        return True
    
    def _check_vendor_count(self, data: Dict[str, Any]) -> bool:
        """检查供应商数量"""
        vendors = data.get('vendors', [])
        procurement_method = data.get('procurement_method', '').lower()
        
        # 根据采购方式确定最低供应商数量
        min_vendor_counts = {
            '公开招标': 3,
            '邀请招标': 3,
            '竞争性谈判': 3,
            '询价': 3,
            '单一来源': 1
        }
        
        for method, min_count in min_vendor_counts.items():
            if method in procurement_method:
                return len(vendors) >= min_count
        
        return len(vendors) >= 3  # 默认最少3家
    
    def _check_contract_terms(self, data: Dict[str, Any]) -> bool:
        """检查合同条款"""
        contract = data.get('contract', {})
        
        # 检查必要的合同条款
        required_terms = [
            'delivery_terms',    # 交付条款
            'payment_terms',     # 付款条款
            'quality_terms',     # 质量条款
            'liability_terms'    # 责任条款
        ]
        
        for term in required_terms:
            if term not in contract:
                return False
        
        return True
    
    def _check_info_disclosure(self, data: Dict[str, Any]) -> bool:
        """检查信息公开"""
        disclosure = data.get('info_disclosure', {})
        
        # 检查是否公开了必要信息
        required_disclosures = [
            'procurement_notice',  # 采购公告
            'bidding_documents',   # 招标文件
            'result_announcement'  # 结果公告
        ]
        
        for disclosure_type in required_disclosures:
            if not disclosure.get(disclosure_type, False):
                return False
        
        return True
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """获取规则摘要"""
        total_rules = len(self.rules)
        enabled_rules = len(self.get_enabled_rules())
        
        # 按类别统计
        category_counts = {}
        for rule in self.rules.values():
            category = rule.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 按严重程度统计
        severity_counts = {}
        for rule in self.rules.values():
            severity = rule.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'category_distribution': category_counts,
            'severity_distribution': severity_counts
        }