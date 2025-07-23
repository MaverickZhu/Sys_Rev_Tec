from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Shared properties
class OCRResultBase(BaseModel):
    filename: str
    engine: str
    language: str = "chi_sim+eng"
    text_content: str
    confidence_score: float = 0.0


# Properties to receive on OCR result creation
class OCRResultCreate(OCRResultBase):
    processing_time: float = 0.0
    word_count: int = 0
    metadata: Optional[str] = None
    document_id: Optional[int] = None


# Properties to receive on OCR result update
class OCRResultUpdate(BaseModel):
    text_content: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Optional[str] = None
    is_verified: Optional[bool] = None
    verified_text: Optional[str] = None


# Properties shared by models stored in DB
class OCRResultInDBBase(OCRResultBase):
    id: int
    processed_by: int
    processing_time: float = 0.0
    word_count: int = 0
    metadata: Optional[str] = None
    document_id: Optional[int] = None
    is_verified: bool = False
    verified_text: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Properties to return to client
class OCRResult(OCRResultInDBBase):
    pass


# Properties stored in DB
class OCRResultInDB(OCRResultInDBBase):
    pass