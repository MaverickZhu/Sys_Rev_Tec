# Shared properties


from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentBase(BaseModel):

    filename: str
    document_type: str


# Properties to receive on document creation


class DocumentCreate(DocumentBase):

    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    document_category: str
    project_id: Optional[int] = None


# Properties to receive on document update


class DocumentUpdate(BaseModel):

    filename: Optional[str] = None
    document_type: Optional[str] = None
    project_id: Optional[int] = None


# Properties shared by models stored in DB


class DocumentInDBBase(DocumentBase):

    id: int
    file_path: str
    file_size: int
    uploaded_by: int
    project_id: Optional[int] = None
    upload_time: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    is_processed: bool = False
    processing_status: Optional[str] = None
    checksum: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Properties to return to client


class Document(DocumentInDBBase):

    pass


# Properties stored in DB


class DocumentInDB(DocumentInDBBase):

    pass
