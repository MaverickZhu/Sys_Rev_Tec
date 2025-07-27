#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务测试
测试向量化、搜索和相关功能
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from httpx import AsyncClient

# 导入AI服务模块
try:
    from ai_service.main import app
    from ai_service.config import get_settings
    from ai_service.vectorization import VectorizationService, EmbeddingProvider
    from ai_service.search import IntelligentSearchService, SearchType
    from ai_service.utils.text_processing import TextProcessor, ChunkStrategy
    from ai_service.utils.cache import CacheManager
    AI_SERVICE_AVAILABLE = True
except ImportError as e:
    AI_SERVICE_AVAILABLE = False
    pytest.skip(f"AI服务模块不可用: {e}", allow_module_level=True)


class TestAIServiceConfig:
    """AI服务配置测试"""
    
    def test_settings_loading(self):
        """测试配置加载"""
        settings = get_settings()
        
        # 检查基本配置
        assert hasattr(settings, 'AI_SERVICE_HOST')
        assert hasattr(settings, 'AI_SERVICE_PORT')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'REDIS_URL')
        
        # 检查AI配置
        assert hasattr(settings, 'OLLAMA_BASE_URL')
        assert hasattr(settings, 'DEFAULT_EMBEDDING_MODEL')
        assert hasattr(settings, 'VECTOR_DIMENSION')
    
    def test_settings_validation(self):
        """测试配置验证"""
        settings = get_settings()
        
        # 检查端口范围
        assert 1 <= settings.AI_SERVICE_PORT <= 65535
        
        # 检查向量维度
        assert settings.VECTOR_DIMENSION > 0
        
        # 检查缓存配置
        assert settings.CACHE_TTL > 0


