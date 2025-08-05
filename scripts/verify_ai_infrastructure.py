#!/usr/bin/env python3
"""
AI基础设施验证脚本
用于验证向量数据库、AI服务和相关组件是否正确配置和运行

使用方法:
    python scripts/verify_ai_infrastructure.py
    python scripts/verify_ai_infrastructure.py --verbose
    python scripts/verify_ai_infrastructure.py --check-models
"""

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
    import psycopg2
    import redis
except ImportError as e:
    print(f"❌ 缺少必要的依赖包: {e}")
    print("请运行: pip install psycopg2-binary redis httpx numpy")
    sys.exit(1)


class CheckStatus(Enum):
    """检查状态枚举"""

    PASS = "✅"
    FAIL = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"


@dataclass
class CheckResult:
    """检查结果数据类"""

    name: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None


class AIInfrastructureVerifier:
    """AI基础设施验证器"""

    def __init__(self, verbose: bool = False, check_models: bool = False):
        self.verbose = verbose
        self.check_models = check_models
        self.results: List[CheckResult] = []

        # 配置信息
        self.config = {
            "database_url": os.getenv(
                "DATABASE_URL",
                "postgresql://sys_rev_user:CHANGE_PASSWORD@127.0.0.1:5432/sys_rev_tec_prod",
            ),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ai_service_url": "http://localhost:8001",
            "app_service_url": "http://localhost:8000",
        }

    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")

    def add_result(self, result: CheckResult):
        """添加检查结果"""
        self.results.append(result)
        status_icon = result.status.value
        duration_info = f" ({result.duration_ms:.1f}ms)" if result.duration_ms else ""
        print(f"{status_icon} {result.name}{duration_info}: {result.message}")

        if self.verbose and result.details:
            for key, value in result.details.items():
                print(f"    {key}: {value}")

    async def check_database_connection(self) -> CheckResult:
        """检查数据库连接"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(self.config["database_url"])
            cur = conn.cursor()

            # 检查基本连接
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]

            details = {"postgres_version": version}

            conn.close()
            duration_ms = (time.time() - start_time) * 1000

            return CheckResult(
                name="数据库连接",
                status=CheckStatus.PASS,
                message="PostgreSQL连接成功",
                details=details,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="数据库连接",
                status=CheckStatus.FAIL,
                message=f"数据库连接失败: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_pgvector_extension(self) -> CheckResult:
        """检查pgvector扩展"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(self.config["database_url"])
            cur = conn.cursor()

            # 检查pgvector扩展
            cur.execute(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
            )
            result = cur.fetchone()

            if result:
                ext_name, ext_version = result
                details = {"extension_version": ext_version}

                # 测试向量操作
                cur.execute("SELECT '[1,2,3]'::vector;")
                cur.fetchone()[0]

                conn.close()
                duration_ms = (time.time() - start_time) * 1000

                return CheckResult(
                    name="pgvector扩展",
                    status=CheckStatus.PASS,
                    message=f"pgvector扩展已安装 (版本: {ext_version})",
                    details=details,
                    duration_ms=duration_ms,
                )
            else:
                conn.close()
                duration_ms = (time.time() - start_time) * 1000
                return CheckResult(
                    name="pgvector扩展",
                    status=CheckStatus.FAIL,
                    message="pgvector扩展未安装",
                    duration_ms=duration_ms,
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="pgvector扩展",
                status=CheckStatus.FAIL,
                message=f"pgvector扩展检查失败: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_vector_tables(self) -> CheckResult:
        """检查向量数据表"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(self.config["database_url"])
            cur = conn.cursor()

            # 检查必要的表是否存在
            required_tables = [
                "document_vectors",
                "vector_search_history",
                "vector_index_stats",
            ]
            existing_tables = []

            for table in required_tables:
                cur.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);",
                    (table,),
                )
                if cur.fetchone()[0]:
                    existing_tables.append(table)

            # 检查索引
            cur.execute(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'document_vectors'
                AND indexname LIKE '%embedding%';
            """
            )
            indexes = [row[0] for row in cur.fetchall()]

            conn.close()
            duration_ms = (time.time() - start_time) * 1000

            details = {"existing_tables": existing_tables, "vector_indexes": indexes}

            if len(existing_tables) == len(required_tables):
                return CheckResult(
                    name="向量数据表",
                    status=CheckStatus.PASS,
                    message=f"所有向量表已创建 ({len(existing_tables)}/{len(required_tables)})",
                    details=details,
                    duration_ms=duration_ms,
                )
            else:
                missing_tables = set(required_tables) - set(existing_tables)
                return CheckResult(
                    name="向量数据表",
                    status=CheckStatus.WARNING,
                    message=f"部分向量表缺失: {', '.join(missing_tables)}",
                    details=details,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="向量数据表",
                status=CheckStatus.FAIL,
                message=f"向量表检查失败: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_redis_connection(self) -> CheckResult:
        """检查Redis连接"""
        start_time = time.time()
        try:
            r = redis.from_url(self.config["redis_url"])

            # 测试连接
            r.ping()

            # 获取Redis信息
            info = r.info()

            details = {
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
            }

            duration_ms = (time.time() - start_time) * 1000

            return CheckResult(
                name="Redis连接",
                status=CheckStatus.PASS,
                message="Redis连接成功",
                details=details,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="Redis连接",
                status=CheckStatus.FAIL,
                message=f"Redis连接失败: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_ollama_service(self) -> CheckResult:
        """检查Ollama服务"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 检查Ollama服务状态
                response = await client.get(f"{self.config['ollama_url']}/api/tags")

                if response.status_code == 200:
                    models_data = response.json()
                    models = [model["name"] for model in models_data.get("models", [])]

                    details = {"available_models": models, "model_count": len(models)}

                    duration_ms = (time.time() - start_time) * 1000

                    return CheckResult(
                        name="Ollama服务",
                        status=CheckStatus.PASS,
                        message=f"Ollama服务运行正常 ({len(models)} 个模型可用)",
                        details=details,
                        duration_ms=duration_ms,
                    )
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    return CheckResult(
                        name="Ollama服务",
                        status=CheckStatus.FAIL,
                        message=f"Ollama服务响应异常: HTTP {response.status_code}",
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="Ollama服务",
                status=CheckStatus.WARNING,
                message=f"Ollama服务不可用: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_required_models(self) -> CheckResult:
        """检查必需的AI模型"""
        if not self.check_models:
            return CheckResult(
                name="AI模型检查",
                status=CheckStatus.INFO,
                message="跳过模型检查 (使用 --check-models 启用)",
            )

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.config['ollama_url']}/api/tags")

                if response.status_code == 200:
                    models_data = response.json()
                    available_models = [
                        model["name"] for model in models_data.get("models", [])
                    ]

                    # 检查推荐模型
                    required_models = ["bge-m3:latest", "deepseek-r1:8b"]
                    missing_models = []
                    present_models = []

                    for model in required_models:
                        if any(model in available for available in available_models):
                            present_models.append(model)
                        else:
                            missing_models.append(model)

                    details = {
                        "required_models": required_models,
                        "present_models": present_models,
                        "missing_models": missing_models,
                        "all_available_models": available_models,
                    }

                    duration_ms = (time.time() - start_time) * 1000

                    if not missing_models:
                        return CheckResult(
                            name="AI模型检查",
                            status=CheckStatus.PASS,
                            message="所有推荐模型已安装",
                            details=details,
                            duration_ms=duration_ms,
                        )
                    else:
                        return CheckResult(
                            name="AI模型检查",
                            status=CheckStatus.WARNING,
                            message=f"缺少推荐模型: {', '.join(missing_models)}",
                            details=details,
                            duration_ms=duration_ms,
                        )
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    return CheckResult(
                        name="AI模型检查",
                        status=CheckStatus.FAIL,
                        message=f"无法获取模型列表: HTTP {response.status_code}",
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="AI模型检查",
                status=CheckStatus.FAIL,
                message=f"模型检查失败: {str(e)}",
                duration_ms=duration_ms,
            )

    async def check_ai_service(self) -> CheckResult:
        """检查AI服务"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 检查AI服务健康状态
                response = await client.get(f"{self.config['ai_service_url']}/health")

                if response.status_code == 200:
                    health_data = response.json()

                    details = {
                        "service_status": health_data.get("status"),
                        "version": health_data.get("version"),
                        "uptime": health_data.get("uptime"),
                    }

                    duration_ms = (time.time() - start_time) * 1000

                    return CheckResult(
                        name="AI服务",
                        status=CheckStatus.PASS,
                        message="AI服务运行正常",
                        details=details,
                        duration_ms=duration_ms,
                    )
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    return CheckResult(
                        name="AI服务",
                        status=CheckStatus.FAIL,
                        message=f"AI服务响应异常: HTTP {response.status_code}",
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="AI服务",
                status=CheckStatus.WARNING,
                message=f"AI服务不可用: {str(e)} (可能尚未启动)",
                duration_ms=duration_ms,
            )

    async def check_main_service(self) -> CheckResult:
        """检查主应用服务"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config['app_service_url']}/health")

                if response.status_code == 200:
                    duration_ms = (time.time() - start_time) * 1000
                    return CheckResult(
                        name="主应用服务",
                        status=CheckStatus.PASS,
                        message="主应用服务运行正常",
                        duration_ms=duration_ms,
                    )
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    return CheckResult(
                        name="主应用服务",
                        status=CheckStatus.FAIL,
                        message=f"主应用服务响应异常: HTTP {response.status_code}",
                        duration_ms=duration_ms,
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="主应用服务",
                status=CheckStatus.WARNING,
                message=f"主应用服务不可用: {str(e)}",
                duration_ms=duration_ms,
            )

    async def run_all_checks(self):
        """运行所有检查"""
        print("🚀 开始AI基础设施验证...\n")

        # 定义检查顺序
        checks = [
            self.check_database_connection,
            self.check_pgvector_extension,
            self.check_vector_tables,
            self.check_redis_connection,
            self.check_ollama_service,
            self.check_required_models,
            self.check_main_service,
            self.check_ai_service,
        ]

        # 执行检查
        for check in checks:
            try:
                result = await check()
                self.add_result(result)
            except Exception as e:
                self.add_result(
                    CheckResult(
                        name=check.__name__.replace("check_", "")
                        .replace("_", " ")
                        .title(),
                        status=CheckStatus.FAIL,
                        message=f"检查执行失败: {str(e)}",
                    )
                )

        # 输出总结
        self.print_summary()

    def print_summary(self):
        """打印检查总结"""
        print("\n" + "=" * 60)
        print("📊 AI基础设施验证总结")
        print("=" * 60)

        # 统计结果
        pass_count = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        fail_count = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warning_count = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        info_count = sum(1 for r in self.results if r.status == CheckStatus.INFO)

        total_checks = len(self.results)

        print(f"总检查项: {total_checks}")
        print(f"✅ 通过: {pass_count}")
        print(f"❌ 失败: {fail_count}")
        print(f"⚠️  警告: {warning_count}")
        print(f"ℹ️  信息: {info_count}")

        # 计算成功率
        success_rate = (pass_count / total_checks) * 100 if total_checks > 0 else 0
        print(f"\n成功率: {success_rate:.1f}%")

        # 给出建议
        if fail_count == 0 and warning_count == 0:
            print("\n🎉 恭喜！AI基础设施配置完美！")
        elif fail_count == 0:
            print("\n✨ AI基础设施基本就绪，建议处理警告项目")
        else:
            print("\n🔧 需要修复失败的检查项目才能正常使用AI功能")

        # 失败项目的修复建议
        if fail_count > 0:
            print("\n🛠️  修复建议:")
            for result in self.results:
                if result.status == CheckStatus.FAIL:
                    print(f"   • {result.name}: {result.message}")

        print("\n" + "=" * 60)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI基础设施验证脚本")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--check-models", "-m", action="store_true", help="检查AI模型")

    args = parser.parse_args()

    verifier = AIInfrastructureVerifier(
        verbose=args.verbose, check_models=args.check_models
    )

    await verifier.run_all_checks()

    # 根据结果设置退出码
    fail_count = sum(1 for r in verifier.results if r.status == CheckStatus.FAIL)
    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
