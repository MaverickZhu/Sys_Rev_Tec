#!/usr/bin/env python3
"""
数据库备份和恢复工具

功能:
1. 数据库备份（支持SQLite和PostgreSQL）
2. 数据库恢复
3. 自动备份调度
4. 备份文件管理

使用方法:
    # 备份数据库
    python scripts/backup_restore.py backup --database-url sqlite:///./test.db --output ./backups/

    # 恢复数据库
    python scripts/backup_restore.py restore --backup-file ./backups/backup_20231201_120000.sql --database-url postgresql://user:pass@localhost/dbname

    # 清理旧备份
    python scripts/backup_restore.py cleanup --backup-dir ./backups/ --keep-days 30
"""

import argparse
import gzip
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseBackupRestore:
    """数据库备份恢复工具"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session = None

    def connect(self):
        """连接数据库"""
        try:
            self.engine = create_engine(self.database_url)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            # 测试连接
            self.session.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def disconnect(self):
        """断开数据库连接"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()

    def is_sqlite(self) -> bool:
        """判断是否为SQLite数据库"""
        return self.database_url.startswith("sqlite")

    def is_postgresql(self) -> bool:
        """判断是否为PostgreSQL数据库"""
        return self.database_url.startswith("postgresql")

    def backup_sqlite(self, output_file: str) -> bool:
        """备份SQLite数据库"""
        try:
            # 从URL中提取数据库文件路径
            db_file = self.database_url.replace("sqlite:///", "")
            if not os.path.exists(db_file):
                logger.error(f"SQLite数据库文件不存在: {db_file}")
                return False

            logger.info(f"开始备份SQLite数据库: {db_file}")

            # 创建备份目录
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # 使用sqlite3命令行工具导出
            cmd = f'sqlite3 "{db_file}" ".dump"'

            with open(output_file, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, shell=True, stdout=f, stderr=subprocess.PIPE, text=True
                )

            if result.returncode == 0:
                logger.info(f"SQLite备份成功: {output_file}")
                return True
            else:
                logger.error(f"SQLite备份失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"SQLite备份异常: {e}")
            return False

    def backup_postgresql(self, output_file: str) -> bool:
        """备份PostgreSQL数据库"""
        try:
            # 解析PostgreSQL URL
            # postgresql://user:password@host:port/database
            url_parts = self.database_url.replace("postgresql://", "").split("/")
            database = url_parts[-1]
            auth_host = url_parts[0]

            if "@" in auth_host:
                auth, host_port = auth_host.split("@")
                if ":" in auth:
                    username, password = auth.split(":")
                else:
                    username = auth
                    password = ""
            else:
                host_port = auth_host
                username = "postgres"
                password = ""

            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host = host_port
                port = "5432"

            logger.info(f"开始备份PostgreSQL数据库: {database}")

            # 创建备份目录
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # 设置环境变量
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password

            # 使用pg_dump命令
            cmd = [
                "pg_dump",
                "-h",
                host,
                "-p",
                port,
                "-U",
                username,
                "-d",
                database,
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
            ]

            with open(output_file, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True
                )

            if result.returncode == 0:
                logger.info(f"PostgreSQL备份成功: {output_file}")
                return True
            else:
                logger.error(f"PostgreSQL备份失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"PostgreSQL备份异常: {e}")
            return False

    def backup(self, output_dir: str, compress: bool = True) -> Optional[str]:
        """执行数据库备份"""
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_type = "sqlite" if self.is_sqlite() else "postgresql"
            backup_filename = f"backup_{db_type}_{timestamp}.sql"
            backup_file = os.path.join(output_dir, backup_filename)

            # 连接数据库
            self.connect()

            # 执行备份
            success = False
            if self.is_sqlite():
                success = self.backup_sqlite(backup_file)
            elif self.is_postgresql():
                success = self.backup_postgresql(backup_file)
            else:
                logger.error("不支持的数据库类型")
                return None

            if not success:
                return None

            # 压缩备份文件
            if compress:
                compressed_file = backup_file + ".gz"
                with open(backup_file, "rb") as f_in:
                    with gzip.open(compressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 删除原始文件
                os.remove(backup_file)
                backup_file = compressed_file
                logger.info(f"备份文件已压缩: {backup_file}")

            # 创建备份元数据
            metadata = {
                "timestamp": timestamp,
                "database_type": db_type,
                "database_url": self.database_url,
                "backup_file": backup_file,
                "compressed": compress,
                "file_size": os.path.getsize(backup_file),
            }

            metadata_file = backup_file.replace(".sql", ".json").replace(".gz", ".json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"备份完成: {backup_file}")
            logger.info(f"备份大小: {metadata['file_size'] / 1024 / 1024:.2f} MB")

            return backup_file

        except Exception as e:
            logger.error(f"备份失败: {e}")
            return None
        finally:
            self.disconnect()

    def restore_sqlite(self, backup_file: str) -> bool:
        """恢复SQLite数据库"""
        try:
            # 从URL中提取数据库文件路径
            db_file = self.database_url.replace("sqlite:///", "")

            logger.info(f"开始恢复SQLite数据库: {db_file}")

            # 备份现有数据库
            if os.path.exists(db_file):
                backup_existing = (
                    f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                shutil.copy2(db_file, backup_existing)
                logger.info(f"现有数据库已备份到: {backup_existing}")

            # 解压备份文件（如果需要）
            restore_file = backup_file
            if backup_file.endswith(".gz"):
                restore_file = backup_file.replace(".gz", "")
                with gzip.open(backup_file, "rb") as f_in:
                    with open(restore_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # 使用sqlite3命令行工具恢复
            cmd = f'sqlite3 "{db_file}" < "{restore_file}"'

            result = subprocess.run(cmd, shell=True, stderr=subprocess.PIPE, text=True)

            # 清理临时文件
            if backup_file.endswith(".gz") and restore_file != backup_file:
                os.remove(restore_file)

            if result.returncode == 0:
                logger.info(f"SQLite恢复成功: {db_file}")
                return True
            else:
                logger.error(f"SQLite恢复失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"SQLite恢复异常: {e}")
            return False

    def restore_postgresql(self, backup_file: str) -> bool:
        """恢复PostgreSQL数据库"""
        try:
            # 解析PostgreSQL URL（与备份时相同）
            url_parts = self.database_url.replace("postgresql://", "").split("/")
            database = url_parts[-1]
            auth_host = url_parts[0]

            if "@" in auth_host:
                auth, host_port = auth_host.split("@")
                if ":" in auth:
                    username, password = auth.split(":")
                else:
                    username = auth
                    password = ""
            else:
                host_port = auth_host
                username = "postgres"
                password = ""

            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host = host_port
                port = "5432"

            logger.info(f"开始恢复PostgreSQL数据库: {database}")

            # 解压备份文件（如果需要）
            restore_file = backup_file
            if backup_file.endswith(".gz"):
                restore_file = backup_file.replace(".gz", "")
                with gzip.open(backup_file, "rb") as f_in:
                    with open(restore_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # 设置环境变量
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password

            # 使用psql命令恢复
            cmd = [
                "psql",
                "-h",
                host,
                "-p",
                port,
                "-U",
                username,
                "-d",
                database,
                "-f",
                restore_file,
                "--quiet",
            ]

            result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env, text=True)

            # 清理临时文件
            if backup_file.endswith(".gz") and restore_file != backup_file:
                os.remove(restore_file)

            if result.returncode == 0:
                logger.info(f"PostgreSQL恢复成功: {database}")
                return True
            else:
                logger.error(f"PostgreSQL恢复失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"PostgreSQL恢复异常: {e}")
            return False

    def restore(self, backup_file: str) -> bool:
        """执行数据库恢复"""
        try:
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False

            # 连接数据库
            self.connect()

            # 执行恢复
            success = False
            if self.is_sqlite():
                success = self.restore_sqlite(backup_file)
            elif self.is_postgresql():
                success = self.restore_postgresql(backup_file)
            else:
                logger.error("不支持的数据库类型")
                return False

            return success

        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return False
        finally:
            self.disconnect()


def cleanup_old_backups(backup_dir: str, keep_days: int) -> int:
    """清理旧的备份文件"""
    try:
        if not os.path.exists(backup_dir):
            logger.warning(f"备份目录不存在: {backup_dir}")
            return 0

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        logger.info(f"清理 {keep_days} 天前的备份文件...")

        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and (
                filename.endswith(".sql")
                or filename.endswith(".gz")
                or filename.endswith(".json")
            ):
                file_path = os.path.join(backup_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"删除旧备份文件: {filename}")

        logger.info(f"清理完成，删除了 {deleted_count} 个文件")
        return deleted_count

    except Exception as e:
        logger.error(f"清理备份文件失败: {e}")
        return 0


def list_backups(backup_dir: str) -> List[Dict]:
    """列出所有备份文件"""
    backups = []

    try:
        if not os.path.exists(backup_dir):
            return backups

        for filename in os.listdir(backup_dir):
            if filename.startswith("backup_") and (
                filename.endswith(".sql") or filename.endswith(".gz")
            ):
                file_path = os.path.join(backup_dir, filename)
                metadata_file = file_path.replace(".sql", ".json").replace(
                    ".gz", ".json"
                )

                backup_info = {
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(file_path)),
                }

                # 读取元数据
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, encoding="utf-8") as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except Exception:
                        pass

                backups.append(backup_info)

        # 按时间排序
        backups.sort(key=lambda x: x["mtime"], reverse=True)

    except Exception as e:
        logger.error(f"列出备份文件失败: {e}")

    return backups


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库备份恢复工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 备份命令
    backup_parser = subparsers.add_parser("backup", help="备份数据库")
    backup_parser.add_argument("--database-url", required=True, help="数据库URL")
    backup_parser.add_argument("--output", required=True, help="备份输出目录")
    backup_parser.add_argument(
        "--no-compress", action="store_true", help="不压缩备份文件"
    )

    # 恢复命令
    restore_parser = subparsers.add_parser("restore", help="恢复数据库")
    restore_parser.add_argument("--backup-file", required=True, help="备份文件路径")
    restore_parser.add_argument("--database-url", required=True, help="目标数据库URL")

    # 清理命令
    cleanup_parser = subparsers.add_parser("cleanup", help="清理旧备份")
    cleanup_parser.add_argument("--backup-dir", required=True, help="备份目录")
    cleanup_parser.add_argument(
        "--keep-days", type=int, default=30, help="保留天数（默认30天）"
    )

    # 列表命令
    list_parser = subparsers.add_parser("list", help="列出备份文件")
    list_parser.add_argument("--backup-dir", required=True, help="备份目录")

    args = parser.parse_args()

    if args.command == "backup":
        tool = DatabaseBackupRestore(args.database_url)
        backup_file = tool.backup(args.output, compress=not args.no_compress)
        return backup_file is not None

    elif args.command == "restore":
        tool = DatabaseBackupRestore(args.database_url)
        return tool.restore(args.backup_file)

    elif args.command == "cleanup":
        cleanup_old_backups(args.backup_dir, args.keep_days)
        return True

    elif args.command == "list":
        backups = list_backups(args.backup_dir)
        if backups:
            print(f"找到 {len(backups)} 个备份文件:")
            for backup in backups:
                size_mb = backup["size"] / 1024 / 1024
                print(f"  {backup['filename']} ({size_mb:.2f} MB) - {backup['mtime']}")
        else:
            print("未找到备份文件")
        return True

    else:
        parser.print_help()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
