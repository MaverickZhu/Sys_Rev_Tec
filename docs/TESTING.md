# 测试指南

本文档详细描述了政府采购项目审查分析系统的测试策略、测试方法和测试最佳实践。

## 目录

- [测试概述](#测试概述)
- [测试策略](#测试策略)
- [测试环境](#测试环境)
- [单元测试](#单元测试)
- [集成测试](#集成测试)
- [端到端测试](#端到端测试)
- [性能测试](#性能测试)
- [安全测试](#安全测试)
- [API测试](#api测试)
- [数据库测试](#数据库测试)
- [测试数据管理](#测试数据管理)
- [测试自动化](#测试自动化)
- [测试报告](#测试报告)
- [最佳实践](#最佳实践)

## 测试概述

### 测试目标

政府采购项目审查分析系统的测试目标是确保：

- **功能正确性**：所有功能按照需求规格正确实现
- **性能达标**：系统在预期负载下性能满足要求
- **安全可靠**：系统具备足够的安全防护能力
- **稳定性**：系统在各种条件下稳定运行
- **可维护性**：代码质量高，易于维护和扩展

### 测试原则

1. **测试驱动开发 (TDD)**：先写测试，再写实现
2. **持续测试**：在 CI/CD 流水线中集成自动化测试
3. **分层测试**：单元测试、集成测试、端到端测试相结合
4. **风险驱动**：优先测试高风险和核心功能
5. **数据驱动**：使用真实和模拟数据进行测试

### 测试金字塔

```
        /\           E2E Tests (10%)
       /  \          - 用户界面测试
      /    \         - 完整业务流程测试
     /______\        
    /        \       Integration Tests (20%)
   /          \      - API 集成测试
  /            \     - 数据库集成测试
 /              \    - 第三方服务集成测试
/________________\   
                     Unit Tests (70%)
                     - 函数/方法测试
                     - 类测试
                     - 模块测试
```

## 测试策略

### 测试分类

#### 按测试层级分类

1. **单元测试 (Unit Tests)**
   - 测试单个函数、方法或类
   - 快速执行，提供即时反馈
   - 覆盖率目标：90%+

2. **集成测试 (Integration Tests)**
   - 测试模块间的交互
   - 验证接口和数据流
   - 包括数据库、外部服务集成

3. **端到端测试 (E2E Tests)**
   - 测试完整的用户场景
   - 验证系统整体功能
   - 模拟真实用户操作

#### 按测试类型分类

1. **功能测试**
   - 验证功能需求
   - 正常流程和异常流程
   - 边界条件测试

2. **性能测试**
   - 负载测试
   - 压力测试
   - 容量测试

3. **安全测试**
   - 认证授权测试
   - 输入验证测试
   - 安全漏洞扫描

4. **兼容性测试**
   - 浏览器兼容性
   - 操作系统兼容性
   - 数据库版本兼容性

### 测试覆盖率目标

```python
# 覆盖率目标配置
COVERAGE_TARGETS = {
    "overall": 90,           # 整体覆盖率
    "unit_tests": 95,       # 单元测试覆盖率
    "integration_tests": 80, # 集成测试覆盖率
    "critical_modules": 100, # 核心模块覆盖率
    "new_code": 100,        # 新代码覆盖率
}

# 关键模块列表
CRITICAL_MODULES = [
    "app.auth",              # 认证模块
    "app.security",          # 安全模块
    "app.models",            # 数据模型
    "app.api.v1.auth",       # 认证 API
    "app.services.ocr",      # OCR 服务
    "app.services.document", # 文档服务
]
```

## 测试环境

### 环境配置

#### 开发环境 (Development)

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  app-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql://test_user:test_pass@db-test:5432/test_db
      - REDIS_URL=redis://redis-test:6379/0
      - JWT_SECRET_KEY=test_secret_key
      - TESTING=true
    depends_on:
      - db-test
      - redis-test
    volumes:
      - .:/app
      - ./test_uploads:/app/uploads
    command: pytest -v --cov=app --cov-report=html --cov-report=term

  db-test:
    image: postgres:15
    environment:
      - POSTGRES_DB=test_db
      - POSTGRES_USER=test_user
      - POSTGRES_PASSWORD=test_pass
    volumes:
      - test_postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

volumes:
  test_postgres_data:
```

#### 测试配置

```python
# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import get_settings

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from app.models.user import User
    from app.services.auth import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """创建认证头"""
    response = client.post("/api/v1/auth/login", json={
        "username": test_user.username,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_project(db_session, test_user):
    """创建测试项目"""
    from app.models.project import Project
    
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=test_user.id,
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
```

## 单元测试

### 模型测试

```python
# tests/test_models/test_user.py
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.services.auth import get_password_hash, verify_password

class TestUserModel:
    """用户模型测试"""
    
    def test_create_user(self, db_session):
        """测试创建用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password123")
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_password_hashing(self):
        """测试密码哈希"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_unique_username_constraint(self, db_session):
        """测试用户名唯一性约束"""
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password=get_password_hash("password")
        )
        user2 = User(
            username="testuser",  # 重复用户名
            email="test2@example.com",
            hashed_password=get_password_hash("password")
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_email_constraint(self, db_session):
        """测试邮箱唯一性约束"""
        user1 = User(
            username="user1",
            email="test@example.com",
            hashed_password=get_password_hash("password")
        )
        user2 = User(
            username="user2",
            email="test@example.com",  # 重复邮箱
            hashed_password=get_password_hash("password")
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_repr(self, db_session):
        """测试用户字符串表示"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password")
        )
        db_session.add(user)
        db_session.commit()
        
        assert "testuser" in str(user)
        assert "test@example.com" in str(user)
```

### 服务测试

```python
# tests/test_services/test_auth_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.auth import AuthService, create_access_token, verify_token
from app.models.user import User
from app.schemas.auth import UserCreate

class TestAuthService:
    """认证服务测试"""
    
    @pytest.fixture
    def auth_service(self, db_session):
        return AuthService(db_session)
    
    def test_create_user(self, auth_service):
        """测试创建用户"""
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            full_name="New User",
            password="securepassword123"
        )
        
        user = auth_service.create_user(user_data)
        
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.hashed_password != "securepassword123"  # 应该被哈希
    
    def test_authenticate_user_success(self, auth_service, test_user):
        """测试用户认证成功"""
        user = auth_service.authenticate_user("testuser", "testpassword")
        
        assert user is not None
        assert user.username == "testuser"
    
    def test_authenticate_user_wrong_password(self, auth_service, test_user):
        """测试错误密码认证失败"""
        user = auth_service.authenticate_user("testuser", "wrongpassword")
        
        assert user is None
    
    def test_authenticate_user_nonexistent(self, auth_service):
        """测试不存在用户认证失败"""
        user = auth_service.authenticate_user("nonexistent", "password")
        
        assert user is None
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        user_id = 123
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """测试验证有效令牌"""
        user_id = 123
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
    
    def test_verify_token_expired(self):
        """测试验证过期令牌"""
        user_id = 123
        # 创建已过期的令牌
        with patch('app.services.auth.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(hours=2)
            token = create_access_token(user_id)
        
        payload = verify_token(token)
        
        assert payload is None
    
    def test_verify_token_invalid(self):
        """测试验证无效令牌"""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    @patch('app.services.auth.send_email')
    def test_send_password_reset_email(self, mock_send_email, auth_service, test_user):
        """测试发送密码重置邮件"""
        result = auth_service.send_password_reset_email(test_user.email)
        
        assert result is True
        mock_send_email.assert_called_once()
        
        # 验证邮件参数
        call_args = mock_send_email.call_args
        assert test_user.email in call_args[1]['to']
        assert "密码重置" in call_args[1]['subject']
```

### OCR 服务测试

```python
# tests/test_services/test_ocr_service.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from app.services.ocr import OCRService, OCRResult
from app.exceptions import OCRProcessingError

class TestOCRService:
    """OCR 服务测试"""
    
    @pytest.fixture
    def ocr_service(self):
        return OCRService()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """模拟 PDF 文件内容"""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    @pytest.fixture
    def sample_image_content(self):
        """模拟图片文件内容"""
        # 简单的 PNG 文件头
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    
    @patch('app.services.ocr.pytesseract.image_to_string')
    @patch('app.services.ocr.Image.open')
    def test_process_image_success(self, mock_image_open, mock_tesseract, 
                                 ocr_service, sample_image_content):
        """测试图片 OCR 处理成功"""
        # 模拟 PIL Image
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        # 模拟 tesseract 输出
        mock_tesseract.return_value = "Extracted text from image"
        
        result = ocr_service.process_image(sample_image_content)
        
        assert isinstance(result, OCRResult)
        assert result.text == "Extracted text from image"
        assert result.confidence > 0
        assert result.language == "chi_sim+eng"
        
        mock_image_open.assert_called_once()
        mock_tesseract.assert_called_once_with(mock_image, lang="chi_sim+eng")
    
    @patch('app.services.ocr.pytesseract.image_to_string')
    @patch('app.services.ocr.Image.open')
    def test_process_image_tesseract_error(self, mock_image_open, mock_tesseract, 
                                         ocr_service, sample_image_content):
        """测试 tesseract 处理错误"""
        mock_image_open.return_value = Mock()
        mock_tesseract.side_effect = Exception("Tesseract error")
        
        with pytest.raises(OCRProcessingError, match="OCR processing failed"):
            ocr_service.process_image(sample_image_content)
    
    @patch('app.services.ocr.fitz.open')
    def test_process_pdf_success(self, mock_fitz_open, ocr_service, sample_pdf_content):
        """测试 PDF OCR 处理成功"""
        # 模拟 PyMuPDF 文档
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Extracted text from PDF"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__enter__ = Mock(return_value=mock_doc)
        mock_doc.__exit__ = Mock(return_value=None)
        
        mock_fitz_open.return_value = mock_doc
        
        result = ocr_service.process_pdf(sample_pdf_content)
        
        assert isinstance(result, OCRResult)
        assert result.text == "Extracted text from PDF"
        assert result.confidence > 0
        
        mock_fitz_open.assert_called_once()
        mock_page.get_text.assert_called_once()
    
    @patch('app.services.ocr.fitz.open')
    def test_process_pdf_error(self, mock_fitz_open, ocr_service, sample_pdf_content):
        """测试 PDF 处理错误"""
        mock_fitz_open.side_effect = Exception("PDF processing error")
        
        with pytest.raises(OCRProcessingError, match="PDF processing failed"):
            ocr_service.process_pdf(sample_pdf_content)
    
    def test_detect_language(self, ocr_service):
        """测试语言检测"""
        chinese_text = "这是中文文本"
        english_text = "This is English text"
        mixed_text = "This is 中英文混合 text"
        
        assert ocr_service.detect_language(chinese_text) == "chi_sim"
        assert ocr_service.detect_language(english_text) == "eng"
        assert ocr_service.detect_language(mixed_text) == "chi_sim+eng"
    
    def test_clean_text(self, ocr_service):
        """测试文本清理"""
        dirty_text = "  Text with\n\nextra   spaces\t\tand\r\nline breaks  "
        expected = "Text with extra spaces and line breaks"
        
        cleaned = ocr_service.clean_text(dirty_text)
        
        assert cleaned == expected
    
    @patch('app.services.ocr.OCRService.process_image')
    @patch('app.services.ocr.OCRService.process_pdf')
    def test_process_file_pdf(self, mock_process_pdf, mock_process_image, ocr_service):
        """测试处理 PDF 文件"""
        mock_result = OCRResult(text="PDF text", confidence=0.95)
        mock_process_pdf.return_value = mock_result
        
        result = ocr_service.process_file(b"pdf content", "document.pdf")
        
        assert result == mock_result
        mock_process_pdf.assert_called_once_with(b"pdf content")
        mock_process_image.assert_not_called()
    
    @patch('app.services.ocr.OCRService.process_image')
    @patch('app.services.ocr.OCRService.process_pdf')
    def test_process_file_image(self, mock_process_pdf, mock_process_image, ocr_service):
        """测试处理图片文件"""
        mock_result = OCRResult(text="Image text", confidence=0.90)
        mock_process_image.return_value = mock_result
        
        result = ocr_service.process_file(b"image content", "image.jpg")
        
        assert result == mock_result
        mock_process_image.assert_called_once_with(b"image content")
        mock_process_pdf.assert_not_called()
    
    def test_process_file_unsupported_format(self, ocr_service):
        """测试不支持的文件格式"""
        with pytest.raises(OCRProcessingError, match="Unsupported file format"):
            ocr_service.process_file(b"content", "document.txt")
```

## 集成测试

### API 集成测试

```python
# tests/test_integration/test_auth_api.py
import pytest
from fastapi.testclient import TestClient

class TestAuthAPI:
    """认证 API 集成测试"""
    
    def test_register_user_success(self, client):
        """测试用户注册成功"""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "full_name": "New User",
            "password": "securepassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # 不应该返回密码
    
    def test_register_user_duplicate_username(self, client, test_user):
        """测试重复用户名注册失败"""
        user_data = {
            "username": test_user.username,  # 重复用户名
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """测试登录成功"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_wrong_password(self, client, test_user):
        """测试错误密码登录失败"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """测试不存在用户登录失败"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client, auth_headers):
        """测试获取当前用户信息"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "hashed_password" not in data
    
    def test_get_current_user_unauthorized(self, client):
        """测试未授权访问用户信息"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_refresh_token(self, client, auth_headers):
        """测试刷新令牌"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, auth_headers):
        """测试登出"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
        
        # 验证令牌已失效
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 401
```

### 数据库集成测试

```python
# tests/test_integration/test_database.py
import pytest
from sqlalchemy import text

from app.models.user import User
from app.models.project import Project
from app.models.document import Document

class TestDatabaseIntegration:
    """数据库集成测试"""
    
    def test_user_project_relationship(self, db_session):
        """测试用户-项目关系"""
        # 创建用户
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # 创建项目
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # 验证关系
        db_session.refresh(user)
        assert len(user.owned_projects) == 1
        assert user.owned_projects[0].name == "Test Project"
        
        db_session.refresh(project)
        assert project.owner.username == "testuser"
    
    def test_project_document_relationship(self, db_session, test_user):
        """测试项目-文档关系"""
        # 创建项目
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # 创建文档
        document = Document(
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            project_id=project.id,
            uploaded_by=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        
        # 验证关系
        db_session.refresh(project)
        assert len(project.documents) == 1
        assert project.documents[0].filename == "test.pdf"
        
        db_session.refresh(document)
        assert document.project.name == "Test Project"
        assert document.uploader.username == test_user.username
    
    def test_cascade_delete(self, db_session, test_user):
        """测试级联删除"""
        # 创建项目和文档
        project = Project(
            name="Test Project",
            owner_id=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        document = Document(
            filename="test.pdf",
            original_filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            project_id=project.id,
            uploaded_by=test_user.id
        )
        db_session.add(document)
        db_session.commit()
        
        project_id = project.id
        document_id = document.id
        
        # 删除项目
        db_session.delete(project)
        db_session.commit()
        
        # 验证文档也被删除
        remaining_document = db_session.query(Document).filter(
            Document.id == document_id
        ).first()
        assert remaining_document is None
    
    def test_database_constraints(self, db_session):
        """测试数据库约束"""
        # 测试用户名唯一约束
        user1 = User(
            username="testuser",
            email="test1@example.com",
            hashed_password="password"
        )
        user2 = User(
            username="testuser",  # 重复用户名
            email="test2@example.com",
            hashed_password="password"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # 应该抛出完整性错误
            db_session.commit()
    
    def test_database_indexes(self, db_session):
        """测试数据库索引"""
        # 检查重要字段的索引
        result = db_session.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename IN ('users', 'projects', 'documents')
        """))
        
        indexes = [row[0] for row in result]
        
        # 验证关键索引存在
        assert any('username' in idx for idx in indexes)
        assert any('email' in idx for idx in indexes)
        assert any('project_id' in idx for idx in indexes)
```

## 端到端测试

### 用户流程测试

```python
# tests/test_e2e/test_user_workflows.py
import pytest
from fastapi.testclient import TestClient
import tempfile
import os

class TestUserWorkflows:
    """用户工作流程端到端测试"""
    
    def test_complete_user_registration_and_login_flow(self, client):
        """测试完整的用户注册和登录流程"""
        # 1. 注册新用户
        registration_data = {
            "username": "e2euser",
            "email": "e2e@example.com",
            "full_name": "E2E Test User",
            "password": "securepassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201
        user_data = response.json()
        
        # 2. 登录
        login_data = {
            "username": "e2euser",
            "password": "securepassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token_data = response.json()
        
        # 3. 使用令牌访问受保护资源
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        current_user = response.json()
        assert current_user["username"] == "e2euser"
        assert current_user["email"] == "e2e@example.com"
    
    def test_complete_project_management_flow(self, client, auth_headers):
        """测试完整的项目管理流程"""
        # 1. 创建项目
        project_data = {
            "name": "E2E Test Project",
            "description": "End-to-end test project",
            "category": "government_procurement"
        }
        
        response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]
        
        # 2. 获取项目列表
        response = client.get("/api/v1/projects/", headers=auth_headers)
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) >= 1
        assert any(p["id"] == project_id for p in projects)
        
        # 3. 获取单个项目
        response = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        retrieved_project = response.json()
        assert retrieved_project["name"] == "E2E Test Project"
        
        # 4. 更新项目
        update_data = {
            "name": "Updated E2E Project",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/v1/projects/{project_id}", 
                            json=update_data, headers=auth_headers)
        assert response.status_code == 200
        updated_project = response.json()
        assert updated_project["name"] == "Updated E2E Project"
        
        # 5. 删除项目
        response = client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # 6. 验证项目已删除
        response = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_complete_document_upload_and_ocr_flow(self, client, auth_headers, test_project):
        """测试完整的文档上传和 OCR 流程"""
        # 1. 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for OCR processing.")
            temp_file_path = f.name
        
        try:
            # 2. 上传文档
            with open(temp_file_path, 'rb') as f:
                files = {"file": ("test_document.txt", f, "text/plain")}
                data = {
                    "project_id": test_project.id,
                    "description": "Test document for E2E testing"
                }
                
                response = client.post("/api/v1/documents/upload", 
                                     files=files, data=data, headers=auth_headers)
                assert response.status_code == 201
                document = response.json()
                document_id = document["id"]
            
            # 3. 获取文档信息
            response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
            assert response.status_code == 200
            retrieved_doc = response.json()
            assert retrieved_doc["original_filename"] == "test_document.txt"
            
            # 4. 触发 OCR 处理
            response = client.post(f"/api/v1/documents/{document_id}/ocr", 
                                 headers=auth_headers)
            assert response.status_code == 202  # 异步处理
            
            # 5. 检查 OCR 状态
            response = client.get(f"/api/v1/documents/{document_id}/ocr/status", 
                                headers=auth_headers)
            assert response.status_code == 200
            ocr_status = response.json()
            assert "status" in ocr_status
            
            # 6. 获取 OCR 结果（如果完成）
            if ocr_status["status"] == "completed":
                response = client.get(f"/api/v1/documents/{document_id}/ocr/result", 
                                    headers=auth_headers)
                assert response.status_code == 200
                ocr_result = response.json()
                assert "text" in ocr_result
            
            # 7. 下载文档
            response = client.get(f"/api/v1/documents/{document_id}/download", 
                                headers=auth_headers)
            assert response.status_code == 200
            
            # 8. 删除文档
            response = client.delete(f"/api/v1/documents/{document_id}", 
                                   headers=auth_headers)
            assert response.status_code == 204
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_search_and_filter_flow(self, client, auth_headers, test_project):
        """测试搜索和过滤流程"""
        # 1. 创建多个测试文档
        documents = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Test document {i} with unique content.")
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {"file": (f"test_doc_{i}.txt", f, "text/plain")}
                    data = {
                        "project_id": test_project.id,
                        "description": f"Test document {i}"
                    }
                    
                    response = client.post("/api/v1/documents/upload", 
                                         files=files, data=data, headers=auth_headers)
                    assert response.status_code == 201
                    documents.append(response.json())
            finally:
                os.unlink(temp_file_path)
        
        # 2. 搜索文档
        response = client.get("/api/v1/documents/search", 
                            params={"q": "test", "project_id": test_project.id}, 
                            headers=auth_headers)
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results) >= 3
        
        # 3. 按项目过滤
        response = client.get("/api/v1/documents/", 
                            params={"project_id": test_project.id}, 
                            headers=auth_headers)
        assert response.status_code == 200
        filtered_docs = response.json()
        assert len(filtered_docs) >= 3
        
        # 4. 分页测试
        response = client.get("/api/v1/documents/", 
                            params={"project_id": test_project.id, "limit": 2}, 
                            headers=auth_headers)
        assert response.status_code == 200
        paginated_docs = response.json()
        assert len(paginated_docs) <= 2
        
        # 清理创建的文档
        for doc in documents:
            client.delete(f"/api/v1/documents/{doc['id']}", headers=auth_headers)
```

## 性能测试

### 负载测试

```python
# tests/test_performance/test_load.py
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import statistics

class TestLoadPerformance:
    """负载性能测试"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture
    async def auth_token(self, base_url):
        """获取认证令牌"""
        async with aiohttp.ClientSession() as session:
            # 先注册用户
            user_data = {
                "username": "loadtest",
                "email": "loadtest@example.com",
                "full_name": "Load Test User",
                "password": "loadtestpassword"
            }
            
            async with session.post(f"{base_url}/api/v1/auth/register", 
                                   json=user_data) as response:
                if response.status not in [201, 400]:  # 400 表示用户已存在
                    raise Exception(f"Registration failed: {response.status}")
            
            # 登录获取令牌
            login_data = {
                "username": "loadtest",
                "password": "loadtestpassword"
            }
            
            async with session.post(f"{base_url}/api/v1/auth/login", 
                                   json=login_data) as response:
                if response.status != 200:
                    raise Exception(f"Login failed: {response.status}")
                
                data = await response.json()
                return data["access_token"]
    
    async def make_request(self, session, url, headers=None, method="GET", json_data=None):
        """发送单个请求并测量响应时间"""
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    await response.text()
                    status = response.status
            elif method == "POST":
                async with session.post(url, headers=headers, json=json_data) as response:
                    await response.text()
                    status = response.status
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                "status": status,
                "response_time": response_time,
                "success": 200 <= status < 300
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "status": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }
    
    @pytest.mark.asyncio
    async def test_api_endpoint_load(self, base_url, auth_token):
        """测试 API 端点负载"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        concurrent_users = 50
        requests_per_user = 10
        
        async with aiohttp.ClientSession() as session:
            # 创建并发任务
            tasks = []
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.make_request(
                        session, 
                        f"{base_url}/api/v1/auth/me", 
                        headers=headers
                    )
                    tasks.append(task)
            
            # 执行所有任务
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # 分析结果
            total_requests = len(results)
            successful_requests = sum(1 for r in results if r["success"])
            failed_requests = total_requests - successful_requests
            
            response_times = [r["response_time"] for r in results if r["success"]]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                max_response_time = max(response_times)
            else:
                avg_response_time = median_response_time = p95_response_time = max_response_time = 0
            
            total_time = end_time - start_time
            requests_per_second = total_requests / total_time
            
            # 性能断言
            assert successful_requests / total_requests >= 0.95, f"Success rate too low: {successful_requests}/{total_requests}"
            assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time}s"
            assert p95_response_time < 2.0, f"95th percentile response time too high: {p95_response_time}s"
            assert requests_per_second > 100, f"Throughput too low: {requests_per_second} req/s"
            
            # 打印性能报告
            print(f"\n=== Load Test Results ===")
            print(f"Total Requests: {total_requests}")
            print(f"Successful Requests: {successful_requests}")
            print(f"Failed Requests: {failed_requests}")
            print(f"Success Rate: {successful_requests/total_requests*100:.2f}%")
            print(f"Total Time: {total_time:.2f}s")
            print(f"Requests/Second: {requests_per_second:.2f}")
            print(f"Average Response Time: {avg_response_time:.3f}s")
            print(f"Median Response Time: {median_response_time:.3f}s")
            print(f"95th Percentile Response Time: {p95_response_time:.3f}s")
            print(f"Max Response Time: {max_response_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool(self, base_url, auth_token):
        """测试数据库连接池性能"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        concurrent_requests = 100
        
        async with aiohttp.ClientSession() as session:
            # 创建大量并发数据库查询
            tasks = []
            for i in range(concurrent_requests):
                task = self.make_request(
                    session,
                    f"{base_url}/api/v1/projects/",
                    headers=headers
                )
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # 验证所有请求都成功
            successful_requests = sum(1 for r in results if r["success"])
            
            assert successful_requests == concurrent_requests, \
                f"Database connection pool failed: {successful_requests}/{concurrent_requests}"
            
            total_time = end_time - start_time
            print(f"\n=== Database Pool Test ===")
            print(f"Concurrent Requests: {concurrent_requests}")
            print(f"Successful Requests: {successful_requests}")
            print(f"Total Time: {total_time:.2f}s")
            print(f"Requests/Second: {concurrent_requests/total_time:.2f}")
```

### 压力测试

```python
# tests/test_performance/test_stress.py
import pytest
import asyncio
import aiohttp
import time
import psutil
import threading
from dataclasses import dataclass
from typing import List

@dataclass
class StressTestResult:
    """压力测试结果"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    max_response_time: float
    requests_per_second: float
    cpu_usage: float
    memory_usage: float
    errors: List[str]

class TestStressPerformance:
    """压力性能测试"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
    
    @pytest.mark.asyncio
    async def test_gradual_load_increase(self, base_url, auth_token):
        """测试逐步增加负载"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        load_levels = [10, 25, 50, 100, 200, 500]  # 并发用户数
        
        results = []
        
        for concurrent_users in load_levels:
            print(f"\nTesting with {concurrent_users} concurrent users...")
            
            # 启动系统监控
            self.system_monitor.start()
            
            try:
                result = await self.run_stress_test(
                    base_url, headers, concurrent_users, requests_per_user=5
                )
                results.append((concurrent_users, result))
                
                # 检查系统是否还能正常响应
                if result.successful_requests / result.total_requests < 0.8:
                    print(f"System degraded at {concurrent_users} users")
                    break
                    
                # 等待系统恢复
                await asyncio.sleep(2)
                
            finally:
                self.system_monitor.stop()
        
        # 分析结果
        self.analyze_stress_results(results)
    
    async def run_stress_test(self, base_url: str, headers: dict, 
                            concurrent_users: int, requests_per_user: int) -> StressTestResult:
        """运行压力测试"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 创建并发任务
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.make_stress_request(session, base_url, headers)
                    tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # 处理结果
            successful_results = []
            failed_results = []
            errors = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append(result)
                    errors.append(str(result))
                elif result["success"]:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
                    if "error" in result:
                        errors.append(result["error"])
            
            total_requests = len(results)
            successful_requests = len(successful_results)
            failed_requests = len(failed_results)
            
            if successful_results:
                response_times = [r["response_time"] for r in successful_results]
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = 0
                max_response_time = 0
            
            total_time = end_time - start_time
            requests_per_second = total_requests / total_time if total_time > 0 else 0
            
            # 获取系统资源使用情况
            cpu_usage = self.system_monitor.get_avg_cpu_usage()
            memory_usage = self.system_monitor.get_avg_memory_usage()
            
            return StressTestResult(
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time=avg_response_time,
                max_response_time=max_response_time,
                requests_per_second=requests_per_second,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                errors=errors
            )
    
    async def make_stress_request(self, session, base_url, headers):
        """发送压力测试请求"""
        start_time = time.time()
        
        try:
            # 随机选择不同的端点进行测试
            endpoints = [
                "/api/v1/auth/me",
                "/api/v1/projects/",
                "/api/v1/documents/",
                "/api/v1/health"
            ]
            
            import random
            endpoint = random.choice(endpoints)
            
            async with session.get(f"{base_url}{endpoint}", headers=headers) as response:
                await response.text()
                end_time = time.time()
                
                return {
                    "status": response.status,
                    "response_time": end_time - start_time,
                    "success": 200 <= response.status < 300,
                    "endpoint": endpoint
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "status": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
                "endpoint": "unknown"
            }
    
    def analyze_stress_results(self, results: List[tuple]):
        """分析压力测试结果"""
        print("\n=== Stress Test Analysis ===")
        print("Load Level | Success Rate | Avg Response | RPS | CPU% | Memory%")
        print("-" * 70)
        
        for concurrent_users, result in results:
            success_rate = result.successful_requests / result.total_requests * 100
            print(f"{concurrent_users:9d} | {success_rate:11.1f}% | {result.avg_response_time:11.3f}s | "
                  f"{result.requests_per_second:3.0f} | {result.cpu_usage:4.1f}% | {result.memory_usage:6.1f}%")
        
        # 找出性能拐点
        for i, (users, result) in enumerate(results):
            if result.successful_requests / result.total_requests < 0.95:
                print(f"\nPerformance degradation detected at {users} concurrent users")
                break
        else:
            print(f"\nSystem handled up to {results[-1][0]} concurrent users successfully")

class SystemMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.cpu_readings = []
        self.memory_readings = []
        self.monitor_thread = None
    
    def start(self):
        """开始监控"""
        self.monitoring = True
        self.cpu_readings = []
        self.memory_readings = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            self.cpu_readings.append(psutil.cpu_percent())
            self.memory_readings.append(psutil.virtual_memory().percent)
            time.sleep(0.5)
    
    def get_avg_cpu_usage(self) -> float:
        """获取平均 CPU 使用率"""
        return sum(self.cpu_readings) / len(self.cpu_readings) if self.cpu_readings else 0
    
    def get_avg_memory_usage(self) -> float:
        """获取平均内存使用率"""
        return sum(self.memory_readings) / len(self.memory_readings) if self.memory_readings else 0
```

## 安全测试

### 认证安全测试

```python
# tests/test_security/test_auth_security.py
import pytest
import jwt
from datetime import datetime, timedelta

class TestAuthSecurity:
    """认证安全测试"""
    
    def test_password_strength_validation(self, client):
        """测试密码强度验证"""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "12345678",
            "password123"
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "password": weak_password
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 400
            assert "password" in response.json()["detail"].lower()
    
    def test_jwt_token_expiration(self, client, test_user):
        """测试 JWT 令牌过期"""
        # 登录获取令牌
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        token = response.json()["access_token"]
        
        # 验证令牌有效
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        # 模拟令牌过期
        from app.config import get_settings
        settings = get_settings()
        
        # 创建过期令牌
        expired_payload = {
            "sub": str(test_user.id),
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm="HS256")
        
        # 使用过期令牌
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=expired_headers)
        assert response.status_code == 401
    
    def test_jwt_token_tampering(self, client, test_user):
        """测试 JWT 令牌篡改"""
        # 获取有效令牌
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        token = response.json()["access_token"]
        
        # 篡改令牌
        tampered_token = token[:-5] + "XXXXX"  # 修改签名部分
        
        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_brute_force_protection(self, client, test_user):
        """测试暴力破解保护"""
        # 多次错误登录尝试
        for i in range(6):  # 超过限制次数
            login_data = {
                "username": test_user.username,
                "password": "wrongpassword"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            if i < 5:
                assert response.status_code == 401
            else:
                # 第6次应该被限制
                assert response.status_code == 429  # Too Many Requests
                assert "rate limit" in response.json()["detail"].lower()
    
    def test_session_fixation_protection(self, client):
        """测试会话固定攻击保护"""
        # 登录前获取会话
        response1 = client.get("/api/v1/health")
        session_before = response1.cookies.get("session_id")
        
        # 登录
        user_data = {
            "username": "sessiontest",
            "email": "session@example.com",
            "full_name": "Session Test",
            "password": "securepassword123"
        }
        
        client.post("/api/v1/auth/register", json=user_data)
        
        login_data = {
            "username": "sessiontest",
            "password": "securepassword123"
        }
        
        response2 = client.post("/api/v1/auth/login", json=login_data)
        session_after = response2.cookies.get("session_id")
        
        # 会话 ID 应该在登录后改变
        assert session_before != session_after