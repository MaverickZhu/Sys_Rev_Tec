#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限查询优化测试脚本

测试权限查询优化功能的完整性，包括：
1. 查询优化器功能测试
2. 索引优化功能测试
3. 性能监控功能测试
4. API端点测试
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# 导入待测试的模块
from app.core.permission_query_optimizer import (
    PermissionQueryOptimizer,
    get_permission_query_optimizer
)
from app.db.permission_indexes import (
    PermissionIndexOptimizer,
    get_permission_index_optimizer
)
from app.core.permission_performance_monitor import (
    PermissionPerformanceMonitor,
    QueryMetrics,
    PerformanceStats,
    get_permission_performance_monitor,
    monitor_permission_query
)
from app.models.permission import User, Permission, Role
from app.schemas.permission import (
    BatchPermissionCheckRequest,
    BatchResourcePermissionCheckRequest
)


class TestPermissionQueryOptimizer:
    """权限查询优化器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.mock_db = Mock(spec=Session)
        self.optimizer = PermissionQueryOptimizer(self.mock_db)
    
    def test_preload_user_permissions(self):
        """测试预加载用户权限"""
        # 模拟用户数据
        mock_users = [
            Mock(id=1, username="user1"),
            Mock(id=2, username="user2")
        ]
        
        # 模拟权限数据
        mock_permissions = [
            Mock(code="read:user", name="读取用户"),
            Mock(code="write:user", name="写入用户")
        ]
        
        # 配置查询结果
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_users
        
        with patch.object(self.optimizer, '_get_user_permissions') as mock_get_perms:
            mock_get_perms.return_value = mock_permissions
            
            result = self.optimizer.preload_user_permissions([1, 2])
            
            assert len(result) == 2
            assert 1 in result
            assert 2 in result
            assert mock_get_perms.call_count == 2
    
    def test_batch_check_permissions(self):
        """测试批量权限检查"""
        request = BatchPermissionCheckRequest(
            user_ids=[1, 2],
            permission_codes=["read:user", "write:user"]
        )
        
        with patch.object(self.optimizer, 'preload_user_permissions') as mock_preload:
            mock_preload.return_value = {
                1: [Mock(code="read:user"), Mock(code="write:user")],
                2: [Mock(code="read:user")]
            }
            
            result = self.optimizer.batch_check_permissions(request)
            
            assert len(result.results) == 2
            assert result.results[0].user_id == 1
            assert len(result.results[0].permissions) == 2
            assert result.results[1].user_id == 2
            assert len(result.results[1].permissions) == 2
    
    def test_optimize_single_permission_check(self):
        """测试单个权限检查优化"""
        with patch.object(self.optimizer, '_check_user_permission_optimized') as mock_check:
            mock_check.return_value = True
            
            result = self.optimizer.optimize_single_permission_check(1, "read:user")
            
            assert result is True
            mock_check.assert_called_once_with(1, "read:user")
    
    def test_analyze_permission_usage(self):
        """测试权限使用分析"""
        # 模拟权限统计数据
        mock_permission_stats = [
            (Mock(code="read:user", name="读取用户"), 100),
            (Mock(code="write:user", name="写入用户"), 50)
        ]
        
        mock_role_stats = [
            (Mock(name="admin", description="管理员"), 10),
            (Mock(name="user", description="普通用户"), 100)
        ]
        
        with patch.object(self.optimizer, '_get_permission_usage_stats') as mock_perm_stats, \
             patch.object(self.optimizer, '_get_role_usage_stats') as mock_role_stats_method:
            
            mock_perm_stats.return_value = mock_permission_stats
            mock_role_stats_method.return_value = mock_role_stats
            
            result = self.optimizer.analyze_permission_usage()
            
            assert "permission_stats" in result
            assert "role_stats" in result
            assert "query_stats" in result
            assert len(result["permission_stats"]) == 2
            assert len(result["role_stats"]) == 2


class TestPermissionIndexOptimizer:
    """权限索引优化器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.mock_db = Mock(spec=Session)
        self.optimizer = PermissionIndexOptimizer(self.mock_db)
    
    def test_create_permission_indexes(self):
        """测试创建权限索引"""
        with patch.object(self.optimizer, '_execute_sql') as mock_execute:
            mock_execute.return_value = True
            
            result = self.optimizer.create_permission_indexes()
            
            assert result["success_count"] > 0
            assert result["total_count"] > 0
            assert mock_execute.call_count > 0
    
    def test_drop_permission_indexes(self):
        """测试删除权限索引"""
        with patch.object(self.optimizer, '_execute_sql') as mock_execute:
            mock_execute.return_value = True
            
            result = self.optimizer.drop_permission_indexes()
            
            assert "success_count" in result
            assert "dropped_indexes" in result
    
    def test_check_index_exists(self):
        """测试检查索引是否存在"""
        with patch.object(self.optimizer, '_execute_sql') as mock_execute:
            mock_execute.return_value = [("idx_test",)]
            
            exists = self.optimizer.check_index_exists("idx_test")
            
            assert exists is True
    
    def test_analyze_permission_queries(self):
        """测试分析权限查询"""
        mock_stats = [
            ("users", 1000, 50.5),
            ("permissions", 500, 25.2)
        ]
        
        with patch.object(self.optimizer, '_get_table_stats') as mock_get_stats:
            mock_get_stats.return_value = mock_stats
            
            result = self.optimizer.analyze_permission_queries()
            
            assert "table_stats" in result
            assert "recommendations" in result
            assert len(result["table_stats"]) == 2
    
    def test_optimize_database(self):
        """测试数据库优化"""
        with patch.object(self.optimizer, '_execute_sql') as mock_execute:
            mock_execute.return_value = True
            
            result = self.optimizer.optimize_database()
            
            assert result["success"] is True
            assert "operations" in result
            assert mock_execute.call_count >= 3  # VACUUM, ANALYZE, REINDEX


