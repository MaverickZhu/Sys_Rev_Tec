import pytest
from fastapi.testclient import TestClient


class TestAPI:
    """API基础功能测试"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "features" in data
    
    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
    
    def test_docs_endpoint(self, client: TestClient):
        """测试API文档端点"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json(self, client: TestClient):
        """测试OpenAPI JSON端点"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert "政府采购项目审查分析系统" in data["info"]["title"]
    
    def test_cors_headers(self, client: TestClient):
        """测试CORS头部"""
        response = client.options("/")
        # 检查是否有CORS相关的头部
        assert response.status_code in [200, 405]  # OPTIONS可能不被支持
        
        # 测试实际请求的CORS头部
        response = client.get("/")
        # 在实际的CORS配置中，这些头部应该存在
        # 这里只是基础测试，实际的CORS测试需要跨域请求
    
    def test_api_version_consistency(self, client: TestClient):
        """测试API版本一致性"""
        # 测试根端点版本
        root_response = client.get("/")
        root_data = root_response.json()
        
        # 测试OpenAPI版本
        openapi_response = client.get("/openapi.json")
        openapi_data = openapi_response.json()
        
        # 版本应该一致
        assert root_data["version"] == openapi_data["info"]["version"]
    
    def test_invalid_endpoint(self, client: TestClient):
        """测试无效端点"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
    
    def test_api_v1_prefix(self, client: TestClient):
        """测试API v1前缀"""
        # 测试需要认证的端点返回401而不是404
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401  # 需要认证，不是404
        
        response = client.get("/api/v1/ocr/statistics")
        assert response.status_code == 401  # 需要认证，不是404
    
    def test_static_files_endpoint(self, client: TestClient):
        """测试静态文件端点"""
        # 测试静态文件路径是否可访问（即使文件不存在）
        response = client.get("/static/nonexistent.txt")
        # 应该返回404而不是500，说明路由配置正确
        assert response.status_code == 404
    
    def test_request_validation(self, client: TestClient):
        """测试请求验证"""
        # 测试无效的JSON请求
        response = client.post(
            "/api/v1/users/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # 验证错误
    
    def test_method_not_allowed(self, client: TestClient):
        """测试不允许的HTTP方法"""
        # 对只支持GET的端点发送POST请求
        response = client.post("/health")
        assert response.status_code == 405  # Method Not Allowed
        
        # 对只支持POST的端点发送GET请求
        response = client.get("/api/v1/login/access-token")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_large_request_body(self, client: TestClient):
        """测试大请求体"""
        # 创建一个大的请求体
        large_data = {"data": "x" * 10000}  # 10KB的数据
        
        response = client.post(
            "/api/v1/users/",
            json=large_data
        )
        # 应该返回验证错误而不是服务器错误
        assert response.status_code in [400, 422]
    
    def test_content_type_validation(self, client: TestClient):
        """测试内容类型验证"""
        # 发送错误的Content-Type
        response = client.post(
            "/api/v1/users/",
            data="{\"username\": \"test\"}",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [400, 422, 415]  # 不支持的媒体类型或验证错误