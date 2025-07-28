import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 添加额外的字段
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # 添加请求相关信息（如果存在）
        for attr in ["request_id", "user_id", "ip_address", "user_agent"]:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """上下文过滤器，添加请求上下文信息"""

    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文信息到日志记录"""
        # 添加应用信息
        record.app_name = getattr(settings, "APP_NAME", "app")
        record.environment = getattr(settings, "ENVIRONMENT", "development")
        record.version = getattr(settings, "VERSION", "1.0.0")

        return True


class SecurityFilter(logging.Filter):
    """安全过滤器，过滤敏感信息"""

    SENSITIVE_PATTERNS = [
        "password",
        "token",
        "secret",
        "key",
        "auth",
        "credential",
        "session",
        "cookie",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感信息"""
        message = record.getMessage().lower()

        # 检查是否包含敏感信息
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # 标记为敏感日志
                record.sensitive = True
                break
        else:
            record.sensitive = False

        return True


class PerformanceFilter(logging.Filter):
    """性能过滤器，添加性能相关信息"""

    def filter(self, record: logging.LogRecord) -> bool:
        """添加性能信息"""
        # 添加时间戳
        record.timestamp_ms = int(record.created * 1000)

        return True


class LoggingConfig:
    """日志配置管理器"""

    def __init__(self):
        log_dir_path = getattr(settings, "LOG_DIR", "logs")
        self.log_dir = Path(log_dir_path)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件路径
        self.app_log_file = self.log_dir / "app.log"
        self.error_log_file = self.log_dir / "error.log"
        self.access_log_file = self.log_dir / "access.log"
        self.security_log_file = self.log_dir / "security.log"
        self.performance_log_file = self.log_dir / "performance.log"
        self.debug_log_file = self.log_dir / "debug.log"

    def setup_logging(self):
        """设置日志配置"""
        # 清除现有的处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 设置根日志级别
        log_level = getattr(settings, "LOG_LEVEL", "INFO")
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # 创建格式化器
        formatters = self._create_formatters()

        # 创建处理器
        handlers = self._create_handlers(formatters)

        # 配置不同的日志记录器
        self._configure_loggers(handlers)

        # 设置第三方库的日志级别
        self._configure_third_party_loggers()

        logging.info(f"日志系统已初始化，日志目录: {self.log_dir}")

    def _create_formatters(self) -> Dict[str, logging.Formatter]:
        """创建日志格式化器"""
        formatters = {}

        # 控制台格式化器
        environment = getattr(settings, "ENVIRONMENT", "development")
        if environment == "development":
            console_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            console_format = "%(asctime)s - %(levelname)s - %(message)s"

        formatters["console"] = logging.Formatter(
            console_format, datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 文件格式化器
        file_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
        )
        formatters["file"] = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")

        # JSON格式化器
        formatters["json"] = JSONFormatter()

        # 访问日志格式化器
        access_format = (
            '%(asctime)s - %(remote_addr)s - "%(method)s %(path)s '
            '%(protocol)s" '
            '%(status_code)s %(response_size)s "%(referer)s" "%(user_agent)s" '
            "%(response_time)s"
        )
        formatters["access"] = logging.Formatter(access_format)

        return formatters

    def _create_handlers(
        self, formatters: Dict[str, logging.Formatter]
    ) -> Dict[str, logging.Handler]:
        """创建日志处理器"""
        handlers = {}

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatters["console"])
        console_handler.addFilter(ContextFilter())
        console_handler.addFilter(SecurityFilter())
        handlers["console"] = console_handler

        # 应用日志文件处理器
        app_handler = logging.handlers.RotatingFileHandler(
            self.app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        app_handler.setFormatter(formatters["file"])
        app_handler.addFilter(ContextFilter())
        app_handler.addFilter(SecurityFilter())
        handlers["app"] = app_handler

        # 错误日志文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatters["file"])
        error_handler.addFilter(ContextFilter())
        handlers["error"] = error_handler

        # JSON日志处理器（用于结构化日志）
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.json",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        json_handler.setFormatter(formatters["json"])
        json_handler.addFilter(ContextFilter())
        json_handler.addFilter(PerformanceFilter())
        handlers["json"] = json_handler

        # 访问日志处理器
        access_handler = logging.handlers.RotatingFileHandler(
            self.access_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        access_handler.setFormatter(formatters["access"])
        handlers["access"] = access_handler

        # 安全日志处理器
        security_handler = logging.handlers.RotatingFileHandler(
            self.security_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        security_handler.setFormatter(formatters["file"])
        handlers["security"] = security_handler

        # 性能日志处理器
        performance_handler = logging.handlers.RotatingFileHandler(
            self.performance_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        performance_handler.setFormatter(formatters["json"])
        performance_handler.addFilter(PerformanceFilter())
        handlers["performance"] = performance_handler

        return handlers

    def _configure_loggers(self, handlers: Dict[str, logging.Handler]):
        """配置不同的日志记录器"""
        # 根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(handlers["console"])
        root_logger.addHandler(handlers["app"])
        root_logger.addHandler(handlers["error"])
        root_logger.addHandler(handlers["json"])

        # 应用日志记录器
        app_logger = logging.getLogger("app")
        app_logger.setLevel(logging.DEBUG)
        app_logger.propagate = False
        app_logger.addHandler(handlers["console"])
        app_logger.addHandler(handlers["app"])
        app_logger.addHandler(handlers["error"])
        app_logger.addHandler(handlers["json"])

        # 访问日志记录器
        access_logger = logging.getLogger("app.access")
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
        access_logger.addHandler(handlers["access"])

        # 安全日志记录器
        security_logger = logging.getLogger("app.security")
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        security_logger.addHandler(handlers["security"])
        security_logger.addHandler(handlers["console"])

        # 性能日志记录器
        performance_logger = logging.getLogger("app.performance")
        performance_logger.setLevel(logging.INFO)
        performance_logger.propagate = False
        performance_logger.addHandler(handlers["performance"])

    def _configure_third_party_loggers(self):
        """配置第三方库的日志级别"""
        # 设置第三方库的日志级别
        third_party_loggers = {
            "uvicorn": logging.INFO,
            "uvicorn.access": logging.WARNING,
            "uvicorn.error": logging.INFO,
            "fastapi": logging.INFO,
            "sqlalchemy": logging.WARNING,
            "sqlalchemy.engine": logging.WARNING,
            "sqlalchemy.pool": logging.WARNING,
            "alembic": logging.INFO,
            "httpx": logging.WARNING,
            "requests": logging.WARNING,
        }

        for logger_name, level in third_party_loggers.items():
            logging.getLogger(logger_name).setLevel(level)


# 全局日志配置实例
logging_config = LoggingConfig()


def setup_logging():
    """设置应用程序日志"""
    logging_config.setup_logging()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器"""
    if name:
        return logging.getLogger(f"app.{name}")
    return logging.getLogger("app")


def get_access_logger() -> logging.Logger:
    """获取访问日志记录器"""
    return logging.getLogger("app.access")


def get_security_logger() -> logging.Logger:
    """获取安全日志记录器"""
    return logging.getLogger("app.security")


def get_performance_logger() -> logging.Logger:
    """获取性能日志记录器"""
    return logging.getLogger("app.performance")
