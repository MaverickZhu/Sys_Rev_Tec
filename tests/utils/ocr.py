from sqlalchemy.orm import Session
from app import crud, models, schemas
from tests.utils.utils import random_lower_string, random_float, random_choice


def create_random_ocr_result(
    db: Session, *, document_id: int = None, processed_by: int
) -> models.OCRResult:
    """创建随机测试OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    text_content = f"Extracted text: {random_lower_string()}"
    confidence_score = random_float(0.7, 1.0)
    processing_time = random_float(0.5, 5.0)
    engine = random_choice(["tesseract", "paddleocr", "easyocr"])
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine=engine,
        language="chi_sim+eng",
        text_content=text_content,
        confidence_score=confidence_score,
        processing_time=processing_time,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result


def create_ocr_with_confidence(
    db: Session, *, document_id: int = None, processed_by: int, confidence_score: float
) -> models.OCRResult:
    """创建指定置信度的OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    text_content = f"Extracted text: {random_lower_string()}"
    processing_time = random_float(0.5, 5.0)
    engine = random_choice(["tesseract", "paddleocr", "easyocr"])
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine=engine,
        language="chi_sim+eng",
        text_content=text_content,
        confidence_score=confidence_score,
        processing_time=processing_time,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result


def create_ocr_with_text(
    db: Session, *, document_id: int = None, processed_by: int, text_content: str
) -> models.OCRResult:
    """创建指定文本的OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    confidence_score = random_float(0.7, 1.0)
    processing_time = random_float(0.5, 5.0)
    engine = random_choice(["tesseract", "paddleocr", "easyocr"])
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine=engine,
        language="chi_sim+eng",
        text_content=text_content,
        confidence_score=confidence_score,
        processing_time=processing_time,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result





def create_processing_ocr(
    db: Session, *, document_id: int, processed_by: int
) -> models.OCRResult:
    """创建处理中的OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine="tesseract",
        language="chi_sim+eng",
        text_content="",
        confidence_score=0.0,
        processing_time=0.0,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result


def create_failed_ocr(
    db: Session, *, document_id: int, processed_by: int
) -> models.OCRResult:
    """创建失败的OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine="tesseract",
        language="chi_sim+eng",
        text_content="",
        confidence_score=0.0,
        processing_time=0.0,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result


def create_multiple_ocr_results(
    db: Session, *, document_id: int, processed_by: int, count: int = 3
) -> list[models.OCRResult]:
    """创建多个测试OCR结果"""
    ocr_results = []
    for _ in range(count):
        ocr_result = create_random_ocr_result(
            db, document_id=document_id, processed_by=processed_by
        )
        ocr_results.append(ocr_result)
    return ocr_results


def create_high_confidence_ocr(
    db: Session, *, document_id: int, processed_by: int
) -> models.OCRResult:
    """创建高置信度OCR结果"""
    return create_ocr_with_confidence(
        db, document_id=document_id, processed_by=processed_by, confidence_score=0.95
    )


def create_low_confidence_ocr(
    db: Session, *, document_id: int, processed_by: int
) -> models.OCRResult:
    """创建低置信度OCR结果"""
    return create_ocr_with_confidence(
        db, document_id=document_id, processed_by=processed_by, confidence_score=0.65
    )


def create_ocr_with_engine(
    db: Session, *, document_id: int, processed_by: int, ocr_engine: str
) -> models.OCRResult:
    """创建指定引擎的OCR结果"""
    filename = f"{random_lower_string()}.pdf"
    text_content = f"Extracted text: {random_lower_string()}"
    confidence_score = random_float(0.7, 1.0)
    processing_time = random_float(0.5, 5.0)
    
    ocr_in = schemas.OCRResultCreate(
        filename=filename,
        engine=ocr_engine,
        language="chi_sim+eng",
        text_content=text_content,
        confidence_score=confidence_score,
        processing_time=processing_time,
        metadata="{}",
        document_id=document_id
    )
    
    ocr_result = crud.ocr_result.create_with_processor(
        db=db, obj_in=ocr_in, processor_id=processed_by
    )
    return ocr_result