from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.models.document import Document
from app.services.document_service import document_service
from app.schemas.response import ResponseModel

router = APIRouter()

@router.post(
    "/process/{document_id}", 
    response_model=ResponseModel,
    summary="处理单个文档OCR",
    description="对指定文档进行OCR文字识别处理，支持多种OCR引擎自动选择和手写文字识别"
)
def process_document_ocr(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    处理单个文档的OCR
    
    - **document_id**: 要处理的文档ID
    - **返回**: OCR处理结果，包含提取的文本、使用的引擎、置信度等信息
    - **特性**: 自动引擎选择、中文优化、手写识别、智能回退
    """
    # 检查文档是否存在
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # 检查是否已经处理过
    if document.is_ocr_processed:
        return ResponseModel(
            code=200,
            message="Document already processed",
            data={
                "document_id": document_id,
                "ocr_text": document.ocr_text,
                "ocr_engine": document.ocr_engine,
                "ocr_confidence": document.ocr_confidence,
                "is_handwritten": document.is_handwritten
            }
        )
    
    try:
        # 处理OCR
        result = document_service.process_document_ocr(document, db)
        
        if result['success']:
            return ResponseModel(
                code=200,
                message="OCR processing completed successfully",
                data={
                    "document_id": document_id,
                    "text": result['text'],
                    "engine": result['engine'],
                    "confidence": result['confidence'],
                    "is_handwritten": result.get('is_handwritten', False),
                    "pages_processed": result.get('pages_processed')
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

@router.post(
    "/batch-process", 
    response_model=ResponseModel,
    summary="批量处理文档OCR",
    description="批量处理多个文档的OCR识别，最多支持50个文档同时处理"
)
def batch_process_ocr(
    document_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    批量处理文档OCR
    
    - **document_ids**: 要处理的文档ID列表（最多50个）
    - **返回**: 批量处理结果统计，包含成功、失败、跳过的数量
    - **限制**: 单次最多处理50个文档
    """
    if not document_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document IDs list cannot be empty"
        )
    
    if len(document_ids) > 50:  # 限制批量处理数量
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process more than 50 documents at once"
        )
    
    try:
        # 执行批量处理
        results = document_service.batch_process_ocr(document_ids, db)
        
        return ResponseModel(
            code=200,
            message=f"Batch processing completed. Processed: {results['processed']}, Failed: {results['failed']}, Skipped: {results['skipped']}",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch OCR processing failed: {str(e)}"
        )

@router.get(
    "/status/{document_id}", 
    response_model=ResponseModel,
    summary="获取文档OCR处理状态",
    description="查询指定文档的OCR处理状态和基本信息"
)
def get_ocr_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    获取文档OCR处理状态
    
    - **document_id**: 文档ID
    - **返回**: 文档OCR处理状态、引擎信息、置信度、处理时间等
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return ResponseModel(
        code=200,
        message="OCR status retrieved successfully",
        data={
            "document_id": document_id,
            "filename": document.filename,
            "is_ocr_processed": document.is_ocr_processed,
            "ocr_engine": document.ocr_engine,
            "ocr_confidence": document.ocr_confidence,
            "is_handwritten": document.is_handwritten,
            "ocr_text_length": len(document.ocr_text) if document.ocr_text else 0,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None
        }
    )

@router.get(
    "/text/{document_id}", 
    response_model=ResponseModel,
    summary="获取文档OCR文本内容",
    description="获取已处理文档的OCR识别文本内容和相关元数据"
)
def get_ocr_text(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    获取文档OCR提取的文本内容
    
    - **document_id**: 文档ID
    - **返回**: OCR提取的完整文本内容、引擎信息、置信度等
    - **前提**: 文档必须已完成OCR处理
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.is_ocr_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has not been processed with OCR yet"
        )
    
    return ResponseModel(
        code=200,
        message="OCR text retrieved successfully",
        data={
            "document_id": document_id,
            "filename": document.filename,
            "ocr_text": document.ocr_text,
            "ocr_engine": document.ocr_engine,
            "ocr_confidence": document.ocr_confidence,
            "is_handwritten": document.is_handwritten,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None
        }
    )

@router.get(
    "/statistics", 
    response_model=ResponseModel,
    summary="获取OCR处理统计信息",
    description="获取OCR处理的统计数据，可按项目筛选"
)
def get_ocr_statistics(
    project_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    获取OCR处理统计信息
    
    - **project_id**: 可选，指定项目ID进行筛选
    - **返回**: OCR处理统计数据，包含总数、成功率、引擎使用情况等
    """
    try:
        stats = document_service.get_ocr_statistics(db, project_id)
        
        return ResponseModel(
            code=200,
            message="OCR statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve OCR statistics: {str(e)}"
        )

@router.post(
    "/reprocess/{document_id}", 
    response_model=ResponseModel,
    summary="重新处理文档OCR",
    description="强制重新处理已处理或处理失败的文档，支持覆盖现有OCR结果"
)
def reprocess_document_ocr(
    document_id: int,
    force: bool = False,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    重新处理文档OCR
    
    - **document_id**: 要重新处理的文档ID
    - **force**: 是否强制重新处理已处理的文档（默认false）
    - **返回**: 重新处理后的OCR结果
    - **用途**: 处理失败重试、更换OCR引擎、提升识别质量
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # 如果已经处理过且不强制重新处理，则返回错误
    if document.is_ocr_processed and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already processed. Use force=true to reprocess"
        )
    
    try:
        # 重置OCR状态
        document.is_ocr_processed = False
        document.ocr_text = None
        document.ocr_engine = None
        document.ocr_confidence = None
        document.is_handwritten = None
        document.ocr_details = None
        db.commit()
        
        # 重新处理OCR
        result = document_service.process_document_ocr(document, db)
        
        if result['success']:
            return ResponseModel(
                code=200,
                message="Document reprocessed successfully",
                data={
                    "document_id": document_id,
                    "text": result['text'],
                    "engine": result['engine'],
                    "confidence": result['confidence'],
                    "is_handwritten": result.get('is_handwritten', False),
                    "pages_processed": result.get('pages_processed')
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR reprocessing failed: {str(e)}"
        )