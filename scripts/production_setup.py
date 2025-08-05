#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境数据库设置脚本

功能:
1. 清理测试数据
2. 重置数据库到生产状态
3. 创建生产环境必需的初始数据
4. 配置生产环境设置
5. 验证生产环境就绪状态

使用方法:
    python scripts/production_setup.py --action clean
    python scripts/production_setup.py --action init
    python scripts/production_setup.py --action verify
    python scripts/production_setup.py --action all
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.document import Document
from app.crud.crud_user import user as user_crud
from app.schemas.user import UserCreate

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f"production_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProductionSetup:
    """生产环境设置管理器"""

    def __init__(self):
        self.db = SessionLocal()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def backup_current_data(self):
        """备份当前数据"""
        logger.info("开始备份当前数据...")
        
        try:
            # 检查是否有重要数据需要备份
            user_count = self.db.query(User).count()
            project_count = self.db.query(Project).count()
            document_count = self.db.query(Document).count()
            
            logger.info(f"当前数据统计: 用户({user_count}), 项目({project_count}), 文档({document_count})")
            
            if user_count > 1 or project_count > 0 or document_count > 0:
                logger.warning("检测到现有数据，建议手动备份重要数据")
                response = input("是否继续清理数据？(y/N): ")
                if response.lower() != 'y':
                    logger.info("用户取消操作")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"备份检查失败: {e}")
            return False

    def clean_test_data(self):
        """清理测试数据"""
        logger.info("开始清理测试数据...")
        
        try:
            # 清理测试用户（保留admin用户）
            test_usernames = ['reviewer', 'analyst', 'operator', 'manager', 'test_user']
            
            for username in test_usernames:
                test_user = self.db.query(User).filter(User.username == username).first()
                if test_user:
                    logger.info(f"删除测试用户: {username}")
                    self.db.delete(test_user)
            
            # 清理测试项目
            test_projects = self.db.query(Project).filter(
                Project.name.like('%测试%')
            ).all()
            
            for project in test_projects:
                logger.info(f"删除测试项目: {project.name}")
                self.db.delete(project)
            
            # 清理测试文档
            test_documents = self.db.query(Document).filter(
                Document.file_name.like('%test%')
            ).all()
            
            for document in test_documents:
                logger.info(f"删除测试文档: {document.file_name}")
                self.db.delete(document)
            
            # 提交更改
            self.db.commit()
            logger.info("测试数据清理完成")
            return True
            
        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")
            self.db.rollback()
            return False

    def create_production_admin(self):
        """创建生产环境管理员用户"""
        logger.info("创建生产环境管理员用户...")
        
        try:
            # 检查是否已存在admin用户
            admin_user = user_crud.get_by_username(self.db, username="admin")
            
            if admin_user:
                logger.info("管理员用户已存在，更新密码和角色...")
                # 更新为生产环境密码和管理员角色
                admin_user.hashed_password = user_crud.get_password_hash("Admin@2025!")
                admin_user.role = UserRole.ADMIN
                admin_user.is_active = True
                self.db.commit()
            else:
                logger.info("创建新的管理员用户...")
                admin_create = UserCreate(
                    username="admin",
                    email="admin@company.com",
                    password="Admin@2025!",
                    full_name="系统管理员",
                    is_active=True
                )
                admin_user = user_crud.create(self.db, obj_in=admin_create)
                # 设置为管理员角色
                admin_user.role = UserRole.ADMIN
                self.db.commit()
            
            logger.info(f"管理员用户设置完成: {admin_user.username}")
            logger.warning("[警告] 生产环境管理员密码: Admin@2025! (请及时修改)")
            return True
            
        except Exception as e:
            logger.error(f"创建管理员用户失败: {e}")
            return False

    def optimize_database(self):
        """优化数据库性能"""
        logger.info("优化数据库性能...")
        
        try:
            with engine.connect() as connection:
                # 更新统计信息
                connection.execute(text("ANALYZE"))
                logger.info("数据库统计信息已更新")
                
                # 创建生产环境推荐的索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                    "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
                    "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents(upload_time)",
                ]
                
                for index_sql in indexes:
                    try:
                        connection.execute(text(index_sql))
                        logger.info(f"创建索引: {index_sql.split()[-1]}")
                    except Exception as e:
                        logger.warning(f"索引创建失败: {e}")
                
                connection.commit()
                logger.info("数据库优化完成")
                return True
                
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            return False

    def update_production_config(self):
        """更新生产环境配置"""
        logger.info("更新生产环境配置...")
        
        try:
            # 创建生产环境配置文件
            prod_env_content = f"""# 生产环境配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# 环境设置
ENVIRONMENT=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://sys_rev_user:CHANGE_PASSWORD@127.0.0.1:5432/sys_rev_tec_prod
DATABASE_ECHO=false

# 安全配置
SECRET_KEY=CHANGE_THIS_SECRET_KEY_IN_PRODUCTION
JWT_SECRET_KEY=CHANGE_THIS_JWT_SECRET_KEY_IN_PRODUCTION

# Redis配置
REDIS_URL=redis://:redis_password@127.0.0.1:6379/0
CACHE_ENABLED=true

# 日志配置
LOG_LEVEL=INFO
LOG_STRUCTURED=true
ERROR_TRACKING_ENABLED=true

# 性能配置
WORKERS=4
THREADS=2

# 监控配置
ENABLE_METRICS=true
ALERT_ENABLED=true

# CORS配置（根据实际域名调整）
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
"""
            
            env_prod_file = Path(".env.production")
            with open(env_prod_file, 'w', encoding='utf-8') as f:
                f.write(prod_env_content)
            
            logger.info(f"生产环境配置文件已创建: {env_prod_file}")
            logger.warning("[警告] 请修改配置文件中的密钥和数据库密码")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False

    def verify_production_ready(self):
        """验证生产环境就绪状态"""
        logger.info("验证生产环境就绪状态...")
        
        try:
            # 检查数据库连接
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info("[成功] 数据库连接正常")
            
            # 检查管理员用户
            admin_user = user_crud.get_by_username(self.db, username="admin")
            if admin_user and admin_user.is_active:
                logger.info("[成功] 管理员用户存在且激活")
            else:
                logger.error("[错误] 管理员用户不存在或未激活")
                return False
            
            # 检查数据库表结构
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = ['users', 'projects', 'documents']
            
            for table in required_tables:
                if table in tables:
                    logger.info(f"[成功] 表 {table} 存在")
                else:
                    logger.error(f"[错误] 表 {table} 不存在")
                    return False
            
            # 检查配置文件
            if Path(".env.production").exists():
                logger.info("[成功] 生产环境配置文件存在")
            else:
                logger.warning("[警告] 生产环境配置文件不存在")
            
            # 统计当前数据
            user_count = self.db.query(User).count()
            project_count = self.db.query(Project).count()
            document_count = self.db.query(Document).count()
            
            logger.info(f"[统计] 当前数据统计:")
            logger.info(f"   - 用户数量: {user_count}")
            logger.info(f"   - 项目数量: {project_count}")
            logger.info(f"   - 文档数量: {document_count}")
            
            logger.info("[完成] 生产环境验证完成")
            return True
            
        except Exception as e:
            logger.error(f"生产环境验证失败: {e}")
            return False

    def run_full_setup(self):
        """运行完整的生产环境设置流程"""
        logger.info("[开始] 生产环境完整设置...")
        
        steps = [
            ("备份检查", self.backup_current_data),
            ("清理测试数据", self.clean_test_data),
            ("创建管理员用户", self.create_production_admin),
            ("优化数据库", self.optimize_database),
            ("更新配置", self.update_production_config),
            ("验证就绪状态", self.verify_production_ready),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            if not step_func():
                logger.error(f"步骤失败: {step_name}")
                return False
            logger.info(f"步骤完成: {step_name}")
        
        logger.info("[成功] 生产环境设置完成")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生产环境数据库设置工具")
    parser.add_argument(
        "--action",
        choices=["clean", "init", "verify", "config", "all"],
        required=True,
        help="要执行的操作",
    )
    parser.add_argument("--force", action="store_true", help="强制执行，跳过确认")
    
    args = parser.parse_args()
    
    # 安全检查
    if not args.force and settings.ENVIRONMENT.lower() == "production":
        logger.warning("[警告] 检测到生产环境，请谨慎操作")
        response = input("确认在生产环境执行操作？(y/N): ")
        if response.lower() != 'y':
            logger.info("用户取消操作")
            return 1
    
    setup = ProductionSetup()
    success = True
    
    logger.info(f"开始执行操作: {args.action}")
    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    logger.info(f"当前环境: {settings.ENVIRONMENT}")
    
    if args.action == "clean":
        success = setup.clean_test_data()
    
    elif args.action == "init":
        success = setup.create_production_admin()
    
    elif args.action == "verify":
        success = setup.verify_production_ready()
    
    elif args.action == "config":
        success = setup.update_production_config()
    
    elif args.action == "all":
        success = setup.run_full_setup()
    
    if success:
        logger.info("[成功] 操作成功完成")
        
        # 显示后续步骤提示
        logger.info("\n[后续步骤]")
        logger.info("1. 修改 .env.production 中的密钥和密码")
        logger.info("2. 配置反向代理和SSL证书")
        logger.info("3. 设置监控和日志收集")
        logger.info("4. 配置备份策略")
        logger.info("5. 进行安全审计")
        
        return 0
    else:
        logger.error("[失败] 操作失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())