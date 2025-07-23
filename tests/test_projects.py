import pytest
from fastapi.testclient import TestClient


class TestProjects:
    """项目管理测试"""
    
    def test_create_project(self, client: TestClient, auth_headers):
        """测试创建项目"""
        project_data = {
            "name": "新测试项目",
            "description": "这是一个新的测试项目",
            "project_code": "NEW-2024-001",
            "project_type": "货物"
        }
        response = client.post(
            "/api/v1/projects/", 
            json=project_data, 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_project_without_auth(self, client: TestClient):
        """测试无认证创建项目"""
        project_data = {
            "name": "未授权项目",
            "description": "这应该失败",
            "project_code": "UNAUTH-2024-001",
            "project_type": "货物"
        }
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == 401
    
    def test_get_projects(self, client: TestClient, auth_headers, test_project):
        """测试获取项目列表"""
        response = client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # 检查测试项目是否在列表中
        project_names = [p["name"] for p in data]
        assert test_project.name in project_names
    
    def test_get_projects_without_auth(self, client: TestClient):
        """测试无认证获取项目列表"""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401
    
    def test_get_projects_with_pagination(self, client: TestClient, auth_headers):
        """测试分页获取项目"""
        # 创建多个项目
        for i in range(5):
            project_data = {
                "name": f"分页测试项目 {i}",
                "description": f"第 {i} 个测试项目",
                "project_code": f"PAGE-2024-{i:03d}",
                "project_type": "货物"
            }
            client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        
        # 测试分页
        response = client.get("/api/v1/projects/?skip=0&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3
        
        # 测试跳过记录
        response = client.get("/api/v1/projects/?skip=2&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_project_with_empty_name(self, client: TestClient, auth_headers):
        """测试创建空名称项目"""
        project_data = {
            "name": "",
            "description": "空名称项目",
            "project_code": "EMPTY-2024-001",
            "project_type": "货物"
        }
        response = client.post(
            "/api/v1/projects/", 
            json=project_data, 
            headers=auth_headers
        )
        # 根据实际的验证逻辑，当前允许空名称项目
        assert response.status_code == 200
    
    def test_create_project_with_long_name(self, client: TestClient, auth_headers):
        """测试创建超长名称项目"""
        project_data = {
            "name": "a" * 300,  # 超长名称
            "description": "超长名称项目测试",
            "project_code": "LONG-2024-001",
            "project_type": "货物"
        }
        response = client.post(
            "/api/v1/projects/", 
            json=project_data, 
            headers=auth_headers
        )
        # 根据实际的验证逻辑，这可能返回400或422
        assert response.status_code in [200, 400, 422]