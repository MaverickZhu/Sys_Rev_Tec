#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规性规则引擎

实现可配置的合规性检查规则引擎，支持多种规则类型和检查逻辑。
"""

import re
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime

from compliance_models import (
    ComplianceRule, ComplianceResult, ComplianceLevel,
    RuleCategory, DocumentCompliance
)


class RuleEngine:
    """合规性规则引擎"""
    
    def __init__(self, rules_config_path: Optional[str] = None):
        self.rules: List[ComplianceRule] = []
        self.rule_categories: Dict[RuleCategory, List[ComplianceRule]] = {
            category: [] for category in RuleCategory
        }
        
        if rules_config_path:
            self.load_rules_from_file(rules_config_path)
        else:
            self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认合规性规则"""
        default_rules = [
            # 法规合规规则
            ComplianceRule(
                rule_id="REG_001",
                name="必需审批信息检查",
                description="检查文档是否包含必需的审批信息",
                category=RuleCategory.LEGAL,
                required_keywords=["审批", "批准", "签字", "盖章"],
                weight=3.0,
                severity=ComplianceLevel.VIOLATION
            ),
            ComplianceRule(
                rule_id="REG_002",
                name="禁用词汇检查",
                description="检查文档是否包含禁用的敏感词汇",
                category=RuleCategory.LEGAL,
                forbidden_keywords=["机密", "内部", "保密", "限制"],
                weight=4.0,
                severity=ComplianceLevel.CRITICAL
            ),
            
            # 程序合规规则
            ComplianceRule(
                rule_id="PROC_001",
                name="文档格式规范检查",
                description="检查文档格式是否符合标准",
                category=RuleCategory.PROCEDURE,
                weight=2.0,
                severity=ComplianceLevel.WARNING
            ),
            ComplianceRule(
                rule_id="PROC_002",
                name="文档命名规范检查",
                description="检查文档命名是否符合规范",
                category=RuleCategory.PROCEDURE,
                format_pattern=r"^[A-Z]{2,4}_\d{4}_\w+\.(pdf|doc|docx)$",
                weight=1.5,
                severity=ComplianceLevel.WARNING
            ),
            
            # 内容规范规则
            ComplianceRule(
                rule_id="CONT_001",
                name="必需字段完整性检查",
                description="检查文档是否包含所有必需字段",
                category=RuleCategory.CONTENT,
                required_fields=["项目名称", "负责人", "日期", "联系方式"],
                weight=2.5,
                severity=ComplianceLevel.VIOLATION
            ),
            ComplianceRule(
                rule_id="CONT_002",
                name="日期格式一致性检查",
                description="检查文档中日期格式的一致性",
                category=RuleCategory.CONTENT,
                format_pattern=r"\d{4}-\d{2}-\d{2}",
                weight=1.0,
                severity=ComplianceLevel.WARNING
            ),
            
            # 质量保证规则
            ComplianceRule(
                rule_id="QA_001",
                name="文档版本控制检查",
                description="检查文档是否有适当的版本控制信息",
                category=RuleCategory.DOCUMENT,
                required_keywords=["版本", "V", "v", "版"],
                weight=1.5,
                severity=ComplianceLevel.WARNING
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: ComplianceRule):
        """添加合规性规则"""
        self.rules.append(rule)
        self.rule_categories[rule.category].append(rule)
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除合规性规则"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                category = rule.category
                self.rules.pop(i)
                self.rule_categories[category] = [
                    r for r in self.rule_categories[category] if r.rule_id != rule_id
                ]
                return True
        return False
    
    def get_rules_by_category(self, category: RuleCategory) -> List[ComplianceRule]:
        """获取指定类别的规则"""
        return self.rule_categories[category]
    
    def get_rules(self) -> List[ComplianceRule]:
        """获取所有规则"""
        return self.rules
    
    def check_document_compliance(self, document_content: str, 
                                document_metadata: Dict[str, Any]) -> DocumentCompliance:
        """检查文档合规性"""
        results = []
        total_score = 0.0
        total_weight = 0.0
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            result = self._apply_rule(rule, document_content, document_metadata)
            results.append(result)
            
            # 计算加权分数
            weighted_score = result.score * rule.weight
            total_score += weighted_score
            total_weight += rule.weight
        
        # 计算最终分数
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        final_score = max(0.0, min(100.0, final_score))
        compliance_level = self._calculate_compliance_level(final_score)
        
        # 更新统计信息
        document_compliance = DocumentCompliance(
            document_id=document_metadata.get("id", "unknown"),
            document_name=document_metadata.get("name", "未知文档"),
            document_type=document_metadata.get("type", None),
            overall_compliance=compliance_level,
            compliance_score=final_score,
            rule_results=results
        )
        
        document_compliance.update_statistics()
        return document_compliance
    
    def _apply_rule(self, rule: ComplianceRule, content: str, 
                   metadata: Dict[str, Any]) -> ComplianceResult:
        """应用单个规则"""
        try:
            issues = []
            suggestions = []
            evidence = []
            
            # 检查必需关键词
            if rule.required_keywords:
                missing_keywords = []
                found_keywords = []
                for keyword in rule.required_keywords:
                    if keyword in content:
                        found_keywords.append(keyword)
                        evidence.append(f"找到关键词: {keyword}")
                    else:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    issues.append(f"缺少必需关键词: {', '.join(missing_keywords)}")
                    suggestions.append(f"请确保文档包含关键词: {', '.join(missing_keywords)}")
            
            # 检查禁用关键词
            if rule.forbidden_keywords:
                found_forbidden = []
                for keyword in rule.forbidden_keywords:
                    if keyword in content:
                        found_forbidden.append(keyword)
                        evidence.append(f"发现禁用关键词: {keyword}")
                
                if found_forbidden:
                    issues.append(f"发现禁用关键词: {', '.join(found_forbidden)}")
                    suggestions.append("请移除或替换禁用的关键词")
            
            # 检查必需字段
            if rule.required_fields:
                missing_fields = []
                for field in rule.required_fields:
                    if field not in content:
                        missing_fields.append(field)
                
                if missing_fields:
                    issues.append(f"缺少必需字段: {', '.join(missing_fields)}")
                    suggestions.append(f"请添加缺少的字段: {', '.join(missing_fields)}")
            
            # 检查格式模式
            if rule.format_pattern:
                if not re.search(rule.format_pattern, content):
                    issues.append("内容格式不符合要求")
                    suggestions.append("请检查内容格式是否符合规范")
                else:
                    evidence.append("格式检查通过")
            
            is_compliant = len(issues) == 0
            score = 100.0 if is_compliant else max(0.0, 100.0 - len(issues) * 20)
            
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                is_compliant=is_compliant,
                compliance_level=rule.severity if not is_compliant else ComplianceLevel.COMPLIANT,
                score=score,
                issues=issues,
                suggestions=suggestions,
                evidence=evidence
            )
            
        except Exception as e:
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                is_compliant=False,
                compliance_level=ComplianceLevel.CRITICAL,
                score=0.0,
                issues=[f"规则执行错误: {str(e)}"],
                suggestions=["请检查规则配置和输入数据"],
                evidence=[]
            )
    
    def _check_keyword_rule(self, rule: ComplianceRule, content: str) -> ComplianceResult:
        """检查关键词规则"""
        conditions = rule.conditions
        issues = []
        recommendations = []
        
        # 检查必需关键词
        if "required_keywords" in conditions:
            required = conditions["required_keywords"]
            min_matches = conditions.get("min_matches", 1)
            
            matches = sum(1 for keyword in required if keyword in content)
            if matches < min_matches:
                issues.append(f"缺少必需关键词，找到 {matches}/{min_matches} 个")
                recommendations.append(f"请确保文档包含以下关键词之一: {', '.join(required)}")
        
        # 检查禁用关键词
        if "forbidden_keywords" in conditions:
            forbidden = conditions["forbidden_keywords"]
            max_matches = conditions.get("max_matches", 0)
            
            found_forbidden = [kw for kw in forbidden if kw in content]
            if len(found_forbidden) > max_matches:
                issues.append(f"发现禁用关键词: {', '.join(found_forbidden)}")
                recommendations.append("请移除或替换禁用的关键词")
        
        passed = len(issues) == 0
        score = 100.0 if passed else 0.0
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            is_compliant=passed,
            compliance_level=ComplianceLevel.COMPLIANT if passed else ComplianceLevel.VIOLATION,
            score=score,
            issues=issues,
            suggestions=recommendations,
            evidence=[]
        )
    
    def _check_pattern_rule(self, rule: ComplianceRule, content: str) -> ComplianceResult:
        """检查模式规则"""
        conditions = rule.conditions
        issues = []
        recommendations = []
        
        if "pattern" in conditions:
            pattern = conditions["pattern"]
            description = conditions.get("description", "符合指定模式")
            
            if not re.search(pattern, content):
                issues.append(f"内容不符合要求的模式")
                recommendations.append(f"请确保内容符合格式要求: {description}")
        
        # 检查日期格式一致性
        if "date_patterns" in conditions:
            date_patterns = conditions["date_patterns"]
            consistency_required = conditions.get("consistency_required", False)
            
            if consistency_required:
                pattern_matches = {}
                for pattern in date_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        pattern_matches[pattern] = len(matches)
                
                if len(pattern_matches) > 1:
                    issues.append("文档中使用了多种日期格式")
                    recommendations.append("请统一使用一种日期格式")
        
        passed = len(issues) == 0
        score = 100.0 if passed else 0.0
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            is_compliant=passed,
            compliance_level=ComplianceLevel.COMPLIANT if passed else ComplianceLevel.VIOLATION,
            score=score,
            issues=issues,
            suggestions=recommendations,
            evidence=[]
        )
    
    def _check_field_rule(self, rule: ComplianceRule, content: str, 
                         metadata: Dict[str, Any]) -> ComplianceResult:
        """检查字段规则"""
        conditions = rule.conditions
        issues = []
        recommendations = []
        
        # 检查必需字段
        if "required_fields" in conditions:
            required_fields = conditions["required_fields"]
            missing_fields = []
            
            for field in required_fields:
                if field not in content and field not in str(metadata.values()):
                    missing_fields.append(field)
            
            if missing_fields:
                issues.append(f"缺少必需字段: {', '.join(missing_fields)}")
                recommendations.append(f"请添加缺少的字段信息")
        
        # 检查内容长度
        if "min_content_length" in conditions:
            min_length = conditions["min_content_length"]
            if len(content.strip()) < min_length:
                issues.append(f"内容长度不足，当前 {len(content)} 字符，最少需要 {min_length} 字符")
                recommendations.append("请补充更详细的内容")
        
        passed = len(issues) == 0
        score = 100.0 if passed else 0.0
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            is_compliant=passed,
            compliance_level=ComplianceLevel.COMPLIANT if passed else ComplianceLevel.VIOLATION,
            score=score,
            issues=issues,
            suggestions=recommendations,
            evidence=[]
        )
    
    def _check_format_rule(self, rule: ComplianceRule, metadata: Dict[str, Any]) -> ComplianceResult:
        """检查格式规则"""
        conditions = rule.conditions
        issues = []
        recommendations = []
        
        # 检查文件格式
        if "allowed_formats" in conditions:
            allowed_formats = conditions["allowed_formats"]
            file_name = metadata.get("filename", "")
            
            if file_name:
                file_ext = Path(file_name).suffix.lower()
                if file_ext not in [fmt.lower() for fmt in allowed_formats]:
                    issues.append(f"不支持的文件格式: {file_ext}")
                    recommendations.append(f"请使用支持的格式: {', '.join(allowed_formats)}")
        
        # 检查文件大小
        if "max_size_mb" in conditions:
            max_size = conditions["max_size_mb"]
            file_size_mb = metadata.get("size_mb", 0)
            
            if file_size_mb > max_size:
                issues.append(f"文件过大: {file_size_mb}MB，最大允许 {max_size}MB")
                recommendations.append("请压缩文件或分割为多个文件")
        
        passed = len(issues) == 0
        score = 100.0 if passed else 0.0
        
        return ComplianceResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            is_compliant=passed,
            compliance_level=ComplianceLevel.COMPLIANT if passed else ComplianceLevel.VIOLATION,
            score=score,
            issues=issues,
            suggestions=recommendations,
            evidence=[]
        )
    
    def _calculate_compliance_level(self, score: float) -> ComplianceLevel:
        """根据分数计算合规等级"""
        if score >= 90:
            return ComplianceLevel.COMPLIANT
        elif score >= 70:
            return ComplianceLevel.WARNING
        elif score >= 50:
            return ComplianceLevel.VIOLATION
        else:
            return ComplianceLevel.CRITICAL
    
    def load_rules_from_file(self, file_path: str):
        """从文件加载规则配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            self.rules.clear()
            for category in RuleCategory:
                self.rule_categories[category].clear()
            
            for rule_data in rules_data.get('rules', []):
                rule = ComplianceRule(**rule_data)
                self.add_rule(rule)
                
        except Exception as e:
            print(f"加载规则文件失败: {e}")
            self._load_default_rules()
    
    def save_rules_to_file(self, file_path: str):
        """保存规则配置到文件"""
        rules_data = {
            'rules': [rule.dict() for rule in self.rules],
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        total_rules = len(self.rules)
        enabled_rules = len([r for r in self.rules if r.enabled])
        
        category_stats = {}
        for category in RuleCategory:
            category_rules = self.rule_categories[category]
            category_stats[category.value] = {
                'total': len(category_rules),
                'enabled': len([r for r in category_rules if r.enabled])
            }
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'category_breakdown': category_stats
        }