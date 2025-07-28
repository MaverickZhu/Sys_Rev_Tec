#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报告生成器
政府采购项目智能报告生成的核心引擎

主要功能:
- 基于模板生成结构化报告
- 集成分析结果和数据可视化
- 支持多种报告格式导出
- 自动化报告内容生成
- 报告质量评估和优化

作者: AI开发团队
创建时间: 2025-07-28
版本: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
from jinja2 import Environment, FileSystemLoader, Template
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from .report_models import (
    ReportRequest, ReportResult, ReportMetadata, ReportSection,
    ReportChart, ReportTemplate, ChartConfig, ReportStatus,
    ReportFormat, TemplateType, ChartType, ReportPriority
)
from ..risk_assessment.risk_models import RiskLevel, RiskCategory
from ..compliance_check.compliance_models import ComplianceStatus, ViolationSeverity
from ..anomaly_detection.anomaly_models import AnomalyType, AnomalySeverity

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    智能报告生成器
    
    负责根据分析结果生成结构化的审查报告，支持多种格式和模板。
    """
    
    def __init__(self, template_dir: str = "templates"):
        """
        初始化报告生成器
        
        Args:
            template_dir: 报告模板目录路径
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
        
        # 初始化Jinja2模板环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # 初始化默认模板
        self._init_default_templates()
        
        # 配置图表样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        logger.info("报告生成器初始化完成")
    
    def _init_default_templates(self):
        """初始化默认报告模板"""
        self.default_templates = {
            TemplateType.RISK_ASSESSMENT: self._create_risk_template(),
            TemplateType.COMPLIANCE_CHECK: self._create_compliance_template(),
            TemplateType.ANOMALY_DETECTION: self._create_anomaly_template(),
            TemplateType.COMPREHENSIVE: self._create_comprehensive_template(),
            TemplateType.EXECUTIVE_SUMMARY: self._create_executive_template()
        }
    
    async def generate_report(self, request: ReportRequest) -> ReportResult:
        """
        生成报告
        
        Args:
            request: 报告生成请求
            
        Returns:
            ReportResult: 报告生成结果
        """
        try:
            logger.info(f"开始生成报告: {request.title}")
            
            # 创建报告元数据
            metadata = ReportMetadata(
                report_id=f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=request.title,
                template_type=request.template_type,
                format=request.format,
                created_at=datetime.now(),
                created_by=request.created_by,
                project_id=request.project_id,
                status=ReportStatus.GENERATING,
                priority=request.priority
            )
            
            # 准备报告数据
            report_data = await self._prepare_report_data(request)
            
            # 生成报告章节
            sections = await self._generate_sections(request, report_data)
            
            # 生成图表
            charts = await self._generate_charts(request, report_data)
            
            # 渲染报告内容
            content = await self._render_report(
                request.template_type, 
                report_data, 
                sections, 
                charts
            )
            
            # 导出报告
            exported_content = await self._export_report(content, request.format)
            
            # 更新元数据
            metadata.status = ReportStatus.COMPLETED
            metadata.completed_at = datetime.now()
            metadata.file_size = len(exported_content) if isinstance(exported_content, bytes) else len(exported_content.encode())
            
            result = ReportResult(
                metadata=metadata,
                content=exported_content,
                sections=sections,
                charts=charts,
                summary=self._generate_summary(report_data),
                recommendations=self._generate_recommendations(report_data)
            )
            
            logger.info(f"报告生成完成: {metadata.report_id}")
            return result
            
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            metadata.status = ReportStatus.FAILED
            metadata.error_message = str(e)
            raise
    
    async def _prepare_report_data(self, request: ReportRequest) -> Dict[str, Any]:
        """准备报告数据"""
        data = {
            'request': request,
            'timestamp': datetime.now(),
            'project_info': request.data.get('project_info', {}),
            'analysis_results': request.data.get('analysis_results', {}),
            'statistics': await self._calculate_statistics(request.data),
            'trends': await self._analyze_trends(request.data),
            'comparisons': await self._generate_comparisons(request.data)
        }
        
        return data
    
    async def _generate_sections(self, request: ReportRequest, data: Dict[str, Any]) -> List[ReportSection]:
        """生成报告章节"""
        sections = []
        
        if request.template_type == TemplateType.RISK_ASSESSMENT:
            sections.extend(await self._generate_risk_sections(data))
        elif request.template_type == TemplateType.COMPLIANCE_CHECK:
            sections.extend(await self._generate_compliance_sections(data))
        elif request.template_type == TemplateType.ANOMALY_DETECTION:
            sections.extend(await self._generate_anomaly_sections(data))
        elif request.template_type == TemplateType.COMPREHENSIVE:
            sections.extend(await self._generate_comprehensive_sections(data))
        elif request.template_type == TemplateType.EXECUTIVE_SUMMARY:
            sections.extend(await self._generate_executive_sections(data))
        
        return sections
    
    async def _generate_risk_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """生成风险评估章节"""
        risk_data = data.get('analysis_results', {}).get('risk_assessment', {})
        
        sections = [
            ReportSection(
                title="风险评估概览",
                content=self._format_risk_overview(risk_data),
                order=1,
                section_type="overview"
            ),
            ReportSection(
                title="风险分类分析",
                content=self._format_risk_categories(risk_data),
                order=2,
                section_type="analysis"
            ),
            ReportSection(
                title="高风险项目识别",
                content=self._format_high_risks(risk_data),
                order=3,
                section_type="findings"
            ),
            ReportSection(
                title="风险缓解建议",
                content=self._format_risk_recommendations(risk_data),
                order=4,
                section_type="recommendations"
            )
        ]
        
        return sections
    
    async def _generate_compliance_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """生成合规检查章节"""
        compliance_data = data.get('analysis_results', {}).get('compliance_check', {})
        
        sections = [
            ReportSection(
                title="合规性检查概览",
                content=self._format_compliance_overview(compliance_data),
                order=1,
                section_type="overview"
            ),
            ReportSection(
                title="违规问题分析",
                content=self._format_violations(compliance_data),
                order=2,
                section_type="analysis"
            ),
            ReportSection(
                title="合规改进建议",
                content=self._format_compliance_recommendations(compliance_data),
                order=3,
                section_type="recommendations"
            )
        ]
        
        return sections
    
    async def _generate_charts(self, request: ReportRequest, data: Dict[str, Any]) -> List[ReportChart]:
        """生成报告图表"""
        charts = []
        
        # 风险分布图
        if 'risk_assessment' in data.get('analysis_results', {}):
            risk_chart = await self._create_risk_distribution_chart(data)
            charts.append(risk_chart)
        
        # 合规状态图
        if 'compliance_check' in data.get('analysis_results', {}):
            compliance_chart = await self._create_compliance_status_chart(data)
            charts.append(compliance_chart)
        
        # 趋势分析图
        if data.get('trends'):
            trend_chart = await self._create_trend_chart(data)
            charts.append(trend_chart)
        
        return charts
    
    async def _create_risk_distribution_chart(self, data: Dict[str, Any]) -> ReportChart:
        """创建风险分布图"""
        risk_data = data.get('analysis_results', {}).get('risk_assessment', {})
        
        # 准备数据
        risk_levels = [level.value for level in RiskLevel]
        risk_counts = [risk_data.get('risk_distribution', {}).get(level, 0) for level in risk_levels]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(risk_levels, risk_counts, color=['green', 'yellow', 'orange', 'red'])
        ax.set_title('项目风险等级分布', fontsize=16, fontweight='bold')
        ax.set_xlabel('风险等级')
        ax.set_ylabel('项目数量')
        
        # 添加数值标签
        for bar, count in zip(bars, risk_counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   str(count), ha='center', va='bottom')
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return ReportChart(
            chart_id="risk_distribution",
            title="风险等级分布",
            chart_type=ChartType.BAR,
            data=chart_data,
            config=ChartConfig(
                width=800,
                height=400,
                color_scheme="risk_levels"
            ),
            description="显示项目按风险等级的分布情况"
        )
    
    async def _render_report(self, template_type: TemplateType, data: Dict[str, Any], 
                           sections: List[ReportSection], charts: List[ReportChart]) -> str:
        """渲染报告内容"""
        template = self.default_templates.get(template_type)
        if not template:
            raise ValueError(f"未找到模板类型: {template_type}")
        
        # 准备模板变量
        template_vars = {
            'data': data,
            'sections': sections,
            'charts': charts,
            'timestamp': datetime.now(),
            'report_id': data.get('request').metadata.report_id if hasattr(data.get('request', {}), 'metadata') else 'N/A'
        }
        
        # 渲染模板
        jinja_template = Template(template.content)
        rendered_content = jinja_template.render(**template_vars)
        
        return rendered_content
    
    async def _export_report(self, content: str, format: ReportFormat) -> Union[str, bytes]:
        """导出报告"""
        if format == ReportFormat.HTML:
            return content
        elif format == ReportFormat.JSON:
            return json.dumps({'content': content}, ensure_ascii=False, indent=2)
        elif format == ReportFormat.CSV:
            # 简化的CSV导出
            return content.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
        else:
            return content
    
    def _create_risk_template(self) -> ReportTemplate:
        """创建风险评估报告模板"""
        content = """
        <h1>项目风险评估报告</h1>
        <p>生成时间: {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>报告ID: {{ report_id }}</p>
        
        {% for section in sections %}
        <h2>{{ section.title }}</h2>
        <div>{{ section.content | safe }}</div>
        {% endfor %}
        
        {% for chart in charts %}
        <h3>{{ chart.title }}</h3>
        <img src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.description }}">
        <p>{{ chart.description }}</p>
        {% endfor %}
        """
        
        return ReportTemplate(
            template_id="risk_assessment_v1",
            name="风险评估报告模板",
            template_type=TemplateType.RISK_ASSESSMENT,
            content=content,
            version="1.0",
            created_at=datetime.now()
        )
    
    def _create_compliance_template(self) -> ReportTemplate:
        """创建合规检查报告模板"""
        content = """
        <h1>合规性检查报告</h1>
        <p>生成时间: {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>报告ID: {{ report_id }}</p>
        
        {% for section in sections %}
        <h2>{{ section.title }}</h2>
        <div>{{ section.content | safe }}</div>
        {% endfor %}
        """
        
        return ReportTemplate(
            template_id="compliance_check_v1",
            name="合规检查报告模板",
            template_type=TemplateType.COMPLIANCE_CHECK,
            content=content,
            version="1.0",
            created_at=datetime.now()
        )
    
    def _create_comprehensive_template(self) -> ReportTemplate:
        """创建综合分析报告模板"""
        content = """
        <h1>综合分析报告</h1>
        <p>生成时间: {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>报告ID: {{ report_id }}</p>
        
        <h2>执行摘要</h2>
        <p>本报告对项目进行了全面的风险评估、合规检查和异常检测分析。</p>
        
        {% for section in sections %}
        <h2>{{ section.title }}</h2>
        <div>{{ section.content | safe }}</div>
        {% endfor %}
        
        {% for chart in charts %}
        <h3>{{ chart.title }}</h3>
        <img src="data:image/png;base64,{{ chart.data }}" alt="{{ chart.description }}">
        <p>{{ chart.description }}</p>
        {% endfor %}
        """
        
        return ReportTemplate(
            template_id="comprehensive_v1",
            name="综合分析报告模板",
            template_type=TemplateType.COMPREHENSIVE,
            content=content,
            version="1.0",
            created_at=datetime.now()
        )
    
    # 辅助方法
    def _format_risk_overview(self, risk_data: Dict[str, Any]) -> str:
        """格式化风险概览"""
        total_risks = risk_data.get('total_risks', 0)
        high_risks = risk_data.get('high_risk_count', 0)
        risk_score = risk_data.get('overall_risk_score', 0)
        
        return f"""
        <p>总风险项目数: {total_risks}</p>
        <p>高风险项目数: {high_risks}</p>
        <p>整体风险评分: {risk_score:.2f}</p>
        <p>风险评估完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
    
    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """生成报告摘要"""
        return "本报告基于智能分析引擎生成，提供了全面的项目审查结果和建议。"
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """生成建议列表"""
        return [
            "建议加强高风险项目的监控和管理",
            "建议完善合规检查流程和标准",
            "建议建立异常检测预警机制",
            "建议定期更新风险评估模型"
        ]
    
    # 其他辅助方法的占位符
    async def _calculate_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算统计数据"""
        return {}
    
    async def _analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析趋势"""
        return {}
    
    async def _generate_comparisons(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成对比数据"""
        return {}
    
    def _create_anomaly_template(self) -> ReportTemplate:
        """创建异常检测报告模板"""
        return ReportTemplate(
            template_id="anomaly_detection_v1",
            name="异常检测报告模板",
            template_type=TemplateType.ANOMALY_DETECTION,
            content="<h1>异常检测报告</h1>",
            version="1.0",
            created_at=datetime.now()
        )
    
    def _create_executive_template(self) -> ReportTemplate:
        """创建执行摘要模板"""
        return ReportTemplate(
            template_id="executive_summary_v1",
            name="执行摘要模板",
            template_type=TemplateType.EXECUTIVE_SUMMARY,
            content="<h1>执行摘要</h1>",
            version="1.0",
            created_at=datetime.now()
        )
    
    async def _generate_anomaly_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """生成异常检测章节"""
        return []
    
    async def _generate_comprehensive_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """生成综合分析章节"""
        return []
    
    async def _generate_executive_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """生成执行摘要章节"""
        return []
    
    async def _create_compliance_status_chart(self, data: Dict[str, Any]) -> ReportChart:
        """创建合规状态图表"""
        return ReportChart(
            chart_id="compliance_status",
            title="合规状态分布",
            chart_type=ChartType.PIE,
            data="",
            config=ChartConfig(),
            description="合规状态分布图"
        )
    
    async def _create_trend_chart(self, data: Dict[str, Any]) -> ReportChart:
        """创建趋势图表"""
        return ReportChart(
            chart_id="trend_analysis",
            title="趋势分析",
            chart_type=ChartType.LINE,
            data="",
            config=ChartConfig(),
            description="趋势分析图"
        )
    
    def _format_risk_categories(self, risk_data: Dict[str, Any]) -> str:
        """格式化风险分类"""
        return "<p>风险分类分析内容</p>"
    
    def _format_high_risks(self, risk_data: Dict[str, Any]) -> str:
        """格式化高风险项目"""
        return "<p>高风险项目识别内容</p>"
    
    def _format_risk_recommendations(self, risk_data: Dict[str, Any]) -> str:
        """格式化风险建议"""
        return "<p>风险缓解建议内容</p>"
    
    def _format_compliance_overview(self, compliance_data: Dict[str, Any]) -> str:
        """格式化合规概览"""
        return "<p>合规性检查概览内容</p>"
    
    def _format_violations(self, compliance_data: Dict[str, Any]) -> str:
        """格式化违规问题"""
        return "<p>违规问题分析内容</p>"
    
    def _format_compliance_recommendations(self, compliance_data: Dict[str, Any]) -> str:
        """格式化合规建议"""
        return "<p>合规改进建议内容</p>"