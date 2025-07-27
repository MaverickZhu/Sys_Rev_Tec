from sqlalchemy.orm import Session
from app import crud, models, schemas
from tests.utils.utils import random_lower_string, random_choice


def create_random_document(
    db: Session, *, owner_id: int, project_id: int = None
) -> models.Document:
    """创建随机测试文档"""
    filename = f"{random_lower_string()}.pdf"
    file_path = f"/uploads/{filename}"
    
    document_in = schemas.DocumentCreate(
        filename=filename,
        original_filename=filename,
        document_type="pdf",
        file_path=file_path,
        file_size=1024,
        file_type="pdf",
        document_category="test",
        project_id=project_id
    )
    
    document = crud.document.create_with_uploader(
        db=db, obj_in=document_in, owner_id=owner_id
    )
    return document


def create_document_with_status(
    db: Session, *, owner_id: int, project_id: int = None, processing_status: str = "pending"
) -> models.Document:
    """创建指定状态的文档"""
    filename = f"{random_lower_string()}.pdf"
    file_path = f"/uploads/{filename}"
    
    document_in = schemas.DocumentCreate(
        filename=filename,
        original_filename=filename,
        document_type="pdf",
        file_path=file_path,
        file_size=1024,
        file_type="pdf",
        document_category="test",
        project_id=project_id
    )
    
    document = crud.document.create_with_uploader(
        db=db, obj_in=document_in, owner_id=owner_id
    )
    # 更新处理状态
    if processing_status != "pending":
        document.processing_status = processing_status
        db.commit()
        db.refresh(document)
    return document


def create_document_with_filename(
    db: Session, *, owner_id: int, project_id: int = None, filename: str
) -> models.Document:
    """创建指定文件名的文档"""
    file_path = f"/uploads/{filename}"
    
    document_in = schemas.DocumentCreate(
        filename=filename,
        original_filename=filename,
        document_type="pdf",
        file_path=file_path,
        file_size=1024,
        file_type="pdf",
        document_category="test",
        project_id=project_id
    )
    
    document = crud.document.create_with_uploader(
        db=db, obj_in=document_in, owner_id=owner_id
    )
    return document


def create_processing_document(
    db: Session, *, owner_id: int, project_id: int = None
) -> models.Document:
    """创建处理中的文档"""
    return create_document_with_status(
        db, owner_id=owner_id, project_id=project_id, processing_status="processing"
    )


def create_completed_document(
    db: Session, *, owner_id: int, project_id: int = None
) -> models.Document:
    """创建已完成的文档"""
    return create_document_with_status(
        db, owner_id=owner_id, project_id=project_id, processing_status="completed"
    )


def create_multiple_documents(
    db: Session, *, owner_id: int, project_id: int = None, count: int = 3
) -> list[models.Document]:
    """创建多个测试文档"""
    documents = []
    for _ in range(count):
        document = create_random_document(
            db, owner_id=owner_id, project_id=project_id
        )
        documents.append(document)
    return documents


def create_document_with_file_type(
    db: Session, *, owner_id: int, project_id: int = None, file_type: str = "pdf"
) -> models.Document:
    """创建指定文件类型的文档"""
    filename = f"{random_lower_string()}.{file_type}"
    file_path = f"/uploads/{filename}"
    
    document_in = schemas.DocumentCreate(
        filename=filename,
        original_filename=filename,
        document_type=file_type,
        file_path=file_path,
        file_size=1024,
        file_type=file_type,
        document_category="test",
        project_id=project_id
    )
    
    document = crud.document.create_with_uploader(
        db=db, obj_in=document_in, owner_id=owner_id
    )
    return document