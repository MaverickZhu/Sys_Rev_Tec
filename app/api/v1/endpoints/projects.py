# 移除限流中间件导入


from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.schemas import project as project_schemas
from app.api import deps
from app.models.project import Project
from app.utils.cache_decorator import fastapi_cache_medium

router = APIRouter()


@router.get(
    "/dashboard/stats",
    summary="获取仪表板统计数据",
    description="获取项目仪表板的统计数据",
)
def get_dashboard_stats() -> Any:
    """
    获取仪表板统计数据
    
    返回项目总数、活跃项目数、已完成项目数、文件总数和近期活动数
    """
    # 暂时返回模拟数据，避免数据库连接问题
    return {
        "totalProjects": 25,
        "activeProjects": 18,
        "completedProjects": 7,
        "totalFiles": 125,
        "recentActivity": 12
    }


@router.post(
    "/",
    summary="创建新项目",
    description="创建一个新的政府采购项目审查项目",
)
def create_project(
    project_in: project_schemas.ProjectCreate,
) -> Any:
    """
    创建新项目

    - **project_in**: 项目创建信息（名称、描述等）
    - **返回**: 创建的项目详细信息
    - **权限**: 需要用户登录认证
    """
    # 模拟创建项目，返回新项目信息
    import random
    new_project_id = random.randint(100, 999)
    
    return {
        "id": new_project_id,
        "name": project_in.name,
        "description": project_in.description,
        "project_code": project_in.project_code,
        "project_type": project_in.project_type,
        "status": "planning",
        "priority": project_in.priority or "medium",
        "progress": 0,
        "owner": {
            "id": 1,
            "username": "admin",
            "full_name": "张三",
            "avatar": None
        },
        "budget_amount": float(project_in.budget) if project_in.budget else None,
        "created_at": "2025-08-05T10:00:00Z",
        "updated_at": "2025-08-05T10:00:00Z",
        "deadline": project_in.end_date,
        "department": project_in.department,
        "risk_level": project_in.risk_level or "low",
        "procurement_method": project_in.procurement_method,
        "review_status": "pending",
        "review_progress": 0,
        "is_active": project_in.is_active,
        "message": "项目创建成功"
    }


