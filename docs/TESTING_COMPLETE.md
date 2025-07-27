# 测试指南完整版

## 输入验证安全测试

```python
# tests/test_security/test_input_validation.py
import pytest

class TestInputValidation:
    """输入验证安全测试"""
    
    def test_sql_injection_protection(self, client, auth_headers):
        """测试 SQL 注入保护"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UPDATE users SET password='hacked'; --",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'hacked'); --"
        ]
        
        for payload in sql_injection_payloads:
            # 测试搜索端点
            response = client.get("/api/v1/documents/search", 
                                params={"q": payload}, 
                                headers=auth_headers)
            
            # 应该返回正常响应，而不是数据库错误
            assert response.status_code in [200, 400, 422]
            
            # 测试项目创建
            project_data = {
                "name": payload,
                "description": "Test project"
            }
            
            response = client.post("/api/v1/projects/", 
                                 json=project_data, 
                                 headers=auth_headers)
            
            # 应该被验证拒绝或正常处理
            assert response.status_code in [201, 400, 422]
    
    def test_xss_protection(self, client, auth_headers):
        """测试 XSS 攻击保护"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>"
        ]
        
        for payload in xss_payloads:
            project_data = {
                "name": f"Test Project {payload}",
                "description": f"Description with {payload}"
            }
            
            response = client.post("/api/v1/projects/", 
                                 json=project_data, 
                                 headers=auth_headers)
            
            if response.status_code == 201:
                project = response.json()
                
                # 获取项目详情
                response = client.get(f"/api/v1/projects/{project['id']}", 
                                    headers=auth_headers)
                
                assert response.status_code == 200
                project_detail = response.json()
                
                # 验证输出已被转义
                assert "<script>" not in project_detail["name"]
                assert "<script>" not in project_detail["description"]
                
                # 清理
                client.delete(f"/api/v1/projects/{project['id']}", 
                            headers=auth_headers)
    
    def test_file_upload_validation(self, client, auth_headers, test_project):
        """测试文件上传验证"""
        # 测试恶意文件扩展名
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.php", b"<?php echo 'hacked'; ?>", "application/x-php"),
            ("shell.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh"),
            ("virus.bat", b"@echo off\ndel /f /q *.*", "application/x-msdos-program")
        ]
        
        for filename, content, mime_type in malicious_files:
            files = {"file": (filename, content, mime_type)}
            data = {
                "project_id": test_project.id,
                "description": "Malicious file test"
            }
            
            response = client.post("/api/v1/documents/upload", 
                                 files=files, data=data, headers=auth_headers)
            
            # 应该被拒绝
            assert response.status_code == 400
            assert "not allowed" in response.json()["detail"].lower()
    
    def test_path_traversal_protection(self, client, auth_headers):
        """测试路径遍历攻击保护"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc//passwd",
            "/var/log/../../etc/passwd"
        ]
        
        for payload in path_traversal_payloads:
            # 测试文件下载端点
            response = client.get(f"/api/v1/documents/download/{payload}", 
                                headers=auth_headers)
            
            # 应该返回 404 或 400，而不是系统文件内容
            assert response.status_code in [400, 404]
    
    def test_command_injection_protection(self, client, auth_headers):
        """测试命令注入保护"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; ping -c 1 127.0.0.1"
        ]
        
        for payload in command_injection_payloads:
            # 测试可能执行系统命令的端点
            project_data = {
                "name": f"Project {payload}",
                "description": "Test project"
            }
            
            response = client.post("/api/v1/projects/", 
                                 json=project_data, 
                                 headers=auth_headers)
            
            # 应该正常处理或被验证拒绝
            assert response.status_code in [201, 400, 422]
            
            if response.status_code == 201:
                project = response.json()
                # 清理
                client.delete(f"/api/v1/projects/{project['id']}", 
                            headers=auth_headers)
```

## API测试

### API 契约测试

```python
# tests/test_api/test_api_contract.py
import pytest
from jsonschema import validate, ValidationError

class TestAPIContract:
    """API 契约测试"""
    
    def test_user_registration_response_schema(self, client):
        """测试用户注册响应模式"""
        user_data = {
            "username": "contracttest",
            "email": "contract@example.com",
            "full_name": "Contract Test",
            "password": "securepassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 定义期望的响应模式
        expected_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "full_name": {"type": "string"},
                "is_active": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "username", "email", "full_name", "is_active", "created_at"],
            "additionalProperties": False
        }
        
        # 验证响应符合模式
        response_data = response.json()
        validate(instance=response_data, schema=expected_schema)
        
        # 验证不包含敏感信息
        assert "password" not in response_data
        assert "hashed_password" not in response_data
    
    def test_project_list_response_schema(self, client, auth_headers):
        """测试项目列表响应模式"""
        response = client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        
        # 定义期望的响应模式
        expected_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "status": {"type": "string", "enum": ["active", "inactive", "completed"]},
                    "owner_id": {"type": "integer"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "status", "owner_id", "created_at"]
            }
        }
        
        response_data = response.json()
        validate(instance=response_data, schema=expected_schema)
    
    def test_error_response_schema(self, client):
        """测试错误响应模式"""
        # 触发 404 错误
        response = client.get("/api/v1/projects/99999")
        assert response.status_code == 404
        
        # 定义期望的错误响应模式
        expected_schema = {
            "type": "object",
            "properties": {
                "detail": {"type": "string"},
                "error_code": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"}
            },
            "required": ["detail"]
        }
        
        response_data = response.json()
        validate(instance=response_data, schema=expected_schema)
    
    def test_pagination_response_schema(self, client, auth_headers):
        """测试分页响应模式"""
        response = client.get("/api/v1/documents/", 
                            params={"limit": 10, "offset": 0}, 
                            headers=auth_headers)
        assert response.status_code == 200
        
        # 定义期望的分页响应模式
        expected_schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array"},
                "total": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1},
                "offset": {"type": "integer", "minimum": 0},
                "has_next": {"type": "boolean"},
                "has_prev": {"type": "boolean"}
            },
            "required": ["items", "total", "limit", "offset", "has_next", "has_prev"]
        }
        
        response_data = response.json()
        validate(instance=response_data, schema=expected_schema)
```

