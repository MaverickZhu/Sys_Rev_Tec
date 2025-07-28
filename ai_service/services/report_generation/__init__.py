"""智能报告生成系统

这个模块提供智能报告生成功能，包括：
- 报告模板引擎
- 多格式输出支持 (PDF, HTML, Word)
- 数据可视化组件
- 自动化报告流程
"""

from .report_models import (
    ReportTemplate,
    ReportData,
    ReportConfig,
    ReportMetadata,
    ChartConfig,
    ReportSection
)

from .template_engine import TemplateEngine
from .report_service import ReportService
from .pdf_generator import PDFGenerator
from .html_generator import HTMLGenerator

__all__ = [
    'ReportTemplate',
    'ReportData', 
    'ReportConfig',
    'ReportMetadata',
    'ChartConfig',
    'ReportSection',
    'TemplateEngine',
    'ReportService',
    'PDFGenerator',
    'HTMLGenerator'
]

__version__ = '1.0.0'
__author__ = 'AI Service Team'