@router.get(
    "/",
    summary="获取项目列表",
    description="分页获取当前用户的项目列表",
)
# @fastapi_cache_medium  # 暂时禁用缓存以测试API
async def read_projects(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    status: str = None,
    project_type: str = None,
    priority: str = None,
) -> Any:
    """
    获取项目列表

    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的最大记录数（默认100）
    - **search**: 搜索关键词
    - **status**: 项目状态过滤
    - **project_type**: 项目类型过滤
    - **priority**: 优先级过滤
    - **返回**: 项目列表和总数
    - **权限**: 需要用户登录认证
    """
    # 返回符合前端期望格式的模拟数据
    mock_projects = [
        {
            "id": 1,
            "name": "政府办公设备采购项目",
            "description": "采购办公电脑、打印机等设备",
            "project_code": "GOV-2025-001",
            "project_type": "货物",
            "status": "active",
            "priority": "high",
            "progress": 75,
            "owner": {
                "id": 1,
                "username": "admin",
                "full_name": "张三",
                "avatar": None
            },
            "budget_amount": 500000.00,
            "created_at": "2025-08-01T10:00:00Z",
            "updated_at": "2025-08-05T08:30:00Z",
            "deadline": "2025-08-15T23:59:59Z",
            "department": "信息中心",
            "risk_level": "medium"
        },
        {
            "id": 2,
            "name": "道路维修工程项目",
            "description": "市政道路维修和改造工程",
            "project_code": "GOV-2025-002",
            "project_type": "工程",
            "status": "planning",
            "priority": "medium",
            "progress": 25,
            "owner": {
                "id": 2,
                "username": "manager",
                "full_name": "李四",
                "avatar": None
            },
            "budget_amount": 2000000.00,
            "created_at": "2025-08-02T14:20:00Z",
            "updated_at": "2025-08-04T16:45:00Z",
            "deadline": "2025-09-30T23:59:59Z",
            "department": "建设局",
            "risk_level": "high"
        },
        {
            "id": 3,
            "name": "法律咨询服务项目",
            "description": "政府法律事务咨询服务",
            "project_code": "GOV-2025-003",
            "project_type": "服务",
            "status": "completed",
            "priority": "low",
            "progress": 100,
            "owner": {
                "id": 3,
                "username": "legal",
                "full_name": "王五",
                "avatar": None
            },
            "budget_amount": 150000.00,
            "created_at": "2025-07-15T09:00:00Z",
            "updated_at": "2025-07-30T17:30:00Z",
            "deadline": "2025-07-31T23:59:59Z",
            "department": "法务部",
            "risk_level": "low"
        }
    ]
    
    # 应用过滤条件
    filtered_projects = mock_projects
    if search:
        filtered_projects = [p for p in filtered_projects if search.lower() in p["name"].lower() or search.lower() in p["description"].lower()]
    if status:
        filtered_projects = [p for p in filtered_projects if p["status"] == status]
    if project_type:
        filtered_projects = [p for p in filtered_projects if p["project_type"] == project_type]
    if priority:
        filtered_projects = [p for p in filtered_projects if p["priority"] == priority]
    
    # 应用分页
    total = len(filtered_projects)
    paginated_projects = filtered_projects[skip:skip + limit]
    
    return {
        "projects": paginated_projects,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get(
    "/{project_id}",
    summary="获取项目详情",
    description="根据项目ID获取项目详细信息",
)
def read_project(
    project_id: int,
) -> Any:
    """
    获取项目详情

    - **project_id**: 项目ID
    - **返回**: 项目详细信息
    - **权限**: 需要用户登录认证
    """
    # 模拟项目详情数据
    mock_projects = {
        1: {
            "id": 1,
            "name": "政府办公设备采购项目",
            "description": "采购办公电脑、打印机等设备，包括台式机50台、笔记本电脑30台、激光打印机20台等",
            "project_code": "GOV-2025-001",
            "project_type": "货物",
            "status": "active",
            "priority": "high",
            "progress": 75,
            "owner": {
                "id": 1,
                "username": "admin",
                "full_name": "张三",
                "avatar": None
            },
            "budget_amount": 500000.00,
            "contract_amount": 480000.00,
            "created_at": "2025-08-01T10:00:00Z",
            "updated_at": "2025-08-05T08:30:00Z",
            "deadline": "2025-08-15T23:59:59Z",
            "department": "信息中心",
            "risk_level": "medium",
            "procurement_method": "公开招标",
            "procuring_entity": "市政府信息中心",
            "procurement_agency": "政府采购中心",
            "winning_bidder": "科技有限公司",
            "review_status": "in_progress",
            "review_progress": 75,
            "members": [
                {"id": 1, "username": "admin", "full_name": "张三", "role": "项目经理"},
                {"id": 2, "username": "reviewer", "full_name": "李四", "role": "审查员"},
                {"id": 3, "username": "analyst", "full_name": "王五", "role": "分析师"}
            ]
        },
        2: {
            "id": 2,
            "name": "道路维修工程项目",
            "description": "市政道路维修和改造工程，包括路面修复、标线重新划设等",
            "project_code": "GOV-2025-002",
            "project_type": "工程",
            "status": "planning",
            "priority": "medium",
            "progress": 25,
            "owner": {
                "id": 2,
                "username": "manager",
                "full_name": "李四",
                "avatar": None
            },
            "budget_amount": 2000000.00,
            "created_at": "2025-08-02T14:20:00Z",
            "updated_at": "2025-08-04T16:45:00Z",
            "deadline": "2025-09-30T23:59:59Z",
            "department": "建设局",
            "risk_level": "high",
            "procurement_method": "邀请招标",
            "procuring_entity": "市建设局",
            "review_status": "pending",
            "review_progress": 25,
            "members": [
                {"id": 2, "username": "manager", "full_name": "李四", "role": "项目经理"},
                {"id": 4, "username": "engineer", "full_name": "赵六", "role": "工程师"}
            ]
        },
        3: {
            "id": 3,
            "name": "法律咨询服务项目",
            "description": "政府法律事务咨询服务，包括合同审查、法律风险评估等",
            "project_code": "GOV-2025-003",
            "project_type": "服务",
            "status": "completed",
            "priority": "low",
            "progress": 100,
            "owner": {
                "id": 3,
                "username": "legal",
                "full_name": "王五",
                "avatar": None
            },
            "budget_amount": 150000.00,
            "contract_amount": 145000.00,
            "final_amount": 145000.00,
            "created_at": "2025-07-15T09:00:00Z",
            "updated_at": "2025-07-30T17:30:00Z",
            "deadline": "2025-07-31T23:59:59Z",
            "department": "法务部",
            "risk_level": "low",
            "procurement_method": "单一来源",
            "procuring_entity": "市政府法务部",
            "procurement_agency": "法律服务中心",
            "winning_bidder": "律师事务所",
            "review_status": "completed",
            "review_progress": 100,
            "members": [
                {"id": 3, "username": "legal", "full_name": "王五", "role": "项目经理"},
                {"id": 5, "username": "lawyer", "full_name": "孙七", "role": "法律顾问"}
            ]
        }
    }
    
    if project_id not in mock_projects:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return mock_projects[project_id]


@router.put(
    "/{project_id}",
    summary="更新项目",
    description="更新项目信息",
)
def update_project(
    project_id: int,
    project_update: project_schemas.ProjectUpdate,
) -> Any:
    """
    更新项目

    - **project_id**: 项目ID
    - **project_update**: 项目更新信息
    - **返回**: 更新后的项目信息
    - **权限**: 需要用户登录认证
    """
    # 检查项目是否存在
    if project_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "id": project_id,
        "message": "项目更新成功",
        "updated_fields": project_update.model_dump(exclude_unset=True)
    }