## 测试数据管理

### 测试数据工厂

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime

from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.services.auth import get_password_hash

class UserFactory(SQLAlchemyModelFactory):
    """用户工厂"""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.Faker("name")
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword"))
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class ProjectFactory(SQLAlchemyModelFactory):
    """项目工厂"""
    
    class Meta:
        model = Project
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)
    status = "active"
    owner = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class DocumentFactory(SQLAlchemyModelFactory):
    """文档工厂"""
    
    class Meta:
        model = Document
        sqlalchemy_session_persistence = "commit"
    
    filename = factory.Faker("file_name", extension="pdf")
    original_filename = factory.LazyAttribute(lambda obj: obj.filename)
    file_path = factory.LazyAttribute(lambda obj: f"/uploads/{obj.filename}")
    file_size = factory.Faker("random_int", min=1024, max=10485760)  # 1KB - 10MB
    mime_type = "application/pdf"
    project = factory.SubFactory(ProjectFactory)
    uploader = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
```

### 测试数据清理

```python
# tests/utils/cleanup.py
import os
import shutil
from pathlib import Path

class TestDataCleanup:
    """测试数据清理工具"""
    
    def __init__(self, test_upload_dir: str = "./test_uploads"):
        self.test_upload_dir = Path(test_upload_dir)
    
    def cleanup_uploaded_files(self):
        """清理上传的测试文件"""
        if self.test_upload_dir.exists():
            shutil.rmtree(self.test_upload_dir)
        self.test_upload_dir.mkdir(exist_ok=True)
    
    def cleanup_database(self, db_session):
        """清理数据库测试数据"""
        from app.models.document import Document
        from app.models.project import Project
        from app.models.user import User
        
        # 按依赖关系顺序删除
        db_session.query(Document).delete()
        db_session.query(Project).delete()
        db_session.query(User).filter(User.username.like("test%")).delete()
        db_session.commit()
    
    def cleanup_cache(self):
        """清理缓存"""
        import redis
        from app.config import get_settings
        
        settings = get_settings()
        if settings.redis_url:
            r = redis.from_url(settings.redis_url)
            # 只清理测试相关的缓存键
            test_keys = r.keys("test:*")
            if test_keys:
                r.delete(*test_keys)
```

## 测试自动化

### GitHub Actions 集成

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 app tests
        black --check app tests
        isort --check-only app tests
        mypy app
    
    - name: Run security checks
      run: |
        bandit -r app
        safety check
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        TESTING: true
      run: |
        pytest -v --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Run performance tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/test_performance/ -v --tb=short
```

### 测试报告生成

