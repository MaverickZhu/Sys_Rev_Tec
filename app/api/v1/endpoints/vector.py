# -*- coding: utf-8 -*-
"""
AI向量化和智能分析API路由
提供文档向量化、语义搜索、智能分析等功能的REST API接口
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.ai_deps import (
    get_ai_integration_service,
    get_vector_service,
    get_knowledge_graph_service,
    check_ai_enabled
)
from app.crud.crud_document import document as crud_document
from app.crud.crud_vector import (
    document_vector as crud_document_vector,
    search_query as crud_search_query
)
from app.models.user import User
from app.schemas.vector import (
    # 向量化相关
    VectorizeRequest,
    VectorizeResponse,
    BatchVectorizeRequest,
    BatchVectorizeResponse,
    VectorizationStatusResponse,
    
    # 搜索相关
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchHistoryResponse,
    
    # 分析相关
    DocumentAnalysisRequest,
    EnhancedDocumentAnalysisResponse,
    AnalysisStatusResponse,
    
    # 知识图谱相关
    KnowledgeGraphNode,
    KnowledgeGraphRelation,
    
    # 统计相关
    AIStatisticsResponse,
    
    # 通用响应
    TaskResponse,
    HealthCheckResponse
)
from app.schemas.response import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 向量化相关API ====================

@router.post("/vectorize", response_model=ResponseModel[VectorizeResponse])
async def vectorize_document(
    request: VectorizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_enabled: bool = Depends(check_ai_enabled),
    vector_service = Depends(get_vector_service)
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查用户权限
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        # 启动向量化任务
        task_id = await vector_service.vectorize_document(
            document_id=request.document_id,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            vector_model=request.vector_model
        )
        
        response = VectorizeResponse(
            document_id=request.document_id,
            status="processing",
            chunk_count=0,
            vector_dimension=0,
            processing_time=0.0,
            message=f"向量化任务已启动，任务ID: {task_id}"
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message="向量化任务已启动"
        )
        
    except Exception as e:
        logger.error(f"向量化文档失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"向量化失败: {str(e)}"
        )


@router.post("/batch-vectorize", response_model=ResponseModel[BatchVectorizeResponse])
async def batch_vectorize_documents(
    request: BatchVectorizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_enabled: bool = Depends(check_ai_enabled),
    vector_service = Depends(get_vector_service)
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
            if document and crud_document.can_access(db=db, document=document, user=current_user):
                accessible_docs.append(doc_id)
        
        if not accessible_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有可访问的文档"
            )
        
        # 启动批量向量化任务
        task_id = await vector_service.batch_vectorize_documents(
            document_ids=accessible_docs,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            vector_model=request.vector_model
        )
        
        response = BatchVectorizeResponse(
            total_documents=len(accessible_docs),
            processed=0,
            failed=0,
            skipped=0,
            processing_time=0.0,
            results=[]
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message=f"批量向量化任务已启动，任务ID: {task_id}"
        )
        
    except Exception as e:
        logger.error(f"批量向量化失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量向量化失败: {str(e)}"
        )


@router.get("/vectorization-status/{document_id}", response_model=ResponseModel[VectorizationStatusResponse])
async def get_vectorization_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    vector_service = Depends(get_vector_service)
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        # 获取向量化状态
        status_info = await vector_service.get_vectorization_status(document_id)
        
        return ResponseModel(
            success=True,
            data=status_info,
            message="获取向量化状态成功"
        )
        
    except Exception as e:
        logger.error(f"获取向量化状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


# ==================== 语义搜索相关API ====================

@router.post("/semantic-search", response_model=ResponseModel[SemanticSearchResponse])
async def semantic_search(
    request: SemanticSearchRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_enabled: bool = Depends(check_ai_enabled),
    vector_service = Depends(get_vector_service)
):
    """
    语义搜索
    
    - **query**: 搜索查询
    - **project_id**: 项目ID过滤（可选）
    - **document_types**: 文档类型过滤（可选）
    - **similarity_threshold**: 相似度阈值
    - **max_results**: 最大结果数量
    - **include_metadata**: 是否包含元数据
    - **search_type**: 搜索类型
    """
    try:
        # 执行语义搜索
        search_results = await vector_service.semantic_search(
            query=request.query,
            user_id=current_user.id,
            project_id=request.project_id,
            document_types=request.document_types,
            similarity_threshold=request.similarity_threshold,
            max_results=request.max_results,
            include_metadata=request.include_metadata,
            search_type=request.search_type
        )
        
        # 保存搜索历史
        search_query = crud_search_query.create(
            db=db,
            obj_in={
                "query_text": request.query,
                "query_type": request.search_type,
                "user_id": current_user.id,
                "similarity_threshold": request.similarity_threshold,
                "max_results": request.max_results,
                "result_count": len(search_results.results),
                "response_time": search_results.search_time
            }
        )
        
        return ResponseModel(
            success=True,
            data=search_results,
            message="语义搜索完成"
        )
        
    except Exception as e:
        logger.error(f"语义搜索失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/search-history", response_model=ResponseModel[SearchHistoryResponse])
async def get_search_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取搜索历史
    
    - **page**: 页码
    - **page_size**: 每页大小
    """
    try:
        # 获取搜索历史
        search_queries = crud_search_query.get_multi_by_user(
            db=db,
            user_id=current_user.id,
            skip=(page - 1) * page_size,
            limit=page_size
        )
        
        total_count = crud_search_query.count_by_user(db=db, user_id=current_user.id)
        total_pages = (total_count + page_size - 1) // page_size
        
        history_items = [
            {
                "id": str(query.id),
                "query": query.query_text,
                "results_count": query.result_count or 0,
                "search_time": query.response_time or 0.0,
                "user_id": query.user_id,
                "created_at": query.created_at
            }
            for query in search_queries
        ]
        
        response = SearchHistoryResponse(
            total_count=total_count,
            items=history_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
        return ResponseModel(
            success=True,
            data=response,
            message="获取搜索历史成功"
        )
        
    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取搜索历史失败: {str(e)}"
        )


