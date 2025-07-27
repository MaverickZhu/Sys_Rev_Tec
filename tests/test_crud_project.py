import pytest
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core.config import settings
from tests.utils.utils import random_lower_string
from tests.utils.user import create_random_user
from tests.utils.project import create_random_project


class TestCRUDProject:
    def test_create_project(self, db: Session) -> None:
        """测试创建项目"""
        user = create_random_user(db)
        
        name = random_lower_string()
        description = random_lower_string()
        
        project_in = schemas.ProjectCreate(
            name=name,
            description=description,
            project_code=f"PRJ-{name[:8].upper()}"
        )
        
        project = crud.project.create_with_owner(
            db=db, obj_in=project_in, owner_id=user.id
        )
        
        assert project.name == name
        assert project.description == description
        assert project.owner_id == user.id
        assert project.status == "planning"
        assert project.is_active is True

    def test_get_project(self, db: Session) -> None:
        """测试获取项目"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        stored_project = crud.project.get(db=db, id=project.id)
        assert stored_project
        assert stored_project.id == project.id
        assert stored_project.name == project.name
        assert stored_project.owner_id == user.id

    def test_update_project(self, db: Session) -> None:
        """测试更新项目"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        new_name = random_lower_string()
        new_description = random_lower_string()
        
        project_update = schemas.ProjectUpdate(
            name=new_name,
            description=new_description,
            project_code=project.project_code
        )
        
        updated_project = crud.project.update(
            db=db, db_obj=project, obj_in=project_update
        )
        
        assert updated_project.id == project.id
        assert updated_project.name == new_name
        assert updated_project.description == new_description
        assert updated_project.owner_id == user.id

    def test_delete_project(self, db: Session) -> None:
        """测试删除项目"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        project_id = project.id
        crud.project.remove(db=db, id=project_id)
        
        deleted_project = crud.project.get(db=db, id=project_id)
        assert deleted_project is None

    def test_get_multi_by_owner(self, db: Session) -> None:
        """测试按所有者获取多个项目"""
        user = create_random_user(db)
        
        # 创建多个项目
        projects = []
        for _ in range(3):
            project = create_random_project(db, owner_id=user.id)
            projects.append(project)
        
        # 创建其他用户的项目
        other_user = create_random_user(db)
        create_random_project(db, owner_id=other_user.id)
        
        stored_projects = crud.project.get_multi_by_owner(
            db=db, owner_id=user.id
        )
        
        assert len(stored_projects) >= 3
        for project in stored_projects:
            assert project.owner_id == user.id

    def test_get_by_status(self, db: Session) -> None:
        """测试按状态获取项目"""
        user = create_random_user(db)
        
        # 创建不同状态的项目
        planning_project = create_random_project(db, owner_id=user.id)
        
        # 更新一个项目状态为completed
        completed_project = create_random_project(db, owner_id=user.id)
        crud.project.update(
            db=db, 
            db_obj=completed_project, 
            obj_in=schemas.ProjectUpdate(status="completed", project_code=completed_project.project_code)
        )
        
        # 获取planning状态的项目
        planning_projects = crud.project.get_by_status(
            db=db, status="planning"
        )
        
        # 获取completed状态的项目
        completed_projects = crud.project.get_by_status(
            db=db, status="completed"
        )
        
        # 验证结果
        planning_ids = [proj.id for proj in planning_projects]
        completed_ids = [proj.id for proj in completed_projects]
        
        assert planning_project.id in planning_ids
        assert completed_project.id in completed_ids
        assert completed_project.id not in planning_ids
        assert planning_project.id not in completed_ids

    def test_update_status(self, db: Session) -> None:
        """测试更新项目状态"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 初始状态应该是planning
        assert project.status == "planning"
        
        # 更新状态为completed
        updated_project = crud.project.update_status(
            db=db, project_id=project.id, status="completed"
        )
        
        assert updated_project.status == "completed"
        assert updated_project.id == project.id
        
        # 验证数据库中的状态也已更新
        stored_project = crud.project.get(db=db, id=project.id)
        assert stored_project.status == "completed"

    def test_activate_deactivate_project(self, db: Session) -> None:
        """测试激活和停用项目"""
        user = create_random_user(db)
        project = create_random_project(db, owner_id=user.id)
        
        # 初始状态应该是激活的
        assert project.is_active is True
        
        # 停用项目
        deactivated_project = crud.project.deactivate(
            db=db, project_id=project.id
        )
        
        assert deactivated_project.is_active is False
        assert deactivated_project.id == project.id
        
        # 重新激活项目
        activated_project = crud.project.activate(
            db=db, project_id=project.id
        )
        
        assert activated_project.is_active is True
        assert activated_project.id == project.id

    def test_get_active_projects(self, db: Session) -> None:
        """测试获取活跃项目"""
        user = create_random_user(db)
        
        # 创建活跃项目
        active_project = create_random_project(db, owner_id=user.id)
        
        # 创建并停用项目
        inactive_project = create_random_project(db, owner_id=user.id)
        crud.project.deactivate(db=db, project_id=inactive_project.id)
        
        # 获取活跃项目
        active_projects = crud.project.get_active_projects(db=db)
        
        # 验证结果
        active_ids = [proj.id for proj in active_projects]
        
        assert active_project.id in active_ids
        assert inactive_project.id not in active_ids
        
        for project in active_projects:
            assert project.is_active is True

    def test_search_projects(self, db: Session) -> None:
        """测试搜索项目"""
        user = create_random_user(db)
        
        # 创建具有特定名称的项目
        search_term = "test_search_project"
        project_in = schemas.ProjectCreate(
            name=f"{search_term}_name",
            description="test description",
            project_code=f"PRJ-{search_term[:8].upper()}"
        )
        
        project = crud.project.create_with_owner(
            db=db, obj_in=project_in, owner_id=user.id
        )
        
        # 创建其他项目
        create_random_project(db, owner_id=user.id)
        
        # 搜索项目
        search_results = crud.project.search(
            db=db, query=search_term
        )
        
        # 验证搜索结果
        found_project = None
        for proj in search_results:
            if proj.id == project.id:
                found_project = proj
                break
        
        assert found_project is not None
        assert search_term in found_project.name

    def test_get_projects_with_pagination(self, db: Session) -> None:
        """测试分页获取项目"""
        user = create_random_user(db)
        
        # 创建5个项目
        projects = []
        for i in range(5):
            project = create_random_project(db, owner_id=user.id)
            projects.append(project)
        
        # 测试分页
        page1 = crud.project.get_multi(db=db, skip=0, limit=3)
        page2 = crud.project.get_multi(db=db, skip=3, limit=3)
        
        assert len(page1) == 3
        assert len(page2) >= 2  # 可能包含其他测试创建的项目
        
        # 确保没有重复
        page1_ids = [proj.id for proj in page1]
        page2_ids = [proj.id for proj in page2]
        
        # 检查前3个项目不在第二页
        for proj_id in page1_ids:
            assert proj_id not in page2_ids

    def test_get_project_statistics(self, db: Session) -> None:
        """测试获取项目统计信息"""
        user = create_random_user(db)
        
        # 创建不同状态的项目
        active_project1 = create_random_project(db, owner_id=user.id)
        active_project2 = create_random_project(db, owner_id=user.id)
        
        completed_project = create_random_project(db, owner_id=user.id)
        crud.project.update_status(
            db=db, project_id=completed_project.id, status="completed"
        )
        
        # 停用一个项目
        crud.project.deactivate(db=db, project_id=active_project2.id)
        
        stats = crud.project.get_statistics(db=db)
        
        assert "total_count" in stats
        assert "active_count" in stats
        assert "completed_count" in stats
        assert "inactive_count" in stats
        
        assert stats["total_count"] >= 3
        assert stats["active_count"] >= 1
        assert stats["completed_count"] >= 1
        assert stats["inactive_count"] >= 1

    def test_get_recent_projects(self, db: Session) -> None:
        """测试获取最近的项目"""
        user = create_random_user(db)
        
        # 创建多个项目
        projects = []
        for i in range(3):
            project = create_random_project(db, owner_id=user.id)
            projects.append(project)
            # 稍等一下确保时间戳不同
            import time
            time.sleep(0.01)
        
        # 获取最近的2个项目
        recent_projects = crud.project.get_recent_projects(db=db, limit=2)
        
        assert len(recent_projects) >= 2
        
        # 验证项目按创建时间降序排列
        for i in range(len(recent_projects) - 1):
            assert recent_projects[i].created_at >= recent_projects[i + 1].created_at

    def test_get_projects_by_date_range(self, db: Session) -> None:
        """测试按日期范围获取项目"""
        from datetime import datetime, timedelta
        
        user = create_random_user(db)
        
        # 创建项目
        project = create_random_project(db, owner_id=user.id)
        
        # 设置日期范围（今天前后一天）
        today = datetime.utcnow()
        start_date = today - timedelta(days=1)
        end_date = today + timedelta(days=1)
        
        projects_in_range = crud.project.get_projects_by_date_range(
            db=db, start_date=start_date, end_date=end_date
        )
        
        # 验证项目在日期范围内
        project_ids = [proj.id for proj in projects_in_range]
        assert project.id in project_ids
        
        for proj in projects_in_range:
            assert start_date <= proj.created_at <= end_date

    def test_get_projects_by_owner_count(self, db: Session) -> None:
        """测试获取用户项目数量"""
        user = create_random_user(db)
        
        # 创建项目
        create_random_project(db, owner_id=user.id)
        create_random_project(db, owner_id=user.id)
        
        # 获取用户项目列表并计算数量
        projects = crud.project.get_by_owner(db, owner_id=user.id)
        assert len(projects) == 2

    def test_update_multiple_projects_status(self, db: Session) -> None:
        """测试更新多个项目状态"""
        user = create_random_user(db)
        
        # 创建多个项目
        projects = []
        for _ in range(3):
            project = create_random_project(db, owner_id=user.id)
            projects.append(project)
        
        # 逐个更新状态
        for project in projects:
            updated_project = crud.project.update(
                db=db, db_obj=project, obj_in=schemas.ProjectUpdate(status="completed", project_code=project.project_code)
            )
            assert updated_project.status == "completed"