```python
# tests/utils/reporting.py
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "./test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_html_report(self, test_results: Dict[str, Any]):
        """生成 HTML 测试报告"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                .passed { color: green; }
                .failed { color: red; }
                .skipped { color: orange; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Generated: {timestamp}</p>
                <p>Total Tests: {total}</p>
                <p class="passed">Passed: {passed}</p>
                <p class="failed">Failed: {failed}</p>
                <p class="skipped">Skipped: {skipped}</p>
                <p>Success Rate: {success_rate:.1f}%</p>
                <p>Duration: {duration:.2f}s</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Case</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Message</th>
                </tr>
                {test_rows}
            </table>
        </body>
        </html>
        """
        
        # 生成测试行
        test_rows = ""
        for test in test_results.get("tests", []):
            status_class = test["status"].lower()
            test_rows += f"""
                <tr>
                    <td>{test['name']}</td>
                    <td class="{status_class}">{test['status']}</td>
                    <td>{test['duration']:.3f}s</td>
                    <td>{test.get('message', '')}</td>
                </tr>
            """
        
        # 填充模板
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=test_results["summary"]["total"],
            passed=test_results["summary"]["passed"],
            failed=test_results["summary"]["failed"],
            skipped=test_results["summary"]["skipped"],
            success_rate=test_results["summary"]["success_rate"],
            duration=test_results["summary"]["duration"],
            test_rows=test_rows
        )
        
        # 保存报告
        report_file = self.output_dir / "test_report.html"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return report_file
    
    def generate_json_report(self, test_results: Dict[str, Any]):
        """生成 JSON 测试报告"""
        report_file = self.output_dir / "test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def parse_junit_xml(self, junit_file: str) -> Dict[str, Any]:
        """解析 JUnit XML 报告"""
        tree = ET.parse(junit_file)
        root = tree.getroot()
        
        test_results = {
            "summary": {
                "total": int(root.get("tests", 0)),
                "passed": 0,
                "failed": int(root.get("failures", 0)),
                "skipped": int(root.get("skipped", 0)),
                "duration": float(root.get("time", 0))
            },
            "tests": []
        }
        
        for testcase in root.findall(".//testcase"):
            test_info = {
                "name": f"{testcase.get('classname')}.{testcase.get('name')}",
                "duration": float(testcase.get("time", 0)),
                "status": "PASSED",
                "message": ""
            }
            
            # 检查失败
            failure = testcase.find("failure")
            if failure is not None:
                test_info["status"] = "FAILED"
                test_info["message"] = failure.get("message", "")
            
            # 检查跳过
            skipped = testcase.find("skipped")
            if skipped is not None:
                test_info["status"] = "SKIPPED"
                test_info["message"] = skipped.get("message", "")
            
            test_results["tests"].append(test_info)
        
        # 计算通过的测试数量
        test_results["summary"]["passed"] = (
            test_results["summary"]["total"] - 
            test_results["summary"]["failed"] - 
            test_results["summary"]["skipped"]
        )
        
        # 计算成功率
        if test_results["summary"]["total"] > 0:
            test_results["summary"]["success_rate"] = (
                test_results["summary"]["passed"] / 
                test_results["summary"]["total"] * 100
            )
        else:
            test_results["summary"]["success_rate"] = 0
        
        return test_results
```

## 最佳实践

### 测试编写原则

1. **FIRST 原则**
   - **Fast**: 测试应该快速执行
   - **Independent**: 测试之间应该相互独立
   - **Repeatable**: 测试应该在任何环境中可重复
   - **Self-Validating**: 测试应该有明确的通过/失败结果
   - **Timely**: 测试应该及时编写

2. **AAA 模式**
   - **Arrange**: 准备测试数据和环境
   - **Act**: 执行被测试的操作
   - **Assert**: 验证结果

3. **测试命名规范**
   ```python
   def test_should_return_user_when_valid_credentials_provided(self):
       """应该在提供有效凭据时返回用户"""
       pass
   
   def test_should_raise_exception_when_invalid_email_format(self):
       """应该在邮箱格式无效时抛出异常"""
       pass
   ```

### 测试数据管理

1. **使用工厂模式**
   ```python
   # 好的做法
   user = UserFactory(username="testuser")
   project = ProjectFactory(owner=user)
   
   # 避免硬编码
   user = User(
       username="testuser",
       email="test@example.com",
       hashed_password="..."
   )
   ```

2. **测试隔离**
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_after_test(self, db_session):
       """每个测试后自动清理"""
       yield
       db_session.rollback()
   ```

3. **使用临时文件**
   ```python
   import tempfile
   
   def test_file_upload(self):
       with tempfile.NamedTemporaryFile() as temp_file:
           temp_file.write(b"test content")
           temp_file.seek(0)
           # 使用 temp_file 进行测试
   ```

### 性能测试建议

1. **设置合理的性能基准**
   ```python
   PERFORMANCE_THRESHOLDS = {
       "api_response_time": 1.0,      # 1秒
       "database_query_time": 0.1,    # 100毫秒
       "file_upload_time": 5.0,       # 5秒
       "ocr_processing_time": 30.0,   # 30秒
   }
   ```

2. **监控资源使用**
   ```python
   import psutil
   
   def test_memory_usage(self):
       process = psutil.Process()
       initial_memory = process.memory_info().rss
       
       # 执行操作
       perform_operation()
       
       final_memory = process.memory_info().rss
       memory_increase = final_memory - initial_memory
       
       assert memory_increase < 100 * 1024 * 1024  # 100MB
   ```

### 测试维护

1. **定期审查测试**
   - 删除过时的测试
   - 更新测试以反映需求变化
   - 重构重复的测试代码

2. **监控测试质量**
   - 跟踪测试覆盖率
   - 分析测试执行时间
   - 识别不稳定的测试

3. **文档化测试策略**
   - 记录测试决策
   - 维护测试用例清单
   - 提供测试环境设置指南

## 总结

本测试指南涵盖了政府采购项目审查分析系统的完整测试策略，包括：

- **分层测试架构**：单元测试、集成测试、端到端测试
- **全面的测试类型**：功能测试、性能测试、安全测试
- **自动化测试流程**：CI/CD 集成、测试报告生成
- **最佳实践指导**：测试编写、数据管理、维护策略

通过遵循本指南，开发团队可以建立高质量的测试体系，确保系统的可靠性、安全性和性能。测试不仅是质量保证的手段，更是促进代码设计改进和团队协作的重要工具。

记住，好的测试是投资，而不是成本。它们为系统的长期维护和演进提供了坚实的基础。