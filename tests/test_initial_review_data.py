import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.initial_review_data import (
    create_default_roles,
    create_default_review_stages,
    create_default_review_points,
    create_default_compliance_rules
)
from app.models.user import Role
from app.models.review_stage import ReviewStage, ReviewPoint
from app.models.document import ComplianceRule


class TestInitialReviewData:
    """测试审查数据初始化功能"""
    
    def test_create_default_roles_creates_new_roles(self):
        """测试创建默认角色 - 新角色创建"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回None（角色不存在）
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_roles(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 4  # 4个默认角色
        
        # 验证添加和提交调用
        assert mock_db.add.call_count == 4
        mock_db.commit.assert_called_once()
    
    def test_create_default_roles_skips_existing_roles(self):
        """测试创建默认角色 - 跳过已存在的角色"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回已存在的角色
        mock_existing_role = MagicMock(spec=Role)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_existing_role
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_roles(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 4
        
        # 验证没有添加任何角色
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_create_default_review_stages_creates_new_stages(self):
        """测试创建默认审查阶段 - 新阶段创建"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回None（阶段不存在）
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_review_stages(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 7  # 7个默认审查阶段
        
        # 验证添加和提交调用
        assert mock_db.add.call_count == 7
        mock_db.commit.assert_called_once()
    
    def test_create_default_review_stages_skips_existing_stages(self):
        """测试创建默认审查阶段 - 跳过已存在的阶段"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回已存在的阶段
        mock_existing_stage = MagicMock(spec=ReviewStage)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_existing_stage
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_review_stages(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 7
        
        # 验证没有添加任何阶段
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_create_default_review_points_creates_new_points(self):
        """测试创建默认审查要点 - 新要点创建"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 创建模拟审查阶段，设置正确的name属性
        mock_stage1 = MagicMock()
        mock_stage1.name = "立项审查"
        mock_stage1.id = 1
        
        mock_stage2 = MagicMock()
        mock_stage2.name = "采购需求审查"
        mock_stage2.id = 2
        
        mock_stage3 = MagicMock()
        mock_stage3.name = "采购方式审查"
        mock_stage3.id = 3
        
        mock_stage4 = MagicMock()
        mock_stage4.name = "招标文件审查"
        mock_stage4.id = 4
        
        mock_stages = [mock_stage1, mock_stage2, mock_stage3, mock_stage4]
        
        def mock_query_side_effect(model):
            if model == ReviewStage:
                mock_query = MagicMock()
                mock_query.all.return_value = mock_stages
                return mock_query
            elif model == ReviewPoint:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = None
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # 执行测试
        create_default_review_points(mock_db)
        
        # 验证添加和提交调用
        assert mock_db.add.call_count >= 6  # 应该添加了至少6个审查要点
        mock_db.commit.assert_called_once()
    
    def test_create_default_review_points_skips_existing_points(self):
        """测试创建默认审查要点 - 跳过已存在的要点"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟审查阶段查询
        mock_stages = [
            MagicMock(name="立项审查", id=1),
            MagicMock(name="采购需求审查", id=2)
        ]
        
        # 模拟已存在的审查要点
        mock_existing_point = MagicMock(spec=ReviewPoint)
        
        def mock_query_side_effect(model):
            if model == ReviewStage:
                mock_query = MagicMock()
                mock_query.all.return_value = mock_stages
                return mock_query
            elif model == ReviewPoint:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = mock_existing_point
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # 执行测试
        create_default_review_points(mock_db)
        
        # 验证没有添加任何要点
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_create_default_review_points_handles_missing_stages(self):
        """测试创建默认审查要点 - 处理缺失的阶段"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟空的审查阶段列表
        def mock_query_side_effect(model):
            if model == ReviewStage:
                mock_query = MagicMock()
                mock_query.all.return_value = []  # 没有阶段
                return mock_query
            elif model == ReviewPoint:
                mock_query = MagicMock()
                mock_query.filter.return_value.first.return_value = None
                return mock_query
            return MagicMock()
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # 执行测试
        create_default_review_points(mock_db)
        
        # 验证没有添加任何要点（因为没有对应的阶段）
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_all_functions_integration(self):
        """测试所有函数的集成调用"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 为角色和阶段设置模拟
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_query.all.return_value = []  # 空的阶段列表
        mock_db.query.return_value = mock_query
        
        # 调用所有函数
        create_default_roles(mock_db)
        create_default_review_stages(mock_db)
        create_default_review_points(mock_db)
        
        # 验证数据库操作被调用
        assert mock_db.query.call_count > 0
        assert mock_db.commit.call_count == 3  # 每个函数都应该提交一次
    
    def test_create_default_roles_data_structure(self):
        """测试默认角色数据结构的正确性"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回None（角色不存在）
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_roles(mock_db)
        
        # 验证添加的角色数据
        added_roles = []
        for call in mock_db.add.call_args_list:
            role = call[0][0]  # 获取添加的角色对象
            added_roles.append(role)
        
        # 验证角色数量
        assert len(added_roles) == 4
        
        # 验证角色名称（通过检查Role构造函数的调用）
        role_names = []
        for call in mock_db.add.call_args_list:
            # 由于我们使用了Role(**role_data)，需要检查构造函数参数
            # 这里我们主要验证调用次数和基本结构
            assert call[0][0] is not None
    
    def test_database_error_handling(self):
        """测试数据库错误处理"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟数据库查询错误
        mock_db.query.side_effect = Exception("Database error")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Database error"):
            create_default_roles(mock_db)
    
    def test_commit_error_handling(self):
        """测试提交错误处理"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询正常，但提交失败
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = Exception("Commit failed")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Commit failed"):
            create_default_roles(mock_db)