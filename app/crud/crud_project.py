from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date

from app.crud.base import CRUDBase
from app.models.project import Project, Issue, ProjectComparison
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectInDB,
    IssueCreate, IssueUpdate, IssueInDB,
    ProjectComparisonCreate, ProjectComparisonUpdate
)
from app.models.user import User


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """项目CRUD操作"""
    
    def create_with_owner(self, db: Session, *, obj_in: Union[ProjectCreate, Dict[str, Any]], owner_id: int) -> Project:
        """创建项目并指定负责人"""
        if isinstance(obj_in, dict):
            obj_data = obj_in.copy()
        else:
            obj_data = obj_in.model_dump()
        # 如果obj_in中没有owner_id，则使用传入的owner_id
        if "owner_id" not in obj_data:
            obj_data["owner_id"] = owner_id
        db_obj = Project(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_code(self, db: Session, *, project_code: str) -> Optional[Project]:
        """根据项目编号获取项目"""
        return db.query(Project).filter(Project.project_code == project_code).first()
    
    def get_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """获取指定负责人的项目列表"""
        return (
            db.query(Project)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """根据状态获取项目列表"""
        return (
            db.query(Project)
            .filter(Project.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_review_status(
        self, db: Session, *, review_status: str, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """根据审查状态获取项目列表"""
        return (
            db.query(Project)
            .filter(Project.review_status == review_status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_department(
        self, db: Session, *, department: str, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """根据部门获取项目列表"""
        return (
            db.query(Project)
            .filter(Project.department == department)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_projects(
        self,
        db: Session,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """搜索项目"""
        search_filter = or_(
            Project.name.contains(query),
            Project.project_code.contains(query),
            Project.description.contains(query),
            Project.procuring_entity.contains(query)
        )
        return (
            db.query(Project)
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_projects_by_filters(
        self,
        db: Session,
        *,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Project]:
        """根据多个条件筛选项目"""
        query = db.query(Project)
        
        # 应用筛选条件
        if "status" in filters and filters["status"]:
            query = query.filter(Project.status == filters["status"])
        
        if "review_status" in filters and filters["review_status"]:
            query = query.filter(Project.review_status == filters["review_status"])
        
        if "project_type" in filters and filters["project_type"]:
            query = query.filter(Project.project_type == filters["project_type"])
        
        if "department" in filters and filters["department"]:
            query = query.filter(Project.department == filters["department"])
        
        if "owner_id" in filters and filters["owner_id"]:
            query = query.filter(Project.owner_id == filters["owner_id"])
        
        if "priority" in filters and filters["priority"]:
            query = query.filter(Project.priority == filters["priority"])
        
        if "risk_level" in filters and filters["risk_level"]:
            query = query.filter(Project.risk_level == filters["risk_level"])
        
        # 日期范围筛选
        if "start_date" in filters and filters["start_date"]:
            query = query.filter(Project.created_at >= filters["start_date"])
        
        if "end_date" in filters and filters["end_date"]:
            query = query.filter(Project.created_at <= filters["end_date"])
        
        # 预算范围筛选
        if "min_budget" in filters and filters["min_budget"]:
            query = query.filter(Project.budget_amount >= filters["min_budget"])
        
        if "max_budget" in filters and filters["max_budget"]:
            query = query.filter(Project.budget_amount <= filters["max_budget"])
        
        # 排序
        if hasattr(Project, order_by):
            order_column = getattr(Project, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def get_project_statistics(
        self, db: Session, *, owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取项目统计信息"""
        query = db.query(Project)
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        
        total_projects = query.count()
        
        # 按状态统计
        status_stats = {}
        for status in ["planning", "procurement", "implementation", "acceptance", "completed", "cancelled"]:
            count = query.filter(Project.status == status).count()
            status_stats[status] = count
        
        # 按审查状态统计
        review_stats = {}
        for review_status in ["pending", "in_progress", "completed", "rejected"]:
            count = query.filter(Project.review_status == review_status).count()
            review_stats[review_status] = count
        
        # 按风险等级统计
        risk_stats = {}
        for risk_level in ["low", "medium", "high", "critical"]:
            count = query.filter(Project.risk_level == risk_level).count()
            risk_stats[risk_level] = count
        
        return {
            "total_projects": total_projects,
            "status_distribution": status_stats,
            "review_status_distribution": review_stats,
            "risk_level_distribution": risk_stats
        }
    
    def update_review_status(
        self, db: Session, *, project_id: int, review_status: str, review_progress: int = None
    ) -> Optional[Project]:
        """更新项目审查状态"""
        project = self.get(db, id=project_id)
        if project:
            project.review_status = review_status
            if review_progress is not None:
                project.review_progress = review_progress
            project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(project)
        return project


class CRUDIssue(CRUDBase[Issue, IssueCreate, IssueUpdate]):
    """问题跟踪CRUD操作"""
    
    def create_with_project(
        self, db: Session, *, obj_in: IssueCreate, project_id: int, reporter_id: int
    ) -> Issue:
        """创建问题并关联项目"""
        obj_in_data = obj_in.model_dump()
        obj_in_data["project_id"] = project_id
        obj_in_data["reporter_id"] = reporter_id
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_project(
        self, db: Session, *, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Issue]:
        """获取项目的问题列表"""
        return (
            db.query(Issue)
            .filter(Issue.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_assignee(
        self, db: Session, *, assignee_id: int, skip: int = 0, limit: int = 100
    ) -> List[Issue]:
        """获取指定负责人的问题列表"""
        return (
            db.query(Issue)
            .filter(Issue.assignee_id == assignee_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[Issue]:
        """根据状态获取问题列表"""
        return (
            db.query(Issue)
            .filter(Issue.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_overdue_issues(self, db: Session) -> List[Issue]:
        """获取逾期问题"""
        now = datetime.utcnow()
        return (
            db.query(Issue)
            .filter(
                and_(
                    Issue.due_date < now,
                    Issue.status.in_(["open", "in_progress"])
                )
            )
            .all()
        )
    
    def assign_issue(
        self, db: Session, *, issue_id: int, assignee_id: int
    ) -> Optional[Issue]:
        """分配问题给指定用户"""
        issue = self.get(db, id=issue_id)
        if issue:
            issue.assignee_id = assignee_id
            issue.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(issue)
        return issue
    
    def resolve_issue(
        self, db: Session, *, issue_id: int, resolution: str
    ) -> Optional[Issue]:
        """解决问题"""
        issue = self.get(db, id=issue_id)
        if issue:
            issue.status = "resolved"
            issue.resolution = resolution
            issue.resolution_date = datetime.utcnow()
            issue.resolved_at = datetime.utcnow()
            issue.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(issue)
        return issue


class CRUDProjectComparison(CRUDBase[ProjectComparison, ProjectComparisonCreate, ProjectComparisonUpdate]):
    """项目比对CRUD操作"""
    
    def create_comparison(
        self,
        db: Session,
        *,
        project_id: int,
        compared_project_id: int,
        comparison_type: str,
        analyst_id: int
    ) -> ProjectComparison:
        """创建项目比对"""
        obj_in_data = {
            "project_id": project_id,
            "compared_project_id": compared_project_id,
            "comparison_type": comparison_type,
            "analyst_id": analyst_id
        }
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_project(
        self, db: Session, *, project_id: int
    ) -> List[ProjectComparison]:
        """获取项目的比对记录"""
        return (
            db.query(ProjectComparison)
            .filter(
                or_(
                    ProjectComparison.project_id == project_id,
                    ProjectComparison.compared_project_id == project_id
                )
            )
            .all()
        )
    
    def get_by_analyst(
        self, db: Session, *, analyst_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProjectComparison]:
        """获取分析员的比对记录"""
        return (
            db.query(ProjectComparison)
            .filter(ProjectComparison.analyst_id == analyst_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_comparison_result(
        self,
        db: Session,
        *,
        comparison_id: int,
        similarity_score: int,
        differences: str,
        anomalies: str = None,
        risk_indicators: str = None
    ) -> Optional[ProjectComparison]:
        """更新比对结果"""
        comparison = self.get(db, id=comparison_id)
        if comparison:
            comparison.similarity_score = similarity_score
            comparison.differences = differences
            if anomalies:
                comparison.anomalies = anomalies
            if risk_indicators:
                comparison.risk_indicators = risk_indicators
            comparison.status = "completed"
            comparison.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(comparison)
        return comparison


# 创建CRUD实例
project = CRUDProject(Project)
issue = CRUDIssue(Issue)
project_comparison = CRUDProjectComparison(ProjectComparison)