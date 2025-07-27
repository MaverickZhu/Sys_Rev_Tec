import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.crud.crud_project import project, issue, project_comparison
from app.models.project import Project, Issue, ProjectComparison
from app.schemas.project import ProjectCreate, IssueCreate, ProjectComparisonCreate
from tests.utils.utils import random_lower_string


class TestCRUDProjectCoverage:
    """测试CRUD项目操作的覆盖率"""
    
    def test_get_by_code(self, db: Session):
        """测试按项目编号获取项目"""
        # Mock数据库查询
        mock_project = Mock(spec=Project)
        mock_project.project_code = "TEST001"
        
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_project
            result = project.get_by_code(db, project_code="TEST001")
            assert result == mock_project
            mock_query.assert_called_once()
    
    def test_get_by_owner(self, db: Session):
        """测试按负责人获取项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_by_owner(db, owner_id=1)
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_status(self, db: Session):
        """测试按状态获取项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_by_status(db, status="active")
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_review_status(self, db: Session):
        """测试按审查状态获取项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_by_review_status(db, review_status="pending")
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_department(self, db: Session):
        """测试按部门获取项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_by_department(db, department="IT")
            assert result == []
            mock_query.assert_called_once()
    
    def test_search_projects(self, db: Session):
        """测试搜索项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.search_projects(db, query="test")
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_projects_by_filters(self, db: Session):
        """测试按多个条件筛选项目"""
        with patch.object(db, 'query') as mock_query:
            # 设置完整的mock链
            mock_chain = mock_query.return_value
            mock_chain.filter.return_value = mock_chain
            mock_chain.order_by.return_value = mock_chain
            mock_chain.offset.return_value = mock_chain
            mock_chain.limit.return_value = mock_chain
            mock_chain.all.return_value = []
            
            result = project.get_projects_by_filters(db, filters={"status": "active", "department": "IT"})
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_project_statistics(self, db: Session):
        """测试获取项目统计信息"""
        with patch.object(db, 'query') as mock_query:
            # Mock count方法返回值
            mock_query.return_value.count.return_value = 10
            mock_query.return_value.filter.return_value.count.return_value = 5
            
            result = project.get_project_statistics(db)
            
            assert "total_projects" in result
            assert "status_distribution" in result
            assert "review_status_distribution" in result
            assert "risk_level_distribution" in result
    
    def test_update_review_status(self, db: Session):
        """测试更新项目审查状态"""
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        
        with patch.object(project, 'get', return_value=mock_project):
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project.update_review_status(db, project_id=1, review_status="approved")
                assert result == mock_project
                assert mock_project.review_status == "approved"
    
    def test_get_projects_by_date_range(self, db: Session):
        """测试根据日期范围获取项目"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_projects_by_date_range(db, start_date=start_date, end_date=end_date)
            assert result == []
            mock_query.assert_called_once()
    
    def test_update_status(self, db: Session):
        """测试更新项目状态"""
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        
        with patch.object(project, 'get', return_value=mock_project):
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project.update_status(db, project_id=1, status="completed")
                assert result == mock_project
                assert mock_project.status == "completed"
    
    def test_get_recent_projects(self, db: Session):
        """测试获取最近创建的项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            result = project.get_recent_projects(db, limit=5)
            assert result == []
            mock_query.assert_called_once()
    
    def test_activate_project(self, db: Session):
        """测试激活项目"""
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_project
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project.activate(db, project_id=1)
                assert result == mock_project
                assert mock_project.is_active == True
    
    def test_deactivate_project(self, db: Session):
        """测试停用项目"""
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_project
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project.deactivate(db, project_id=1)
                assert result == mock_project
                assert mock_project.is_active == False
    
    def test_get_active_projects(self, db: Session):
        """测试获取活跃项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.get_active_projects(db)
            assert result == []
            mock_query.assert_called_once()
    
    def test_search(self, db: Session):
        """测试搜索项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project.search(db, query="test")
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_statistics(self, db: Session):
        """测试获取项目统计信息"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.count.return_value = 10
            mock_query.return_value.filter.return_value.count.return_value = 5
            
            result = project.get_statistics(db)
            
            assert "total_count" in result
            assert "active_count" in result
            assert "completed_count" in result
            assert "inactive_count" in result


