#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存预热机制
提供智能缓存预热功能，提升系统启动后的响应速度
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.config.cache_strategy import get_cache_strategy
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.services.multi_level_cache import get_multi_cache_service

logger = logging.getLogger(__name__)


class WarmupPriority(Enum):
    """预热优先级"""

    CRITICAL = "critical"  # 关键数据，立即预热
    HIGH = "high"  # 高优先级，优先预热
    MEDIUM = "medium"  # 中等优先级，正常预热
    LOW = "low"  # 低优先级，延迟预热


@dataclass
class WarmupTask:
    """预热任务"""

    name: str
    priority: WarmupPriority
    cache_type: str
    data_loader: Callable
    key_generator: Callable
    enabled: bool = True
    max_items: Optional[int] = None
    batch_size: int = 100
    delay_seconds: float = 0.1


@dataclass
class WarmupResult:
    """预热结果"""

    task_name: str
    success: bool
    items_loaded: int
    duration_seconds: float
    error_message: Optional[str] = None


class CacheWarmupService:
    """缓存预热服务"""

    def __init__(self):
        self.warmup_tasks: List[WarmupTask] = []
        self.results: List[WarmupResult] = []
        self._initialize_tasks()

    def _initialize_tasks(self):
        """初始化预热任务"""
        self.warmup_tasks = [
            # 系统配置预热
            WarmupTask(
                name="system_config",
                priority=WarmupPriority.CRITICAL,
                cache_type="system_config",
                data_loader=self._load_system_config,
                key_generator=lambda item: f"config:{item['key']}",
                max_items=50,
            ),
            # 用户会话预热（活跃用户）
            WarmupTask(
                name="active_users",
                priority=WarmupPriority.HIGH,
                cache_type="user_session",
                data_loader=self._load_active_users,
                key_generator=lambda user: f"user:{user.id}",
                max_items=100,
            ),
            # 热门项目预热
            WarmupTask(
                name="popular_projects",
                priority=WarmupPriority.HIGH,
                cache_type="db_query",
                data_loader=self._load_popular_projects,
                key_generator=lambda project: f"project:{project.id}",
                max_items=50,
            ),
            # 最近文档预热
            WarmupTask(
                name="recent_documents",
                priority=WarmupPriority.MEDIUM,
                cache_type="db_query",
                data_loader=self._load_recent_documents,
                key_generator=lambda doc: f"document:{doc.id}",
                max_items=200,
            ),
            # 常用搜索结果预热
            WarmupTask(
                name="common_searches",
                priority=WarmupPriority.MEDIUM,
                cache_type="search_result",
                data_loader=self._load_common_searches,
                key_generator=lambda search: f"search:{search['query_hash']}",
                max_items=100,
            ),
            # 统计数据预热
            WarmupTask(
                name="statistics",
                priority=WarmupPriority.LOW,
                cache_type="statistics",
                data_loader=self._load_statistics,
                key_generator=lambda stat: f"stat:{stat['type']}",
                max_items=20,
            ),
        ]

    async def warmup_all(
        self, priority_filter: Optional[WarmupPriority] = None
    ) -> List[WarmupResult]:
        """执行所有预热任务"""
        logger.info("Starting cache warmup process")
        start_time = time.time()

        # 过滤任务
        tasks_to_run = self.warmup_tasks
        if priority_filter:
            tasks_to_run = [
                task for task in tasks_to_run if task.priority == priority_filter
            ]

        # 按优先级排序
        priority_order = {
            WarmupPriority.CRITICAL: 0,
            WarmupPriority.HIGH: 1,
            WarmupPriority.MEDIUM: 2,
            WarmupPriority.LOW: 3,
        }
        tasks_to_run.sort(key=lambda t: priority_order[t.priority])

        # 执行任务
        results = []
        for task in tasks_to_run:
            if task.enabled:
                result = await self._execute_warmup_task(task)
                results.append(result)

                # 任务间延迟
                if task.delay_seconds > 0:
                    await asyncio.sleep(task.delay_seconds)

        total_time = time.time() - start_time
        total_items = sum(r.items_loaded for r in results)
        success_count = sum(1 for r in results if r.success)

        logger.info(
            f"Cache warmup completed: {success_count}/{len(results)} tasks successful, "
            f"{total_items} items loaded in {total_time:.2f}s"
        )

        self.results.extend(results)
        return results

    async def warmup_critical(self) -> List[WarmupResult]:
        """仅预热关键数据"""
        return await self.warmup_all(WarmupPriority.CRITICAL)

    async def warmup_by_task_name(self, task_name: str) -> Optional[WarmupResult]:
        """按任务名称预热"""
        task = next((t for t in self.warmup_tasks if t.name == task_name), None)
        if not task:
            logger.error(f"Warmup task '{task_name}' not found")
            return None

        return await self._execute_warmup_task(task)

    async def _execute_warmup_task(self, task: WarmupTask) -> WarmupResult:
        """执行单个预热任务"""
        logger.info(f"Starting warmup task: {task.name}")
        start_time = time.time()

        try:
            # 获取缓存服务和策略
            cache_service = await get_multi_cache_service()
            strategy = get_cache_strategy(task.cache_type)

            # 加载数据
            data_items = await task.data_loader()

            # 限制数量
            if task.max_items and len(data_items) > task.max_items:
                data_items = data_items[: task.max_items]

            # 批量预热
            items_loaded = 0
            for i in range(0, len(data_items), task.batch_size):
                batch = data_items[i : i + task.batch_size]

                for item in batch:
                    try:
                        cache_key = task.key_generator(item)
                        await cache_service.set(cache_key, item, strategy)
                        items_loaded += 1
                    except Exception as e:
                        logger.warning(f"Failed to cache item in task {task.name}: {e}")

                # 批次间短暂延迟
                if i + task.batch_size < len(data_items):
                    await asyncio.sleep(0.01)

            duration = time.time() - start_time
            logger.info(
                f"Warmup task '{task.name}' completed: {items_loaded} items in {duration:.2f}s"
            )

            return WarmupResult(
                task_name=task.name,
                success=True,
                items_loaded=items_loaded,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Warmup task '{task.name}' failed: {str(e)}"
            logger.error(error_msg)

            return WarmupResult(
                task_name=task.name,
                success=False,
                items_loaded=0,
                duration_seconds=duration,
                error_message=error_msg,
            )

    async def _load_system_config(self) -> List[Dict[str, Any]]:
        """加载系统配置"""
        # 模拟系统配置数据
        configs = [
            {
                "key": "app_name",
                "value": getattr(settings, "PROJECT_NAME", "System Review"),
            },
            {"key": "version", "value": "1.0.0"},
            {"key": "debug_mode", "value": getattr(settings, "DEBUG", False)},
            {"key": "max_upload_size", "value": "10MB"},
            {"key": "supported_formats", "value": ["pdf", "docx", "txt", "md"]},
            {"key": "cache_enabled", "value": True},
            {
                "key": "ai_service_url",
                "value": getattr(settings, "AI_SERVICE_URL", "http://localhost:8001"),
            },
            {
                "key": "redis_url",
                "value": getattr(settings, "REDIS_URL", "redis://redis:6379"),
            },
        ]
        return configs

    async def _load_active_users(self) -> List[User]:
        """加载活跃用户"""
        try:
            db = SessionLocal()
            # 获取最近30天活跃的用户
            cutoff_date = datetime.now() - timedelta(days=30)
            users = (
                db.query(User)
                .filter(User.last_login > cutoff_date, User.is_active)
                .limit(100)
                .all()
            )
            db.close()
            return users
        except Exception as e:
            logger.error(f"Failed to load active users: {e}")
            return []

    async def _load_popular_projects(self) -> List[Project]:
        """加载热门项目"""
        try:
            db = SessionLocal()
            # 获取最近访问的项目
            projects = (
                db.query(Project)
                .filter(Project.is_active)
                .order_by(Project.updated_at.desc())
                .limit(50)
                .all()
            )
            db.close()
            return projects
        except Exception as e:
            logger.error(f"Failed to load popular projects: {e}")
            return []

    async def _load_recent_documents(self) -> List[Document]:
        """加载最近文档"""
        try:
            db = SessionLocal()
            # 获取最近30天的文档
            cutoff_date = datetime.now() - timedelta(days=30)
            documents = (
                db.query(Document)
                .filter(Document.created_at > cutoff_date)
                .order_by(Document.created_at.desc())
                .limit(200)
                .all()
            )
            db.close()
            return documents
        except Exception as e:
            logger.error(f"Failed to load recent documents: {e}")
            return []

    async def _load_common_searches(self) -> List[Dict[str, Any]]:
        """加载常用搜索"""
        # 模拟常用搜索查询
        common_searches = [
            {"query_hash": "project_status", "query": "项目状态", "results": []},
            {"query_hash": "document_review", "query": "文档审查", "results": []},
            {"query_hash": "compliance_check", "query": "合规检查", "results": []},
            {"query_hash": "risk_assessment", "query": "风险评估", "results": []},
            {"query_hash": "audit_report", "query": "审计报告", "results": []},
        ]
        return common_searches

    async def _load_statistics(self) -> List[Dict[str, Any]]:
        """加载统计数据"""
        try:
            db = SessionLocal()

            # 计算各种统计数据
            stats = []

            # 项目统计
            project_count = db.query(Project).count()
            stats.append({"type": "project_count", "value": project_count})

            # 文档统计
            document_count = db.query(Document).count()
            stats.append({"type": "document_count", "value": document_count})

            # 用户统计
            user_count = db.query(User).count()
            stats.append({"type": "user_count", "value": user_count})

            # 活跃用户统计
            cutoff_date = datetime.now() - timedelta(days=7)
            active_users = db.query(User).filter(User.last_login > cutoff_date).count()
            stats.append({"type": "active_users_week", "value": active_users})

            db.close()
            return stats

        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
            return []

    def get_warmup_status(self) -> Dict[str, Any]:
        """获取预热状态"""
        if not self.results:
            return {"status": "not_started", "tasks": []}

        total_tasks = len(self.results)
        successful_tasks = sum(1 for r in self.results if r.success)
        total_items = sum(r.items_loaded for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)

        return {
            "status": "completed" if successful_tasks == total_tasks else "partial",
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "total_items_loaded": total_items,
            "total_duration_seconds": total_duration,
            "tasks": [
                {
                    "name": r.task_name,
                    "success": r.success,
                    "items_loaded": r.items_loaded,
                    "duration_seconds": r.duration_seconds,
                    "error_message": r.error_message,
                }
                for r in self.results
            ],
        }

    def add_custom_task(self, task: WarmupTask):
        """添加自定义预热任务"""
        self.warmup_tasks.append(task)
        logger.info(f"Added custom warmup task: {task.name}")

    def disable_task(self, task_name: str):
        """禁用预热任务"""
        for task in self.warmup_tasks:
            if task.name == task_name:
                task.enabled = False
                logger.info(f"Disabled warmup task: {task_name}")
                break

    def enable_task(self, task_name: str):
        """启用预热任务"""
        for task in self.warmup_tasks:
            if task.name == task_name:
                task.enabled = True
                logger.info(f"Enabled warmup task: {task_name}")
                break


# 全局缓存预热服务实例
_warmup_service: Optional[CacheWarmupService] = None


def get_cache_warmup_service() -> CacheWarmupService:
    """获取缓存预热服务实例"""
    global _warmup_service

    if _warmup_service is None:
        _warmup_service = CacheWarmupService()

    return _warmup_service
