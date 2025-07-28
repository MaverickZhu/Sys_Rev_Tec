"""
AI服务配置管理
管理环境变量和应用配置
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")

    # 服务配置
    AI_SERVICE_HOST: str = Field(default="0.0.0.0", env="AI_SERVICE_HOST")
    AI_SERVICE_PORT: int = Field(default=8001, env="AI_SERVICE_PORT")
    AI_SERVICE_WORKERS: int = Field(default=1, env="AI_SERVICE_WORKERS")

    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql://postgres:sys_rev_password@localhost:5432/sys_rev_tech",
        env="DATABASE_URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

    # Redis配置
    REDIS_URL: str = Field(default="redis://:redis_password@localhost:6379/0", env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")

    # Ollama配置
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434", env="OLLAMA_BASE_URL"
    )
    OLLAMA_TIMEOUT: int = Field(default=30, env="OLLAMA_TIMEOUT")
    OLLAMA_MAX_RETRIES: int = Field(default=3, env="OLLAMA_MAX_RETRIES")

    # AI模型配置
    AI_EMBEDDING_MODEL: str = Field(default="bge-m3:latest", env="AI_EMBEDDING_MODEL")
    AI_CHAT_MODEL: str = Field(default="deepseek-r1:8b", env="AI_CHAT_MODEL")
    AI_MODEL_PRELOAD: bool = Field(default=True, env="AI_MODEL_PRELOAD")
    AI_EMBEDDING_DIMENSION: int = Field(default=1024, env="AI_EMBEDDING_DIMENSION")

    # Azure OpenAI配置（备用）
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(
        default=None, env="AZURE_OPENAI_ENDPOINT"
    )
    AZURE_OPENAI_API_KEY: Optional[str] = Field(
        default=None, env="AZURE_OPENAI_API_KEY"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION"
    )
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = Field(
        default=None, env="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: Optional[str] = Field(
        default=None, env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    # 文档处理配置
    MAX_DOCUMENT_SIZE: int = Field(default=10485760, env="MAX_DOCUMENT_SIZE")  # 10MB
    MAX_CHUNK_SIZE: int = Field(default=1000, env="MAX_CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    SUPPORTED_FILE_TYPES: List[str] = Field(
        default=["txt", "md", "pdf", "docx", "html"], env="SUPPORTED_FILE_TYPES"
    )

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1小时
    VECTOR_CACHE_TTL: int = Field(default=86400, env="VECTOR_CACHE_TTL")  # 24小时
    SEARCH_CACHE_TTL: int = Field(default=1800, env="SEARCH_CACHE_TTL")  # 30分钟

    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    BATCH_SIZE: int = Field(default=10, env="BATCH_SIZE")
    MAX_SEARCH_RESULTS: int = Field(default=50, env="MAX_SEARCH_RESULTS")

    # 向量搜索配置
    VECTOR_SEARCH_K: int = Field(default=10, env="VECTOR_SEARCH_K")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    HYBRID_SEARCH_ALPHA: float = Field(default=0.7, env="HYBRID_SEARCH_ALPHA")

    # 监控配置
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # 安全配置
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"], env="ALLOWED_HOSTS"
    )
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    # 特性开关
    ENABLE_VECTOR_SEARCH: bool = Field(default=True, env="ENABLE_VECTOR_SEARCH")
    ENABLE_SEMANTIC_SEARCH: bool = Field(default=True, env="ENABLE_SEMANTIC_SEARCH")
    ENABLE_HYBRID_SEARCH: bool = Field(default=True, env="ENABLE_HYBRID_SEARCH")
    ENABLE_QA_GENERATION: bool = Field(default=True, env="ENABLE_QA_GENERATION")
    ENABLE_DOCUMENT_SUMMARIZATION: bool = Field(
        default=True, env="ENABLE_DOCUMENT_SUMMARIZATION"
    )
    ENABLE_AUTO_TAGGING: bool = Field(default=True, env="ENABLE_AUTO_TAGGING")

    # 开发和调试
    ENABLE_QUERY_LOGGING: bool = Field(default=False, env="ENABLE_QUERY_LOGGING")
    ENABLE_PERFORMANCE_PROFILING: bool = Field(
        default=False, env="ENABLE_PERFORMANCE_PROFILING"
    )
    MOCK_AI_RESPONSES: bool = Field(default=False, env="MOCK_AI_RESPONSES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """解析允许的主机"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("SUPPORTED_FILE_TYPES", pre=True)
    def parse_file_types(cls, v):
        """解析支持的文件类型"""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("SIMILARITY_THRESHOLD")
    def validate_similarity_threshold(cls, v):
        """验证相似度阈值"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0.0 and 1.0")
        return v

    @validator("HYBRID_SEARCH_ALPHA")
    def validate_hybrid_search_alpha(cls, v):
        """验证混合搜索权重"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("HYBRID_SEARCH_ALPHA must be between 0.0 and 1.0")
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]

    @property
    def database_config(self) -> dict:
        """数据库配置"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
        }

    @property
    def redis_config(self) -> dict:
        """Redis配置"""
        return {
            "url": self.REDIS_URL,
            "pool_size": self.REDIS_POOL_SIZE,
            "timeout": self.REDIS_TIMEOUT,
        }

    @property
    def ollama_config(self) -> dict:
        """Ollama配置"""
        return {
            "base_url": self.OLLAMA_BASE_URL,
            "timeout": self.OLLAMA_TIMEOUT,
            "max_retries": self.OLLAMA_MAX_RETRIES,
        }

    @property
    def azure_openai_config(self) -> dict:
        """Azure OpenAI配置"""
        return {
            "endpoint": self.AZURE_OPENAI_ENDPOINT,
            "api_key": self.AZURE_OPENAI_API_KEY,
            "api_version": self.AZURE_OPENAI_API_VERSION,
            "deployment_name": self.AZURE_OPENAI_DEPLOYMENT_NAME,
            "embedding_deployment": self.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        }

    @property
    def has_azure_openai(self) -> bool:
        """是否配置了Azure OpenAI"""
        return bool(
            self.AZURE_OPENAI_ENDPOINT
            and self.AZURE_OPENAI_API_KEY
            and self.AZURE_OPENAI_DEPLOYMENT_NAME
        )

    def get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)

    def get_model_config(self, model_type: str) -> dict:
        """获取模型配置"""
        if model_type == "embedding":
            return {
                "model": self.AI_EMBEDDING_MODEL,
                "dimension": self.AI_EMBEDDING_DIMENSION,
            }
        elif model_type == "chat":
            return {"model": self.AI_CHAT_MODEL}
        else:
            raise ValueError(f"Unknown model type: {model_type}")


@lru_cache
def get_settings() -> Settings:
    """获取应用配置（单例模式）"""
    return Settings()


# 导出常用配置
settings = get_settings()


# 配置验证
def validate_config():
    """验证配置"""
    errors = []

    # 检查必要的配置
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
        errors.append("SECRET_KEY must be set to a secure value")

    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL must be set")

    if not settings.REDIS_URL:
        errors.append("REDIS_URL must be set")

    if not settings.OLLAMA_BASE_URL:
        errors.append("OLLAMA_BASE_URL must be set")

    # 检查模型配置
    if not settings.AI_EMBEDDING_MODEL:
        errors.append("AI_EMBEDDING_MODEL must be set")

    if not settings.AI_CHAT_MODEL:
        errors.append("AI_CHAT_MODEL must be set")

    # 检查端口冲突
    if settings.AI_SERVICE_PORT == settings.PROMETHEUS_PORT:
        errors.append("AI_SERVICE_PORT and PROMETHEUS_PORT cannot be the same")

    if errors:
        raise ValueError(
            "Configuration errors:\n" + "\n".join(f"- {error}" for error in errors)
        )


if __name__ == "__main__":
    # 验证配置
    try:
        validate_config()
        print("✅ 配置验证通过")

        # 打印关键配置信息
        print(f"环境: {settings.ENVIRONMENT}")
        print(f"调试模式: {settings.DEBUG}")
        print(f"AI服务端口: {settings.AI_SERVICE_PORT}")
        print(f"嵌入模型: {settings.AI_EMBEDDING_MODEL}")
        print(f"聊天模型: {settings.AI_CHAT_MODEL}")
        print(f"Azure OpenAI: {'已配置' if settings.has_azure_openai else '未配置'}")

    except ValueError as e:
        print(f"❌ 配置验证失败: {e}")
        exit(1)
