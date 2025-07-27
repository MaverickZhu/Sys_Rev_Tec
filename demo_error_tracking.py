#!/usr/bin/env python3
"""
错误追踪和报警系统演示脚本

这个脚本演示了如何使用错误追踪系统的各种功能：
1. 错误事件追踪
2. 报警规则配置
3. 错误统计查看
4. 错误去重
5. 时间窗口过滤
"""

import asyncio
from datetime import datetime, timedelta
from app.core.error_tracking import (
    ErrorTracker, ErrorEvent, AlertRule, ErrorSeverity, AlertChannel
)
from app.core.error_tracking import track_error, get_error_stats


def demo_basic_error_tracking():
    """演示基本的错误追踪功能"""
    print("=== 基本错误追踪演示 ===")
    
    # 创建错误追踪器
    tracker = ErrorTracker()
    
    # 创建一些测试错误事件
    errors = [
        ErrorEvent(
            id="demo_1",
            timestamp=datetime.utcnow(),
            error_type="DATABASE_ERROR",
            error_code="DB_001",
            message="数据库连接失败",
            severity=ErrorSeverity.HIGH,
            path="/api/users",
            method="GET",
            user_id="user123",
            details={"database": "postgres", "timeout": 30}
        ),
        ErrorEvent(
            id="demo_2",
            timestamp=datetime.utcnow(),
            error_type="VALIDATION_ERROR",
            error_code="VAL_001",
            message="用户输入验证失败",
            severity=ErrorSeverity.MEDIUM,
            path="/api/users",
            method="POST",
            user_id="user456",
            details={"field": "email", "value": "invalid-email"}
        ),
        ErrorEvent(
            id="demo_3",
            timestamp=datetime.utcnow(),
            error_type="AUTHENTICATION_ERROR",
            error_code="AUTH_001",
            message="用户认证失败",
            severity=ErrorSeverity.HIGH,
            path="/api/login",
            method="POST",
            user_id="user789",
            details={"reason": "invalid_credentials"}
        )
    ]
    
    # 追踪错误
    for error in errors:
        tracker.track_error(error)
        print(f"追踪错误: {error.error_type} - {error.message}")
    
    # 获取统计信息
    stats = tracker.get_error_statistics()
    print(f"\n总错误数: {stats['total_errors']}")
    print(f"按类型统计: {stats['error_by_type']}")
    print(f"按严重程度统计: {stats['error_by_severity']}")
    print(f"按路径统计: {stats['error_by_path']}")
    
    return tracker


def demo_alert_rules(tracker):
    """演示报警规则功能"""
    print("\n=== 报警规则演示 ===")
    
    # 创建报警规则
    rules = [
        AlertRule(
            name="高严重程度错误报警",
            error_types=set(),  # 所有错误类型
            severity_threshold=ErrorSeverity.HIGH,
            frequency_threshold=1,  # 1次就报警
            time_window=3600,  # 1小时窗口
            channels=[AlertChannel.EMAIL, AlertChannel.WEBHOOK],
            cooldown=1800,  # 30分钟冷却
            enabled=True
        ),
        AlertRule(
            name="数据库错误报警",
            error_types={"DATABASE_ERROR"},
            severity_threshold=ErrorSeverity.MEDIUM,
            frequency_threshold=3,  # 3次才报警
            time_window=1800,  # 30分钟窗口
            channels=[AlertChannel.EMAIL],
            cooldown=3600,  # 1小时冷却
            enabled=True
        )
    ]
    
    # 添加报警规则
    for rule in rules:
        tracker._alert_rules.append(rule)  # 直接添加到内部列表
        print(f"添加报警规则: {rule.name}")
    
    # 显示当前规则
    current_rules = tracker._alert_rules  # 直接访问内部属性
    print(f"\n当前报警规则数量: {len(current_rules)}")
    for rule in current_rules:
        error_types_str = ", ".join(rule.error_types) if rule.error_types else "所有类型"
        print(f"- {rule.name}: {error_types_str} >= {rule.frequency_threshold}次/{rule.time_window}秒")


def demo_error_deduplication(tracker):
    """演示错误去重功能"""
    print("\n=== 错误去重演示 ===")
    
    # 创建重复的错误
    duplicate_error = ErrorEvent(
        id="dup_1",
        timestamp=datetime.utcnow(),
        error_type="DUPLICATE_TEST",
        error_code="DUP_001",
        message="这是一个重复错误",
        severity=ErrorSeverity.MEDIUM,
        path="/api/test",
        method="GET"
    )
    
    # 追踪同样的错误多次
    print("追踪相同错误5次...")
    for i in range(5):
        # 使用不同的ID但相同的内容
        error = ErrorEvent(
            id=f"dup_{i+1}",
            timestamp=datetime.utcnow(),
            error_type=duplicate_error.error_type,
            error_code=duplicate_error.error_code,
            message=duplicate_error.message,
            severity=duplicate_error.severity,
            path=duplicate_error.path,
            method=duplicate_error.method
        )
        tracker.track_error(error)
    
    # 检查去重效果
    stats = tracker.get_error_statistics()
    print(f"去重后的错误统计: {stats['error_by_type']}")