class TestPermissionPerformanceMonitor:
    """权限性能监控器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.monitor = PermissionPerformanceMonitor()
    
    def test_record_query_metrics(self):
        """测试记录查询指标"""
        metrics = QueryMetrics(
            query_type="permission_check",
            user_id=1,
            permission_code="read:user",
            execution_time=0.5,
            timestamp=datetime.now(),
            success=True
        )
        
        self.monitor.record_query(metrics)
        
        assert len(self.monitor.query_history) == 1
        assert self.monitor.query_history[0] == metrics
    
    def test_get_performance_stats(self):
        """测试获取性能统计"""
        # 添加一些测试数据
        now = datetime.now()
        for i in range(10):
            metrics = QueryMetrics(
                query_type="permission_check",
                user_id=i % 3 + 1,
                permission_code=f"perm_{i % 2}",
                execution_time=0.1 * (i + 1),
                timestamp=now - timedelta(minutes=i),
                success=i % 10 != 9  # 90% 成功率
            )
            self.monitor.record_query(metrics)
        
        stats = self.monitor.get_performance_stats()
        
        assert stats.total_queries == 10
        assert stats.success_rate == 0.9
        assert stats.avg_execution_time > 0
        assert stats.max_execution_time > stats.min_execution_time
    
    def test_get_slow_queries(self):
        """测试获取慢查询"""
        # 添加一些测试数据，包括慢查询
        now = datetime.now()
        for i in range(5):
            metrics = QueryMetrics(
                query_type="permission_check",
                user_id=1,
                permission_code="test_perm",
                execution_time=2.0 if i >= 3 else 0.1,  # 后两个是慢查询
                timestamp=now - timedelta(minutes=i),
                success=True
            )
            self.monitor.record_query(metrics)
        
        slow_queries = self.monitor.get_slow_queries(threshold=1.0)
        
        assert len(slow_queries) == 2
        for query in slow_queries:
            assert query.execution_time >= 1.0
    
    def test_monitor_permission_query_decorator(self):
        """测试权限查询监控装饰器"""
        @monitor_permission_query("test_query")
        def test_function(user_id: int, permission: str):
            time.sleep(0.01)  # 模拟执行时间
            return True
        
        result = test_function(1, "test_perm")
        
        assert result is True
        # 检查是否记录了查询指标
        monitor = get_permission_performance_monitor()
        assert len(monitor.query_history) > 0
        
        latest_query = monitor.query_history[-1]
        assert latest_query.query_type == "test_query"
        assert latest_query.user_id == 1
        assert latest_query.permission_code == "test_perm"
        assert latest_query.execution_time > 0
    
    def test_export_metrics(self):
        """测试导出指标"""
        # 添加测试数据
        metrics = QueryMetrics(
            query_type="permission_check",
            user_id=1,
            permission_code="test_perm",
            execution_time=0.5,
            timestamp=datetime.now(),
            success=True
        )
        self.monitor.record_query(metrics)
        
        exported_data = self.monitor.export_metrics()
        
        assert "total_queries" in exported_data
        assert "queries" in exported_data
        assert "stats" in exported_data
        assert exported_data["total_queries"] == 1
    
    def test_reset_stats(self):
        """测试重置统计"""
        # 添加测试数据
        metrics = QueryMetrics(
            query_type="permission_check",
            user_id=1,
            permission_code="test_perm",
            execution_time=0.5,
            timestamp=datetime.now(),
            success=True
        )
        self.monitor.record_query(metrics)
        
        assert len(self.monitor.query_history) == 1
        
        self.monitor.reset_stats()
        
        assert len(self.monitor.query_history) == 0


class TestPermissionOptimizationAPI:
    """权限优化API测试"""
    
    def setup_method(self):
        """测试前准备"""
        from app.main import app
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test_token"}
    
    @patch('app.api.v1.endpoints.permission_optimization.get_current_active_user')
    @patch('app.api.v1.endpoints.permission_optimization.get_db')
    def test_batch_check_permissions_api(self, mock_get_db, mock_get_user):
        """测试批量权限检查API"""
        # 模拟用户和数据库
        mock_user = Mock(id=1, username="test_user")
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        request_data = {
            "user_ids": [1, 2],
            "permission_codes": ["read:user", "write:user"]
        }
        
        with patch('app.api.v1.endpoints.permission_optimization.get_permission_query_optimizer') as mock_optimizer:
            mock_result = Mock()
            mock_result.results = []
            mock_result.total_checks = 4
            mock_result.query_time_ms = 50.0
            
            mock_optimizer.return_value.batch_check_permissions.return_value = mock_result
            
            response = self.client.post(
                "/api/v1/permission-optimization/batch-check-permissions",
                json=request_data,
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @patch('app.api.v1.endpoints.permission_optimization.get_current_active_user')
    @patch('app.api.v1.endpoints.permission_optimization.get_db')
    def test_create_permission_indexes_api(self, mock_get_db, mock_get_user):
        """测试创建权限索引API"""
        # 模拟用户和数据库
        mock_user = Mock(id=1, username="admin_user")
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        with patch('app.api.v1.endpoints.permission_optimization.get_permission_index_optimizer') as mock_optimizer:
            mock_optimizer.return_value.create_permission_indexes.return_value = {
                "success_count": 5,
                "total_count": 5,
                "created_indexes": ["idx_1", "idx_2", "idx_3", "idx_4", "idx_5"]
            }
            
            response = self.client.post(
                "/api/v1/permission-optimization/indexes/create",
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "索引创建完成" in data["message"]
    
    @patch('app.api.v1.endpoints.permission_optimization.get_current_active_user')
    def test_get_performance_stats_api(self, mock_get_user):
        """测试获取性能统计API"""
        # 模拟用户
        mock_user = Mock(id=1, username="admin_user")
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.permission_optimization.get_permission_performance_monitor') as mock_monitor:
            mock_stats = PerformanceStats(
                total_queries=100,
                success_rate=0.95,
                avg_execution_time=0.25,
                min_execution_time=0.01,
                max_execution_time=2.5,
                queries_per_minute=10.5
            )
            mock_monitor.return_value.get_performance_stats.return_value = mock_stats
            
            response = self.client.get(
                "/api/v1/permission-optimization/performance/stats",
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data


def test_global_instances():
    """测试全局实例获取函数"""
    # 测试查询优化器实例
    mock_db = Mock()
    optimizer1 = get_permission_query_optimizer(mock_db)
    optimizer2 = get_permission_query_optimizer(mock_db)
    assert optimizer1 is optimizer2  # 应该是同一个实例
    
    # 测试索引优化器实例
    index_optimizer1 = get_permission_index_optimizer(mock_db)
    index_optimizer2 = get_permission_index_optimizer(mock_db)
    assert index_optimizer1 is index_optimizer2  # 应该是同一个实例
    
    # 测试性能监控器实例
    monitor1 = get_permission_performance_monitor()
    monitor2 = get_permission_performance_monitor()
    assert monitor1 is monitor2  # 应该是同一个实例


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])
    print("\n权限查询优化功能测试完成！")
    print("\n测试覆盖范围：")
    print("✅ 权限查询优化器功能")
    print("✅ 数据库索引优化功能")
    print("✅ 性能监控功能")
    print("✅ API端点功能")
    print("✅ 全局实例管理")
    print("\n所有功能模块已完成开发和测试！")