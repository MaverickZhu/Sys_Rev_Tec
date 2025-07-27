#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档向量化功能测试
测试智能文档处理的核心功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.ai_integration import AIIntegrationService
from app.utils.text_processing import TextProcessor
from app.utils.vector_service import VectorService
from app.core.config import settings

async def test_document_vectorization():
    """
    测试文档向量化流程
    """
    print("=== 测试文档向量化功能 ===")
    
    # 初始化服务
    ai_service = AIIntegrationService()
    text_processor = TextProcessor()
    vector_service = VectorService()
    
    # 测试文档内容
    test_document = """
    政府采购项目审查报告
    
    项目名称：办公设备采购项目
    采购单位：某市政府办公室
    采购金额：500万元
    
    项目概述：
    本项目旨在为市政府办公室采购一批现代化办公设备，包括计算机、打印机、复印机等。
    采购过程严格按照《政府采购法》相关规定执行，确保公开、公平、公正。
    
    技术要求：
    1. 计算机配置：Intel i7处理器，16GB内存，512GB SSD硬盘
    2. 打印机要求：激光打印，双面打印功能，网络连接
    3. 复印机要求：多功能一体机，扫描、复印、传真功能
    
    供应商评估：
    经过公开招标，共有5家供应商参与投标。评标委员会按照技术标准、价格因素、
    服务能力等方面进行综合评估，最终确定中标供应商。
    
    风险评估：
    1. 技术风险：设备兼容性问题
    2. 供应风险：供应商履约能力
    3. 价格风险：市场价格波动
    
    合规性检查：
    项目采购流程符合相关法律法规要求，资金来源合法，预算审批完整。
    """
    
    try:
        print("\n1. 文本预处理...")
        # 文本清理和预处理
        cleaned_text = text_processor.clean_text(test_document)
        print(f"清理后文本长度: {len(cleaned_text)} 字符")
        
        # 文本分块
        chunks = text_processor.chunk_text(cleaned_text, chunk_size=200, chunk_overlap=50)
        print(f"文本分块数量: {len(chunks)}")
        
        # 提取关键词
        keywords = text_processor.extract_keywords(cleaned_text)
        print(f"提取关键词: {keywords[:10]}")
        
        print("\n2. 文档向量化...")
        # 创建模拟文档对象
        mock_document = type('MockDocument', (), {
            'id': 'test_doc_001',
            'title': '办公设备采购项目',
            'content': test_document,
            'extracted_text': cleaned_text,
            'ocr_text': None
        })()
        
        # 文档向量化
        vectorization_result = await ai_service.vectorize_document(
            document=mock_document,
            model_name="bge-m3:latest",
            chunk_size=200,
            chunk_overlap=50
        )
        
        print(f"文档ID: {vectorization_result.get('document_id')}")
        print(f"向量维度: {vectorization_result.get('embedding_dimension')}")
        print(f"文本块数量: {vectorization_result.get('total_chunks')}")
        
        print("\n3. 智能分析...")
        # 文档智能分析
        analysis_result = await ai_service.analyze_document(
            document=mock_document,
            analysis_types=["summary", "keywords", "classification", "risk_assessment", "sentiment_analysis"]
        )
        
        print(f"分析结果类型: {list(analysis_result.keys())}")
        if 'classification' in analysis_result:
            print(f"文档分类: {analysis_result.get('classification')}")
        if 'risk_assessment' in analysis_result:
            print(f"风险评估: {analysis_result.get('risk_assessment')}")
        if 'sentiment_analysis' in analysis_result:
            print(f"情感分析: {analysis_result.get('sentiment_analysis')}")
        if 'keywords' in analysis_result:
            print(f"关键词数量: {len(analysis_result.get('keywords', []))}")
        
        print("\n4. 语义搜索测试...")
        # 测试语义搜索
        search_queries = [
            "办公设备采购",
            "风险评估",
            "供应商评估",
            "合规性检查"
        ]
        
        for query in search_queries:
            print(f"\n搜索查询: '{query}'")
            # 创建一个模拟的数据库会话
            from unittest.mock import MagicMock
            mock_db = MagicMock()
            
            search_results = await vector_service.semantic_search(
                db=mock_db,
                query=query,
                max_results=3,
                similarity_threshold=0.5
            )
            
            if search_results:
                for i, result in enumerate(search_results[:2], 1):
                    print(f"  结果{i}: 相似度={result.get('score', 0):.3f}")
                    print(f"    内容预览: {result.get('content', '')[:100]}...")
            else:
                print("  未找到相关结果")
        
        print("\n5. 向量存储测试...")
        # 测试向量存储 - 使用 update_document_vectors 方法
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        
        try:
            # 测试更新文档向量
            update_result = await vector_service.update_document_vectors(
                db=mock_db,
                document_id=1,  # 使用测试文档ID
                force_update=True
            )
            print(f"向量更新结果: {update_result}")
        except Exception as e:
            print(f"向量存储测试跳过: {str(e)}")
            print("注意: 向量存储需要真实的数据库连接")
        
        print("\n✅ 文档向量化功能测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_batch_processing():
    """
    测试批量文档处理
    """
    print("\n=== 测试批量文档处理 ===")
    
    ai_service = AIIntegrationService()
    
    # 模拟多个文档
    test_documents = [
        {
            "id": "doc_001",
            "title": "采购合同审查",
            "content": "本合同为政府采购合同，涉及办公用品采购，金额100万元。合同条款完整，符合相关法规要求。"
        },
        {
            "id": "doc_002", 
            "title": "供应商资质审查",
            "content": "供应商具备相应资质证书，财务状况良好，履约能力强。建议通过资质审查。"
        },
        {
            "id": "doc_003",
            "title": "项目验收报告",
            "content": "项目按期完成，设备安装调试正常，用户培训到位。验收合格，建议办理结算手续。"
        }
    ]
    
    try:
        print(f"\n开始批量处理 {len(test_documents)} 个文档...")
        
        # 批量向量化
        batch_results = []
        for doc in test_documents:
            print(f"\n处理文档: {doc['title']}")
            
            # 创建模拟文档对象
            mock_doc = type('MockDocument', (), {
                'id': doc["id"],
                'title': doc["title"],
                'content': doc["content"],
                'extracted_text': doc["content"],
                'ocr_text': None
            })()
            
            result = await ai_service.vectorize_document(
                document=mock_doc,
                model_name="bge-m3:latest",
                chunk_size=200,
                chunk_overlap=50
            )
            
            batch_results.append({
                "document_id": doc["id"],
                "title": doc["title"],
                "document_id_result": result.get("document_id"),
                "chunk_count": result.get("total_chunks", 0)
            })
            
            print(f"  文档ID: {result.get('document_id')}")
            print(f"  块数: {result.get('total_chunks', 0)}")
        
        print("\n批量处理结果汇总:")
        successful = sum(1 for r in batch_results if r["document_id_result"] is not None)
        total_chunks = sum(r["chunk_count"] for r in batch_results)
        
        print(f"  成功处理: {successful}/{len(test_documents)} 个文档")
        print(f"  总文本块: {total_chunks} 个")
        
        print("\n✅ 批量文档处理测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 批量处理测试失败: {str(e)}")
        return False

async def main():
    """
    主测试函数
    """
    print("开始智能文档处理功能测试")
    print(f"配置信息:")
    print(f"  默认向量存储: {settings.DEFAULT_VECTOR_STORE}")
    print(f"  OpenAI API: {'已配置' if settings.OPENAI_API_KEY else '未配置'}")
    print(f"  Ollama URL: {settings.OLLAMA_BASE_URL or '未配置'}")
    
    # 运行测试
    test_results = []
    
    # 测试1: 文档向量化
    result1 = await test_document_vectorization()
    test_results.append(("文档向量化", result1))
    
    # 测试2: 批量处理
    result2 = await test_batch_processing()
    test_results.append(("批量处理", result2))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("智能文档处理功能测试结果汇总")
    print("="*50)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 所有测试通过！智能文档处理功能已就绪。")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试。")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())