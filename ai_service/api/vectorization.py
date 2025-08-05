"""
AI服务向量化API路由
提供文档向量化、嵌入生成等功能的REST API接口
"""

import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ai_service.database import get_vector_database
from ai_service.utils.logging import StructuredLogger
from ai_service.utils.text_processing import ChunkStrategy
from ai_service.vectorization import EmbeddingProvider, get_vectorization_service

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("api.vectorization")

# 创建路由器
router = APIRouter(prefix="/vectorization", tags=["vectorization"])


# 请求模型
class EmbeddingRequest(BaseModel):
    """嵌入请求"""

    text: str = Field(
        ..., description="要生成嵌入的文本", min_length=1, max_length=10000
    )
    provider: Optional[EmbeddingProvider] = Field(
        default=EmbeddingProvider.OLLAMA, description="嵌入提供商"
    )
    model: Optional[str] = Field(default=None, description="指定模型名称")
    normalize: bool = Field(default=True, description="是否标准化向量")
    cache: bool = Field(default=True, description="是否使用缓存")


class BatchEmbeddingRequest(BaseModel):
    """批量嵌入请求"""

    texts: List[str] = Field(
        ..., description="要生成嵌入的文本列表", min_items=1, max_items=100
    )
    provider: Optional[EmbeddingProvider] = Field(
        default=EmbeddingProvider.OLLAMA, description="嵌入提供商"
    )
    model: Optional[str] = Field(default=None, description="指定模型名称")
    normalize: bool = Field(default=True, description="是否标准化向量")
    cache: bool = Field(default=True, description="是否使用缓存")

    @validator("texts")
    def validate_texts(cls, v):
        for text in v:
            if not text or len(text.strip()) == 0:
                raise ValueError("文本不能为空")
            if len(text) > 10000:
                raise ValueError("单个文本长度不能超过10000字符")
        return v


