"""报告生成服务

整合模板引擎和各种格式生成器的主服务类
"""

import os
import uuid
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

from .report_models import (
    ReportTemplate, ReportData, ReportConfig, ReportMetadata,
    ReportResult, ReportRequest, OutputFormat, ReportType
)
from .template_engine import TemplateEngine
from .pdf_generator import PDFGenerator
from .html_generator import HTMLGenerator


class ReportService:
    """报告生成服务"""
    
    def __init__(self, template_dir: str = "templates", output_dir: str = "reports"):
        """初始化报告服务
        
        Args:
            template_dir: 模板文件目录
            output_dir: 报告输出目录
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # 确保目录存在
        os.makedirs(template_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化组件
        self.template_engine = TemplateEngine(template_dir)
        self.pdf_generator = PDFGenerator()
        self.html_generator = HTMLGenerator()
        
        # 内置模板
        self.built_in_templates = self._load_built_in_templates()
        
        # 报告缓存
        self.report_cache = {}
    
    def _load_built_in_templates(self) -> Dict[str, ReportTemplate]:
        """加载内置模板
        
        Returns:
            内置模板字典
        """
        templates = {}
        
        # 风险评估报告模板
        risk_template = ReportTemplate(
            id="risk_assessment_template",
            name="风险评估报告模板",
            report_type=ReportType.RISK_ASSESSMENT,
            description="标准风险评估报告模板",
            template_path="risk_assessment.html",
            sections=[
                {
                    "id": "executive_summary",
                    "title": "执行摘要",
                    "content": "本报告对项目 {{ data.project_info.name }} 进行了全面的风险评估分析。",
                    "order": 1,
                    "template": None,
                    "charts": [],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "risk_overview",
                    "title": "风险概览",
                    "content": "总体风险评分: {{ data.risk_assessment.overall_score | format_number }}\n\n风险等级: {{ calculate_risk_level(data.risk_assessment.overall_score) }}",
                    "order": 2,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "gauge",
                            "title": "总体风险评分",
                            "data_source": "risk_assessment.overall_score",
                            "width": 600,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "detailed_analysis",
                    "title": "详细分析",
                    "content": "{% for category, risks in data.risk_assessment.categories.items() %}\n### {{ category }}\n{% for risk in risks %}\n- {{ risk.name }}: {{ risk.score | format_number }} ({{ risk.level }})\n{% endfor %}\n{% endfor %}",
                    "order": 3,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "bar",
                            "title": "各类别风险分布",
                            "data_source": "risk_assessment.categories",
                            "width": 800,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "recommendations",
                    "title": "建议措施",
                    "content": "{% for rec in data.risk_assessment.recommendations %}\n{{ loop.index }}. {{ rec }}\n{% endfor %}",
                    "order": 4,
                    "template": None,
                    "charts": [],
                    "data": {},
                    "show_in_toc": True
                }
            ],
            styles={},
            variables={}
        )
        templates["risk_assessment"] = risk_template
        
        # 合规检查报告模板
        compliance_template = ReportTemplate(
            id="compliance_check_template",
            name="合规检查报告模板",
            report_type=ReportType.COMPLIANCE_CHECK,
            description="标准合规检查报告模板",
            template_path="compliance_check.html",
            sections=[
                {
                    "id": "compliance_summary",
                    "title": "合规性摘要",
                    "content": "合规性评分: {{ data.compliance_check.overall_score | format_percent }}\n\n合规状态: {{ get_compliance_status(data.compliance_check.overall_score) }}",
                    "order": 1,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "pie",
                            "title": "合规性分布",
                            "data_source": "compliance_check.distribution",
                            "width": 600,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "compliance_details",
                    "title": "详细检查结果",
                    "content": "{% for rule in data.compliance_check.rules %}\n### {{ rule.name }}\n状态: {{ rule.status }}\n描述: {{ rule.description }}\n\n{% endfor %}",
                    "order": 2,
                    "template": None,
                    "charts": [],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "issues_found",
                    "title": "发现的问题",
                    "content": "{% for issue in data.compliance_check.issues %}\n**{{ issue.severity }}**: {{ issue.description }}\n位置: {{ issue.location }}\n建议: {{ issue.recommendation }}\n\n{% endfor %}",
                    "order": 3,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "bar",
                            "title": "问题严重程度分布",
                            "data_source": "compliance_check.issue_severity",
                            "width": 800,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                }
            ],
            styles={},
            variables={}
        )
        templates["compliance_check"] = compliance_template
        
        # 综合报告模板
        comprehensive_template = ReportTemplate(
            id="comprehensive_template",
            name="综合报告模板",
            report_type=ReportType.COMPREHENSIVE,
            description="包含风险评估和合规检查的综合报告模板",
            template_path="comprehensive.html",
            sections=[
                {
                    "id": "project_overview",
                    "title": "项目概览",
                    "content": "项目名称: {{ data.project_info.name }}\n项目描述: {{ data.project_info.description }}\n分析时间: {{ now().strftime('%Y-%m-%d %H:%M') }}",
                    "order": 1,
                    "template": None,
                    "charts": [],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "risk_section",
                    "title": "风险评估",
                    "content": "总体风险评分: {{ data.risk_assessment.overall_score | format_number }}\n风险等级: {{ calculate_risk_level(data.risk_assessment.overall_score) }}",
                    "order": 2,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "gauge",
                            "title": "风险评分",
                            "data_source": "risk_assessment.overall_score",
                            "width": 600,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "compliance_section",
                    "title": "合规检查",
                    "content": "合规性评分: {{ data.compliance_check.overall_score | format_percent }}\n合规状态: {{ get_compliance_status(data.compliance_check.overall_score) }}",
                    "order": 3,
                    "template": None,
                    "charts": [
                        {
                            "chart_type": "pie",
                            "title": "合规性分布",
                            "data_source": "compliance_check.distribution",
                            "width": 600,
                            "height": 400
                        }
                    ],
                    "data": {},
                    "show_in_toc": True
                },
                {
                    "id": "summary_recommendations",
                    "title": "总结与建议",
                    "content": "基于风险评估和合规检查结果，我们提出以下建议:\n\n{% for rec in data.recommendations %}\n{{ loop.index }}. {{ rec }}\n{% endfor %}",
                    "order": 4,
                    "template": None,
                    "charts": [],
                    "data": {},
                    "show_in_toc": True
                }
            ],
            styles={},
            variables={}
        )
        templates["comprehensive"] = comprehensive_template
        
        return templates
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """获取可用模板列表
        
        Returns:
            模板信息列表
        """
        templates = []
        
        # 内置模板
        for template_id, template in self.built_in_templates.items():
            templates.append({
                'id': template.id,
                'name': template.name,
                'type': template.report_type.value,
                'description': template.description,
                'built_in': True
            })
        
        # 自定义模板（从文件系统加载）
        template_files = Path(self.template_dir).glob('*.html')
        for template_file in template_files:
            templates.append({
                'id': template_file.stem,
                'name': template_file.stem.replace('_', ' ').title(),
                'type': 'custom',
                'description': f'自定义模板: {template_file.name}',
                'built_in': False
            })
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """获取模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            模板对象或None
        """
        # 先查找内置模板
        if template_id in self.built_in_templates:
            return self.built_in_templates[template_id]
        
        # 查找自定义模板文件
        template_path = Path(self.template_dir) / f"{template_id}.html"
        if template_path.exists():
            # 创建简单的自定义模板对象
            return ReportTemplate(
                id=template_id,
                name=template_id.replace('_', ' ').title(),
                report_type=ReportType.CUSTOM,
                description=f"自定义模板: {template_id}",
                template_path=f"{template_id}.html",
                sections=[],
                styles={},
                variables={}
            )
        
        return None
    
    def validate_report_request(self, request: ReportRequest) -> List[str]:
        """验证报告生成请求
        
        Args:
            request: 报告请求
            
        Returns:
            错误信息列表
        """
        errors = []
        
        # 检查模板是否存在
        template = self.get_template(request.config.template_id)
        if not template:
            errors.append(f"模板不存在: {request.config.template_id}")
        
        # 检查输出路径
        if request.config.output_path:
            output_dir = os.path.dirname(request.config.output_path)
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"无法创建输出目录: {str(e)}")
        
        # 检查必要的数据字段
        if not request.metadata.title:
            errors.append("报告标题不能为空")
        
        if not request.metadata.author:
            errors.append("报告作者不能为空")
        
        return errors
    
    def generate_report(self, request: ReportRequest) -> ReportResult:
        """生成报告
        
        Args:
            request: 报告生成请求
            
        Returns:
            报告生成结果
        """
        start_time = time.time()
        report_id = str(uuid.uuid4())
        
        try:
            # 验证请求
            errors = self.validate_report_request(request)
            if errors:
                return ReportResult(
                    success=False,
                    report_id=report_id,
                    generation_time=time.time() - start_time,
                    metadata=request.metadata,
                    error_message="请求验证失败: " + "; ".join(errors)
                )
            
            # 获取模板
            template = self.get_template(request.config.template_id)
            if not template:
                return ReportResult(
                    success=False,
                    report_id=report_id,
                    generation_time=time.time() - start_time,
                    metadata=request.metadata,
                    error_message=f"模板不存在: {request.config.template_id}"
                )
            
            # 准备输出路径
            if request.config.output_path:
                output_path = request.config.output_path
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"report_{report_id[:8]}_{timestamp}.{request.config.output_format.value}"
                output_path = os.path.join(self.output_dir, filename)
            
            # 渲染报告内容
            if template.sections:
                # 使用模板章节
                rendered_content = self.template_engine.render_report(template, request.data)
                sections = [{
                    'id': section.id,
                    'title': section.title,
                    'content': self.template_engine.render_section(section, request.data),
                    'order': section.order,
                    'show_in_toc': section.show_in_toc,
                    'charts': [chart.dict() for chart in section.charts]
                } for section in template.sections]
            else:
                # 使用自定义模板
                context = {
                    'data': request.data.dict(),
                    'metadata': request.metadata.dict(),
                    'config': request.config.dict()
                }
                rendered_content = self.template_engine.render_template(template.template_path, context)
                sections = []
            
            # 根据输出格式生成报告
            success = False
            if request.config.output_format == OutputFormat.HTML:
                success = self.html_generator.generate_html(
                    rendered_content, request.config, request.metadata, sections, output_path
                )
            elif request.config.output_format == OutputFormat.PDF:
                success = self.pdf_generator.generate_pdf(
                    rendered_content, request.config, request.metadata, sections, output_path
                )
            else:
                return ReportResult(
                    success=False,
                    report_id=report_id,
                    generation_time=time.time() - start_time,
                    metadata=request.metadata,
                    error_message=f"不支持的输出格式: {request.config.output_format.value}"
                )
            
            if not success:
                return ReportResult(
                    success=False,
                    report_id=report_id,
                    generation_time=time.time() - start_time,
                    metadata=request.metadata,
                    error_message="报告生成失败"
                )
            
            # 获取文件信息
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            # 缓存报告信息
            self.report_cache[report_id] = {
                'request': request,
                'output_path': output_path,
                'generated_at': datetime.now()
            }
            
            return ReportResult(
                success=True,
                report_id=report_id,
                file_path=output_path,
                file_size=file_size,
                generation_time=time.time() - start_time,
                metadata=request.metadata
            )
            
        except Exception as e:
            return ReportResult(
                success=False,
                report_id=report_id,
                generation_time=time.time() - start_time,
                metadata=request.metadata,
                error_message=f"报告生成异常: {str(e)}"
            )
    
    def get_report_info(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告信息
        
        Args:
            report_id: 报告ID
            
        Returns:
            报告信息或None
        """
        return self.report_cache.get(report_id)
    
    def delete_report(self, report_id: str) -> bool:
        """删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否删除成功
        """
        try:
            report_info = self.report_cache.get(report_id)
            if report_info:
                output_path = report_info['output_path']
                if os.path.exists(output_path):
                    os.remove(output_path)
                del self.report_cache[report_id]
                return True
            return False
        except Exception:
            return False
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """列出所有报告
        
        Returns:
            报告列表
        """
        reports = []
        for report_id, info in self.report_cache.items():
            reports.append({
                'report_id': report_id,
                'title': info['request'].metadata.title,
                'type': info['request'].report_type.value,
                'format': info['request'].config.output_format.value,
                'generated_at': info['generated_at'],
                'file_path': info['output_path'],
                'file_exists': os.path.exists(info['output_path'])
            })
        return reports
    
    def create_sample_data(self, report_type: ReportType) -> ReportData:
        """创建示例数据
        
        Args:
            report_type: 报告类型
            
        Returns:
            示例报告数据
        """
        base_data = ReportData(
            project_info={
                'name': '示例项目',
                'description': '这是一个示例项目，用于演示报告生成功能',
                'version': '1.0.0',
                'start_date': '2024-01-01',
                'end_date': '2024-12-31'
            },
            statistics={
                'total_files': 150,
                'analyzed_files': 145,
                'issues_found': 12,
                'warnings': 8,
                'errors': 4
            }
        )
        
        if report_type in [ReportType.RISK_ASSESSMENT, ReportType.COMPREHENSIVE]:
            base_data.risk_assessment = {
                'overall_score': 75.5,
                'categories': {
                    '技术风险': [{'name': '技术债务', 'score': 80, 'level': '高'}],
                    '业务风险': [{'name': '市场变化', 'score': 60, 'level': '中'}],
                    '运营风险': [{'name': '人员流失', 'score': 40, 'level': '低'}]
                },
                'recommendations': [
                    '加强技术架构设计',
                    '建立风险监控机制',
                    '完善应急预案'
                ]
            }
        
        if report_type in [ReportType.COMPLIANCE_CHECK, ReportType.COMPREHENSIVE]:
            base_data.compliance_check = {
                'overall_score': 0.85,
                'distribution': {'合规': 85, '部分合规': 10, '不合规': 5},
                'rules': [
                    {'name': '数据安全规则', 'status': '通过', 'description': '数据加密符合要求'},
                    {'name': '访问控制规则', 'status': '警告', 'description': '部分权限配置需要优化'}
                ],
                'issues': [
                    {
                        'severity': '中等',
                        'description': '部分API缺少访问控制',
                        'location': '/api/user/info',
                        'recommendation': '添加身份验证中间件'
                    }
                ],
                'issue_severity': {'高': 2, '中': 5, '低': 5}
            }
        
        if report_type == ReportType.COMPREHENSIVE:
            base_data.custom_data['recommendations'] = [
                '优化系统架构设计',
                '加强安全防护措施',
                '建立持续监控机制',
                '完善文档管理流程'
            ]
        
        return base_data