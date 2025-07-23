from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "政府采购项目审查分析系统"
    PROJECT_DESCRIPTION: str = "Government Procurement Project Review and Analysis System"
    VERSION: str = "1.0.0"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 安全配置
    # openssl rand -hex 32
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    SQLALCHEMY_ECHO: bool = False  # 生产环境设为False
    
    # 初始超级用户
    FIRST_SUPERUSER: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: list = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".jpg", ".jpeg", ".png"]
    
    # OCR配置
    TESSERACT_CMD: Optional[str] = None  # Tesseract可执行文件路径
    OCR_LANGUAGE: str = "chi_sim+eng"  # 中文简体+英文
    
    # PaddleOCR配置
    PADDLEOCR_USE_ANGLE_CLS: bool = True  # 是否使用角度分类器
    PADDLEOCR_USE_GPU: bool = False  # 是否使用GPU
    PADDLEOCR_LANG: str = "ch"  # 语言设置
    
    # TrOCR配置
    TROCR_MODEL_NAME: str = "microsoft/trocr-base-handwritten"  # TrOCR模型名称
    TROCR_DEVICE: str = "cpu"  # 设备类型: cpu, cuda
    
    # OCR处理配置
    OCR_CONFIDENCE_THRESHOLD: float = 0.6  # OCR置信度阈值
    OCR_HANDWRITING_THRESHOLD: float = 0.3  # 手写检测阈值
    OCR_MAX_IMAGE_SIZE: int = 2048  # 最大图像尺寸
    OCR_BATCH_SIZE: int = 10  # 批处理大小
    
    # PDF处理配置
    PDF_DPI: int = 200  # PDF转图像DPI
    PDF_MAX_PAGES: int = 100  # 最大处理页数
    
    # 审查配置
    REVIEW_STAGES: list = ["前期", "采购", "合同", "实施", "验收", "后期"]
    
    # 环境配置
    ENVIRONMENT: str = "development"  # development, production, testing
    DEBUG: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()