class DocumentVectorizationRequest(BaseModel):
    """文档向量化请求"""

    document_id: str = Field(..., description="文档ID", min_length=1)
    content: str = Field(..., description="文档内容", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文档元数据")
    chunk_strategy: ChunkStrategy = Field(
        default=ChunkStrategy.SENTENCE, description="分块策略"
    )
    chunk_size: int = Field(default=500, description="分块大小", ge=100, le=2000)
    chunk_overlap: int = Field(default=50, description="分块重叠", ge=0, le=500)
    provider: Optional[EmbeddingProvider] = Field(
        default=EmbeddingProvider.OLLAMA, description="嵌入提供商"
    )
    model: Optional[str] = Field(default=None, description="指定模型名称")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的向量")
    cache: bool = Field(default=True, description="是否使用缓存")


class BatchDocumentVectorizationRequest(BaseModel):
    """批量文档向量化请求"""

    documents: List[DocumentVectorizationRequest] = Field(
        ..., description="文档列表", min_items=1, max_items=50
    )
    provider: Optional[EmbeddingProvider] = Field(
        default=EmbeddingProvider.OLLAMA, description="嵌入提供商"
    )
    model: Optional[str] = Field(default=None, description="指定模型名称")
    overwrite: bool = Field(default=False, description="是否覆盖已存在的向量")
    cache: bool = Field(default=True, description="是否使用缓存")


class SimilarityRequest(BaseModel):
    """相似度计算请求"""

    vector1: List[float] = Field(..., description="向量1")
    vector2: List[float] = Field(..., description="向量2")

    @validator("vector1", "vector2")
    def validate_vectors(cls, v):
        if len(v) == 0:
            raise ValueError("向量不能为空")
        if len(v) > 4096:
            raise ValueError("向量维度不能超过4096")
        return v


# 响应模型
class EmbeddingResponse(BaseModel):
    """嵌入响应"""

    embedding: List[float] = Field(..., description="嵌入向量")
    dimension: int = Field(..., description="向量维度")
    provider: str = Field(..., description="提供商")
    model: str = Field(..., description="模型名称")
    processing_time: float = Field(..., description="处理时间（秒）")
    cached: bool = Field(..., description="是否来自缓存")


class BatchEmbeddingResponse(BaseModel):
    """批量嵌入响应"""

    embeddings: List[List[float]] = Field(..., description="嵌入向量列表")
    dimension: int = Field(..., description="向量维度")
    provider: str = Field(..., description="提供商")
    model: str = Field(..., description="模型名称")
    total_texts: int = Field(..., description="文本总数")
    processing_time: float = Field(..., description="处理时间（秒）")
    cache_hits: int = Field(..., description="缓存命中数")
    cache_misses: int = Field(..., description="缓存未命中数")


class DocumentVectorizationResponse(BaseModel):
    """文档向量化响应"""

    document_id: str = Field(..., description="文档ID")
    total_chunks: int = Field(..., description="总分块数")
    vectorized_chunks: int = Field(..., description="已向量化分块数")
    skipped_chunks: int = Field(..., description="跳过的分块数")
    provider: str = Field(..., description="提供商")
    model: str = Field(..., description="模型名称")
    processing_time: float = Field(..., description="处理时间（秒）")
    chunk_details: List[Dict[str, Any]] = Field(..., description="分块详情")


class BatchDocumentVectorizationResponse(BaseModel):
    """批量文档向量化响应"""

    total_documents: int = Field(..., description="文档总数")
    successful_documents: int = Field(..., description="成功处理的文档数")
    failed_documents: int = Field(..., description="失败的文档数")
    total_chunks: int = Field(..., description="总分块数")
    processing_time: float = Field(..., description="处理时间（秒）")
    results: List[DocumentVectorizationResponse] = Field(..., description="处理结果")
    errors: List[Dict[str, str]] = Field(..., description="错误信息")


class SimilarityResponse(BaseModel):
    """相似度响应"""

    similarity: float = Field(..., description="相似度分数")
    distance: float = Field(..., description="距离")
    processing_time: float = Field(..., description="处理时间（秒）")


class VectorizationStatsResponse(BaseModel):
    """向量化统计响应"""

    total_embeddings: int = Field(..., description="总嵌入数")
    cache_hits: int = Field(..., description="缓存命中数")
    cache_misses: int = Field(..., description="缓存未命中数")
    total_processing_time: float = Field(..., description="总处理时间")
    average_processing_time: float = Field(..., description="平均处理时间")
    provider_stats: Dict[str, Dict[str, Any]] = Field(..., description="提供商统计")
    model_stats: Dict[str, Dict[str, Any]] = Field(..., description="模型统计")


# API端点
@router.post(
    "/embed",
    response_model=EmbeddingResponse,
    summary="生成文本嵌入",
    description="为单个文本生成嵌入向量",
)
async def create_embedding(
    request: EmbeddingRequest, vectorization_service=Depends(get_vectorization_service)
):
    """生成文本嵌入"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            method="POST",
            path="/vectorization/embed",
            status_code=200,
            duration_ms=0,
            text_length=len(request.text),
            provider=request.provider.value if request.provider else None,
            model=request.model,
            cache=request.cache,
        )

        # 生成嵌入
        result = await vectorization_service.get_embedding(
            text=request.text,
            provider=request.provider,
            model=request.model,
            normalize=request.normalize,
            use_cache=request.cache,
        )

        processing_time = time.time() - start_time

        # 记录向量化日志
        structured_logger.log_vectorization(
            document_id="single_text",
            chunks=1,
            model=result.model,
            duration_ms=int(processing_time * 1000),
        )

        return EmbeddingResponse(
            embedding=result.embedding,
            dimension=result.dimension,
            provider=result.provider,
            model=result.model,
            processing_time=processing_time,
            cached=result.cached,
        )

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            operation="embedding_error",
            error=e,
            text_length=len(request.text),
            provider=request.provider.value if request.provider else None,
            processing_time=processing_time,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"嵌入生成失败: {str(e)}",
        )


@router.post(
    "/embed/batch",
    response_model=BatchEmbeddingResponse,
    summary="批量生成文本嵌入",
    description="为多个文本批量生成嵌入向量",
)
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    vectorization_service=Depends(get_vectorization_service),
):
    """批量生成文本嵌入"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            method="POST",
            path="/vectorization/embed/batch",
            status_code=200,
            duration_ms=0,
            text_count=len(request.texts),
            total_length=sum(len(text) for text in request.texts),
            provider=request.provider.value if request.provider else None,
            model=request.model,
            cache=request.cache,
        )

        # 批量生成嵌入
        result = await vectorization_service.get_batch_embeddings(
            texts=request.texts,
            provider=request.provider,
            model=request.model,
            normalize=request.normalize,
            use_cache=request.cache,
        )

        processing_time = time.time() - start_time

        # 记录向量化日志
        structured_logger.log_vectorization(
            document_id="batch_texts",
            chunks=len(request.texts),
            model=result.model,
            duration_ms=int(processing_time * 1000),
        )

        return BatchEmbeddingResponse(
            embeddings=result.embeddings,
            dimension=result.dimension,
            provider=result.provider,
            model=result.model,
            total_texts=len(request.texts),
            processing_time=processing_time,
            cache_hits=result.cache_hits,
            cache_misses=result.cache_misses,
        )

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            operation="batch_embedding_error",
            error=e,
            text_count=len(request.texts),
            provider=request.provider.value if request.provider else None,
            processing_time=processing_time,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量嵌入生成失败: {str(e)}",
        )


