#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规检查引擎
政府采购项目合规性检查的核心引擎

主要功能:
- 执行合规规则检查
- 生成合规报告
- 提供整改建议
- 合规历史跟踪

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .compliance_models import (
    ComplianceStatus, ViolationSeverity, RuleCategory,
    ComplianceViolation, ComplianceResult, ComplianceReport,
    ComplianceMetrics, DocumentCheckResult
)
from .compliance_rules import ComplianceRule, ComplianceRuleSet


class CheckMode(Enum):
    """检查模式"""
    FULL = "full"  # 全面检查
    QUICK = "quick"  # 快速检查
    TARGETED = "targeted"  # 针对性检查
    INCREMENTAL = "incremental"  # 增量检查


class ComplianceEngine:
    """
    合规检查引擎
    
    负责执行政府采购项目的合规性检查，
    包括规则执行、结果汇总、报告生成等功能。
    """
    
    def __init__(self, rule_set: Optional[ComplianceRuleSet] = None):
        """
        初始化合规检查引擎
        
        Args:
            rule_set: 合规规则集，如果为None则使用默认规则集
        """
        self.rule_set = rule_set or ComplianceRuleSet()
        self.logger = logging.getLogger(__name__)
        self.check_history: List[ComplianceReport] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 性能配置
        self.max_parallel_checks = 10
        self.check_timeout = 30  # 秒
        self.cache_enabled = True
        self.cache_ttl = 300  # 5分钟
        self._cache: Dict[str, Tuple[datetime, ComplianceResult]] = {}
    
    async def check_compliance(
        self,
        project_data: Dict[str, Any],
        mode: CheckMode = CheckMode.FULL,
        categories: Optional[List[RuleCategory]] = None,
        rule_ids: Optional[List[str]] = None
    ) -> ComplianceReport:
        """
        执行合规性检查
        
        Args:
            project_data: 项目数据
            mode: 检查模式
            categories: 要检查的规则类别
            rule_ids: 要检查的具体规则ID
            
        Returns:
            ComplianceReport: 合规检查报告
        """
        start_time = datetime.now()
        
        try:
            # 获取要检查的规则
            rules_to_check = self._get_rules_to_check(mode, categories, rule_ids)
            
            # 执行检查
            check_results = await self._execute_checks(project_data, rules_to_check)
            
            # 生成报告
            report = self._generate_report(
                project_data, check_results, start_time, mode
            )
            
            # 保存到历史记录
            self.check_history.append(report)
            
            self.logger.info(
                f"合规检查完成: {report.overall_status.value}, "
                f"检查了{len(check_results)}条规则, "
                f"耗时{report.check_duration.total_seconds():.2f}秒"
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"合规检查失败: {str(e)}")
            raise
    
    def _get_rules_to_check(
        self,
        mode: CheckMode,
        categories: Optional[List[RuleCategory]] = None,
        rule_ids: Optional[List[str]] = None
    ) -> List[ComplianceRule]:
        """
        获取要检查的规则列表
        
        Args:
            mode: 检查模式
            categories: 规则类别
            rule_ids: 规则ID列表
            
        Returns:
            List[ComplianceRule]: 规则列表
        """
        if rule_ids:
            # 检查指定规则
            return [self.rule_set.get_rule(rule_id) for rule_id in rule_ids 
                   if self.rule_set.get_rule(rule_id)]
        
        if categories:
            # 检查指定类别
            rules = []
            for category in categories:
                rules.extend(self.rule_set.get_rules_by_category(category))
            return rules
        
        # 根据模式选择规则
        all_rules = self.rule_set.get_enabled_rules()
        
        if mode == CheckMode.QUICK:
            # 快速检查：只检查高优先级规则
            return [rule for rule in all_rules 
                   if rule.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]]
        
        elif mode == CheckMode.TARGETED:
            # 针对性检查：根据项目特点选择规则
            # 这里可以根据项目数据智能选择规则
            return all_rules[:10]  # 简化实现
        
        else:
            # 全面检查
            return all_rules
    
    async def _execute_checks(
        self,
        project_data: Dict[str, Any],
        rules: List[ComplianceRule]
    ) -> List[ComplianceResult]:
        """
        执行合规检查
        
        Args:
            project_data: 项目数据
            rules: 要检查的规则列表
            
        Returns:
            List[ComplianceResult]: 检查结果列表
        """
        results = []
        
        # 分批并行执行检查
        for i in range(0, len(rules), self.max_parallel_checks):
            batch = rules[i:i + self.max_parallel_checks]
            batch_results = await asyncio.gather(
                *[self._check_single_rule(project_data, rule) for rule in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"规则检查异常: {str(result)}")
                else:
                    results.append(result)
        
        return results
    
    async def _check_single_rule(
        self,
        project_data: Dict[str, Any],
        rule: ComplianceRule
    ) -> ComplianceResult:
        """
        检查单个规则
        
        Args:
            project_data: 项目数据
            rule: 合规规则
            
        Returns:
            ComplianceResult: 检查结果
        """
        # 检查缓存
        cache_key = f"{rule.rule_id}_{hash(str(project_data))}"
        if self.cache_enabled and cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                return cached_result
        
        start_time = datetime.now()
        
        try:
            # 执行规则检查
            loop = asyncio.get_event_loop()
            is_compliant = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    rule.check,
                    project_data
                ),
                timeout=self.check_timeout
            )
            
            check_duration = datetime.now() - start_time
            
            # 创建检查结果
            result = ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                status=ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT,
                violations=[] if is_compliant else [
                    ComplianceViolation(
                        rule_id=rule.rule_id,
                        description=rule.error_message,
                        severity=rule.severity,
                        recommendation=rule.recommendation,
                        legal_reference=rule.legal_reference
                    )
                ],
                check_time=start_time,
                check_duration=check_duration,
                confidence_score=0.95,  # 可以根据规则复杂度调整
                metadata={
                    "rule_version": "1.0",
                    "check_method": "automated",
                    "data_quality": "high"
                }
            )
            
            # 缓存结果
            if self.cache_enabled:
                self._cache[cache_key] = (datetime.now(), result)
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"规则检查超时: {rule.rule_id}")
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                status=ComplianceStatus.ERROR,
                violations=[],
                check_time=start_time,
                check_duration=datetime.now() - start_time,
                confidence_score=0.0,
                metadata={"error": "检查超时"}
            )
        
        except Exception as e:
            self.logger.error(f"规则检查失败 {rule.rule_id}: {str(e)}")
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                status=ComplianceStatus.ERROR,
                violations=[],
                check_time=start_time,
                check_duration=datetime.now() - start_time,
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _generate_report(
        self,
        project_data: Dict[str, Any],
        check_results: List[ComplianceResult],
        start_time: datetime,
        mode: CheckMode
    ) -> ComplianceReport:
        """
        生成合规检查报告
        
        Args:
            project_data: 项目数据
            check_results: 检查结果列表
            start_time: 检查开始时间
            mode: 检查模式
            
        Returns:
            ComplianceReport: 合规报告
        """
        end_time = datetime.now()
        
        # 统计结果
        total_rules = len(check_results)
        compliant_count = sum(1 for r in check_results if r.status == ComplianceStatus.COMPLIANT)
        non_compliant_count = sum(1 for r in check_results if r.status == ComplianceStatus.NON_COMPLIANT)
        error_count = sum(1 for r in check_results if r.status == ComplianceStatus.ERROR)
        
        # 收集所有违规
        all_violations = []
        for result in check_results:
            all_violations.extend(result.violations)
        
        # 确定总体状态
        if error_count > total_rules * 0.1:  # 超过10%的规则检查失败
            overall_status = ComplianceStatus.ERROR
        elif non_compliant_count == 0:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT
        
        # 计算合规分数
        compliance_score = compliant_count / max(total_rules - error_count, 1) if total_rules > 0 else 0.0
        
        # 生成指标
        metrics = ComplianceMetrics(
            total_rules_checked=total_rules,
            compliant_rules=compliant_count,
            non_compliant_rules=non_compliant_count,
            error_rules=error_count,
            compliance_score=compliance_score,
            critical_violations=sum(1 for v in all_violations if v.severity == ViolationSeverity.CRITICAL),
            high_violations=sum(1 for v in all_violations if v.severity == ViolationSeverity.HIGH),
            medium_violations=sum(1 for v in all_violations if v.severity == ViolationSeverity.MEDIUM),
            low_violations=sum(1 for v in all_violations if v.severity == ViolationSeverity.LOW),
            categories_checked=list(set(r.category for r in check_results)),
            average_confidence=sum(r.confidence_score for r in check_results) / len(check_results) if check_results else 0.0
        )
        
        return ComplianceReport(
            report_id=f"compliance_{start_time.strftime('%Y%m%d_%H%M%S')}",
            project_id=project_data.get('project_id', 'unknown'),
            check_time=start_time,
            check_duration=end_time - start_time,
            overall_status=overall_status,
            compliance_score=compliance_score,
            results=check_results,
            violations=all_violations,
            metrics=metrics,
            recommendations=self._generate_recommendations(all_violations),
            metadata={
                "check_mode": mode.value,
                "engine_version": "1.0.0",
                "total_rules_available": len(self.rule_set.get_all_rules()),
                "cache_hits": sum(1 for key in self._cache.keys() if key.startswith("compliance_")),
                "project_type": project_data.get('project_type', 'unknown')
            }
        )
    
    def _generate_recommendations(self, violations: List[ComplianceViolation]) -> List[str]:
        """
        生成整改建议
        
        Args:
            violations: 违规列表
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 按严重程度分组
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        high_violations = [v for v in violations if v.severity == ViolationSeverity.HIGH]
        
        if critical_violations:
            recommendations.append("🚨 紧急处理严重违规问题，这些问题可能导致项目无法通过审核")
            for violation in critical_violations[:3]:  # 只显示前3个
                recommendations.append(f"  • {violation.recommendation}")
        
        if high_violations:
            recommendations.append("⚠️ 优先处理高风险违规问题")
            for violation in high_violations[:3]:  # 只显示前3个
                recommendations.append(f"  • {violation.recommendation}")
        
        # 通用建议
        if violations:
            recommendations.extend([
                "📋 建议建立合规检查清单，定期进行自查",
                "📚 加强团队对政府采购法规的培训",
                "🔄 建立合规问题跟踪和整改机制"
            ])
        else:
            recommendations.append("✅ 项目合规性良好，建议继续保持")
        
        return recommendations
    
    def get_compliance_trend(
        self,
        project_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取合规趋势分析
        
        Args:
            project_id: 项目ID
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 筛选相关报告
        relevant_reports = [
            report for report in self.check_history
            if report.project_id == project_id and report.check_time >= cutoff_date
        ]
        
        if not relevant_reports:
            return {"message": "没有足够的历史数据进行趋势分析"}
        
        # 计算趋势
        scores = [report.compliance_score for report in relevant_reports]
        dates = [report.check_time for report in relevant_reports]
        
        return {
            "project_id": project_id,
            "analysis_period": f"{days}天",
            "total_checks": len(relevant_reports),
            "latest_score": scores[-1] if scores else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_trend": "上升" if len(scores) > 1 and scores[-1] > scores[0] else "下降" if len(scores) > 1 else "稳定",
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "improvement_needed": any(report.overall_status == ComplianceStatus.NON_COMPLIANT for report in relevant_reports[-3:])
        }
    
    def export_report(
        self,
        report: ComplianceReport,
        format_type: str = "json"
    ) -> str:
        """
        导出合规报告
        
        Args:
            report: 合规报告
            format_type: 导出格式 (json, csv, html)
            
        Returns:
            str: 导出的报告内容
        """
        if format_type == "json":
            return json.dumps(report.__dict__, default=str, indent=2, ensure_ascii=False)
        
        elif format_type == "csv":
            # 简化的CSV导出
            lines = [
                "规则ID,规则名称,类别,状态,违规数量,置信度",
            ]
            for result in report.results:
                lines.append(
                    f"{result.rule_id},{result.rule_name},{result.category.value},"
                    f"{result.status.value},{len(result.violations)},{result.confidence_score}"
                )
            return "\n".join(lines)
        
        elif format_type == "html":
            # 简化的HTML报告
            html = f"""
            <html>
            <head><title>合规检查报告 - {report.report_id}</title></head>
            <body>
                <h1>合规检查报告</h1>
                <p>项目ID: {report.project_id}</p>
                <p>检查时间: {report.check_time}</p>
                <p>总体状态: {report.overall_status.value}</p>
                <p>合规分数: {report.compliance_score:.2%}</p>
                <h2>检查结果</h2>
                <ul>
            """
            for result in report.results:
                html += f"<li>{result.rule_name}: {result.status.value}</li>"
            html += "</ul></body></html>"
            return html
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.logger.info("合规检查缓存已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "total_rules": len(self.rule_set.get_all_rules()),
            "enabled_rules": len(self.rule_set.get_enabled_rules()),
            "total_checks_performed": len(self.check_history),
            "cache_size": len(self._cache),
            "average_check_duration": sum(
                report.check_duration.total_seconds() for report in self.check_history
            ) / len(self.check_history) if self.check_history else 0,
            "success_rate": sum(
                1 for report in self.check_history 
                if report.overall_status != ComplianceStatus.ERROR
            ) / len(self.check_history) if self.check_history else 0
        }