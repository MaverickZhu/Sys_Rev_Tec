#!/usr/bin/env python3
"""
生产环境数据库迁移脚本

此脚本用于将开发环境的数据库迁移到生产环境，包括：
1. 数据库架构迁移
2. 数据备份和恢复
3. 索引优化
4. 性能调优

使用方法:
    python scripts/migrate_to_production.py --action backup
    python scripts/migrate_to_production.py --action migrate
    python scripts/migrate_to_production.py --action optimize
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

import alembic.config
from app.core.config import settings
from app.db.session import engine

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProductionMigrator:
    """生产环境迁移器"""

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_database(self):
        """备份当前数据库"""
        logger.info("开始备份数据库...")

        try:
            if "sqlite" in settings.DATABASE_URL.lower():
                self._backup_sqlite()
            elif "postgresql" in settings.DATABASE_URL.lower():
                self._backup_postgresql()
            else:
                logger.warning("不支持的数据库类型，跳过备份")
                return False

            logger.info("数据库备份完成")
            return True

        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False

    def _backup_sqlite(self):
        """备份SQLite数据库"""
        import shutil

        # 提取数据库文件路径
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            backup_path = self.backup_dir / f"database_backup_{self.timestamp}.db"
            shutil.copy2(db_path, backup_path)
            logger.info(f"SQLite数据库已备份到: {backup_path}")
        else:
            logger.warning(f"数据库文件不存在: {db_path}")

    def _backup_postgresql(self):
        """备份PostgreSQL数据库"""
        # 解析数据库URL
        import urllib.parse as urlparse

        parsed = urlparse.urlparse(settings.DATABASE_URL)

        backup_file = self.backup_dir / f"postgres_backup_{self.timestamp}.sql"

        cmd = [
            "pg_dump",
            "-h",
            parsed.hostname,
            "-p",
            str(parsed.port or 5432),
            "-U",
            parsed.username,
            "-d",
            parsed.path[1:],  # 移除开头的'/'
            "-f",
            str(backup_file),
            "--verbose",
        ]

        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"PostgreSQL数据库已备份到: {backup_file}")
        else:
            raise Exception(f"pg_dump失败: {result.stderr}")

    def run_migrations(self):
        """运行数据库迁移"""
        logger.info("开始运行数据库迁移...")

        try:
            # 运行Alembic迁移
            alembic_cfg = alembic.config.Config("alembic.ini")

            # 检查当前迁移状态
            from alembic import command
            from alembic.runtime.migration import MigrationContext
            from alembic.script import ScriptDirectory

            # 获取当前版本
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                logger.info(f"当前数据库版本: {current_rev}")

            # 获取最新版本
            script = ScriptDirectory.from_config(alembic_cfg)
            head_rev = script.get_current_head()
            logger.info(f"目标数据库版本: {head_rev}")

            if current_rev != head_rev:
                logger.info("执行数据库迁移...")
                command.upgrade(alembic_cfg, "head")
                logger.info("数据库迁移完成")
            else:
                logger.info("数据库已是最新版本，无需迁移")

            return True

        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            return False

    def optimize_database(self):
        """优化数据库性能"""
        logger.info("开始优化数据库...")

        try:
            with engine.connect() as connection:
                # 获取数据库类型
                inspect(engine)

                if "sqlite" in str(engine.url).lower():
                    self._optimize_sqlite(connection)
                elif "postgresql" in str(engine.url).lower():
                    self._optimize_postgresql(connection)

                logger.info("数据库优化完成")
                return True

        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            return False

    def _optimize_sqlite(self, connection):
        """优化SQLite数据库"""
        logger.info("优化SQLite数据库...")

        # 分析表统计信息
        connection.execute(text("ANALYZE"))

        # 清理数据库
        connection.execute(text("VACUUM"))

        # 设置性能相关的PRAGMA
        pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL",
            "PRAGMA cache_size=10000",
            "PRAGMA temp_store=MEMORY",
            "PRAGMA mmap_size=268435456",  # 256MB
        ]

        for pragma in pragmas:
            connection.execute(text(pragma))
            logger.info(f"执行: {pragma}")

    def _optimize_postgresql(self, connection):
        """优化PostgreSQL数据库"""
        logger.info("优化PostgreSQL数据库...")

        # 更新表统计信息
        connection.execute(text("ANALYZE"))

        # 获取所有表名
        tables_result = connection.execute(
            text(
                """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """
            )
        )

        tables = [row[0] for row in tables_result]

        # 为每个表重建索引
        for table in tables:
            try:
                connection.execute(text(f"REINDEX TABLE {table}"))
                logger.info(f"重建表 {table} 的索引")
            except Exception as e:
                logger.warning(f"重建表 {table} 索引失败: {e}")

    def create_indexes(self):
        """创建生产环境推荐的索引"""
        logger.info("创建生产环境索引...")

        try:
            with engine.connect() as connection:
                # 检查表是否存在
                inspector = inspect(engine)
                tables = inspector.get_table_names()

                # 为用户表创建索引
                if "users" in tables:
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
                        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                    ]

                    for index_sql in indexes:
                        try:
                            connection.execute(text(index_sql))
                            logger.info(f"创建索引: {index_sql}")
                        except Exception as e:
                            logger.warning(f"索引创建失败: {e}")

                # 为项目表创建索引
                if "projects" in tables:
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)",
                        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
                        "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
                        "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
                    ]

                    for index_sql in indexes:
                        try:
                            connection.execute(text(index_sql))
                            logger.info(f"创建索引: {index_sql}")
                        except Exception as e:
                            logger.warning(f"索引创建失败: {e}")

                # 为文档表创建索引
                if "documents" in tables:
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)",
                        "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)",
                        "CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON documents(upload_time)",
                        "CREATE INDEX IF NOT EXISTS idx_documents_file_name ON documents(file_name)",
                    ]

                    for index_sql in indexes:
                        try:
                            connection.execute(text(index_sql))
                            logger.info(f"创建索引: {index_sql}")
                        except Exception as e:
                            logger.warning(f"索引创建失败: {e}")

                connection.commit()
                logger.info("生产环境索引创建完成")
                return True

        except Exception as e:
            logger.error(f"索引创建失败: {e}")
            return False

    def verify_migration(self):
        """验证迁移结果"""
        logger.info("验证迁移结果...")

        try:
            with engine.connect() as connection:
                # 检查数据库连接
                connection.execute(text("SELECT 1"))
                logger.info("✓ 数据库连接正常")

                # 检查表结构
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                logger.info(f"✓ 发现 {len(tables)} 个表: {', '.join(tables)}")

                # 检查关键表的记录数
                for table in ["users", "projects", "documents"]:
                    if table in tables:
                        result = connection.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        count = result.scalar()
                        logger.info(f"✓ 表 {table} 包含 {count} 条记录")

                # 检查索引
                for table in tables:
                    indexes = inspector.get_indexes(table)
                    logger.info(f"✓ 表 {table} 包含 {len(indexes)} 个索引")

                logger.info("迁移验证完成")
                return True

        except Exception as e:
            logger.error(f"迁移验证失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生产环境数据库迁移工具")
    parser.add_argument(
        "--action",
        choices=["backup", "migrate", "optimize", "indexes", "verify", "all"],
        required=True,
        help="要执行的操作",
    )
    parser.add_argument("--skip-backup", action="store_true", help="跳过备份步骤")

    args = parser.parse_args()

    migrator = ProductionMigrator()
    success = True

    logger.info(f"开始执行操作: {args.action}")
    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    logger.info(f"环境: {settings.ENVIRONMENT}")

    if args.action == "backup":
        success = migrator.backup_database()

    elif args.action == "migrate":
        if not args.skip_backup:
            success = migrator.backup_database()
        if success:
            success = migrator.run_migrations()

    elif args.action == "optimize":
        success = migrator.optimize_database()

    elif args.action == "indexes":
        success = migrator.create_indexes()

    elif args.action == "verify":
        success = migrator.verify_migration()

    elif args.action == "all":
        # 执行完整的迁移流程
        steps = [
            (
                "备份数据库",
                lambda: migrator.backup_database() if not args.skip_backup else True,
            ),
            ("运行迁移", migrator.run_migrations),
            ("创建索引", migrator.create_indexes),
            ("优化数据库", migrator.optimize_database),
            ("验证结果", migrator.verify_migration),
        ]

        for step_name, step_func in steps:
            logger.info(f"执行步骤: {step_name}")
            if not step_func():
                logger.error(f"步骤失败: {step_name}")
                success = False
                break
            logger.info(f"步骤完成: {step_name}")

    if success:
        logger.info("✅ 操作成功完成")
        sys.exit(0)
    else:
        logger.error("❌ 操作失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
