from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
import json
from datetime import datetime

from app.api import deps
from app.models.document import Document
from app.services.document_service import document_service
from app.schemas.response import ResponseModel
from app.middleware import strict_rate_limit, moderate_rate_limit, loose_rate_limit
from app.utils.cache_decorator import fastapi_cache_medium, fastapi_cache_short

router = APIRouter()

@router.post(
    "/process/{document_id}", 
    response_model=ResponseModel,
    summary="处理单个文档OCR",
    description="对指定文档进行OCR文字识别处理，支持多种OCR引擎自动选择和手写文字识别"
)
@strict_rate_limit
def process_document_ocr(
    request: Request,
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
@strict_rate_limit
def batch_process_ocr(
    request: Request,
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
@loose_rate_limit
def get_ocr_status(
    request: Request,
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
@fastapi_cache_medium
@loose_rate_limit
def get_ocr_text(
    request: Request,
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
@fastapi_cache_medium
@loose_rate_limit
def get_ocr_statistics(
    request: Request,
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
@moderate_rate_limit
def reprocess_document_ocr(
    request: Request,
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

@router.get(
    "/export",
    summary="导出OCR结果",
    description="导出OCR处理结果，支持JSON、CSV、TXT格式，可按条件过滤"
)
@moderate_rate_limit
def export_ocr_results(
    request: Request,
    format: str = Query("json", description="导出格式: json, csv, txt"),
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    导出OCR结果
    
    - **format**: 导出格式 (json, csv, txt)
    - **project_id**: 可选，按项目ID过滤
    - **start_date**: 可选，开始日期过滤
    - **end_date**: 可选，结束日期过滤
    - **返回**: 导出的文件流
    """
    # 验证导出格式
    if format not in ["json", "csv", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Supported formats: json, csv, txt"
        )
    
    try:
        # 构建查询
        query = db.query(Document).filter(Document.is_ocr_processed == True)
        
        # 如果不是超级用户，只能导出自己上传的文档
        if not current_user.is_superuser:
            query = query.filter(Document.uploader_id == current_user.id)
        
        # 按项目过滤
        if project_id:
            query = query.filter(Document.project_id == project_id)
        
        # 按日期过滤
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Document.processed_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Document.processed_at <= end_dt)
        
        # 获取结果
        documents = query.all()
        
        # 根据格式生成导出内容
        if format == "json":
            content = _export_json(documents)
            media_type = "application/json"
            filename = f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif format == "csv":
            content = _export_csv(documents)
            media_type = "text/csv"
            filename = f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:  # txt
            content = _export_txt(documents)
            media_type = "text/plain"
            filename = f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

def _export_json(documents):
    """导出为JSON格式"""
    data = []
    for doc in documents:
        data.append({
            "id": doc.id,
            "filename": doc.filename,
            "project_id": doc.project_id,
            "ocr_text": doc.ocr_text,
            "ocr_engine": doc.ocr_engine,
            "ocr_confidence": doc.ocr_confidence,
            "is_handwritten": doc.is_handwritten,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
            "uploader_id": doc.uploader_id
        })
    return json.dumps(data, ensure_ascii=False, indent=2)

def _export_csv(documents):
    """导出为CSV格式"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow([
        "ID", "文件名", "项目ID", "OCR文本", "OCR引擎", 
        "置信度", "是否手写", "处理时间", "上传者ID"
    ])
    
    # 写入数据行
    for doc in documents:
        writer.writerow([
            doc.id,
            doc.filename,
            doc.project_id,
            doc.ocr_text,
            doc.ocr_engine,
            doc.ocr_confidence,
            doc.is_handwritten,
            doc.processed_at.isoformat() if doc.processed_at else "",
            doc.uploader_id
        ])
    
    return output.getvalue()

def _export_txt(documents):
    """导出为纯文本格式"""
    lines = []
    lines.append("OCR结果导出")
    lines.append("=" * 50)
    lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总计文档: {len(documents)}")
    lines.append("=" * 50)
    lines.append("")
    
    for i, doc in enumerate(documents, 1):
        lines.append(f"文档 {i}: {doc.filename}")
        lines.append(f"项目ID: {doc.project_id}")
        lines.append(f"OCR引擎: {doc.ocr_engine}")
        lines.append(f"置信度: {doc.ocr_confidence}")
        lines.append(f"是否手写: {doc.is_handwritten}")
        lines.append(f"处理时间: {doc.processed_at.isoformat() if doc.processed_at else '未知'}")
        lines.append("OCR文本内容:")
        lines.append("-" * 30)
        lines.append(doc.ocr_text or "无内容")
        lines.append("-" * 30)
        lines.append("")
    
    return "\n".join(lines)