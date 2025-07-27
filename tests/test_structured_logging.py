import pytest
import json
import logging
from unittest.mock import patch, MagicMock
from io import StringIO

from app.core.logging import (
    StructuredFormatter,
    StructuredLoggerAdapter,
    setup_logging,
    get_structured_logger,
    log_with_context,
    log_api_request,
    log_database_operation
)


class TestStructuredFormatter:
    """测试结构化日志格式化器"""
    
    def test_basic_formatting(self):
        """测试基本的JSON格式化"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["line"] == 10
        assert "timestamp" in log_data
    
    def test_formatting_with_exception(self):
        """测试包含异常信息的格式化"""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error occurred"
        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]
    
    def test_formatting_with_extra_fields(self):
        """测试包含额外字段的格式化"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Test with extra",
            args=(),
            exc_info=None
        )
        
        # 添加额外字段
        record.extra_fields = {
            "user_id": "123",
            "action": "login"
        }
        record.request_id = "req-456"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["user_id"] == "123"
        assert log_data["action"] == "login"
        assert log_data["request_id"] == "req-456"


class TestStructuredLoggerAdapter:
    """测试结构化日志适配器"""
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        logger = logging.getLogger("test")
        adapter = StructuredLoggerAdapter(logger, {"service": "api"})
        
        assert adapter.logger == logger
        assert adapter.extra["service"] == "api"
    
    def test_process_method(self):
        """测试消息处理方法"""
        logger = logging.getLogger("test")
        adapter = StructuredLoggerAdapter(logger, {"service": "api"})
        
        msg, kwargs = adapter.process("Test message", {})
        
        assert msg == "Test message"
        assert "extra" in kwargs
        assert kwargs["extra"]["service"] == "api"
        assert "extra_fields" in kwargs["extra"]


class TestStructuredLogging:
    """测试结构化日志功能"""
    
    def test_setup_logging_structured(self):
        """测试结构化日志设置"""
        import tempfile
        import os
        import logging as log_module
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.core.logging.Path') as mock_path_class:
                # 创建一个真实的Path对象来模拟日志目录
                from pathlib import Path
                log_dir = Path(temp_dir) / "logs"
                log_dir.mkdir(exist_ok=True)
                
                # Mock Path类返回真实的路径
                mock_path_class.return_value = log_dir
                
                # Mock文件路径
                with patch('app.core.logging.logging.FileHandler') as mock_handler:
                    mock_handler.return_value = MagicMock()
                    
                    logger = setup_logging("INFO", structured=True)
                    
                    assert logger.name == "app"
                    assert logger.level == log_module.INFO
                    # 检查是否有控制台handler
                    console_handlers = [h for h in logger.handlers if isinstance(h, log_module.StreamHandler) and not hasattr(h, 'baseFilename')]
                    assert len(console_handlers) >= 1
    
    def test_setup_logging_traditional(self):
        """测试传统日志设置"""
        import tempfile
        import os
        import logging as log_module
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.core.logging.Path') as mock_path_class:
                # 创建一个真实的Path对象来模拟日志目录
                from pathlib import Path
                log_dir = Path(temp_dir) / "logs"
                log_dir.mkdir(exist_ok=True)
                
                # Mock Path类返回真实的路径
                mock_path_class.return_value = log_dir
                
                # Mock文件路径
                with patch('app.core.logging.logging.FileHandler') as mock_handler:
                    mock_handler.return_value = MagicMock()
                    
                    logger = setup_logging("DEBUG", structured=False)
                    
                    assert logger.name == "app"
                    assert logger.level == log_module.DEBUG
                    # 检查是否有控制台handler
                    console_handlers = [h for h in logger.handlers if isinstance(h, log_module.StreamHandler) and not hasattr(h, 'baseFilename')]
                    assert len(console_handlers) >= 1
    
    def test_get_structured_logger(self):
        """测试获取结构化日志记录器"""
        adapter = get_structured_logger("test_service", user_id="123")
        
        assert isinstance(adapter, StructuredLoggerAdapter)
        assert adapter.extra["user_id"] == "123"
        assert adapter.logger.name == "app.test_service"
    
    def test_log_with_context(self):
        """测试带上下文的日志记录"""
        # 创建一个内存中的日志处理器来捕获输出
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        
        logger = logging.getLogger("test_context")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        log_with_context(
            logger, 
            logging.INFO, 
            "Test message", 
            user_id="123", 
            action="test"
        )
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["message"] == "Test message"
        assert log_data["user_id"] == "123"
        assert log_data["action"] == "test"
    
    def test_log_api_request(self):
        """测试API请求日志记录"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        
        logger = logging.getLogger("test_api")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        log_api_request(
            logger,
            "GET",
            "/api/v1/documents",
            200,
            0.123,
            user_id="456"
        )
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["event_type"] == "api_request"
        assert log_data["http_method"] == "GET"
        assert log_data["path"] == "/api/v1/documents"
        assert log_data["status_code"] == 200
        assert log_data["duration_seconds"] == 0.123
        assert log_data["user_id"] == "456"
        assert "GET /api/v1/documents - 200" in log_data["message"]
    
    def test_log_database_operation(self):
        """测试数据库操作日志记录"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        
        logger = logging.getLogger("test_db")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        log_database_operation(
            logger,
            "SELECT",
            "documents",
            0.045,
            affected_rows=10,
            query_id="q123"
        )
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["event_type"] == "database_operation"
        assert log_data["operation"] == "SELECT"
        assert log_data["table"] == "documents"
        assert log_data["duration_seconds"] == 0.045
        assert log_data["affected_rows"] == 10
        assert log_data["query_id"] == "q123"
        assert "DB SELECT on documents" in log_data["message"]
    
    def test_log_database_operation_without_affected_rows(self):
        """测试不包含影响行数的数据库操作日志"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        
        logger = logging.getLogger("test_db2")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        log_database_operation(
            logger,
            "SELECT",
            "users",
            0.032
        )
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["event_type"] == "database_operation"
        assert log_data["operation"] == "SELECT"
        assert log_data["table"] == "users"
        assert log_data["duration_seconds"] == 0.032
        assert "affected_rows" not in log_data


class TestLoggingIntegration:
    """测试日志集成功能"""
    
    def test_json_serialization_safety(self):
        """测试JSON序列化的安全性"""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test with unicode: 测试中文",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "测试中文" in log_data["message"]
        # 确保JSON是有效的
        assert isinstance(log_data, dict)
    
    def test_large_context_handling(self):
        """测试大量上下文数据的处理"""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredFormatter())
        
        logger = logging.getLogger("test_large")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # 创建大量上下文数据
        large_context = {f"field_{i}": f"value_{i}" for i in range(100)}
        
        log_with_context(
            logger,
            logging.INFO,
            "Test with large context",
            **large_context
        )
        
        output = stream.getvalue()
        log_data = json.loads(output.strip())
        
        assert log_data["message"] == "Test with large context"
        assert log_data["field_0"] == "value_0"
        assert log_data["field_99"] == "value_99"
        assert len([k for k in log_data.keys() if k.startswith("field_")]) == 100