from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils.ai_integration import AIIntegrationService
from app.utils.vector_service import VectorService
from app.utils.knowledge_graph import KnowledgeGraphService

router = APIRouter()


@router.post("/vectorize-document/{document_id}", response_model=schemas.VectorizeResponse)
def vectorize_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int,
    vectorize_request: schemas.VectorizeRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    对文档进行向量化处理
    """
    # 检查文档是否存在
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 检查用户权限
    if not crud.user.is_superuser(current_user) and document.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # 检查文档是否已经向量化
    if document.is_vectorized and not vectorize_request.force_re_vectorize:
        raise HTTPException(
            status_code=400, 
            detail="Document already vectorized. Use force_re_vectorize=true to re-vectorize"
        )
    
    # 启动后台向量化任务
    background_tasks.add_task(
        _vectorize_document_task,
        db,
        document_id,
        vectorize_request.dict(),
        current_user.id
    )
    
    return schemas.VectorizeResponse(
        message="Document vectorization started",
        document_id=document_id,
        status="processing",
        estimated_completion_time=datetime.utcnow().isoformat()
    )


@router.get("/vectorization-status/{document_id}", response_model=schemas.VectorizeStatusResponse)
def get_vectorization_status(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取文档向量化状态
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 检查用户权限
    if not crud.user.is_superuser(current_user) and document.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # 获取向量化信息
    vectors = crud.document_vector.get_by_document(db=db, document_id=document_id)
    
    return schemas.VectorizeStatusResponse(
        document_id=document_id,
        is_vectorized=document.is_vectorized,
        vector_status=document.vector_status,
        vector_model=document.vector_model,
        embedding_dimension=document.embedding_dimension,
        chunk_count=document.chunk_count,
        vectorized_at=document.vectorized_at,
        total_vectors=len(vectors)
    )


@router.post("/semantic-search", response_model=schemas.SemanticSearchResponse)
def semantic_search(
    *,
    db: Session = Depends(deps.get_db),
    search_request: schemas.SemanticSearchRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    语义搜索
    """
    try:
        # 初始化向量服务
        vector_service = VectorService()
        
        # 执行语义搜索
        search_results = vector_service.semantic_search(
            db=db,
            query=search_request.query,
            similarity_threshold=search_request.similarity_threshold,
            max_results=search_request.max_results,
            document_ids=search_request.document_ids,
            filter_params=search_request.filters
        )
        
        # 记录搜索查询
        search_query_data = schemas.SearchQueryCreate(
            user_id=current_user.id,
            query_text=search_request.query,
            query_type="semantic",
            result_count=len(search_results),
            response_time=0.0,  # 实际应该计算响应时间
            filters_applied=search_request.filters or {}
        )
        crud.search_query.create(db=db, obj_in=search_query_data)
        
        return schemas.SemanticSearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            search_time=0.0,  # 实际应该计算搜索时间
            similarity_threshold=search_request.similarity_threshold
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/document-vectors/{document_id}", response_model=List[schemas.DocumentVectorResponse])
def get_document_vectors(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取文档的向量分块
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 检查用户权限
    if not crud.user.is_superuser(current_user) and document.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    vectors = crud.document_vector.get_by_document(db=db, document_id=document_id)
    
    return [
        schemas.DocumentVectorResponse(
            id=vector.id,
            document_id=vector.document_id,
            chunk_index=vector.chunk_index,
            chunk_text=vector.chunk_text,
            vector_model=vector.vector_model,
            embedding_dimension=vector.embedding_dimension,
            topic_category=vector.topic_category,
            importance_score=vector.importance_score,
            created_at=vector.created_at
        )
        for vector in vectors[skip:skip + limit]
    ]


@router.post("/analyze-document/{document_id}", response_model=schemas.DocumentAnalysisResponse)
def analyze_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int,
    analysis_request: schemas.DocumentAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    对文档进行AI智能分析
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 检查用户权限
    if not crud.user.is_superuser(current_user) and document.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # 启动后台分析任务
    background_tasks.add_task(
        _analyze_document_task,
        db,
        document_id,
        analysis_request.dict(),
        current_user.id
    )
    
    return schemas.DocumentAnalysisResponse(
        message="Document analysis started",
        document_id=document_id,
        analysis_types=analysis_request.analysis_types,
        status="processing"
    )


@router.get("/search-history", response_model=List[schemas.SearchQueryResponse])
def get_search_history(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取用户搜索历史
    """
    search_queries = crud.search_query.get_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    return [
        schemas.SearchQueryResponse(
            id=query.id,
            query_text=query.query_text,
            query_type=query.query_type,
            result_count=query.result_count,
            response_time=query.response_time,
            user_rating=query.user_rating,
            created_at=query.created_at
        )
        for query in search_queries
    ]


@router.get("/knowledge-graph/nodes", response_model=List[schemas.KnowledgeGraphNodeResponse])
def get_knowledge_graph_nodes(
    *,
    db: Session = Depends(deps.get_db),
    node_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取知识图谱节点
    """
    if search_query:
        nodes = crud.knowledge_graph.search_nodes(db=db, query=search_query, limit=limit)
    elif node_type:
        nodes = crud.knowledge_graph.get_by_type(db=db, node_type=node_type, limit=limit)
    elif entity_type:
        nodes = crud.knowledge_graph.get_by_entity_type(db=db, entity_type=entity_type, limit=limit)
    else:
        nodes = crud.knowledge_graph.get_multi(db=db, skip=0, limit=limit)
    
    return [
        schemas.KnowledgeGraphNodeResponse(
            id=node.id,
            node_id=node.node_id,
            node_name=node.node_name,
            node_type=node.node_type,
            entity_type=node.entity_type,
            node_description=node.node_description,
            confidence_score=node.confidence_score,
            source_document_id=node.source_document_id,
            created_at=node.created_at
        )
        for node in nodes
    ]


@router.get("/knowledge-graph/relations", response_model=List[schemas.KnowledgeGraphRelationResponse])
def get_knowledge_graph_relations(
    *,
    db: Session = Depends(deps.get_db),
    source_node_id: Optional[str] = Query(None),
    target_node_id: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取知识图谱关系
    """
    if source_node_id and target_node_id:
        relations = crud.knowledge_graph_relation.get_by_nodes(
            db=db, source_node_id=source_node_id, target_node_id=target_node_id
        )
    elif source_node_id:
        relations = crud.knowledge_graph_relation.get_node_relations(
            db=db, node_id=source_node_id, direction="outgoing"
        )
    elif target_node_id:
        relations = crud.knowledge_graph_relation.get_node_relations(
            db=db, node_id=target_node_id, direction="incoming"
        )
    elif relation_type:
        relations = crud.knowledge_graph_relation.get_by_relation_type(
            db=db, relation_type=relation_type, limit=limit
        )
    else:
        relations = crud.knowledge_graph_relation.get_multi(db=db, skip=0, limit=limit)
    
    return [
        schemas.KnowledgeGraphRelationResponse(
            id=relation.id,
            relation_id=relation.relation_id,
            source_node_id=relation.source_node_id,
            target_node_id=relation.target_node_id,
            relation_type=relation.relation_type,
            relation_description=relation.relation_description,
            weight=relation.weight,
            confidence_score=relation.confidence_score,
            source_document_id=relation.source_document_id,
            created_at=relation.created_at
        )
        for relation in relations
    ]


@router.get("/statistics", response_model=schemas.VectorStatisticsResponse)
def get_vector_statistics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    获取向量化统计信息（仅管理员）
    """
    vector_stats = crud.document_vector.get_statistics(db=db)
    
    # 获取搜索分析数据
    from datetime import timedelta
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    search_stats = crud.search_query.get_search_analytics(
        db=db, start_date=start_date, end_date=end_date
    )
    
    return schemas.VectorStatisticsResponse(
        vector_statistics=vector_stats,
        search_statistics=search_stats,
        generated_at=datetime.utcnow()
    )


# 后台任务函数
async def _vectorize_document_task(
    db: Session,
    document_id: int,
    vectorize_params: Dict[str, Any],
    user_id: int
):
    """
    后台文档向量化任务
    """
    try:
        # 获取文档
        document = crud.document.get(db=db, id=document_id)
        if not document:
            return
        
        # 更新文档状态
        document_update = schemas.DocumentUpdate(
            vector_status="processing"
        )
        crud.document.update(db=db, db_obj=document, obj_in=document_update)
        
        # 初始化AI集成服务
        ai_service = AIIntegrationService()
        
        # 执行向量化
        vectorization_result = await ai_service.vectorize_document(
            document=document,
            model_name=vectorize_params.get("model_name", "text-embedding-ada-002"),
            chunk_size=vectorize_params.get("chunk_size", 1000),
            chunk_overlap=vectorize_params.get("chunk_overlap", 200)
        )
        
        # 保存向量化结果
        for chunk_data in vectorization_result["chunks"]:
            vector_data = schemas.DocumentVectorCreate(
                document_id=document_id,
                chunk_index=chunk_data["index"],
                chunk_text=chunk_data["text"],
                embedding_vector=chunk_data["embedding"],
                vector_model=vectorize_params.get("model_name"),
                embedding_dimension=len(chunk_data["embedding"]),
                topic_category=chunk_data.get("topic"),
                importance_score=chunk_data.get("importance", 0.5)
            )
            crud.document_vector.create(db=db, obj_in=vector_data)
        
        # 更新文档向量化状态
        document_update = schemas.DocumentUpdate(
            is_vectorized=True,
            vector_status="completed",
            vector_model=vectorize_params.get("model_name"),
            embedding_dimension=len(vectorization_result["chunks"][0]["embedding"]),
            chunk_count=len(vectorization_result["chunks"]),
            vectorized_at=datetime.utcnow()
        )
        crud.document.update(db=db, db_obj=document, obj_in=document_update)
        
    except Exception as e:
        # 更新错误状态
        document_update = schemas.DocumentUpdate(
            vector_status=f"failed: {str(e)}"
        )
        crud.document.update(db=db, db_obj=document, obj_in=document_update)


async def _analyze_document_task(
    db: Session,
    document_id: int,
    analysis_params: Dict[str, Any],
    user_id: int
):
    """
    后台文档分析任务
    """
    try:
        # 获取文档
        document = crud.document.get(db=db, id=document_id)
        if not document:
            return
        
        # 初始化AI集成服务
        ai_service = AIIntegrationService()
        
        # 执行智能分析
        analysis_result = await ai_service.analyze_document(
            document=document,
            analysis_types=analysis_params.get("analysis_types", ["summary", "keywords"])
        )
        
        # 更新文档分析结果
        document_update = schemas.DocumentUpdate(
            ai_summary=analysis_result.get("summary"),
            ai_keywords=analysis_result.get("keywords"),
            document_classification=analysis_result.get("classification"),
            risk_assessment=analysis_result.get("risk_assessment"),
            compliance_analysis=analysis_result.get("compliance_analysis"),
            entity_extraction=analysis_result.get("entities")
        )
        crud.document.update(db=db, db_obj=document, obj_in=document_update)
        
        # 如果启用了知识图谱构建
        if "knowledge_graph" in analysis_params.get("analysis_types", []):
            kg_service = KnowledgeGraphService()
            await kg_service.build_knowledge_graph_from_document(
                db=db, document=document, analysis_result=analysis_result
            )
        
    except Exception as e:
        # 记录错误日志
        print(f"Document analysis failed for document {document_id}: {str(e)}")