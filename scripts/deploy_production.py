#!/usr/bin/env python3
"""
生产环境部署脚本

此脚本用于自动化部署系统审查技术项目到生产环境，包括：
1. 环境检查和准备
2. 依赖安装
3. 数据库迁移
4. 服务配置
5. 健康检查

使用方法:
    python scripts/deploy_production.py --env production
    python scripts/deploy_production.py --env staging --skip-tests
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProductionDeployer:
    """生产环境部署器"""

    def __init__(self, environment="production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.deployment_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 环境配置
        self.env_configs = {
            "production": {
                "env_file": ".env.production",
                "port": 8000,
                "workers": 4,
                "log_level": "info",
            },
            "staging": {
                "env_file": ".env.staging",
                "port": 8001,
                "workers": 2,
                "log_level": "debug",
            },
        }

    def check_prerequisites(self):
        """检查部署前提条件"""
        logger.info("检查部署前提条件...")

        try:
            # 检查Python版本
            python_version = sys.version_info
            if python_version.major < 3 or python_version.minor < 8:
                raise Exception(
                    f"需要Python 3.8+，当前版本: {python_version.major}.{python_version.minor}"
                )
            logger.info(
                f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
            )

            # 检查必要的系统命令
            required_commands = ["pip", "git"]
            for cmd in required_commands:
                if not shutil.which(cmd):
                    raise Exception(f"缺少必要命令: {cmd}")
                logger.info(f"✓ 命令可用: {cmd}")

            # 检查项目文件
            required_files = [
                "requirements.txt",
                "app/main.py",
                "app/core/config.py",
                "alembic.ini",
            ]

            for file_path in required_files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    raise Exception(f"缺少必要文件: {file_path}")
                logger.info(f"✓ 文件存在: {file_path}")

            # 检查环境配置文件
            env_file = self.env_configs[self.environment]["env_file"]
            env_path = self.project_root / env_file
            if not env_path.exists():
                raise Exception(f"缺少环境配置文件: {env_file}")
            logger.info(f"✓ 环境配置文件: {env_file}")

            logger.info("前提条件检查完成")
            return True

        except Exception as e:
            logger.error(f"前提条件检查失败: {e}")
            return False

    def setup_environment(self):
        """设置部署环境"""
        logger.info("设置部署环境...")

        try:
            # 创建必要目录
            directories = ["logs", "uploads", "backups", "temp", "static"]

            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                logger.info(f"✓ 目录创建: {directory}")

            # 复制环境配置文件
            env_file = self.env_configs[self.environment]["env_file"]
            source_env = self.project_root / env_file
            target_env = self.project_root / ".env"

            shutil.copy2(source_env, target_env)
            logger.info(f"✓ 环境配置复制: {env_file} -> .env")

            # 设置文件权限（Unix系统）
            if os.name != "nt":  # 非Windows系统
                os.chmod(target_env, 0o600)  # 只有所有者可读写
                logger.info("✓ 环境文件权限设置")

            logger.info("环境设置完成")
            return True

        except Exception as e:
            logger.error(f"环境设置失败: {e}")
            return False

    def install_dependencies(self):
        """安装项目依赖"""
        logger.info("安装项目依赖...")

        try:
            # 升级pip
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )
            logger.info("✓ pip已升级")

            # 安装生产依赖
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True,
                cwd=self.project_root,
            )
            logger.info("✓ 生产依赖已安装")

            # 安装额外的生产工具
            production_packages = [
                "gunicorn",  # WSGI服务器
                "uvicorn[standard]",  # ASGI服务器
                "psycopg2-binary",  # PostgreSQL驱动
                "redis",  # Redis客户端
                "prometheus-client",  # 监控指标
            ]

            for package in production_packages:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        check=True,
                        capture_output=True,
                    )
                    logger.info(f"✓ 生产工具已安装: {package}")
                except subprocess.CalledProcessError:
                    logger.warning(f"生产工具安装失败: {package}")

            logger.info("依赖安装完成")
            return True

        except Exception as e:
            logger.error(f"依赖安装失败: {e}")
            return False

    def run_database_migration(self):
        """运行数据库迁移"""
        logger.info("运行数据库迁移...")

        try:
            # 运行迁移脚本
            migration_script = (
                self.project_root / "scripts" / "migrate_to_production.py"
            )

            if migration_script.exists():
                subprocess.run(
                    [sys.executable, str(migration_script), "--action", "all"],
                    check=True,
                    cwd=self.project_root,
                )
                logger.info("✓ 数据库迁移完成")
            else:
                # 直接运行Alembic迁移
                subprocess.run(
                    ["alembic", "upgrade", "head"], check=True, cwd=self.project_root
                )
                logger.info("✓ Alembic迁移完成")

            return True

        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            return False

    def run_tests(self):
        """运行测试套件"""
        logger.info("运行测试套件...")

        try:
            # 检查是否有测试文件
            test_dirs = ["tests", "test"]
            test_files_found = False

            for test_dir in test_dirs:
                test_path = self.project_root / test_dir
                if test_path.exists() and any(test_path.glob("test_*.py")):
                    test_files_found = True
                    break

            if not test_files_found:
                logger.warning("未找到测试文件，跳过测试")
                return True

            # 运行pytest
            subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                check=True,
                cwd=self.project_root,
            )

            logger.info("✓ 测试通过")
            return True

        except subprocess.CalledProcessError:
            logger.error("测试失败")
            return False
        except Exception as e:
            logger.error(f"测试运行失败: {e}")
            return False

    def create_systemd_service(self):
        """创建systemd服务文件（Linux）"""
        if os.name == "nt":  # Windows系统
            logger.info("Windows系统，跳过systemd服务创建")
            return True

        logger.info("创建systemd服务文件...")

        try:
            config = self.env_configs[self.environment]
            service_name = f"sys-rev-tec-{self.environment}"

            service_content = f"""[Unit]
