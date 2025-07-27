from sqlalchemy.orm import Session
from app import crud, models, schemas
from tests.utils.utils import random_lower_string, random_choice


def create_random_project(db: Session, *, owner_id: int) -> models.Project:
    """创建随机测试项目"""
    name = random_lower_string()
    description = random_lower_string()
    project_code = f"PRJ-{random_lower_string()[:8].upper()}"
    
    project_in = schemas.ProjectCreate(
        name=name,
        description=description,
        project_code=project_code
    )
    
    project = crud.project.create_with_owner(
        db=db, obj_in=project_in, owner_id=owner_id
    )
    return project


def create_project_with_status(
    db: Session, *, owner_id: int, status: str = "active"
) -> models.Project:
    """创建指定状态的项目"""
    name = random_lower_string()
    description = random_lower_string()
    project_code = f"PRJ-{random_lower_string()[:8].upper()}"
    
    project_in = schemas.ProjectCreate(
        name=name,
        description=description,
        project_code=project_code,
        status=status
    )
    
    project = crud.project.create_with_owner(
        db=db, obj_in=project_in, owner_id=owner_id
    )
    return project


def create_inactive_project(db: Session, *, owner_id: int) -> models.Project:
    """创建非活跃项目"""
    project = create_random_project(db, owner_id=owner_id)
    # 停用项目
    crud.project.deactivate(db=db, project_id=project.id)
    # 重新获取更新后的项目
    return crud.project.get(db=db, id=project.id)


def create_completed_project(db: Session, *, owner_id: int) -> models.Project:
    """创建已完成项目"""
    project = create_random_project(db, owner_id=owner_id)
    # 更新状态为已完成
    crud.project.update_status(db=db, project_id=project.id, status="completed")
    # 重新获取更新后的项目
    return crud.project.get(db=db, id=project.id)


def create_project_with_name(
    db: Session, *, owner_id: int, name: str
) -> models.Project:
    """创建指定名称的项目"""
    description = random_lower_string()
    project_code = f"PRJ-{random_lower_string()[:8].upper()}"
    
    project_in = schemas.ProjectCreate(
        name=name,
        description=description,
        project_code=project_code,
        status="active"
    )
    
    project = crud.project.create_with_owner(
        db=db, obj_in=project_in, owner_id=owner_id
    )
    return project


def create_multiple_projects(
    db: Session, *, owner_id: int, count: int = 3
) -> list[models.Project]:
    """创建多个测试项目"""
    projects = []
    for _ in range(count):
        project = create_random_project(db, owner_id=owner_id)
        projects.append(project)
    return projects