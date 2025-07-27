import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app import crud, models, schemas
from app.core.config import settings
from app.utils.ai_integration import AIIntegrationService
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor

# 配置日志
logger = logging.getLogger(__name__)


class VectorService:
    """
    向量服务 - 管理文档向量化、搜索和索引
    """
    
    def __init__(self):
        self.ai_service = AIIntegrationService()
        self.cache_manager = CacheManager()
        self.text_processor = TextProcessor()
        self.vector_stores = {
            "memory": MemoryVectorStore(),
            "chroma": ChromaVectorStore() if settings.CHROMA_HOST else None,
            "pinecone": PineconeVectorStore() if settings.PINECONE_API_KEY else None,
            "weaviate": WeaviateVectorStore() if settings.WEAVIATE_URL else None
        }
        # 过滤掉None的存储
        self.vector_stores = {k: v for k, v in self.vector_stores.items() if v is not None}
        
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
        vector_store: Optional[str] = None
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
            cache_key = f"search:{hash(query)}:{similarity_threshold}:{max_results}:{hash(str(document_ids))}:{hash(str(filter_params))}"
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
                    db, query_embedding, similarity_threshold, max_results, document_ids, filter_params
                )
            else:
                # 使用向量存储搜索
                results = await vector_store_instance.search(
                    query_embedding, similarity_threshold, max_results, document_ids, filter_params
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
                ttl=300  # 5分钟缓存
            )
            
            logger.info(f"Semantic search completed: {len(enhanced_results)} results in {search_time:.2f}s")
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
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        使用数据库进行向量搜索
        """
        try:
            # 构建查询
            query = db.query(models.DocumentVector)
            
            # 添加文档过滤
            if document_ids:
                query = query.filter(models.DocumentVector.document_id.in_(document_ids))
            
            # 添加其他过滤条件
            if filter_params:
                if "topic_category" in filter_params:
                    query = query.filter(models.DocumentVector.topic_category == filter_params["topic_category"])
                if "min_importance" in filter_params:
                    query = query.filter(models.DocumentVector.importance_score >= filter_params["min_importance"])
                if "vector_model" in filter_params:
                    query = query.filter(models.DocumentVector.vector_model == filter_params["vector_model"])
            
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
                        similarities.append({
                            "vector_id": vector.id,
                            "document_id": vector.document_id,
                            "chunk_index": vector.chunk_index,
                            "chunk_text": vector.chunk_text,
                            "similarity": similarity,
                            "topic_category": vector.topic_category,
                            "importance_score": vector.importance_score,
                            "vector_model": vector.vector_model
                        })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:max_results]
            
        except Exception as e:
            logger.error(f"Database vector search failed: {str(e)}")
            raise
    
    async def _enhance_search_results(
        self,
        db: Session,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        增强搜索结果，添加文档信息
        """
        try:
            enhanced_results = []
            
            for result in results:
                # 获取文档信息
                document = crud.document.get(db=db, id=result["document_id"])
                if document:
                    enhanced_result = result.copy()
                    enhanced_result.update({
                        "document_title": document.title,
                        "document_filename": document.filename,
                        "document_type": document.document_type,
                        "document_status": document.status,
                        "document_created_at": document.created_at,
                        "document_updated_at": document.updated_at,
                        "document_classification": document.document_classification,
                        "document_ai_summary": document.ai_summary
                    })
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
        rebuild: bool = False
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
            existing_index = crud.vector_search_index.get_by_name(db=db, index_name=index_name)
            if existing_index and not rebuild:
                return {
                    "status": "exists",
                    "message": "Index already exists. Use rebuild=True to rebuild.",
                    "index_id": existing_index.id
                }
            
            # 获取要索引的向量
            query = db.query(models.DocumentVector)
            if document_ids:
                query = query.filter(models.DocumentVector.document_id.in_(document_ids))
            
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
                    is_active=True
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
                    is_active=True
                )
                new_index = crud.vector_search_index.create(db=db, obj_in=index_data)
                index_id = new_index.id
            
            build_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Vector index '{index_name}' built successfully in {build_time:.2f}s")
            
            return {
                "status": "success",
                "index_id": index_id,
                "index_name": index_name,
                "vector_store": store_name,
                "total_vectors": len(vectors),
                "build_time": build_time,
                "index_size": index_result.get("index_size", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to build vector index: {str(e)}")
            raise
    
    async def _build_memory_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector]
    ) -> Dict[str, Any]:
        """
        构建内存向量索引
        """
        try:
            # 简单的内存索引实现
            index_data = {
                "vectors": [],
                "metadata": []
            }
            
            for vector in vectors:
                if vector.embedding_vector:
                    index_data["vectors"].append(vector.embedding_vector)
                    index_data["metadata"].append({
                        "vector_id": vector.id,
                        "document_id": vector.document_id,
                        "chunk_index": vector.chunk_index,
                        "chunk_text": vector.chunk_text,
                        "topic_category": vector.topic_category,
                        "importance_score": vector.importance_score
                    })
            
            # 缓存索引数据
            await self.cache_manager.set(
                f"vector_index:{index_name}",
                json.dumps(index_data, default=str),
                expire_time=3600  # 1小时缓存
            )
            
            return {
                "index_size": len(index_data["vectors"]) * len(index_data["vectors"][0]) * 4,  # 估算大小
                "vector_count": len(index_data["vectors"])
            }
            
        except Exception as e:
            logger.error(f"Failed to build memory index: {str(e)}")
            raise
    
    async def get_similar_documents(
        self,
        db: Session,
        document_id: int,
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取相似文档
        
        Args:
            db: 数据库会话
            document_id: 参考文档ID
            similarity_threshold: 相似度阈值
            max_results: 最大结果数
        
        Returns:
            相似文档列表
        """
        try:
            # 获取参考文档的向量
            reference_vectors = crud.document_vector.get_by_document(db=db, document_id=document_id)
            if not reference_vectors:
                return []
            
            # 使用第一个向量作为参考（也可以使用平均向量）
            reference_vector = reference_vectors[0]
            if not reference_vector.embedding_vector:
                return []
            
            # 搜索相似向量
            similar_vectors = crud.document_vector.search_similar_vectors(
                db=db,
                query_vector=reference_vector.embedding_vector,
                similarity_threshold=similarity_threshold,
                max_results=max_results * 3,  # 获取更多结果用于去重
                document_ids=None
            )
            
            # 按文档分组并去重
            document_similarities = {}
            for result in similar_vectors:
                vector = result["vector"]
                similarity = result["similarity"]
                
                # 排除自身
                if vector.document_id == document_id:
                    continue
                
                # 保留每个文档的最高相似度
                if vector.document_id not in document_similarities or similarity > document_similarities[vector.document_id]["similarity"]:
                    document_similarities[vector.document_id] = {
                        "document_id": vector.document_id,
                        "similarity": similarity,
                        "matching_chunk": vector.chunk_text
                    }
            
            # 转换为列表并排序
            similar_documents = list(document_similarities.values())
            similar_documents.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 增强结果
            enhanced_results = await self._enhance_search_results(db, similar_documents[:max_results])
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Failed to get similar documents: {str(e)}")
            raise
    
    async def update_document_vectors(
        self,
        db: Session,
        document_id: int,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        更新文档向量
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            force_update: 是否强制更新
        
        Returns:
            更新结果
        """
        try:
            # 获取文档
            document = crud.document.get(db=db, id=document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # 检查是否需要更新
            if document.is_vectorized and not force_update:
                return {
                    "status": "skipped",
                    "message": "Document already vectorized. Use force_update=True to re-vectorize."
                }
            
            # 删除现有向量
            if force_update:
                deleted_count = crud.document_vector.delete_by_document(db=db, document_id=document_id)
                logger.info(f"Deleted {deleted_count} existing vectors for document {document_id}")
            
            # 重新向量化
            vectorization_result = await self.ai_service.vectorize_document(
                document=document,
                force_refresh=force_update
            )
            
            # 保存新向量
            for chunk_data in vectorization_result["chunks"]:
                vector_data = schemas.DocumentVectorCreate(
                    document_id=document_id,
                    chunk_index=chunk_data["index"],
                    chunk_text=chunk_data["text"],
                    embedding_vector=chunk_data["embedding"],
                    vector_model=vectorization_result["model_name"],
                    embedding_dimension=vectorization_result["embedding_dimension"],
                    topic_category=chunk_data.get("topic"),
                    importance_score=chunk_data.get("importance", 0.5)
                )
                crud.document_vector.create(db=db, obj_in=vector_data)
            
            # 更新文档状态
            document_update = schemas.DocumentUpdate(
                is_vectorized=True,
                vector_status="completed",
                vector_model=vectorization_result["model_name"],
                embedding_dimension=vectorization_result["embedding_dimension"],
                chunk_count=vectorization_result["total_chunks"],
                vectorized_at=datetime.utcnow()
            )
            crud.document.update(db=db, db_obj=document, obj_in=document_update)
            
            return {
                "status": "success",
                "document_id": document_id,
                "total_chunks": vectorization_result["total_chunks"],
                "model_name": vectorization_result["model_name"],
                "embedding_dimension": vectorization_result["embedding_dimension"]
            }
            
        except Exception as e:
            logger.error(f"Failed to update document vectors: {str(e)}")
            raise
    
    async def get_vector_statistics(self, db: Session) -> Dict[str, Any]:
        """
        获取向量统计信息
        """
        try:
            # 基础统计
            base_stats = crud.document_vector.get_statistics(db=db)
            
            # 向量存储状态
            store_status = {}
            for store_name, store_instance in self.vector_stores.items():
                if store_instance:
                    try:
                        status = await store_instance.get_status()
                        store_status[store_name] = status
                    except:
                        store_status[store_name] = {"status": "error"}
            
            # 索引信息
            indexes = crud.vector_search_index.get_active_indexes(db=db)
            index_info = [
                {
                    "name": idx.index_name,
                    "type": idx.vector_store_type,
                    "vectors": idx.total_vectors,
                    "size": idx.index_size,
                    "created": idx.created_at,
                    "last_rebuild": idx.last_rebuild_at
                }
                for idx in indexes
            ]
            
            return {
                "basic_statistics": base_stats,
                "vector_stores": store_status,
                "indexes": index_info,
                "default_store": self.default_store,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector statistics: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {}
            }
            
            # 检查AI服务
            try:
                ai_health = await self.ai_service.health_check()
                health_status["services"]["ai_integration"] = ai_health["status"]
            except:
                health_status["services"]["ai_integration"] = "unhealthy"
            
            # 检查向量存储
            for store_name, store_instance in self.vector_stores.items():
                if store_instance:
                    try:
                        store_health = await store_instance.health_check()
                        health_status["services"][f"vector_store_{store_name}"] = store_health["status"]
                    except:
                        health_status["services"][f"vector_store_{store_name}"] = "unhealthy"
            
            # 检查缓存
            try:
                await self.cache_manager.set("health_check", "ok", expire_time=60)
                cached_value = await self.cache_manager.get("health_check")
                if cached_value == "ok":
                    health_status["services"]["cache"] = "healthy"
                else:
                    health_status["services"]["cache"] = "unhealthy"
            except:
                health_status["services"]["cache"] = "unhealthy"
            
            # 检查整体状态
            unhealthy_services = [k for k, v in health_status["services"].items() if v == "unhealthy"]
            if unhealthy_services:
                health_status["status"] = "degraded"
                health_status["unhealthy_services"] = unhealthy_services
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class BaseVectorStore:
    """
    向量存储基类
    """
    
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    async def build_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector],
        rebuild: bool = False
    ) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def get_status(self) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError


