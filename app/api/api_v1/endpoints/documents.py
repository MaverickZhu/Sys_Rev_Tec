from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path

from app import crud, models, schemas
from app.api import deps
from app.core.permissions import (
    Permission, require_permissions, get_current_active_user,
    get_user_permissions
)
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

# 支持的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file(file: UploadFile) -> None:
    """验证上传文件"""
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 检查文件大小（这里只能检查已读取的内容，实际大小检查需要在读取时进行）
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（{MAX_FILE_SIZE // (1024*1024)}MB）"
        )


def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    """保存上传文件并返回文件路径"""
    # 创建上传目录
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（{MAX_FILE_SIZE // (1024*1024)}MB）"
            )
        buffer.write(content)
    
    return file_path


@router.get("/", response_model=List[schemas.Document])
def read_documents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    document_type: Optional[str] = None,
    current_user: models.User = Depends(require_permissions(Permission.DOCUMENT_LIST)),
) -> Any:
    """
    获取文档列表
    """
    # 构建筛选条件
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if document_type:
        filters["document_type"] = document_type
    
    # 如果不是超级用户或管理员，只能查看自己上传的文档
    user_permissions = get_user_permissions(current_user)
    if not (current_user.is_superuser or Permission.DOCUMENT_READ in user_permissions):
        filters["uploaded_by"] = current_user.id
    
    if filters:
        documents = crud.document.get_by_filters(
            db, filters=filters, skip=skip, limit=limit
        )
    else:
        if current_user.is_superuser or Permission.DOCUMENT_READ in user_permissions:
            documents = crud.document.get_multi(db, skip=skip, limit=limit)
        else:
            documents = crud.document.get_by_uploader(
                db, uploader_id=current_user.id, skip=skip, limit=limit
            )
    
    return documents


@router.post("/upload", response_model=schemas.Document)
def upload_document(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: models.User = Depends(require_permissions(Permission.DOCUMENT_CREATE)),
) -> Any:
    """
    上传文档
    """
    # 验证文件
    validate_file(file)
    
    # 如果指定了项目ID，检查项目是否存在且用户有权限
    if project_id:
        project = crud.project.get(db=db, id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查用户是否有权限向该项目上传文档
        user_permissions = get_user_permissions(current_user)
        if not (
            current_user.is_superuser
            or project.owner_id == current_user.id
            or Permission.DOCUMENT_CREATE in user_permissions
        ):
            raise HTTPException(status_code=403, detail="没有权限向此项目上传文档")
    
    # 保存文件
    upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    try:
        file_path = save_upload_file(file, upload_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 创建文档记录
    document_in = schemas.DocumentCreate(
        filename=file.filename,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        document_type=document_type,
        description=description,
        project_id=project_id
    )
    
    document = crud.document.create_with_uploader(
        db=db, obj_in=document_in, uploader_id=current_user.id
    )
    
    return document


@router.get("/{document_id}", response_model=schemas.Document)
def read_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    根据ID获取文档详情
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 权限检查：超级用户、文档上传者或有读取权限的用户可以查看
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or document.uploaded_by == current_user.id
        or Permission.DOCUMENT_READ in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限访问此文档")
    
    return document


@router.put("/{document_id}", response_model=schemas.Document)
def update_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    document_in: schemas.DocumentUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    更新文档信息
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 权限检查：超级用户、文档上传者或有更新权限的用户可以修改
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or document.uploaded_by == current_user.id
        or Permission.DOCUMENT_UPDATE in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限修改此文档")
    
    document = crud.document.update(db=db, db_obj=document, obj_in=document_in)
    return document


@router.delete("/{document_id}")
def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: models.User = Depends(require_permissions(Permission.DOCUMENT_DELETE)),
) -> Any:
    """
    删除文档
    """
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 权限检查：超级用户、文档上传者或有删除权限的用户可以删除
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or document.uploaded_by == current_user.id
        or Permission.DOCUMENT_DELETE in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限删除此文档")
    
    # 删除物理文件
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        # 记录错误但不阻止删除数据库记录
        print(f"删除文件失败: {e}")
    
    document = crud.document.remove(db=db, id=document_id)
    return {"message": "文档删除成功"}


@router.get("/{document_id}/download")
def download_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    下载文档
    """
    from fastapi.responses import FileResponse
    
    document = crud.document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 权限检查
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or document.uploaded_by == current_user.id
        or Permission.DOCUMENT_READ in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限下载此文档")
    
    # 检查文件是否存在
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=document.file_path,
        filename=document.filename,
        media_type='application/octet-stream'
    )


@router.get("/project/{project_id}", response_model=List[schemas.Document])
def read_project_documents(
    *,
    db: Session = Depends(get_db),
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    获取项目的文档列表
    """
    # 检查项目是否存在
    project = crud.project.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查
    user_permissions = get_user_permissions(current_user)
    if not (
        current_user.is_superuser
        or project.owner_id == current_user.id
        or Permission.PROJECT_READ in user_permissions
    ):
        raise HTTPException(status_code=403, detail="没有权限访问此项目")
    
    documents = crud.document.get_by_project(
        db, project_id=project_id, skip=skip, limit=limit
    )
    return documents