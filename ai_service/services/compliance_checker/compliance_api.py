#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规性检查API服务

提供合规性检查的API接口，集成规则引擎和现有的风险评估系统。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from rule_engine import RuleEngine
from compliance_models import (
    ComplianceRule, ComplianceResult, ComplianceLevel, RuleCategory,
    DocumentCompliance, ComplianceReport, ComplianceConfig
)

logger = logging.getLogger(__name__)


class ComplianceAPI:
    """合规性检查API服务"""
    
    def __init__(self, config: Optional[ComplianceConfig] = None):
        self.config = config or ComplianceConfig()
        self.rule_engine = RuleEngine()
        self._initialize_service()
    
    def _initialize_service(self):
        """初始化服务"""
        logger.info("初始化合规性检查服务")
        
        # 根据配置调整规则引擎
        if hasattr(self.config, 'rules_config_path') and self.config.rules_config_path:
            self.rule_engine.load_rules_from_file(self.config.rules_config_path)
        
        logger.info(f"加载了 {len(self.rule_engine.rules)} 条合规性规则")
    
    async def check_document_compliance(self, 
                                      document_content: str,
                                      document_metadata: Dict[str, Any]) -> DocumentCompliance:
        """检查单个文档的合规性"""
        try:
            logger.info(f"开始检查文档合规性: {document_metadata.get('filename', 'unknown')}")
            
            # 使用规则引擎进行合规性检查
            compliance_result = self.rule_engine.check_document_compliance(
                document_content, document_metadata
            )
            
            logger.info(
                f"文档合规性检查完成，得分: {compliance_result.overall_score:.1f}, "
                f"等级: {compliance_result.compliance_level.value}"
            )
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"文档合规性检查失败: {str(e)}")
            # 返回错误结果
            return DocumentCompliance(
                document_id=document_metadata.get("id", "unknown"),
                document_name=document_metadata.get("filename", "unknown"),
                overall_compliance=ComplianceLevel.CRITICAL,
                compliance_score=0.0,
                rule_results=[
                    ComplianceResult(
                        rule_id="ERROR",
                        rule_name="系统错误",
                        category=RuleCategory.DOCUMENT,
                        is_compliant=False,
                        compliance_level=ComplianceLevel.CRITICAL,
                        score=0.0,
                        issues=[f"合规性检查失败: {str(e)}"],
                        suggestions=["请检查文档格式和内容"],
                        evidence=[]
                    )
                ],
                total_rules=0,
                passed_rules=0,
                checked_at=datetime.now()
            )
    
    async def check_project_compliance(self, 
                                     documents: List[Dict[str, Any]]) -> ComplianceReport:
        """检查项目级别的合规性"""
        try:
            logger.info(f"开始检查项目合规性，文档数量: {len(documents)}")
            
            document_results = []
            total_score = 0.0
            total_documents = len(documents)
            
            # 检查每个文档
            for doc in documents:
                content = doc.get('content', '')
                metadata = {
                    'id': doc.get('id'),
                    'filename': doc.get('filename'),
                    'size_mb': doc.get('size_mb', 0),
                    'upload_date': doc.get('upload_date')
                }
                
                doc_compliance = await self.check_document_compliance(content, metadata)
                document_results.append(doc_compliance)
                total_score += doc_compliance.compliance_score
            
            # 计算项目整体合规性
            overall_score = total_score / total_documents if total_documents > 0 else 0.0
            compliance_level = self._calculate_project_compliance_level(overall_score)
            
            # 统计信息
            total_rules_checked = sum(doc.total_rules for doc in document_results)
            total_rules_passed = sum(doc.passed_rules for doc in document_results)
            
            # 收集所有问题和建议
            all_issues = []
            all_recommendations = []
            
            for doc_result in document_results:
                for check_result in doc_result.rule_results:
                    all_issues.extend(check_result.issues)
                    all_recommendations.extend(check_result.suggestions)
            
            # 去重并排序
            unique_issues = list(set(all_issues))
            unique_recommendations = list(set(all_recommendations))
            
            report = ComplianceReport(
                project_id=documents[0].get('project_id', 'unknown') if documents else 'unknown',
                project_name=documents[0].get('project_name', 'unknown') if documents else 'unknown',
                overall_compliance=compliance_level,
                compliance_score=overall_score,
                document_reports=document_results,
                total_documents=total_documents,
                compliant_documents=len([d for d in document_results 
                                       if d.overall_compliance == ComplianceLevel.COMPLIANT]),
                critical_issues=unique_issues[:10],  # 限制最多10个关键问题
                recommendations=unique_recommendations[:10],  # 限制最多10个建议
                generated_at=datetime.now()
            )
            
            logger.info(
                f"项目合规性检查完成，整体得分: {overall_score:.1f}, "
                f"等级: {compliance_level.value}, "
                f"合规文档: {report.compliant_documents}/{total_documents}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"项目合规性检查失败: {str(e)}")
            raise
    
    def _calculate_project_compliance_level(self, score: float) -> ComplianceLevel:
        """计算项目级别的合规等级"""
        # 项目级别的标准可能比单文档更严格
        if score >= 90:
            return ComplianceLevel.COMPLIANT
        elif score >= 70:
            return ComplianceLevel.WARNING
        elif score >= 50:
            return ComplianceLevel.VIOLATION
        else:
            return ComplianceLevel.CRITICAL
    
    async def get_compliance_rules(self) -> List[ComplianceRule]:
        """获取所有合规性规则"""
        return self.rule_engine.rules
    
    async def add_compliance_rule(self, rule: ComplianceRule) -> bool:
        """添加新的合规性规则"""
        try:
            self.rule_engine.add_rule(rule)
            logger.info(f"添加合规性规则: {rule.name} ({rule.id})")
            return True
        except Exception as e:
            logger.error(f"添加合规性规则失败: {str(e)}")
            return False
    
    async def remove_compliance_rule(self, rule_id: str) -> bool:
        """移除合规性规则"""
        try:
            success = self.rule_engine.remove_rule(rule_id)
            if success:
                logger.info(f"移除合规性规则: {rule_id}")
            else:
                logger.warning(f"未找到要移除的规则: {rule_id}")
            return success
        except Exception as e:
            logger.error(f"移除合规性规则失败: {str(e)}")
            return False
    
    async def update_compliance_rule(self, rule_id: str, updated_rule: ComplianceRule) -> bool:
        """更新合规性规则"""
        try:
            # 先移除旧规则
            if self.rule_engine.remove_rule(rule_id):
                # 添加新规则
                self.rule_engine.add_rule(updated_rule)
                logger.info(f"更新合规性规则: {rule_id}")
                return True
            else:
                logger.warning(f"未找到要更新的规则: {rule_id}")
                return False
        except Exception as e:
            logger.error(f"更新合规性规则失败: {str(e)}")
            return False
    
    async def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        return self.rule_engine.get_rule_statistics()
    
    async def export_compliance_config(self, file_path: str) -> bool:
        """导出合规性配置"""
        try:
            self.rule_engine.save_rules_to_file(file_path)
            logger.info(f"导出合规性配置到: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出合规性配置失败: {str(e)}")
            return False
    
    async def import_compliance_config(self, file_path: str) -> bool:
        """导入合规性配置"""
        try:
            self.rule_engine.load_rules_from_file(file_path)
            logger.info(f"从文件导入合规性配置: {file_path}")
            return True
        except Exception as e:
            logger.error(f"导入合规性配置失败: {str(e)}")
            return False
    
    async def validate_document_format(self, document_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """验证文档格式（快速检查）"""
        try:
            filename = document_metadata.get('filename', '')
            size_mb = document_metadata.get('size_mb', 0)
            
            issues = []
            recommendations = []
            
            # 检查文件扩展名
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
            if filename:
                import os
                ext = os.path.splitext(filename)[1].lower()
                if ext not in allowed_extensions:
                    issues.append(f"不支持的文件格式: {ext}")
                    recommendations.append(f"请使用支持的格式: {', '.join(allowed_extensions)}")
            
            # 检查文件大小
            max_size_mb = 50
            if size_mb > max_size_mb:
                issues.append(f"文件过大: {size_mb}MB，最大允许 {max_size_mb}MB")
                recommendations.append("请压缩文件或分割为多个文件")
            
            # 检查文件名规范
            if filename and not filename.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').isalnum():
                issues.append("文件名包含特殊字符")
                recommendations.append("建议使用字母、数字、下划线和连字符")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'recommendations': recommendations,
                'metadata': document_metadata
            }
            
        except Exception as e:
            logger.error(f"文档格式验证失败: {str(e)}")
            return {
                'valid': False,
                'issues': [f"验证失败: {str(e)}"],
                'recommendations': ["请检查文档格式"],
                'metadata': document_metadata
            }
    
    async def get_compliance_summary(self, project_id: str) -> Dict[str, Any]:
        """获取项目合规性摘要"""
        try:
            # 这里应该从数据库获取项目的合规性历史数据
            # 目前返回模拟数据
            return {
                'project_id': project_id,
                'last_check_date': datetime.now().isoformat(),
                'overall_compliance_score': 85.5,
                'compliance_level': 'GOOD',
                'total_documents': 12,
                'compliant_documents': 10,
                'pending_issues': 3,
                'critical_issues': 0,
                'trend': 'improving',  # improving, declining, stable
                'next_check_due': (datetime.now()).isoformat()
            }
        except Exception as e:
            logger.error(f"获取合规性摘要失败: {str(e)}")
            return {
                'project_id': project_id,
                'error': str(e)
            }


# 全局合规性API实例
complianceAPI = ComplianceAPI()


# 便捷函数
async def check_document_compliance(document_content: str, 
                                  document_metadata: Dict[str, Any]) -> DocumentCompliance:
    """检查文档合规性的便捷函数"""
    return await complianceAPI.check_document_compliance(document_content, document_metadata)


async def check_project_compliance(documents: List[Dict[str, Any]]) -> ComplianceReport:
    """检查项目合规性的便捷函数"""
    return await complianceAPI.check_project_compliance(documents)


async def validate_document_format(document_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """验证文档格式的便捷函数"""
    return await complianceAPI.validate_document_format(document_metadata)