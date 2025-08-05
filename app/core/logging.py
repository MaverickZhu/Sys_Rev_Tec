import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器，输出JSON格式的日志
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为JSON格式

        Args:
            record: 日志记录对象

        Returns:
            JSON格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外的字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # 添加请求ID（如果存在）
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # 添加用户ID（如果存在）
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_level: str = "INFO", structured: bool = False) -> logging.Logger:
    """
    设置应用程序日志配置

    Args:
        log_level: 日志级别
        structured: 是否使用结构化日志格式（JSON）

    Returns:
        配置好的logger实例
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 选择格式化器
    if structured:
        formatter = StructuredFormatter()
        console_formatter = StructuredFormatter()
    else:
        # 传统文本格式
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, date_format)
        console_formatter = formatter

    # 获取根logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的handlers
    logger.handlers.clear()

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件handler - 总日志
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 结构化日志文件handler（仅在结构化模式下）
    if structured:
        structured_handler = logging.FileHandler(
            log_dir / "app_structured.log", encoding="utf-8"
        )
        structured_handler.setFormatter(StructuredFormatter())
        logger.addHandler(structured_handler)

    # 错误文件handler
    error_handler = logging.FileHandler(log_dir / "error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# 创建全局logger实例
logger = setup_logging(
    getattr(settings, "LOG_LEVEL", "INFO"), getattr(settings, "LOG_STRUCTURED", False)
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取logger实例

    Args:
        name: logger名称，如果为None则返回根logger

    Returns:
        logger实例
    """
    if name:
        return logging.getLogger(f"app.{name}")
    return logger


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
    结构化日志适配器，用于添加上下文信息
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})

    def process(self, msg: Any, kwargs: Dict[str, Any]) -> tuple:
        """
        处理日志消息，添加额外的上下文信息

        Args:
            msg: 日志消息
            kwargs: 关键字参数

        Returns:
            处理后的消息和关键字参数
        """
        # 将extra字段添加到record中
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        # 合并适配器的extra和调用时的extra
        kwargs["extra"].update(self.extra)

        # 如果有额外字段，添加到record的extra_fields属性中
        if kwargs["extra"]:
            kwargs["extra"]["extra_fields"] = kwargs["extra"]

        return msg, kwargs


def get_structured_logger(
    name: Optional[str] = None, **context
) -> StructuredLoggerAdapter:
    """
    获取结构化日志记录器

    Args:
        name: logger名称
        **context: 上下文信息

    Returns:
        结构化日志适配器
    """
    base_logger = get_logger(name)
    return StructuredLoggerAdapter(base_logger, context)


def log_with_context(logger: logging.Logger, level: int, msg: str, **context):
    """
    使用上下文信息记录日志

    Args:
        logger: 日志记录器
        level: 日志级别
        msg: 日志消息
        **context: 上下文信息
    """
    extra = {"extra_fields": context} if context else {}
    logger.log(level, msg, extra=extra)


def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration: float,
    **extra,
):
    """
    记录API请求日志

    Args:
        logger: 日志记录器
        method: HTTP方法
        path: 请求路径
        status_code: 状态码
        duration: 请求耗时（秒）
        **extra: 额外信息
    """
    context = {
        "event_type": "api_request",
        "http_method": method,
        "path": path,
        "status_code": status_code,
        "duration_seconds": duration,
        **extra,
    }

    log_with_context(
        logger,
        logging.INFO,
        f"{method} {path} - {status_code} ({duration:.3f}s)",
        **context,
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    duration: float,
    affected_rows: int = None,
    **extra,
):
    """
    记录数据库操作日志

    Args:
        logger: 日志记录器
        operation: 操作类型（SELECT, INSERT, UPDATE, DELETE等）
        table: 表名
        duration: 操作耗时（秒）
        affected_rows: 影响的行数
        **extra: 额外信息
    """
    context = {
        "event_type": "database_operation",
        "operation": operation,
        "table": table,
        "duration_seconds": duration,
        **extra,
    }

    if affected_rows is not None:
        context["affected_rows"] = affected_rows

    log_with_context(
        logger, logging.INFO, f"DB {operation} on {table} ({duration:.3f}s)", **context
    )
