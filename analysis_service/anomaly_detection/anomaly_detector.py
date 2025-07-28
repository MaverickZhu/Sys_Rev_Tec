#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测器
政府采购项目异常检测的核心引擎

主要功能:
- 多算法异常检测
- 模式识别和学习
- 实时异常监控
- 异常评分和分级
- 智能报告生成

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
from collections import defaultdict

# 机器学习库
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.svm import OneClassSVM
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn未安装，部分机器学习功能将不可用")

from .anomaly_models import (
    AnomalyType, AnomalySeverity, AnomalyStatus, DetectionMethod,
    AnomalyResult, AnomalyReport, AnomalyPattern, AnomalyMetrics,
    DetectionConfig, AnomalyThreshold, TimeSeriesPoint, BehaviorProfile
)


class AnomalyDetector:
    """
    异常检测器
    
    集成多种异常检测算法，提供全面的异常识别和分析能力。
    支持统计方法、机器学习算法和自定义规则。
    """
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        初始化异常检测器
        
        Args:
            config: 检测配置，如果为None则使用默认配置
        """
        self.config = config or DetectionConfig()
        self.logger = logging.getLogger(__name__)
        
        # 检测器组件
        self.patterns: Dict[str, AnomalyPattern] = {}
        self.thresholds: Dict[str, AnomalyThreshold] = {}
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        
        # 历史记录
        self.detection_history: List[AnomalyReport] = []
        self.anomaly_cache: Dict[str, AnomalyResult] = {}
        
        # 性能组件
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # 初始化默认模式和阈值
        self._initialize_default_patterns()
        self._initialize_default_thresholds()
        
        self.logger.info("异常检测器初始化完成")
    
    def _initialize_default_patterns(self):
        """初始化默认异常模式"""
        default_patterns = [
            # 预算异常模式
            AnomalyPattern(
                pattern_id="budget_spike",
                pattern_name="预算异常增长",
                pattern_type=AnomalyType.STATISTICAL,
                description="项目预算出现异常增长",
                indicators=["budget_amount", "budget_change_rate"],
                threshold_config={"z_score": 3.0, "percentage_change": 0.5},
                detection_method=DetectionMethod.Z_SCORE,
                severity_mapping={"high": AnomalySeverity.HIGH, "medium": AnomalySeverity.MEDIUM}
            ),
            
            # 时间异常模式
            AnomalyPattern(
                pattern_id="timeline_deviation",
                pattern_name="时间线偏差",
                pattern_type=AnomalyType.TEMPORAL,
                description="项目时间线出现异常偏差",
                indicators=["planned_duration", "actual_duration", "delay_days"],
                threshold_config={"delay_threshold": 30, "acceleration_threshold": -15},
                detection_method=DetectionMethod.CUSTOM_RULE,
                severity_mapping={"critical": AnomalySeverity.CRITICAL, "high": AnomalySeverity.HIGH}
            ),
            
            # 供应商行为异常
            AnomalyPattern(
                pattern_id="supplier_behavior",
                pattern_name="供应商行为异常",
                pattern_type=AnomalyType.BEHAVIORAL,
                description="供应商投标或履约行为异常",
                indicators=["bid_frequency", "win_rate", "performance_score"],
                threshold_config={"frequency_threshold": 10, "win_rate_threshold": 0.8},
                detection_method=DetectionMethod.ISOLATION_FOREST,
                severity_mapping={"high": AnomalySeverity.HIGH, "medium": AnomalySeverity.MEDIUM}
            ),
            
            # 价格异常模式
            AnomalyPattern(
                pattern_id="price_anomaly",
                pattern_name="价格异常",
                pattern_type=AnomalyType.OUTLIER,
                description="投标价格或采购价格异常",
                indicators=["bid_price", "market_price", "price_deviation"],
                threshold_config={"deviation_threshold": 0.3, "outlier_factor": 2.0},
                detection_method=DetectionMethod.IQR,
                severity_mapping={"critical": AnomalySeverity.CRITICAL, "high": AnomalySeverity.HIGH}
            )
        ]
        
        for pattern in default_patterns:
            self.patterns[pattern.pattern_id] = pattern
    
    def _initialize_default_thresholds(self):
        """初始化默认阈值"""
        default_thresholds = [
            AnomalyThreshold(
                field_name="budget_amount",
                threshold_type="upper",
                threshold_value=10000000,  # 1000万
                severity=AnomalySeverity.HIGH,
                description="预算金额超过1000万需要特别关注"
            ),
            AnomalyThreshold(
                field_name="delay_days",
                threshold_type="upper",
                threshold_value=60,
                severity=AnomalySeverity.CRITICAL,
                description="项目延期超过60天为严重异常"
            ),
            AnomalyThreshold(
                field_name="supplier_performance",
                threshold_type="lower",
                threshold_value=0.6,
                severity=AnomalySeverity.HIGH,
                description="供应商绩效低于60%需要关注"
            )
        ]
        
        for threshold in default_thresholds:
            self.thresholds[threshold.field_name] = threshold
    
    async def detect_anomalies(
        self,
        data: Union[Dict[str, Any], pd.DataFrame],
        project_id: str,
        detection_types: Optional[List[AnomalyType]] = None
    ) -> AnomalyReport:
        """
        执行异常检测
        
        Args:
            data: 要检测的数据
            project_id: 项目ID
            detection_types: 要执行的检测类型，如果为None则执行所有类型
            
        Returns:
            AnomalyReport: 异常检测报告
        """
        start_time = datetime.now()
        
        try:
            # 数据预处理
            processed_data = self._preprocess_data(data)
            
            # 执行不同类型的异常检测
            all_anomalies = []
            
            if not detection_types:
                detection_types = list(AnomalyType)
            
            # 并行执行不同类型的检测
            detection_tasks = []
            
            for anomaly_type in detection_types:
                task = self._detect_by_type(processed_data, anomaly_type, project_id)
                detection_tasks.append(task)
            
            # 等待所有检测任务完成
            detection_results = await asyncio.gather(*detection_tasks, return_exceptions=True)
            
            # 收集结果
            for result in detection_results:
                if isinstance(result, Exception):
                    self.logger.error(f"检测任务异常: {str(result)}")
                elif isinstance(result, list):
                    all_anomalies.extend(result)
            
            # 去重和排序
            unique_anomalies = self._deduplicate_anomalies(all_anomalies)
            sorted_anomalies = sorted(
                unique_anomalies,
                key=lambda x: (x.severity.value, -x.confidence_score)
            )
            
            # 限制异常数量
            if len(sorted_anomalies) > self.config.max_anomalies_per_check:
                sorted_anomalies = sorted_anomalies[:self.config.max_anomalies_per_check]
            
            # 生成报告
            report = self._generate_report(
                project_id, sorted_anomalies, start_time, processed_data
            )
            
            # 更新历史记录
            self.detection_history.append(report)
            
            # 更新行为画像
            await self._update_behavior_profiles(project_id, sorted_anomalies, processed_data)
            
            self.logger.info(
                f"异常检测完成: 项目{project_id}, 发现{len(sorted_anomalies)}个异常, "
                f"耗时{report.detection_duration.total_seconds():.2f}秒"
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            raise
    
    def _preprocess_data(self, data: Union[Dict[str, Any], pd.DataFrame]) -> pd.DataFrame:
        """
        数据预处理
        
        Args:
            data: 原始数据
            
        Returns:
            pd.DataFrame: 预处理后的数据
        """
        if isinstance(data, dict):
            # 将字典转换为DataFrame
            df = pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError(f"不支持的数据类型: {type(data)}")
        
        # 数据清洗
        # 处理缺失值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())
        
        # 处理无穷大值
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        
        # 数据类型转换
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        return df
    
    async def _detect_by_type(
        self,
        data: pd.DataFrame,
        anomaly_type: AnomalyType,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        按类型执行异常检测
        
        Args:
            data: 预处理后的数据
            anomaly_type: 异常类型
            project_id: 项目ID
            
        Returns:
            List[AnomalyResult]: 检测到的异常列表
        """
        anomalies = []
        
        try:
            if anomaly_type == AnomalyType.STATISTICAL:
                anomalies.extend(await self._detect_statistical_anomalies(data, project_id))
            
            elif anomaly_type == AnomalyType.BEHAVIORAL:
                anomalies.extend(await self._detect_behavioral_anomalies(data, project_id))
            
            elif anomaly_type == AnomalyType.TEMPORAL:
                anomalies.extend(await self._detect_temporal_anomalies(data, project_id))
            
            elif anomaly_type == AnomalyType.PATTERN:
                anomalies.extend(await self._detect_pattern_anomalies(data, project_id))
            
            elif anomaly_type == AnomalyType.OUTLIER:
                anomalies.extend(await self._detect_outliers(data, project_id))
            
            elif anomaly_type == AnomalyType.THRESHOLD:
                anomalies.extend(await self._detect_threshold_anomalies(data, project_id))
            
        except Exception as e:
            self.logger.error(f"检测类型{anomaly_type.value}时发生异常: {str(e)}")
        
        return anomalies
    
    async def _detect_statistical_anomalies(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        统计异常检测
        
        使用Z分数、IQR等统计方法检测异常
        """
        anomalies = []
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            values = data[column].dropna()
            if len(values) < 2:
                continue
            
            # Z分数检测
            z_scores = np.abs((values - values.mean()) / values.std())
            z_anomalies = values[z_scores > self.config.z_score_threshold]
            
            for idx, value in z_anomalies.items():
                anomaly = AnomalyResult(
                    anomaly_id=f"stat_z_{project_id}_{column}_{idx}",
                    anomaly_type=AnomalyType.STATISTICAL,
                    severity=self._calculate_severity_from_z_score(z_scores.iloc[idx]),
                    confidence_score=min(z_scores.iloc[idx] / 5.0, 1.0),
                    anomaly_score=z_scores.iloc[idx],
                    title=f"{column}字段Z分数异常",
                    description=f"{column}的值{value}的Z分数为{z_scores.iloc[idx]:.2f}，超过阈值{self.config.z_score_threshold}",
                    affected_fields=[column],
                    detection_method=DetectionMethod.Z_SCORE,
                    detection_time=datetime.now(),
                    original_value=value,
                    expected_value=values.mean(),
                    deviation=abs(value - values.mean()),
                    threshold_value=self.config.z_score_threshold
                )
                anomalies.append(anomaly)
            
            # IQR检测
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - self.config.iqr_multiplier * IQR
            upper_bound = Q3 + self.config.iqr_multiplier * IQR
            
            iqr_anomalies = values[(values < lower_bound) | (values > upper_bound)]
            
            for idx, value in iqr_anomalies.items():
                anomaly = AnomalyResult(
                    anomaly_id=f"stat_iqr_{project_id}_{column}_{idx}",
                    anomaly_type=AnomalyType.STATISTICAL,
                    severity=AnomalySeverity.MEDIUM,
                    confidence_score=0.8,
                    anomaly_score=abs(value - values.median()) / IQR if IQR > 0 else 0,
                    title=f"{column}字段IQR异常",
                    description=f"{column}的值{value}超出IQR范围[{lower_bound:.2f}, {upper_bound:.2f}]",
                    affected_fields=[column],
                    detection_method=DetectionMethod.IQR,
                    detection_time=datetime.now(),
                    original_value=value,
                    expected_value=values.median(),
                    deviation=abs(value - values.median()),
                    threshold_value=(lower_bound, upper_bound)
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_behavioral_anomalies(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        行为异常检测
        
        检测供应商、采购方等实体的异常行为模式
        """
        anomalies = []
        
        # 检查是否有供应商相关字段
        supplier_fields = [col for col in data.columns if 'supplier' in col.lower()]
        
        if supplier_fields:
            # 供应商行为分析
            for _, row in data.iterrows():
                supplier_id = row.get('supplier_id', 'unknown')
                
                # 获取或创建行为画像
                profile = self.behavior_profiles.get(
                    supplier_id,
                    BehaviorProfile(
                        entity_id=supplier_id,
                        entity_type='supplier',
                        profile_period=(datetime.now() - timedelta(days=90), datetime.now())
                    )
                )
                
                # 检查投标频率异常
                bid_frequency = row.get('bid_frequency', 0)
                if bid_frequency > 20:  # 异常高频投标
                    anomaly = AnomalyResult(
                        anomaly_id=f"behavior_freq_{project_id}_{supplier_id}",
                        anomaly_type=AnomalyType.BEHAVIORAL,
                        severity=AnomalySeverity.HIGH,
                        confidence_score=0.85,
                        anomaly_score=bid_frequency / 20.0,
                        title="供应商异常高频投标",
                        description=f"供应商{supplier_id}投标频率{bid_frequency}次异常偏高",
                        affected_fields=['bid_frequency'],
                        detection_method=DetectionMethod.CUSTOM_RULE,
                        detection_time=datetime.now(),
                        original_value=bid_frequency,
                        expected_value=10,
                        context_data={'supplier_id': supplier_id}
                    )
                    anomalies.append(anomaly)
                
                # 检查中标率异常
                win_rate = row.get('win_rate', 0)
                if win_rate > 0.8:  # 异常高中标率
                    anomaly = AnomalyResult(
                        anomaly_id=f"behavior_winrate_{project_id}_{supplier_id}",
                        anomaly_type=AnomalyType.BEHAVIORAL,
                        severity=AnomalySeverity.HIGH,
                        confidence_score=0.9,
                        anomaly_score=win_rate,
                        title="供应商异常高中标率",
                        description=f"供应商{supplier_id}中标率{win_rate:.1%}异常偏高，可能存在不当竞争",
                        affected_fields=['win_rate'],
                        detection_method=DetectionMethod.CUSTOM_RULE,
                        detection_time=datetime.now(),
                        original_value=win_rate,
                        expected_value=0.3,
                        context_data={'supplier_id': supplier_id}
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_temporal_anomalies(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        时间异常检测
        
        检测项目时间线、季节性等时间相关异常
        """
        anomalies = []
        
        # 检查时间相关字段
        time_fields = [col for col in data.columns if any(keyword in col.lower() 
                      for keyword in ['time', 'date', 'duration', 'delay'])]
        
        for _, row in data.iterrows():
            # 检查项目延期
            if 'delay_days' in row:
                delay_days = row['delay_days']
                if delay_days > 30:  # 延期超过30天
                    severity = AnomalySeverity.CRITICAL if delay_days > 90 else AnomalySeverity.HIGH
                    anomaly = AnomalyResult(
                        anomaly_id=f"temporal_delay_{project_id}",
                        anomaly_type=AnomalyType.TEMPORAL,
                        severity=severity,
                        confidence_score=0.95,
                        anomaly_score=delay_days / 30.0,
                        title="项目严重延期",
                        description=f"项目延期{delay_days}天，超出正常范围",
                        affected_fields=['delay_days'],
                        detection_method=DetectionMethod.CUSTOM_RULE,
                        detection_time=datetime.now(),
                        original_value=delay_days,
                        expected_value=0,
                        threshold_value=30
                    )
                    anomalies.append(anomaly)
            
            # 检查执行时间异常
            if 'planned_duration' in row and 'actual_duration' in row:
                planned = row['planned_duration']
                actual = row['actual_duration']
                if planned > 0:
                    deviation_ratio = abs(actual - planned) / planned
                    if deviation_ratio > 0.5:  # 偏差超过50%
                        anomaly = AnomalyResult(
                            anomaly_id=f"temporal_duration_{project_id}",
                            anomaly_type=AnomalyType.TEMPORAL,
                            severity=AnomalySeverity.MEDIUM,
                            confidence_score=0.8,
                            anomaly_score=deviation_ratio,
                            title="项目执行时间异常",
                            description=f"实际执行时间{actual}与计划时间{planned}偏差{deviation_ratio:.1%}",
                            affected_fields=['planned_duration', 'actual_duration'],
                            detection_method=DetectionMethod.CUSTOM_RULE,
                            detection_time=datetime.now(),
                            original_value=actual,
                            expected_value=planned,
                            deviation=abs(actual - planned)
                        )
                        anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_pattern_anomalies(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        模式异常检测
        
        使用预定义的异常模式进行检测
        """
        anomalies = []
        
        for pattern_id, pattern in self.patterns.items():
            if not pattern.enabled:
                continue
            
            try:
                # 检查模式所需的指标是否存在
                available_indicators = [ind for ind in pattern.indicators if ind in data.columns]
                if len(available_indicators) < len(pattern.indicators) * 0.5:  # 至少50%的指标可用
                    continue
                
                # 根据检测方法执行模式检测
                pattern_anomalies = await self._apply_pattern_detection(
                    data, pattern, project_id, available_indicators
                )
                anomalies.extend(pattern_anomalies)
                
            except Exception as e:
                self.logger.error(f"模式{pattern_id}检测失败: {str(e)}")
        
        return anomalies
    
    async def _apply_pattern_detection(
        self,
        data: pd.DataFrame,
        pattern: AnomalyPattern,
        project_id: str,
        indicators: List[str]
    ) -> List[AnomalyResult]:
        """
        应用特定模式进行检测
        """
        anomalies = []
        
        if pattern.detection_method == DetectionMethod.Z_SCORE:
            # 使用Z分数方法
            for indicator in indicators:
                if indicator in data.columns:
                    values = data[indicator].dropna()
                    if len(values) > 1:
                        z_scores = np.abs((values - values.mean()) / values.std())
                        threshold = pattern.threshold_config.get('z_score', 3.0)
                        
                        anomalous_indices = z_scores[z_scores > threshold].index
                        for idx in anomalous_indices:
                            anomaly = AnomalyResult(
                                anomaly_id=f"pattern_{pattern.pattern_id}_{project_id}_{indicator}_{idx}",
                                anomaly_type=pattern.pattern_type,
                                severity=AnomalySeverity.MEDIUM,
                                confidence_score=min(z_scores.iloc[idx] / 5.0, 1.0),
                                anomaly_score=z_scores.iloc[idx],
                                title=f"{pattern.pattern_name} - {indicator}",
                                description=f"在{indicator}字段检测到{pattern.description}",
                                affected_fields=[indicator],
                                detection_method=pattern.detection_method,
                                detection_time=datetime.now(),
                                original_value=values.iloc[idx],
                                expected_value=values.mean()
                            )
                            anomalies.append(anomaly)
        
        elif pattern.detection_method == DetectionMethod.CUSTOM_RULE:
            # 自定义规则检测
            anomalies.extend(await self._apply_custom_rule_detection(
                data, pattern, project_id, indicators
            ))
        
        return anomalies
    
    async def _apply_custom_rule_detection(
        self,
        data: pd.DataFrame,
        pattern: AnomalyPattern,
        project_id: str,
        indicators: List[str]
    ) -> List[AnomalyResult]:
        """
        应用自定义规则检测
        """
        anomalies = []
        
        # 根据模式ID应用特定规则
        if pattern.pattern_id == "budget_spike":
            # 预算异常增长检测
            if 'budget_change_rate' in data.columns:
                for idx, row in data.iterrows():
                    change_rate = row.get('budget_change_rate', 0)
                    threshold = pattern.threshold_config.get('percentage_change', 0.5)
                    
                    if abs(change_rate) > threshold:
                        severity = AnomalySeverity.HIGH if abs(change_rate) > 1.0 else AnomalySeverity.MEDIUM
                        anomaly = AnomalyResult(
                            anomaly_id=f"budget_spike_{project_id}_{idx}",
                            anomaly_type=AnomalyType.PATTERN,
                            severity=severity,
                            confidence_score=0.9,
                            anomaly_score=abs(change_rate),
                            title="预算异常变化",
                            description=f"预算变化率{change_rate:.1%}超过阈值{threshold:.1%}",
                            affected_fields=['budget_change_rate'],
                            detection_method=DetectionMethod.CUSTOM_RULE,
                            detection_time=datetime.now(),
                            original_value=change_rate,
                            threshold_value=threshold
                        )
                        anomalies.append(anomaly)
        
        elif pattern.pattern_id == "timeline_deviation":
            # 时间线偏差检测
            if 'delay_days' in data.columns:
                for idx, row in data.iterrows():
                    delay_days = row.get('delay_days', 0)
                    delay_threshold = pattern.threshold_config.get('delay_threshold', 30)
                    acceleration_threshold = pattern.threshold_config.get('acceleration_threshold', -15)
                    
                    if delay_days > delay_threshold:
                        anomaly = AnomalyResult(
                            anomaly_id=f"timeline_delay_{project_id}_{idx}",
                            anomaly_type=AnomalyType.PATTERN,
                            severity=AnomalySeverity.CRITICAL if delay_days > 60 else AnomalySeverity.HIGH,
                            confidence_score=0.95,
                            anomaly_score=delay_days / delay_threshold,
                            title="项目严重延期",
                            description=f"项目延期{delay_days}天，超过阈值{delay_threshold}天",
                            affected_fields=['delay_days'],
                            detection_method=DetectionMethod.CUSTOM_RULE,
                            detection_time=datetime.now(),
                            original_value=delay_days,
                            threshold_value=delay_threshold
                        )
                        anomalies.append(anomaly)
                    
                    elif delay_days < acceleration_threshold:
                        anomaly = AnomalyResult(
                            anomaly_id=f"timeline_acceleration_{project_id}_{idx}",
                            anomaly_type=AnomalyType.PATTERN,
                            severity=AnomalySeverity.MEDIUM,
                            confidence_score=0.8,
                            anomaly_score=abs(delay_days / acceleration_threshold),
                            title="项目异常提前",
                            description=f"项目提前{abs(delay_days)}天完成，可能存在质量风险",
                            affected_fields=['delay_days'],
                            detection_method=DetectionMethod.CUSTOM_RULE,
                            detection_time=datetime.now(),
                            original_value=delay_days,
                            threshold_value=acceleration_threshold
                        )
                        anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_outliers(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        离群值检测
        
        使用机器学习算法检测离群值
        """
        anomalies = []
        
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn不可用，跳过机器学习离群值检测")
            return anomalies
        
        # 获取数值列
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty or len(numeric_data) < 2:
            return anomalies
        
        try:
            # 数据标准化
            scaled_data = self.scaler.fit_transform(numeric_data.fillna(0))
            
            # 孤立森林检测
            iso_forest = IsolationForest(
                contamination=self.config.contamination_rate,
                random_state=self.config.random_state,
                n_estimators=self.config.n_estimators
            )
            outlier_labels = iso_forest.fit_predict(scaled_data)
            outlier_scores = iso_forest.score_samples(scaled_data)
            
            # 生成异常结果
            for idx, (label, score) in enumerate(zip(outlier_labels, outlier_scores)):
                if label == -1:  # 离群值
                    anomaly = AnomalyResult(
                        anomaly_id=f"outlier_isolation_{project_id}_{idx}",
                        anomaly_type=AnomalyType.OUTLIER,
                        severity=self._calculate_severity_from_score(-score),
                        confidence_score=min(abs(score) * 2, 1.0),
                        anomaly_score=-score,
                        title="数据离群值",
                        description=f"第{idx}行数据被识别为离群值，异常分数{-score:.3f}",
                        affected_fields=list(numeric_data.columns),
                        detection_method=DetectionMethod.ISOLATION_FOREST,
                        detection_time=datetime.now(),
                        metadata={'isolation_score': score, 'row_index': idx}
                    )
                    anomalies.append(anomaly)
            
            # 局部离群因子检测
            if len(scaled_data) >= 20:  # LOF需要足够的样本
                lof = LocalOutlierFactor(
                    n_neighbors=min(20, len(scaled_data) - 1),
                    contamination=self.config.contamination_rate
                )
                lof_labels = lof.fit_predict(scaled_data)
                lof_scores = lof.negative_outlier_factor_
                
                for idx, (label, score) in enumerate(zip(lof_labels, lof_scores)):
                    if label == -1:  # 离群值
                        anomaly = AnomalyResult(
                            anomaly_id=f"outlier_lof_{project_id}_{idx}",
                            anomaly_type=AnomalyType.OUTLIER,
                            severity=self._calculate_severity_from_score(-score),
                            confidence_score=min(abs(score), 1.0),
                            anomaly_score=-score,
                            title="局部离群值",
                            description=f"第{idx}行数据被识别为局部离群值，LOF分数{score:.3f}",
                            affected_fields=list(numeric_data.columns),
                            detection_method=DetectionMethod.LOCAL_OUTLIER_FACTOR,
                            detection_time=datetime.now(),
                            metadata={'lof_score': score, 'row_index': idx}
                        )
                        anomalies.append(anomaly)
        
        except Exception as e:
            self.logger.error(f"机器学习离群值检测失败: {str(e)}")
        
        return anomalies
    
    async def _detect_threshold_anomalies(
        self,
        data: pd.DataFrame,
        project_id: str
    ) -> List[AnomalyResult]:
        """
        阈值异常检测
        
        基于预定义阈值检测异常
        """
        anomalies = []
        
        for field_name, threshold in self.thresholds.items():
            if not threshold.enabled or field_name not in data.columns:
                continue
            
            for idx, row in data.iterrows():
                value = row.get(field_name)
                if value is None:
                    continue
                
                if threshold.check_threshold(value):
                    anomaly = AnomalyResult(
                        anomaly_id=f"threshold_{field_name}_{project_id}_{idx}",
                        anomaly_type=AnomalyType.THRESHOLD,
                        severity=threshold.severity,
                        confidence_score=0.9,
                        anomaly_score=self._calculate_threshold_score(value, threshold),
                        title=f"{field_name}阈值异常",
                        description=f"{field_name}的值{value}超过阈值{threshold.threshold_value}。{threshold.description}",
                        affected_fields=[field_name],
                        detection_method=DetectionMethod.CUSTOM_RULE,
                        detection_time=datetime.now(),
                        original_value=value,
                        threshold_value=threshold.threshold_value
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_severity_from_z_score(self, z_score: float) -> AnomalySeverity:
        """根据Z分数计算严重程度"""
        if z_score >= 5.0:
            return AnomalySeverity.CRITICAL
        elif z_score >= 4.0:
            return AnomalySeverity.HIGH
        elif z_score >= 3.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_severity_from_score(self, score: float) -> AnomalySeverity:
        """根据异常分数计算严重程度"""
        if score >= 0.8:
            return AnomalySeverity.CRITICAL
        elif score >= 0.6:
            return AnomalySeverity.HIGH
        elif score >= 0.4:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_threshold_score(self, value: float, threshold: AnomalyThreshold) -> float:
        """计算阈值异常分数"""
        if threshold.threshold_type == "upper":
            return max(0, (value - threshold.threshold_value) / threshold.threshold_value)
        elif threshold.threshold_type == "lower":
            return max(0, (threshold.threshold_value - value) / threshold.threshold_value)
        elif threshold.threshold_type == "range":
            min_val, max_val = threshold.threshold_value
            if value < min_val:
                return (min_val - value) / (max_val - min_val)
            elif value > max_val:
                return (value - max_val) / (max_val - min_val)
        return 0.0
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """去除重复异常"""
        seen = set()
        unique_anomalies = []
        
        for anomaly in anomalies:
            # 创建唯一标识
            key = f"{anomaly.anomaly_type.value}_{','.join(anomaly.affected_fields)}_{anomaly.original_value}"
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(anomaly)
        
        return unique_anomalies
    
    def _generate_report(
        self,
        project_id: str,
        anomalies: List[AnomalyResult],
        start_time: datetime,
        data: pd.DataFrame
    ) -> AnomalyReport:
        """生成异常检测报告"""
        end_time = datetime.now()
        
        # 计算指标
        metrics = AnomalyMetrics(
            total_anomalies=len(anomalies),
            critical_anomalies=sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL),
            high_anomalies=sum(1 for a in anomalies if a.severity == AnomalySeverity.HIGH),
            medium_anomalies=sum(1 for a in anomalies if a.severity == AnomalySeverity.MEDIUM),
            low_anomalies=sum(1 for a in anomalies if a.severity == AnomalySeverity.LOW),
            info_anomalies=sum(1 for a in anomalies if a.severity == AnomalySeverity.INFO),
            statistical_anomalies=sum(1 for a in anomalies if a.anomaly_type == AnomalyType.STATISTICAL),
            behavioral_anomalies=sum(1 for a in anomalies if a.anomaly_type == AnomalyType.BEHAVIORAL),
            temporal_anomalies=sum(1 for a in anomalies if a.anomaly_type == AnomalyType.TEMPORAL),
            pattern_anomalies=sum(1 for a in anomalies if a.anomaly_type == AnomalyType.PATTERN),
            outlier_anomalies=sum(1 for a in anomalies if a.anomaly_type == AnomalyType.OUTLIER),
            average_confidence=sum(a.confidence_score for a in anomalies) / len(anomalies) if anomalies else 0.0,
            average_anomaly_score=sum(a.anomaly_score for a in anomalies) / len(anomalies) if anomalies else 0.0,
            detection_time_seconds=(end_time - start_time).total_seconds(),
            data_points_analyzed=len(data)
        )
        
        # 确定整体风险等级
        if metrics.critical_anomalies > 0:
            overall_risk_level = "极高风险"
        elif metrics.high_anomalies > 0:
            overall_risk_level = "高风险"
        elif metrics.medium_anomalies > 0:
            overall_risk_level = "中等风险"
        elif metrics.low_anomalies > 0:
            overall_risk_level = "低风险"
        else:
            overall_risk_level = "正常"
        
        # 生成关键发现
        key_findings = self._generate_key_findings(anomalies, metrics)
        
        # 生成建议
        recommendations = self._generate_recommendations(anomalies, metrics)
        
        return AnomalyReport(
            report_id=f"anomaly_{start_time.strftime('%Y%m%d_%H%M%S')}_{project_id}",
            project_id=project_id,
            detection_time=start_time,
            detection_duration=end_time - start_time,
            anomalies=anomalies,
            metrics=metrics,
            detection_config=self.config,
            patterns_used=list(self.patterns.values()),
            data_source="project_data",
            data_time_range=(start_time, end_time),
            overall_risk_level=overall_risk_level,
            key_findings=key_findings,
            recommendations=recommendations,
            metadata={
                "detector_version": "1.0.0",
                "sklearn_available": SKLEARN_AVAILABLE,
                "patterns_count": len(self.patterns),
                "thresholds_count": len(self.thresholds)
            }
        )
    
    def _generate_key_findings(self, anomalies: List[AnomalyResult], metrics: AnomalyMetrics) -> List[str]:
        """生成关键发现"""
        findings = []
        
        if metrics.critical_anomalies > 0:
            findings.append(f"发现{metrics.critical_anomalies}个严重异常，需要立即处理")
        
        if metrics.high_anomalies > 0:
            findings.append(f"发现{metrics.high_anomalies}个高风险异常，建议优先关注")
        
        # 分析异常类型分布
        type_counts = metrics.get_type_distribution()
        max_type = max(type_counts.items(), key=lambda x: x[1])
        if max_type[1] > 0:
            findings.append(f"主要异常类型为{max_type[0]}异常，共{max_type[1]}个")
        
        # 分析置信度
        if metrics.average_confidence > 0.8:
            findings.append(f"异常检测平均置信度{metrics.average_confidence:.1%}，结果可信度较高")
        elif metrics.average_confidence < 0.6:
            findings.append(f"异常检测平均置信度{metrics.average_confidence:.1%}，建议进一步验证")
        
        return findings
    
    def _generate_recommendations(self, anomalies: List[AnomalyResult], metrics: AnomalyMetrics) -> List[str]:
        """生成建议措施"""
        recommendations = []
        
        if metrics.critical_anomalies > 0:
            recommendations.append("🚨 立即调查和处理所有严重异常，暂停相关项目进展")
        
        if metrics.high_anomalies > 0:
            recommendations.append("⚠️ 优先处理高风险异常，制定应对措施")
        
        if metrics.behavioral_anomalies > 0:
            recommendations.append("👥 加强对相关供应商和参与方的监督和审查")
        
        if metrics.temporal_anomalies > 0:
            recommendations.append("⏰ 重新评估项目时间安排，调整进度计划")
        
        if metrics.outlier_anomalies > 0:
            recommendations.append("📊 深入分析数据异常原因，检查数据质量")
        
        # 通用建议
        recommendations.extend([
            "📋 建立异常监控机制，定期进行异常检测",
            "📚 完善异常处理流程和应急预案",
            "🔄 持续优化检测算法和阈值设置"
        ])
        
        return recommendations
    
    async def _update_behavior_profiles(
        self,
        project_id: str,
        anomalies: List[AnomalyResult],
        data: pd.DataFrame
    ):
        """更新行为画像"""
        try:
            # 提取实体信息
            entities = set()
            
            # 从数据中提取供应商ID
            if 'supplier_id' in data.columns:
                entities.update(data['supplier_id'].dropna().unique())
            
            # 从异常中提取相关实体
            for anomaly in anomalies:
                if 'supplier_id' in anomaly.context_data:
                    entities.add(anomaly.context_data['supplier_id'])
            
            # 更新每个实体的行为画像
            for entity_id in entities:
                if entity_id not in self.behavior_profiles:
                    self.behavior_profiles[entity_id] = BehaviorProfile(
                        entity_id=str(entity_id),
                        entity_type='supplier',
                        profile_period=(datetime.now() - timedelta(days=90), datetime.now())
                    )
                
                profile = self.behavior_profiles[entity_id]
                
                # 更新异常历史
                entity_anomalies = [
                    a for a in anomalies 
                    if a.context_data.get('supplier_id') == entity_id
                ]
                
                if entity_anomalies:
                    profile.update_risk_score(entity_anomalies)
                    profile.anomaly_history.extend([a.anomaly_id for a in entity_anomalies])
        
        except Exception as e:
            self.logger.error(f"更新行为画像失败: {str(e)}")
    
    def add_pattern(self, pattern: AnomalyPattern):
        """添加异常模式"""
        self.patterns[pattern.pattern_id] = pattern
        self.logger.info(f"添加异常模式: {pattern.pattern_name}")
    
    def add_threshold(self, threshold: AnomalyThreshold):
        """添加阈值配置"""
        self.thresholds[threshold.field_name] = threshold
        self.logger.info(f"添加阈值配置: {threshold.field_name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "total_detections": len(self.detection_history),
            "total_patterns": len(self.patterns),
            "total_thresholds": len(self.thresholds),
            "behavior_profiles": len(self.behavior_profiles),
            "cache_size": len(self.anomaly_cache),
            "sklearn_available": SKLEARN_AVAILABLE,
            "average_detection_time": sum(
                report.detection_duration.total_seconds() 
                for report in self.detection_history
            ) / len(self.detection_history) if self.detection_history else 0
        }