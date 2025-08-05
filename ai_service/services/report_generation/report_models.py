"""报告生成系统数据模型

定义报告生成相关的数据结构和模型
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """报告类型枚举"""
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECK = "compliance_check"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    """输出格式枚举"""
    PDF = "pdf"
    HTML = "html"
    WORD = "word"
    EXCEL = "excel"


class ChartType(str, Enum):
    """图表类型枚举"""
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"


class ReportMetadata(BaseModel):
    """报告元数据"""
    title: str = Field(..., description="报告标题")
    subtitle: Optional[str] = Field(None, description="报告副标题")
    author: str = Field(..., description="报告作者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    version: str = Field(default="1.0", description="报告版本")
    description: Optional[str] = Field(None, description="报告描述")
    tags: List[str] = Field(default_factory=list, description="报告标签")
    project_id: Optional[str] = Field(None, description="关联项目ID")


class ChartConfig(BaseModel):
    """图表配置"""
    chart_type: ChartType = Field(..., description="图表类型")
    title: str = Field(..., description="图表标题")
    data_source: str = Field(..., description="数据源字段名")
    x_axis: Optional[str] = Field(None, description="X轴字段")
    y_axis: Optional[str] = Field(None, description="Y轴字段")
    colors: List[str] = Field(default_factory=list, description="图表颜色")
    width: int = Field(default=800, description="图表宽度")
    height: int = Field(default=400, description="图表高度")
    options: Dict[str, Any] = Field(default_factory=dict, description="其他图表选项")


class ReportSection(BaseModel):
    """报告章节"""
    section_id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    order: int = Field(..., description="章节顺序")
    template: Optional[str] = Field(None, description="章节模板")
    charts: List[ChartConfig] = Field(default_factory=list, description="章节图表")
    data: Dict[str, Any] = Field(default_factory=dict, description="章节数据")
    show_in_toc: bool = Field(default=True, description="是否显示在目录中")


class ReportTemplate(BaseModel):
    """报告模板"""
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    report_type: ReportType = Field(..., description="报告类型")
    description: Optional[str] = Field(None, description="模板描述")
    template_path: str = Field(..., description="模板文件路径")
    sections: List[ReportSection] = Field(default_factory=list, description="报告章节")
    styles: Dict[str, Any] = Field(default_factory=dict, description="样式配置")
    variables: Dict[str, Any] = Field(default_factory=dict, description="模板变量")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class ReportData(BaseModel):
    """报告数据"""
    project_info: Dict[str, Any] = Field(default_factory=dict, description="项目信息")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="风险评估数据")
    compliance_check: Dict[str, Any] = Field(default_factory=dict, description="合规检查数据")
    document_analysis: Dict[str, Any] = Field(default_factory=dict, description="文档分析数据")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计数据")
    charts_data: Dict[str, Any] = Field(default_factory=dict, description="图表数据")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="自定义数据")


class ReportConfig(BaseModel):
    """报告配置"""
    template_id: str = Field(..., description="使用的模板ID")
    output_format: OutputFormat = Field(..., description="输出格式")
    output_path: Optional[str] = Field(None, description="输出路径")
    include_charts: bool = Field(default=True, description="是否包含图表")
    include_toc: bool = Field(default=True, description="是否包含目录")
    include_summary: bool = Field(default=True, description="是否包含摘要")
    page_size: str = Field(default="A4", description="页面大小")
    orientation: str = Field(default="portrait", description="页面方向")
    margins: Dict[str, float] = Field(
        default_factory=lambda: {"top": 2.5, "bottom": 2.5, "left": 2.5, "right": 2.5},
        description="页边距(cm)"
    )
    font_family: str = Field(default="SimSun", description="字体")
    font_size: int = Field(default=12, description="字体大小")
    custom_options: Dict[str, Any] = Field(default_factory=dict, description="自定义选项")


class ReportResult(BaseModel):
    """报告生成结果"""
    success: bool = Field(..., description="是否成功")
    report_id: str = Field(..., description="报告ID")
    file_path: Optional[str] = Field(None, description="生成的文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    generation_time: float = Field(..., description="生成耗时(秒)")
    metadata: ReportMetadata = Field(..., description="报告元数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class ReportRequest(BaseModel):
    """报告生成请求"""
    project_id: Optional[str] = Field(None, description="项目ID")
    report_type: ReportType = Field(..., description="报告类型")
    config: ReportConfig = Field(..., description="报告配置")
    data: ReportData = Field(..., description="报告数据")
    metadata: ReportMetadata = Field(..., description="报告元数据")
    custom_template: Optional[str] = Field(None, description="自定义模板内容")
    async_generation: bool = Field(default=False, description="是否异步生成")