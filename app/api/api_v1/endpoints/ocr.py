from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
import json

from app import crud, models, schemas
from app.api import deps
from app.core.permissions import (
    Permission, require_permissions, get_current_active_user
)
from app.db.session import get_db
from app.core.config import settings
from app.services.ocr_service import OCRService

router = APIRouter()

# 支持的图像文件类型
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def validate_ocr_file(file: UploadFile) -> None:
    """验证OCR文件"""
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def save_temp_file(file: UploadFile) -> str:
    """保存临时文件用于OCR处理"""
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_ext = Path(file.filename).suffix
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    with open(temp_path, "wb") as buffer:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（{MAX_FILE_SIZE // (1024*1024)}MB）"
            )
        buffer.write(content)
    
    return temp_path


@router.post("/process", response_model=schemas.OCRResult)
def process_ocr(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    engine: str = Form("tesseract", description="OCR引擎: tesseract, paddleocr, easyocr"),
    language: str = Form("chi_sim+eng", description="识别语言"),
    document_id: Optional[int] = Form(None, description="关联的文档ID"),
    current_user: models.User = Depends(require_permissions(Permission.OCR_PROCESS)),
) -> Any:
    """
    处理OCR文字识别
    """
    # 验证文件
    validate_ocr_file(file)
    
    # 验证OCR引擎
    supported_engines = ["tesseract", "paddleocr", "easyocr"]
    if engine not in supported_engines:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的OCR引擎。支持的引擎: {', '.join(supported_engines)}"
        )
    
    # 如果指定了文档ID，检查文档是否存在且用户有权限
    document = None
    if document_id:
        document = crud.document.get(db=db, id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查权限
        if not (
            current_user.is_superuser
            or document.uploaded_by == current_user.id
        ):
            raise HTTPException(status_code=403, detail="没有权限处理此文档")
    
    # 保存临时文件
    try:
        temp_file_path = save_temp_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    try:
        # 初始化OCR服务
        ocr_service = OCRService()
        
        # 执行OCR处理
        ocr_result = ocr_service.process_file(
            file_path=temp_file_path,
            engine=engine,
            language=language
        )
        
        # 创建OCR结果记录
        ocr_result_in = schemas.OCRResultCreate(
            filename=file.filename,
            engine=engine,
            language=language,
            text_content=ocr_result["text"],
            confidence_score=ocr_result.get("confidence", 0.0),
            processing_time=ocr_result.get("processing_time", 0.0),
            word_count=len(ocr_result["text"].split()) if ocr_result["text"] else 0,
            metadata=json.dumps(ocr_result.get("metadata", {})),
            document_id=document_id
        )
        
        ocr_record = crud.ocr_result.create_with_processor(
            db=db, obj_in=ocr_result_in, processor_id=current_user.id
        )
        
        return ocr_record
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR处理失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception:
            pass


@router.post("/batch-process")
def batch_process_ocr(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    engine: str = Form("tesseract"),
    language: str = Form("chi_sim+eng"),
    current_user: models.User = Depends(require_permissions(Permission.OCR_PROCESS)),
) -> Any:
    """
    批量处理OCR文字识别
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="批量处理最多支持10个文件"
        )
    
    # 验证所有文件
    for file in files:
        validate_ocr_file(file)
    
    # 创建批处理任务
    task_ids = []
    for file in files:
        try:
            temp_file_path = save_temp_file(file)
            # 这里应该使用后台任务处理，简化示例直接返回任务信息
            task_id = str(uuid.uuid4())
            task_ids.append({
                "task_id": task_id,
                "filename": file.filename,
                "status": "queued"
            })
        except Exception as e:
            task_ids.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": "批处理任务已创建",
        "tasks": task_ids
    }


@router.get("/results", response_model=List[schemas.OCRResult])
def read_ocr_results(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    document_id: Optional[int] = None,
    engine: Optional[str] = None,
    current_user: models.User = Depends(require_permissions(Permission.OCR_LIST)),
) -> Any:
    """
    获取OCR结果列表
    """
    filters = {}
    if document_id:
        filters["document_id"] = document_id
    if engine:
        filters["engine"] = engine
    
    # 如果不是超级用户，只能查看自己处理的结果
    if not current_user.is_superuser:
        filters["processed_by"] = current_user.id
    
    if filters:
        results = crud.ocr_result.get_by_filters(
            db, filters=filters, skip=skip, limit=limit
        )
    else:
        if current_user.is_superuser:
            results = crud.ocr_result.get_multi(db, skip=skip, limit=limit)
        else:
            results = crud.ocr_result.get_by_processor(
                db, processor_id=current_user.id, skip=skip, limit=limit
            )
    
    return results


@router.get("/results/{result_id}", response_model=schemas.OCRResult)
def read_ocr_result(
    *,
    db: Session = Depends(get_db),
    result_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    根据ID获取OCR结果详情
    """
    result = crud.ocr_result.get(db=db, id=result_id)
    if not result:
        raise HTTPException(status_code=404, detail="OCR结果不存在")
    
    # 权限检查：超级用户或处理者可以查看
    if not (
        current_user.is_superuser
        or result.processed_by == current_user.id
    ):
        raise HTTPException(status_code=403, detail="没有权限访问此OCR结果")
    
    return result


@router.delete("/results/{result_id}")
def delete_ocr_result(
    *,
    db: Session = Depends(get_db),
    result_id: int,
    current_user: models.User = Depends(require_permissions(Permission.OCR_DELETE)),
) -> Any:
    """
    删除OCR结果
    """
    result = crud.ocr_result.get(db=db, id=result_id)
    if not result:
        raise HTTPException(status_code=404, detail="OCR结果不存在")
    
    # 权限检查：超级用户或处理者可以删除
    if not (
        current_user.is_superuser
        or result.processed_by == current_user.id
    ):
        raise HTTPException(status_code=403, detail="没有权限删除此OCR结果")
    
    crud.ocr_result.remove(db=db, id=result_id)
    return {"message": "OCR结果删除成功"}


@router.get("/engines")
def get_available_engines(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    获取可用的OCR引擎列表
    """
    engines = [
        {
            "name": "tesseract",
            "display_name": "Tesseract OCR",
            "description": "开源OCR引擎，支持多种语言",
            "languages": ["chi_sim", "chi_tra", "eng", "chi_sim+eng"]
        },
        {
            "name": "paddleocr",
            "display_name": "PaddleOCR",
            "description": "百度开源OCR引擎，中文识别效果好",
            "languages": ["ch", "en", "ch+en"]
        },
        {
            "name": "easyocr",
            "display_name": "EasyOCR",
            "description": "易用的OCR引擎，支持80+语言",
            "languages": ["ch_sim", "ch_tra", "en", "ch_sim+en"]
        }
    ]
    
    return {"engines": engines}


@router.get("/statistics")
def get_ocr_statistics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permissions(Permission.OCR_LIST)),
) -> Any:
    """
    获取OCR处理统计信息
    """
    # 如果不是超级用户，只统计自己的数据
    processor_id = None if current_user.is_superuser else current_user.id
    
    statistics = crud.ocr_result.get_statistics(db, processor_id=processor_id)
    return statistics