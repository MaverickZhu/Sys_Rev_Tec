#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规性检查测试运行器

提供简单的测试执行接口，支持不同类型的测试运行。

Author: AI Assistant
Date: 2024-07-28
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from test_compliance import (
    TestDataGenerator,
    TestComplianceRuleEngine,
    TestComplianceAPI,
    TestPerformance
)


def run_basic_tests():
    """运行基础功能测试"""
    print("=== 运行基础功能测试 ===")
    
    # 测试规则引擎
    print("\n1. 测试合规规则引擎...")
    engine_test = TestComplianceRuleEngine()
    engine_test.setup_method()
    
    try:
        engine_test.test_load_default_rules()
        print("   ✅ 默认规则加载测试通过")
        
        engine_test.test_add_custom_rule()
        print("   ✅ 自定义规则添加测试通过")
        
        engine_test.test_check_document_compliance()
        print("   ✅ 文档合规性检查测试通过")
        
        engine_test.test_check_non_compliant_document()
        print("   ✅ 不合规文档检测测试通过")
        
        engine_test.test_format_validation()
        print("   ✅ 格式验证测试通过")
        
        engine_test.test_scoring_mechanism()
        print("   ✅ 评分机制测试通过")
        
    except Exception as e:
        print(f"   ❌ 规则引擎测试失败: {e}")
        return False
    
    return True


async def run_api_tests():
    """运行API测试"""
    print("\n2. 测试合规性检查API...")
    api_test = TestComplianceAPI()
    api_test.setup_method()
    
    try:
        await api_test.test_check_document_compliance()
        print("   ✅ 单文档合规性检查API测试通过")
        
        await api_test.test_check_project_compliance()
        print("   ✅ 项目合规性检查API测试通过")
        
        await api_test.test_validate_document_format()
        print("   ✅ 文档格式验证API测试通过")
        
        await api_test.test_get_compliance_summary()
        print("   ✅ 合规性摘要API测试通过")
        
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")
        return False
    
    return True


async def run_performance_tests():
    """运行性能测试"""
    print("\n3. 测试性能...")
    perf_test = TestPerformance()
    perf_test.setup_method()
    
    try:
        perf_test.test_large_document_processing()
        print("   ✅ 大文档处理性能测试通过")
        
        await perf_test.test_batch_processing_performance()
        print("   ✅ 批量处理性能测试通过")
        
    except Exception as e:
        print(f"   ❌ 性能测试失败: {e}")
        return False
    
    return True


def run_demo():
    """运行演示示例"""
    print("\n=== 合规性检查功能演示 ===")
    
    from rule_engine import RuleEngine
    
    # 创建规则引擎
    engine = RuleEngine()
    
    # 获取测试文档
    test_docs = TestDataGenerator.get_sample_documents()
    
    print(f"\n加载了 {len(engine.get_rules())} 个合规检查规则")
    print(f"准备检查 {len(test_docs)} 个测试文档\n")
    
    # 检查每个文档
    for i, doc in enumerate(test_docs, 1):
        print(f"{i}. 检查文档: {doc['filename']}")
        
        # 准备文档元数据
        metadata = {
            'filename': doc['filename'],
            'file_type': doc.get('file_type', 'pdf'),
            'project_id': doc.get('project_id', 'demo_project'),
            'document_type': doc.get('document_type', 'general')
        }
        
        result = engine.check_document_compliance(doc['content'], metadata)
        
        print(f"   合规评分: {result.compliance_score:.1f}/100")
        print(f"   合规等级: {result.overall_compliance.value}")
        
        if result.rule_results:
            failed_checks = [r for r in result.rule_results if not r.is_compliant]
            if failed_checks:
                print(f"   发现 {len(failed_checks)} 个合规问题:")
                for check in failed_checks[:2]:  # 只显示前2个问题
                    print(f"     - {check.rule_name}: {'; '.join(check.issues[:1])}")
            else:
                print("   ✅ 所有检查项均通过")
        print()


async def main():
    """主函数"""
    print("合规性检查功能测试套件")
    print("=" * 50)
    
    # 运行基础测试
    basic_success = run_basic_tests()
    
    if basic_success:
        # 运行API测试
        api_success = await run_api_tests()
        
        if api_success:
            # 运行性能测试
            perf_success = await run_performance_tests()
            
            if perf_success:
                print("\n🎉 所有测试通过！")
                
                # 运行演示
                run_demo()
                
                print("\n=== 测试总结 ===")
                print("✅ 合规性检查功能已完成开发并通过测试")
                print("✅ 支持多种合规规则和检查类型")
                print("✅ API接口完整，性能良好")
                print("✅ 可以投入生产环境使用")
                
                return True
    
    print("\n❌ 部分测试失败，请检查代码")
    return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)