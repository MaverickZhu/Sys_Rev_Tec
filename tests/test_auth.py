import pytest
from fastapi.testclient import TestClient


class TestUserAuth:
    """用户认证测试"""
    
    def test_create_user(self, client: TestClient):
        """测试用户注册"""
        user_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert "password" not in data
        assert "id" in data
        assert "is_active" in data  # 确保密码不在响应中
    
    def test_create_user_duplicate_username(self, client: TestClient, test_user):
        """测试重复用户名注册"""
        user_data = {
            "username": test_user.username,
            "password": "password123"
        }
        response = client.post("/api/v1/users/", json=user_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 400
        response_data = response.json()
        assert "already exists" in response_data["error"]["message"]
    
    def test_login_success(self, client: TestClient, test_user):
        """测试成功登录"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, test_user):
        """测试无效凭据登录"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 400
        assert "Incorrect" in response.json()["error"]["message"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """测试不存在用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 400
        assert "Incorrect" in response.json()["error"]["message"]
    
    def test_access_protected_endpoint_without_token(self, client: TestClient):
        """测试无令牌访问受保护端点"""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_token(self, client: TestClient, auth_headers):
        """测试有令牌访问受保护端点"""
        response = client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200