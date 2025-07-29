"""添加用户认证相关字段

数据库迁移脚本，为用户表添加密码、角色、登录信息等字段
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_auth_fields'
down_revision = None  # 根据实际情况设置
branch_labels = None
depends_on = None


def upgrade():
    """添加认证相关字段"""
    # 添加用户角色枚举类型
    user_role_enum = postgresql.ENUM('ADMIN', 'USER', name='userrole')
    user_role_enum.create(op.get_bind())
    
    # 为用户表添加新字段
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='USER'))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'))
    
    # 创建索引
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_last_login', 'users', ['last_login'])
    
    # 为现有用户设置默认密码（需要在生产环境中手动处理）
    # 注意：这里只是示例，实际部署时需要根据具体需求处理
    

def downgrade():
    """移除认证相关字段"""
    # 删除索引
    op.drop_index('ix_users_last_login', 'users')
    op.drop_index('ix_users_role', 'users')
    
    # 删除字段
    op.drop_column('users', 'login_count')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'role')
    op.drop_column('users', 'hashed_password')
    
    # 删除枚举类型
    user_role_enum = postgresql.ENUM('ADMIN', 'USER', name='userrole')
    user_role_enum.drop(op.get_bind())