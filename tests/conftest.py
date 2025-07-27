import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
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
from app.services.cache_service import cache_service

# 在测试中禁用缓存
settings.CACHE_ENABLED = False
cache_service.is_enabled = False

# 测试数据库配置
import tempfile
import os
import uuid


@pytest.fixture(scope="function")
def db():
    """创建测试数据库"""
    # 为每个测试创建独立的内存数据库
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # 创建表
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
        # 清理数据库
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


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
        db.refresh(user)  # 确保对象与会话保持连接
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
        db.refresh(project)  # 确保对象与会话保持连接
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
        # 确保关联对象也被刷新
        db.refresh(test_project)
        db.refresh(test_user)
        return document
    except Exception as e:
        db.rollback()
        raise e


@pytest.fixture(scope="function")
def auth_user(db):
    """创建认证用户"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user_data = schemas.UserCreate(
        username=f"testuser_{unique_id}",
        password="testpassword123"
    )
    user = crud.user.create(db=db, obj_in=user_data)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(auth_user):
    """获取认证头"""
    from app.core.security import create_access_token
    access_token = create_access_token(subject=auth_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_client(db, auth_user):
    """创建带认证的测试客户端"""
    from app.api.deps import get_current_user, get_current_user_id
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    def override_get_current_user():
        return auth_user
    
    def override_get_current_user_id():
        return auth_user.id
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()