class TestTextProcessor:
    """文本处理器测试"""
    
    def setup_method(self):
        """设置测试"""
        self.processor = TextProcessor()
    
    def test_text_cleaning(self):
        """测试文本清理"""
        dirty_text = "  这是一个测试文本。  \n\n  包含多余空格和换行。  "
        cleaned = self.processor.clean_text(dirty_text)
        
        assert cleaned == "这是一个测试文本。 包含多余空格和换行。"
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
    
    def test_language_detection(self):
        """测试语言检测"""
        chinese_text = "这是中文文本"
        english_text = "This is English text"
        mixed_text = "这是中英文混合 mixed text"
        
        assert self.processor.detect_language(chinese_text) == "zh"
        assert self.processor.detect_language(english_text) == "en"
        assert self.processor.detect_language(mixed_text) == "mixed"
    
    def test_sentence_splitting(self):
        """测试句子分割"""
        text = "这是第一句。这是第二句！这是第三句？"
        sentences = self.processor.split_sentences(text)
        
        assert len(sentences) == 3
        assert "这是第一句。" in sentences
        assert "这是第二句！" in sentences
        assert "这是第三句？" in sentences
    
    def test_paragraph_splitting(self):
        """测试段落分割"""
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        paragraphs = self.processor.split_paragraphs(text)
        
        assert len(paragraphs) == 3
        assert "第一段内容。" in paragraphs
        assert "第二段内容。" in paragraphs
        assert "第三段内容。" in paragraphs
    
    def test_text_chunking(self):
        """测试文本分块"""
        long_text = "这是一个很长的文本。" * 50
        
        # 固定大小分块
        chunks = self.processor.chunk_text(
            long_text, 
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=100,
            overlap=20
        )
        
        assert len(chunks) > 1
        assert all(len(chunk.content) <= 120 for chunk in chunks)  # 考虑重叠
        assert all(chunk.chunk_id == i for i, chunk in enumerate(chunks))
    
    def test_keyword_extraction(self):
        """测试关键词提取"""
        text = "人工智能是计算机科学的一个分支。机器学习是人工智能的重要组成部分。"
        keywords = self.processor.extract_keywords(text, max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert "人工智能" in keywords or "智能" in keywords
    
    def test_text_stats(self):
        """测试文本统计"""
        text = "这是测试文本。包含两个句子。"
        stats = self.processor.calculate_text_stats(text)
        
        assert stats["char_count"] > 0
        assert stats["word_count"] > 0
        assert stats["sentence_count"] == 2
        assert stats["language"] == "zh"
        assert "keywords" in stats


class TestCacheManager:
    """缓存管理器测试"""
    
    @pytest.fixture
    async def cache_manager(self):
        """缓存管理器fixture"""
        # 使用模拟的Redis客户端
        with patch('ai_service.utils.cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            cache = CacheManager()
            await cache.initialize()
            
            yield cache, mock_client
            
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache_manager):
        """测试缓存基本操作"""
        cache, mock_client = cache_manager
        
        # 模拟Redis操作
        mock_client.set.return_value = True
        mock_client.get.return_value = json.dumps("test_value")
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = True
        
        # 测试设置和获取
        await cache.set("test_key", "test_value", ttl=3600)
        value = await cache.get("test_key")
        
        assert value == "test_value"
        mock_client.set.assert_called_once()
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_embedding_cache(self, cache_manager):
        """测试嵌入向量缓存"""
        cache, mock_client = cache_manager
        
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_client.set.return_value = True
        mock_client.get.return_value = json.dumps(test_embedding)
        
        # 缓存嵌入向量
        await cache.cache_embedding("test_text", "test_model", test_embedding)
        
        # 获取嵌入向量
        cached_embedding = await cache.get_cached_embedding("test_text", "test_model")
        
        assert cached_embedding == test_embedding


class TestVectorizationService:
    """向量化服务测试"""
    
    def setup_method(self):
        """设置测试"""
        self.service = VectorizationService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.settings is not None
        assert self.service.cache_manager is not None
        assert self.service.text_processor is not None
    
    @pytest.mark.asyncio
    async def test_embedding_generation_mock(self):
        """测试嵌入向量生成（模拟）"""
        with patch.object(self.service, '_get_ollama_embedding') as mock_ollama:
            mock_embedding = [0.1] * 384  # 模拟384维向量
            mock_ollama.return_value = mock_embedding
            
            result = await self.service.get_embedding(
                "测试文本",
                provider=EmbeddingProvider.OLLAMA
            )
            
            assert result.success
            assert result.embedding == mock_embedding
            assert result.model_name is not None
            assert result.dimension == len(mock_embedding)
    
    @pytest.mark.asyncio
    async def test_batch_embedding_mock(self):
        """测试批量嵌入向量生成（模拟）"""
        texts = ["文本1", "文本2", "文本3"]
        
        with patch.object(self.service, 'get_embedding') as mock_get_embedding:
            # 模拟单个嵌入结果
            from ai_service.vectorization import EmbeddingResult
            mock_result = EmbeddingResult(
                success=True,
                embedding=[0.1] * 384,
                model_name="test_model",
                dimension=384,
                processing_time=0.1
            )
            mock_get_embedding.return_value = mock_result
            
            result = await self.service.get_batch_embeddings(texts)
            
            assert result.success
            assert len(result.embeddings) == len(texts)
            assert result.total_texts == len(texts)
            assert result.successful_count == len(texts)
    
    @pytest.mark.asyncio
    async def test_document_vectorization_mock(self):
        """测试文档向量化（模拟）"""
        document_content = "这是一个测试文档。" * 100  # 创建较长文档
        
        with patch.object(self.service, 'get_embedding') as mock_get_embedding:
            from ai_service.vectorization import EmbeddingResult
            mock_result = EmbeddingResult(
                success=True,
                embedding=[0.1] * 384,
                model_name="test_model",
                dimension=384,
                processing_time=0.1
            )
            mock_get_embedding.return_value = mock_result
            
            result = await self.service.vectorize_document(
                document_content,
                document_id="test_doc",
                chunk_strategy=ChunkStrategy.FIXED_SIZE,
                chunk_size=200
            )
            
            assert result.success
            assert len(result.chunks) > 0
            assert all(chunk.embedding is not None for chunk in result.chunks)


class TestIntelligentSearchService:
    """智能搜索服务测试"""
    
    def setup_method(self):
        """设置测试"""
        self.service = IntelligentSearchService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.settings is not None
        assert self.service.vector_db is not None
        assert self.service.vectorization_service is not None
    
    @pytest.mark.asyncio
    async def test_vector_search_mock(self):
        """测试向量搜索（模拟）"""
        with patch.object(self.service.vector_db, 'similarity_search') as mock_search:
            # 模拟搜索结果
            mock_results = [
                {
                    'id': 1,
                    'content': '测试内容1',
                    'similarity': 0.9,
                    'metadata': {'title': '测试文档1'}
                },
                {
                    'id': 2,
                    'content': '测试内容2',
                    'similarity': 0.8,
                    'metadata': {'title': '测试文档2'}
                }
            ]
            mock_search.return_value = mock_results
            
            # 模拟向量化
            with patch.object(self.service.vectorization_service, 'get_embedding') as mock_embedding:
                from ai_service.vectorization import EmbeddingResult
                mock_embedding.return_value = EmbeddingResult(
                    success=True,
                    embedding=[0.1] * 384,
                    model_name="test_model",
                    dimension=384,
                    processing_time=0.1
                )
                
                result = await self.service.search(
                    query="测试查询",
                    search_type=SearchType.VECTOR,
                    limit=10
                )
                
                assert result.success
                assert len(result.results) == 2
                assert result.total_results == 2
                assert all(r.score >= 0.8 for r in result.results)


class TestAIServiceAPI:
    """AI服务API测试"""
    
    def setup_method(self):
        """设置测试"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """测试健康检查"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "AI服务"
        assert "endpoints" in data
    
    def test_metrics_endpoint(self):
        """测试指标端点"""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_vectorization_api_mock(self):
        """测试向量化API（模拟）"""
        with patch('ai_service.api.vectorization.get_vectorization_service') as mock_service:
            # 模拟向量化服务
            mock_instance = AsyncMock()
            from ai_service.vectorization import EmbeddingResult
            mock_instance.get_embedding.return_value = EmbeddingResult(
                success=True,
                embedding=[0.1] * 384,
                model_name="test_model",
                dimension=384,
                processing_time=0.1
            )
            mock_service.return_value = mock_instance
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/vectorization/embed",
                    json={"text": "测试文本"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"]
                assert "embedding" in data
                assert len(data["embedding"]) == 384
    
    @pytest.mark.asyncio
    async def test_search_api_mock(self):
        """测试搜索API（模拟）"""
        with patch('ai_service.api.search.get_search_service') as mock_service:
            # 模拟搜索服务
            mock_instance = AsyncMock()
            from ai_service.search import SearchResponse, SearchResult
            mock_instance.search.return_value = SearchResponse(
                success=True,
                results=[
                    SearchResult(
                        id="1",
                        content="测试内容",
                        score=0.9,
                        metadata={"title": "测试文档"}
                    )
                ],
                total_results=1,
                query="测试查询",
                search_type=SearchType.VECTOR,
                processing_time=0.1
            )
            mock_service.return_value = mock_instance
            
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/v1/search/intelligent",
                    json={
                        "query": "测试查询",
                        "search_type": "vector",
                        "limit": 10
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"]
                assert "results" in data
                assert len(data["results"]) == 1


class TestAIServiceIntegration:
    """AI服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """测试完整工作流程（模拟）"""
        # 这个测试模拟了从文档向量化到搜索的完整流程
        
        # 1. 初始化服务
        vectorization_service = VectorizationService()
        search_service = IntelligentSearchService()
        
        # 2. 模拟文档向量化
        with patch.object(vectorization_service, 'get_embedding') as mock_embedding:
            from ai_service.vectorization import EmbeddingResult
            mock_embedding.return_value = EmbeddingResult(
                success=True,
                embedding=[0.1] * 384,
                model_name="test_model",
                dimension=384,
                processing_time=0.1
            )
            
            doc_result = await vectorization_service.vectorize_document(
                "这是一个测试文档，包含重要信息。",
                document_id="test_doc_1"
            )
            
            assert doc_result.success
            assert len(doc_result.chunks) > 0
        
        # 3. 模拟搜索
        with patch.object(search_service.vector_db, 'similarity_search') as mock_search:
            mock_search.return_value = [
                {
                    'id': 1,
                    'content': '这是一个测试文档，包含重要信息。',
                    'similarity': 0.95,
                    'metadata': {'document_id': 'test_doc_1'}
                }
            ]
            
            with patch.object(search_service.vectorization_service, 'get_embedding') as mock_query_embedding:
                mock_query_embedding.return_value = EmbeddingResult(
                    success=True,
                    embedding=[0.1] * 384,
                    model_name="test_model",
                    dimension=384,
                    processing_time=0.1
                )
                
                search_result = await search_service.search(
                    query="测试文档",
                    search_type=SearchType.VECTOR
                )
                
                assert search_result.success
                assert len(search_result.results) == 1
                assert search_result.results[0].score >= 0.9


if __name__ == "__main__":
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])