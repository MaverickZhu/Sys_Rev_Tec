# -*- coding: utf-8 -*-
"""
响应模型定义
"""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": 200,
                "message": "success",
                "data": None
            }
        }
    }

class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: int
    message: str
    detail: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code": 400,
                "message": "Bad Request",
                "detail": "Invalid input parameters"
            }
        }
    }

class OCRResponse(BaseModel):
    """OCR响应模型"""
    text: str
    confidence: float
    engine: str
    is_handwritten: bool
    details: Optional[dict] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "识别的文本内容",
                "confidence": 0.95,
                "engine": "paddleocr",
                "is_handwritten": False,
                "details": {}
            }
        }
    }

class OCRStatusResponse(BaseModel):
    """OCR状态响应模型"""
    document_id: int
    is_ocr_processed: bool
    ocr_engine: Optional[str] = None
    ocr_confidence: Optional[float] = None
    is_handwritten: Optional[bool] = None
    processed_at: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "document_id": 1,
                "is_ocr_processed": True,
                "ocr_engine": "paddleocr",
                "ocr_confidence": 0.95,
                "is_handwritten": False,
                "processed_at": "2024-01-01T12:00:00"
            }
        }
    }

class OCRStatsResponse(BaseModel):
    """OCR统计响应模型"""
    total_documents: int
    processed_documents: int
    pending_documents: int
    engine_stats: dict
    avg_confidence: float
    handwritten_count: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_documents": 100,
                "processed_documents": 85,
                "pending_documents": 15,
                "engine_stats": {
                    "paddleocr": 60,
                    "trocr": 20,
                    "tesseract": 5
                },
                "avg_confidence": 0.87,
                "handwritten_count": 20
            }
        }
    }