from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import os
from datetime import datetime

from app import crud, models, schemas
from app.api import deps
from app.services.document_service import document_service
from app.schemas.response import ResponseModel
from app.core.config import settings

router = APIRouter()


@router.post(
    "/upload/{project_id}",
    response_model=ResponseModel,
    summary="上传文档到项目",
    description="上传文档文件到指定项目，支持图片、PDF、Word等多种格式"
)
def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    document_category: str = Form(...),
    document_type: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    上传文档到项目
    
    - **project_id**: 目标项目ID
    - **file**: 要上传的文档文件
    - **document_category**: 文档类别（必填）
    - **document_type**: 具体文档类型（可选）
    - **description**: 文档描述（可选）
    - **返回**: 上传成功的文档信息
    - **权限**: 需要用户登录认证
    - **支持格式**: JPG, PNG, PDF, DOC, DOCX, TXT等
    """
    # 检查项目是否存在
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 检查文件类型
    file_extension = Path(file.filename).suffix.lower()
    supported_extensions = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',  # 图片
        '.pdf',  # PDF
        '.doc', '.docx', '.txt', '.rtf'  # 文档
    }
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}"
        )
    
    try:
        # 创建项目上传目录
        upload_dir = Path(settings.UPLOAD_DIR) / f"project_{project_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 创建文档记录
        document_data = {
            "filename": file.filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": os.path.getsize(file_path),
            "file_type": file_extension.lstrip('.'),
            "mime_type": file.content_type,
            "project_id": project_id,
            "uploader_id": current_user.id,
            "document_category": document_category,
            "document_type": document_type,
            "summary": summary
        }
        
        # 保存到数据库
        from app.models.document import Document
        document = Document(**document_data)
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return ResponseModel(
            code=200,
            message="Document uploaded successfully",
            data={
                "document_id": document.id,
                "filename": document.filename,
                "file_size": document.file_size,
                "file_type": document.file_type,
                "document_category": document.document_category,
                "created_at": document.created_at.isoformat()
            }
        )
        
    except Exception as e:
        # 如果数据库操作失败，删除已上传的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get(
    "/project/{project_id}",
    response_model=ResponseModel,
    summary="获取项目文档列表",
    description="获取指定项目的所有文档列表，支持分页和筛选"
)
def get_project_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    document_category: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    获取项目文档列表
    
    - **project_id**: 项目ID
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（默认100）
    - **document_category**: 可选，按文档类别筛选
    - **返回**: 文档列表和统计信息
    - **权限**: 需要用户登录认证
    """
    # 检查项目是否存在
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        from app.models.document import Document
        
        # 构建查询
        query = db.query(Document).filter(Document.project_id == project_id)
        
        if document_category:
            query = query.filter(Document.document_category == document_category)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        documents = query.offset(skip).limit(limit).all()
        
        # 格式化文档信息
        document_list = []
        for doc in documents:
            document_list.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "document_category": doc.document_category,
                "document_type": doc.document_type,
                "summary": doc.summary,
                "is_ocr_processed": doc.is_ocr_processed,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "uploader_id": doc.uploader_id
            })
        
        return ResponseModel(
            code=200,
            message="Documents retrieved successfully",
            data={
                "documents": document_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=ResponseModel,
    summary="获取文档详细信息",
    description="获取指定文档的详细信息，包括OCR处理状态"
)
def get_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    获取文档详细信息
    
    - **document_id**: 文档ID
    - **返回**: 文档的完整信息，包括OCR处理状态
    - **权限**: 需要用户登录认证
    """
    from app.models.document import Document
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return ResponseModel(
        code=200,
        message="Document retrieved successfully",
        data={
            "id": document.id,
            "filename": document.filename,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "project_id": document.project_id,
            "uploader_id": document.uploader_id,
            "document_category": document.document_category,
            "document_type": document.document_type,
            "summary": document.summary,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "is_ocr_processed": document.is_ocr_processed,
            "ocr_engine": document.ocr_engine,
            "ocr_confidence": document.ocr_confidence,
            "is_handwritten": document.is_handwritten,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "extracted_text_length": len(document.extracted_text) if document.extracted_text else 0
        }
    )


@router.delete(
    "/{document_id}",
    response_model=ResponseModel,
    summary="删除文档",
    description="删除指定文档及其关联的文件"
)
def delete_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    删除文档
    
    - **document_id**: 要删除的文档ID
    - **返回**: 删除操作结果
    - **权限**: 需要用户登录认证
    - **注意**: 将同时删除数据库记录和物理文件
    """
    from app.models.document import Document
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # 删除物理文件
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        db.delete(document)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="Document deleted successfully",
            data={
                "document_id": document_id,
                "filename": document.filename
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.put(
    "/{document_id}",
    response_model=ResponseModel,
    summary="更新文档信息",
    description="更新文档的元数据信息（不包括文件内容）"
)
def update_document(
    document_id: int,
    document_category: Optional[str] = None,
    document_type: Optional[str] = None,
    summary: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    更新文档信息
    
    - **document_id**: 要更新的文档ID
    - **document_category**: 新的文档类别（可选）
    - **document_type**: 新的文档类型（可选）
    - **summary**: 新的文档摘要（可选）
    - **返回**: 更新后的文档信息
    - **权限**: 需要用户登录认证
    """
    from app.models.document import Document
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # 更新字段
        if document_category is not None:
            document.document_category = document_category
        if document_type is not None:
            document.document_type = document_type
        if summary is not None:
            document.summary = summary
        
        db.commit()
        db.refresh(document)
        
        return ResponseModel(
            code=200,
            message="Document updated successfully",
            data={
                "id": document.id,
                "filename": document.filename,
                "document_category": document.document_category,
                "document_type": document.document_type,
                "summary": document.summary
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )