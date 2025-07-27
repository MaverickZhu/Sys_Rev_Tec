#!/usr/bin/env python3
"""
日志配置模块

提供统一的日志配置和管理功能，包括：
1. 结构化日志配置
2. 多种日志处理器
3. 日志轮转和归档
4. 性能监控日志
5. 安全审计日志
"""

import os
import sys
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

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
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # 添加请求相关信息（如果存在）
        for attr in ['request_id', 'user_id', 'ip_address', 'user_agent']:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)
        
        return json.dumps(log_entry, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """上下文过滤器，添加请求上下文信息"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加上下文信息到日志记录"""
        # 添加应用信息
        record.app_name = settings.APP_NAME
        record.environment = settings.ENVIRONMENT
        record.version = settings.VERSION
        
        return True

class SecurityFilter(logging.Filter):
    """安全过滤器，过滤敏感信息"""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'secret', 'key', 'auth',
        'credential', 'session', 'cookie'
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
        self.log_dir = Path(settings.LOG_DIR)
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
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
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
        if settings.ENVIRONMENT == "development":
            console_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            console_format = (
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        
        formatters['console'] = logging.Formatter(
            console_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件格式化器
        file_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
        )
        formatters['file'] = logging.Formatter(
            file_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # JSON格式化器
        formatters['json'] = JSONFormatter()
        
        # 访问日志格式化器
        access_format = (
            '%(asctime)s - %(remote_addr)s - "%(method)s %(path)s %(protocol)s" '
            '%(status_code)s %(response_size)s "%(referer)s" "%(user_agent)s" '
            '%(response_time)s'
        )
        formatters['access'] = logging.Formatter(access_format)
        
        return formatters
    
    def _create_handlers(self, formatters: Dict[str, logging.Formatter]) -> Dict[str, logging.Handler]:
        """创建日志处理器"""
        handlers = {}
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG)
        console_handler.setFormatter(formatters['console'])
        console_handler.addFilter(ContextFilter())
        handlers['console'] = console_handler
        
        # 应用日志文件处理器
        app_handler = logging.handlers.RotatingFileHandler(
            self.app_log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(formatters['json'] if settings.LOG_FORMAT == 'json' else formatters['file'])
        app_handler.addFilter(ContextFilter())
        app_handler.addFilter(SecurityFilter())
        handlers['app'] = app_handler
        
        # 错误日志文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatters['json'] if settings.LOG_FORMAT == 'json' else formatters['file'])
        error_handler.addFilter(ContextFilter())
        handlers['error'] = error_handler
        
        # 访问日志处理器
        access_handler = logging.handlers.RotatingFileHandler(
            self.access_log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(formatters['access'])
        handlers['access'] = access_handler
        
        # 安全日志处理器
        security_handler = logging.handlers.RotatingFileHandler(
            self.security_log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(formatters['json'] if settings.LOG_FORMAT == 'json' else formatters['file'])
        security_handler.addFilter(ContextFilter())
        handlers['security'] = security_handler
        
        # 性能日志处理器
        performance_handler = logging.handlers.RotatingFileHandler(
            self.performance_log_file,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(formatters['json'] if settings.LOG_FORMAT == 'json' else formatters['file'])
        performance_handler.addFilter(ContextFilter())
        performance_handler.addFilter(PerformanceFilter())
        handlers['performance'] = performance_handler
        
        # 调试日志处理器（仅开发环境）
        if settings.ENVIRONMENT == "development":
            debug_handler = logging.handlers.RotatingFileHandler(
                self.debug_log_file,
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(formatters['file'])
            debug_handler.addFilter(ContextFilter())
            handlers['debug'] = debug_handler
        
        return handlers
    
    def _configure_loggers(self, handlers: Dict[str, logging.Handler]):
        """配置不同的日志记录器"""
        # 根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(handlers['console'])
        root_logger.addHandler(handlers['app'])
        root_logger.addHandler(handlers['error'])
        
        if settings.ENVIRONMENT == "development" and 'debug' in handlers:
            root_logger.addHandler(handlers['debug'])
        
        # 应用日志记录器
        app_logger = logging.getLogger('app')
        app_logger.setLevel(logging.INFO)
        app_logger.propagate = False
        app_logger.addHandler(handlers['console'])
        app_logger.addHandler(handlers['app'])
        app_logger.addHandler(handlers['error'])
        
        # 访问日志记录器
        access_logger = logging.getLogger('access')
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
        access_logger.addHandler(handlers['access'])
        
        # 安全日志记录器
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.WARNING)
        security_logger.propagate = False
        security_logger.addHandler(handlers['security'])
        security_logger.addHandler(handlers['console'])
        
        # 性能日志记录器
        performance_logger = logging.getLogger('performance')
        performance_logger.setLevel(logging.INFO)
        performance_logger.propagate = False
        performance_logger.addHandler(handlers['performance'])
        
        # 数据库日志记录器
        db_logger = logging.getLogger('sqlalchemy')
        db_logger.setLevel(logging.WARNING if settings.ENVIRONMENT == "production" else logging.INFO)
        
        # OCR日志记录器
        ocr_logger = logging.getLogger('ocr')
        ocr_logger.setLevel(logging.INFO)
        ocr_logger.propagate = True
    
    def _configure_third_party_loggers(self):
        """配置第三方库的日志级别"""
        third_party_loggers = {
            'uvicorn': logging.INFO,
            'uvicorn.access': logging.INFO,
            'uvicorn.error': logging.INFO,
            'fastapi': logging.INFO,
            'sqlalchemy.engine': logging.WARNING if settings.ENVIRONMENT == "production" else logging.INFO,
            'sqlalchemy.pool': logging.WARNING,
            'alembic': logging.INFO,
            'httpx': logging.WARNING,
            'requests': logging.WARNING,
            'urllib3': logging.WARNING,
            'PIL': logging.WARNING,
            'matplotlib': logging.WARNING,
        }
        
        for logger_name, level in third_party_loggers.items():
            logging.getLogger(logger_name).setLevel(level)

class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，添加上下文信息"""
    
    def process(self, msg, kwargs):
        """处理日志消息，添加额外信息"""
        # 添加额外字段到日志记录
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        
        return msg, kwargs

def get_logger(name: str, **context) -> LoggerAdapter:
    """获取带上下文的日志记录器"""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)

def log_request(request_id: str, method: str, path: str, ip_address: str, 
                user_agent: str, user_id: Optional[str] = None):
    """记录HTTP请求"""
    access_logger = logging.getLogger('access')
    access_logger.info(
        "HTTP Request",
        extra={
            'request_id': request_id,
            'method': method,
            'path': path,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'user_id': user_id,
            'event_type': 'http_request'
        }
    )

def log_security_event(event_type: str, description: str, ip_address: str, 
                      user_id: Optional[str] = None, **extra_data):
    """记录安全事件"""
    security_logger = logging.getLogger('security')
    security_logger.warning(
        f"Security Event: {event_type} - {description}",
        extra={
            'event_type': event_type,
            'description': description,
            'ip_address': ip_address,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            **extra_data
        }
    )

def log_performance(operation: str, duration: float, **extra_data):
    """记录性能指标"""
    performance_logger = logging.getLogger('performance')
    performance_logger.info(
        f"Performance: {operation} took {duration:.3f}s",
        extra={
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat(),
            **extra_data
        }
    )

def setup_logging():
    """设置日志系统"""
    config = LoggingConfig()
    config.setup_logging()

if __name__ == "__main__":
    # 测试日志配置
    setup_logging()
    
    # 测试不同类型的日志
    logger = get_logger(__name__, component="test")
    
    logger.debug("这是一个调试消息")
    logger.info("这是一个信息消息")
    logger.warning("这是一个警告消息")
    logger.error("这是一个错误消息")
    
    # 测试访问日志
    log_request(
        request_id="test-123",
        method="GET",
        path="/api/test",
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        user_id="user123"
    )
    
    # 测试安全日志
    log_security_event(
        event_type="login_attempt",
        description="Failed login attempt",
        ip_address="192.168.1.100",
        user_id="user456",
        attempts=3
    )
    
    # 测试性能日志
    log_performance(
        operation="database_query",
        duration=0.125,
        query_type="SELECT",
        table="users"
    )
    
    print("日志测试完成，请检查日志文件")