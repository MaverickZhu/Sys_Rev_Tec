#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限查询索引优化脚本

提供数据库索引创建和优化功能，用于提升权限查询性能
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import text, Index
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.models.user import User
from app.models.permission import Permission, Role, PermissionGroup, ResourcePermission
from app.models.associations import user_roles, role_permission_association, user_permission_association, permission_group_permissions

logger = logging.getLogger(__name__)

class PermissionIndexOptimizer:
    """权限索引优化器
    
    提供数据库索引创建和优化功能
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_permission_indexes(self) -> Dict[str, Any]:
        """创建权限相关索引
        
        Returns:
            Dict[str, Any]: 索引创建结果
        """
        results = {
            "created_indexes": [],
            "failed_indexes": [],
            "total_count": 0,
            "success_count": 0
        }
        
        # 定义需要创建的索引
        indexes = [
            # 用户表索引
            {
                "name": "idx_users_email",
                "table": "users",
                "columns": ["email"],
                "unique": True
            },
            {
                "name": "idx_users_username",
                "table": "users",
                "columns": ["username"],
                "unique": True
            },
            {
                "name": "idx_users_is_active",
                "table": "users",
                "columns": ["is_active"]
            },
            {
                "name": "idx_users_is_superuser",
                "table": "users",
                "columns": ["is_superuser"]
            },
            
            # 权限表索引
            {
                "name": "idx_permissions_code",
                "table": "permissions",
                "columns": ["code"],
                "unique": True
            },
            {
                "name": "idx_permissions_resource_type",
                "table": "permissions",
                "columns": ["resource_type"]
            },
            {
                "name": "idx_permissions_operation",
                "table": "permissions",
                "columns": ["operation"]
            },
            {
                "name": "idx_permissions_parent_id",
                "table": "permissions",
                "columns": ["parent_id"]
            },
            {
                "name": "idx_permissions_resource_operation",
                "table": "permissions",
                "columns": ["resource_type", "operation"]
            },
            
            # 角色表索引
            {
                "name": "idx_roles_code",
                "table": "roles",
                "columns": ["code"],
                "unique": True
            },
            {
                "name": "idx_roles_name",
                "table": "roles",
                "columns": ["name"]
            },
            
            # 用户角色关联表索引
            {
                "name": "idx_user_roles_user_id",
                "table": "user_roles",
                "columns": ["user_id"]
            },
            {
                "name": "idx_user_roles_role_id",
                "table": "user_roles",
                "columns": ["role_id"]
            },
            {
                "name": "idx_user_roles_composite",
                "table": "user_roles",
                "columns": ["user_id", "role_id"],
                "unique": True
            },
            
            # 角色权限关联表索引
            {
                "name": "idx_role_permissions_role_id",
                "table": "role_permissions",
                "columns": ["role_id"]
            },
            {
                "name": "idx_role_permissions_permission_id",
                "table": "role_permissions",
                "columns": ["permission_id"]
            },
            {
                "name": "idx_role_permissions_composite",
                "table": "role_permissions",
                "columns": ["role_id", "permission_id"],
                "unique": True
            },
            
            # 用户权限关联表索引
            {
                "name": "idx_user_permissions_user_id",
                "table": "user_permissions",
                "columns": ["user_id"]
            },
            {
                "name": "idx_user_permissions_permission_id",
                "table": "user_permissions",
                "columns": ["permission_id"]
            },
            {
                "name": "idx_user_permissions_composite",
                "table": "user_permissions",
                "columns": ["user_id", "permission_id"],
                "unique": True
            },
            
            # 资源权限表索引
            {
                "name": "idx_resource_permissions_user_id",
                "table": "resource_permissions",
                "columns": ["user_id"]
            },
            {
                "name": "idx_resource_permissions_resource_type",
                "table": "resource_permissions",
                "columns": ["resource_type"]
            },
            {
                "name": "idx_resource_permissions_resource_id",
                "table": "resource_permissions",
                "columns": ["resource_id"]
            },
            {
                "name": "idx_resource_permissions_operation",
                "table": "resource_permissions",
                "columns": ["operation"]
            },
            {
                "name": "idx_resource_permissions_composite",
                "table": "resource_permissions",
                "columns": ["user_id", "resource_type", "resource_id", "operation"]
            },
            
            # 权限组表索引
            {
                "name": "idx_permission_groups_name",
                "table": "permission_groups",
                "columns": ["name"],
                "unique": True
            },
            
            # 权限组权限关联表索引
            {
                "name": "idx_permission_group_permissions_group_id",
                "table": "permission_group_permissions",
                "columns": ["permission_group_id"]
            },
            {
                "name": "idx_permission_group_permissions_permission_id",
                "table": "permission_group_permissions",
                "columns": ["permission_id"]
            },
            {
                "name": "idx_permission_group_permissions_composite",
                "table": "permission_group_permissions",
                "columns": ["permission_group_id", "permission_id"],
                "unique": True
            }
        ]
        
        results["total_count"] = len(indexes)
        
        for index_config in indexes:
            try:
                self._create_index(index_config)
                results["created_indexes"].append(index_config["name"])
                results["success_count"] += 1
                logger.info(f"成功创建索引: {index_config['name']}")
            except Exception as e:
                results["failed_indexes"].append({
                    "name": index_config["name"],
                    "error": str(e)
                })
                logger.error(f"创建索引失败 {index_config['name']}: {e}")
        
        return results
    
    def _create_index(self, index_config: Dict[str, Any]) -> None:
        """创建单个索引
        
        Args:
            index_config: 索引配置
        """
        name = index_config["name"]
        table = index_config["table"]
        columns = index_config["columns"]
        unique = index_config.get("unique", False)
        
        # 检查索引是否已存在
        if self._index_exists(name):
            logger.info(f"索引 {name} 已存在，跳过创建")
            return
        
        # 构建CREATE INDEX语句
        columns_str = ", ".join(columns)
        unique_str = "UNIQUE " if unique else ""
        
        sql = f"CREATE {unique_str}INDEX {name} ON {table} ({columns_str})"
        
        try:
            self.db.execute(text(sql))
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def _index_exists(self, index_name: str) -> bool:
        """检查索引是否存在
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 索引是否存在
        """
        try:
            # SQLite查询索引
            sql = """
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name=:index_name
            """
            result = self.db.execute(text(sql), {"index_name": index_name}).fetchone()
            return result is not None
        except Exception:
            return False
    
    def drop_permission_indexes(self) -> Dict[str, Any]:
        """删除权限相关索引
        
        Returns:
            Dict[str, Any]: 索引删除结果
        """
        results = {
            "dropped_indexes": [],
            "failed_indexes": [],
            "total_count": 0,
            "success_count": 0
        }
        
        # 获取所有权限相关索引
        index_names = [
            "idx_users_email", "idx_users_username", "idx_users_is_active", "idx_users_is_superuser",
            "idx_permissions_code", "idx_permissions_resource_type", "idx_permissions_operation",
            "idx_permissions_parent_id", "idx_permissions_resource_operation",
            "idx_roles_code", "idx_roles_name",
            "idx_user_roles_user_id", "idx_user_roles_role_id", "idx_user_roles_composite",
            "idx_role_permissions_role_id", "idx_role_permissions_permission_id", "idx_role_permissions_composite",
            "idx_user_permissions_user_id", "idx_user_permissions_permission_id", "idx_user_permissions_composite",
            "idx_resource_permissions_user_id", "idx_resource_permissions_resource_type",
            "idx_resource_permissions_resource_id", "idx_resource_permissions_operation",
            "idx_resource_permissions_composite",
            "idx_permission_groups_name",
            "idx_permission_group_permissions_group_id", "idx_permission_group_permissions_permission_id",
            "idx_permission_group_permissions_composite"
        ]
        
        results["total_count"] = len(index_names)
        
        for index_name in index_names:
            try:
                if self._index_exists(index_name):
                    self._drop_index(index_name)
                    results["dropped_indexes"].append(index_name)
                    results["success_count"] += 1
                    logger.info(f"成功删除索引: {index_name}")
            except Exception as e:
                results["failed_indexes"].append({
                    "name": index_name,
                    "error": str(e)
                })
                logger.error(f"删除索引失败 {index_name}: {e}")
        
        return results
    
    def _drop_index(self, index_name: str) -> None:
        """删除单个索引
        
        Args:
            index_name: 索引名称
        """
        sql = f"DROP INDEX {index_name}"
        
        try:
            self.db.execute(text(sql))
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def analyze_permission_queries(self) -> Dict[str, Any]:
        """分析权限查询性能
        
        Returns:
            Dict[str, Any]: 查询分析结果
        """
        results = {
            "table_stats": {},
            "index_usage": {},
            "recommendations": []
        }
        
        try:
            # 获取表统计信息
            tables = ["users", "permissions", "roles", "user_roles", "role_permissions", 
                     "user_permissions", "resource_permissions", "permission_groups", 
                     "permission_group_permissions"]
            
            for table in tables:
                count_sql = f"SELECT COUNT(*) as count FROM {table}"
                result = self.db.execute(text(count_sql)).fetchone()
                results["table_stats"][table] = {
                    "row_count": result[0] if result else 0
                }
            
            # 获取索引使用情况
            index_sql = """
            SELECT name, tbl_name 
            FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
            """
            index_results = self.db.execute(text(index_sql)).fetchall()
            
            for index_result in index_results:
                results["index_usage"][index_result[0]] = {
                    "table": index_result[1],
                    "exists": True
                }
            
            # 生成优化建议
            recommendations = []
            
            # 检查大表是否有适当的索引
            for table, stats in results["table_stats"].items():
                if stats["row_count"] > 1000:
                    if table == "users" and "idx_users_email" not in results["index_usage"]:
                        recommendations.append(f"建议为 {table} 表的 email 字段创建索引")
                    elif table == "permissions" and "idx_permissions_code" not in results["index_usage"]:
                        recommendations.append(f"建议为 {table} 表的 code 字段创建索引")
                    elif table == "user_roles" and "idx_user_roles_composite" not in results["index_usage"]:
                        recommendations.append(f"建议为 {table} 表创建复合索引")
            
            results["recommendations"] = recommendations
            
        except Exception as e:
            logger.error(f"分析权限查询性能失败: {e}")
            results["error"] = str(e)
        
        return results
    
    def optimize_database(self) -> Dict[str, Any]:
        """优化数据库
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        results = {
            "vacuum_result": None,
            "analyze_result": None,
            "reindex_result": None,
            "success": False
        }
        
        try:
            # VACUUM - 重建数据库文件，回收空间
            self.db.execute(text("VACUUM"))
            results["vacuum_result"] = "成功"
            
            # ANALYZE - 更新查询优化器统计信息
            self.db.execute(text("ANALYZE"))
            results["analyze_result"] = "成功"
            
            # REINDEX - 重建所有索引
            self.db.execute(text("REINDEX"))
            results["reindex_result"] = "成功"
            
            self.db.commit()
            results["success"] = True
            
            logger.info("数据库优化完成")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"数据库优化失败: {e}")
            results["error"] = str(e)
        
        return results


def get_permission_index_optimizer(db: Session) -> PermissionIndexOptimizer:
    """获取权限索引优化器实例
    
    Args:
        db: 数据库会话
        
    Returns:
        PermissionIndexOptimizer: 权限索引优化器实例
    """
    return PermissionIndexOptimizer(db)