Description=System Review Technology - {self.environment.title()}
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory={self.project_root}
Environment=PATH={sys.executable}
EnvironmentFile={self.project_root}/.env
ExecStart={sys.executable} -m uvicorn app.main:app --host 0.0.0.0 --port {config["port"]} --workers {config["workers"]} --log-level {config["log_level"]}
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

            service_file = Path(f"/etc/systemd/system/{service_name}.service")

            # 检查是否有写入权限
            if os.access("/etc/systemd/system", os.W_OK):
                with open(service_file, "w") as f:
                    f.write(service_content)
                logger.info(f"✓ systemd服务文件已创建: {service_file}")

                # 重新加载systemd
                subprocess.run(["systemctl", "daemon-reload"], check=True)
                logger.info("✓ systemd已重新加载")
            else:
                # 保存到项目目录，提示手动复制
                local_service_file = self.project_root / f"{service_name}.service"
                with open(local_service_file, "w") as f:
                    f.write(service_content)
                logger.warning(f"权限不足，服务文件已保存到: {local_service_file}")
                logger.warning(f"请手动复制到: {service_file}")

            return True

        except Exception as e:
            logger.error(f"systemd服务创建失败: {e}")
            return False

    def create_nginx_config(self):
        """创建Nginx配置文件"""
        logger.info("创建Nginx配置文件...")

        try:
            config = self.env_configs[self.environment]
            server_name = f"sys-rev-tec-{self.environment}.local"

            nginx_content = f"""server {{
    listen 80;
    server_name {server_name};

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # 客户端最大请求体大小
    client_max_body_size 100M;

    # 静态文件
    location /static/ {{
        alias {self.project_root}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # 上传文件
    location /uploads/ {{
        alias {self.project_root}/uploads/;
        expires 1d;
    }}

    # API代理
    location / {{
        proxy_pass http://127.0.0.1:{config["port"]};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # 健康检查
    location /health {{
        access_log off;
        proxy_pass http://127.0.0.1:{config["port"]}/health;
    }}
}}
"""

            nginx_file = self.project_root / f"nginx-{self.environment}.conf"
            with open(nginx_file, "w") as f:
                f.write(nginx_content)

            logger.info(f"✓ Nginx配置文件已创建: {nginx_file}")
            logger.info("请将配置文件复制到Nginx配置目录并重新加载Nginx")

            return True

        except Exception as e:
            logger.error(f"Nginx配置创建失败: {e}")
            return False

    def health_check(self):
        """执行健康检查"""
        logger.info("执行健康检查...")

        try:
            # 导入配置以检查设置
            from app.core.config import settings

            logger.info(f"✓ 配置加载成功，环境: {settings.ENVIRONMENT}")

            # 检查数据库连接
            from sqlalchemy import text

            from app.db.session import engine

            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✓ 数据库连接正常")

            # 检查必要目录
            required_dirs = ["logs", "uploads", "temp"]
            for directory in required_dirs:
                dir_path = self.project_root / directory
                if dir_path.exists():
                    logger.info(f"✓ 目录存在: {directory}")
                else:
                    logger.warning(f"目录不存在: {directory}")

            logger.info("健康检查完成")
            return True

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    def create_deployment_info(self):
        """创建部署信息文件"""
        logger.info("创建部署信息文件...")

        try:
            deployment_info = {
                "deployment_time": self.deployment_time,
                "environment": self.environment,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "project_root": str(self.project_root),
                "config": self.env_configs[self.environment],
            }

            # 获取Git信息（如果可用）
            try:
                git_hash = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=self.project_root, text=True
                ).strip()
                deployment_info["git_commit"] = git_hash
            except:
                deployment_info["git_commit"] = "unknown"

            info_file = self.project_root / "deployment_info.json"
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(deployment_info, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ 部署信息文件已创建: {info_file}")
            return True

        except Exception as e:
            logger.error(f"部署信息文件创建失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生产环境部署工具")
    parser.add_argument(
        "--env",
        choices=["production", "staging"],
        default="production",
        help="部署环境",
    )
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试步骤")
    parser.add_argument("--skip-migration", action="store_true", help="跳过数据库迁移")
    parser.add_argument("--skip-services", action="store_true", help="跳过服务配置创建")

    args = parser.parse_args()

    deployer = ProductionDeployer(args.env)

    logger.info(f"开始部署到 {args.env} 环境")
    logger.info(f"部署时间: {deployer.deployment_time}")

    # 部署步骤
    steps = [
        ("检查前提条件", deployer.check_prerequisites),
        ("设置环境", deployer.setup_environment),
        ("安装依赖", deployer.install_dependencies),
    ]

    if not args.skip_migration:
        steps.append(("数据库迁移", deployer.run_database_migration))

    if not args.skip_tests:
        steps.append(("运行测试", deployer.run_tests))

    if not args.skip_services:
        steps.extend(
            [
                ("创建systemd服务", deployer.create_systemd_service),
                ("创建Nginx配置", deployer.create_nginx_config),
            ]
        )

    steps.extend(
        [
            ("健康检查", deployer.health_check),
            ("创建部署信息", deployer.create_deployment_info),
        ]
    )

    # 执行部署步骤
    success = True
    for step_name, step_func in steps:
        logger.info(f"执行步骤: {step_name}")
        if not step_func():
            logger.error(f"步骤失败: {step_name}")
            success = False
            break
        logger.info(f"步骤完成: {step_name}")

    if success:
        logger.info("🎉 部署成功完成！")
        logger.info(f"环境: {args.env}")
        logger.info(f"配置: {deployer.env_configs[args.env]}")
        logger.info("请检查服务状态并启动应用程序")
        sys.exit(0)
    else:
        logger.error("❌ 部署失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