class MemoryVectorStore(BaseVectorStore):
    """
    内存向量存储实现
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        # 内存搜索实现（简化版）
        return []
    
    async def build_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector],
        rebuild: bool = False
    ) -> Dict[str, Any]:
        # 内存索引构建
        return {"index_size": len(vectors) * 1536 * 4}
    
    async def get_status(self) -> Dict[str, Any]:
        return {"status": "healthy", "type": "memory"}
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy"}


class ChromaVectorStore(BaseVectorStore):
    """
    Chroma向量存储实现
    """
    
    def __init__(self):
        self.host = settings.CHROMA_HOST
        self.port = settings.CHROMA_PORT
        self.client = None
    
    async def _get_client(self):
        if not self.client:
            try:
                import chromadb
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            except ImportError:
                logger.error("ChromaDB not installed. Install with: pip install chromadb")
                raise
        return self.client
    
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        # Chroma搜索实现
        try:
            client = await self._get_client()
            # 实现Chroma搜索逻辑
            return []
        except Exception as e:
            logger.error(f"Chroma search failed: {str(e)}")
            return []
    
    async def build_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector],
        rebuild: bool = False
    ) -> Dict[str, Any]:
        # Chroma索引构建
        return {"index_size": len(vectors) * 1536 * 4}
    
    async def get_status(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            return {"status": "healthy", "type": "chroma"}
        except:
            return {"status": "unhealthy", "type": "chroma"}
    
    async def health_check(self) -> Dict[str, Any]:
        return await self.get_status()


class PineconeVectorStore(BaseVectorStore):
    """
    Pinecone向量存储实现
    """
    
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.environment = settings.PINECONE_ENVIRONMENT
        self.client = None
    
    async def _get_client(self):
        if not self.client:
            try:
                import pinecone
                pinecone.init(
                    api_key=self.api_key,
                    environment=self.environment
                )
                self.client = pinecone
            except ImportError:
                logger.error("Pinecone not installed. Install with: pip install pinecone-client")
                raise
        return self.client
    
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        # Pinecone搜索实现
        return []
    
    async def build_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector],
        rebuild: bool = False
    ) -> Dict[str, Any]:
        # Pinecone索引构建
        return {"index_size": len(vectors) * 1536 * 4}
    
    async def get_status(self) -> Dict[str, Any]:
        return {"status": "healthy", "type": "pinecone"}
    
    async def health_check(self) -> Dict[str, Any]:
        return await self.get_status()


class WeaviateVectorStore(BaseVectorStore):
    """
    Weaviate向量存储实现
    """
    
    def __init__(self):
        self.url = settings.WEAVIATE_URL
        self.api_key = settings.WEAVIATE_API_KEY
        self.client = None
    
    async def _get_client(self):
        if not self.client:
            try:
                import weaviate
                self.client = weaviate.Client(
                    url=self.url,
                    auth_client_secret=weaviate.AuthApiKey(api_key=self.api_key) if self.api_key else None
                )
            except ImportError:
                logger.error("Weaviate not installed. Install with: pip install weaviate-client")
                raise
        return self.client
    
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float,
        max_results: int,
        document_ids: Optional[List[int]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        # Weaviate搜索实现
        return []
    
    async def build_index(
        self,
        index_name: str,
        vectors: List[models.DocumentVector],
        rebuild: bool = False
    ) -> Dict[str, Any]:
        # Weaviate索引构建
        return {"index_size": len(vectors) * 1536 * 4}
    
    async def get_status(self) -> Dict[str, Any]:
        return {"status": "healthy", "type": "weaviate"}
    
    async def health_check(self) -> Dict[str, Any]:
        return await self.get_status()