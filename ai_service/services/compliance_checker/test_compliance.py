#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规性检查功能测试模块

提供完整的测试用例和测试数据集，验证合规性检查功能的正确性。
包含单元测试、集成测试和性能测试。

Author: AI Assistant
Date: 2024-07-28
"""

import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from compliance_models import (
    ComplianceRule, ComplianceResult, DocumentCompliance,
    ComplianceReport, ComplianceLevel, RuleCategory
)
from rule_engine import RuleEngine
from compliance_api import ComplianceAPI


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def get_sample_documents() -> List[Dict[str, Any]]:
        """获取样本文档数据"""
        return [
            {
                "id": "doc_001",
                "filename": "项目计划书.pdf",
                "content": "项目名称：智能审计系统\n项目负责人：张三\n联系方式：13800138000\n预算：100万元\n审批人：李四\n审批日期：2024-01-15\n项目描述：本项目旨在开发一套智能化的审计系统，提高审计效率和准确性。",
                "size_mb": 1.2,
                "project_id": "proj_001",
                "upload_date": "2024-01-01"
            },
            {
                "id": "doc_002",
                "filename": "预算明细表.xlsx",
                "content": "预算项目\t金额\n人员费用\t60万\n设备费用\t30万\n其他费用\t10万\n负责人：王五\n联系方式：13900139000\n备注：所有费用已通过财务审核",
                "size_mb": 0.8,
                "project_id": "proj_001",
                "upload_date": "2024-01-02"
            },
            {
                "id": "doc_003",
                "filename": "风险评估报告.docx",
                "content": "风险评估结果\n技术风险：中等\n市场风险：低\n财务风险：低\n评估人员：赵六\n评估日期：2024-01-10\n建议：加强技术团队建设，定期进行风险监控。",
                "size_mb": 0.5,
                "project_id": "proj_001",
                "upload_date": "2024-01-03"
            },
            {
                "id": "doc_004",
                "filename": "不合规文档.txt",
                "content": "这是一个包含敏感信息的文档\n身份证号：123456789012345678\n银行卡号：6222021234567890\n密码：admin123\n机密信息：公司内部财务数据\n该文档未经审批直接上传。",
                "size_mb": 0.1,
                "project_id": "proj_002",
                "upload_date": "2024-01-04"
            },
            {
                "id": "doc_005",
                "filename": "格式错误文档",  # 缺少文件扩展名
                "content": "内容正常但文件名格式不规范",
                "size_mb": 15.5,  # 超过大小限制
                "project_id": "proj_002",
                "upload_date": "2024-01-05"
            }
        ]
    
    @staticmethod
    def get_custom_rules() -> List[ComplianceRule]:
        """获取自定义合规规则"""
        return [
            ComplianceRule(
                rule_id="CUSTOM_001",
                name="项目编号格式检查",
                category=RuleCategory.PROCEDURE,
                format_pattern=r"PROJ-\d{4}-\d{3}",
                weight=0.8,
                severity=ComplianceLevel.WARNING,
                description="项目编号必须符合PROJ-YYYY-XXX格式"
            ),
            ComplianceRule(
                rule_id="CUSTOM_002",
                name="金额格式检查",
                category=RuleCategory.CONTENT,
                format_pattern=r"\d+(\.\d{1,2})?万元",
                weight=0.6,
                severity=ComplianceLevel.WARNING,
                description="金额必须使用标准格式（如：100.50万元）"
            )
        ]


class TestComplianceRuleEngine:
    """合规规则引擎测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = RuleEngine()
        self.test_documents = TestDataGenerator.get_sample_documents()
    
    def test_load_default_rules(self):
        """测试加载默认规则"""
        rules = self.engine.get_rules()
        assert len(rules) > 0
        assert any(rule.rule_id == "REG_001" for rule in rules)
        assert any(rule.rule_id == "REG_002" for rule in rules)
    
    def test_add_custom_rule(self):
        """测试添加自定义规则"""
        custom_rules = TestDataGenerator.get_custom_rules()
        for rule in custom_rules:
            self.engine.add_rule(rule)
        
        rules = self.engine.get_rules()
        assert any(rule.rule_id == "CUSTOM_001" for rule in rules)
        assert any(rule.rule_id == "CUSTOM_002" for rule in rules)
    
    def test_check_document_compliance(self):
        """测试文档合规性检查"""
        # 测试合规文档
        compliant_doc = self.test_documents[0]  # 项目计划书
        content = compliant_doc["content"]
        metadata = {k: v for k, v in compliant_doc.items() if k != "content"}
        result = self.engine.check_document_compliance(content, metadata)
        
        assert isinstance(result, DocumentCompliance)
        assert result.document_id == "doc_001"
        assert result.compliance_score >= 0  # 应该有评分
        assert isinstance(result.overall_compliance, ComplianceLevel)
    
    def test_check_non_compliant_document(self):
        """测试不合规文档检查"""
        # 测试不合规文档
        non_compliant_doc = self.test_documents[3]  # 包含敏感信息的文档
        content = non_compliant_doc["content"]
        metadata = {k: v for k, v in non_compliant_doc.items() if k != "content"}
        result = self.engine.check_document_compliance(content, metadata)
        
        assert isinstance(result, DocumentCompliance)
        assert result.document_id == "doc_004"
        assert isinstance(result.compliance_score, (int, float))
        assert len(result.rule_results) > 0
        
        # 检查是否检测到敏感数据
        sensitive_violations = [r for r in result.rule_results if r.rule_id == "REG_002"]
        assert len(sensitive_violations) > 0
        assert not sensitive_violations[0].is_compliant
    
    def test_format_validation(self):
        """测试格式验证"""
        # 测试格式错误文档
        format_error_doc = self.test_documents[4]  # 格式错误文档
        content = format_error_doc["content"]
        metadata = {k: v for k, v in format_error_doc.items() if k != "content"}
        result = self.engine.check_document_compliance(content, metadata)
        
        # 应该检测到格式问题
        assert isinstance(result, DocumentCompliance)
        assert len(result.rule_results) > 0
    
    def test_scoring_mechanism(self):
        """测试评分机制"""
        doc = self.test_documents[0]
        content = doc["content"]
        metadata = {k: v for k, v in doc.items() if k != "content"}
        result = self.engine.check_document_compliance(content, metadata)
        
        # 验证评分在有效范围内
        assert 0 <= result.compliance_score <= 100
        
        # 验证合规等级是有效的
        assert isinstance(result.overall_compliance, ComplianceLevel)


