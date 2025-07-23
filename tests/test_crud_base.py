import pytest
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from app.crud.base import CRUDBase
from app.crud.crud_project import project as crud_project
from app.models.project import Project
from app.models.document import Document
from app.schemas.project import ProjectCreate, ProjectUpdate


class TestCRUDBase:
    """CRUD基础类测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.crud_project = crud_project
        self.crud_document = CRUDBase(Document)
    
    def test_get_existing_item(self, db: Session, test_project: Project):
        """测试获取存在的项目"""
        result = self.crud_project.get(db, id=test_project.id)
        assert result is not None
        assert result.id == test_project.id
        assert result.name == test_project.name
    
    def test_get_nonexistent_item(self, db: Session):
        """测试获取不存在的项目"""
        result = self.crud_project.get(db, id=999)
        assert result is None
    
    def test_get_multi_no_items(self, db: Session):
        """测试获取多个项目（无数据）"""
        # 清空数据库
        db.query(Project).delete()
        db.commit()
        
        result = self.crud_project.get_multi(db)
        assert result == []
    
    def test_get_multi_with_items(self, db: Session, test_user):
        """测试获取多个项目（有数据）"""
        # 创建多个项目
        projects = []
        for i in range(3):
            project_data = {
                "name": f"Test Project {i}", 
                "description": f"Description {i}",
                "project_code": f"MULTI-2024-{i:03d}",
                "project_type": "货物"
            }
            project = self.crud_project.create_with_owner(db, obj_in=project_data, owner_id=test_user.id)
            projects.append(project)
        
        result = self.crud_project.get_multi(db)
        assert len(result) >= 3
        
        # 验证项目名称
        project_names = [p.name for p in result]
        for project in projects:
            assert project.name in project_names
    
    def test_get_multi_with_skip_and_limit(self, db: Session, test_user):
        """测试获取多个项目（分页）"""
        # 创建5个项目
        projects = []
        for i in range(5):
            project_data = {
                "name": f"Paginated Project {i}", 
                "description": f"Description {i}",
                "project_code": f"PAGE-2024-{i:03d}",
                "project_type": "货物"
            }
            project = self.crud_project.create_with_owner(db, obj_in=project_data, owner_id=test_user.id)
            projects.append(project)
        
        # 测试跳过前2个，限制3个
        result = self.crud_project.get_multi(db, skip=2, limit=3)
        assert len(result) <= 3
        
        # 测试只限制数量
        result_limited = self.crud_project.get_multi(db, limit=2)
        assert len(result_limited) <= 2
    
    def test_create_item(self, db: Session, test_user):
        """测试创建项目"""
        project_data = ProjectCreate(
            name="New Test Project", 
            description="New Description",
            project_code="NEW-2024-001",
            project_type="货物"
        )
        
        result = self.crud_project.create_with_owner(db, obj_in=project_data, owner_id=test_user.id)
        
        assert result.id is not None
        assert result.name == "New Test Project"
        assert result.description == "New Description"
        
        # 验证数据库中确实创建了
        db_project = db.query(Project).filter(Project.id == result.id).first()
        assert db_project is not None
        assert db_project.name == "New Test Project"
    
    def test_create_item_with_dict(self, db: Session, test_user):
        """测试使用字典创建项目"""
        project_data = {
            "name": "Dict Project", 
            "description": "Dict Description",
            "project_code": "DICT-2024-001",
            "project_type": "货物"
        }
        
        result = self.crud_project.create_with_owner(db, obj_in=project_data, owner_id=test_user.id)
        
        assert result.id is not None
        assert result.name == "Dict Project"
        assert result.description == "Dict Description"
    
    def test_update_existing_item(self, db: Session, test_project: Project):
        """测试更新存在的项目"""
        original_description = test_project.description
        update_data = ProjectUpdate(name="Updated Project Name")
        
        result = self.crud_project.update(db, db_obj=test_project, obj_in=update_data)
        
        assert result.id == test_project.id
        assert result.name == "Updated Project Name"
        assert result.description == original_description  # 未更新的字段保持不变
        
        # 验证数据库中的更新
        db.refresh(test_project)
        assert test_project.name == "Updated Project Name"
    
    def test_update_with_dict(self, db: Session, test_project: Project):
        """测试使用字典更新项目"""
        update_data = {"name": "Dict Updated Name", "description": "Dict Updated Description"}
        
        result = self.crud_project.update(db, db_obj=test_project, obj_in=update_data)
        
        assert result.name == "Dict Updated Name"
        assert result.description == "Dict Updated Description"
        
        # 验证数据库中的更新
        db.refresh(test_project)
        assert test_project.name == "Dict Updated Name"
        assert test_project.description == "Dict Updated Description"
    
    def test_update_partial_fields(self, db: Session, test_project: Project):
        """测试部分字段更新"""
        original_description = test_project.description
        update_data = {"name": "Partially Updated"}
        
        result = self.crud_project.update(db, db_obj=test_project, obj_in=update_data)
        
        assert result.name == "Partially Updated"
        assert result.description == original_description  # 未更新的字段保持不变
    
    def test_remove_existing_item(self, db: Session, test_project: Project):
        """测试删除存在的项目"""
        project_id = test_project.id
        
        result = self.crud_project.remove(db, id=project_id)
        
        assert result.id == project_id
        
        # 验证数据库中已删除
        deleted_project = db.query(Project).filter(Project.id == project_id).first()
        assert deleted_project is None
    
    def test_remove_nonexistent_item(self, db: Session):
        """测试删除不存在的项目"""
        result = self.crud_project.remove(db, id=999)
        assert result is None
    
    def test_crud_with_different_model(self, db: Session, test_project: Project, test_user):
        """测试CRUD基础类与不同模型的使用"""
        # 创建文档
        document_data = {
            "filename": "test.pdf",
            "original_filename": "test.pdf",
            "file_path": "/test/test.pdf",
            "file_size": 1024,
            "file_type": "pdf",
            "document_category": "技术文档",
            "project_id": test_project.id,
            "uploader_id": test_user.id
        }
        
        # 创建文档
        created_doc = self.crud_document.create(db, obj_in=document_data)
        assert created_doc.filename == "test.pdf"
        assert created_doc.project_id == test_project.id
        
        # 获取文档
        retrieved_doc = self.crud_document.get(db, id=created_doc.id)
        assert retrieved_doc is not None
        assert retrieved_doc.filename == "test.pdf"
        
        # 更新文档
        update_data = {"filename": "updated.pdf"}
        updated_doc = self.crud_document.update(db, db_obj=retrieved_doc, obj_in=update_data)
        assert updated_doc.filename == "updated.pdf"
        
        # 删除文档
        deleted_doc = self.crud_document.remove(db, id=created_doc.id)
        assert deleted_doc.id == created_doc.id
        
        # 验证删除
        assert self.crud_document.get(db, id=created_doc.id) is None
    
    def test_get_multi_empty_result(self, db: Session):
        """测试获取多个项目返回空结果"""
        # 确保没有文档
        db.query(Document).delete()
        db.commit()
        
        result = self.crud_document.get_multi(db)
        assert result == []
        assert isinstance(result, list)
    
    def test_create_with_none_values(self, db: Session, test_user):
        """测试创建时处理None值"""
        project_data = {
            "name": "Test Project", 
            "description": None,
            "project_code": "NONE-2024-001",
            "project_type": "货物"
        }
        
        result = self.crud_project.create_with_owner(db, obj_in=project_data, owner_id=test_user.id)
        
        assert result.name == "Test Project"
        assert result.description is None
    
    def test_update_with_none_values(self, db: Session, test_project: Project):
        """测试更新时处理None值"""
        # 设置初始描述
        test_project.description = "Initial Description"
        db.commit()
        
        # 更新为None（应该被跳过）
        update_data = {"description": None}
        result = self.crud_project.update(db, db_obj=test_project, obj_in=update_data)
        
        # None值应该被跳过，保持原值
        assert result.description == "Initial Description"
    
    def test_update_with_empty_dict(self, db: Session, test_project: Project):
        """测试使用空字典更新"""
        original_name = test_project.name
        original_description = test_project.description
        
        result = self.crud_project.update(db, db_obj=test_project, obj_in={})
        
        # 空字典更新不应该改变任何值
        assert result.name == original_name
        assert result.description == original_description
    
    def test_model_attribute_access(self, db: Session):
        """测试模型属性访问"""
        assert self.crud_project.model == Project
        assert self.crud_document.model == Document
    
    def test_get_with_invalid_id_type(self, db: Session):
        """测试使用无效ID类型获取项目"""
        # 测试字符串ID（应该能正常工作或抛出适当异常）
        try:
            result = self.crud_project.get(db, id="invalid")
            # 如果没有抛出异常，结果应该是None
            assert result is None
        except (ValueError, TypeError):
            # 如果抛出异常，这也是可接受的行为
            pass
    
    def test_remove_with_invalid_id(self, db: Session):
        """测试使用无效ID删除项目"""
        result = self.crud_project.remove(db, id=-1)
        assert result is None
        
        result = self.crud_project.remove(db, id=0)
        assert result is None