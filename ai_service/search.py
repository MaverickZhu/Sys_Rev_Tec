# -*- coding: utf-8 -*-
"""
AI服务智能搜索模块
提供向量搜索、语义搜索、混合搜索和智能问答功能
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    import ollama
except ImportError:
    ollama = None

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None

from ai_service.config import get_settings
from ai_service.database import get_vector_database
from ai_service.vectorization import get_vectorization_service, EmbeddingProvider
from ai_service.utils.cache import get_cache_manager
from ai_service.utils.text_processing import get_text_processor
from ai_service.utils.logging import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger()
settings = get_settings()


class SearchType(Enum):
    """搜索类型"""
    VECTOR = "vector"              # 纯向量搜索
    TEXT = "text"                  # 纯文本搜索
    HYBRID = "hybrid"              # 混合搜索
    SEMANTIC = "semantic"          # 语义搜索
    QUESTION_ANSWER = "qa"         # 问答搜索


class RerankMethod(Enum):
    """重排序方法"""
    NONE = "none"
    SIMILARITY = "similarity"
    RELEVANCE = "relevance"
    DIVERSITY = "diversity"
    LLM_RERANK = "llm_rerank"


@dataclass
class SearchFilter:
    """搜索过滤器"""
    document_types: Optional[List[str]] = None
    date_range: Optional[Tuple[str, str]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    min_score: Optional[float] = None
    max_results: Optional[int] = None


@dataclass
class SearchResult:
    """搜索结果项"""
    document_id: str
    chunk_id: int
    content: str
    score: float
    metadata: Dict[str, Any]
    highlights: Optional[List[str]] = None
    explanation: Optional[str] = None


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    search_type: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    metadata: Dict[str, Any]
    suggestions: Optional[List[str]] = None
    answer: Optional[str] = None  # 用于问答搜索


class IntelligentSearchService:
    """智能搜索服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_db = None
        self.vectorization_service = None
        self.cache_manager = None
        self.text_processor = get_text_processor()
        
        # LLM客户端（用于问答和重排序）
        self.ollama_client = None
        self.azure_client = None
        
        # 搜索配置
        self.default_search_config = {
            "max_results": settings.MAX_SEARCH_RESULTS,
            "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            "rerank_top_k": settings.RERANK_TOP_K,
            "enable_highlights": True,
            "enable_explanations": False
        }
        
        # 性能统计
        self.stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "search_type_stats": {search_type.value: {"count": 0, "total_time": 0.0} for search_type in SearchType}
        }
    
    async def initialize(self):
        """初始化服务"""
        try:
            # 初始化依赖服务
            self.vector_db = await get_vector_database()
            self.vectorization_service = await get_vectorization_service()
            self.cache_manager = await get_cache_manager()
            
            # 初始化LLM客户端
            if settings.OLLAMA_ENABLED:
                await self._initialize_ollama()
            
            if settings.AZURE_OPENAI_ENABLED:
                await self._initialize_azure_openai()
            
            logger.info("✅ 智能搜索服务初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 智能搜索服务初始化失败: {e}")
            raise
    
    async def _initialize_ollama(self):
        """初始化Ollama客户端"""
        if not ollama:
            logger.warning("⚠️ Ollama库未安装，跳过Ollama初始化")
            return
        
        try:
            self.ollama_client = ollama.AsyncClient(
                host=settings.OLLAMA_HOST,
                timeout=settings.OLLAMA_TIMEOUT
            )
            
            # 测试连接
            models = await self.ollama_client.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            if settings.OLLAMA_CHAT_MODEL not in available_models:
                logger.warning(
                    f"⚠️ 聊天模型 {settings.OLLAMA_CHAT_MODEL} 不可用，"
                    f"可用模型: {available_models}"
                )
            else:
                logger.info(f"✅ Ollama聊天模型 {settings.OLLAMA_CHAT_MODEL} 已就绪")
            
        except Exception as e:
            logger.error(f"❌ Ollama初始化失败: {e}")
            self.ollama_client = None
    
    async def _initialize_azure_openai(self):
        """初始化Azure OpenAI客户端"""
        if not AsyncAzureOpenAI:
            logger.warning("⚠️ Azure OpenAI库未安装，跳过Azure初始化")
            return
        
        try:
            self.azure_client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                timeout=settings.AZURE_OPENAI_TIMEOUT
            )
            
            logger.info(f"✅ Azure OpenAI客户端初始化完成")
            
        except Exception as e:
            logger.error(f"❌ Azure OpenAI初始化失败: {e}")
            self.azure_client = None
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        filters: Optional[SearchFilter] = None,
        rerank_method: RerankMethod = RerankMethod.SIMILARITY,
        use_cache: bool = True,
        **kwargs
    ) -> SearchResponse:
        """执行智能搜索"""
        start_time = time.time()
        
        # 参数验证
        if not query or not query.strip():
            raise ValueError("查询不能为空")
        
        # 预处理查询
        processed_query = self.text_processor.clean_text(query, {
            'normalize_whitespace': True,
            'remove_control_chars': True
        })
        
        # 检查缓存
        cached_results = None
        if use_cache and self.cache_manager:
            cache_key_data = {
                "query": processed_query,
                "search_type": search_type.value,
                "filters": filters.__dict__ if filters else None,
                "rerank_method": rerank_method.value
            }
            
            cached_results = await self.cache_manager.get_cached_search_results(
                processed_query,
                search_type.value,
                cache_key_data
            )
            
            if cached_results:
                self.stats["cache_hits"] += 1
                processing_time = time.time() - start_time
                
                structured_logger.log_search(
                    query=processed_query,
                    search_type=search_type.value,
                    result_count=len(cached_results),
                    processing_time=processing_time,
                    cache_hit=True
                )
                
                return SearchResponse(
                    query=processed_query,
                    search_type=search_type.value,
                    results=[SearchResult(**result) for result in cached_results],
                    total_results=len(cached_results),
                    processing_time=processing_time,
                    metadata={"cache_hit": True}
                )
        
        self.stats["cache_misses"] += 1
        
        # 执行搜索
        try:
            if search_type == SearchType.VECTOR:
                results = await self._vector_search(processed_query, filters, **kwargs)
            elif search_type == SearchType.TEXT:
                results = await self._text_search(processed_query, filters, **kwargs)
            elif search_type == SearchType.HYBRID:
                results = await self._hybrid_search(processed_query, filters, **kwargs)
            elif search_type == SearchType.SEMANTIC:
                results = await self._semantic_search(processed_query, filters, **kwargs)
            elif search_type == SearchType.QUESTION_ANSWER:
                results = await self._question_answer_search(processed_query, filters, **kwargs)
            else:
                raise ValueError(f"不支持的搜索类型: {search_type}")
            
            # 重排序
            if rerank_method != RerankMethod.NONE and results:
                results = await self._rerank_results(
                    processed_query, results, rerank_method, **kwargs
                )
            
            # 生成高亮和解释
            if kwargs.get('enable_highlights', self.default_search_config['enable_highlights']):
                results = await self._add_highlights(processed_query, results)
            
            if kwargs.get('enable_explanations', self.default_search_config['enable_explanations']):
                results = await self._add_explanations(processed_query, results)
            
            processing_time = time.time() - start_time
            
            # 更新统计
            self.stats["total_searches"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["total_searches"]
            )
            self.stats["search_type_stats"][search_type.value]["count"] += 1
            self.stats["search_type_stats"][search_type.value]["total_time"] += processing_time
            
            # 构建响应
            response = SearchResponse(
                query=processed_query,
                search_type=search_type.value,
                results=results,
                total_results=len(results),
                processing_time=processing_time,
                metadata={
                    "cache_hit": False,
                    "rerank_method": rerank_method.value,
                    "filters_applied": filters is not None
                }
            )
            
            # 缓存结果
            if use_cache and self.cache_manager and results:
                cache_data = {
                    "query": processed_query,
                    "search_type": search_type.value,
                    "filters": cache_key_data
                }
                
                await self.cache_manager.cache_search_results(
                    processed_query,
                    search_type.value,
                    [result.__dict__ for result in results],
                    cache_data
                )
            
            # 记录搜索日志
            structured_logger.log_search(
                query=processed_query,
                search_type=search_type.value,
                result_count=len(results),
                processing_time=processing_time,
                cache_hit=False,
                extra_data={
                    "rerank_method": rerank_method.value,
                    "filters_applied": filters is not None
                }
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            structured_logger.log_error(
                error_type="search_error",
                error_message=str(e),
                context={
                    "query": processed_query,
                    "search_type": search_type.value,
                    "processing_time": processing_time
                }
            )
            
            raise RuntimeError(f"搜索失败 ({search_type.value}): {e}")
    
    async def _vector_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        **kwargs
    ) -> List[SearchResult]:
        """向量搜索"""
        # 生成查询向量
        embedding_result = await self.vectorization_service.get_embedding(query)
        query_vector = embedding_result.embedding
        
        # 设置搜索参数
        limit = kwargs.get('max_results', self.default_search_config['max_results'])
        similarity_threshold = kwargs.get(
            'similarity_threshold',
            self.default_search_config['similarity_threshold']
        )
        
        # 执行向量搜索
        db_results = await self.vector_db.search_similar_documents(
            query_vector=query_vector,
            limit=limit,
            similarity_threshold=similarity_threshold,
            metadata_filter=filters.metadata_filters if filters else None
        )
        
        # 转换结果格式
        results = []
        for db_result in db_results:
            result = SearchResult(
                document_id=db_result['document_id'],
                chunk_id=db_result['chunk_id'],
                content=db_result['content'],
                score=float(db_result['similarity']),
                metadata=db_result.get('metadata', {})
            )
            results.append(result)
        
        return results
    
    async def _text_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        **kwargs
    ) -> List[SearchResult]:
        """文本搜索"""
        # 设置搜索参数
        limit = kwargs.get('max_results', self.default_search_config['max_results'])
        
        # 执行文本搜索
        db_results = await self.vector_db.search_documents_by_text(
            query_text=query,
            limit=limit,
            metadata_filter=filters.metadata_filters if filters else None
        )
        
        # 转换结果格式
        results = []
        for db_result in db_results:
            # 计算文本相似度分数（简化版）
            score = self._calculate_text_similarity(query, db_result['content'])
            
            result = SearchResult(
                document_id=db_result['document_id'],
                chunk_id=db_result['chunk_id'],
                content=db_result['content'],
                score=score,
                metadata=db_result.get('metadata', {})
            )
            results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    async def _hybrid_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        **kwargs
    ) -> List[SearchResult]:
        """混合搜索（向量+文本）"""
        # 并行执行向量搜索和文本搜索
        vector_task = self._vector_search(query, filters, **kwargs)
        text_task = self._text_search(query, filters, **kwargs)
        
        vector_results, text_results = await asyncio.gather(vector_task, text_task)
        
        # 合并和去重结果
        combined_results = {}
        
        # 添加向量搜索结果
        for result in vector_results:
            key = f"{result.document_id}_{result.chunk_id}"
            combined_results[key] = result
            # 标记来源
            result.metadata['search_source'] = 'vector'
        
        # 添加文本搜索结果
        for result in text_results:
            key = f"{result.document_id}_{result.chunk_id}"
            if key in combined_results:
                # 如果已存在，合并分数
                existing = combined_results[key]
                # 使用加权平均
                vector_weight = kwargs.get('vector_weight', 0.7)
                text_weight = kwargs.get('text_weight', 0.3)
                
                combined_score = (
                    existing.score * vector_weight + 
                    result.score * text_weight
                )
                existing.score = combined_score
                existing.metadata['search_source'] = 'hybrid'
            else:
                combined_results[key] = result
                result.metadata['search_source'] = 'text'
        
        # 转换为列表并排序
        results = list(combined_results.values())
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 限制结果数量
        max_results = kwargs.get('max_results', self.default_search_config['max_results'])
        return results[:max_results]
    
    async def _semantic_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        **kwargs
    ) -> List[SearchResult]:
        """语义搜索"""
        # 首先执行向量搜索获取候选结果
        candidate_results = await self._vector_search(query, filters, **kwargs)
        
        # 如果没有LLM客户端，直接返回向量搜索结果
        if not self.ollama_client and not self.azure_client:
            return candidate_results
        
        # 使用LLM进行语义理解和重排序
        if len(candidate_results) > 1:
            semantic_results = await self._semantic_rerank(
                query, candidate_results, **kwargs
            )
            return semantic_results
        
        return candidate_results
    
    async def _question_answer_search(
        self,
        query: str,
        filters: Optional[SearchFilter] = None,
        **kwargs
    ) -> List[SearchResult]:
        """问答搜索"""
        # 首先获取相关文档
        context_results = await self._hybrid_search(query, filters, **kwargs)
        
        if not context_results:
            return []
        
        # 使用LLM生成答案
        if self.ollama_client or self.azure_client:
            try:
                answer = await self._generate_answer(query, context_results, **kwargs)
                
                # 将答案作为第一个结果
                answer_result = SearchResult(
                    document_id="generated_answer",
                    chunk_id=0,
                    content=answer,
                    score=1.0,
                    metadata={
                        "type": "generated_answer",
                        "source_count": len(context_results)
                    }
                )
                
                # 返回答案和相关文档
                return [answer_result] + context_results[:5]
                
            except Exception as e:
                logger.warning(f"答案生成失败: {e}")
        
        # 如果答案生成失败，返回相关文档
        return context_results
    
    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        method: RerankMethod,
        **kwargs
    ) -> List[SearchResult]:
        """重排序结果"""
        if not results or method == RerankMethod.NONE:
            return results
        
        if method == RerankMethod.SIMILARITY:
            # 基于相似度重排序（已经按相似度排序）
            return results
        
        elif method == RerankMethod.RELEVANCE:
            # 基于相关性重排序
            return await self._relevance_rerank(query, results, **kwargs)
        
        elif method == RerankMethod.DIVERSITY:
            # 基于多样性重排序
            return await self._diversity_rerank(results, **kwargs)
        
        elif method == RerankMethod.LLM_RERANK:
            # 基于LLM重排序
            return await self._llm_rerank(query, results, **kwargs)
        
        return results
    
    async def _semantic_rerank(
        self,
        query: str,
        results: List[SearchResult],
        **kwargs
    ) -> List[SearchResult]:
        """语义重排序"""
        if not results:
            return results
        
        try:
            # 构建语义分析提示
            context_texts = [result.content for result in results[:10]]  # 限制上下文长度
            
            prompt = f"""
请分析以下查询和文档片段的语义相关性，并按相关性从高到低排序。

查询: {query}

文档片段:
"""
            
            for i, text in enumerate(context_texts):
                prompt += f"{i+1}. {text[:200]}...\n\n"
            
            prompt += """
请返回一个JSON数组，包含按相关性排序的文档编号（1-based）。
例如: [3, 1, 5, 2, 4]
"""
            
            # 使用LLM进行语义分析
            response = await self._call_llm(prompt, max_tokens=100)
            
            # 解析排序结果
            try:
                ranking = json.loads(response.strip())
                if isinstance(ranking, list) and all(isinstance(x, int) for x in ranking):
                    # 重新排序结果
                    reranked_results = []
                    for rank in ranking:
                        if 1 <= rank <= len(results):
                            reranked_results.append(results[rank - 1])
                    
                    # 添加未排序的结果
                    ranked_indices = set(rank - 1 for rank in ranking if 1 <= rank <= len(results))
                    for i, result in enumerate(results):
                        if i not in ranked_indices:
                            reranked_results.append(result)
                    
                    return reranked_results
            except (json.JSONDecodeError, ValueError):
                logger.warning("语义重排序响应解析失败，使用原始排序")
        
        except Exception as e:
            logger.warning(f"语义重排序失败: {e}")
        
        return results
    
    async def _relevance_rerank(
        self,
        query: str,
        results: List[SearchResult],
        **kwargs
    ) -> List[SearchResult]:
        """相关性重排序"""
        # 简化的相关性计算
        query_keywords = set(self.text_processor.extract_keywords(query, max_keywords=10))
        
        for result in results:
            content_keywords = set(self.text_processor.extract_keywords(result.content, max_keywords=20))
            
            # 计算关键词重叠度
            overlap = len(query_keywords & content_keywords)
            total_keywords = len(query_keywords | content_keywords)
            
            if total_keywords > 0:
                keyword_score = overlap / total_keywords
                # 结合原始分数和关键词分数
                result.score = result.score * 0.7 + keyword_score * 0.3
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _diversity_rerank(
        self,
        results: List[SearchResult],
        **kwargs
    ) -> List[SearchResult]:
        """多样性重排序"""
        if len(results) <= 1:
            return results
        
        # 简化的多样性算法：确保不同文档的结果分散
        diverse_results = []
        used_documents = set()
        
        # 第一轮：每个文档选择最好的结果
        for result in results:
            if result.document_id not in used_documents:
                diverse_results.append(result)
                used_documents.add(result.document_id)
        
        # 第二轮：添加剩余结果
        for result in results:
            if result not in diverse_results:
                diverse_results.append(result)
        
        return diverse_results
    
    async def _llm_rerank(
        self,
        query: str,
        results: List[SearchResult],
        **kwargs
    ) -> List[SearchResult]:
        """LLM重排序"""
        return await self._semantic_rerank(query, results, **kwargs)
    
    async def _generate_answer(
        self,
        query: str,
        context_results: List[SearchResult],
        **kwargs
    ) -> str:
        """生成答案"""
        if not context_results:
            return "抱歉，没有找到相关信息来回答您的问题。"
        
        # 构建上下文
        context_texts = []
        for i, result in enumerate(context_results[:5]):  # 限制上下文长度
            context_texts.append(f"文档{i+1}: {result.content}")
        
        context = "\n\n".join(context_texts)
        
        # 构建问答提示
        prompt = f"""
基于以下文档内容，请回答用户的问题。如果文档中没有足够的信息来回答问题，请诚实地说明。

问题: {query}

相关文档:
{context}

请提供一个准确、简洁的答案:
"""
        
        try:
            answer = await self._call_llm(prompt, max_tokens=500)
            return answer.strip()
        
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，在生成答案时遇到了问题。"
    
    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.1
    ) -> str:
        """调用LLM"""
        # 优先使用Ollama
        if self.ollama_client:
            try:
                response = await self.ollama_client.generate(
                    model=settings.OLLAMA_CHAT_MODEL,
                    prompt=prompt,
                    options={
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                )
                return response.get('response', '')
            
            except Exception as e:
                logger.warning(f"Ollama调用失败: {e}")
        
        # 备用Azure OpenAI
        if self.azure_client:
            try:
                response = await self.azure_client.chat.completions.create(
                    model=settings.AZURE_CHAT_MODEL,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return response.choices[0].message.content
            
            except Exception as e:
                logger.warning(f"Azure OpenAI调用失败: {e}")
        
        raise RuntimeError("没有可用的LLM服务")
    
    async def _add_highlights(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """添加高亮"""
        query_keywords = self.text_processor.extract_keywords(query, max_keywords=10)
        
        for result in results:
            highlights = []
            content_lower = result.content.lower()
            
            for keyword in query_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in content_lower:
                    # 找到关键词周围的上下文
                    start_pos = content_lower.find(keyword_lower)
                    if start_pos != -1:
                        context_start = max(0, start_pos - 50)
                        context_end = min(len(result.content), start_pos + len(keyword) + 50)
                        highlight = result.content[context_start:context_end]
                        highlights.append(highlight)
            
            result.highlights = highlights[:3]  # 限制高亮数量
        
        return results
    
    async def _add_explanations(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """添加解释"""
        for result in results:
            # 简化的解释生成
            explanation_parts = []
            
            if result.score > 0.8:
                explanation_parts.append("高度相关")
            elif result.score > 0.6:
                explanation_parts.append("中度相关")
            else:
                explanation_parts.append("低度相关")
            
            if 'search_source' in result.metadata:
                source = result.metadata['search_source']
                if source == 'vector':
                    explanation_parts.append("基于语义相似度匹配")
                elif source == 'text':
                    explanation_parts.append("基于关键词匹配")
                elif source == 'hybrid':
                    explanation_parts.append("基于语义和关键词混合匹配")
            
            result.explanation = "，".join(explanation_parts)
        
        return results
    
    def _calculate_text_similarity(self, query: str, content: str) -> float:
        """计算文本相似度（简化版）"""
        query_keywords = set(self.text_processor.extract_keywords(query, max_keywords=10))
        content_keywords = set(self.text_processor.extract_keywords(content, max_keywords=20))
        
        if not query_keywords:
            return 0.0
        
        overlap = len(query_keywords & content_keywords)
        return overlap / len(query_keywords)
    
    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """获取搜索建议"""
        # 这里可以实现基于历史搜索、热门查询等的建议算法
        # 简化版：返回一些通用建议
        suggestions = [
            f"{partial_query} 是什么",
            f"{partial_query} 如何使用",
            f"{partial_query} 的优缺点",
            f"{partial_query} 相关技术",
            f"{partial_query} 最佳实践"
        ]
        
        return suggestions[:limit]
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        cache_stats = {}
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_cache_stats()
        
        return {
            "search_stats": self.stats,
            "cache_stats": cache_stats,
            "service_status": {
                "vector_db_available": self.vector_db is not None,
                "vectorization_available": self.vectorization_service is not None,
                "ollama_available": self.ollama_client is not None,
                "azure_available": self.azure_client is not None,
                "cache_available": self.cache_manager is not None
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": time.time()
        }
        
        # 检查向量数据库
        if self.vector_db:
            try:
                await self.vector_db.health_check()
                health_status["checks"]["vector_db"] = "healthy"
            except Exception as e:
                health_status["checks"]["vector_db"] = f"unhealthy: {e}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["vector_db"] = "not_configured"
        
        # 检查向量化服务
        if self.vectorization_service:
            try:
                vectorization_health = await self.vectorization_service.health_check()
                if vectorization_health["status"] == "healthy":
                    health_status["checks"]["vectorization"] = "healthy"
                else:
                    health_status["checks"]["vectorization"] = "degraded"
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["checks"]["vectorization"] = f"unhealthy: {e}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["vectorization"] = "not_configured"
        
        return health_status
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.azure_client:
                await self.azure_client.close()
            
            logger.info("✅ 智能搜索服务资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 智能搜索服务资源清理失败: {e}")


# 全局搜索服务实例
_search_service = None


async def get_search_service() -> IntelligentSearchService:
    """获取搜索服务实例"""
    global _search_service
    
    if _search_service is None:
        _search_service = IntelligentSearchService()
        await _search_service.initialize()
    
    return _search_service


async def cleanup_search_service():
    """清理搜索服务"""
    global _search_service
    
    if _search_service:
        await _search_service.cleanup()
        _search_service = None


if __name__ == "__main__":
    # 测试搜索功能
    import asyncio
    
    async def test_search():
        try:
            service = await get_search_service()
            
            # 测试向量搜索
            query = "人工智能的应用"
            response = await service.search(query, SearchType.VECTOR)
            print(f"向量搜索结果: {len(response.results)} 个，耗时 {response.processing_time:.3f}s")
            
            # 测试混合搜索
            response = await service.search(query, SearchType.HYBRID)
            print(f"混合搜索结果: {len(response.results)} 个，耗时 {response.processing_time:.3f}s")
            
            # 测试问答搜索
            qa_query = "什么是机器学习？"
            response = await service.search(qa_query, SearchType.QUESTION_ANSWER)
            print(f"问答搜索结果: {len(response.results)} 个")
            if response.results and response.results[0].metadata.get('type') == 'generated_answer':
                print(f"生成答案: {response.results[0].content[:100]}...")
            
            # 获取搜索建议
            suggestions = await service.get_search_suggestions("机器学习")
            print(f"搜索建议: {suggestions}")
            
            # 获取服务统计
            stats = await service.get_service_stats()
            print(f"服务统计: {stats['search_stats']}")
            
            # 健康检查
            health = await service.health_check()
            print(f"健康状态: {health['status']}")
            
            await cleanup_search_service()
            
        except Exception as e:
            print(f"搜索测试失败: {e}")
    
    asyncio.run(test_search())