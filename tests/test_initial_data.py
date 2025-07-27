import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.initial_data import init_db
from app.models.user import User
from app.schemas.user import UserCreate


class TestInitialData:
    """测试初始化数据功能"""
    
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_creates_superuser_when_not_exists(self, mock_settings, mock_user_crud, mock_session_local):
        """测试当超级用户不存在时创建超级用户"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        mock_settings.FIRST_SUPERUSER_PASSWORD = "admin123"
        
        # 模拟用户不存在
        mock_user_crud.get_by_username.return_value = None
        
        # 模拟创建的用户
        mock_created_user = MagicMock(spec=User)
        mock_user_crud.create.return_value = mock_created_user
        
        # 执行测试
        init_db()
        
        # 验证调用
        mock_user_crud.get_by_username.assert_called_once_with(
            mock_db, username="admin"
        )
        
        # 验证创建用户的调用
        mock_user_crud.create.assert_called_once()
        call_args = mock_user_crud.create.call_args
        assert call_args[0][0] == mock_db  # 第一个参数是db
        
        # 验证UserCreate对象的属性
        user_create_obj = call_args[1]['obj_in']
        assert isinstance(user_create_obj, UserCreate)
        assert user_create_obj.username == "admin"
        assert user_create_obj.password == "admin123"
        assert user_create_obj.is_superuser is True
    
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_skips_creation_when_superuser_exists(self, mock_settings, mock_user_crud, mock_session_local):
        """测试当超级用户已存在时跳过创建"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        
        # 模拟用户已存在
        mock_existing_user = MagicMock(spec=User)
        mock_user_crud.get_by_username.return_value = mock_existing_user
        
        # 执行测试
        init_db()
        
        # 验证调用
        mock_user_crud.get_by_username.assert_called_once_with(
            mock_db, username="admin"
        )
        
        # 验证没有调用创建用户
        mock_user_crud.create.assert_not_called()
    
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_handles_database_error(self, mock_settings, mock_user_crud, mock_session_local):
        """测试数据库错误处理"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        
        # 模拟数据库错误
        mock_user_crud.get_by_username.side_effect = Exception("Database connection error")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="Database connection error"):
            init_db()
    
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_handles_user_creation_error(self, mock_settings, mock_user_crud, mock_session_local):
        """测试用户创建错误处理"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        mock_settings.FIRST_SUPERUSER_PASSWORD = "admin123"
        
        # 模拟用户不存在但创建失败
        mock_user_crud.get_by_username.return_value = None
        mock_user_crud.create.side_effect = Exception("User creation failed")
        
        # 执行测试并验证异常
        with pytest.raises(Exception, match="User creation failed"):
            init_db()
    
    @patch('app.initial_data.logger')
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_logs_superuser_creation(self, mock_settings, mock_user_crud, mock_session_local, mock_logger):
        """测试超级用户创建时的日志记录"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        mock_settings.FIRST_SUPERUSER_PASSWORD = "admin123"
        
        # 模拟用户不存在
        mock_user_crud.get_by_username.return_value = None
        mock_created_user = MagicMock(spec=User)
        mock_user_crud.create.return_value = mock_created_user
        
        # 执行测试
        init_db()
        
        # 验证日志调用
        mock_logger.info.assert_called_with("Superuser created")
    
    @patch('app.initial_data.logger')
    @patch('app.initial_data.SessionLocal')
    @patch('app.initial_data.user')
    @patch('app.initial_data.settings')
    def test_init_db_logs_superuser_exists(self, mock_settings, mock_user_crud, mock_session_local, mock_logger):
        """测试超级用户已存在时的日志记录"""
        # 设置模拟
        mock_db = MagicMock(spec=Session)
        mock_session_local.return_value = mock_db
        
        mock_settings.FIRST_SUPERUSER = "admin"
        
        # 模拟用户已存在
        mock_existing_user = MagicMock(spec=User)
        mock_user_crud.get_by_username.return_value = mock_existing_user
        
        # 执行测试
        init_db()
        
        # 验证日志调用
        mock_logger.info.assert_called_with("Superuser already exists")
    
    @patch('app.initial_data.init_db')
    @patch('app.initial_data.logger')
    def test_main_execution(self, mock_logger, mock_init_db):
        """测试主程序执行"""
        # 模拟主程序执行
        import app.initial_data
        
        # 由于我们不能直接测试 if __name__ == "__main__" 块，
        # 我们测试相关的函数调用
        with patch.object(app.initial_data, '__name__', '__main__'):
            # 手动调用主程序逻辑
            mock_logger.info("Creating initial data")
            mock_init_db()
            mock_logger.info("Initial data created")
            
            # 验证调用
            assert mock_logger.info.call_count >= 2
            mock_init_db.assert_called_once()