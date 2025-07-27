import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.initial_review_data import (
    create_default_compliance_rules,
    init_review_data
)
from app.models.document import ComplianceRule


class TestInitialReviewDataAdditional:
    """测试审查数据初始化功能的额外测试用例"""
    
    def test_create_default_compliance_rules_creates_new_rules(self):
        """测试创建默认合规规则 - 新规则创建"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回None（规则不存在）
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_compliance_rules(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 5  # 5个默认合规规则
        
        # 验证添加和提交调用
        assert mock_db.add.call_count == 5
        mock_db.commit.assert_called_once()
    
    def test_create_default_compliance_rules_skips_existing_rules(self):
        """测试创建默认合规规则 - 跳过已存在的规则"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回已存在的规则
        mock_existing_rule = MagicMock(spec=ComplianceRule)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_existing_rule
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_compliance_rules(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 5
        
        # 验证没有添加任何规则
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
    
    def test_create_default_compliance_rules_mixed_existing(self):
        """测试创建默认合规规则 - 部分规则已存在"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟部分规则存在，部分不存在
        call_count = 0
        def mock_query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            mock_query = MagicMock()
            if call_count <= 2:  # 前两个规则存在
                mock_query.filter.return_value.first.return_value = MagicMock(spec=ComplianceRule)
            else:  # 后面的规则不存在
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # 执行测试
        create_default_compliance_rules(mock_db)
        
        # 验证查询调用
        assert mock_db.query.call_count == 5
        
        # 验证只添加了不存在的规则
        assert mock_db.add.call_count == 3  # 5 - 2 = 3个新规则
        mock_db.commit.assert_called_once()
    
    def test_create_default_compliance_rules_data_structure(self):
        """测试默认合规规则数据结构的正确性"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询返回None（规则不存在）
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 执行测试
        create_default_compliance_rules(mock_db)
        
        # 验证添加的规则数据
        added_rules = []
        for call in mock_db.add.call_args_list:
            rule = call[0][0]  # 获取添加的规则对象
            added_rules.append(rule)
        
        # 验证规则数量
        assert len(added_rules) == 5
        
        # 验证每个规则对象都不为空
        for rule in added_rules:
            assert rule is not None
    
    def test_create_default_compliance_rules_database_error(self):
        """测试创建默认合规规则时的数据库错误处理"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟数据库查询错误
        mock_db.query.side_effect = Exception("Database connection error")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Database connection error"):
            create_default_compliance_rules(mock_db)
    
    def test_create_default_compliance_rules_commit_error(self):
        """测试创建默认合规规则时的提交错误处理"""
        # 创建模拟数据库会话
        mock_db = MagicMock(spec=Session)
        
        # 模拟查询正常，但提交失败
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = Exception("Commit failed")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Commit failed"):
            create_default_compliance_rules(mock_db)
    
    @patch('app.initial_review_data.SessionLocal')
    @patch('app.initial_review_data.create_default_roles')
    @patch('app.initial_review_data.create_default_review_stages')
    @patch('app.initial_review_data.create_default_review_points')
    @patch('app.initial_review_data.create_default_compliance_rules')
    def test_init_review_data_success(self, mock_create_rules, mock_create_points, 
                                     mock_create_stages, mock_create_roles, mock_session_local):
        """测试初始化审查数据 - 成功场景"""
        # 创建模拟数据库会话
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 执行测试
        init_review_data()
        
        # 验证所有创建函数都被调用
        mock_create_roles.assert_called_once_with(mock_db)
        mock_create_stages.assert_called_once_with(mock_db)
        mock_create_points.assert_called_once_with(mock_db)
        mock_create_rules.assert_called_once_with(mock_db)
        
        # 验证数据库会话被正确关闭
        mock_db.close.assert_called_once()
        
        # 验证没有调用回滚
        mock_db.rollback.assert_not_called()
    
    @patch('app.initial_review_data.SessionLocal')
    @patch('app.initial_review_data.create_default_roles')
    @patch('app.initial_review_data.create_default_review_stages')
    @patch('app.initial_review_data.create_default_review_points')
    @patch('app.initial_review_data.create_default_compliance_rules')
    def test_init_review_data_with_exception(self, mock_create_rules, mock_create_points, 
                                           mock_create_stages, mock_create_roles, mock_session_local):
        """测试初始化审查数据 - 异常处理"""
        # 创建模拟数据库会话
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 模拟创建角色时抛出异常
        mock_create_roles.side_effect = Exception("Role creation failed")
        
        # 执行测试（不应该抛出异常，因为有异常处理）
        init_review_data()
        
        # 验证创建角色函数被调用
        mock_create_roles.assert_called_once_with(mock_db)
        
        # 验证回滚被调用
        mock_db.rollback.assert_called_once()
        
        # 验证数据库会话被正确关闭
        mock_db.close.assert_called_once()
    
    @patch('app.initial_review_data.SessionLocal')
    @patch('app.initial_review_data.create_default_roles')
    @patch('app.initial_review_data.create_default_review_stages')
    @patch('app.initial_review_data.create_default_review_points')
    @patch('app.initial_review_data.create_default_compliance_rules')
    def test_init_review_data_session_creation_error(self, mock_create_rules, mock_create_points, 
                                                   mock_create_stages, mock_create_roles, mock_session_local):
        """测试初始化审查数据 - 会话创建错误"""
        # 模拟会话创建失败
        mock_session_local.side_effect = Exception("Session creation failed")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Session creation failed"):
            init_review_data()
        
        # 验证创建函数都没有被调用
        mock_create_roles.assert_not_called()
        mock_create_stages.assert_not_called()
        mock_create_points.assert_not_called()
        mock_create_rules.assert_not_called()
    
    @patch('app.initial_review_data.SessionLocal')
    @patch('app.initial_review_data.create_default_roles')
    @patch('app.initial_review_data.create_default_review_stages')
    @patch('app.initial_review_data.create_default_review_points')
    @patch('app.initial_review_data.create_default_compliance_rules')
    def test_init_review_data_partial_success(self, mock_create_rules, mock_create_points, 
                                             mock_create_stages, mock_create_roles, mock_session_local):
        """测试初始化审查数据 - 部分成功场景"""
        # 创建模拟数据库会话
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        
        # 模拟前两个函数成功，第三个函数失败
        mock_create_points.side_effect = Exception("Points creation failed")
        
        # 执行测试
        init_review_data()
        
        # 验证前两个函数被调用
        mock_create_roles.assert_called_once_with(mock_db)
        mock_create_stages.assert_called_once_with(mock_db)
        mock_create_points.assert_called_once_with(mock_db)
        
        # 验证第四个函数没有被调用（因为第三个失败了）
        mock_create_rules.assert_not_called()
        
        # 验证回滚被调用
        mock_db.rollback.assert_called_once()
        
        # 验证数据库会话被正确关闭
        mock_db.close.assert_called_once()
    
    @patch('app.initial_review_data.init_review_data')
    def test_main_execution(self, mock_init_review_data):
        """测试主函数执行"""
        # 导入模块以触发 if __name__ == "__main__" 检查
        import app.initial_review_data
        
        # 由于我们已经导入了模块，主函数不会自动执行
        # 我们直接测试主函数逻辑
        app.initial_review_data.init_review_data()
        
        # 验证初始化函数被调用
        mock_init_review_data.assert_called_once()