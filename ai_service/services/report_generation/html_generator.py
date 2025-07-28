"""HTML报告生成器

基于模板的HTML报告生成功能
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .report_models import ReportConfig, ReportMetadata, ReportSection, ChartConfig


class HTMLGenerator:
    """HTML报告生成器"""
    
    def __init__(self):
        """初始化HTML生成器"""
        self.base_template = self._get_base_template()
        self.chart_templates = self._get_chart_templates()
    
    def _get_base_template(self) -> str:
        """获取基础HTML模板"""
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .title {
            color: #007acc;
            font-size: 2.5em;
            margin: 0;
            font-weight: bold;
        }
        .subtitle {
            color: #666;
            font-size: 1.2em;
            margin: 10px 0;
        }
        .metadata {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #007acc;
        }
        .metadata-item {
            margin: 5px 0;
        }
        .metadata-label {
            font-weight: bold;
            color: #333;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .toc h2 {
            color: #007acc;
            margin-top: 0;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px dotted #ccc;
        }
        .toc a {
            text-decoration: none;
            color: #333;
        }
        .toc a:hover {
            color: #007acc;
        }
        .section {
            margin: 30px 0;
            padding: 20px 0;
        }
        .section-title {
            color: #007acc;
            font-size: 1.8em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        .section-content {
            line-height: 1.8;
            color: #333;
        }
        .chart-container {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #fafafa;
        }
        .chart-title {
            font-weight: bold;
            color: #007acc;
            margin-bottom: 10px;
        }
        .chart-placeholder {
            width: 100%;
            height: 400px;
            background-color: #f0f0f0;
            border: 2px dashed #ccc;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 1.1em;
        }
        .summary {
            background-color: #e8f4fd;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #007acc;
            margin: 20px 0;
        }
        .summary h3 {
            color: #007acc;
            margin-top: 0;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .table th, .table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .table th {
            background-color: #007acc;
            color: white;
            font-weight: bold;
        }
        .table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 0.9em;
        }
        .risk-high { color: #d32f2f; font-weight: bold; }
        .risk-medium { color: #f57c00; font-weight: bold; }
        .risk-low { color: #388e3c; font-weight: bold; }
        .compliance-good { color: #388e3c; font-weight: bold; }
        .compliance-warning { color: #f57c00; font-weight: bold; }
        .compliance-bad { color: #d32f2f; font-weight: bold; }
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
        }
    </style>
    <!-- Chart.js for charts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- ECharts for advanced charts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.0/dist/echarts.min.js"></script>
</head>
<body>
    <div class="container">
        {{ content }}
    </div>
    
    <script>
        // 图表初始化脚本
        {{ chart_scripts }}
    </script>
</body>
</html>
        '''
    
    def _get_chart_templates(self) -> Dict[str, str]:
        """获取图表模板"""
        return {
            'bar': '''
                <div class="chart-container">
                    <div class="chart-title">{{ title }}</div>
                    <canvas id="{{ chart_id }}" width="{{ width }}" height="{{ height }}"></canvas>
                </div>
            ''',
            'pie': '''
                <div class="chart-container">
                    <div class="chart-title">{{ title }}</div>
                    <canvas id="{{ chart_id }}" width="{{ width }}" height="{{ height }}"></canvas>
                </div>
            ''',
            'line': '''
                <div class="chart-container">
                    <div class="chart-title">{{ title }}</div>
                    <canvas id="{{ chart_id }}" width="{{ width }}" height="{{ height }}"></canvas>
                </div>
            ''',
            'gauge': '''
                <div class="chart-container">
                    <div class="chart-title">{{ title }}</div>
                    <div id="{{ chart_id }}" style="width: {{ width }}px; height: {{ height }}px;"></div>
                </div>
            '''
        }
    
    def _generate_header(self, metadata: ReportMetadata) -> str:
        """生成报告头部
        
        Args:
            metadata: 报告元数据
            
        Returns:
            HTML头部内容
        """
        header_html = f'''
        <div class="header">
            <h1 class="title">{metadata.title}</h1>
        '''
        
        if metadata.subtitle:
            header_html += f'<p class="subtitle">{metadata.subtitle}</p>'
        
        header_html += '</div>'
        
        # 元数据信息
        metadata_html = '''
        <div class="metadata">
            <h3>报告信息</h3>
        '''
        
        metadata_items = [
            ('报告作者', metadata.author),
            ('创建时间', metadata.created_at.strftime('%Y年%m月%d日 %H:%M')),
            ('报告版本', metadata.version)
        ]
        
        if metadata.project_id:
            metadata_items.append(('项目编号', metadata.project_id))
        
        if metadata.tags:
            metadata_items.append(('标签', '、'.join(metadata.tags)))
        
        for label, value in metadata_items:
            metadata_html += f'''
            <div class="metadata-item">
                <span class="metadata-label">{label}:</span> {value}
            </div>
            '''
        
        metadata_html += '</div>'
        
        return header_html + metadata_html
    
    def _generate_toc(self, sections: List[Dict[str, Any]]) -> str:
        """生成目录
        
        Args:
            sections: 章节列表
            
        Returns:
            目录HTML内容
        """
        toc_html = '''
        <div class="toc">
            <h2>目录</h2>
            <ul>
        '''
        
        for i, section in enumerate(sections, 1):
            if section.get('show_in_toc', True):
                section_id = section.get('id', f'section_{i}')
                toc_html += f'''
                <li><a href="#{section_id}">{i}. {section['title']}</a></li>
                '''
        
        toc_html += '''
            </ul>
        </div>
        '''
        
        return toc_html
    
    def _generate_summary(self, metadata: ReportMetadata) -> str:
        """生成摘要
        
        Args:
            metadata: 报告元数据
            
        Returns:
            摘要HTML内容
        """
        if not metadata.description:
            return ''
        
        return f'''
        <div class="summary">
            <h3>执行摘要</h3>
            <p>{metadata.description}</p>
        </div>
        '''
    
    def _generate_chart_html(self, chart_config: ChartConfig, chart_id: str) -> str:
        """生成图表HTML
        
        Args:
            chart_config: 图表配置
            chart_id: 图表ID
            
        Returns:
            图表HTML内容
        """
        chart_type = chart_config.chart_type.value
        template = self.chart_templates.get(chart_type, self.chart_templates['bar'])
        
        # 替换模板变量
        chart_html = template.replace('{{ title }}', chart_config.title)
        chart_html = chart_html.replace('{{ chart_id }}', chart_id)
        chart_html = chart_html.replace('{{ width }}', str(chart_config.width))
        chart_html = chart_html.replace('{{ height }}', str(chart_config.height))
        
        return chart_html
    
    def _generate_chart_script(self, chart_config: ChartConfig, chart_id: str, data: Dict[str, Any]) -> str:
        """生成图表脚本
        
        Args:
            chart_config: 图表配置
            chart_id: 图表ID
            data: 图表数据
            
        Returns:
            图表JavaScript代码
        """
        chart_type = chart_config.chart_type.value
        
        if chart_type in ['bar', 'pie', 'line']:
            # Chart.js 图表
            return f'''
            // {chart_config.title}
            var ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
            var chart_{chart_id} = new Chart(ctx_{chart_id}, {{
                type: '{chart_type}',
                data: {json.dumps(data, ensure_ascii=False)},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{chart_config.title}'
                        }}
                    }}
                }}
            }});
            '''
        elif chart_type == 'gauge':
            # ECharts 仪表盘
            return f'''
            // {chart_config.title}
            var chart_{chart_id} = echarts.init(document.getElementById('{chart_id}'));
            var option_{chart_id} = {{
                title: {{
                    text: '{chart_config.title}',
                    left: 'center'
                }},
                series: [{{
                    type: 'gauge',
                    data: {json.dumps(data, ensure_ascii=False)}
                }}]
            }};
            chart_{chart_id}.setOption(option_{chart_id});
            '''
        else:
            return f'// 未支持的图表类型: {chart_type}'
    
    def _process_section_content(self, section: Dict[str, Any], section_index: int) -> tuple[str, str]:
        """处理章节内容
        
        Args:
            section: 章节数据
            section_index: 章节索引
            
        Returns:
            (章节HTML内容, 图表脚本)
        """
        section_id = section.get('id', f'section_{section_index}')
        
        section_html = f'''
        <div class="section" id="{section_id}">
            <h2 class="section-title">{section['title']}</h2>
            <div class="section-content">
        '''
        
        # 处理章节内容
        content = section.get('content', '')
        if content:
            # 简单的Markdown到HTML转换
            content = content.replace('\n\n', '</p><p>')
            content = content.replace('\n', '<br>')
            content = f'<p>{content}</p>'
            
            # 处理特殊标记
            content = content.replace('**', '<strong>').replace('**', '</strong>')
            content = content.replace('*', '<em>').replace('*', '</em>')
            
            section_html += content
        
        section_html += '</div>'
        
        # 处理图表
        chart_scripts = []
        charts = section.get('charts', [])
        for i, chart in enumerate(charts):
            if isinstance(chart, dict):
                chart_config = ChartConfig(**chart)
                chart_id = f'chart_{section_index}_{i}'
                
                # 生成图表HTML
                chart_html = self._generate_chart_html(chart_config, chart_id)
                section_html += chart_html
                
                # 生成示例数据
                sample_data = self._generate_sample_chart_data(chart_config)
                
                # 生成图表脚本
                chart_script = self._generate_chart_script(chart_config, chart_id, sample_data)
                chart_scripts.append(chart_script)
        
        section_html += '</div>'
        
        return section_html, '\n'.join(chart_scripts)
    
    def _generate_sample_chart_data(self, chart_config: ChartConfig) -> Dict[str, Any]:
        """生成示例图表数据
        
        Args:
            chart_config: 图表配置
            
        Returns:
            示例图表数据
        """
        chart_type = chart_config.chart_type.value
        
        if chart_type == 'bar':
            return {
                'labels': ['项目A', '项目B', '项目C', '项目D'],
                'datasets': [{
                    'label': chart_config.title,
                    'data': [65, 59, 80, 81],
                    'backgroundColor': chart_config.colors or [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(255, 205, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ]
                }]
            }
        elif chart_type == 'pie':
            return {
                'labels': ['高风险', '中风险', '低风险', '无风险'],
                'datasets': [{
                    'data': [30, 25, 35, 10],
                    'backgroundColor': [
                        '#FF6384',
                        '#FF9F40',
                        '#FFCD56',
                        '#4BC0C0'
                    ]
                }]
            }
        elif chart_type == 'line':
            return {
                'labels': ['1月', '2月', '3月', '4月', '5月', '6月'],
                'datasets': [{
                    'label': chart_config.title,
                    'data': [65, 59, 80, 81, 56, 55],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                }]
            }
        elif chart_type == 'gauge':
            return [{
                'value': 75,
                'name': '完成度'
            }]
        else:
            return {}
    
    def _generate_footer(self) -> str:
        """生成页脚
        
        Returns:
            页脚HTML内容
        """
        return f'''
        <div class="footer">
            <p>本报告由智能报告生成系统自动生成</p>
            <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
        '''
    
    def generate_html(self,
                     content: str,
                     config: ReportConfig,
                     metadata: ReportMetadata,
                     sections: List[Dict[str, Any]],
                     output_path: str) -> bool:
        """生成HTML报告
        
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
            
            # 生成HTML内容
            html_content = ''
            chart_scripts = []
            
            # 头部
            html_content += self._generate_header(metadata)
            
            # 目录
            if config.include_toc:
                html_content += self._generate_toc(sections)
            
            # 摘要
            if config.include_summary:
                html_content += self._generate_summary(metadata)
            
            # 章节内容
            for i, section in enumerate(sections, 1):
                section_html, section_scripts = self._process_section_content(section, i)
                html_content += section_html
                if section_scripts:
                    chart_scripts.append(section_scripts)
            
            # 页脚
            html_content += self._generate_footer()
            
            # 组装完整HTML
            full_html = self.base_template.replace('{{ title }}', metadata.title)
            full_html = full_html.replace('{{ content }}', html_content)
            full_html = full_html.replace('{{ chart_scripts }}', '\n'.join(chart_scripts))
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            return True
            
        except Exception as e:
            print(f"HTML生成失败: {str(e)}")
            return False
    
    def generate_from_template(self, template_content: str, context: Dict[str, Any], output_path: str) -> bool:
        """从模板生成HTML
        
        Args:
            template_content: 模板内容
            context: 模板上下文
            output_path: 输出文件路径
            
        Returns:
            是否生成成功
        """
        try:
            # 简单的模板变量替换
            html_content = template_content
            for key, value in context.items():
                placeholder = f'{{{{ {key} }}}}'
                html_content = html_content.replace(placeholder, str(value))
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"模板HTML生成失败: {str(e)}")
            return False
    
    def get_html_info(self, html_path: str) -> Dict[str, Any]:
        """获取HTML文件信息
        
        Args:
            html_path: HTML文件路径
            
        Returns:
            HTML文件信息
        """
        try:
            if os.path.exists(html_path):
                file_size = os.path.getsize(html_path)
                return {
                    'file_path': html_path,
                    'file_size': file_size,
                    'created_at': datetime.fromtimestamp(os.path.getctime(html_path)),
                    'modified_at': datetime.fromtimestamp(os.path.getmtime(html_path))
                }
            else:
                return {'error': 'HTML文件不存在'}
        except Exception as e:
            return {'error': f'获取HTML信息失败: {str(e)}'}