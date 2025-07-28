# 缓存系统使用指南

本文档介绍如何使用项目中的缓存系统，包括基本操作、配置管理、性能监控和优化功能。

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [基本操作](#基本操作)
4. [缓存策略](#缓存策略)
5. [性能监控](#性能监控)
6. [自动优化](#自动优化)
7. [配置管理](#配置管理)
8. [API接口](#api接口)
9. [最佳实践](#最佳实践)
10. [故障排除](#故障排除)

## 系统概述

缓存系统提供了一个完整的缓存解决方案，包括：

- **多级缓存**：支持本地缓存、Redis缓存和混合缓存
- **策略管理**：灵活的缓存策略配置和管理
- **性能监控**：实时监控缓存性能指标
- **自动优化**：基于性能指标的自动优化
- **统一管理**：通过缓存管理器统一管理所有组件

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cache API     │    │  Cache Manager  │    │ Cache Service   │
│   (REST API)    │───▶│  (统一管理器)    │───▶│  (核心服务)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cache Monitor   │    │Cache Optimizer  │    │Strategy Manager │
│  (性能监控)      │    │  (自动优化)      │    │  (策略管理)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 快速开始

### 1. 导入缓存管理器

```python
from app.services.cache_manager import cache_manager
```

### 2. 基本使用

```python
import asyncio

async def main():
    # 设置缓存
    await cache_manager.set("user:123", {"name": "张三", "age": 25})
    
    # 获取缓存
    user_data = await cache_manager.get("user:123")
    print(user_data)  # {'name': '张三', 'age': 25}
    
    # 删除缓存
    await cache_manager.delete("user:123")

asyncio.run(main())
```

### 3. 使用特定策略

```python
# 使用会话策略（较短TTL）
await cache_manager.set("session:abc123", session_data, strategy="session")

# 使用OCR结果策略（较长TTL，启用压缩）
await cache_manager.set("ocr:doc123", ocr_result, strategy="ocr_result")
```

## 基本操作

### 单个操作

```python
# 设置缓存（带TTL）
await cache_manager.set("key1", "value1", ttl=3600)  # 1小时后过期

# 获取缓存
value = await cache_manager.get("key1")

# 检查是否存在
exists = await cache_manager.exists("key1")

# 删除缓存
await cache_manager.delete("key1")
```

### 批量操作

```python
# 批量设置
data = {
    "user:1": {"name": "用户1"},
    "user:2": {"name": "用户2"},
    "user:3": {"name": "用户3"}
}
await cache_manager.batch_set(data)

# 批量获取
keys = ["user:1", "user:2", "user:3"]
values = await cache_manager.batch_get(keys)
# 返回: {"user:1": {"name": "用户1"}, ...}

# 批量删除
await cache_manager.batch_delete(keys)
```

### 缓存管理

```python
# 清空所有缓存
await cache_manager.clear_cache()

# 缓存预热
warmup_data = {
    "config:app": app_config,
    "config:db": db_config
}
await cache_manager.warmup_cache(warmup_data)

# 健康检查
is_healthy = await cache_manager.health_check()
```

## 缓存策略

系统预定义了多种缓存策略：

### 预定义策略

| 策略名称 | 缓存类型 | TTL | 最大大小 | 淘汰策略 | 压缩 | 用途 |
|---------|---------|-----|---------|---------|------|------|
| default | hybrid | 1小时 | 1000 | LRU | 否 | 通用缓存 |
| session | redis | 30分钟 | 500 | TTL | 否 | 会话数据 |
| api_response | local | 5分钟 | 2000 | LRU | 是 | API响应 |
| ocr_result | hybrid | 2小时 | 500 | LRU | 是 | OCR结果 |
| project_data | redis | 30分钟 | 200 | LRU | 否 | 项目数据 |
| user_data | redis | 15分钟 | 1000 | TTL | 否 | 用户数据 |

### 自定义策略

```python
from app.services.cache_strategies import strategy_manager
from app.core.cache_config import CacheStrategyConfig

# 创建自定义策略
custom_config = CacheStrategyConfig(
    cache_type="redis",
    ttl=7200,  # 2小时
    max_size=500,
    eviction_policy="lfu",  # 最少使用频率
    compression_enabled=True,
    key_prefix="custom"
)

# 注册策略
strategy_manager.register_strategy("custom_strategy", custom_config)

# 使用自定义策略
await cache_manager.set("custom:key", data, strategy="custom_strategy")
```

### 动态更新策略

```python
# 更新现有策略
updates = {
    "ttl": 14400,  # 4小时
    "max_size": 1500
}
success = strategy_manager.update_strategy("default", updates)

# 获取策略信息
strategy_info = strategy_manager.get_strategy("default")
print(f"TTL: {strategy_info.ttl}, 最大大小: {strategy_info.max_size}")
```

## 性能监控

### 获取实时指标

```python
from app.services.cache_monitor import cache_monitor

# 获取当前指标
metrics = cache_monitor.get_current_metrics()
print(f"命中率: {metrics.hit_rate:.2%}")
print(f"平均响应时间: {metrics.avg_response_time:.2f}ms")
print(f"内存使用率: {metrics.memory_usage:.2%}")
print(f"错误率: {metrics.error_rate:.2%}")
```

### 历史数据查询

```python
from datetime import datetime, timedelta

# 获取过去24小时的指标
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)
history = cache_monitor.get_metrics_history(start_time, end_time)

for metric in history:
    print(f"{metric.timestamp}: 命中率 {metric.hit_rate:.2%}")
```

### 性能报告

```python
# 生成7天性能报告
report = cache_monitor.generate_performance_report(days=7)
print(f"性能评分: {report.performance_score}/100")
print("优化建议:")
for suggestion in report.recommendations:
    print(f"- {suggestion}")
```

### 导出指标

```python
# 导出指标数据
exported_data = cache_monitor.export_metrics()
print(f"导出时间: {exported_data['timestamp']}")
print(f"总请求数: {exported_data['metrics']['total_requests']}")
```

## 自动优化

### 手动触发优化

```python
# 触发自动优化
task_id = await cache_manager.trigger_optimization()
print(f"优化任务ID: {task_id}")

# 检查优化状态
status = cache_manager.get_optimization_status(task_id)
print(f"任务状态: {status.status}")
print(f"进度: {status.progress}%")
```

### 自定义优化任务

```python
from app.services.cache_optimizer import cache_optimizer, OptimizationTask

# 创建自定义优化任务
task = OptimizationTask(
    task_id="custom_ttl_optimization",
    optimization_type="ttl_adjustment",
    target_strategy="default",
    parameters={"new_ttl": 7200},
    priority=1
)

# 执行优化
task_id = await cache_optimizer.trigger_optimization(task)
```

### 优化类型

系统支持以下优化类型：

1. **TTL调整** (`ttl_adjustment`): 根据访问模式调整过期时间
2. **淘汰策略** (`eviction_policy`): 优化缓存淘汰策略
3. **压缩设置** (`compression`): 启用/禁用数据压缩
4. **缓存级别** (`cache_level`): 调整缓存层级
5. **内存清理** (`memory_cleanup`): 清理过期和无效数据
6. **预加载** (`preload`): 预加载热点数据

## 配置管理

### 环境配置

```python
from app.core.cache_config import get_cache_config_for_environment

# 获取开发环境配置
dev_config = get_cache_config_for_environment("development")

# 获取生产环境配置
prod_config = get_cache_config_for_environment("production")

# 获取测试环境配置
test_config = get_cache_config_for_environment("testing")
```

### 配置文件

```python
from app.core.cache_config import (
    load_cache_config_from_file,
    save_cache_config_to_file
)

# 从文件加载配置
config = load_cache_config_from_file("config/cache_config.json")

# 保存配置到文件
save_cache_config_to_file(config, "config/cache_config_backup.json")
```

### 动态配置更新

```python
# 更新配置
new_config = {
    "monitor": {
        "collection_interval": 30,
        "retention_hours": 48
    },
    "optimizer": {
        "optimization_interval": 180,
        "auto_optimization": True
    }
}

success = update_cache_config(new_config)
```

## API接口

系统提供了完整的REST API接口：

### 缓存操作

```bash
# 设置缓存
curl -X POST "http://localhost:8000/api/v1/cache/set" \
  -H "Content-Type: application/json" \
  -d '{"key": "test_key", "value": "test_value", "ttl": 3600}'

# 获取缓存
curl -X POST "http://localhost:8000/api/v1/cache/get" \
  -H "Content-Type: application/json" \
  -d '{"key": "test_key"}'

# 批量设置
curl -X POST "http://localhost:8000/api/v1/cache/batch/set" \
  -H "Content-Type: application/json" \
  -d '{"data": {"key1": "value1", "key2": "value2"}}'
```

### 监控接口

```bash
# 获取缓存统计
curl "http://localhost:8000/api/v1/cache/stats"

# 获取性能指标
curl "http://localhost:8000/api/v1/cache/metrics"

# 获取性能报告
curl "http://localhost:8000/api/v1/cache/report?days=7"

# 导出指标
curl "http://localhost:8000/api/v1/cache/export"
```

### 管理接口

```bash
# 清空缓存
curl -X POST "http://localhost:8000/api/v1/cache/clear"

# 健康检查
curl "http://localhost:8000/api/v1/cache/health"

# 缓存预热
curl -X POST "http://localhost:8000/api/v1/cache/warmup" \
  -H "Content-Type: application/json" \
  -d '{"data": {"config:app": {"version": "1.0"}}}'

# 触发优化
curl -X POST "http://localhost:8000/api/v1/cache/optimize"

# 获取优化状态
curl "http://localhost:8000/api/v1/cache/optimization/status?task_id=xxx"
```

## 最佳实践

### 1. 键命名规范

```python
# 使用有意义的前缀
user_key = f"user:{user_id}"
session_key = f"session:{session_id}"
api_key = f"api:response:{endpoint}:{params_hash}"

# 避免过长的键名
# 好的例子
key = "project:123:config"
# 不好的例子
key = "very_long_project_name_with_lots_of_details:123:configuration_data"
```

### 2. TTL设置

```python
# 根据数据特性设置合适的TTL

# 频繁变化的数据 - 短TTL
await cache_manager.set("user:online_status", status, ttl=60)  # 1分钟

# 相对稳定的数据 - 中等TTL
await cache_manager.set("user:profile", profile, ttl=1800)  # 30分钟

# 很少变化的数据 - 长TTL
await cache_manager.set("system:config", config, ttl=86400)  # 24小时
```

### 3. 错误处理

```python
async def get_user_data(user_id: int):
    try:
        # 尝试从缓存获取
        cached_data = await cache_manager.get(f"user:{user_id}")
        if cached_data:
            return cached_data
        
        # 缓存未命中，从数据库获取
        user_data = await database.get_user(user_id)
        
        # 存入缓存
        await cache_manager.set(
            f"user:{user_id}", 
            user_data, 
            ttl=1800,
            strategy="user_data"
        )
        
        return user_data
        
    except Exception as e:
        logger.error(f"获取用户数据失败: {e}")
        # 降级到直接数据库查询
        return await database.get_user(user_id)
```

### 4. 批量操作优化

```python
# 使用批量操作提高性能
async def get_multiple_users(user_ids: List[int]):
    # 构造缓存键
    cache_keys = [f"user:{uid}" for uid in user_ids]
    
    # 批量获取缓存
    cached_data = await cache_manager.batch_get(cache_keys)
    
    # 找出缓存未命中的用户ID
    missing_ids = [
        uid for uid in user_ids 
        if cached_data.get(f"user:{uid}") is None
    ]
    
    # 从数据库获取缺失的数据
    if missing_ids:
        db_data = await database.get_users(missing_ids)
        
        # 批量存入缓存
        cache_data = {
            f"user:{uid}": data 
            for uid, data in db_data.items()
        }
        await cache_manager.batch_set(cache_data, ttl=1800)
        
        # 合并结果
        cached_data.update(cache_data)
    
    return cached_data
```

### 5. 监控和告警

```python
import asyncio
from app.services.cache_monitor import cache_monitor

async def monitor_cache_health():
    """监控缓存健康状态"""
    while True:
        try:
            metrics = cache_monitor.get_current_metrics()
            
            # 检查关键指标
            if metrics.hit_rate < 0.8:
                logger.warning(f"缓存命中率过低: {metrics.hit_rate:.2%}")
            
            if metrics.avg_response_time > 100:
                logger.warning(f"缓存响应时间过高: {metrics.avg_response_time:.2f}ms")
            
            if metrics.error_rate > 0.05:
                logger.error(f"缓存错误率过高: {metrics.error_rate:.2%}")
            
            # 等待下次检查
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"缓存监控异常: {e}")
            await asyncio.sleep(60)

# 启动监控任务
asyncio.create_task(monitor_cache_health())
```

## 故障排除

### 常见问题

#### 1. Redis连接失败

```python
# 检查Redis连接
status = await cache_manager.get_system_status()
if not status.redis_connected:
    print("Redis连接失败，请检查配置和网络")
    # 检查配置
    print(f"Redis URL: {cache_config.redis_url}")
```

#### 2. 缓存命中率低

```python
# 分析缓存性能
metrics = cache_monitor.get_current_metrics()
if metrics.hit_rate < 0.5:
    print("缓存命中率过低，建议：")
    print("1. 检查TTL设置是否过短")
    print("2. 检查缓存大小是否足够")
    print("3. 考虑调整淘汰策略")
    
    # 触发自动优化
    await cache_manager.trigger_optimization()
```

#### 3. 内存使用过高

```python
# 检查内存使用
if metrics.memory_usage > 0.9:
    print("内存使用过高，建议：")
    print("1. 启用数据压缩")
    print("2. 减小缓存大小")
    print("3. 调整淘汰策略为LRU")
    
    # 手动清理
    await cache_manager.clear_cache()
```

#### 4. 响应时间过长

```python
# 分析响应时间
if metrics.avg_response_time > 50:
    print("响应时间过长，建议：")
    print("1. 检查网络连接")
    print("2. 考虑使用本地缓存")
    print("3. 优化数据序列化")
```

### 调试工具

```python
# 启用调试模式
import logging
logging.getLogger('cache').setLevel(logging.DEBUG)

# 导出详细指标
detailed_metrics = cache_monitor.export_metrics()
with open('cache_debug.json', 'w') as f:
    json.dump(detailed_metrics, f, indent=2, default=str)

# 生成性能报告
report = cache_monitor.generate_performance_report(days=1)
print("详细性能分析:")
for metric_name, value in report.detailed_metrics.items():
    print(f"{metric_name}: {value}")
```

### 性能调优

```python
# 根据业务场景调优

# 读多写少的场景
read_heavy_config = CacheStrategyConfig(
    cache_type="hybrid",
    ttl=7200,  # 较长TTL
    max_size=2000,  # 较大缓存
    eviction_policy="lru",
    compression_enabled=True
)

# 写多读少的场景
write_heavy_config = CacheStrategyConfig(
    cache_type="local",
    ttl=300,  # 较短TTL
    max_size=500,  # 较小缓存
    eviction_policy="ttl",
    compression_enabled=False
)

# 内存敏感的场景
memory_optimized_config = CacheStrategyConfig(
    cache_type="redis",
    ttl=1800,
    max_size=200,  # 很小的缓存
    eviction_policy="lfu",
    compression_enabled=True  # 启用压缩
)
```

---

## 总结

本缓存系统提供了完整的缓存解决方案，包括：

- ✅ 多级缓存支持
- ✅ 灵活的策略配置
- ✅ 实时性能监控
- ✅ 自动优化功能
- ✅ 完整的API接口
- ✅ 详细的使用文档

通过合理使用这些功能，可以显著提升应用的性能和用户体验。如有问题，请参考故障排除部分或联系开发团队。