@router.post(
    "/vectorize/document",
    response_model=DocumentVectorizationResponse,
    summary="文档向量化",
    description="对文档进行分块和向量化处理",
)
async def vectorize_document(
    request: DocumentVectorizationRequest,
    background_tasks: BackgroundTasks,
    vectorization_service=Depends(get_vectorization_service),
    vector_db=Depends(get_vector_database),
):
    """文档向量化"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            method="POST",
            path="/vectorization/vectorize/document",
            status_code=200,
            duration_ms=0,
            document_id=request.document_id,
            content_length=len(request.content),
            chunk_strategy=request.chunk_strategy.value,
            chunk_size=request.chunk_size,
            provider=request.provider.value if request.provider else None,
            overwrite=request.overwrite,
        )

        # 检查文档是否已存在
        if not request.overwrite:
            existing_vectors = await vector_db.get_document_vectors(request.document_id)
            if existing_vectors:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"文档 {request.document_id} 已存在向量，使用 overwrite=true 覆盖",
                )

        # 执行文档向量化
        result = await vectorization_service.vectorize_document(
            document_id=request.document_id,
            content=request.content,
            metadata=request.metadata or {},
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            provider=request.provider,
            model=request.model,
            use_cache=request.cache,
        )

        processing_time = time.time() - start_time

        # 构建响应
        chunk_details = []
        for chunk_result in result.chunk_results:
            chunk_details.append(
                {
                    "chunk_id": chunk_result.chunk_id,
                    "content_length": len(chunk_result.content),
                    "vector_dimension": len(chunk_result.embedding),
                    "processing_time": chunk_result.processing_time,
                    "cached": chunk_result.cached,
                }
            )

        # 记录向量化日志
        structured_logger.log_vectorization(
            document_id=request.document_id,
            chunks=result.total_chunks,
            model=result.model,
            duration_ms=int(processing_time * 1000),
        )

        # 后台任务：更新向量统计
        background_tasks.add_task(
            vector_db.update_vector_stats,
            request.document_id,
            result.total_chunks,
            result.dimension,
        )

        return DocumentVectorizationResponse(
            document_id=request.document_id,
            total_chunks=result.total_chunks,
            vectorized_chunks=result.successful_chunks,
            skipped_chunks=result.total_chunks - result.successful_chunks,
            provider=result.provider,
            model=result.model,
            processing_time=processing_time,
            chunk_details=chunk_details,
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="document_vectorization_error",
            error_message=str(e),
            context={
                "document_id": request.document_id,
                "content_length": len(request.content),
                "processing_time": processing_time,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档向量化失败: {str(e)}",
        )


@router.post(
    "/vectorize/documents/batch",
    response_model=BatchDocumentVectorizationResponse,
    summary="批量文档向量化",
    description="批量对多个文档进行向量化处理",
)
async def vectorize_documents_batch(
    request: BatchDocumentVectorizationRequest,
    background_tasks: BackgroundTasks,
    vectorization_service=Depends(get_vectorization_service),
    vector_db=Depends(get_vector_database),
):
    """批量文档向量化"""
    start_time = time.time()

    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/vectorization/vectorize/documents/batch",
            method="POST",
            request_data={
                "document_count": len(request.documents),
                "total_content_length": sum(
                    len(doc.content) for doc in request.documents
                ),
                "provider": request.provider.value if request.provider else None,
                "overwrite": request.overwrite,
            },
        )

        results = []
        errors = []
        total_chunks = 0
        successful_documents = 0

        # 处理每个文档
        for doc_request in request.documents:
            try:
                # 检查文档是否已存在
                if not request.overwrite:
                    existing_vectors = await vector_db.get_document_vectors(
                        doc_request.document_id
                    )
                    if existing_vectors:
                        errors.append(
                            {
                                "document_id": doc_request.document_id,
                                "error": "文档已存在，使用 overwrite=true 覆盖",
                            }
                        )
                        continue

                # 执行文档向量化
                result = await vectorization_service.vectorize_document(
                    document_id=doc_request.document_id,
                    content=doc_request.content,
                    metadata=doc_request.metadata or {},
                    chunk_strategy=doc_request.chunk_strategy,
                    chunk_size=doc_request.chunk_size,
                    chunk_overlap=doc_request.chunk_overlap,
                    provider=request.provider or doc_request.provider,
                    model=request.model or doc_request.model,
                    use_cache=request.cache,
                )

                # 构建响应
                chunk_details = []
                for chunk_result in result.chunk_results:
                    chunk_details.append(
                        {
                            "chunk_id": chunk_result.chunk_id,
                            "content_length": len(chunk_result.content),
                            "vector_dimension": len(chunk_result.embedding),
                            "processing_time": chunk_result.processing_time,
                            "cached": chunk_result.cached,
                        }
                    )

                doc_response = DocumentVectorizationResponse(
                    document_id=doc_request.document_id,
                    total_chunks=result.total_chunks,
                    vectorized_chunks=result.successful_chunks,
                    skipped_chunks=result.total_chunks - result.successful_chunks,
                    provider=result.provider,
                    model=result.model,
                    processing_time=result.processing_time,
                    chunk_details=chunk_details,
                )

                results.append(doc_response)
                total_chunks += result.total_chunks
                successful_documents += 1

                # 后台任务：更新向量统计
                background_tasks.add_task(
                    vector_db.update_vector_stats,
                    doc_request.document_id,
                    result.total_chunks,
                    result.dimension,
                )

            except Exception as e:
                errors.append({"document_id": doc_request.document_id, "error": str(e)})

        processing_time = time.time() - start_time

        # 记录批量向量化日志
        structured_logger.log_vectorization(
            document_id="batch_documents",
            chunks=total_chunks,
            model=request.model or "mixed",
            duration_ms=int(processing_time * 1000),
        )

        return BatchDocumentVectorizationResponse(
            total_documents=len(request.documents),
            successful_documents=successful_documents,
            failed_documents=len(errors),
            total_chunks=total_chunks,
            processing_time=processing_time,
            results=results,
            errors=errors,
        )

    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="batch_document_vectorization_error",
            error_message=str(e),
            context={
                "document_count": len(request.documents),
                "processing_time": processing_time,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量文档向量化失败: {str(e)}",
        )


@router.post(
    "/similarity",
    response_model=SimilarityResponse,
    summary="计算向量相似度",
    description="计算两个向量之间的相似度",
)
async def calculate_similarity(
    request: SimilarityRequest, vectorization_service=Depends(get_vectorization_service)
):
    """计算向量相似度"""
    start_time = time.time()

    try:
        # 验证向量维度
        if len(request.vector1) != len(request.vector2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="两个向量的维度必须相同"
            )

        # 计算相似度
        similarity = vectorization_service.calculate_similarity(
            request.vector1, request.vector2
        )

        # 计算距离（1 - 相似度）
        distance = 1.0 - similarity

        processing_time = time.time() - start_time

        return SimilarityResponse(
            similarity=similarity, distance=distance, processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time

        structured_logger.log_error(
            error_type="similarity_calculation_error",
            error_message=str(e),
            context={
                "vector1_dim": len(request.vector1),
                "vector2_dim": len(request.vector2),
                "processing_time": processing_time,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"相似度计算失败: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=VectorizationStatsResponse,
    summary="获取向量化统计",
    description="获取向量化服务的统计信息",
)
async def get_vectorization_stats(
    vectorization_service=Depends(get_vectorization_service),
):
    """获取向量化统计"""
    try:
        stats = await vectorization_service.get_service_stats()

        return VectorizationStatsResponse(
            total_embeddings=stats.get("total_embeddings", 0),
            cache_hits=stats.get("cache_hits", 0),
            cache_misses=stats.get("cache_misses", 0),
            total_processing_time=stats.get("total_processing_time", 0.0),
            average_processing_time=stats.get("average_processing_time", 0.0),
            provider_stats=stats.get("provider_stats", {}),
            model_stats=stats.get("model_stats", {}),
        )

    except Exception as e:
        structured_logger.log_error(
            error_type="stats_retrieval_error",
            error_message=str(e),
            context={"endpoint": "/vectorization/stats"},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统计信息获取失败: {str(e)}",
        )


@router.delete(
    "/document/{document_id}",
    summary="删除文档向量",
    description="删除指定文档的所有向量",
)
async def delete_document_vectors(
    document_id: str,
    background_tasks: BackgroundTasks,
    vector_db=Depends(get_vector_database),
):
    """删除文档向量"""
    try:
        # 记录请求
        structured_logger.log_request(
            endpoint=f"/vectorization/document/{document_id}",
            method="DELETE",
            request_data={"document_id": document_id},
        )

        # 删除文档向量
        deleted_count = await vector_db.delete_document_vectors(document_id)

        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 {document_id} 的向量不存在",
            )

        # 后台任务：更新统计
        background_tasks.add_task(
            vector_db.update_vector_stats,
            document_id,
            -deleted_count,  # 负数表示删除
            0,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"成功删除文档 {document_id} 的 {deleted_count} 个向量",
                "document_id": document_id,
                "deleted_count": deleted_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(
            error_type="vector_deletion_error",
            error_message=str(e),
            context={"document_id": document_id},
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档向量失败: {str(e)}",
        )


@router.get(
    "/health", summary="向量化服务健康检查", description="检查向量化服务的健康状态"
)
async def health_check(vectorization_service=Depends(get_vectorization_service)):
    """向量化服务健康检查"""
    try:
        health_status = await vectorization_service.health_check()

        if health_status["status"] == "healthy":
            return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status
            )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e), "timestamp": time.time()},
        )