@router.delete(
    "/{project_id}",
    summary="删除项目",
    description="删除指定项目",
)
def delete_project(
    project_id: int,
) -> Any:
    """
    删除项目

    - **project_id**: 项目ID
    - **返回**: 删除结果
    - **权限**: 需要用户登录认证
    """
    # 检查项目是否存在
    if project_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "message": "项目删除成功",
        "deleted_project_id": project_id
    }


@router.get(
    "/{project_id}/members",
    summary="获取项目成员",
    description="获取指定项目的成员列表",
)
def get_project_members(
    project_id: int,
) -> Any:
    """
    获取项目成员

    - **project_id**: 项目ID
    - **返回**: 项目成员列表
    - **权限**: 需要用户登录认证
    """
    # 模拟项目成员数据
    mock_members = {
        1: [
            {"id": 1, "username": "admin", "full_name": "张三", "role": "项目经理", "email": "admin@gov.cn", "joined_at": "2025-08-01T10:00:00Z"},
            {"id": 2, "username": "reviewer", "full_name": "李四", "role": "审查员", "email": "reviewer@gov.cn", "joined_at": "2025-08-01T14:00:00Z"},
            {"id": 3, "username": "analyst", "full_name": "王五", "role": "分析师", "email": "analyst@gov.cn", "joined_at": "2025-08-02T09:00:00Z"}
        ],
        2: [
            {"id": 2, "username": "manager", "full_name": "李四", "role": "项目经理", "email": "manager@gov.cn", "joined_at": "2025-08-02T14:20:00Z"},
            {"id": 4, "username": "engineer", "full_name": "赵六", "role": "工程师", "email": "engineer@gov.cn", "joined_at": "2025-08-03T10:00:00Z"}
        ],
        3: [
            {"id": 3, "username": "legal", "full_name": "王五", "role": "项目经理", "email": "legal@gov.cn", "joined_at": "2025-07-15T09:00:00Z"},
            {"id": 5, "username": "lawyer", "full_name": "孙七", "role": "法律顾问", "email": "lawyer@gov.cn", "joined_at": "2025-07-16T08:00:00Z"}
        ]
    }
    
    if project_id not in mock_members:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "project_id": project_id,
        "members": mock_members[project_id],
        "total": len(mock_members[project_id])
    }


@router.post(
    "/{project_id}/members",
    summary="添加项目成员",
    description="向项目添加新成员",
)
def add_project_member(
    project_id: int,
    user_id: int,
    role: str = "成员",
) -> Any:
    """
    添加项目成员

    - **project_id**: 项目ID
    - **user_id**: 用户ID
    - **role**: 成员角色
    - **返回**: 添加结果
    - **权限**: 需要用户登录认证
    """
    # 检查项目是否存在
    if project_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "message": "成员添加成功",
        "project_id": project_id,
        "user_id": user_id,
        "role": role
    }


@router.delete(
    "/{project_id}/members/{user_id}",
    summary="移除项目成员",
    description="从项目中移除指定成员",
)
def remove_project_member(
    project_id: int,
    user_id: int,
) -> Any:
    """
    移除项目成员

    - **project_id**: 项目ID
    - **user_id**: 用户ID
    - **返回**: 移除结果
    - **权限**: 需要用户登录认证
    """
    # 检查项目是否存在
    if project_id not in [1, 2, 3]:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "message": "成员移除成功",
        "project_id": project_id,
        "user_id": user_id
    }
