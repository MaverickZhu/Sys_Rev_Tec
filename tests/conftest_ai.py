# AI功能测试配置
# 为向量化和智能搜索功能提供测试夹具和配置

import pytest
import asyncio
import numpy as np
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai_service.services.vector_service import VectorService
from ai_service.services.search_service import IntelligentSearchService
from ai_service.models.vector_models import DocumentVector, SearchRequest


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vector_service():
    """模拟向量服务"""
    service = Mock(spec=VectorService)
    
    # 模拟向量化方法
    async def mock_vectorize_text(text: str) -> List[float]:
        # 返回固定维度的模拟向量
        return [0.1] * 1024
    
    service.vectorize_text = AsyncMock(side_effect=mock_vectorize_text)
    
    # 模拟文档向量化
    async def mock_vectorize_document(document_id: int, content: str) -> List[DocumentVector]:
        chunks = [content[i:i+500] for i in range(0, len(content), 500)]
        vectors = []
        for i, chunk in enumerate(chunks):
            vector = DocumentVector(
                document_id=document_id,
                chunk_index=i,
                content=chunk,
                embedding=await mock_vectorize_text(chunk),
                metadata={"chunk_size": len(chunk)}
            )
            vectors.append(vector)
        return vectors
    
    service.vectorize_document = AsyncMock(side_effect=mock_vectorize_document)
    
    # 模拟相似度搜索
    async def mock_similarity_search(query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        # 返回模拟搜索结果
        return [
            {
                "document_id": 1,
                "chunk_index": 0,
                "content": "这是一个测试文档内容",
                "similarity": 0.95,
                "metadata": {"source": "test"}
            },
            {
                "document_id": 2,
                "chunk_index": 0,
                "content": "另一个相关的测试内容",
                "similarity": 0.87,
                "metadata": {"source": "test"}
            }
        ]
    
    service.similarity_search = AsyncMock(side_effect=mock_similarity_search)
    
    return service


@pytest.fixture
def mock_search_service(mock_vector_service):
    """模拟智能搜索服务"""
    service = Mock(spec=IntelligentSearchService)
    service.vector_service = mock_vector_service
    
    # 模拟语义搜索
    async def mock_semantic_search(request: SearchRequest) -> Dict[str, Any]:
        query_vector = await mock_vector_service.vectorize_text(request.query)
        results = await mock_vector_service.similarity_search(query_vector, request.limit)
        
        return {
            "query": request.query,
            "search_type": "semantic",
            "results": results,
            "total_results": len(results),
            "response_time_ms": 150
        }
    
    service.semantic_search = AsyncMock(side_effect=mock_semantic_search)
    
    # 模拟混合搜索
    async def mock_hybrid_search(request: SearchRequest) -> Dict[str, Any]:
        semantic_results = await mock_semantic_search(request)
        
        return {
            "query": request.query,
            "search_type": "hybrid",
            "results": semantic_results["results"],
            "semantic_weight": 0.7,
            "keyword_weight": 0.3,
            "total_results": len(semantic_results["results"]),
            "response_time_ms": 200
        }
    
    service.hybrid_search = AsyncMock(side_effect=mock_hybrid_search)
    
    # 模拟智能问答
    async def mock_intelligent_qa(request: SearchRequest) -> Dict[str, Any]:
        search_results = await mock_semantic_search(request)
        
        return {
            "query": request.query,
            "answer": "基于搜索结果生成的智能回答",
            "confidence": 0.85,
            "sources": search_results["results"][:3],
            "response_time_ms": 800
        }
    
    service.intelligent_qa = AsyncMock(side_effect=mock_intelligent_qa)
    
    return service


@pytest.fixture
def sample_documents():
    """示例文档数据"""
    return [
        {
            "id": 1,
            "title": "技术文档1",
            "content": "这是一个关于人工智能和机器学习的技术文档。文档包含了深度学习、神经网络、自然语言处理等相关内容。",
            "metadata": {"category": "技术", "language": "zh"}
        },
        {
            "id": 2,
            "title": "业务报告",
            "content": "本报告分析了公司在过去一年的业务发展情况，包括市场表现、财务状况、客户满意度等关键指标。",
            "metadata": {"category": "业务", "language": "zh"}
        },
        {
            "id": 3,
            "title": "产品规格说明",
            "content": "产品采用先进的技术架构，支持高并发处理，具备良好的扩展性和稳定性。系统集成了多种安全机制。",
            "metadata": {"category": "产品", "language": "zh"}
        }
    ]


@pytest.fixture
def sample_search_requests():
    """示例搜索请求"""
    return [
        SearchRequest(
            query="人工智能技术",
            search_type="semantic",
            limit=10,
            filters={"category": "技术"}
        ),
        SearchRequest(
            query="业务发展情况",
            search_type="hybrid",
            limit=5,
            filters={"language": "zh"}
        ),
        SearchRequest(
            query="系统架构和安全",
            search_type="intelligent_qa",
            limit=3
        )
    ]


@pytest.fixture
def mock_ollama_client():
    """模拟Ollama客户端"""
    client = Mock()
    
    # 模拟嵌入生成
    async def mock_embeddings(model: str, prompt: str) -> Dict[str, Any]:
        return {
            "embedding": [0.1] * 1024,  # 1024维向量
            "model": model
        }
    
    client.embeddings = AsyncMock(side_effect=mock_embeddings)
    
    # 模拟文本生成
    async def mock_generate(model: str, prompt: str) -> Dict[str, Any]:
        return {
            "response": "这是一个模拟的AI生成回答",
            "model": model,
            "done": True
        }
    
    client.generate = AsyncMock(side_effect=mock_generate)
    
    # 模拟模型列表
    async def mock_list() -> Dict[str, Any]:
        return {
            "models": [
                {"name": "bge-m3:latest", "size": 1000000},
                {"name": "deepseek-r1:8b", "size": 5000000}
            ]
        }
    
    client.list = AsyncMock(side_effect=mock_list)
    
    return client


@pytest.fixture
def mock_azure_openai_client():
    """模拟Azure OpenAI客户端"""
    client = Mock()
    
    # 模拟嵌入生成
    async def mock_create_embedding(input_text: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        return {
            "data": [
                {
                    "embedding": [0.1] * 1536,  # Ada-002的1536维向量
                    "index": 0
                }
            ],
            "model": model,
            "usage": {"total_tokens": len(input_text.split())}
        }
    
    client.embeddings.create = AsyncMock(side_effect=mock_create_embedding)
    
    # 模拟聊天完成
    async def mock_create_chat_completion(messages: List[Dict], model: str = "gpt-4") -> Dict[str, Any]:
        return {
            "choices": [
                {
                    "message": {
                        "content": "这是一个模拟的GPT回答",
                        "role": "assistant"
                    },
                    "finish_reason": "stop"
                }
            ],
            "model": model,
            "usage": {"total_tokens": 100}
        }
    
    client.chat.completions.create = AsyncMock(side_effect=mock_create_chat_completion)
    
    return client


@pytest.fixture
def vector_test_data():
    """向量测试数据"""
    return {
        "sample_vectors": {
            "query1": [0.1, 0.2, 0.3] + [0.0] * 1021,  # 1024维向量
            "doc1": [0.15, 0.25, 0.35] + [0.0] * 1021,
            "doc2": [0.8, 0.1, 0.1] + [0.0] * 1021
        },
        "expected_similarities": {
            "query1_doc1": 0.95,  # 高相似度
            "query1_doc2": 0.3    # 低相似度
        }
    }


@pytest.fixture
def performance_test_config():
    """性能测试配置"""
    return {
        "concurrent_requests": 10,
        "test_duration_seconds": 30,
        "max_response_time_ms": 1000,
        "min_throughput_rps": 5,
        "vector_dimensions": 1024,
        "batch_sizes": [1, 5, 10, 20]
    }


# 测试数据库连接夹具
@pytest.fixture
async def test_vector_db():
    """测试向量数据库连接"""
    # 这里应该连接到测试数据库
    # 为了示例，我们使用模拟连接
    db_mock = Mock()
    
    async def mock_execute(query: str, params: tuple = None):
        return Mock(fetchall=lambda: [], fetchone=lambda: None)
    
    db_mock.execute = AsyncMock(side_effect=mock_execute)
    
    yield db_mock
    
    # 清理测试数据
    await db_mock.execute("DELETE FROM document_vectors WHERE document_id < 1000")


# 测试工具函数
def assert_vector_similarity(vector1: List[float], vector2: List[float], threshold: float = 0.8):
    """断言两个向量的相似度"""
    similarity = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
    assert similarity >= threshold, f"向量相似度 {similarity} 低于阈值 {threshold}"


def assert_search_response_format(response: Dict[str, Any]):
    """断言搜索响应格式正确"""
    required_fields = ["query", "search_type", "results", "total_results", "response_time_ms"]
    for field in required_fields:
        assert field in response, f"搜索响应缺少必需字段: {field}"
    
    assert isinstance(response["results"], list), "搜索结果应该是列表"
    assert isinstance(response["total_results"], int), "总结果数应该是整数"
    assert isinstance(response["response_time_ms"], (int, float)), "响应时间应该是数字"


def assert_performance_metrics(metrics: Dict[str, Any], config: Dict[str, Any]):
    """断言性能指标符合要求"""
    assert metrics["avg_response_time_ms"] <= config["max_response_time_ms"], \
        f"平均响应时间 {metrics['avg_response_time_ms']}ms 超过阈值 {config['max_response_time_ms']}ms"
    
    assert metrics["throughput_rps"] >= config["min_throughput_rps"], \
        f"吞吐量 {metrics['throughput_rps']} RPS 低于阈值 {config['min_throughput_rps']} RPS"