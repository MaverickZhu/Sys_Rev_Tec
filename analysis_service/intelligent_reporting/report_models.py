#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能报告数据模型
定义报告生成系统的数据结构和枚举类型

作者: AI Assistant
创建时间: 2025-07-28
版本: 1.0.0
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json


class ReportStatus(Enum):
    """报告状态"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"      # 已取消
    SCHEDULED = "scheduled"      # 已调度


class ReportPriority(Enum):
    """报告优先级"""
    LOW = 1      # 低优先级
    NORMAL = 2   # 普通优先级
    HIGH = 3     # 高优先级
    URGENT = 4   # 紧急优先级
    CRITICAL = 5 # 关键优先级


class ReportFormat(Enum):
    """报告格式"""
    PDF = "pdf"           # PDF格式
    HTML = "html"         # HTML格式
    DOCX = "docx"         # Word文档
    XLSX = "xlsx"         # Excel表格
    JSON = "json"         # JSON数据
    CSV = "csv"           # CSV文件
    PPTX = "pptx"         # PowerPoint演示文稿
    PNG = "png"           # PNG图片
    SVG = "svg"           # SVG矢量图


class TemplateType(Enum):
    """报告模板类型"""
    EXECUTIVE_SUMMARY = "executive_summary"     # 执行摘要
    DETAILED_ANALYSIS = "detailed_analysis"     # 详细分析
    RISK_ASSESSMENT = "risk_assessment"         # 风险评估
    COMPLIANCE_REPORT = "compliance_report"     # 合规报告
    ANOMALY_REPORT = "anomaly_report"           # 异常报告
    PERFORMANCE_DASHBOARD = "performance_dashboard" # 绩效仪表板
    TREND_ANALYSIS = "trend_analysis"           # 趋势分析
    COMPARATIVE_ANALYSIS = "comparative_analysis" # 对比分析
    CUSTOM = "custom"                           # 自定义模板


class ChartType(Enum):
    """图表类型"""
    BAR = "bar"                 # 柱状图
    LINE = "line"               # 折线图
    PIE = "pie"                 # 饼图
    SCATTER = "scatter"         # 散点图
    HISTOGRAM = "histogram"     # 直方图
    BOX = "box"                 # 箱线图
    HEATMAP = "heatmap"         # 热力图
    RADAR = "radar"             # 雷达图
    TREEMAP = "treemap"         # 树状图
    SANKEY = "sankey"           # 桑基图
    GAUGE = "gauge"             # 仪表盘
    WATERFALL = "waterfall"     # 瀑布图
    FUNNEL = "funnel"           # 漏斗图
    GANTT = "gantt"             # 甘特图
    NETWORK = "network"         # 网络图


class ReportDeliveryMethod(Enum):
    """报告交付方式"""
    EMAIL = "email"             # 邮件发送
    DOWNLOAD = "download"       # 下载链接
    API = "api"                 # API接口
    FTP = "ftp"                 # FTP上传
    WEBHOOK = "webhook"         # Webhook推送
    STORAGE = "storage"         # 存储系统


@dataclass
class ReportMetadata:
    """报告元数据"""
    title: str                              # 报告标题
    description: str                        # 报告描述
    author: str                            # 报告作者
    created_time: datetime                 # 创建时间
    updated_time: Optional[datetime] = None # 更新时间
    version: str = "1.0"                   # 版本号
    tags: List[str] = field(default_factory=list) # 标签
    category: str = "general"              # 分类
    language: str = "zh-CN"                # 语言
    template_id: Optional[str] = None      # 模板ID
    data_sources: List[str] = field(default_factory=list) # 数据源
    custom_fields: Dict[str, Any] = field(default_factory=dict) # 自定义字段


@dataclass
class ReportRequest:
    """报告生成请求"""
    request_id: str                        # 请求ID
    project_id: str                        # 项目ID
    template_type: TemplateType            # 模板类型
    output_formats: List[ReportFormat]     # 输出格式
    priority: ReportPriority = ReportPriority.NORMAL # 优先级
    
    # 数据配置
    data_filters: Dict[str, Any] = field(default_factory=dict) # 数据过滤器
    date_range: Optional[tuple] = None     # 日期范围
    include_sections: List[str] = field(default_factory=list) # 包含章节
    exclude_sections: List[str] = field(default_factory=list) # 排除章节
    
    # 定制配置
    custom_title: Optional[str] = None     # 自定义标题
    custom_template: Optional[str] = None  # 自定义模板
    chart_configs: Dict[str, Any] = field(default_factory=dict) # 图表配置
    style_config: Dict[str, Any] = field(default_factory=dict) # 样式配置
    
    # 交付配置
    delivery_method: ReportDeliveryMethod = ReportDeliveryMethod.DOWNLOAD
    delivery_config: Dict[str, Any] = field(default_factory=dict) # 交付配置
    
    # 调度配置
    schedule_config: Optional[Dict[str, Any]] = None # 调度配置
    auto_refresh: bool = False             # 自动刷新
    refresh_interval: Optional[timedelta] = None # 刷新间隔
    
    # 元数据
    metadata: Optional[ReportMetadata] = None # 报告元数据
    created_by: str = "system"             # 创建者
    created_time: datetime = field(default_factory=datetime.now) # 创建时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "project_id": self.project_id,
            "template_type": self.template_type.value,
            "output_formats": [f.value for f in self.output_formats],
            "priority": self.priority.value,
            "data_filters": self.data_filters,
            "date_range": self.date_range,
            "include_sections": self.include_sections,
            "exclude_sections": self.exclude_sections,
            "custom_title": self.custom_title,
            "custom_template": self.custom_template,
            "chart_configs": self.chart_configs,
            "style_config": self.style_config,
            "delivery_method": self.delivery_method.value,
            "delivery_config": self.delivery_config,
            "schedule_config": self.schedule_config,
            "auto_refresh": self.auto_refresh,
            "refresh_interval": self.refresh_interval.total_seconds() if self.refresh_interval else None,
            "created_by": self.created_by,
            "created_time": self.created_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportRequest':
        """从字典创建"""
        return cls(
            request_id=data["request_id"],
            project_id=data["project_id"],
            template_type=TemplateType(data["template_type"]),
            output_formats=[ReportFormat(f) for f in data["output_formats"]],
            priority=ReportPriority(data.get("priority", ReportPriority.NORMAL.value)),
            data_filters=data.get("data_filters", {}),
            date_range=data.get("date_range"),
            include_sections=data.get("include_sections", []),
            exclude_sections=data.get("exclude_sections", []),
            custom_title=data.get("custom_title"),
            custom_template=data.get("custom_template"),
            chart_configs=data.get("chart_configs", {}),
            style_config=data.get("style_config", {}),
            delivery_method=ReportDeliveryMethod(data.get("delivery_method", ReportDeliveryMethod.DOWNLOAD.value)),
            delivery_config=data.get("delivery_config", {}),
            schedule_config=data.get("schedule_config"),
            auto_refresh=data.get("auto_refresh", False),
            refresh_interval=timedelta(seconds=data["refresh_interval"]) if data.get("refresh_interval") else None,
            created_by=data.get("created_by", "system"),
            created_time=datetime.fromisoformat(data["created_time"]) if data.get("created_time") else datetime.now()
        )


@dataclass
class ReportResult:
    """报告生成结果"""
    result_id: str                         # 结果ID
    request_id: str                        # 请求ID
    status: ReportStatus                   # 状态
    
    # 生成信息
    generated_time: Optional[datetime] = None # 生成时间
    generation_duration: Optional[timedelta] = None # 生成耗时
    file_paths: Dict[ReportFormat, str] = field(default_factory=dict) # 文件路径
    file_sizes: Dict[ReportFormat, int] = field(default_factory=dict) # 文件大小
    
    # 内容信息
    page_count: Optional[int] = None       # 页数
    chart_count: Optional[int] = None      # 图表数量
    table_count: Optional[int] = None      # 表格数量
    data_points: Optional[int] = None      # 数据点数量
    
    # 质量指标
    completeness_score: float = 1.0       # 完整性评分
    accuracy_score: float = 1.0           # 准确性评分
    readability_score: float = 1.0        # 可读性评分
    
    # 错误信息
    error_message: Optional[str] = None    # 错误消息
    warnings: List[str] = field(default_factory=list) # 警告信息
    
    # 交付信息
    delivery_status: Optional[str] = None  # 交付状态
    delivery_time: Optional[datetime] = None # 交付时间
    download_urls: Dict[ReportFormat, str] = field(default_factory=dict) # 下载链接
    
    # 元数据
    metadata: Optional[ReportMetadata] = None # 报告元数据
    processing_logs: List[str] = field(default_factory=list) # 处理日志
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "result_id": self.result_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "generated_time": self.generated_time.isoformat() if self.generated_time else None,
            "generation_duration": self.generation_duration.total_seconds() if self.generation_duration else None,
            "file_paths": {k.value: v for k, v in self.file_paths.items()},
            "file_sizes": {k.value: v for k, v in self.file_sizes.items()},
            "page_count": self.page_count,
            "chart_count": self.chart_count,
            "table_count": self.table_count,
            "data_points": self.data_points,
            "completeness_score": self.completeness_score,
            "accuracy_score": self.accuracy_score,
            "readability_score": self.readability_score,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "delivery_status": self.delivery_status,
            "delivery_time": self.delivery_time.isoformat() if self.delivery_time else None,
            "download_urls": {k.value: v for k, v in self.download_urls.items()},
            "processing_logs": self.processing_logs
        }
    
    def is_successful(self) -> bool:
        """检查是否成功"""
        return self.status == ReportStatus.COMPLETED and not self.error_message
    
    def get_overall_quality_score(self) -> float:
        """获取整体质量评分"""
        return (self.completeness_score + self.accuracy_score + self.readability_score) / 3.0


@dataclass
class ReportSection:
    """报告章节"""
    section_id: str                        # 章节ID
    title: str                            # 章节标题
    content: str                          # 章节内容
    order: int = 0                        # 排序
    level: int = 1                        # 层级
    
    # 样式配置
    style_class: Optional[str] = None     # 样式类
    custom_styles: Dict[str, Any] = field(default_factory=dict) # 自定义样式
    
    # 内容配置
    include_charts: bool = True           # 包含图表
    include_tables: bool = True           # 包含表格
    include_images: bool = True           # 包含图片
    
    # 子章节
    subsections: List['ReportSection'] = field(default_factory=list) # 子章节
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict) # 元数据
    
    def add_subsection(self, subsection: 'ReportSection'):
        """添加子章节"""
        subsection.level = self.level + 1
        self.subsections.append(subsection)
    
    def get_word_count(self) -> int:
        """获取字数"""
        count = len(self.content.split())
        for subsection in self.subsections:
            count += subsection.get_word_count()
        return count


@dataclass
class ReportChart:
    """报告图表"""
    chart_id: str                         # 图表ID
    title: str                           # 图表标题
    chart_type: ChartType                # 图表类型
    data: Dict[str, Any]                 # 图表数据
    
    # 配置
    width: int = 800                     # 宽度
    height: int = 600                    # 高度
    config: Dict[str, Any] = field(default_factory=dict) # 图表配置
    
    # 样式
    theme: str = "default"               # 主题
    color_palette: List[str] = field(default_factory=list) # 颜色调色板
    
    # 交互
    interactive: bool = True             # 是否交互
    export_formats: List[str] = field(default_factory=lambda: ["png", "svg"]) # 导出格式
    
    # 元数据
    description: Optional[str] = None    # 描述
    data_source: Optional[str] = None    # 数据源
    created_time: datetime = field(default_factory=datetime.now) # 创建时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_id": self.chart_id,
            "title": self.title,
            "chart_type": self.chart_type.value,
            "data": self.data,
            "width": self.width,
            "height": self.height,
            "config": self.config,
            "theme": self.theme,
            "color_palette": self.color_palette,
            "interactive": self.interactive,
            "export_formats": self.export_formats,
            "description": self.description,
            "data_source": self.data_source,
            "created_time": self.created_time.isoformat()
        }


@dataclass
class ReportTemplate:
    """报告模板"""
    template_id: str                      # 模板ID
    name: str                            # 模板名称
    template_type: TemplateType          # 模板类型
    description: str                     # 模板描述
    
    # 结构配置
    sections: List[ReportSection] = field(default_factory=list) # 章节列表
    default_charts: List[ReportChart] = field(default_factory=list) # 默认图表
    
    # 样式配置
    style_config: Dict[str, Any] = field(default_factory=dict) # 样式配置
    layout_config: Dict[str, Any] = field(default_factory=dict) # 布局配置
    
    # 数据配置
    required_fields: List[str] = field(default_factory=list) # 必需字段
    optional_fields: List[str] = field(default_factory=list) # 可选字段
    data_transformations: List[Dict[str, Any]] = field(default_factory=list) # 数据转换
    
    # 元数据
    version: str = "1.0"                 # 版本
    author: str = "system"               # 作者
    created_time: datetime = field(default_factory=datetime.now) # 创建时间
    updated_time: Optional[datetime] = None # 更新时间
    tags: List[str] = field(default_factory=list) # 标签
    
    # 配置
    enabled: bool = True                 # 是否启用
    public: bool = False                 # 是否公开
    
    def add_section(self, section: ReportSection):
        """添加章节"""
        section.order = len(self.sections)
        self.sections.append(section)
    
    def add_chart(self, chart: ReportChart):
        """添加默认图表"""
        self.default_charts.append(chart)
    
    def validate(self) -> List[str]:
        """验证模板"""
        errors = []
        
        if not self.name:
            errors.append("模板名称不能为空")
        
        if not self.sections:
            errors.append("模板必须包含至少一个章节")
        
        # 检查章节ID唯一性
        section_ids = [s.section_id for s in self.sections]
        if len(section_ids) != len(set(section_ids)):
            errors.append("章节ID必须唯一")
        
        # 检查图表ID唯一性
        chart_ids = [c.chart_id for c in self.default_charts]
        if len(chart_ids) != len(set(chart_ids)):
            errors.append("图表ID必须唯一")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "template_type": self.template_type.value,
            "description": self.description,
            "sections": [s.__dict__ for s in self.sections],
            "default_charts": [c.to_dict() for c in self.default_charts],
            "style_config": self.style_config,
            "layout_config": self.layout_config,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "data_transformations": self.data_transformations,
            "version": self.version,
            "author": self.author,
            "created_time": self.created_time.isoformat(),
            "updated_time": self.updated_time.isoformat() if self.updated_time else None,
            "tags": self.tags,
            "enabled": self.enabled,
            "public": self.public
        }


@dataclass
class ChartConfig:
    """图表配置"""
    chart_type: ChartType                 # 图表类型
    title: str                           # 标题
    x_axis: str                          # X轴字段
    y_axis: Union[str, List[str]]        # Y轴字段
    
    # 样式配置
    width: int = 800                     # 宽度
    height: int = 600                    # 高度
    theme: str = "default"               # 主题
    colors: List[str] = field(default_factory=list) # 颜色
    
    # 数据配置
    aggregation: Optional[str] = None    # 聚合方式
    filters: Dict[str, Any] = field(default_factory=dict) # 过滤器
    sort_by: Optional[str] = None        # 排序字段
    limit: Optional[int] = None          # 数据限制
    
    # 显示配置
    show_legend: bool = True             # 显示图例
    show_grid: bool = True               # 显示网格
    show_labels: bool = True             # 显示标签
    show_values: bool = False            # 显示数值
    
    # 交互配置
    interactive: bool = True             # 交互式
    zoom_enabled: bool = False           # 缩放
    pan_enabled: bool = False            # 平移
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "width": self.width,
            "height": self.height,
            "theme": self.theme,
            "colors": self.colors,
            "aggregation": self.aggregation,
            "filters": self.filters,
            "sort_by": self.sort_by,
            "limit": self.limit,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "show_labels": self.show_labels,
            "show_values": self.show_values,
            "interactive": self.interactive,
            "zoom_enabled": self.zoom_enabled,
            "pan_enabled": self.pan_enabled
        }