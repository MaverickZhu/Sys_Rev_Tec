"""
AI服务日志配置
配置和管理应用日志
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from ai_service.config import get_settings

settings = get_settings()


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None):
    """设置日志配置"""
    # 获取日志级别
    level = log_level or settings.LOG_LEVEL
    log_level_num = getattr(logging, level.upper(), logging.INFO)

    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_num)

    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建格式器
    formatter = logging.Formatter(fmt=settings.LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_num)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器
    file_path = log_file or settings.LOG_FILE
    if file_path:
        # 确保日志目录存在
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level_num)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # 设置第三方库的日志级别
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # 如果是开发环境，设置更详细的日志
    if settings.is_development:
        logging.getLogger("ai_service").setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)
    logger.info(f"日志系统初始化完成 - 级别: {level}")
    if file_path:
        logger.info(f"日志文件: {file_path}")


class StructuredLogger:
    """结构化日志器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_request(
        self, method: str, path: str, status_code: int, duration_ms: float, **kwargs
    ):
        """记录请求日志"""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(
            f"REQUEST {method} {path} - {status_code} - {duration_ms:.2f}ms {extra_info}"
        )

    def log_vectorization(
        self, document_id: str, chunks: int, model: str, duration_ms: float, **kwargs
    ):
        """记录向量化日志"""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(
            f"VECTORIZATION doc={document_id} chunks={chunks} model={model} duration={duration_ms:.2f}ms {extra_info}"
        )

    def log_search(
        self, query: str, search_type: str, results: int, duration_ms: float, **kwargs
    ):
        """记录搜索日志"""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        query_preview = query[:50] + "..." if len(query) > 50 else query
        self.logger.info(
            f"SEARCH type={search_type} query='{query_preview}' results={results} duration={duration_ms:.2f}ms {extra_info}"
        )

    def log_error(self, operation: str, error: Exception, **kwargs):
        """记录错误日志"""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.error(
            f"ERROR {operation} - {type(error).__name__}: {str(error)} {extra_info}",
            exc_info=True,
        )

    def log_performance(self, operation: str, duration_ms: float, **metrics):
        """记录性能日志"""
        metrics_info = " ".join(f"{k}={v}" for k, v in metrics.items())
        self.logger.info(
            f"PERFORMANCE {operation} duration={duration_ms:.2f}ms {metrics_info}"
        )


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志器"""
    return StructuredLogger(name)


# 创建默认日志器
default_logger = get_logger("ai_service")