class TestComplianceAPI:
    """合规性检查API测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.api = ComplianceAPI()
        self.test_documents = TestDataGenerator.get_sample_documents()
    
    @pytest.mark.asyncio
    async def test_check_document_compliance(self):
        """测试单文档合规性检查API"""
        doc = self.test_documents[0]
        content = doc["content"]
        metadata = {k: v for k, v in doc.items() if k != "content"}
        result = await self.api.check_document_compliance(content, metadata)
        
        assert isinstance(result, DocumentCompliance)
        assert result.document_id == doc["id"]
        assert isinstance(result.compliance_score, (int, float))
        assert isinstance(result.overall_compliance, ComplianceLevel)
    
    @pytest.mark.asyncio
    async def test_check_project_compliance(self):
        """测试项目合规性检查API"""
        documents = self.test_documents[:3]  # 使用前3个文档
        result = await self.api.check_project_compliance(documents)
        
        assert isinstance(result, ComplianceReport)
        assert result.total_documents == 3
        assert len(result.document_reports) == 3
        assert 0 <= result.compliance_score <= 100
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_validate_document_format(self):
        """测试文档格式验证API"""
        # 测试正常格式文档
        normal_doc = self.test_documents[0]
        metadata = {k: v for k, v in normal_doc.items() if k != "content"}
        result = await self.api.validate_document_format(metadata)
        assert isinstance(result, dict)
        assert "valid" in result
        assert "issues" in result
        
        # 测试格式错误文档
        error_doc = self.test_documents[4]
        metadata = {k: v for k, v in error_doc.items() if k != "content"}
        result = await self.api.validate_document_format(metadata)
        assert isinstance(result, dict)
        assert "valid" in result
    
    @pytest.mark.asyncio
    async def test_get_compliance_summary(self):
        """测试合规性摘要API"""
        project_id = "test_project_001"
        summary = await self.api.get_compliance_summary(project_id)
        
        assert "project_id" in summary
        assert "total_documents" in summary
        assert "compliant_documents" in summary
        assert "overall_compliance_score" in summary
        assert summary["project_id"] == project_id


class TestPerformance:
    """性能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.engine = RuleEngine()
        self.api = ComplianceAPI()
    
    def test_large_document_processing(self):
        """测试大文档处理性能"""
        # 创建大文档
        large_content = "测试内容 " * 10000  # 约10万字符
        large_doc = {
            "id": "large_doc",
            "filename": "大文档.pdf",
            "content": large_content,
            "size_mb": 5.0,
            "project_id": "proj_perf",
            "upload_date": "2024-01-01"
        }
        
        import time
        start_time = time.time()
        content = large_doc["content"]
        metadata = {k: v for k, v in large_doc.items() if k != "content"}
        result = self.engine.check_document_compliance(content, metadata)
        end_time = time.time()
        
        # 处理时间应该在合理范围内（<5秒）
        processing_time = end_time - start_time
        assert processing_time < 5.0
        assert isinstance(result, DocumentCompliance)
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self):
        """测试批量处理性能"""
        # 创建多个文档
        documents = []
        for i in range(50):
            doc = {
                "id": f"batch_doc_{i}",
                "filename": f"文档_{i}.pdf",
                "content": f"这是第{i}个测试文档的内容",
                "size_mb": 1.0,
                "project_id": "proj_batch",
                "upload_date": "2024-01-01"
            }
            documents.append(doc)
        
        import time
        start_time = time.time()
        result = await self.api.check_project_compliance(documents)
        end_time = time.time()
        
        # 批量处理时间应该在合理范围内（<10秒）
        processing_time = end_time - start_time
        assert processing_time < 10.0
        assert result.total_documents == 50


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])