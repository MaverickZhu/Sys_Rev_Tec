"""缓存系统测试模块

测试缓存系统的各个组件和功能。
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.cache_service import CacheService
from app.services.cache_strategies import CacheStrategyManager
from app.services.cache_monitor import CacheMonitor, CacheMetrics
from app.services.cache_optimizer import CacheOptimizer, OptimizationTask
from app.services.cache_manager import CacheManager
from app.core.cache_config import (
    CacheSystemConfig, 
    CacheStrategyConfig,
    get_cache_config_for_environment
)


class TestCacheService:
    """缓存服务测试"""
    
    @pytest.fixture
    async def cache_service(self):
        """创建缓存服务实例"""
        service = CacheService()
        await service.initialize()
        yield service
        await service.close()
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, cache_service):
        """测试基本缓存操作"""
        # 测试设置和获取
        await cache_service.set("test_key", "test_value")
        value = await cache_service.get("test_key")
        assert value == "test_value"
        
        # 测试删除
        await cache_service.delete("test_key")
        value = await cache_service.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache_service):
        """测试TTL过期"""
        # 设置短TTL
        await cache_service.set("ttl_key", "ttl_value", ttl=1)
        
        # 立即获取应该成功
        value = await cache_service.get("ttl_key")
        assert value == "ttl_value"
        
        # 等待过期
        await asyncio.sleep(1.1)
        value = await cache_service.get("ttl_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, cache_service):
        """测试批量操作"""
        # 批量设置
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        await cache_service.batch_set(data)
        
        # 批量获取
        keys = list(data.keys())
        values = await cache_service.batch_get(keys)
        
        for key, expected_value in data.items():
            assert values.get(key) == expected_value
        
        # 批量删除
        await cache_service.batch_delete(keys)
        values = await cache_service.batch_get(keys)
        
        for key in keys:
            assert values.get(key) is None


class TestCacheStrategyManager:
    """缓存策略管理器测试"""
    
    @pytest.fixture
    def strategy_manager(self):
        """创建策略管理器实例"""
        return CacheStrategyManager()
    
    def test_register_strategy(self, strategy_manager):
        """测试注册策略"""
        config = CacheStrategyConfig(
            cache_type="local",
            ttl=3600,
            max_size=1000,
            eviction_policy="lru"
        )
        
        strategy_manager.register_strategy("test_strategy", config)
        retrieved_config = strategy_manager.get_strategy("test_strategy")
        
        assert retrieved_config is not None
        assert retrieved_config.cache_type == "local"
        assert retrieved_config.ttl == 3600
    
    def test_update_strategy(self, strategy_manager):
        """测试更新策略"""
        # 先注册一个策略
        config = CacheStrategyConfig(cache_type="local", ttl=3600)
        strategy_manager.register_strategy("test_strategy", config)
        
        # 更新策略
        updates = {"ttl": 7200, "max_size": 2000}
        success = strategy_manager.update_strategy("test_strategy", updates)
        
        assert success
        updated_config = strategy_manager.get_strategy("test_strategy")
        assert updated_config.ttl == 7200
        assert updated_config.max_size == 2000
    
    def test_remove_strategy(self, strategy_manager):
        """测试移除策略"""
        config = CacheStrategyConfig(cache_type="local")
        strategy_manager.register_strategy("test_strategy", config)
        
        # 确认策略存在
        assert strategy_manager.get_strategy("test_strategy") is not None
        
        # 移除策略
        success = strategy_manager.remove_strategy("test_strategy")
        assert success
        assert strategy_manager.get_strategy("test_strategy") is None


class TestCacheMonitor:
    """缓存监控器测试"""
    
    @pytest.fixture
    def cache_monitor(self):
        """创建缓存监控器实例"""
        return CacheMonitor()
    
    def test_record_hit(self, cache_monitor):
        """测试记录缓存命中"""
        cache_monitor.record_hit("test_key", 10.5)
        
        metrics = cache_monitor.get_current_metrics()
        assert metrics.total_requests == 1
        assert metrics.cache_hits == 1
        assert metrics.hit_rate == 1.0
        assert metrics.avg_response_time == 10.5
    
    def test_record_miss(self, cache_monitor):
        """测试记录缓存未命中"""
        cache_monitor.record_miss("test_key", 25.0)
        
        metrics = cache_monitor.get_current_metrics()
        assert metrics.total_requests == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.0
        assert metrics.avg_response_time == 25.0
    
    def test_record_error(self, cache_monitor):
        """测试记录错误"""
        cache_monitor.record_error("test_key", "Connection failed")
        
        metrics = cache_monitor.get_current_metrics()
        assert metrics.total_requests == 1
        assert metrics.errors == 1
        assert metrics.error_rate == 1.0
    
    def test_hit_rate_calculation(self, cache_monitor):
        """测试命中率计算"""
        # 记录一些命中和未命中
        cache_monitor.record_hit("key1", 10)
        cache_monitor.record_hit("key2", 15)
        cache_monitor.record_miss("key3", 20)
        cache_monitor.record_miss("key4", 25)
        
        metrics = cache_monitor.get_current_metrics()
        assert metrics.total_requests == 4
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 2
        assert metrics.hit_rate == 0.5
    
    def test_export_metrics(self, cache_monitor):
        """测试导出指标"""
        # 记录一些数据
        cache_monitor.record_hit("key1", 10)
        cache_monitor.record_miss("key2", 20)
        
        # 导出指标
        exported_data = cache_monitor.export_metrics()
        
        assert "timestamp" in exported_data
        assert "metrics" in exported_data
        assert exported_data["metrics"]["total_requests"] == 2
        assert exported_data["metrics"]["cache_hits"] == 1
        assert exported_data["metrics"]["cache_misses"] == 1


class TestCacheOptimizer:
    """缓存优化器测试"""
    
    @pytest.fixture
    def cache_optimizer(self):
        """创建缓存优化器实例"""
        return CacheOptimizer()
    
    @pytest.mark.asyncio
    async def test_analyze_performance(self, cache_optimizer):
        """测试性能分析"""
        # 模拟低命中率的指标
        metrics = CacheMetrics(
            timestamp=datetime.now(),
            total_requests=1000,
            cache_hits=300,  # 30% 命中率
            cache_misses=700,
            hit_rate=0.3,
            avg_response_time=150,  # 高响应时间
            memory_usage=0.9,  # 高内存使用
            errors=50,
            error_rate=0.05
        )
        
        with patch.object(cache_optimizer.cache_monitor, 'get_current_metrics', return_value=metrics):
            suggestions = await cache_optimizer.analyze_performance()
        
        # 应该有优化建议
        assert len(suggestions) > 0
        
        # 检查是否包含预期的优化类型
        optimization_types = [task.optimization_type for task in suggestions]
        assert "ttl_adjustment" in optimization_types or "eviction_policy" in optimization_types
    
    @pytest.mark.asyncio
    async def test_trigger_optimization(self, cache_optimizer):
        """测试触发优化"""
        task = OptimizationTask(
            task_id="test_task",
            optimization_type="ttl_adjustment",
            target_strategy="default",
            parameters={"new_ttl": 7200},
            priority=1
        )
        
        task_id = await cache_optimizer.trigger_optimization(task)
        assert task_id == "test_task"
        
        # 检查任务状态
        status = cache_optimizer.get_optimization_status(task_id)
        assert status is not None
        assert status.task_id == task_id
    
    @pytest.mark.asyncio
    async def test_execute_ttl_adjustment(self, cache_optimizer):
        """测试TTL调整优化"""
        task = OptimizationTask(
            task_id="ttl_test",
            optimization_type="ttl_adjustment",
            target_strategy="default",
            parameters={"new_ttl": 7200}
        )
        
        with patch.object(cache_optimizer.strategy_manager, 'update_strategy', return_value=True) as mock_update:
            result = await cache_optimizer._execute_ttl_adjustment(task)
        
        assert result
        mock_update.assert_called_once_with("default", {"ttl": 7200})


class TestCacheManager:
    """缓存管理器测试"""
    
    @pytest.fixture
    async def cache_manager(self):
        """创建缓存管理器实例"""
        manager = CacheManager()
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, cache_manager):
        """测试基本操作"""
        # 测试设置和获取
        await cache_manager.set("test_key", "test_value")
        value = await cache_manager.get("test_key")
        assert value == "test_value"
        
        # 测试存在性检查
        exists = await cache_manager.exists("test_key")
        assert exists
        
        # 测试删除
        await cache_manager.delete("test_key")
        exists = await cache_manager.exists("test_key")
        assert not exists
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, cache_manager):
        """测试批量操作"""
        # 批量设置
        data = {"key1": "value1", "key2": "value2"}
        await cache_manager.batch_set(data)
        
        # 批量获取
        values = await cache_manager.batch_get(list(data.keys()))
        assert values == data
        
        # 批量删除
        await cache_manager.batch_delete(list(data.keys()))
        values = await cache_manager.batch_get(list(data.keys()))
        assert all(v is None for v in values.values())
    
    @pytest.mark.asyncio
    async def test_get_system_status(self, cache_manager):
        """测试获取系统状态"""
        status = await cache_manager.get_system_status()
        
        assert hasattr(status, 'redis_connected')
        assert hasattr(status, 'local_cache_size')
        assert hasattr(status, 'total_strategies')
        assert hasattr(status, 'active_optimizations')
    
    @pytest.mark.asyncio
    async def test_trigger_optimization(self, cache_manager):
        """测试触发优化"""
        task_id = await cache_manager.trigger_optimization()
        assert task_id is not None
        
        # 检查优化状态
        status = cache_manager.get_optimization_status(task_id)
        assert status is not None


class TestCacheConfig:
    """缓存配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = get_cache_config_for_environment("development")
        
        assert config.enabled
        assert config.environment == "development"
        assert len(config.default_strategies) > 0
        assert "default" in config.default_strategies
    
    def test_environment_specific_config(self):
        """测试环境特定配置"""
        # 测试开发环境
        dev_config = get_cache_config_for_environment("development")
        assert dev_config.monitor.collection_interval == 30
        
        # 测试生产环境
        prod_config = get_cache_config_for_environment("production")
        assert prod_config.monitor.collection_interval == 120
        assert prod_config.monitor.retention_hours == 72
    
    def test_strategy_config_to_dict(self):
        """测试策略配置转换为字典"""
        config = CacheStrategyConfig(
            cache_type="redis",
            ttl=3600,
            max_size=1000,
            eviction_policy="lru",
            compression_enabled=True,
            key_prefix="test"
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["cache_type"] == "redis"
        assert config_dict["ttl"] == 3600
        assert config_dict["max_size"] == 1000
        assert config_dict["eviction_policy"] == "lru"
        assert config_dict["compression_enabled"] is True
        assert config_dict["key_prefix"] == "test"
    
    def test_system_config_to_dict(self):
        """测试系统配置转换为字典"""
        config = get_cache_config_for_environment("testing")
        config_dict = config.to_dict()
        
        assert "enabled" in config_dict
        assert "redis_url" in config_dict
        assert "strategies" in config_dict
        assert "monitor" in config_dict
        assert "optimizer" in config_dict
        assert "manager" in config_dict
        assert "environment" in config_dict


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_system_integration(self):
        """测试完整系统集成"""
        # 创建所有组件
        cache_service = CacheService()
        strategy_manager = CacheStrategyManager()
        cache_monitor = CacheMonitor()
        cache_optimizer = CacheOptimizer()
        cache_manager = CacheManager()
        
        try:
            # 初始化系统
            await cache_service.initialize()
            await cache_manager.initialize()
            
            # 执行一些缓存操作
            await cache_manager.set("integration_key", "integration_value")
            value = await cache_manager.get("integration_key")
            assert value == "integration_value"
            
            # 检查监控指标
            metrics = cache_monitor.get_current_metrics()
            assert metrics.total_requests >= 0
            
            # 获取系统状态
            status = await cache_manager.get_system_status()
            assert status is not None
            
        finally:
            # 清理资源
            await cache_service.close()
            await cache_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        cache_manager = CacheManager()
        
        try:
            await cache_manager.initialize()
            
            # 测试获取不存在的键
            value = await cache_manager.get("nonexistent_key")
            assert value is None
            
            # 测试删除不存在的键
            await cache_manager.delete("nonexistent_key")  # 应该不抛出异常
            
        finally:
            await cache_manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_performance_optimization_flow(self):
        """测试性能优化流程"""
        cache_manager = CacheManager()
        
        try:
            await cache_manager.initialize()
            
            # 模拟一些缓存操作以生成指标
            for i in range(10):
                await cache_manager.set(f"perf_key_{i}", f"value_{i}")
                await cache_manager.get(f"perf_key_{i}")
            
            # 触发优化
            task_id = await cache_manager.trigger_optimization()
            assert task_id is not None
            
            # 检查优化状态
            status = cache_manager.get_optimization_status(task_id)
            assert status is not None
            
        finally:
            await cache_manager.shutdown()


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])