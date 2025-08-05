#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境PostgreSQL数据库初始化脚本

功能:
1. 创建生产数据库
2. 创建数据库用户
3. 设置权限
4. 运行数据库迁移
5. 创建初始数据
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

from app.core.config import settings
from app.db.init_data import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionDBInitializer:
    """生产数据库初始化器"""
    
    def __init__(self):
        self.db_name = os.getenv("PROD_DB_NAME", "audit_system_prod")
        self.db_user = os.getenv("PROD_DB_USER", "postgres")
        self.db_password = os.getenv("PROD_DB_PASSWORD")
        if not self.db_password:
            raise ValueError("PROD_DB_PASSWORD环境变量必须设置")
        self.db_host = os.getenv("PROD_DB_HOST", "localhost")
        self.db_port = int(os.getenv("PROD_DB_PORT", "5432"))
        
        # 管理员连接URL（连接到postgres数据库）
        self.admin_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/postgres"
        # 目标数据库URL
        self.target_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    async def check_postgresql_connection(self):
        """检查PostgreSQL连接"""
        try:
            conn = await asyncpg.connect(self.admin_url)
            await conn.close()
            logger.info("✅ PostgreSQL连接正常")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            return False
    
    async def create_database(self):
        """创建生产数据库"""
        try:
            conn = await asyncpg.connect(self.admin_url)
            
            # 检查数据库是否已存在
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.db_name
            )
            
            if result:
                logger.info(f"📊 数据库 {self.db_name} 已存在")
            else:
                # 创建数据库
                await conn.execute(f"CREATE DATABASE {self.db_name}")
                logger.info(f"✅ 成功创建数据库: {self.db_name}")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False
    
    def run_migrations(self):
        """运行数据库迁移"""
        try:
            # 设置Alembic配置
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.target_url)
            
            # 运行迁移
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ 数据库迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            return False
    
    def create_indexes(self):
        """创建生产环境索引"""
        try:
            engine = create_engine(self.target_url)
            
            with engine.connect() as conn:
                # 创建常用查询索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);",
                    "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);",
                    "CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);",
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                    "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
                    "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
                    "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id);",
                    "CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);",
                ]
                
                for index_sql in indexes:
                    conn.execute(text(index_sql))
                    logger.info(f"✅ 创建索引: {index_sql.split('idx_')[1].split(' ')[0]}")
                
                conn.commit()
            
            engine.dispose()
            logger.info("✅ 所有索引创建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {e}")
            return False
    
    def optimize_database(self):
        """优化数据库配置"""
        try:
            engine = create_engine(self.target_url)
            
            with engine.connect() as conn:
                # PostgreSQL性能优化设置
                optimizations = [
                    "ALTER SYSTEM SET shared_buffers = '256MB';",
                    "ALTER SYSTEM SET effective_cache_size = '1GB';",
                    "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
                    "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
                    "ALTER SYSTEM SET wal_buffers = '16MB';",
                    "ALTER SYSTEM SET default_statistics_target = 100;",
                ]
                
                for opt_sql in optimizations:
                    try:
                        conn.execute(text(opt_sql))
                        logger.info(f"✅ 应用优化: {opt_sql.split('SET ')[1].split(' =')[0]}")
                    except Exception as e:
                        logger.warning(f"⚠️ 优化设置跳过 (需要超级用户权限): {e}")
                
                # 更新表统计信息
                conn.execute(text("ANALYZE;"))
                logger.info("✅ 更新表统计信息完成")
                
                conn.commit()
            
            engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库优化失败: {e}")
            return False
    
    async def initialize_data(self):
        """初始化基础数据"""
        try:
            # 更新环境变量
            os.environ["DATABASE_URL"] = self.target_url
            
            # 初始化数据
            await init_db()
            logger.info("✅ 基础数据初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据初始化失败: {e}")
            return False
    
    async def run_full_initialization(self):
        """运行完整的数据库初始化流程"""
        logger.info("🚀 开始生产数据库初始化...")
        
        # 1. 检查PostgreSQL连接
        if not await self.check_postgresql_connection():
            logger.error("❌ 初始化失败：无法连接到PostgreSQL")
            return False
        
        # 2. 创建数据库
        if not await self.create_database():
            logger.error("❌ 初始化失败：无法创建数据库")
            return False
        
        # 3. 运行迁移
        if not self.run_migrations():
            logger.error("❌ 初始化失败：数据库迁移失败")
            return False
        
        # 4. 创建索引
        if not self.create_indexes():
            logger.error("❌ 初始化失败：创建索引失败")
            return False
        
        # 5. 优化数据库
        if not self.optimize_database():
            logger.warning("⚠️ 数据库优化部分失败，但可以继续")
        
        # 6. 初始化数据
        if not await self.initialize_data():
            logger.error("❌ 初始化失败：基础数据创建失败")
            return False
        
        logger.info("🎉 生产数据库初始化完成！")
        logger.info(f"📊 数据库连接URL: {self.target_url}")
        return True


async def main():
    """主函数"""
    initializer = ProductionDBInitializer()
    success = await initializer.run_full_initialization()
    
    if success:
        print("\n✅ 生产数据库初始化成功！")
        print("\n📋 下一步操作:")
        print("1. 启动应用服务")
        print("2. 验证API功能")
        print("3. 检查数据库连接")
        return 0
    else:
        print("\n❌ 生产数据库初始化失败！")
        print("\n🔧 故障排除:")
        print("1. 检查PostgreSQL服务是否运行")
        print("2. 验证数据库连接参数")
        print("3. 检查用户权限")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)