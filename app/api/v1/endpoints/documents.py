import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core.config import settings
from app.models.document import Document
from app.models.project import Project
from app.schemas.response import ResponseModel
from app.services.cache_service import cache_service
from app.utils.cache_decorator import fastapi_cache_medium, fastapi_cache_short

"""
文档管理API端点

提供文档上传、批量上传、查询等功能的API接口。
"""


router = APIRouter()


@router.post(
    "/upload",
    response_model=ResponseModel,
    summary="上传文档到项目",
    description="上传文档文件到指定项目，支持图片、PDF、Word等多种格式",
)
def upload_document(
    request: Request,
    project_id: int,
    file: UploadFile = File(...),
    document_category: str = Form(...),
    document_type: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    上传文档到项目

    - **project_id**: 目标项目ID
    - **file**: 要上传的文档文件
    - **document_category**: 文档类别（必填）
    - **document_type**: 具体文档类型（可选）
    - **summary**: 文档描述（可选）
    - **返回**: 上传成功的文档信息
    - **权限**: 需要用户登录认证
    - **支持格式**: JPG, PNG, PDF, DOC, DOCX, TXT等
    """
    # 使用默认用户ID（无需认证）
    uploader_id = 1

    # 检查项目是否存在
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # 检查文件类型
    file_extension = Path(file.filename).suffix.lower()
    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",  # 图片
        ".pdf",  # PDF
        ".doc",
        ".docx",
        ".txt",
        ".rtf",  # 文档
    }

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}",
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
            "file_type": file_extension.lstrip("."),
            "mime_type": file.content_type,
            "project_id": project_id,
            "uploader_id": uploader_id,
            "document_category": document_category,
            "document_type": document_type,
            "summary": summary,
        }

        # 保存到数据库

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
                "created_at": document.created_at.isoformat(),
            },
        )

    except Exception as e:
        # 如果数据库操作失败，删除已上传的文件
        if "file_path" in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.post(
    "/batch-upload",
    response_model=ResponseModel,
    summary="批量上传文档到项目",
    description="批量上传多个文档文件到指定项目，最多支持10个文件同时上传",
)
def batch_upload_documents(
    request: Request,
    project_id: int,
    files: List[UploadFile] = File(...),
    document_category: str = Form(...),
    document_type: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    批量上传文档到项目

    - **project_id**: 目标项目ID
    - **files**: 要上传的文档文件列表（最多10个）
    - **document_category**: 文档类别（必填）
    - **document_type**: 具体文档类型（可选）
    - **summary**: 文档描述（可选）
    - **返回**: 上传成功的文档信息列表
    - **权限**: 需要用户登录认证
    - **支持格式**: JPG, PNG, PDF, DOC, DOCX, TXT等
    """
    # 检查文件数量限制
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed for batch upload",
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    # 使用默认用户ID（无需认证）
    uploader_id = 1

    # 检查项目是否存在
    project = crud.project.get(db, id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # 检查所有文件类型
    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".tif",  # 图片
        ".pdf",  # PDF
        ".doc",
        ".docx",
        ".txt",
        ".rtf",  # 文档
    }

    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type: {file_extension} "
                    f"in file {file.filename}"
                ),
            )

    uploaded_documents = []
    failed_uploads = []

    try:
        # 创建项目上传目录
        upload_dir = Path(settings.UPLOAD_DIR) / f"project_{project_id}"
        upload_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            try:
                # 生成唯一文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{file.filename}"
                file_path = upload_dir / safe_filename

                # 保存文件
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # 创建文档记录
                file_extension = Path(file.filename).suffix.lower()
                document_data = {
                    "filename": file.filename,
                    "original_filename": file.filename,
                    "file_path": str(file_path),
                    "file_size": os.path.getsize(file_path),
                    "file_type": file_extension.lstrip("."),
                    "mime_type": file.content_type,
                    "project_id": project_id,
                    "uploader_id": uploader_id,
                    "document_category": document_category,
                    "document_type": document_type,
                    "summary": summary,
                }

                # 保存到数据库

                document = Document(**document_data)
                db.add(document)
                db.flush()  # 获取ID但不提交

                uploaded_documents.append(
                    {
                        "document_id": document.id,
                        "filename": document.filename,
                        "file_size": document.file_size,
                        "file_type": document.file_type,
                        "document_category": document.document_category,
                        "status": "success",
                    }
                )

            except Exception as e:
                # 记录失败的文件
                failed_uploads.append(
                    {"filename": file.filename, "error": str(e), "status": "failed"}
                )

                # 如果文件已保存但数据库操作失败，删除文件
                if "file_path" in locals() and file_path.exists():
                    file_path.unlink()

        # 如果有成功上传的文件，提交事务
        if uploaded_documents:
            db.commit()

        # 构建响应
        response_data = {
            "uploaded_documents": uploaded_documents,
            "failed_uploads": failed_uploads,
            "total_files": len(files),
            "successful_uploads": len(uploaded_documents),
            "failed_uploads_count": len(failed_uploads),
        }

        if failed_uploads:
            message = (
                f"Batch upload completed with {len(uploaded_documents)} "
                f"successful and {len(failed_uploads)} failed uploads"
            )
        else:
            message = f"All {len(uploaded_documents)} files uploaded successfully"

        return ResponseModel(code=200, message=message, data=response_data)

    except Exception as e:
        db.rollback()
        # 清理所有已上传的文件
        for doc_info in uploaded_documents:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{doc_info['filename']}"
                file_path = upload_dir / filename
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}",
        )


