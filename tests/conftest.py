import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
from app.db.base import Base
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app import crud, schemas

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """创建测试数据库"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """创建测试用户"""
    try:
        user_data = schemas.UserCreate(
            username="testuser",
            password="testpassword123"
        )
        user = crud.user.create(db=db, obj_in=user_data)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        raise e


@pytest.fixture(scope="function")
def test_project(db, test_user):
    """创建测试项目"""
    try:
        project_data = schemas.ProjectCreate(
            name="测试项目",
            description="这是一个测试项目",
            project_code="TEST-2024-001",
            project_type="货物"
        )
        project = crud.project.create_with_owner(
            db=db, obj_in=project_data, owner_id=test_user.id
        )
        db.commit()
        return project
    except Exception as e:
        db.rollback()
        raise e


@pytest.fixture(scope="function")
def test_document(db, test_project, test_user):
    """创建测试文档"""
    try:
        from datetime import datetime
        document = Document(
            filename="test_document.pdf",
            original_filename="test_document.pdf",
            file_path="/uploads/test_document.pdf",
            file_size=1024,
            file_type="pdf",
            mime_type="application/pdf",
            project_id=test_project.id,
            uploader_id=test_user.id,
            document_category="technical",
            document_type="技术文档",
            status="uploaded"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except Exception as e:
        db.rollback()
        raise e


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}