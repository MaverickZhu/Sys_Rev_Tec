import logging
import logging.handlers
from pathlib import Path
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用程序配置"""

    # 基础配置
    APP_NAME: str = "系统审查技术平台"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "基于AI的系统审查技术平台"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here"
    API_PREFIX: str = "/api/v1"
    API_V1_STR: str = "/api/v1"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10  # MB
    ALLOWED_FILE_TYPES: str = ".txt,.pdf,.doc,.docx,.png,.jpg,.jpeg"

    # OCR配置
    OCR_PROVIDER: str = "tesseract"  # tesseract, azure, aws, google
    OCR_API_KEY: Optional[str] = None
    OCR_LANGUAGE: str = "chi_sim+eng"
    OCR_CONFIDENCE_THRESHOLD: float = 0.6

    # Tesseract配置
    TESSERACT_CMD: Optional[str] = None

    # PaddleOCR配置
    PADDLEOCR_USE_ANGLE_CLS: bool = True
    PADDLEOCR_USE_GPU: bool = False
    PADDLEOCR_LANG: str = "ch"

    # TrOCR配置
    TROCR_MODEL_NAME: str = "microsoft/trocr-base-handwritten"
    TROCR_DEVICE: str = "cpu"

    # OCR处理配置
    OCR_HANDWRITING_THRESHOLD: float = 0.3
    OCR_MAX_IMAGE_SIZE: int = 2048
    OCR_BATCH_SIZE: int = 10

    # PDF处理配置
    PDF_DPI: int = 200
    PDF_MAX_PAGES: int = 100

    # 审查配置
    REVIEW_STAGES: list = ["前期", "采购", "合同", "实施", "验收", "后期"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_FILE: str = "./logs/app.log"
    LOG_MAX_SIZE: int = 10  # MB
    LOG_BACKUP_COUNT: int = 5
    LOG_STRUCTURED: bool = False  # 是否使用结构化日志（JSON格式）
    LOG_INCLUDE_REQUEST_ID: bool = True  # 是否在日志中包含请求ID

    # 错误追踪配置
    ERROR_TRACKING_ENABLED: bool = True
    ERROR_TRACKING_TRACK_4XX: bool = False
    ERROR_TRACKING_CLEANUP_DAYS: int = 7

    # 报警配置
    ALERT_ENABLED: bool = True
    ALERT_EMAIL: str = "admin@example.com"
    ALERT_WEBHOOK_URL: Optional[str] = None

    # SMTP配置（用于邮件报警）
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_FROM: str = "noreply@example.com"

    # 缓存配置
    CACHE_ENABLED: bool = True
    REDIS_URL: Optional[str] = None
    CACHE_EXPIRE_TIME: int = 3600  # 秒

    # CORS配置
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000"
    )
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    ALLOWED_HEADERS: str = "*"

    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"
    HEALTH_CHECK_PATH: str = "/health"

    # 邮件配置
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: Optional[str] = None

    # AI集成配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Azure OpenAI配置
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"

    # Ollama配置
    OLLAMA_BASE_URL: str = "http://localhost:11435"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3:latest"

    # 向量数据库配置
    VECTOR_DB_URL: Optional[str] = None
    VECTOR_COLLECTION_NAME: str = "documents"
    DEFAULT_VECTOR_STORE: str = "memory"  # memory, chroma, pinecone, weaviate

    # Chroma配置
    CHROMA_HOST: Optional[str] = None
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_NAME: str = "documents"

    # Pinecone配置
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "documents"

    # Weaviate配置
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    WEAVIATE_CLASS_NAME: str = "Document"

    # 开发调试配置
    SHOW_ERROR_DETAILS: bool = True
    ENABLE_DOCS: bool = True

    # 性能配置
    WORKERS: int = 1
    THREADS: int = 1
    REQUEST_TIMEOUT: int = 30
    KEEP_ALIVE_TIMEOUT: int = 5

    @property
    def allowed_origins_list(self) -> List[str]:
        """将CORS允许的源转换为列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_file_types_list(self) -> List[str]:
        """将允许的文件类型转换为列表"""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]

    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"

    def setup_logging(self) -> None:
        """配置日志系统"""
        # 创建日志目录
        log_dir = Path(self.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 配置日志格式
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # 配置根日志记录器
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format=log_format,
            handlers=[
                logging.StreamHandler(),  # 控制台输出
                logging.handlers.RotatingFileHandler(
                    self.LOG_FILE,
                    maxBytes=self.LOG_MAX_SIZE * 1024 * 1024,  # 转换为字节
                    backupCount=self.LOG_BACKUP_COUNT,
                    encoding="utf-8",
                ),
            ],
        )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
