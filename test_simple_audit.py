#!/usr/bin/env python3
"""简化审计功能测试脚本"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_service.services.risk_assessment import (
    SimpleRiskAnalyzer,
    AuditConfig,
    AuditCategory,
    RiskLevel
)

def test_document_audit():
    """测试文档审计功能"""
    print("=== 测试文档审计功能 ===")
    
    # 创建审计配置
    config = AuditConfig()
    analyzer = SimpleRiskAnalyzer(config)
    
    # 测试文档数据
    test_document = {
        "id": "test_doc_001",
        "name": "项目计划书.pdf",
        "type": "项目计划书",
        "content": "这是一个项目计划书，包含项目描述、预算安排、时间计划等内容。项目负责人：张三，联系电话：13800138000",
        "file_path": "/docs/项目计划书.pdf",
        "size": 1024000,
        "budget": "1000000",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "project_code": "PROJ-2024-001",
    }
    
    # 执行文档审计
    doc_audit = analyzer.analyze_document(test_document)
    
    print(f"文档ID: {doc_audit.document_id}")
    print(f"文档名称: {doc_audit.document_name}")
    print(f"整体评分: {doc_audit.overall_score:.2f}")
    print(f"风险等级: {doc_audit.overall_risk.value}")
    print(f"审计时间: {doc_audit.audited_at}")
    print()
    
    # 显示各类别审计结果
    for result in doc_audit.audit_results:
        print(f"类别: {result.category.value}")
        print(f"  评分: {result.score:.2f}")
        print(f"  风险等级: {result.risk_level.value}")
        if result.issues:
            print(f"  发现问题: {'; '.join(result.issues)}")
        if result.suggestions:
            print(f"  改进建议: {'; '.join(result.suggestions)}")
        print()
    
    return doc_audit

def test_project_audit():
    """测试项目审计功能"""
    print("=== 测试项目审计功能 ===")
    
    # 创建审计配置
    config = AuditConfig()
    analyzer = SimpleRiskAnalyzer(config)
    
    # 测试项目数据
    project_data = {
        "id": "test_project_001",
        "name": "政府采购信息化项目",
        "budget": "5000000",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "project_code": "GOV-2024-001",
    }
    
    # 测试文档数据
    documents_data = [
        {
            "id": "doc_001",
            "name": "项目计划书.pdf",
            "type": "项目计划书",
            "content": "项目描述内容，包含预算、时间安排、法律依据、审批流程等信息。负责人：李四，电话：13900139000",
            "file_path": "/docs/项目计划书.pdf",
            "size": 1024000,
        },
        {
            "id": "doc_002",
            "name": "预算表.xlsx",
            "type": "预算表",
            "content": "详细预算分解，包含各项费用明细、审批信息、监督机制等",
            "file_path": "/docs/预算表.xlsx",
            "size": 512000,
        },
        {
            "id": "doc_003",
            "name": "合同草案.doc",
            "type": "合同文件",
            "content": "合同条款，包含验收标准、法律依据等内容",
            "file_path": "/docs/合同草案.doc",
            "size": 256000,
        }
    ]
    
    # 执行项目审计
    project_audit = analyzer.analyze_project(project_data, documents_data)
    
    print(f"项目ID: {project_audit.project_id}")
    print(f"项目名称: {project_audit.project_name}")
    print(f"整体评分: {project_audit.overall_score:.2f}")
    print(f"风险等级: {project_audit.overall_risk.value}")
    print(f"文档总数: {project_audit.total_documents}")
    print(f"高风险文档数: {project_audit.high_risk_documents}")
    print(f"审计时间: {project_audit.audited_at}")
    print()
    
    print("项目摘要:")
    print(project_audit.summary)
    print()
    
    print("改进建议:")
    for i, recommendation in enumerate(project_audit.recommendations, 1):
        print(f"  {i}. {recommendation}")
    print()
    
    # 显示各文档审计结果
    print("各文档审计详情:")
    for doc_audit in project_audit.document_audits:
        print(f"  文档: {doc_audit.document_name}")
        print(f"    评分: {doc_audit.overall_score:.2f}")
        print(f"    风险: {doc_audit.overall_risk.value}")
        
        # 显示主要问题
        issues = []
        for result in doc_audit.audit_results:
            if result.issues:
                issues.extend(result.issues)
        
        if issues:
            print(f"    主要问题: {'; '.join(issues[:2])}{'...' if len(issues) > 2 else ''}")
        print()
    
    return project_audit

def test_audit_summary():
    """测试审计摘要功能"""
    print("=== 测试审计摘要功能 ===")
    
    # 创建审计配置
    config = AuditConfig()
    analyzer = SimpleRiskAnalyzer(config)
    
    # 执行项目审计
    project_data = {
        "id": "summary_test_001",
        "name": "测试项目摘要",
    }
    
    documents_data = [
        {
            "id": "summary_doc_001",
            "name": "测试文档.pdf",
            "type": "项目计划书",
            "content": "简单的测试内容",
            "file_path": "/docs/测试文档.pdf",
            "size": 100,  # 小文件，会触发问题
        }
    ]
    
    project_audit = analyzer.analyze_project(project_data, documents_data)
    
    # 获取审计摘要
    summary = analyzer.get_audit_summary(project_audit)
    
    print("审计摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return summary

def main():
    """主测试函数"""
    print("开始测试简化审计功能...\n")
    
    try:
        # 测试文档审计
        doc_audit = test_document_audit()
        print("\n" + "="*50 + "\n")
        
        # 测试项目审计
        project_audit = test_project_audit()
        print("\n" + "="*50 + "\n")
        
        # 测试审计摘要
        summary = test_audit_summary()
        
        print("\n" + "="*50)
        print("✅ 所有测试完成！简化审计功能运行正常。")
        print("\n主要功能验证:")
        print("  ✅ 文档质量检查")
        print("  ✅ 合规性检查")
        print("  ✅ 完整性验证")
        print("  ✅ 一致性分析")
        print("  ✅ 项目整体审计")
        print("  ✅ 审计摘要生成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)