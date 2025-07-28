"""PDF报告生成器

基于ReportLab的PDF报告生成功能
"""

import os
import io
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .report_models import ReportConfig, ReportMetadata, ReportSection, ChartConfig


class PDFGenerator:
    """PDF报告生成器"""
    
    def __init__(self):
        """初始化PDF生成器"""
        self.styles = getSampleStyleSheet()
        self._setup_chinese_fonts()
        self._setup_custom_styles()
        self.toc = TableOfContents()
        
    def _setup_chinese_fonts(self):
        """设置中文字体支持"""
        try:
            # 尝试注册中文字体
            font_paths = [
                'C:/Windows/Fonts/simsun.ttc',  # Windows 宋体
                'C:/Windows/Fonts/simhei.ttf',  # Windows 黑体
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('SimSun', font_path))
                        break
                    except Exception:
                        continue
        except Exception:
            # 如果无法注册中文字体，使用默认字体
            pass
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # 章节标题样式
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        ))
        
        # 子标题样式
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # 正文样式
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            firstLineIndent=20
        ))
        
        # 摘要样式
        self.styles.add(ParagraphStyle(
            name='Summary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=20,
            rightIndent=20,
            borderWidth=1,
            borderColor=colors.lightblue,
            borderPadding=10,
            backColor=colors.lightcyan
        ))
    
    def _create_header_footer(self, canvas_obj, doc):
        """创建页眉页脚"""
        canvas_obj.saveState()
        
        # 页眉
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawString(inch, doc.height + doc.topMargin - 0.5*inch, 
                            "智能报告生成系统")
        canvas_obj.drawRightString(doc.width + doc.leftMargin, 
                                 doc.height + doc.topMargin - 0.5*inch,
                                 datetime.now().strftime('%Y-%m-%d'))
        
        # 页脚
        canvas_obj.drawCentredString(doc.width/2 + doc.leftMargin, 
                                   0.5*inch, 
                                   f"第 {doc.page} 页")
        
        canvas_obj.restoreState()
    
    def _create_cover_page(self, metadata: ReportMetadata) -> List:
        """创建封面页
        
        Args:
            metadata: 报告元数据
            
        Returns:
            封面页元素列表
        """
        story = []
        
        # 添加空白
        story.append(Spacer(1, 2*inch))
        
        # 主标题
        title = Paragraph(metadata.title, self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # 副标题
        if metadata.subtitle:
            subtitle = Paragraph(metadata.subtitle, self.styles['Heading2'])
            story.append(subtitle)
            story.append(Spacer(1, 0.3*inch))
        
        # 报告信息表格
        info_data = [
            ['报告作者:', metadata.author],
            ['创建时间:', metadata.created_at.strftime('%Y年%m月%d日')],
            ['报告版本:', metadata.version]
        ]
        
        if metadata.project_id:
            info_data.append(['项目编号:', metadata.project_id])
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        story.append(Spacer(1, 1*inch))
        story.append(info_table)
        
        # 描述
        if metadata.description:
            story.append(Spacer(1, 0.5*inch))
            desc = Paragraph(f"<b>报告描述:</b><br/>{metadata.description}", 
                           self.styles['Summary'])
            story.append(desc)
        
        # 标签
        if metadata.tags:
            story.append(Spacer(1, 0.3*inch))
            tags_text = "、".join(metadata.tags)
            tags = Paragraph(f"<b>标签:</b> {tags_text}", self.styles['Normal'])
            story.append(tags)
        
        story.append(PageBreak())
        return story
    
    def _create_table_of_contents(self, sections: List[Dict[str, Any]]) -> List:
        """创建目录
        
        Args:
            sections: 章节列表
            
        Returns:
            目录元素列表
        """
        story = []
        
        # 目录标题
        toc_title = Paragraph("目录", self.styles['CustomTitle'])
        story.append(toc_title)
        story.append(Spacer(1, 0.3*inch))
        
        # 目录项
        toc_data = []
        for i, section in enumerate(sections, 1):
            if section.get('show_in_toc', True):
                toc_data.append([f"{i}. {section['title']}", "...", f"{i}"])
        
        if toc_data:
            toc_table = Table(toc_data, colWidths=[4*inch, 1*inch, 0.5*inch])
            toc_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.lightgrey)
            ]))
            story.append(toc_table)
        
        story.append(PageBreak())
        return story
    
    def _create_chart_placeholder(self, chart_config: ChartConfig) -> Table:
        """创建图表占位符
        
        Args:
            chart_config: 图表配置
            
        Returns:
            图表占位符表格
        """
        # 创建图表占位符
        chart_data = [
            [f"图表: {chart_config.title}"],
            [f"类型: {chart_config.chart_type.value}"],
            [f"数据源: {chart_config.data_source}"],
            ["[图表将在此处显示]"]
        ]
        
        chart_table = Table(chart_data, colWidths=[5*inch])
        chart_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow)
        ]))
        
        return chart_table
    
    def _process_section_content(self, section: Dict[str, Any]) -> List:
        """处理章节内容
        
        Args:
            section: 章节数据
            
        Returns:
            章节元素列表
        """
        story = []
        
        # 章节标题
        title = Paragraph(section['title'], self.styles['SectionTitle'])
        story.append(title)
        
        # 章节内容
        content = section.get('content', '')
        if content:
            # 简单的HTML标签处理
            content = content.replace('<br>', '<br/>')
            content = content.replace('<hr>', '<br/><br/>')
            
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    p = Paragraph(para.strip(), self.styles['CustomBody'])
                    story.append(p)
                    story.append(Spacer(1, 6))
        
        # 处理图表
        charts = section.get('charts', [])
        for chart in charts:
            if isinstance(chart, dict):
                chart_config = ChartConfig(**chart)
                chart_table = self._create_chart_placeholder(chart_config)
                story.append(Spacer(1, 12))
                story.append(chart_table)
                story.append(Spacer(1, 12))
        
        return story
    
    def generate_pdf(self, 
                    content: str,
                    config: ReportConfig,
                    metadata: ReportMetadata,
                    sections: List[Dict[str, Any]],
                    output_path: str) -> bool:
        """生成PDF报告
        
        Args:
            content: 报告内容
            config: 报告配置
            metadata: 报告元数据
            sections: 章节列表
            output_path: 输出文件路径
            
        Returns:
            是否生成成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 设置页面大小
            page_size = A4 if config.page_size == 'A4' else letter
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=page_size,
                topMargin=config.margins['top'] * cm,
                bottomMargin=config.margins['bottom'] * cm,
                leftMargin=config.margins['left'] * cm,
                rightMargin=config.margins['right'] * cm
            )
            
            # 构建文档内容
            story = []
            
            # 封面页
            story.extend(self._create_cover_page(metadata))
            
            # 目录
            if config.include_toc:
                story.extend(self._create_table_of_contents(sections))
            
            # 摘要
            if config.include_summary and metadata.description:
                summary_title = Paragraph("执行摘要", self.styles['SectionTitle'])
                story.append(summary_title)
                summary_content = Paragraph(metadata.description, self.styles['Summary'])
                story.append(summary_content)
                story.append(PageBreak())
            
            # 章节内容
            for section in sections:
                section_story = self._process_section_content(section)
                story.extend(section_story)
                story.append(Spacer(1, 20))
            
            # 生成PDF
            doc.build(story, onFirstPage=self._create_header_footer,
                     onLaterPages=self._create_header_footer)
            
            return True
            
        except Exception as e:
            print(f"PDF生成失败: {str(e)}")
            return False
    
    def generate_from_html(self, html_content: str, output_path: str) -> bool:
        """从HTML内容生成PDF
        
        Args:
            html_content: HTML内容
            output_path: 输出文件路径
            
        Returns:
            是否生成成功
        """
        try:
            # 这里可以集成HTML到PDF的转换库
            # 如 weasyprint, pdfkit 等
            # 目前返回简单实现
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # 简单的HTML解析和转换
            # 实际项目中应该使用专业的HTML解析库
            content = html_content.replace('<br>', '<br/>')
            content = content.replace('<p>', '').replace('</p>', '<br/><br/>')
            
            paragraphs = content.split('<br/><br/>')
            for para in paragraphs:
                if para.strip():
                    p = Paragraph(para.strip(), self.styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"HTML转PDF失败: {str(e)}")
            return False
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """获取PDF文件信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PDF文件信息
        """
        try:
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                return {
                    'file_path': pdf_path,
                    'file_size': file_size,
                    'created_at': datetime.fromtimestamp(os.path.getctime(pdf_path)),
                    'modified_at': datetime.fromtimestamp(os.path.getmtime(pdf_path))
                }
            else:
                return {'error': 'PDF文件不存在'}
        except Exception as e:
            return {'error': f'获取PDF信息失败: {str(e)}'}