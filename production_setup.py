#!/usr/bin/env python3
"""
生产环境设置脚本
用于清理测试数据并准备生产环境
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core.auth import get_password_hash
from app.db.session import SessionLocal, get_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('production_setup.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def clean_test_data():
    """清理测试数据"""
    logger.info("[CLEAN] 开始清理测试数据...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # 清理测试用户（保留管理员）
        test_users = db.query(User).filter(
            User.email.like('%test%'),
            User.email != 'admin@example.com'
        ).all()
        
        for user in test_users:
            logger.info(f"删除测试用户: {user.email}")
            db.delete(user)
        
        db.commit()
        logger.info(f"[SUCCESS] 清理了 {len(test_users)} 个测试用户")
        
    except Exception as e:
        logger.error(f"[ERROR] 清理测试数据失败: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

def create_admin_user():
    """创建或更新管理员用户"""
    logger.info("[INIT] 创建管理员用户...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        admin_email = "admin@example.com"
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        # 检查管理员是否存在
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if admin_user:
            # 更新现有管理员
            admin_user.hashed_password = get_password_hash(admin_password)
            admin_user.role = UserRole.ADMIN
            admin_user.is_active = True
            logger.info("[SUCCESS] 管理员用户已更新")
        else:
            # 创建新管理员
            admin_data = UserCreate(
                email=admin_email,
                password=admin_password,
                username="admin",
                full_name="系统管理员"
            )
            
            admin_user = User(
                email=admin_data.email,
                username=admin_data.username,
                full_name=admin_data.full_name,
                hashed_password=get_password_hash(admin_data.password),
                is_active=True
            )
            
            # 设置管理员角色
            admin_user.role = UserRole.ADMIN
            
            db.add(admin_user)
            logger.info("[SUCCESS] 管理员用户已创建")
        
        db.commit()
        logger.info(f"管理员邮箱: {admin_email}")
        logger.info(f"管理员密码: {admin_password}")
        
    except Exception as e:
        logger.error(f"[ERROR] 创建管理员用户失败: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

def verify_production_ready():
    """验证生产环境就绪状态"""
    logger.info("[VERIFY] 验证生产环境状态...")
    
    checks = {
        "数据库连接": False,
        "管理员用户": False,
        "环境配置": False
    }
    
    try:
        # 检查数据库连接
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["数据库连接"] = True
        
        # 检查管理员用户
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        admin_user = db.query(User).filter(
            User.email == "admin@example.com",
            User.role == UserRole.ADMIN
        ).first()
        if admin_user:
            checks["管理员用户"] = True
        db.close()
        
        # 检查环境配置
        if settings.ENVIRONMENT == "production":
            checks["环境配置"] = True
        
        # 输出检查结果
        logger.info("\n=== 生产环境检查结果 ===")
        for check, status in checks.items():
            status_text = "[PASS]" if status else "[FAIL]"
            logger.info(f"{status_text} {check}")
        
        all_passed = all(checks.values())
        if all_passed:
            logger.info("\n[SUCCESS] 生产环境准备就绪！")
        else:
            logger.warning("\n[WARNING] 部分检查未通过，请检查配置")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"[ERROR] 验证失败: {str(e)}")
        return False

def configure_production():
    """配置生产环境设置"""
    logger.info("[CONFIG] 配置生产环境...")
    
    try:
        # 检查必要的环境变量
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'REDIS_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"缺少环境变量: {', '.join(missing_vars)}")
        else:
            logger.info("[SUCCESS] 环境变量配置完整")
        
        # 创建必要的目录
        directories = [
            'logs',
            'uploads',
            'temp',
            'backups'
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"创建目录: {directory}")
        
        logger.info("[SUCCESS] 生产环境配置完成")
        
    except Exception as e:
        logger.error(f"[ERROR] 配置生产环境失败: {str(e)}")
        raise

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生产环境设置脚本')
    parser.add_argument('action', choices=['clean', 'init', 'verify', 'config', 'all'],
                       help='执行的操作')
    
    args = parser.parse_args()
    
    logger.info(f"开始执行生产环境设置: {args.action}")
    logger.info(f"当前环境: {settings.ENVIRONMENT}")
    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    
    try:
        if args.action == 'clean':
            clean_test_data()
        elif args.action == 'init':
            create_admin_user()
        elif args.action == 'verify':
            verify_production_ready()
        elif args.action == 'config':
            configure_production()
        elif args.action == 'all':
            configure_production()
            clean_test_data()
            create_admin_user()
            verify_production_ready()
        
        logger.info("[SUCCESS] 操作完成")
        
    except Exception as e:
        logger.error(f"[ERROR] 操作失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()