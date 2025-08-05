#!/usr/bin/env python3
"""初始化测试用户脚本

这个脚本用于在数据库中创建测试用户，包括：
- admin (超级管理员)
- reviewer (审查员)
- analyst (数据分析师)
- operator (系统操作员)
- manager (部门经理)

使用方法：
    python -m app.scripts.init_test_users
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal
from app.db.init_data import init_default_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("开始初始化测试用户...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化默认数据和测试用户
        init_default_data(db, create_test_users=True)
        logger.info("测试用户初始化完成！")
        
        # 显示创建的测试用户信息
        logger.info("\n=== 测试用户信息 ===")
        logger.info("用户名: admin, 密码: admin123, 角色: 超级管理员")
        logger.info("用户名: reviewer, 密码: reviewer123, 角色: 审查员")
        logger.info("用户名: analyst, 密码: analyst123, 角色: 数据分析师")
        logger.info("用户名: operator, 密码: operator123, 角色: 系统操作员")
        logger.info("用户名: manager, 密码: manager123, 角色: 部门经理")
        logger.info("===================")
        
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)