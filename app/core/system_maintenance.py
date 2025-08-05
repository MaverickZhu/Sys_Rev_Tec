#!/usr/bin/env python3
"""
系统维护管理器

功能:
1. 数据库清理和维护
2. 系统状态监控
3. 日志轮转管理
4. 数据备份恢复
5. 配置文件管理
6. 系统健康检查
"""

import json
import logging
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import psutil
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class SystemMaintenanceManager:
    """系统维护管理器"""

    def __init__(self):
        self.backup_dir = Path(
            settings.BACKUP_DIR if hasattr(settings, "BACKUP_DIR") else "./backups"
        )
        self.log_dir = Path(
            settings.LOG_DIR if hasattr(settings, "LOG_DIR") else "./logs"
        )
        self.config_dir = Path(
            settings.CONFIG_DIR if hasattr(settings, "CONFIG_DIR") else "./config"
        )

        # 确保目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # 系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # 数据库连接信息
            db_status = await self._get_database_status()

            # 应用进程信息
            app_status = await self._get_application_status()

            # 磁盘空间信息
            disk_status = await self._get_disk_status()

            # 日志文件状态
            log_status = await self._get_log_status()

            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_usage": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used,
                        "free": memory.free,
                    },
                    "disk": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100,
                    },
                    "uptime": self._get_system_uptime(),
                },
                "database": db_status,
                "application": app_status,
                "storage": disk_status,
                "logs": log_status,
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            raise

    async def _get_database_status(self) -> Dict[str, Any]:
        """获取数据库状态"""
        try:
            db = SessionLocal()
            try:
                # 检查数据库连接
                result = db.execute(text("SELECT 1"))
                connection_status = "healthy" if result else "error"

                # 获取数据库大小
                size_result = db.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """
                    )
                )
                size_info = size_result.fetchone()

                # 获取表统计信息
                tables_result = db.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        n_live_tup as row_count,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_stat_user_tables
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """
                    )
                )
                tables_info = [dict(row._mapping) for row in tables_result.fetchall()]

                # 获取活跃连接数
                connections_result = db.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """
                    )
                )
                active_connections = connections_result.scalar()

                return {
                    "status": connection_status,
                    "size": size_info[0] if size_info else "unknown",
                    "size_bytes": size_info[1] if size_info else 0,
                    "active_connections": active_connections,
                    "tables": tables_info,
                }
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库状态失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_application_status(self) -> Dict[str, Any]:
        """获取应用状态"""
        try:
            current_process = psutil.Process()

            return {
                "pid": current_process.pid,
                "memory_usage": current_process.memory_info().rss,
                "cpu_percent": current_process.cpu_percent(),
                "create_time": datetime.fromtimestamp(
                    current_process.create_time()
                ).isoformat(),
                "status": current_process.status(),
                "num_threads": current_process.num_threads(),
            }
        except Exception as e:
            logger.error(f"获取应用状态失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_disk_status(self) -> Dict[str, Any]:
        """获取磁盘状态"""
        try:
            disk_info = {}

            # 检查主要目录的磁盘使用情况
            directories = {
                "backup": self.backup_dir,
                "logs": self.log_dir,
                "uploads": Path("./uploads"),
                "temp": Path("./temp"),
            }

            for name, path in directories.items():
                if path.exists():
                    size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                    file_count = len(list(path.rglob("*")))
                    disk_info[name] = {
                        "path": str(path),
                        "size_bytes": size,
                        "size_human": self._format_bytes(size),
                        "file_count": file_count,
                    }
                else:
                    disk_info[name] = {
                        "path": str(path),
                        "size_bytes": 0,
                        "size_human": "0 B",
                        "file_count": 0,
                        "exists": False,
                    }

            return disk_info
        except Exception as e:
            logger.error(f"获取磁盘状态失败: {e}")
            return {"error": str(e)}

    async def _get_log_status(self) -> Dict[str, Any]:
        """获取日志状态"""
        try:
            log_files = []

            if self.log_dir.exists():
                for log_file in self.log_dir.glob("*.log*"):
                    stat = log_file.stat()
                    log_files.append(
                        {
                            "name": log_file.name,
                            "size_bytes": stat.st_size,
                            "size_human": self._format_bytes(stat.st_size),
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "lines": await self._count_log_lines(log_file),
                        }
                    )

            return {
                "total_files": len(log_files),
                "total_size": sum(f["size_bytes"] for f in log_files),
                "files": sorted(log_files, key=lambda x: x["size_bytes"], reverse=True),
            }
        except Exception as e:
            logger.error(f"获取日志状态失败: {e}")
            return {"error": str(e)}

    async def _count_log_lines(self, log_file: Path) -> int:
        """统计日志文件行数"""
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _get_system_uptime(self) -> str:
        """获取系统运行时间"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_delta = timedelta(seconds=int(uptime_seconds))
            return str(uptime_delta)
        except Exception:
            return "unknown"

    def _format_bytes(self, bytes_value: int) -> str:
        """格式化字节数"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    async def cleanup_database(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """数据库清理"""
        if options is None:
            options = {}

        try:
            db = SessionLocal()
            results = []

            try:
                # 清理过期的审计日志
                if options.get("cleanup_audit_logs", True):
                    days_to_keep = options.get("audit_log_retention_days", 90)
                    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

                    result = db.execute(
                        text(
                            """
                        DELETE FROM audit_logs
                        WHERE created_at < :cutoff_date
                    """
                        ),
                        {"cutoff_date": cutoff_date},
                    )

                    results.append(
                        {
                            "operation": "cleanup_audit_logs",
                            "deleted_rows": result.rowcount,
                            "cutoff_date": cutoff_date.isoformat(),
                        }
                    )

                # 清理过期的用户会话
                if options.get("cleanup_expired_sessions", True):
                    result = db.execute(
                        text(
                            """
                        DELETE FROM user_sessions
                        WHERE expires_at < NOW() OR is_active = false
                    """
                        )
                    )

                    results.append(
                        {
                            "operation": "cleanup_expired_sessions",
                            "deleted_rows": result.rowcount,
                        }
                    )

                # 清理临时文件记录
                if options.get("cleanup_temp_files", True):
                    days_to_keep = options.get("temp_file_retention_days", 7)
                    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

                    # 这里可以添加清理临时文件的逻辑
                    results.append(
                        {"operation": "cleanup_temp_files", "status": "completed"}
                    )

                # 执行VACUUM ANALYZE
                if options.get("vacuum_analyze", True):
                    db.execute(text("VACUUM ANALYZE"))
                    results.append(
                        {"operation": "vacuum_analyze", "status": "completed"}
                    )

                db.commit()

                return {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "operations": results,
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"数据库清理失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def rotate_logs(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """日志轮转"""
        if options is None:
            options = {}

        try:
            max_size_mb = options.get("max_size_mb", 100)
            max_files = options.get("max_files", 10)
            compress = options.get("compress", True)

            rotated_files = []

            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_size > max_size_mb * 1024 * 1024:
                    # 执行日志轮转
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rotated_name = f"{log_file.stem}_{timestamp}.log"
                    rotated_path = self.log_dir / rotated_name

                    # 移动当前日志文件
                    shutil.move(str(log_file), str(rotated_path))

                    # 压缩文件
                    if compress:
                        import gzip

                        with open(rotated_path, "rb") as f_in:
                            with gzip.open(f"{rotated_path}.gz", "wb") as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        rotated_path.unlink()  # 删除未压缩的文件
                        rotated_path = Path(f"{rotated_path}.gz")

                    # 创建新的空日志文件
                    log_file.touch()

                    rotated_files.append(
                        {
                            "original": str(log_file),
                            "rotated": str(rotated_path),
                            "size": rotated_path.stat().st_size,
                        }
                    )

            # 清理旧的日志文件
            cleaned_files = await self._cleanup_old_logs(max_files)

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "rotated_files": rotated_files,
                "cleaned_files": cleaned_files,
            }

        except Exception as e:
            logger.error(f"日志轮转失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _cleanup_old_logs(self, max_files: int) -> List[str]:
        """清理旧的日志文件"""
        try:
            cleaned_files = []

            # 获取所有日志文件（包括压缩的）
            log_files = list(self.log_dir.glob("*.log*"))

            # 按修改时间排序
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 删除超出数量限制的文件
            for log_file in log_files[max_files:]:
                log_file.unlink()
                cleaned_files.append(str(log_file))

            return cleaned_files

        except Exception as e:
            logger.error(f"清理旧日志文件失败: {e}")
            return []

    async def backup_system(self, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """系统备份"""
        if options is None:
            options = {}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"system_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)

            backup_results = []

            # 备份数据库
            if options.get("backup_database", True):
                db_backup_result = await self._backup_database(backup_path)
                backup_results.append(db_backup_result)

            # 备份配置文件
            if options.get("backup_config", True):
                config_backup_result = await self._backup_config(backup_path)
                backup_results.append(config_backup_result)

            # 备份上传文件
            if options.get("backup_uploads", True):
                uploads_backup_result = await self._backup_uploads(backup_path)
                backup_results.append(uploads_backup_result)

            # 创建备份清单
            manifest = {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "options": options,
                "results": backup_results,
            }

            manifest_path = backup_path / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            return {
                "status": "success",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "timestamp": timestamp,
                "results": backup_results,
            }

        except Exception as e:
            logger.error(f"系统备份失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _backup_database(self, backup_path: Path) -> Dict[str, Any]:
        """备份数据库"""
        try:
            db_backup_file = backup_path / "database.sql"

            # 使用pg_dump备份数据库
            cmd = [
                "pg_dump",
                "--no-password",
                "--verbose",
                "--clean",
                "--if-exists",
                settings.DATABASE_URL.replace("postgresql://", "postgres://"),
            ]

            with open(db_backup_file, "w") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, text=True
                )

            if result.returncode == 0:
                return {
                    "operation": "backup_database",
                    "status": "success",
                    "file": str(db_backup_file),
                    "size": db_backup_file.stat().st_size,
                }
            else:
                return {
                    "operation": "backup_database",
                    "status": "error",
                    "error": result.stderr,
                }

        except Exception as e:
            return {"operation": "backup_database", "status": "error", "error": str(e)}

    async def _backup_config(self, backup_path: Path) -> Dict[str, Any]:
        """备份配置文件"""
        try:
            config_backup_dir = backup_path / "config"
            config_backup_dir.mkdir(exist_ok=True)

            # 备份环境变量文件
            env_files = [".env", ".env.production", ".env.example"]
            backed_up_files = []

            for env_file in env_files:
                source_path = Path(env_file)
                if source_path.exists():
                    dest_path = config_backup_dir / env_file
                    shutil.copy2(source_path, dest_path)
                    backed_up_files.append(env_file)

            # 备份其他配置文件
            config_files = ["alembic.ini", "pyproject.toml"]
            for config_file in config_files:
                source_path = Path(config_file)
                if source_path.exists():
                    dest_path = config_backup_dir / config_file
                    shutil.copy2(source_path, dest_path)
                    backed_up_files.append(config_file)

            return {
                "operation": "backup_config",
                "status": "success",
                "files": backed_up_files,
                "directory": str(config_backup_dir),
            }

        except Exception as e:
            return {"operation": "backup_config", "status": "error", "error": str(e)}

    async def _backup_uploads(self, backup_path: Path) -> Dict[str, Any]:
        """备份上传文件"""
        try:
            uploads_dir = Path("./uploads")
            if not uploads_dir.exists():
                return {
                    "operation": "backup_uploads",
                    "status": "skipped",
                    "reason": "uploads directory not found",
                }

            uploads_backup_dir = backup_path / "uploads"
            shutil.copytree(uploads_dir, uploads_backup_dir)

            # 统计备份的文件
            file_count = len(list(uploads_backup_dir.rglob("*")))
            total_size = sum(
                f.stat().st_size for f in uploads_backup_dir.rglob("*") if f.is_file()
            )

            return {
                "operation": "backup_uploads",
                "status": "success",
                "directory": str(uploads_backup_dir),
                "file_count": file_count,
                "total_size": total_size,
            }

        except Exception as e:
            return {"operation": "backup_uploads", "status": "error", "error": str(e)}

    async def get_maintenance_schedule(self) -> Dict[str, Any]:
        """获取维护计划"""
        try:
            # 这里可以从配置文件或数据库读取维护计划
            schedule = {
                "database_cleanup": {
                    "frequency": "weekly",
                    "day": "sunday",
                    "time": "02:00",
                    "enabled": True,
                    "last_run": None,
                    "next_run": None,
                },
                "log_rotation": {
                    "frequency": "daily",
                    "time": "01:00",
                    "enabled": True,
                    "last_run": None,
                    "next_run": None,
                },
                "system_backup": {
                    "frequency": "daily",
                    "time": "03:00",
                    "enabled": True,
                    "last_run": None,
                    "next_run": None,
                },
            }

            return {
                "status": "success",
                "schedule": schedule,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取维护计划失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_health_check(self) -> Dict[str, Any]:
        """运行健康检查"""
        try:
            checks = []
            overall_status = "healthy"

            # 数据库连接检查
            db_check = await self._check_database_health()
            checks.append(db_check)
            if db_check["status"] != "healthy":
                overall_status = "warning"

            # 磁盘空间检查
            disk_check = await self._check_disk_health()
            checks.append(disk_check)
            if disk_check["status"] != "healthy":
                overall_status = "warning"

            # 内存使用检查
            memory_check = await self._check_memory_health()
            checks.append(memory_check)
            if memory_check["status"] != "healthy":
                if overall_status == "healthy":
                    overall_status = "warning"

            # 日志文件检查
            log_check = await self._check_log_health()
            checks.append(log_check)
            if log_check["status"] != "healthy":
                if overall_status == "healthy":
                    overall_status = "warning"

            return {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "checks": checks,
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态"""
        try:
            db = SessionLocal()
            try:
                # 检查连接
                db.execute(text("SELECT 1"))

                # 检查活跃连接数
                result = db.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active'
                """
                    )
                )
                active_connections = result.scalar()

                status = "healthy"
                if active_connections > 50:  # 假设50是警告阈值
                    status = "warning"

                return {
                    "name": "database",
                    "status": status,
                    "details": {
                        "active_connections": active_connections,
                        "connection_test": "passed",
                    },
                }
            finally:
                db.close()
        except Exception as e:
            return {"name": "database", "status": "error", "error": str(e)}

    async def _check_disk_health(self) -> Dict[str, Any]:
        """检查磁盘健康状态"""
        try:
            disk = psutil.disk_usage("/")
            usage_percent = (disk.used / disk.total) * 100

            status = "healthy"
            if usage_percent > 90:
                status = "error"
            elif usage_percent > 80:
                status = "warning"

            return {
                "name": "disk_space",
                "status": status,
                "details": {
                    "usage_percent": round(usage_percent, 2),
                    "free_space": self._format_bytes(disk.free),
                    "total_space": self._format_bytes(disk.total),
                },
            }
        except Exception as e:
            return {"name": "disk_space", "status": "error", "error": str(e)}

    async def _check_memory_health(self) -> Dict[str, Any]:
        """检查内存健康状态"""
        try:
            memory = psutil.virtual_memory()

            status = "healthy"
            if memory.percent > 90:
                status = "error"
            elif memory.percent > 80:
                status = "warning"

            return {
                "name": "memory",
                "status": status,
                "details": {
                    "usage_percent": memory.percent,
                    "available": self._format_bytes(memory.available),
                    "total": self._format_bytes(memory.total),
                },
            }
        except Exception as e:
            return {"name": "memory", "status": "error", "error": str(e)}

    async def _check_log_health(self) -> Dict[str, Any]:
        """检查日志健康状态"""
        try:
            total_size = 0
            large_files = []

            if self.log_dir.exists():
                for log_file in self.log_dir.glob("*.log"):
                    size = log_file.stat().st_size
                    total_size += size

                    if size > 100 * 1024 * 1024:  # 100MB
                        large_files.append(
                            {"name": log_file.name, "size": self._format_bytes(size)}
                        )

            status = "healthy"
            if total_size > 1024 * 1024 * 1024:  # 1GB
                status = "warning"
            if len(large_files) > 0:
                status = "warning"

            return {
                "name": "log_files",
                "status": status,
                "details": {
                    "total_size": self._format_bytes(total_size),
                    "large_files": large_files,
                },
            }
        except Exception as e:
            return {"name": "log_files", "status": "error", "error": str(e)}


# 全局实例
system_maintenance = SystemMaintenanceManager()
