#!/usr/bin/env python3
"""
Docker 容器化部署脚本
用于自动化部署系统审查技术项目到 Docker 容器环境

功能:
- 环境检查和准备
- Docker 镜像构建
- 容器编排和启动
- 健康检查和监控
- 日志收集和分析
- 备份和恢复

使用方法:
    python docker_deploy.py --env production --action deploy
    python docker_deploy.py --env development --action build
    python docker_deploy.py --action stop
    python docker_deploy.py --action logs --service app
    python docker_deploy.py --action backup
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings
except ImportError:
    print("警告: 无法导入配置文件，使用默认配置")
    settings = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("docker_deploy.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DockerDeployer:
    """Docker 容器化部署管理器"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = project_root
        self.compose_file = self.project_root / "docker-compose.yml"
        self.env_file = self.project_root / f".env.{environment}"

        # Docker 服务配置
        self.services = {
            "app": "系统审查技术应用",
            "postgres": "PostgreSQL 数据库",
            "redis": "Redis 缓存",
            "nginx": "Nginx 反向代理",
        }

        # 健康检查配置
        self.health_check_urls = {
            "app": "http://localhost:8000/health",
            "nginx": "http://localhost/health",
        }

        logger.info(f"初始化 Docker 部署器 - 环境: {environment}")

    def check_prerequisites(self) -> bool:
        """检查部署前置条件"""
        logger.info("检查部署前置条件...")

        # 检查 Docker
        if not self._check_docker():
            return False

        # 检查 Docker Compose
        if not self._check_docker_compose():
            return False

        # 检查必要文件
        required_files = [
            self.compose_file,
            self.project_root / "Dockerfile",
            self.project_root / "requirements.txt",
        ]

        for file_path in required_files:
            if not file_path.exists():
                logger.error(f"缺少必要文件: {file_path}")
                return False

        # 检查环境文件
        if not self.env_file.exists():
            logger.warning(f"环境文件不存在: {self.env_file}")
            logger.info("将使用默认的 .env 文件")
            self.env_file = self.project_root / ".env"

        # 检查磁盘空间
        if not self._check_disk_space():
            return False

        logger.info("前置条件检查通过")
        return True

    def _check_docker(self) -> bool:
        """检查 Docker 是否安装和运行"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, check=True
            )
            logger.info(f"Docker 版本: {result.stdout.strip()}")

            # 检查 Docker 守护进程
            subprocess.run(["docker", "info"], capture_output=True, check=True)
            logger.info("Docker 守护进程运行正常")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Docker 检查失败: {e}")
            return False

    def _check_docker_compose(self) -> bool:
        """检查 Docker Compose 是否安装"""
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Docker Compose 版本: {result.stdout.strip()}")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            # 尝试新版本的 docker compose 命令
            try:
                result = subprocess.run(
                    ["docker", "compose", "version"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logger.info(f"Docker Compose 版本: {result.stdout.strip()}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Docker Compose 检查失败: {e}")
                return False

    def _check_disk_space(self, min_gb: int = 5) -> bool:
        """检查磁盘空间"""
        try:
            import shutil

            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free // (1024**3)

            logger.info(f"可用磁盘空间: {free_gb} GB")

            if free_gb < min_gb:
                logger.error(f"磁盘空间不足，至少需要 {min_gb} GB")
                return False

            return True

        except Exception as e:
            logger.warning(f"无法检查磁盘空间: {e}")
            return True

    def build_images(self, no_cache: bool = False) -> bool:
        """构建 Docker 镜像"""
        logger.info("开始构建 Docker 镜像...")

        try:
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.append("build")

            if no_cache:
                cmd.append("--no-cache")

            subprocess.run(cmd, cwd=self.project_root, check=True)

            logger.info("Docker 镜像构建完成")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Docker 镜像构建失败: {e}")
            return False

    def deploy(self, recreate: bool = False) -> bool:
        """部署容器"""
        logger.info("开始部署容器...")

        try:
            # 停止现有容器（如果存在）
            if recreate:
                self.stop(remove_volumes=False)

            # 启动容器
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.extend(["up", "-d"])

            if recreate:
                cmd.append("--force-recreate")

            subprocess.run(cmd, cwd=self.project_root, check=True)

            logger.info("容器部署完成")

            # 等待服务启动
            time.sleep(10)

            # 执行健康检查
            if self.health_check():
                logger.info("部署成功，所有服务运行正常")
                return True
            else:
                logger.error("部署失败，服务健康检查未通过")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"容器部署失败: {e}")
            return False

    def stop(self, remove_volumes: bool = False) -> bool:
        """停止容器"""
        logger.info("停止容器...")

        try:
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.append("down")

            if remove_volumes:
                cmd.append("--volumes")

            subprocess.run(cmd, cwd=self.project_root, check=True)

            logger.info("容器已停止")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"停止容器失败: {e}")
            return False

    def restart(self, service: Optional[str] = None) -> bool:
        """重启容器"""
        service_name = service or "所有服务"
        logger.info(f"重启 {service_name}...")

        try:
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.append("restart")

            if service:
                cmd.append(service)

            subprocess.run(cmd, cwd=self.project_root, check=True)

            logger.info(f"{service_name} 重启完成")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"重启 {service_name} 失败: {e}")
            return False

    def get_status(self) -> Dict[str, str]:
        """获取容器状态"""
        logger.info("获取容器状态...")

        try:
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.extend(["ps", "--format", "json"])

            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, check=True
            )

            status = {}
            for line in result.stdout.strip().split("\n"):
                if line:
                    container_info = json.loads(line)
                    service = container_info.get("Service", "unknown")
                    state = container_info.get("State", "unknown")
                    status[service] = state

            return status

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"获取容器状态失败: {e}")
            return {}

    def get_logs(self, service: Optional[str] = None, tail: int = 100) -> bool:
        """获取容器日志"""
        service_name = service or "所有服务"
        logger.info(f"获取 {service_name} 日志...")

        try:
            cmd = ["docker-compose", "-f", str(self.compose_file)]

            if self.env_file.exists():
                cmd.extend(["--env-file", str(self.env_file)])

            cmd.extend(["logs", "--tail", str(tail)])

            if service:
                cmd.append(service)

            result = subprocess.run(cmd, cwd=self.project_root)

            return result.returncode == 0

        except subprocess.CalledProcessError as e:
            logger.error(f"获取日志失败: {e}")
            return False

    def health_check(self) -> bool:
        """执行健康检查"""
        logger.info("执行健康检查...")

        # 检查容器状态
        status = self.get_status()

        for service, description in self.services.items():
            if service not in status:
                logger.warning(f"服务 {service} ({description}) 未运行")
                continue

            if status[service] != "running":
                logger.error(
                    f"服务 {service} ({description}) 状态异常: {status[service]}"
                )
                return False

            logger.info(f"服务 {service} ({description}) 运行正常")

        # 检查服务健康状态
        import requests

        for service, url in self.health_check_urls.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"服务 {service} 健康检查通过")
                else:
                    logger.error(
                        f"服务 {service} 健康检查失败: HTTP {response.status_code}"
                    )
                    return False
            except requests.RequestException as e:
                logger.error(f"服务 {service} 健康检查失败: {e}")
                return False

        logger.info("所有服务健康检查通过")
        return True

    def backup_data(self) -> bool:
        """备份数据"""
        logger.info("开始数据备份...")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 备份数据库
            db_backup_file = backup_dir / "database.sql"

            cmd = [
                "docker-compose",
                "-f",
                str(self.compose_file),
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U",
                "postgres",
                "sys_rev_tech",
            ]

            with open(db_backup_file, "w") as f:
                subprocess.run(cmd, cwd=self.project_root, stdout=f, check=True)

            logger.info(f"数据库备份完成: {db_backup_file}")

            # 备份上传文件
            uploads_dir = self.project_root / "uploads"
            if uploads_dir.exists():
                import shutil

                uploads_backup = backup_dir / "uploads"
                shutil.copytree(uploads_dir, uploads_backup)
                logger.info(f"上传文件备份完成: {uploads_backup}")

            # 备份配置文件
            config_backup = backup_dir / "config"
            config_backup.mkdir(exist_ok=True)

            config_files = [
                ".env",
                ".env.production",
                ".env.development",
                "docker-compose.yml",
            ]

            for config_file in config_files:
                src = self.project_root / config_file
                if src.exists():
                    import shutil

                    shutil.copy2(src, config_backup / config_file)

            logger.info(f"配置文件备份完成: {config_backup}")

            # 创建备份信息文件
            backup_info = {
                "timestamp": timestamp,
                "environment": self.environment,
                "services": list(self.services.keys()),
                "backup_path": str(backup_dir),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            with open(backup_dir / "backup_info.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            logger.info(f"数据备份完成: {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"数据备份失败: {e}")
            return False

    def cleanup_old_images(self, keep_latest: int = 3) -> bool:
        """清理旧的 Docker 镜像"""
        logger.info("清理旧的 Docker 镜像...")

        try:
            # 清理未使用的镜像
            subprocess.run(["docker", "image", "prune", "-f"], check=True)

            # 清理未使用的容器
            subprocess.run(["docker", "container", "prune", "-f"], check=True)

            # 清理未使用的网络
            subprocess.run(["docker", "network", "prune", "-f"], check=True)

            # 清理未使用的卷（谨慎操作）
            # subprocess.run(
            #     ["docker", "volume", "prune", "-f"],
            #     check=True
            # )

            logger.info("Docker 镜像清理完成")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Docker 镜像清理失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Docker 容器化部署脚本")
    parser.add_argument(
        "--env",
        choices=["development", "production", "testing"],
        default="production",
        help="部署环境",
    )
    parser.add_argument(
        "--action",
        choices=[
            "build",
            "deploy",
            "stop",
            "restart",
            "status",
            "logs",
            "health",
            "backup",
            "cleanup",
        ],
        required=True,
        help="执行的操作",
    )
    parser.add_argument(
        "--service",
        choices=list(DockerDeployer("").services.keys()),
        help="指定服务（用于 restart、logs 等操作）",
    )
    parser.add_argument("--no-cache", action="store_true", help="构建时不使用缓存")
    parser.add_argument("--recreate", action="store_true", help="强制重新创建容器")
    parser.add_argument("--tail", type=int, default=100, help="日志行数")

    args = parser.parse_args()

    # 创建部署器
    deployer = DockerDeployer(args.env)

    # 执行操作
    success = False

    if args.action == "build":
        if deployer.check_prerequisites():
            success = deployer.build_images(no_cache=args.no_cache)

    elif args.action == "deploy":
        if deployer.check_prerequisites():
            if not deployer.build_images():
                logger.error("镜像构建失败，部署中止")
                sys.exit(1)
            success = deployer.deploy(recreate=args.recreate)

    elif args.action == "stop":
        success = deployer.stop()

    elif args.action == "restart":
        success = deployer.restart(args.service)

    elif args.action == "status":
        status = deployer.get_status()
        if status:
            print("\n容器状态:")
            for service, state in status.items():
                print(f"  {service}: {state}")
            success = True
        else:
            success = False

    elif args.action == "logs":
        success = deployer.get_logs(args.service, args.tail)

    elif args.action == "health":
        success = deployer.health_check()

    elif args.action == "backup":
        success = deployer.backup_data()

    elif args.action == "cleanup":
        success = deployer.cleanup_old_images()

    # 退出
    if success:
        logger.info(f"操作 '{args.action}' 执行成功")
        sys.exit(0)
    else:
        logger.error(f"操作 '{args.action}' 执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