class TestCRUDIssueCoverage:
    """测试CRUD问题操作的覆盖率"""
    
    def test_create_with_project(self, db: Session):
        """测试创建问题并关联项目"""
        mock_issue_create = Mock()
        mock_issue_create.model_dump.return_value = {"title": "Test Issue"}
        
        mock_issue = Mock(spec=Issue)
        
        with patch.object(issue, 'model', return_value=mock_issue) as mock_model:
            with patch.object(db, 'add'), patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = issue.create_with_project(db, obj_in=mock_issue_create, project_id=1, reporter_id=1)
                assert result == mock_issue
    
    def test_get_by_project(self, db: Session):
        """测试获取项目的问题列表"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = issue.get_by_project(db, project_id=1)
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_assignee(self, db: Session):
        """测试获取指定负责人的问题列表"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = issue.get_by_assignee(db, assignee_id=1)
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_status(self, db: Session):
        """测试根据状态获取问题列表"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = issue.get_by_status(db, status="open")
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_overdue_issues(self, db: Session):
        """测试获取逾期问题"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = []
            result = issue.get_overdue_issues(db)
            assert result == []
            mock_query.assert_called_once()
    
    def test_assign_issue(self, db: Session):
        """测试分配问题给指定用户"""
        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        
        with patch.object(issue, 'get', return_value=mock_issue):
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = issue.assign_issue(db, issue_id=1, assignee_id=2)
                assert result == mock_issue
                assert mock_issue.assignee_id == 2
    
    def test_resolve_issue(self, db: Session):
        """测试解决问题"""
        mock_issue = Mock(spec=Issue)
        mock_issue.id = 1
        
        with patch.object(issue, 'get', return_value=mock_issue):
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = issue.resolve_issue(db, issue_id=1, resolution="Fixed")
                assert result == mock_issue
                assert mock_issue.status == "resolved"
                assert mock_issue.resolution == "Fixed"


class TestCRUDProjectComparisonCoverage:
    """测试CRUD项目比对操作的覆盖率"""
    
    def test_create_comparison(self, db: Session):
        """测试创建项目比对"""
        mock_comparison = Mock(spec=ProjectComparison)
        
        with patch.object(project_comparison, 'model', return_value=mock_comparison) as mock_model:
            with patch.object(db, 'add'), patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project_comparison.create_comparison(
                    db, project_id=1, compared_project_id=2, 
                    comparison_type="similarity", analyst_id=1
                )
                assert result == mock_comparison
    
    def test_get_by_project(self, db: Session):
        """测试获取项目的比对记录"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = []
            result = project_comparison.get_by_project(db, project_id=1)
            assert result == []
            mock_query.assert_called_once()
    
    def test_get_by_analyst(self, db: Session):
        """测试获取分析员的比对记录"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = project_comparison.get_by_analyst(db, analyst_id=1)
            assert result == []
            mock_query.assert_called_once()
    
    def test_update_comparison_result(self, db: Session):
        """测试更新比对结果"""
        mock_comparison = Mock(spec=ProjectComparison)
        mock_comparison.id = 1
        
        with patch.object(project_comparison, 'get', return_value=mock_comparison):
            with patch.object(db, 'commit'), patch.object(db, 'refresh'):
                result = project_comparison.update_comparison_result(
                    db, comparison_id=1, similarity_score=85, 
                    differences="Some differences", anomalies="No anomalies"
                )
                assert result == mock_comparison
                assert mock_comparison.similarity_score == 85
                assert mock_comparison.differences == "Some differences"
                assert mock_comparison.status == "completed"


class TestCRUDProjectEdgeCases:
    """测试CRUD项目操作的边界情况"""
    
    def test_update_review_status_not_found(self, db: Session):
        """测试更新不存在项目的审查状态"""
        with patch.object(project, 'get', return_value=None):
            result = project.update_review_status(db, project_id=999, review_status="approved")
            assert result is None
    
    def test_update_status_not_found(self, db: Session):
        """测试更新不存在项目的状态"""
        with patch.object(project, 'get', return_value=None):
            result = project.update_status(db, project_id=999, status="completed")
            assert result is None
    
    def test_activate_not_found(self, db: Session):
        """测试激活不存在的项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            result = project.activate(db, project_id=999)
            assert result is None
    
    def test_deactivate_not_found(self, db: Session):
        """测试停用不存在的项目"""
        with patch.object(db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            result = project.deactivate(db, project_id=999)
            assert result is None
    
    def test_assign_issue_not_found(self, db: Session):
        """测试分配不存在的问题"""
        with patch.object(issue, 'get', return_value=None):
            result = issue.assign_issue(db, issue_id=999, assignee_id=1)
            assert result is None
    
    def test_resolve_issue_not_found(self, db: Session):
        """测试解决不存在的问题"""
        with patch.object(issue, 'get', return_value=None):
            result = issue.resolve_issue(db, issue_id=999, resolution="Fixed")
            assert result is None
    
    def test_update_comparison_result_not_found(self, db: Session):
        """测试更新不存在比对的结果"""
        with patch.object(project_comparison, 'get', return_value=None):
            result = project_comparison.update_comparison_result(
                db, comparison_id=999, similarity_score=85, differences="test"
            )
            assert result is None