@router.get(
    "/project/{project_id}",
    response_model=ResponseModel,
    summary="获取项目文档列表",
    description="获取指定项目的所有文档列表，支持分页和筛选",
)
@fastapi_cache_medium
def get_project_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    document_category: Optional[str] = None,
    db: Session = Depends(deps.get_db),
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    try:

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
            document_list.append(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "document_category": doc.document_category,
                    "document_type": doc.document_type,
                    "summary": doc.summary,
                    "is_ocr_processed": doc.is_ocr_processed,
                    "created_at": (
                        doc.created_at.isoformat() if doc.created_at else None
                    ),
                    "uploader_id": doc.uploader_id,
                }
            )

        return ResponseModel(
            code=200,
            message="Documents retrieved successfully",
            data={
                "documents": document_list,
                "total": total,
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


@router.get(
    "/search",
    response_model=ResponseModel,
    summary="搜索文档",
    description="根据关键词搜索文档，支持按文件名、摘要、文本内容等多字段搜索",
)
@fastapi_cache_short
def search_documents(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    搜索文档

    - **q**: 搜索关键词（必填）
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（默认100）
    - **project_id**: 可选，限制在指定项目中搜索
    - **返回**: 匹配的文档列表
    - **权限**: 需要用户登录认证
    """
    # 验证查询参数
    if not q or len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters long",
        )

    # 验证项目是否存在（如果提供了project_id）
    if project_id:
        project = crud.project.get(db, id=project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )

    try:
        # 使用CRUD层的搜索功能
        documents = crud.document.search_documents(
            db=db, query=q.strip(), project_id=project_id, skip=skip, limit=limit
        )

        # 获取总数（不分页）
        total_documents = crud.document.search_documents(
            db=db, query=q.strip(), project_id=project_id, skip=0, limit=None
        )
        total_count = len(total_documents)

        # 格式化搜索结果
        search_results = []
        for doc in documents:
            search_results.append(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "file_type": doc.file_type,
                    "document_category": doc.document_category,
                    "document_type": doc.document_type,
                    "summary": doc.summary,
                    "project_id": doc.project_id,
                    "created_at": (
                        doc.created_at.isoformat() if doc.created_at else None
                    ),
                    "uploader_id": doc.uploader_id,
                }
            )

        return ResponseModel(
            code=200,
            message=f"Found {total_count} documents matching '{q}'",
            data={
                "documents": search_results,
                "query": q.strip(),
                "total_results": total_count,
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get(
    "/{document_id}",
    response_model=ResponseModel,
    summary="获取文档详细信息",
    description="根据文档ID获取文档的详细信息",
)
@fastapi_cache_medium
def get_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取文档详细信息

    - **document_id**: 文档ID
    - **返回**: 文档的详细信息
    - **权限**: 需要用户登录认证
    """
    try:

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        return ResponseModel(
            code=200,
            message="Document retrieved successfully",
            data={
                "id": document.id,
                "filename": document.filename,
                "original_filename": document.original_filename,
                "file_path": document.file_path,
                "file_size": document.file_size,
                "file_type": document.file_type,
                "mime_type": document.mime_type,
                "document_category": document.document_category,
                "document_type": document.document_type,
                "summary": document.summary,
                "project_id": document.project_id,
                "uploader_id": document.uploader_id,
                "is_ocr_processed": document.is_ocr_processed,
                "ocr_text": document.ocr_text,
                "created_at": (
                    document.created_at.isoformat() if document.created_at else None
                ),
                "updated_at": (
                    document.updated_at.isoformat() if document.updated_at else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )


class DocumentUpdateRequest(BaseModel):

    document_category: Optional[str] = None
    document_type: Optional[str] = None
    summary: Optional[str] = None


@router.put(
    "/{document_id}",
    response_model=ResponseModel,
    summary="更新文档信息",
    description="根据文档ID更新文档的元数据信息",
)
def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    更新文档信息

    - **document_id**: 文档ID
    - **document_category**: 文档类别（可选）
    - **document_type**: 文档类型（可选）
    - **summary**: 文档摘要（可选）
    - **返回**: 更新后的文档信息
    - **权限**: 需要用户登录认证
    """
    try:

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # 更新文档信息
        if request.document_category is not None:
            document.document_category = request.document_category
        if request.document_type is not None:
            document.document_type = request.document_type
        if request.summary is not None:
            document.summary = request.summary

        # 更新时间戳

        document.updated_at = datetime.utcnow()

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
                "summary": document.summary,
                "updated_at": (
                    document.updated_at.isoformat() if document.updated_at else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}",
        )


@router.delete(
    "/{document_id}",
    response_model=ResponseModel,
    summary="删除文档",
    description="根据文档ID删除文档及其关联的文件",
)
def delete_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    删除文档

    - **document_id**: 文档ID
    - **返回**: 删除操作的结果
    - **权限**: 需要用户登录认证
    """
    try:

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # 删除物理文件
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        # 删除数据库记录
        db.delete(document)
        db.commit()

        # 清除相关缓存

        # 清除get_document的缓存
        cache_service.clear_pattern(f"get_document:*{document_id}*", "api")

        return ResponseModel(
            code=200,
            message="Document deleted successfully",
            data={"document_id": document_id, "filename": document.filename},
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
