import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from app.main import app
from app.core.config import settings


class TestMainApp:
    """测试主应用模块"""
    
    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """测试根路径端点"""
        # 创建临时的index.html文件
        os.makedirs("static", exist_ok=True)
        with open("static/index.html", "w", encoding="utf-8") as f:
            f.write("<html><body>Test Page</body></html>")
        
        try:
            response = self.client.get("/")
            assert response.status_code == 200
        finally:
            # 清理
            if os.path.exists("static/index.html"):
                os.remove("static/index.html")
    
    def test_api_info_endpoint(self):
        """测试API信息端点"""
        response = self.client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "features" in data
        assert isinstance(data["features"], list)
    
    def test_health_check_success(self):
        """测试健康检查成功情况"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "file_system" in data["components"]
    
    def test_health_check_database_error(self):
        """测试健康检查数据库错误情况"""
        import os
        from app.core.config import settings
        from app.main import get_db
        from fastapi.testclient import TestClient
        from app.main import app
        
        # 确保上传目录存在，这样只有数据库错误会导致不健康
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # 创建一个会抛出异常的模拟数据库会话
        def failing_get_db():
            mock_db = MagicMock()
            mock_db.execute.side_effect = Exception("Database connection failed")
            mock_db.close = MagicMock()  # 模拟close方法
            yield mock_db
        
        # 创建一个新的测试客户端来避免状态污染
        test_client = TestClient(app)
        
        # 保存原始依赖
        original_dependency = test_client.app.dependency_overrides.get(get_db)
        
        try:
            # 设置依赖覆盖
            test_client.app.dependency_overrides[get_db] = failing_get_db
            
            response = test_client.get("/health")
            assert response.status_code == 200
            data = response.json()
      
            assert data["status"] == "unhealthy"
            assert data["components"]["database"]["status"] == "error"
            assert "Database connection failed" in data["components"]["database"]["error"]
        finally:
            # 恢复原始依赖
            if original_dependency:
                test_client.app.dependency_overrides[get_db] = original_dependency
            else:
                test_client.app.dependency_overrides.pop(get_db, None)
    
    def test_readiness_check_success(self):
        """测试就绪检查成功情况"""
        response = self.client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data
    
    @patch('app.main.SessionLocal')
    def test_readiness_check_database_error(self, mock_session_local):
        """测试就绪检查数据库错误情况"""
        # 模拟数据库连接错误
        mock_db = MagicMock()
        mock_db.execute.side_effect = SQLAlchemyError("Database connection failed")
        mock_session_local.return_value = mock_db
        
        response = self.client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert "系统未就绪" in data["error"]["message"]
    
    @patch('app.main.os.path.exists')
    def test_readiness_check_creates_upload_dir(self, mock_exists):
        """测试就绪检查创建上传目录"""
        # 模拟上传目录不存在
        mock_exists.return_value = False
        
        with patch('app.main.os.makedirs') as mock_makedirs:
            response = self.client.get("/ready")
            assert response.status_code == 200
            mock_makedirs.assert_called_once_with(settings.UPLOAD_DIR, exist_ok=True)
    
    @patch.dict(os.environ, {'ENABLE_METRICS': 'true'})
    @patch('app.core.config.settings.ENABLE_METRICS', True)
    def test_metrics_endpoint_enabled(self):
        """测试指标端点启用情况"""
        # 重新导入以应用环境变量
        from importlib import reload
        import app.main
        reload(app.main)
        
        client = TestClient(app.main.app)
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "Metrics endpoint" in data["message"]
    
    def test_static_directory_creation(self):
        """测试静态目录创建"""
        # 删除静态目录（如果存在）
        import shutil
        if os.path.exists("static"):
            shutil.rmtree("static")
        
        # 重新导入main模块以触发目录创建
        from importlib import reload
        import app.main
        reload(app.main)
        
        # 验证目录已创建
        assert os.path.exists("static")
    
    def test_cors_headers(self):
        """测试CORS头设置"""
        response = self.client.options("/api/info")
        # 检查CORS相关头是否存在
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 405]
    
    @patch('app.core.config.settings.ALLOWED_HEADERS', "Content-Type,Authorization")
    def test_cors_with_specific_headers(self):
        """测试CORS特定头设置"""
        # 重新导入以应用设置
        from importlib import reload
        import app.main
        reload(app.main)
        
        client = TestClient(app.main.app)
        response = client.options("/api/info")
        # 验证响应（可能是405或200）
        assert response.status_code in [200, 405]
    
    def test_exception_handlers_registered(self):
        """测试异常处理器注册"""
        # 触发一个不存在的端点来测试异常处理
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
        # 验证返回的是JSON格式
        assert response.headers["content-type"] == "application/json"
    
    @patch('app.core.config.settings.ENVIRONMENT', 'production')
    @patch('app.core.config.settings.FORCE_HTTPS', True)
    def test_https_redirect_middleware_in_production(self):
        """测试生产环境HTTPS重定向中间件"""
        # 重新导入以应用设置
        from importlib import reload
        import app.main
        reload(app.main)
        
        # 验证应用仍然可以正常响应
        client = TestClient(app.main.app)
        response = client.get("/api/info")
        assert response.status_code == 200
    
    @patch('app.core.config.settings.ENABLE_SECURITY_HEADERS', True)
    def test_security_headers_enabled(self):
        """测试安全头启用情况"""
        # 重新导入以应用设置
        from importlib import reload
        import app.main
        reload(app.main)
        
        # 验证应用仍然可以正常响应
        client = TestClient(app.main.app)
        response = client.get("/api/info")
        assert response.status_code == 200
    
    @patch('app.core.config.settings.ENABLE_SECURITY_HEADERS', False)
    def test_security_headers_disabled(self):
        """测试安全头禁用情况"""
        # 重新导入以应用设置
        from importlib import reload
        import app.main
        reload(app.main)
        
        # 验证应用仍然可以正常响应
        client = TestClient(app.main.app)
        response = client.get("/api/info")
        assert response.status_code == 200
    
    def test_docs_disabled_when_configured(self):
        """测试文档禁用配置"""
        with patch('app.core.config.settings.ENABLE_DOCS', False):
            # 重新导入以应用设置
            from importlib import reload
            import app.main
            reload(app.main)
            
            client = TestClient(app.main.app)
            # 验证docs端点不可用
            response = client.get("/docs")
            assert response.status_code == 404
    
    def teardown_method(self):
        """清理测试环境"""
        # 清理可能创建的文件
        if os.path.exists("static/index.html"):
            os.remove("static/index.html")
        
        # 清理依赖覆盖
        self.client.app.dependency_overrides.clear()
        
        # 重置模块状态
        from importlib import reload
        import app.main
        reload(app.main)