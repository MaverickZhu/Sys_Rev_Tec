import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_document
from app.schemas.response import ResponseModel

"""
AI向量化和智能分析API路由

提供文档向量化、语义搜索、智能分析等功能的REST API接口
"""

from app.core.ai_deps import (
    get_ai_integration_service,
    get_knowledge_graph_service,
    get_vector_service,
    is_ai_enabled,
)
from app.schemas.ai import (
    AIStatisticsResponse,
    AnalysisStatusResponse,
    BatchVectorizeRequest,
    BatchVectorizeResponse,
    DocumentAnalysisRequest,
    EnhancedDocumentAnalysisResponse,
    HealthCheckResponse,
    SearchHistoryResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    VectorizationStatusResponse,
    VectorizeRequest,
    VectorizeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 向量化相关API ====================


@router.post("/vectorize", response_model=ResponseModel[VectorizeResponse])
async def vectorize_document(
    request: VectorizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
):
    """
    向量化单个文档

    - **document_id**: 文档ID
    - **force_reprocess**: 是否强制重新处理
    - **chunk_strategy**: 分块策略 (semantic/fixed/paragraph)
    - **chunk_size**: 分块大小
    - **chunk_overlap**: 分块重叠
    - **vector_model**: 向量化模型
    """
    try:
        # 检查文档是否存在
        document = crud_document.get(db=db, id=request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        # 检查用户权限
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        # 启动向量化任务
        task_id = await vector_service.vectorize_document(
            document_id=request.document_id,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            vector_model=request.vector_model,
        )

        response = VectorizeResponse(
            document_id=request.document_id,
            status="processing",
            chunk_count=0,
            vector_dimension=0,
            processing_time=0.0,
            message=f"向量化任务已启动，任务ID: {task_id}",
        )

        return ResponseModel(success=True, data=response, message="向量化任务已启动")

    except Exception as e:
        logger.error(f"向量化文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"向量化失败: {str(e)}",
        )


@router.post("/batch-vectorize", response_model=ResponseModel[BatchVectorizeResponse])
async def batch_vectorize_documents(
    request: BatchVectorizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
):
    """
    批量向量化文档

    - **document_ids**: 文档ID列表
    - **force_reprocess**: 是否强制重新处理
    - **chunk_strategy**: 分块策略
    - **chunk_size**: 分块大小
    - **chunk_overlap**: 分块重叠
    - **vector_model**: 向量化模型
    """
    try:
        # 检查文档权限
        accessible_docs = []
        for doc_id in request.document_ids:
            document = crud_document.get(db=db, id=doc_id)
            if document and crud_document.can_access(
                db=db, document=document, user=current_user
            ):
                accessible_docs.append(doc_id)

        if not accessible_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="没有可访问的文档"
            )

        # 启动批量向量化任务
        task_id = await vector_service.batch_vectorize_documents(
            document_ids=accessible_docs,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            vector_model=request.vector_model,
        )

        response = BatchVectorizeResponse(
            total_documents=len(accessible_docs),
            processed=0,
            failed=0,
            skipped=0,
            processing_time=0.0,
            results=[],
        )

        return ResponseModel(
            success=True,
            data=response,
            message=f"批量向量化任务已启动，任务ID: {task_id}",
        )

    except Exception as e:
        logger.error(f"批量向量化失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量向量化失败: {str(e)}",
        )


@router.get(
    "/vectorization-status/{document_id}",
    response_model=ResponseModel[VectorizationStatusResponse],
)
async def get_vectorization_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
):
    """
    获取文档向量化状态

    - **document_id**: 文档ID
    """
    try:
        # 检查文档权限
        document = crud_document.get(db=db, id=document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        # 获取向量化状态
        status_info = await vector_service.get_vectorization_status(
            document_id=document_id
        )

        response = VectorizationStatusResponse(
            document_id=document_id,
            status=status_info.get("status", "unknown"),
            chunk_count=status_info.get("chunk_count", 0),
            vector_dimension=status_info.get("vector_dimension", 0),
            processing_time=status_info.get("processing_time", 0.0),
            error_message=status_info.get("error_message"),
            created_at=status_info.get("created_at"),
            updated_at=status_info.get("updated_at"),
        )

        return ResponseModel(success=True, data=response, message="获取状态成功")

    except Exception as e:
        logger.error(f"获取向量化状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}",
        )


# ==================== 语义搜索相关API ====================


@router.post("/semantic-search", response_model=ResponseModel[SemanticSearchResponse])
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
):
    """
    语义搜索

    - **query**: 搜索查询
    - **project_ids**: 限制搜索的项目ID列表
    - **document_types**: 限制搜索的文档类型
    - **top_k**: 返回结果数量
    - **similarity_threshold**: 相似度阈值
    - **search_mode**: 搜索模式 (semantic/hybrid/keyword)
    - **include_metadata**: 是否包含元数据
    """
    try:
        # 执行语义搜索
        search_results = await vector_service.semantic_search(
            query=request.query,
            user_id=current_user.id,
            project_ids=request.project_ids,
            document_types=request.document_types,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            search_mode=request.search_mode,
            include_metadata=request.include_metadata,
        )

        response = SemanticSearchResponse(
            query=request.query,
            total_results=len(search_results),
            search_time=search_results.get("search_time", 0.0),
            results=search_results.get("results", []),
            suggestions=search_results.get("suggestions", []),
        )

        return ResponseModel(success=True, data=response, message="搜索完成")

    except Exception as e:
        logger.error(f"语义搜索失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}",
        )


