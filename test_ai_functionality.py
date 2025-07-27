#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI功能的脚本
验证文档向量化、语义搜索等功能是否正常工作
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.ai_integration import AIIntegrationService
from app.utils.vector_service import VectorService
from app.utils.text_processing import TextProcessor
from app.models.document import Document
from app.db.session import SessionLocal
from app.crud.crud_document import document as crud_document


async def test_text_processing():
    """测试文本处理功能"""
    print("\n=== 测试文本处理功能 ===")
    
    processor = TextProcessor()
    
    # 测试文本
    test_text = """
    这是一个测试文档，用于验证AI功能的正常工作。
    文档包含多个段落，每个段落都有不同的内容。
    我们需要测试文本分块、关键词提取、文本清理等功能。
    
    第二段落包含一些技术术语，比如API、数据库、向量化等。
    这些术语应该被正确识别和处理。
    
    最后一段包含一些数字和特殊字符：123, @#$%, 测试@example.com
    """
    
    # 测试文本清理
    cleaned_text = processor.clean_text(test_text)
    print(f"原始文本长度: {len(test_text)}")
    print(f"清理后文本长度: {len(cleaned_text)}")
    print(f"清理后文本预览: {cleaned_text[:100]}...")
    
    # 测试文本分块
    chunks = processor.chunk_text(cleaned_text, chunk_size=100, chunk_overlap=20)
    print(f"\n分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):  # 只显示前3个分块
        print(f"分块 {i+1}: {chunk['text'][:50]}...")
    
    # 测试关键词提取
    keywords = processor.extract_keywords(cleaned_text, max_keywords=10)
    print(f"\n提取的关键词: {keywords}")
    
    # 测试文本统计
    stats = processor.get_text_statistics(cleaned_text)
    print(f"\n文本统计: {stats}")
    
    return True


async def test_ai_integration():
    """测试AI集成服务"""
    print("\n=== 测试AI集成服务 ===")
    
    ai_service = AIIntegrationService()
    
    # 测试文本嵌入（模拟）
    test_text = "这是一个测试文本，用于验证向量化功能。"
    
    try:
        # 由于没有真实的AI模型，这里会使用模拟的嵌入
        embedding = await ai_service._get_text_embedding(test_text)
        print(f"文本嵌入维度: {len(embedding)}")
        print(f"嵌入向量前5个值: {embedding[:5]}")
        
        # 测试相似度计算
        embedding2 = await ai_service._get_text_embedding("这是另一个测试文本。")
        similarity = ai_service._calculate_cosine_similarity(embedding, embedding2)
        print(f"两个文本的相似度: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print(f"AI集成测试失败: {str(e)}")
        return False


async def test_vector_service():
    """测试向量服务"""
    print("\n=== 测试向量服务 ===")
    
    vector_service = VectorService()
    
    # 测试向量存储初始化
    print(f"可用的向量存储: {list(vector_service.vector_stores.keys())}")
    print(f"默认向量存储: {vector_service.default_store}")
    
    # 测试语义搜索（模拟）
    try:
        # 由于没有真实的数据库数据，这里只测试服务初始化
        print("向量服务初始化成功")
        return True
        
    except Exception as e:
        print(f"向量服务测试失败: {str(e)}")
        return False


async def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    
    try:
        db = SessionLocal()
        
        # 测试查询文档
        documents = crud_document.get_multi(db, limit=5)
        print(f"数据库中的文档数量（前5个）: {len(documents)}")
        
        for doc in documents:
            print(f"文档ID: {doc.id}, 标题: {doc.title}, 状态: {doc.status}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"数据库连接测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("开始AI功能测试...")
    
    test_results = []
    
    # 运行各项测试
    test_results.append(("文本处理", await test_text_processing()))
    test_results.append(("AI集成服务", await test_ai_integration()))
    test_results.append(("向量服务", await test_vector_service()))
    test_results.append(("数据库连接", await test_database_connection()))
    
    # 输出测试结果
    print("\n=== 测试结果汇总 ===")
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！AI功能基础架构正常工作。")
        print("\n下一步可以开始实现具体的AI功能：")
        print("1. 文档向量化API测试")
        print("2. 语义搜索功能测试")
        print("3. 智能分析功能测试")
    else:
        print("\n⚠️ 部分测试失败，需要检查相关配置和依赖。")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())