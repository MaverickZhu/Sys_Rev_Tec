"""报告模板引擎

基于Jinja2的智能报告模板处理系统
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateNotFound

from .report_models import ReportTemplate, ReportData, ReportSection, ChartConfig


class TemplateEngine:
    """报告模板引擎"""
    
    def __init__(self, template_dir: str = "templates"):
        """初始化模板引擎
        
        Args:
            template_dir: 模板文件目录
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 注册自定义过滤器
        self._register_filters()
        
        # 注册自定义函数
        self._register_functions()
    
    def _register_filters(self):
        """注册自定义过滤器"""
        
        @self.env.filter('format_number')
        def format_number(value, decimal_places=2):
            """格式化数字"""
            try:
                return f"{float(value):.{decimal_places}f}"
            except (ValueError, TypeError):
                return str(value)
        
        @self.env.filter('format_percent')
        def format_percent(value, decimal_places=1):
            """格式化百分比"""
            try:
                return f"{float(value) * 100:.{decimal_places}f}%"
            except (ValueError, TypeError):
                return str(value)
        
        @self.env.filter('format_date')
        def format_date(value, format_str='%Y-%m-%d'):
            """格式化日期"""
            if isinstance(value, datetime):
                return value.strftime(format_str)
            elif isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.strftime(format_str)
                except ValueError:
                    return value
            return str(value)
        
        @self.env.filter('safe_get')
        def safe_get(data, key, default='N/A'):
            """安全获取字典值"""
            if isinstance(data, dict):
                return data.get(key, default)
            return default
        
        @self.env.filter('json_pretty')
        def json_pretty(value):
            """美化JSON输出"""
            try:
                return json.dumps(value, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)
    
    def _register_functions(self):
        """注册自定义函数"""
        
        def generate_chart_html(chart_config: Dict[str, Any]) -> str:
            """生成图表HTML代码"""
            chart_id = f"chart_{chart_config.get('id', 'default')}"
            chart_type = chart_config.get('chart_type', 'bar')
            
            # 基础图表HTML模板
            chart_html = f'''
            <div id="{chart_id}" style="width: {chart_config.get('width', 800)}px; height: {chart_config.get('height', 400)}px;"></div>
            <script>
                // 图表配置
                var chartConfig = {json.dumps(chart_config, ensure_ascii=False)};
                // 这里可以集成具体的图表库 (如 ECharts, Chart.js 等)
                console.log('Chart config:', chartConfig);
            </script>
            '''
            return chart_html
        
        def calculate_risk_level(score: float) -> str:
            """计算风险等级"""
            if score >= 80:
                return "高风险"
            elif score >= 60:
                return "中风险"
            elif score >= 40:
                return "低风险"
            else:
                return "极低风险"
        
        def get_compliance_status(score: float) -> str:
            """获取合规状态"""
            if score >= 90:
                return "完全合规"
            elif score >= 70:
                return "基本合规"
            elif score >= 50:
                return "部分合规"
            else:
                return "不合规"
        
        # 注册到Jinja2环境
        self.env.globals.update({
            'generate_chart_html': generate_chart_html,
            'calculate_risk_level': calculate_risk_level,
            'get_compliance_status': get_compliance_status,
            'now': datetime.now,
            'today': datetime.now().date()
        })
    
    def load_template(self, template_path: str) -> Template:
        """加载模板文件
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            Jinja2模板对象
            
        Raises:
            TemplateNotFound: 模板文件不存在
        """
        try:
            return self.env.get_template(template_path)
        except TemplateNotFound as e:
            raise TemplateNotFound(f"模板文件不存在: {template_path}") from e
    
    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """渲染模板
        
        Args:
            template_path: 模板文件路径
            context: 模板上下文数据
            
        Returns:
            渲染后的内容
            
        Raises:
            TemplateError: 模板渲染错误
        """
        try:
            template = self.load_template(template_path)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateError(f"模板渲染失败: {str(e)}") from e
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """渲染模板字符串
        
        Args:
            template_string: 模板字符串
            context: 模板上下文数据
            
        Returns:
            渲染后的内容
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateError(f"模板字符串渲染失败: {str(e)}") from e
    
    def render_section(self, section: ReportSection, data: ReportData) -> str:
        """渲染报告章节
        
        Args:
            section: 报告章节
            data: 报告数据
            
        Returns:
            渲染后的章节内容
        """
        # 准备章节上下文
        context = {
            'section': section,
            'data': data.dict(),
            'section_data': section.data,
            'charts': section.charts
        }
        
        # 如果有模板，使用模板渲染
        if section.template:
            return self.render_template(section.template, context)
        else:
            # 否则直接渲染内容
            return self.render_string(section.content, context)
    
    def render_report(self, template: ReportTemplate, data: ReportData) -> str:
        """渲染完整报告
        
        Args:
            template: 报告模板
            data: 报告数据
            
        Returns:
            渲染后的报告内容
        """
        # 准备全局上下文
        context = {
            'template': template,
            'data': data.dict(),
            'sections': [],
            'metadata': template.variables
        }
        
        # 渲染各个章节
        rendered_sections = []
        for section in sorted(template.sections, key=lambda s: s.order):
            try:
                rendered_content = self.render_section(section, data)
                rendered_sections.append({
                    'id': section.id,
                    'title': section.title,
                    'content': rendered_content,
                    'order': section.order,
                    'show_in_toc': section.show_in_toc
                })
            except Exception as e:
                # 章节渲染失败时，添加错误信息
                rendered_sections.append({
                    'id': section.id,
                    'title': section.title,
                    'content': f"<div class='error'>章节渲染失败: {str(e)}</div>",
                    'order': section.order,
                    'show_in_toc': section.show_in_toc
                })
        
        context['sections'] = rendered_sections
        
        # 渲染主模板
        return self.render_template(template.template_path, context)
    
    def validate_template(self, template_path: str) -> List[str]:
        """验证模板语法
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            错误信息列表，空列表表示无错误
        """
        errors = []
        try:
            template = self.load_template(template_path)
            # 尝试解析模板
            template.environment.parse(template.source)
        except TemplateNotFound:
            errors.append(f"模板文件不存在: {template_path}")
        except TemplateError as e:
            errors.append(f"模板语法错误: {str(e)}")
        except Exception as e:
            errors.append(f"模板验证失败: {str(e)}")
        
        return errors
    
    def get_template_variables(self, template_path: str) -> List[str]:
        """获取模板中使用的变量
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            变量名列表
        """
        try:
            template = self.load_template(template_path)
            ast = template.environment.parse(template.source)
            variables = set()
            
            # 遍历AST节点查找变量
            for node in ast.find_all():
                if hasattr(node, 'name'):
                    variables.add(node.name)
            
            return list(variables)
        except Exception:
            return []
    
    def create_sample_context(self, template_path: str) -> Dict[str, Any]:
        """为模板创建示例上下文
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            示例上下文数据
        """
        variables = self.get_template_variables(template_path)
        
        # 创建示例数据
        sample_context = {
            'project_name': '示例项目',
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'author': '系统管理员',
            'version': '1.0',
            'risk_score': 75.5,
            'compliance_score': 85.2,
            'total_documents': 150,
            'issues_found': 12,
            'recommendations': [
                '建议1：完善文档管理流程',
                '建议2：加强风险控制措施',
                '建议3：定期进行合规性检查'
            ]
        }
        
        # 为模板变量提供默认值
        for var in variables:
            if var not in sample_context:
                sample_context[var] = f'示例_{var}'
        
        return sample_context