@router.get("/search-history", response_model=ResponseModel[SearchHistoryResponse])
async def get_search_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
):
    """
    获取搜索历史

    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    try:
        # 获取搜索历史
        history = await vector_service.get_search_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

        response = SearchHistoryResponse(
            total_count=history.get("total_count", 0),
            searches=history.get("searches", []),
        )

        return ResponseModel(success=True, data=response, message="获取历史成功")

    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史失败: {str(e)}",
        )


# ==================== 文档分析相关API ====================


@router.post(
    "/analyze-document", response_model=ResponseModel[EnhancedDocumentAnalysisResponse]
)
async def analyze_document(
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    ai_service=Depends(get_ai_integration_service),
):
    """
    智能文档分析

    - **document_id**: 文档ID
    - **analysis_types**: 分析类型列表
    - **include_summary**: 是否包含摘要
    - **include_keywords**: 是否包含关键词
    - **include_entities**: 是否包含实体识别
    - **include_sentiment**: 是否包含情感分析
    - **include_compliance**: 是否包含合规检查
    """
    try:
        # 检查文档权限
        document = crud_document.get(db=db, id=request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        # 启动文档分析任务
        task_id = await ai_service.analyze_document(
            document_id=request.document_id,
            user_id=current_user.id,
            analysis_types=request.analysis_types,
            include_summary=request.include_summary,
            include_keywords=request.include_keywords,
            include_entities=request.include_entities,
            include_sentiment=request.include_sentiment,
            include_compliance=request.include_compliance,
        )

        response = EnhancedDocumentAnalysisResponse(
            document_id=request.document_id,
            status="processing",
            analysis_types=request.analysis_types,
            processing_time=0.0,
            task_id=task_id,
        )

        return ResponseModel(
            success=True,
            data=response,
            message=f"文档分析任务已启动，任务ID: {task_id}",
        )

    except Exception as e:
        logger.error(f"文档分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}",
        )


@router.get(
    "/analysis-status/{document_id}",
    response_model=ResponseModel[AnalysisStatusResponse],
)
async def get_analysis_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    ai_service=Depends(get_ai_integration_service),
):
    """
    获取文档分析状态

    - **document_id**: 文档ID
    """
    try:
        # 检查文档权限
        document = crud_document.get(db=db, id=document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此文档"
            )

        # 获取分析状态
        status_info = await ai_service.get_analysis_status(document_id=document_id)

        response = AnalysisStatusResponse(
            document_id=document_id,
            status=status_info.get("status", "unknown"),
            analysis_types=status_info.get("analysis_types", []),
            processing_time=status_info.get("processing_time", 0.0),
            results=status_info.get("results", {}),
            error_message=status_info.get("error_message"),
            created_at=status_info.get("created_at"),
            updated_at=status_info.get("updated_at"),
        )

        return ResponseModel(success=True, data=response, message="获取状态成功")

    except Exception as e:
        logger.error(f"获取分析状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}",
        )


# ==================== 统计和监控API ====================


@router.get("/ai-statistics", response_model=ResponseModel[AIStatisticsResponse])
async def get_ai_statistics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    ai_enabled: bool = Depends(is_ai_enabled),
    ai_service=Depends(get_ai_integration_service),
):
    """
    获取AI功能使用统计

    - **days**: 统计天数
    """
    try:
        # 获取统计数据
        stats = await ai_service.get_usage_statistics(
            user_id=current_user.id,
            days=days,
        )

        response = AIStatisticsResponse(
            total_vectorized_documents=stats.get("total_vectorized_documents", 0),
            total_searches=stats.get("total_searches", 0),
            total_analyses=stats.get("total_analyses", 0),
            average_search_time=stats.get("average_search_time", 0.0),
            average_analysis_time=stats.get("average_analysis_time", 0.0),
            popular_search_terms=stats.get("popular_search_terms", []),
            usage_by_day=stats.get("usage_by_day", []),
        )

        return ResponseModel(success=True, data=response, message="获取统计成功")

    except Exception as e:
        logger.error(f"获取AI统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}",
        )


@router.get("/health", response_model=ResponseModel[HealthCheckResponse])
async def ai_health_check(
    ai_enabled: bool = Depends(is_ai_enabled),
    vector_service=Depends(get_vector_service),
    ai_service=Depends(get_ai_integration_service),
    kg_service=Depends(get_knowledge_graph_service),
):
    """
    AI服务健康检查
    """
    try:
        # 检查各个服务状态
        vector_status = await vector_service.health_check()
        ai_status = await ai_service.health_check()
        kg_status = await kg_service.health_check()

        response = HealthCheckResponse(
            ai_enabled=ai_enabled,
            vector_service_status=vector_status.get("status", "unknown"),
            ai_service_status=ai_status.get("status", "unknown"),
            knowledge_graph_status=kg_status.get("status", "unknown"),
            vector_store_connected=vector_status.get("vector_store_connected", False),
            ai_model_loaded=ai_status.get("model_loaded", False),
            last_check_time=vector_status.get("timestamp"),
        )

        return ResponseModel(success=True, data=response, message="健康检查完成")

    except Exception as e:
        logger.error(f"AI健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}",
        )
