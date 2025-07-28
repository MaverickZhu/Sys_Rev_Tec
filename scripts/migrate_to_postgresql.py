#!/usr/bin/env python3
"""
数据库迁移脚本：SQLite -> PostgreSQL

使用方法:
    python scripts/migrate_to_postgresql.py --source sqlite:///./test.db --target postgresql://user:pass@localhost/dbname

注意事项:
1. 运行前请确保目标PostgreSQL数据库已创建
2. 建议先备份原数据库
3. 迁移过程中会保持数据完整性
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入模型
from app.db.base import Base
from app.models.document import Document
from app.models.issue import Issue
from app.models.ocr_result import OCRResult
from app.models.project import Project
from app.models.project_comparison import ProjectComparison
from app.models.user import User

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """数据库迁移器"""

    def __init__(self, source_url: str, target_url: str):
        self.source_url = source_url
        self.target_url = target_url
        self.source_engine = None
        self.target_engine = None
        self.source_session = None
        self.target_session = None

    def connect_databases(self):
        """连接源数据库和目标数据库"""
        try:
            # 连接源数据库
            logger.info(f"连接源数据库: {self.source_url}")
            self.source_engine = create_engine(self.source_url)
            SourceSession = sessionmaker(bind=self.source_engine)
            self.source_session = SourceSession()

            # 连接目标数据库
            logger.info(f"连接目标数据库: {self.target_url}")
            self.target_engine = create_engine(self.target_url)
            TargetSession = sessionmaker(bind=self.target_engine)
            self.target_session = TargetSession()

            # 测试连接
            self.source_session.execute(text("SELECT 1"))
            self.target_session.execute(text("SELECT 1"))

            logger.info("数据库连接成功")

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def create_target_schema(self):
        """在目标数据库中创建表结构"""
        try:
            logger.info("创建目标数据库表结构...")
            Base.metadata.create_all(bind=self.target_engine)
            logger.info("表结构创建成功")
        except Exception as e:
            logger.error(f"创建表结构失败: {e}")
            raise

    def get_table_data_count(self, session, model_class) -> int:
        """获取表中数据数量"""
        try:
            return session.query(model_class).count()
        except Exception as e:
            logger.warning(f"获取表 {model_class.__tablename__} 数据数量失败: {e}")
            return 0

    def migrate_table_data(self, model_class, batch_size: int = 1000):
        """迁移单个表的数据"""
        table_name = model_class.__tablename__
        logger.info(f"开始迁移表: {table_name}")

        try:
            # 获取源数据总数
            total_count = self.get_table_data_count(self.source_session, model_class)
            logger.info(f"表 {table_name} 共有 {total_count} 条记录")

            if total_count == 0:
                logger.info(f"表 {table_name} 无数据，跳过迁移")
                return

            # 分批迁移数据
            migrated_count = 0
            offset = 0

            while offset < total_count:
                # 从源数据库获取一批数据
                batch_data = (
                    self.source_session.query(model_class)
                    .offset(offset)
                    .limit(batch_size)
                    .all()
                )

                if not batch_data:
                    break

                # 将数据插入目标数据库
                for record in batch_data:
                    # 创建新记录（避免主键冲突）
                    record_dict = {}
                    for column in model_class.__table__.columns:
                        value = getattr(record, column.name)
                        record_dict[column.name] = value

                    new_record = model_class(**record_dict)
                    self.target_session.merge(new_record)

                # 提交批次
                self.target_session.commit()
                migrated_count += len(batch_data)
                offset += batch_size

                logger.info(
                    f"表 {table_name}: 已迁移 {migrated_count}/{total_count} 条记录"
                )

            logger.info(f"表 {table_name} 迁移完成，共迁移 {migrated_count} 条记录")

        except Exception as e:
            logger.error(f"迁移表 {table_name} 失败: {e}")
            self.target_session.rollback()
            raise

    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info("开始验证迁移结果...")

        verification_result = {"success": True, "tables": {}, "errors": []}

        # 要验证的模型列表
        models_to_verify = [
            User,
            Project,
            Document,
            OCRResult,
            Issue,
            ProjectComparison,
        ]

        for model_class in models_to_verify:
            table_name = model_class.__tablename__
            try:
                source_count = self.get_table_data_count(
                    self.source_session, model_class
                )
                target_count = self.get_table_data_count(
                    self.target_session, model_class
                )

                verification_result["tables"][table_name] = {
                    "source_count": source_count,
                    "target_count": target_count,
                    "match": source_count == target_count,
                }

                if source_count != target_count:
                    error_msg = f"表 {table_name} 数据数量不匹配: 源={source_count}, 目标={target_count}"
                    verification_result["errors"].append(error_msg)
                    verification_result["success"] = False
                    logger.warning(error_msg)
                else:
                    logger.info(f"表 {table_name} 验证通过: {source_count} 条记录")

            except Exception as e:
                error_msg = f"验证表 {table_name} 时出错: {e}"
                verification_result["errors"].append(error_msg)
                verification_result["success"] = False
                logger.error(error_msg)

        return verification_result

    def run_migration(self):
        """执行完整的迁移流程"""
        try:
            logger.info("开始数据库迁移...")
            start_time = datetime.now()

            # 1. 连接数据库
            self.connect_databases()

            # 2. 创建目标数据库表结构
            self.create_target_schema()

            # 3. 迁移数据（按依赖顺序）
            migration_order = [
                User,  # 用户表（无外键依赖）
                Project,  # 项目表（依赖用户）
                Document,  # 文档表（依赖项目和用户）
                OCRResult,  # OCR结果表（依赖文档）
                Issue,  # 问题表（依赖项目和用户）
                ProjectComparison,  # 项目比较表（依赖项目和用户）
            ]

            for model_class in migration_order:
                self.migrate_table_data(model_class)

            # 4. 验证迁移结果
            verification_result = self.verify_migration()

            end_time = datetime.now()
            duration = end_time - start_time

            if verification_result["success"]:
                logger.info(f"数据库迁移成功完成！耗时: {duration}")
                logger.info("迁移摘要:")
                for table_name, info in verification_result["tables"].items():
                    logger.info(f"  {table_name}: {info['target_count']} 条记录")
            else:
                logger.error("数据库迁移验证失败！")
                for error in verification_result["errors"]:
                    logger.error(f"  - {error}")
                return False

            return True

        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            return False

        finally:
            # 关闭数据库连接
            if self.source_session:
                self.source_session.close()
            if self.target_session:
                self.target_session.close()
            if self.source_engine:
                self.source_engine.dispose()
            if self.target_engine:
                self.target_engine.dispose()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库迁移工具：SQLite -> PostgreSQL")
    parser.add_argument(
        "--source", required=True, help="源数据库URL (例如: sqlite:///./test.db)"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="目标数据库URL (例如: postgresql://user:pass@localhost/dbname)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="仅验证连接，不执行实际迁移"
    )

    args = parser.parse_args()

    # 创建迁移器
    migrator = DatabaseMigrator(args.source, args.target)

    if args.dry_run:
        logger.info("执行干运行模式，仅测试数据库连接...")
        try:
            migrator.connect_databases()
            logger.info("数据库连接测试成功！")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    else:
        # 执行完整迁移
        success = migrator.run_migration()
        return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
