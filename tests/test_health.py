import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import psutil
import time

from app.main import app
from app.core.config import settings

client = TestClient(app)


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_health_check_success(self):
        """测试基础健康检查端点"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "data" in data
        assert "status" in data["data"]
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]
        assert "uptime_seconds" in data["data"]
        assert "version" in data["data"]
        assert "environment" in data["data"]
        assert "system" in data["data"]
        
        # 检查系统信息
        system_info = data["data"]["system"]
        assert "cpu_percent" in system_info
        assert "memory_percent" in system_info
        assert "memory_available_mb" in system_info
        assert "disk_percent" in system_info
        assert "disk_free_gb" in system_info
    
    @patch('psutil.cpu_percent')
    def test_health_check_with_mocked_system_info(self, mock_cpu):
        """测试健康检查端点的系统信息获取"""
        mock_cpu.return_value = 25.5
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["system"]["cpu_percent"] == 25.5
    
    @patch('psutil.cpu_percent', side_effect=Exception("System error"))
    def test_health_check_system_error(self, mock_cpu):
        """测试健康检查端点在系统错误时的处理"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 503
        data = response.json()
        assert "Health check failed" in data["error"]["message"]
    
    def test_readiness_check_success(self):
        """测试就绪检查端点"""
        response = client.get("/api/v1/ready")
        
        # 可能返回200或503，取决于数据库连接状态
        assert response.status_code in [200, 503]
        data = response.json()
        
        if response.status_code == 200:
            assert data["code"] == 200
            assert "data" in data
            assert "status" in data["data"]
            assert data["data"]["status"] == "ready"
            assert "checks" in data["data"]
            
            # 检查各项检查结果
            checks = data["data"]["checks"]
            assert "database" in checks
            assert "upload_directory" in checks
            assert "log_directory" in checks
            assert "memory" in checks
            assert "disk_space" in checks
        else:
            # 服务不可用的情况
            assert "error" in data
    
    @patch('sqlalchemy.orm.Session.execute')
    def test_readiness_check_database_failure(self, mock_execute):
        """测试就绪检查在数据库连接失败时的处理"""
        # 模拟数据库连接失败
        mock_execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert "Application is not ready" in data["error"]["message"]
    
    @patch('os.path.exists', return_value=False)
    def test_readiness_check_directory_failure(self, mock_exists):
        """测试就绪检查在目录不存在时的处理"""
        response = client.get("/api/v1/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert "Application is not ready" in data["error"]["message"]
    
    @patch('psutil.virtual_memory')
    def test_readiness_check_high_memory_usage(self, mock_memory):
        """测试就绪检查在高内存使用时的处理"""
        # 模拟高内存使用
        mock_memory_info = MagicMock()
        mock_memory_info.percent = 95.0
        mock_memory.return_value = mock_memory_info
        
        response = client.get("/api/v1/ready")
        
        # 高内存使用不会导致服务不可用，只是警告
        data = response.json()
        if response.status_code == 200:
            checks = data["data"]["checks"]
            assert checks["memory"]["status"] == "warning"
    
    def test_metrics_endpoint_success(self):
        """测试指标端点"""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "data" in data
        assert "timestamp" in data["data"]
        assert "system" in data["data"]
        assert "process" in data["data"]
        assert "application" in data["data"]
        
        # 检查系统指标
        system_metrics = data["data"]["system"]
        assert "cpu_percent" in system_metrics
        assert "cpu_count" in system_metrics
        assert "memory_total_mb" in system_metrics
        assert "memory_available_mb" in system_metrics
        assert "memory_percent" in system_metrics
        assert "disk_total_gb" in system_metrics
        assert "disk_free_gb" in system_metrics
        assert "disk_percent" in system_metrics
        
        # 检查进程指标
        process_metrics = data["data"]["process"]
        assert "pid" in process_metrics
        assert "memory_rss_mb" in process_metrics
        assert "memory_vms_mb" in process_metrics
        assert "cpu_percent" in process_metrics
        assert "num_threads" in process_metrics
        assert "create_time" in process_metrics
        assert "uptime_seconds" in process_metrics
        
        # 检查应用程序指标
        app_metrics = data["data"]["application"]
        assert "version" in app_metrics
        assert "environment" in app_metrics
        assert "debug" in app_metrics
    
    @patch('psutil.Process')
    def test_metrics_endpoint_process_error(self, mock_process):
        """测试指标端点在进程信息获取失败时的处理"""
        mock_process.side_effect = Exception("Process error")
        
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve metrics" in data["error"]["message"]
    
    def test_health_endpoints_no_auth_required(self):
        """测试健康检查端点不需要认证"""
        # 这些端点应该在没有认证的情况下也能访问
        endpoints = ["/api/v1/health", "/api/v1/ready", "/api/v1/metrics"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # 不应该返回401未授权错误
            assert response.status_code != 401
    
    def test_health_response_format(self):
        """测试健康检查响应格式"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式符合ResponseModel
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["code"], int)
        assert isinstance(data["message"], str)
        assert isinstance(data["data"], dict)
    
    def test_metrics_response_format(self):
        """测试指标端点响应格式"""
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应格式符合ResponseModel
        assert "code" in data
        assert "message" in data
        assert "data" in data
        assert isinstance(data["code"], int)
        assert isinstance(data["message"], str)
        assert isinstance(data["data"], dict)
        
        # 检查数据类型
        metrics_data = data["data"]
        assert isinstance(metrics_data["timestamp"], int)
        assert isinstance(metrics_data["system"], dict)
        assert isinstance(metrics_data["process"], dict)
        assert isinstance(metrics_data["application"], dict)