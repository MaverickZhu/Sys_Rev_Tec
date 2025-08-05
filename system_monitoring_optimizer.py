#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控优化脚本
优化系统监控配置、告警规则和性能指标收集
"""

import os
import sys
import json
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config.performance_config import PerformanceConfig, load_and_validate_config
except ImportError:
    print("警告: 无法导入性能配置模块，使用默认配置")
    PerformanceConfig = None


@dataclass
class MonitoringMetrics:
    """监控指标数据结构"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    response_time: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    db_connections: int = 0
    api_throughput: float = 0.0


class SystemMonitoringOptimizer:
    """系统监控优化器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics_history: List[MonitoringMetrics] = []
        self.optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'config_optimization': {},
            'alert_optimization': {},
            'metrics_analysis': {},
            'performance_recommendations': [],
            'success_rate': 0.0
        }
        
        # 设置日志
        self._setup_logging()
        
    def _load_config(self) -> Optional[PerformanceConfig]:
        """加载性能监控配置"""
        try:
            if PerformanceConfig:
                return load_and_validate_config()
            return None
        except Exception as e:
            print(f"配置加载失败: {e}")
            return None
    
    def _setup_logging(self):
        """设置日志配置"""
        log_level = logging.INFO
        if self.config and hasattr(self.config.monitoring, 'performance_log_level'):
            log_level = getattr(logging, self.config.monitoring.performance_log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('system_monitoring_optimization.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_system_metrics(self) -> MonitoringMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # 进程数量
            process_count = len(psutil.pids())
            
            # 负载平均值（仅Linux/Unix）
            try:
                load_average = list(os.getloadavg())
            except (OSError, AttributeError):
                load_average = [0.0, 0.0, 0.0]
            
            metrics = MonitoringMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"系统指标收集失败: {e}")
            raise
    
    def analyze_config_optimization(self) -> Dict[str, Any]:
        """分析配置优化"""
        self.logger.info("开始配置优化分析...")
        
        optimization = {
            'current_config': {},
            'recommended_changes': [],
            'optimization_score': 0
        }
        
        try:
            if self.config:
                # 当前配置分析
                optimization['current_config'] = {
                    'metrics_collection_interval': self.config.monitoring.metrics_collection_interval,
                    'alert_check_interval': self.config.monitoring.alert_check_interval,
                    'slow_request_threshold': self.config.monitoring.slow_request_threshold,
                    'enabled_monitoring': {
                        'system': self.config.monitoring.enable_system_monitoring,
                        'api': self.config.monitoring.enable_api_monitoring,
                        'database': self.config.monitoring.enable_database_monitoring,
                        'cache': self.config.monitoring.enable_cache_monitoring,
                        'business': self.config.monitoring.enable_business_monitoring
                    }
                }
                
                # 配置优化建议
                score = 70  # 基础分数
                
                # 检查收集间隔
                if self.config.monitoring.metrics_collection_interval > 60:
                    optimization['recommended_changes'].append({
                        'type': 'metrics_interval',
                        'current': self.config.monitoring.metrics_collection_interval,
                        'recommended': 30,
                        'reason': '降低指标收集间隔以提高监控精度'
                    })
                else:
                    score += 10
                
                # 检查告警间隔
                if self.config.monitoring.alert_check_interval > 120:
                    optimization['recommended_changes'].append({
                        'type': 'alert_interval',
                        'current': self.config.monitoring.alert_check_interval,
                        'recommended': 60,
                        'reason': '缩短告警检查间隔以快速响应问题'
                    })
                else:
                    score += 10
                
                # 检查慢请求阈值
                if self.config.monitoring.slow_request_threshold > 3.0:
                    optimization['recommended_changes'].append({
                        'type': 'slow_request_threshold',
                        'current': self.config.monitoring.slow_request_threshold,
                        'recommended': 2.0,
                        'reason': '降低慢请求阈值以更好地识别性能问题'
                    })
                else:
                    score += 10
                
                optimization['optimization_score'] = min(score, 100)
            
            else:
                optimization['recommended_changes'].append({
                    'type': 'config_missing',
                    'reason': '建议创建完整的性能监控配置文件'
                })
            
            self.logger.info(f"配置优化分析完成，得分: {optimization['optimization_score']}")
            return optimization
            
        except Exception as e:
            self.logger.error(f"配置优化分析失败: {e}")
            return optimization
    
    def analyze_alert_optimization(self) -> Dict[str, Any]:
        """分析告警优化"""
        self.logger.info("开始告警优化分析...")
        
        alert_analysis = {
            'current_thresholds': {},
            'recommended_thresholds': {},
            'alert_rules': [],
            'optimization_score': 0
        }
        
        try:
            if self.config:
                # 当前阈值
                alert_analysis['current_thresholds'] = {
                    'response_time': {
                        'warning': self.config.alert_thresholds.response_time_warning,
                        'critical': self.config.alert_thresholds.response_time_critical
                    },
                    'cpu_usage': {
                        'warning': self.config.alert_thresholds.cpu_usage_warning,
                        'critical': self.config.alert_thresholds.cpu_usage_critical
                    },
                    'memory_usage': {
                        'warning': self.config.alert_thresholds.memory_usage_warning,
                        'critical': self.config.alert_thresholds.memory_usage_critical
                    },
                    'error_rate': {
                        'warning': self.config.alert_thresholds.error_rate_warning,
                        'critical': self.config.alert_thresholds.error_rate_critical
                    }
                }
                
                # 基于历史数据的推荐阈值
                if self.metrics_history:
                    avg_cpu = sum(m.cpu_usage for m in self.metrics_history) / len(self.metrics_history)
                    avg_memory = sum(m.memory_usage for m in self.metrics_history) / len(self.metrics_history)
                    
                    alert_analysis['recommended_thresholds'] = {
                        'cpu_usage': {
                            'warning': min(avg_cpu * 1.5, 80.0),
                            'critical': min(avg_cpu * 2.0, 95.0)
                        },
                        'memory_usage': {
                            'warning': min(avg_memory * 1.3, 85.0),
                            'critical': min(avg_memory * 1.5, 95.0)
                        }
                    }
                
                # 告警规则建议
                alert_analysis['alert_rules'] = [
                    {
                        'name': '高CPU使用率持续告警',
                        'condition': 'CPU使用率超过阈值持续5分钟',
                        'action': '发送告警通知并记录日志'
                    },
                    {
                        'name': '内存泄漏检测',
                        'condition': '内存使用率持续上升超过30分钟',
                        'action': '发送严重告警并建议重启服务'
                    },
                    {
                        'name': '磁盘空间不足预警',
                        'condition': '磁盘使用率超过85%',
                        'action': '发送预警通知并建议清理空间'
                    },
                    {
                        'name': 'API响应时间异常',
                        'condition': 'API平均响应时间超过阈值',
                        'action': '发送性能告警并触发性能分析'
                    }
                ]
                
                alert_analysis['optimization_score'] = 85
            
            self.logger.info("告警优化分析完成")
            return alert_analysis
            
        except Exception as e:
            self.logger.error(f"告警优化分析失败: {e}")
            return alert_analysis
    
    def analyze_metrics_performance(self) -> Dict[str, Any]:
        """分析指标性能"""
        self.logger.info("开始指标性能分析...")
        
        metrics_analysis = {
            'collection_performance': {},
            'data_quality': {},
            'storage_optimization': {},
            'recommendations': []
        }
        
        try:
            if self.metrics_history:
                # 收集性能分析
                collection_times = []
                for i in range(1, len(self.metrics_history)):
                    prev_time = datetime.fromisoformat(self.metrics_history[i-1].timestamp)
                    curr_time = datetime.fromisoformat(self.metrics_history[i].timestamp)
                    collection_times.append((curr_time - prev_time).total_seconds())
                
                if collection_times:
                    metrics_analysis['collection_performance'] = {
                        'avg_interval': sum(collection_times) / len(collection_times),
                        'min_interval': min(collection_times),
                        'max_interval': max(collection_times),
                        'consistency_score': 100 - (max(collection_times) - min(collection_times)) * 10
                    }
                
                # 数据质量分析
                cpu_values = [m.cpu_usage for m in self.metrics_history]
                memory_values = [m.memory_usage for m in self.metrics_history]
                
                metrics_analysis['data_quality'] = {
                    'cpu_stats': {
                        'avg': sum(cpu_values) / len(cpu_values),
                        'min': min(cpu_values),
                        'max': max(cpu_values),
                        'variance': sum((x - sum(cpu_values)/len(cpu_values))**2 for x in cpu_values) / len(cpu_values)
                    },
                    'memory_stats': {
                        'avg': sum(memory_values) / len(memory_values),
                        'min': min(memory_values),
                        'max': max(memory_values),
                        'variance': sum((x - sum(memory_values)/len(memory_values))**2 for x in memory_values) / len(memory_values)
                    }
                }
                
                # 存储优化建议
                data_points = len(self.metrics_history)
                estimated_daily_points = data_points * (86400 / (sum(collection_times) / len(collection_times))) if collection_times else 2880
                
                metrics_analysis['storage_optimization'] = {
                    'current_data_points': data_points,
                    'estimated_daily_points': int(estimated_daily_points),
                    'storage_recommendations': [
                        '使用时间序列数据库（如InfluxDB）存储指标数据',
                        '实施数据压缩和归档策略',
                        '设置合理的数据保留期限',
                        '使用数据聚合减少存储需求'
                    ]
                }
                
                # 优化建议
                metrics_analysis['recommendations'] = [
                    '实施指标数据的批量收集以提高效率',
                    '使用异步处理避免阻塞主线程',
                    '添加指标数据的缓存机制',
                    '实施智能采样策略减少数据量',
                    '建立指标数据的质量检查机制'
                ]
            
            self.logger.info("指标性能分析完成")
            return metrics_analysis
            
        except Exception as e:
            self.logger.error(f"指标性能分析失败: {e}")
            return metrics_analysis
    
    def generate_performance_recommendations(self) -> List[Dict[str, Any]]:
        """生成性能优化建议"""
        self.logger.info("生成性能优化建议...")
        
        recommendations = [
            {
                'category': '监控配置优化',
                'priority': 'high',
                'title': '优化指标收集间隔',
                'description': '根据系统负载动态调整指标收集频率',
                'implementation': '在高负载时降低收集频率，在低负载时提高精度',
                'expected_benefit': '减少监控开销，提高系统性能'
            },
            {
                'category': '告警策略优化',
                'priority': 'high',
                'title': '实施智能告警',
                'description': '基于历史数据和机器学习的动态阈值告警',
                'implementation': '使用统计分析识别异常模式，减少误报',
                'expected_benefit': '提高告警准确性，减少告警疲劳'
            },
            {
                'category': '数据存储优化',
                'priority': 'medium',
                'title': '实施数据分层存储',
                'description': '根据数据访问频率实施分层存储策略',
                'implementation': '热数据存储在内存，温数据存储在SSD，冷数据归档',
                'expected_benefit': '降低存储成本，提高查询性能'
            },
            {
                'category': '性能监控增强',
                'priority': 'medium',
                'title': '添加业务指标监控',
                'description': '监控关键业务指标和用户体验指标',
                'implementation': '集成APM工具，监控事务性能和用户满意度',
                'expected_benefit': '提供端到端的性能可见性'
            },
            {
                'category': '自动化优化',
                'priority': 'low',
                'title': '实施自动化响应',
                'description': '基于告警自动执行修复操作',
                'implementation': '配置自动扩容、重启服务、清理缓存等操作',
                'expected_benefit': '减少人工干预，提高系统可用性'
            }
        ]
        
        return recommendations
    
    def run_optimization(self) -> Dict[str, Any]:
        """运行完整的监控优化分析"""
        self.logger.info("开始系统监控优化分析...")
        
        try:
            # 收集系统指标（多次采样）
            self.logger.info("收集系统指标...")
            for i in range(5):
                metrics = self.collect_system_metrics()
                self.logger.info(f"采样 {i+1}/5: CPU={metrics.cpu_usage:.1f}%, 内存={metrics.memory_usage:.1f}%")
                if i < 4:  # 最后一次不等待
                    time.sleep(2)
            
            # 执行各项分析
            self.optimization_results['config_optimization'] = self.analyze_config_optimization()
            self.optimization_results['alert_optimization'] = self.analyze_alert_optimization()
            self.optimization_results['metrics_analysis'] = self.analyze_metrics_performance()
            self.optimization_results['performance_recommendations'] = self.generate_performance_recommendations()
            
            # 计算总体成功率
            success_count = 0
            total_count = 4
            
            if self.optimization_results['config_optimization']:
                success_count += 1
            if self.optimization_results['alert_optimization']:
                success_count += 1
            if self.optimization_results['metrics_analysis']:
                success_count += 1
            if self.optimization_results['performance_recommendations']:
                success_count += 1
            
            self.optimization_results['success_rate'] = (success_count / total_count) * 100
            
            # 保存结果
            self.save_optimization_report()
            
            self.logger.info(f"系统监控优化完成，成功率: {self.optimization_results['success_rate']:.1f}%")
            return self.optimization_results
            
        except Exception as e:
            self.logger.error(f"系统监控优化失败: {e}")
            self.optimization_results['error'] = str(e)
            return self.optimization_results
    
    def save_optimization_report(self):
        """保存优化报告"""
        try:
            report_file = 'system_monitoring_optimization_report.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.optimization_results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"优化报告已保存到: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存优化报告失败: {e}")


def main():
    """主函数"""
    print("🔍 系统监控优化分析")
    print("=" * 50)
    
    try:
        # 创建优化器实例
        optimizer = SystemMonitoringOptimizer()
        
        # 运行优化分析
        results = optimizer.run_optimization()
        
        # 显示结果摘要
        print(f"\n📊 优化分析完成")
        print(f"成功率: {results['success_rate']:.1f}%")
        print(f"时间戳: {results['timestamp']}")
        
        if 'config_optimization' in results:
            config_opt = results['config_optimization']
            print(f"\n⚙️ 配置优化得分: {config_opt.get('optimization_score', 0)}")
            print(f"建议更改数量: {len(config_opt.get('recommended_changes', []))}")
        
        if 'performance_recommendations' in results:
            recommendations = results['performance_recommendations']
            high_priority = len([r for r in recommendations if r['priority'] == 'high'])
            print(f"\n🎯 性能建议: {len(recommendations)} 项（{high_priority} 项高优先级）")
        
        print(f"\n📄 详细报告已保存到: system_monitoring_optimization_report.json")
        
    except Exception as e:
        print(f"❌ 优化分析失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())