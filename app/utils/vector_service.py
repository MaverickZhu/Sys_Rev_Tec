import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None
try:
    import weaviate
except ImportError:
    weaviate = None
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.models.vector import DocumentVector
from app.utils.ai_integration import AIIntegrationService
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor

# from app.models.document import Document
# from app.models.vector import Vector
# from fastapi import status

logger = logging.getLogger(__name__)


class VectorService:
    """
    向量服务 - 管理文档向量化、搜索和索引
    """

    def __init__(self, ai_service: AIIntegrationService):
        self.ai_service = ai_service
        self.cache_manager = CacheManager()
        self.text_processor = TextProcessor()

        # 初始化向量存储并过滤掉None的存储
        all_stores = {
            "memory": MemoryVectorStore(),
            "chroma": (ChromaVectorStore() if settings.CHROMA_HOST else None),
            "pinecone": (
                PineconeVectorStore()
                if settings.PINECONE_API_KEY and Pinecone
                else None
            ),
            "weaviate": (
                WeaviateVectorStore() if settings.WEAVIATE_URL and weaviate else None
            ),
        }

        self.vector_stores = {k: v for k, v in all_stores.items() if v is not None}

        # 默认使用的向量存储
        self.default_store = settings.DEFAULT_VECTOR_STORE or "memory"

    async def semantic_search(
        self,
        db: Session,
        query: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        vector_store: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        执行语义搜索

        Args:
            db: 数据库会话
            query: 搜索查询
            similarity_threshold: 相似度阈值
            max_results: 最大结果数
            document_ids: 限制搜索的文档ID列表
            filter_params: 过滤参数
            vector_store: 指定使用的向量存储
        Returns:
            搜索结果列表
        """
        try:
            start_time = datetime.utcnow()

            # 检查缓存
            cache_key = (
                f"search:{hash(query)}:{similarity_threshold}:"
                f"{max_results}:{hash(str(document_ids))}:"
                f"{hash(str(filter_params))}"
            )
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Using cached search result for query: {query[:50]}...")
                return json.loads(cached_result)

            # 获取查询向量
            query_embedding = await self.ai_service._get_text_embedding(query)

            # 选择向量存储
            store_name = vector_store or self.default_store
            vector_store_instance = self.vector_stores.get(store_name)

            if not vector_store_instance:
                # Fallback到数据库搜索
                results = await self._database_vector_search(
                    db,
                    query_embedding,
                    similarity_threshold,
                    max_results,
                    document_ids,
                    filter_params,
                )
            else:
                # 使用向量存储搜索
                results = await vector_store_instance.search(
                    query_embedding,
                    similarity_threshold,
                    max_results,
                    document_ids,
                    filter_params,
                )

            # 增强搜索结果
            enhanced_results = await self._enhance_search_results(db, results)

            # 计算搜索时间
            search_time = (datetime.utcnow() - start_time).total_seconds()

            # 添加搜索元数据
            for result in enhanced_results:
                result["search_time"] = search_time
                result["query"] = query
                result["vector_store"] = store_name

            # 缓存结果
            await self.cache_manager.set(
                cache_key,
                json.dumps(enhanced_results, default=str),
                ttl=300,  # 5分钟缓存
            )

            logger.info(
                f"Semantic search completed: {len(enhanced_results)} results in {search_time:.2f}s"
            )
            return enhanced_results

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise

    async def _database_vector_search(
        self,
        db: Session,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        使用数据库进行向量搜索
        """
        try:
            # 构建查询
            query = db.query(models.DocumentVector)

            # 添加文档过滤
            if document_ids:
                query = query.filter(
                    models.DocumentVector.document_id.in_(document_ids)
                )

            # 添加其他过滤条件
            if filter_params:
                if "topic_category" in filter_params:
                    query = query.filter(
                        models.DocumentVector.topic_category
                        == filter_params["topic_category"]
                    )
                if "min_importance" in filter_params:
                    query = query.filter(
                        models.DocumentVector.importance_score
                        >= filter_params["min_importance"]
                    )
                if "vector_model" in filter_params:
                    query = query.filter(
                        models.DocumentVector.vector_model
                        == filter_params["vector_model"]
                    )

            # 获取所有向量
            vectors = query.all()

            # 计算相似度
            similarities = []
            for vector in vectors:
                if vector.embedding_vector:
                    similarity = self.ai_service._calculate_cosine_similarity(
                        query_embedding, vector.embedding_vector
                    )
                    if similarity >= similarity_threshold:
                        similarities.append(
                            {
                                "vector_id": vector.id,
                                "document_id": vector.document_id,
                                "chunk_index": vector.chunk_index,
                                "chunk_text": vector.chunk_text,
                                "similarity": similarity,
                                "topic_category": vector.topic_category,
                                "importance_score": vector.importance_score,
                                "vector_model": vector.vector_model,
                            }
                        )

            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)

            return similarities[:max_results]

        except Exception as e:
            logger.error(f"Database vector search failed: {str(e)}")
            raise

    async def _enhance_search_results(
        self, db: Session, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        增强搜索结果,添加文档信息
        """
        try:
            enhanced_results = []

            for result in results:
                # 获取文档信息
                document = crud.document.get(db=db, id=result["document_id"])
                if document:
                    enhanced_result = result.copy()
                    enhanced_result.update(
                        {
                            "document_title": document.title,
                            "document_filename": document.filename,
                            "document_type": document.document_type,
                            "document_status": document.status,
                            "document_created_at": document.created_at,
                            "document_updated_at": document.updated_at,
                            "document_classification": document.document_classification,
                            "document_ai_summary": document.ai_summary,
                        }
                    )
                    enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            logger.error(f"Failed to enhance search results: {str(e)}")
            return results

    async def build_vector_index(
        self,
        db: Session,
        index_name: str,
        document_ids: Optional[List[int]] = None,
        vector_store: Optional[str] = None,
        rebuild: bool = False,
    ) -> Dict[str, Any]:
        """
        构建向量索引

        Args:
            db: 数据库会话
            index_name: 索引名称
            document_ids: 要索引的文档ID列表
            vector_store: 向量存储类型
            rebuild: 是否重建索引

        Returns:
            索引构建结果
        """
        try:
            start_time = datetime.utcnow()

            # 检查索引是否已存在
            existing_index = crud.vector_search_index.get_by_name(
                db=db, index_name=index_name
            )
            if existing_index and not rebuild:
                return {
                    "status": "exists",
                    "message": ("Index already exists. Use rebuild=True to rebuild."),
                    "index_id": existing_index.id,
                }

            # 获取要索引的向量
            query = db.query(models.DocumentVector)
            if document_ids:
                query = query.filter(
                    models.DocumentVector.document_id.in_(document_ids)
                )

            vectors = query.all()

            if not vectors:
                raise ValueError("No vectors found to index")

            # 选择向量存储
            store_name = vector_store or self.default_store
            vector_store_instance = self.vector_stores.get(store_name)

            if vector_store_instance:
                # 使用向量存储构建索引
                index_result = await vector_store_instance.build_index(
                    index_name, vectors, rebuild
                )
            else:
                # 使用内存存储
                index_result = await self._build_memory_index(index_name, vectors)

            # 保存或更新索引信息
            if existing_index:
                index_data = schemas.VectorSearchIndexUpdate(
                    total_vectors=len(vectors),
                    index_size=index_result.get("index_size", 0),
                    last_rebuild_at=datetime.utcnow(),
                    is_active=True,
                )
                updated_index = crud.vector_search_index.update(
                    db=db, db_obj=existing_index, obj_in=index_data
                )
                index_id = updated_index.id
            else:
                index_data = schemas.VectorSearchIndexCreate(
                    index_name=index_name,
                    vector_store_type=store_name,
                    total_vectors=len(vectors),
                    index_size=index_result.get("index_size", 0),
                    configuration={"similarity_metric": "cosine"},
                    is_active=True,
                )
                new_index = crud.vector_search_index.create(db=db, obj_in=index_data)
                index_id = new_index.id

            build_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Vector index '{index_name}' built successfully in "
                f"{build_time:.2f}s"
            )

            return {
                "status": "success",
                "index_id": index_id,
                "index_name": index_name,
                "vector_store": store_name,
                "total_vectors": len(vectors),
                "build_time": build_time,
                "index_size": index_result.get("index_size", 0),
            }

        except Exception as e:
            logger.error(f"Failed to build vector index: {str(e)}")
            raise

    async def _build_memory_index(
        self, index_name: str, vectors: List[DocumentVector]
    ) -> Dict[str, Any]:
        """
        构建内存向量索引
        """
        try:
            # 简单的内存索引实现
            index_data = {"vectors": [], "metadata": []}

            for vector in vectors:
                if vector.embedding_vector:
                    index_data["vectors"].append(vector.embedding_vector)
                    index_data["metadata"].append(
                        {
                            "vector_id": vector.id,
                            "document_id": vector.document_id,
                            "chunk_index": vector.chunk_index,
                            "chunk_text": vector.chunk_text,
                            "topic_category": vector.topic_category,
                            "importance_score": vector.importance_score,
                        }
                    )

            # 缓存索引数据
            await self.cache_manager.set(
                f"vector_index:{index_name}",
                json.dumps(index_data, default=str),
                expire_time=3600,  # 1小时缓存
            )

            return {
                "index_size": len(index_data["vectors"])
                * len(index_data["vectors"][0])
                * 4,  # 估算大小
            }

        except Exception as e:
            logger.error(f"Failed to build memory index: {str(e)}")
            raise


class MemoryVectorStore:
    """内存向量存储"""

    def __init__(self):
        self.vectors = {}
        self.metadata = {}

    async def search(
        self,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        # 简单实现
        return []

    async def build_index(
        self, index_name: str, vectors: List[DocumentVector], rebuild: bool
    ) -> Dict[str, Any]:
        """构建索引"""
        # 简单实现
        return {"index_size": 0}


class ChromaVectorStore:
    """Chroma向量存储"""

    def __init__(self):
        self.client = chromadb.Client()

    async def search(
        self,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        # Chroma实现
        return []

    async def build_index(
        self, index_name: str, vectors: List[DocumentVector], rebuild: bool
    ) -> Dict[str, Any]:
        """构建索引"""
        # Chroma实现
        return {"index_size": 0}


class PineconeVectorStore:
    """Pinecone向量存储"""

    def __init__(self):
        if Pinecone:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        else:
            self.pc = None

    async def search(
        self,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        # Pinecone实现
        return []

    async def build_index(
        self, index_name: str, vectors: List[DocumentVector], rebuild: bool
    ) -> Dict[str, Any]:
        """构建索引"""
        # Pinecone实现
        return {"index_size": 0}


class WeaviateVectorStore:
    """Weaviate向量存储"""

    def __init__(self):
        self.client = weaviate.Client(url=settings.WEAVIATE_URL)

    async def search(
        self,
        query_embedding: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        # Weaviate实现
        return []

    async def build_index(
        self, index_name: str, vectors: List[DocumentVector], rebuild: bool
    ) -> Dict[str, Any]:
        """构建索引"""
        # Weaviate实现
        return {"index_size": 0}