# ==================== 文档智能分析相关API ====================

@router.post("/analyze", response_model=ResponseModel[EnhancedDocumentAnalysisResponse])
async def analyze_document(
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_enabled: bool = Depends(check_ai_enabled),
    ai_service = Depends(get_ai_integration_service)
):
    """
    文档智能分析
    
    - **document_id**: 文档ID
    - **analysis_types**: 分析类型列表 (summary/keywords/classification/risk/compliance/entities/sentiment)
    - **force_reprocess**: 是否强制重新分析
    """
    try:
        # 检查文档权限
        document = crud_document.get(db=db, id=request.document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        # 启动分析任务
        analysis_result = await ai_service.analyze_document(
            document_id=request.document_id,
            analysis_types=request.analysis_types,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess
        )
        
        return ResponseModel(
            success=True,
            data=analysis_result,
            message="文档分析完成"
        )
        
    except Exception as e:
        logger.error(f"文档分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析失败: {str(e)}"
        )


@router.get("/analysis-status/{document_id}", response_model=ResponseModel[AnalysisStatusResponse])
async def get_analysis_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_service = Depends(get_ai_integration_service)
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        # 获取分析状态
        status_info = await ai_service.get_analysis_status(document_id)
        
        return ResponseModel(
            success=True,
            data=status_info,
            message="获取分析状态成功"
        )
        
    except Exception as e:
        logger.error(f"获取分析状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


# ==================== 知识图谱相关API ====================

@router.get("/knowledge-graph/{document_id}", response_model=ResponseModel[Dict[str, Any]])
async def get_document_knowledge_graph(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    kg_service = Depends(get_knowledge_graph_service)
):
    """
    获取文档知识图谱
    
    - **document_id**: 文档ID
    """
    try:
        # 检查文档权限
        document = crud_document.get(db=db, id=document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        if not crud_document.can_access(db=db, document=document, user=current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文档"
            )
        
        # 获取知识图谱
        kg_data = await kg_service.get_document_knowledge_graph(document_id)
        
        return ResponseModel(
            success=True,
            data=kg_data,
            message="获取知识图谱成功"
        )
        
    except Exception as e:
        logger.error(f"获取知识图谱失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识图谱失败: {str(e)}"
        )


# ==================== 统计信息相关API ====================

@router.get("/statistics", response_model=ResponseModel[AIStatisticsResponse])
async def get_ai_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    ai_service = Depends(get_ai_integration_service)
):
    """
    获取AI功能统计信息
    """
    try:
        # 获取统计信息
        stats = await ai_service.get_statistics(user_id=current_user.id)
        
        return ResponseModel(
            success=True,
            data=stats,
            message="获取统计信息成功"
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


# ==================== 健康检查相关API ====================

@router.get("/health", response_model=ResponseModel[HealthCheckResponse])
async def ai_health_check(
    ai_service = Depends(get_ai_integration_service)
):
    """
    AI服务健康检查
    """
    try:
        # 执行健康检查
        health_status = await ai_service.health_check()
        
        return ResponseModel(
            success=True,
            data=health_status,
            message="AI服务健康检查完成"
        )
        
    except Exception as e:
        logger.error(f"AI健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI服务不可用: {str(e)}"
        )