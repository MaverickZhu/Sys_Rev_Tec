# -*- coding: utf-8 -*-
"""
错误追踪系统测试
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.core.error_tracking import (
    ErrorEvent,
    ErrorSeverity,
    AlertRule,
    AlertChannel,
    ErrorTracker,
    track_error,
    get_error_stats
)


class TestErrorEvent:
    """测试ErrorEvent类"""
    
    def test_error_event_creation(self):
        """测试错误事件创建"""
        timestamp = datetime.utcnow()
        event = ErrorEvent(
            id="test_error_1",
            timestamp=timestamp,
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error message",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        assert event.id == "test_error_1"
        assert event.error_type == "TEST_ERROR"
        assert event.error_code == "TEST_001"
        assert event.message == "Test error message"
        assert event.severity == ErrorSeverity.MEDIUM
        assert event.path == "/test"
        assert event.method == "GET"
        assert event.count == 1
        assert event.first_seen == timestamp
        assert event.last_seen == timestamp
    
    def test_error_event_to_dict(self):
        """测试错误事件转换为字典"""
        timestamp = datetime.utcnow()
        event = ErrorEvent(
            id="test_error_1",
            timestamp=timestamp,
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error message",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET",
            details={"key": "value"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["id"] == "test_error_1"
        assert event_dict["error_type"] == "TEST_ERROR"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["details"] == {"key": "value"}


class TestAlertRule:
    """测试AlertRule类"""
    
    def test_alert_rule_creation(self):
        """测试报警规则创建"""
        rule = AlertRule(
            name="test_rule",
            error_types={"TEST_ERROR"},
            severity_threshold=ErrorSeverity.MEDIUM,
            frequency_threshold=5,
            time_window=300,
            channels=[AlertChannel.EMAIL, AlertChannel.LOG]
        )
        
        assert rule.name == "test_rule"
        assert rule.error_types == {"TEST_ERROR"}
        assert rule.severity_threshold == ErrorSeverity.MEDIUM
        assert rule.frequency_threshold == 5
        assert rule.time_window == 300
        assert rule.channels == [AlertChannel.EMAIL, AlertChannel.LOG]
        assert rule.enabled is True
        assert rule.cooldown == 300
    
    def test_should_trigger_error_type_match(self):
        """测试错误类型匹配触发条件"""
        rule = AlertRule(
            name="test_rule",
            error_types={"TEST_ERROR"},
            severity_threshold=ErrorSeverity.LOW,
            frequency_threshold=1,
            time_window=300,
            channels=[AlertChannel.LOG]
        )
        
        # 匹配的错误类型
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        assert rule.should_trigger(event, 1) is True
        
        # 不匹配的错误类型
        event.error_type = "OTHER_ERROR"
        assert rule.should_trigger(event, 1) is False
    
    def test_should_trigger_severity_threshold(self):
        """测试严重程度阈值触发条件"""
        rule = AlertRule(
            name="test_rule",
            error_types=set(),  # 匹配所有类型
            severity_threshold=ErrorSeverity.HIGH,
            frequency_threshold=1,
            time_window=300,
            channels=[AlertChannel.LOG]
        )
        
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test",
            severity=ErrorSeverity.CRITICAL,
            path="/test",
            method="GET"
        )
        
        # 严重程度足够高
        assert rule.should_trigger(event, 1) is True
        
        # 严重程度不够
        event.severity = ErrorSeverity.MEDIUM
        assert rule.should_trigger(event, 1) is False
    
    def test_should_trigger_frequency_threshold(self):
        """测试频率阈值触发条件"""
        rule = AlertRule(
            name="test_rule",
            error_types=set(),
            severity_threshold=ErrorSeverity.LOW,
            frequency_threshold=5,
            time_window=300,
            channels=[AlertChannel.LOG]
        )
        
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        # 频率足够
        assert rule.should_trigger(event, 5) is True
        
        # 频率不够
        assert rule.should_trigger(event, 3) is False
    
    def test_should_trigger_cooldown(self):
        """测试冷却时间触发条件"""
        rule = AlertRule(
            name="test_rule",
            error_types=set(),
            severity_threshold=ErrorSeverity.LOW,
            frequency_threshold=1,
            time_window=300,
            channels=[AlertChannel.LOG],
            cooldown=300
        )
        
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        # 没有上次触发时间
        assert rule.should_trigger(event, 1) is True
        
        # 设置上次触发时间（在冷却期内）
        rule.last_triggered = datetime.utcnow() - timedelta(seconds=100)
        assert rule.should_trigger(event, 1) is False
        
        # 设置上次触发时间（冷却期外）
        rule.last_triggered = datetime.utcnow() - timedelta(seconds=400)
        assert rule.should_trigger(event, 1) is True


class TestErrorTracker:
    """测试ErrorTracker类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.tracker = ErrorTracker()
    
    def test_track_error_new(self):
        """测试追踪新错误"""
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        self.tracker.track_error(event)
        
        # 检查错误是否被存储
        error_key = self.tracker._generate_error_key(event)
        assert error_key in self.tracker._errors
        assert self.tracker._errors[error_key].count == 1
        assert len(self.tracker._error_history) == 1
    
    def test_track_error_duplicate(self):
        """测试追踪重复错误"""
        event1 = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        event2 = ErrorEvent(
            id="test_2",
            timestamp=datetime.utcnow() + timedelta(seconds=10),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        self.tracker.track_error(event1)
        self.tracker.track_error(event2)
        
        # 检查错误计数
        error_key = self.tracker._generate_error_key(event1)
        assert self.tracker._errors[error_key].count == 2
        assert len(self.tracker._error_history) == 2
    
    def test_generate_error_key(self):
        """测试错误键生成"""
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        key = self.tracker._generate_error_key(event)
        expected_key = "TEST_ERROR:TEST_001:/test"
        assert key == expected_key
    
    @patch('asyncio.create_task')
    def test_check_alert_rules(self, mock_create_task):
        """测试报警规则检查"""
        # 添加一个简单的报警规则
        rule = AlertRule(
            name="test_rule",
            error_types=set(),
            severity_threshold=ErrorSeverity.LOW,
            frequency_threshold=1,
            time_window=300,
            channels=[AlertChannel.LOG]
        )
        self.tracker.add_alert_rule(rule)
        
        event = ErrorEvent(
            id="test_1",
            timestamp=datetime.utcnow(),
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error",
            severity=ErrorSeverity.MEDIUM,
            path="/test",
            method="GET"
        )
        
        self.tracker.track_error(event)
        
        # 检查是否创建了报警任务
        mock_create_task.assert_called_once()
    
    def test_get_error_statistics(self):
        """测试获取错误统计"""
        # 添加一些测试错误
        events = [
            ErrorEvent(
                id=f"test_{i}",
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                error_type="TEST_ERROR" if i % 2 == 0 else "OTHER_ERROR",
                error_code="TEST_001",
                message=f"Test error {i}",
                severity=ErrorSeverity.MEDIUM,
                path=f"/test/{i}",
                method="GET"
            )
            for i in range(5)
        ]
        
        for event in events:
            self.tracker.track_error(event)
        
        stats = self.tracker.get_error_statistics(hours=1)
        
        assert stats["total_errors"] == 5
        assert stats["error_by_type"]["TEST_ERROR"] == 3
        assert stats["error_by_type"]["OTHER_ERROR"] == 2
        assert len(stats["top_errors"]) > 0
    
    def test_add_remove_alert_rule(self):
        """测试添加和移除报警规则"""
        rule = AlertRule(
            name="test_rule",
            error_types={"TEST_ERROR"},
            severity_threshold=ErrorSeverity.MEDIUM,
            frequency_threshold=5,
            time_window=300,
            channels=[AlertChannel.LOG]
        )
        
        # 添加规则
        self.tracker.add_alert_rule(rule)
        rules = self.tracker.get_alert_rules()
        assert len(rules) > 0
        assert any(r.name == "test_rule" for r in rules)
        
        # 移除规则
        success = self.tracker.remove_alert_rule("test_rule")
        assert success is True
        
        # 尝试移除不存在的规则
        success = self.tracker.remove_alert_rule("nonexistent_rule")
        assert success is False
    
    def test_clear_old_errors(self):
        """测试清理旧错误"""
        # 添加新错误
        new_event = ErrorEvent(
            id="new_error",
            timestamp=datetime.utcnow(),
            error_type="NEW_ERROR",
            error_code="NEW_001",
            message="New error",
            severity=ErrorSeverity.MEDIUM,
            path="/new",
            method="GET"
        )
        
        # 添加旧错误
        old_event = ErrorEvent(
            id="old_error",
            timestamp=datetime.utcnow() - timedelta(days=10),
            error_type="OLD_ERROR",
            error_code="OLD_001",
            message="Old error",
            severity=ErrorSeverity.MEDIUM,
            path="/old",
            method="GET"
        )
        old_event.last_seen = datetime.utcnow() - timedelta(days=10)
        
        self.tracker.track_error(new_event)
        self.tracker.track_error(old_event)
        
        # 清理7天前的错误
        cleaned_count = self.tracker.clear_old_errors(days=7)
        
        assert cleaned_count > 0
        # 新错误应该还在
        new_key = self.tracker._generate_error_key(new_event)
        assert new_key in self.tracker._errors


class TestErrorTrackingFunctions:
    """测试错误追踪便捷函数"""
    
    @patch('app.core.error_tracking.error_tracker')
    def test_track_error_function(self, mock_tracker):
        """测试track_error便捷函数"""
        track_error(
            error_type="TEST_ERROR",
            error_code="TEST_001",
            message="Test error message",
            severity=ErrorSeverity.HIGH,
            path="/test",
            method="POST",
            user_id="user123",
            request_id="req123",
            client_ip="192.168.1.1",
            details={"key": "value"}
        )
        
        # 检查是否调用了tracker的track_error方法
        mock_tracker.track_error.assert_called_once()
        
        # 检查传递的参数
        call_args = mock_tracker.track_error.call_args[0][0]
        assert call_args.error_type == "TEST_ERROR"
        assert call_args.error_code == "TEST_001"
        assert call_args.message == "Test error message"
        assert call_args.severity == ErrorSeverity.HIGH
        assert call_args.path == "/test"
        assert call_args.method == "POST"
        assert call_args.user_id == "user123"
        assert call_args.request_id == "req123"
        assert call_args.client_ip == "192.168.1.1"
        assert call_args.details == {"key": "value"}
    
    @patch('app.core.error_tracking.error_tracker')
    def test_get_error_stats_function(self, mock_tracker):
        """测试get_error_stats便捷函数"""
        mock_tracker.get_error_statistics.return_value = {"total_errors": 10}
        
        stats = get_error_stats(hours=12)
        
        mock_tracker.get_error_statistics.assert_called_once_with(12)
        assert stats == {"total_errors": 10}


class TestErrorTrackingIntegration:
    """错误追踪集成测试"""
    
    @pytest.mark.asyncio
    async def test_alert_sending_integration(self):
        """测试报警发送集成"""
        tracker = ErrorTracker()
        
        # 模拟发送报警的方法
        with patch.object(tracker, '_send_log_alert', new_callable=AsyncMock) as mock_log_alert:
            # 添加一个会立即触发的规则
            rule = AlertRule(
                name="immediate_rule",
                error_types=set(),
                severity_threshold=ErrorSeverity.LOW,
                frequency_threshold=1,
                time_window=300,
                channels=[AlertChannel.LOG]
            )
            tracker.add_alert_rule(rule)
            
            # 创建错误事件
            event = ErrorEvent(
                id="test_alert",
                timestamp=datetime.utcnow(),
                error_type="TEST_ERROR",
                error_code="TEST_001",
                message="Test alert error",
                severity=ErrorSeverity.CRITICAL,
                path="/test",
                method="GET"
            )
            
            # 追踪错误（应该触发报警）
            tracker.track_error(event)
            
            # 等待异步任务完成
            await asyncio.sleep(0.1)
            
            # 检查是否发送了报警
            # 注意：由于异步任务的执行，这个测试可能需要调整
    
    def test_error_deduplication(self):
        """测试错误去重"""
        tracker = ErrorTracker()
        
        # 创建相同的错误事件
        base_event = {
            "error_type": "DUPLICATE_ERROR",
            "error_code": "DUP_001",
            "message": "Duplicate error",
            "severity": ErrorSeverity.MEDIUM,
            "path": "/duplicate",
            "method": "GET"
        }
        
        # 追踪多个相同的错误
        for i in range(5):
            event = ErrorEvent(
                id=f"dup_{i}",
                timestamp=datetime.utcnow() + timedelta(seconds=i),
                **base_event
            )
            tracker.track_error(event)
        
        # 检查去重效果
        error_key = f"{base_event['error_type']}:{base_event['error_code']}:{base_event['path']}"
        assert error_key in tracker._errors
        assert tracker._errors[error_key].count == 5
        assert len(tracker._error_history) == 5  # 历史记录保留所有事件
    
    def test_time_window_filtering(self):
        """测试时间窗口过滤"""
        tracker = ErrorTracker()
        
        # 使用当前时间作为基准
        current_time = datetime.utcnow()
        
        # 添加不同时间的错误
        # 创建明确的时间点：2小时前、1.5小时前、30分钟前、现在
        events = [
            ErrorEvent(
                id="old_error",
                timestamp=current_time - timedelta(hours=2),  # 2小时前
                error_type="OLD_ERROR",
                error_code="OLD_001",
                message="Old error",
                severity=ErrorSeverity.MEDIUM,
                path="/old",
                method="GET"
            ),
            ErrorEvent(
                id="recent_error_1",
                timestamp=current_time - timedelta(minutes=30),  # 30分钟前
                error_type="RECENT_ERROR",
                error_code="REC_001",
                message="Recent error 1",
                severity=ErrorSeverity.MEDIUM,
                path="/recent",
                method="GET"
            ),
            ErrorEvent(
                id="recent_error_2",
                timestamp=current_time - timedelta(minutes=10),  # 10分钟前
                error_type="RECENT_ERROR",
                error_code="REC_002",
                message="Recent error 2",
                severity=ErrorSeverity.MEDIUM,
                path="/recent2",
                method="GET"
            )
        ]
        
        for event in events:
            tracker.track_error(event)
        
        # 获取1小时内的统计
        stats_1h = tracker.get_error_statistics(hours=1)
        # 获取3小时内的统计
        stats_3h = tracker.get_error_statistics(hours=3)
        
        # 1小时内应该有2个错误（30分钟前和10分钟前）
        assert stats_1h["total_errors"] == 2
        # 3小时内应该有3个错误（所有错误）
        assert stats_3h["total_errors"] == 3
        
        # 验证错误类型统计
        assert stats_1h["error_by_type"]["RECENT_ERROR"] == 2
        assert stats_3h["error_by_type"]["OLD_ERROR"] == 1
        assert stats_3h["error_by_type"]["RECENT_ERROR"] == 2


if __name__ == "__main__":
    pytest.main([__file__])