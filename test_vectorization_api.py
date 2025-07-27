#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档向量化API端点测试
测试智能文档处理的API接口功能
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

# 创建测试客户端
client = TestClient(app)

def test_vectorization_api():
    """
    测试文档向量化API端点
    """
    print("\n=== 测试文档向量化API端点 ===")
    
    # 测试数据
    test_document = {
        "content": "政府采购项目审查报告。项目名称：办公设备采购项目。采购单位：某市政府办公室。采购金额：500万元。项目概述：本项目旨在为市政府办公室采购一批现代化办公设备，包括计算机、打印机、复印机等。",
        "metadata": {
            "title": "办公设备采购项目",
            "category": "政府采购",
            "amount": "500万元"
        },
        "model_name": "text-embedding-ada-002",
        "chunk_size": 200,
        "chunk_overlap": 50
    }
    
    try:
        print("\n1. 测试单文档向量化API...")
        
        # 调用向量化API
        response = client.post(
            "/api/v1/vector/vectorize",
            json=test_document
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"向量化成功:")
            print(f"  文档ID: {result.get('document_id', 'N/A')}")
            print(f"  模型名称: {result.get('model_name', 'N/A')}")
            print(f"  文本块数量: {result.get('total_chunks', 0)}")
            print(f"  向量维度: {result.get('embedding_dimension', 0)}")
            print(f"  处理时间: {result.get('processing_time', 'N/A')}")
            
            # 检查文本块详情
            chunks = result.get('chunks', [])
            if chunks:
                print(f"\n  文本块示例:")
                for i, chunk in enumerate(chunks[:3]):
                    print(f"    块{i+1}: {chunk.get('text', '')[:50]}...")
                    print(f"         主题: {chunk.get('topic', 'N/A')}")
                    print(f"         重要性: {chunk.get('importance', 0):.2f}")
        else:
            print(f"向量化失败: {response.text}")
            return False
        
        print("\n2. 测试批量向量化API...")
        
        # 批量向量化测试数据
        batch_data = {
            "documents": [
                {
                    "content": "采购合同审查报告。本合同为政府采购合同，涉及办公用品采购，金额100万元。",
                    "metadata": {"title": "采购合同审查", "type": "合同"}
                },
                {
                    "content": "供应商资质审查报告。供应商具备相应资质证书，财务状况良好。",
                    "metadata": {"title": "供应商资质审查", "type": "审查"}
                }
            ],
            "model_name": "text-embedding-ada-002",
            "chunk_size": 150
        }
        
        # 调用批量向量化API
        batch_response = client.post(
            "/api/v1/vector/batch-vectorize",
            json=batch_data
        )
        
        print(f"批量响应状态码: {batch_response.status_code}")
        
        if batch_response.status_code == 200:
            batch_result = batch_response.json()
            print(f"批量向量化成功:")
            print(f"  处理文档数: {len(batch_result.get('results', []))}")
            print(f"  总文本块数: {sum(r.get('total_chunks', 0) for r in batch_result.get('results', []))}")
            
            # 显示每个文档的处理结果
            for i, doc_result in enumerate(batch_result.get('results', [])[:2]):
                print(f"  文档{i+1}: {doc_result.get('total_chunks', 0)} 个文本块")
        else:
            print(f"批量向量化失败: {batch_response.text}")
            return False
        
        print("\n3. 测试语义搜索API...")
        
        # 语义搜索测试
        search_data = {
            "query": "办公设备采购",
            "top_k": 5,
            "similarity_threshold": 0.5
        }
        
        search_response = client.post(
            "/api/v1/vector/semantic-search",
            json=search_data
        )
        
        print(f"搜索响应状态码: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            print(f"语义搜索成功:")
            print(f"  找到结果数: {len(search_result.get('results', []))}")
            
            # 显示搜索结果
            for i, result in enumerate(search_result.get('results', [])[:3]):
                print(f"  结果{i+1}: 相似度 {result.get('similarity', 0):.3f}")
                print(f"         内容: {result.get('text', '')[:60]}...")
        else:
            print(f"语义搜索失败: {search_response.text}")
        
        print("\n✅ 文档向量化API测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_document_analysis_api():
    """
    测试文档智能分析API端点
    """
    print("\n=== 测试文档智能分析API端点 ===")
    
    # 测试数据
    analysis_data = {
        "content": "政府采购项目审查报告。项目存在一定风险，需要加强监管。供应商资质良好，建议通过审查。",
        "analysis_types": ["summary", "keywords", "classification", "risk_assessment", "sentiment_analysis"],
        "metadata": {
            "title": "项目审查报告",
            "category": "政府采购"
        }
    }
    
    try:
        print("\n调用文档分析API...")
        
        response = client.post(
            "/api/v1/vector/analyze",
            json=analysis_data
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"文档分析成功:")
            
            # 显示分析结果
            analysis_results = result.get('analysis', {})
            for analysis_type, analysis_result in analysis_results.items():
                print(f"  {analysis_type}: {analysis_result}")
            
            print(f"  处理时间: {result.get('processing_time', 'N/A')}")
        else:
            print(f"文档分析失败: {response.text}")
            return False
        
        print("\n✅ 文档智能分析API测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 分析API测试失败: {str(e)}")
        return False

def test_health_check():
    """
    测试健康检查API
    """
    print("\n=== 测试健康检查API ===")
    
    try:
        response = client.get("/api/v1/vector/health")
        
        print(f"健康检查状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"系统状态: {result.get('status', 'unknown')}")
            print(f"AI服务状态: {result.get('ai_service', 'unknown')}")
            print(f"向量服务状态: {result.get('vector_service', 'unknown')}")
            print(f"缓存服务状态: {result.get('cache_service', 'unknown')}")
        else:
            print(f"健康检查失败: {response.text}")
            return False
        
        print("\n✅ 健康检查API测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 健康检查失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("开始文档向量化API端点测试")
    print(f"配置信息:")
    print(f"  API基础URL: http://localhost:8001")
    print(f"  默认向量存储: {settings.DEFAULT_VECTOR_STORE}")
    print(f"  OpenAI API: {'已配置' if settings.OPENAI_API_KEY else '未配置'}")
    
    # 运行测试
    test_results = []
    
    # 测试1: 健康检查
    result1 = test_health_check()
    test_results.append(("健康检查API", result1))
    
    # 测试2: 文档向量化API
    result2 = test_vectorization_api()
    test_results.append(("文档向量化API", result2))
    
    # 测试3: 文档分析API
    result3 = test_document_analysis_api()
    test_results.append(("文档分析API", result3))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("文档向量化API端点测试结果汇总")
    print("="*50)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 所有API测试通过！文档向量化API端点已就绪。")
    else:
        print("\n⚠️ 部分API测试失败，需要进一步调试。")
    
    return all_passed

if __name__ == "__main__":
    main()