def demo_time_window_filtering(tracker):
    """演示时间窗口过滤功能"""
    print("\n=== 时间窗口过滤演示 ===")
    
    # 创建不同时间的错误
    current_time = datetime.utcnow()
    time_errors = [
        ErrorEvent(
            id="time_1",
            timestamp=current_time - timedelta(hours=2),
            error_type="TIME_TEST",
            error_code="TIME_001",
            message="2小时前的错误",
            severity=ErrorSeverity.LOW,
            path="/api/time1",
            method="GET"
        ),
        ErrorEvent(
            id="time_2",
            timestamp=current_time - timedelta(minutes=30),
            error_type="TIME_TEST",
            error_code="TIME_002",
            message="30分钟前的错误",
            severity=ErrorSeverity.MEDIUM,
            path="/api/time2",
            method="GET"
        ),
        ErrorEvent(
            id="time_3",
            timestamp=current_time - timedelta(minutes=5),
            error_type="TIME_TEST",
            error_code="TIME_003",
            message="5分钟前的错误",
            severity=ErrorSeverity.HIGH,
            path="/api/time3",
            method="GET"
        )
    ]
    
    # 追踪时间错误
    for error in time_errors:
        tracker.track_error(error)
    
    # 获取不同时间窗口的统计
    stats_1h = tracker.get_error_statistics(hours=1)
    stats_3h = tracker.get_error_statistics(hours=3)
    
    print(f"1小时内错误数: {stats_1h['total_errors']}")
    print(f"3小时内错误数: {stats_3h['total_errors']}")
    print(f"1小时内按类型: {stats_1h['error_by_type']}")
    print(f"3小时内按类型: {stats_3h['error_by_type']}")


def demo_convenience_functions():
    """演示便捷函数"""
    print("\n=== 便捷函数演示 ===")
    
    # 使用便捷函数追踪错误
    track_error(
        error_type="CONVENIENCE_TEST",
        error_code="CONV_001",
        message="使用便捷函数追踪的错误",
        severity=ErrorSeverity.MEDIUM,
        path="/api/convenience",
        method="POST",
        user_id="conv_user",
        details={"function": "track_error"}
    )
    
    # 使用便捷函数获取统计
    stats = get_error_stats(hours=24)
    print(f"便捷函数获取的统计: 总错误数 = {stats['total_errors']}")


async def demo_alert_sending():
    """演示报警发送功能"""
    print("\n=== 报警发送演示 ===")
    
    tracker = ErrorTracker()
    
    # 添加一个低阈值的报警规则
    alert_rule = AlertRule(
        name="演示报警",
        error_types={"ALERT_DEMO"},
        severity_threshold=ErrorSeverity.HIGH,
        frequency_threshold=1,
        time_window=3600,
        channels=[AlertChannel.EMAIL],
        cooldown=60,
        enabled=True
    )
    tracker._alert_rules.append(alert_rule)  # 直接添加到内部列表
    
    # 创建触发报警的错误
    error = ErrorEvent(
        id="alert_demo",
        timestamp=datetime.utcnow(),
        error_type="ALERT_DEMO",
        error_code="ALERT_001",
        message="这个错误会触发报警",
        severity=ErrorSeverity.HIGH,
        path="/api/alert",
        method="GET"
    )
    
    # 追踪错误（这会触发报警检查）
    tracker.track_error(error)  # 移除 await，因为这是同步方法
    print("错误已追踪，报警规则已检查")


def main():
    """主演示函数"""
    print("错误追踪和报警系统演示")
    print("=" * 50)
    
    # 基本功能演示
    tracker = demo_basic_error_tracking()
    
    # 报警规则演示
    demo_alert_rules(tracker)
    
    # 错误去重演示
    demo_error_deduplication(tracker)
    
    # 时间窗口过滤演示
    demo_time_window_filtering(tracker)
    
    # 便捷函数演示
    demo_convenience_functions()
    
    # 报警发送演示（异步）
    print("\n运行异步报警演示...")
    asyncio.run(demo_alert_sending())
    
    print("\n=== 演示完成 ===")
    print("错误追踪系统已成功演示所有主要功能！")


if __name__ == "__main__":
    main()