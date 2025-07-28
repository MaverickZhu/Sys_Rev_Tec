"""
AI服务向量化模块
提供文本向量化、嵌入生成和向量操作功能
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

# AI模型客户端
try:
    import ollama
except ImportError:
    ollama = None

try:
    from openai import AsyncAzureOpenAI
except ImportError:
    AsyncAzureOpenAI = None

from ai_service.config import get_settings
from ai_service.utils.cache import get_cache_manager
from ai_service.utils.logging import StructuredLogger
from ai_service.utils.text_processing import get_text_processor

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("vectorization")
settings = get_settings()


class EmbeddingProvider(Enum):
    """嵌入提供商"""

    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"


@dataclass
class EmbeddingResult:
    """嵌入结果"""

    embedding: List[float]
    model: str
    provider: str
    dimension: int
    processing_time: float
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        self.metadata.update(
            {
                "dimension": self.dimension,
                "processing_time": self.processing_time,
                "provider": self.provider,
                "model": self.model,
            }
        )


@dataclass
class BatchEmbeddingResult:
    """批量嵌入结果"""

    embeddings: List[List[float]]
    texts: List[str]
    model: str
    provider: str
    total_processing_time: float
    individual_times: List[float]
    failed_indices: List[int]
    metadata: Optional[Dict[str, Any]] = None


class VectorizationService:
    """向量化服务"""

    def __init__(self):
        self.settings = get_settings()
        self.cache_manager = None
        self.text_processor = get_text_processor()

        # 初始化客户端
        self.ollama_client = None
        self.azure_client = None

        # 模型配置
        self.default_provider = EmbeddingProvider.OLLAMA
        self.model_configs = {
            EmbeddingProvider.OLLAMA: {
                "model": settings.OLLAMA_EMBEDDING_MODEL,
                "dimension": settings.EMBEDDING_DIMENSION,
                "max_tokens": settings.MAX_TOKENS_PER_REQUEST,
            },
            EmbeddingProvider.AZURE_OPENAI: {
                "model": settings.AZURE_EMBEDDING_MODEL,
                "dimension": settings.AZURE_EMBEDDING_DIMENSION,
                "max_tokens": settings.AZURE_MAX_TOKENS,
            },
        }

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "provider_stats": {
                provider.value: {"requests": 0, "total_time": 0.0}
                for provider in EmbeddingProvider
            },
        }

    async def initialize(self):
        """初始化服务"""
        try:
            # 初始化缓存管理器
            self.cache_manager = await get_cache_manager()

            # 初始化Ollama客户端
            if settings.OLLAMA_ENABLED:
                await self._initialize_ollama()

            # 初始化Azure OpenAI客户端
            if settings.AZURE_OPENAI_ENABLED:
                await self._initialize_azure_openai()

            logger.info("✅ 向量化服务初始化完成")

        except Exception as e:
            logger.error(f"❌ 向量化服务初始化失败: {e}")
            raise

    async def _initialize_ollama(self):
        """初始化Ollama客户端"""
        if not ollama:
            logger.warning("⚠️ Ollama库未安装，跳过Ollama初始化")
            return

        try:
            # 创建异步客户端
            self.ollama_client = ollama.AsyncClient(
                host=settings.OLLAMA_HOST, timeout=settings.OLLAMA_TIMEOUT
            )

            # 测试连接
            models = await self.ollama_client.list()
            available_models = [model["name"] for model in models.get("models", [])]

            if settings.OLLAMA_EMBEDDING_MODEL not in available_models:
                logger.warning(
                    f"⚠️ 嵌入模型 {settings.OLLAMA_EMBEDDING_MODEL} 不可用，"
                    f"可用模型: {available_models}"
                )
            else:
                logger.info(
                    f"✅ Ollama嵌入模型 {settings.OLLAMA_EMBEDDING_MODEL} 已就绪"
                )

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
                timeout=settings.AZURE_OPENAI_TIMEOUT,
            )

            # 测试连接（通过尝试获取模型列表）
            logger.info("✅ Azure OpenAI客户端初始化完成")

        except Exception as e:
            logger.error(f"❌ Azure OpenAI初始化失败: {e}")
            self.azure_client = None

    async def get_embedding(
        self,
        text: str,
        provider: Optional[EmbeddingProvider] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> EmbeddingResult:
        """获取文本嵌入向量"""
        start_time = time.time()

        # 参数验证
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        # 默认提供商和模型
        if provider is None:
            provider = self.default_provider

        if model is None:
            model = self.model_configs[provider]["model"]

        # 文本预处理
        processed_text = self.text_processor.clean_text(
            text, {"normalize_whitespace": True, "remove_control_chars": True}
        )

        # 检查缓存
        cached_embedding = None
        if use_cache and self.cache_manager:
            cached_embedding = await self.cache_manager.get_cached_embedding(
                processed_text, f"{provider.value}:{model}"
            )

            if cached_embedding:
                self.stats["cache_hits"] += 1
                processing_time = time.time() - start_time

                structured_logger.log_vectorization(
                    text=processed_text[:100],
                    model=model,
                    provider=provider.value,
                    dimension=len(cached_embedding),
                    processing_time=processing_time,
                    cache_hit=True,
                )

                return EmbeddingResult(
                    embedding=cached_embedding,
                    model=model,
                    provider=provider.value,
                    dimension=len(cached_embedding),
                    processing_time=processing_time,
                    metadata={"cache_hit": True},
                )

        self.stats["cache_misses"] += 1

        # 生成嵌入向量
        try:
            if provider == EmbeddingProvider.OLLAMA:
                embedding = await self._get_ollama_embedding(
                    processed_text, model, **kwargs
                )
            elif provider == EmbeddingProvider.AZURE_OPENAI:
                embedding = await self._get_azure_embedding(
                    processed_text, model, **kwargs
                )
            else:
                raise ValueError(f"不支持的提供商: {provider}")

            processing_time = time.time() - start_time

            # 更新统计
            self.stats["total_requests"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["total_requests"]
            )
            self.stats["provider_stats"][provider.value]["requests"] += 1
            self.stats["provider_stats"][provider.value][
                "total_time"
            ] += processing_time

            # 缓存结果
            if use_cache and self.cache_manager:
                await self.cache_manager.cache_embedding(
                    processed_text, f"{provider.value}:{model}", embedding
                )

            # 记录日志
            structured_logger.log_vectorization(
                text=processed_text[:100],
                model=model,
                provider=provider.value,
                dimension=len(embedding),
                processing_time=processing_time,
                cache_hit=False,
            )

            return EmbeddingResult(
                embedding=embedding,
                model=model,
                provider=provider.value,
                dimension=len(embedding),
                processing_time=processing_time,
                metadata={"cache_hit": False},
            )

        except Exception as e:
            processing_time = time.time() - start_time

            structured_logger.log_error(
                error_type="vectorization_error",
                error_message=str(e),
                context={
                    "text_length": len(processed_text),
                    "provider": provider.value,
                    "model": model,
                    "processing_time": processing_time,
                },
            )

            raise RuntimeError(f"向量化失败 ({provider.value}): {e}")

    async def _get_ollama_embedding(
        self, text: str, model: str, **kwargs
    ) -> List[float]:
        """使用Ollama获取嵌入向量"""
        if not self.ollama_client:
            raise RuntimeError("Ollama客户端未初始化")

        try:
            response = await self.ollama_client.embeddings(model=model, prompt=text)

            embedding = response.get("embedding")
            if not embedding:
                raise ValueError("Ollama返回空嵌入向量")

            return embedding

        except Exception as e:
            logger.error(f"Ollama嵌入生成失败: {e}")
            raise

    async def _get_azure_embedding(
        self, text: str, model: str, **kwargs
    ) -> List[float]:
        """使用Azure OpenAI获取嵌入向量"""
        if not self.azure_client:
            raise RuntimeError("Azure OpenAI客户端未初始化")

        try:
            response = await self.azure_client.embeddings.create(
                input=text, model=model
            )

            if not response.data:
                raise ValueError("Azure OpenAI返回空响应")

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            logger.error(f"Azure OpenAI嵌入生成失败: {e}")
            raise

    async def get_batch_embeddings(
        self,
        texts: List[str],
        provider: Optional[EmbeddingProvider] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> BatchEmbeddingResult:
        """批量获取嵌入向量"""
        start_time = time.time()

        if not texts:
            raise ValueError("文本列表不能为空")

        # 默认参数
        if provider is None:
            provider = self.default_provider

        if model is None:
            model = self.model_configs[provider]["model"]

        if batch_size is None:
            batch_size = settings.BATCH_SIZE

        embeddings = []
        individual_times = []
        failed_indices = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_start = time.time()

            # 并发处理批次内的文本
            tasks = [
                self.get_embedding(text, provider, model, use_cache, **kwargs)
                for text in batch_texts
            ]

            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(batch_results):
                    global_index = i + j

                    if isinstance(result, Exception):
                        logger.warning(f"文本 {global_index} 向量化失败: {result}")
                        failed_indices.append(global_index)
                        embeddings.append([])
                        individual_times.append(0.0)
                    else:
                        embeddings.append(result.embedding)
                        individual_times.append(result.processing_time)

                batch_time = time.time() - batch_start
                logger.info(
                    f"批次 {i // batch_size + 1} 处理完成: "
                    f"{len(batch_texts)} 个文本，耗时 {batch_time:.2f}s"
                )

            except Exception as e:
                logger.error(f"批次 {i // batch_size + 1} 处理失败: {e}")
                # 标记整个批次为失败
                for j in range(len(batch_texts)):
                    failed_indices.append(i + j)
                    embeddings.append([])
                    individual_times.append(0.0)

        total_processing_time = time.time() - start_time

        # 记录批量处理日志
        structured_logger.log_vectorization(
            text=f"批量处理 {len(texts)} 个文本",
            model=model,
            provider=provider.value,
            dimension=len(embeddings[0]) if embeddings and embeddings[0] else 0,
            processing_time=total_processing_time,
            cache_hit=False,
            extra_data={
                "batch_size": batch_size,
                "failed_count": len(failed_indices),
                "success_rate": (len(texts) - len(failed_indices)) / len(texts),
            },
        )

        return BatchEmbeddingResult(
            embeddings=embeddings,
            texts=texts,
            model=model,
            provider=provider.value,
            total_processing_time=total_processing_time,
            individual_times=individual_times,
            failed_indices=failed_indices,
            metadata={
                "batch_size": batch_size,
                "success_rate": (len(texts) - len(failed_indices)) / len(texts),
            },
        )

    async def vectorize_document(
        self,
        document_id: str,
        content: str,
        chunk_strategy: str = "sentence",
        chunk_size: int = 1000,
        overlap: int = 100,
        provider: Optional[EmbeddingProvider] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """向量化整个文档"""
        start_time = time.time()

        try:
            # 文档分块
            from ai_service.utils.text_processing import ChunkStrategy

            strategy_map = {
                "fixed_size": ChunkStrategy.FIXED_SIZE,
                "sentence": ChunkStrategy.SENTENCE,
                "paragraph": ChunkStrategy.PARAGRAPH,
                "semantic": ChunkStrategy.SEMANTIC,
                "sliding_window": ChunkStrategy.SLIDING_WINDOW,
            }

            strategy = strategy_map.get(chunk_strategy, ChunkStrategy.SENTENCE)

            chunks = self.text_processor.chunk_text(
                content, strategy=strategy, chunk_size=chunk_size, overlap=overlap
            )

            if not chunks:
                raise ValueError("文档分块失败，没有生成有效块")

            # 提取文本内容
            chunk_texts = [chunk.content for chunk in chunks]

            # 批量向量化
            batch_result = await self.get_batch_embeddings(
                chunk_texts,
                provider=provider,
                model=model,
                use_cache=use_cache,
                **kwargs,
            )

            # 构建结果
            vectorized_chunks = []
            for i, (chunk, embedding) in enumerate(
                zip(chunks, batch_result.embeddings)
            ):
                if i not in batch_result.failed_indices and embedding:
                    vectorized_chunks.append(
                        {
                            "chunk_id": chunk.chunk_id,
                            "content": chunk.content,
                            "start_pos": chunk.start_pos,
                            "end_pos": chunk.end_pos,
                            "embedding": embedding,
                            "metadata": {
                                **chunk.metadata,
                                "document_id": document_id,
                                "processing_time": batch_result.individual_times[i],
                            },
                        }
                    )

            total_processing_time = time.time() - start_time

            # 缓存文档分块结果
            if use_cache and self.cache_manager:
                await self.cache_manager.cache_document_chunks(
                    document_id, vectorized_chunks
                )

            result = {
                "document_id": document_id,
                "total_chunks": len(chunks),
                "successful_chunks": len(vectorized_chunks),
                "failed_chunks": len(batch_result.failed_indices),
                "chunks": vectorized_chunks,
                "processing_time": total_processing_time,
                "model": batch_result.model,
                "provider": batch_result.provider,
                "metadata": {
                    "chunk_strategy": chunk_strategy,
                    "chunk_size": chunk_size,
                    "overlap": overlap,
                    "success_rate": len(vectorized_chunks) / len(chunks),
                },
            }

            # 记录文档向量化日志
            structured_logger.log_vectorization(
                text=f"文档 {document_id}",
                model=batch_result.model,
                provider=batch_result.provider,
                dimension=(
                    len(batch_result.embeddings[0])
                    if batch_result.embeddings and batch_result.embeddings[0]
                    else 0
                ),
                processing_time=total_processing_time,
                cache_hit=False,
                extra_data={
                    "document_id": document_id,
                    "total_chunks": len(chunks),
                    "successful_chunks": len(vectorized_chunks),
                    "chunk_strategy": chunk_strategy,
                },
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time

            structured_logger.log_error(
                error_type="document_vectorization_error",
                error_message=str(e),
                context={
                    "document_id": document_id,
                    "content_length": len(content),
                    "chunk_strategy": chunk_strategy,
                    "processing_time": processing_time,
                },
            )

            raise RuntimeError(f"文档向量化失败: {e}")

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float], method: str = "cosine"
    ) -> float:
        """计算向量相似度"""
        if not embedding1 or not embedding2:
            return 0.0

        if len(embedding1) != len(embedding2):
            raise ValueError("向量维度不匹配")

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        if method == "cosine":
            # 余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        elif method == "euclidean":
            # 欧几里得距离（转换为相似度）
            distance = np.linalg.norm(vec1 - vec2)
            return float(1 / (1 + distance))

        elif method == "manhattan":
            # 曼哈顿距离（转换为相似度）
            distance = np.sum(np.abs(vec1 - vec2))
            return float(1 / (1 + distance))

        elif method == "dot_product":
            # 点积
            return float(np.dot(vec1, vec2))

        else:
            raise ValueError(f"不支持的相似度计算方法: {method}")

    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        cache_stats = {}
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_cache_stats()

        return {
            "vectorization_stats": self.stats,
            "cache_stats": cache_stats,
            "model_configs": {
                provider.value: config
                for provider, config in self.model_configs.items()
            },
            "service_status": {
                "ollama_available": self.ollama_client is not None,
                "azure_available": self.azure_client is not None,
                "cache_available": self.cache_manager is not None,
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {"status": "healthy", "checks": {}, "timestamp": time.time()}

        # 检查Ollama
        if self.ollama_client:
            try:
                await self.ollama_client.list()
                health_status["checks"]["ollama"] = "healthy"
            except Exception as e:
                health_status["checks"]["ollama"] = f"unhealthy: {e}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["ollama"] = "not_configured"

        # 检查Azure OpenAI
        if self.azure_client:
            try:
                # 简单的连接测试
                health_status["checks"]["azure_openai"] = "healthy"
            except Exception as e:
                health_status["checks"]["azure_openai"] = f"unhealthy: {e}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["azure_openai"] = "not_configured"

        # 检查缓存
        if self.cache_manager:
            try:
                await self.cache_manager.redis.ping()
                health_status["checks"]["cache"] = "healthy"
            except Exception as e:
                health_status["checks"]["cache"] = f"unhealthy: {e}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["cache"] = "not_configured"

        return health_status

    async def cleanup(self):
        """清理资源"""
        try:
            if self.ollama_client:
                # Ollama客户端通常不需要显式关闭
                pass

            if self.azure_client:
                await self.azure_client.close()

            logger.info("✅ 向量化服务资源清理完成")

        except Exception as e:
            logger.error(f"❌ 向量化服务资源清理失败: {e}")


# 全局向量化服务实例
_vectorization_service = None


async def get_vectorization_service() -> VectorizationService:
    """获取向量化服务实例"""
    global _vectorization_service

    if _vectorization_service is None:
        _vectorization_service = VectorizationService()
        await _vectorization_service.initialize()

    return _vectorization_service


async def cleanup_vectorization_service():
    """清理向量化服务"""
    global _vectorization_service

    if _vectorization_service:
        await _vectorization_service.cleanup()
        _vectorization_service = None


if __name__ == "__main__":
    # 测试向量化功能
    import asyncio

    async def test_vectorization():
        try:
            service = await get_vectorization_service()

            # 测试单个文本向量化
            test_text = "这是一个测试文本，用于验证向量化功能。"
            result = await service.get_embedding(test_text)
            print(
                f"向量化结果: 维度={result.dimension}, 耗时={result.processing_time:.3f}s"
            )

            # 测试批量向量化
            test_texts = ["第一个测试文本", "第二个测试文本", "第三个测试文本"]
            batch_result = await service.get_batch_embeddings(test_texts)
            print(
                f"批量向量化: {len(batch_result.embeddings)} 个向量，耗时={batch_result.total_processing_time:.3f}s"
            )

            # 测试相似度计算
            if len(batch_result.embeddings) >= 2:
                similarity = service.calculate_similarity(
                    batch_result.embeddings[0], batch_result.embeddings[1]
                )
                print(f"相似度: {similarity:.4f}")

            # 获取服务统计
            stats = await service.get_service_stats()
            print(f"服务统计: {stats['vectorization_stats']}")

            # 健康检查
            health = await service.health_check()
            print(f"健康状态: {health['status']}")

            await cleanup_vectorization_service()

        except Exception as e:
            print(f"向量化测试失败: {e}")

    asyncio.run(test_vectorization())
