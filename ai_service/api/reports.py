#!/usr/bin/env python3
"""
AI服务智能报告生成API路由
提供项目风险评估、合规性检查、异常检测和智能报告生成功能
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ai_service.utils.logging import StructuredLogger

logger = logging.getLogger(__name__)
structured_logger = StructuredLogger("api.reports")

# 创建路由器
router = APIRouter(prefix="/reports", tags=["reports"])


# 请求模型
class RiskAssessmentRequest(BaseModel):
    """风险评估请求"""
    
    project_id: str = Field(..., description="项目ID")
    document_ids: Optional[List[str]] = Field(default=None, description="文档ID列表")
    assessment_type: str = Field(default="comprehensive", description="评估类型")
    risk_categories: Optional[List[str]] = Field(default=None, description="风险类别")
    include_recommendations: bool = Field(default=True, description="是否包含建议")
    
    @validator("assessment_type")
    def validate_assessment_type(cls, v):
        allowed_types = ["comprehensive", "financial", "technical", "compliance", "operational"]
        if v not in allowed_types:
            raise ValueError(f"评估类型必须是以下之一: {allowed_types}")
        return v


class ComplianceCheckRequest(BaseModel):
    """合规性检查请求"""
    
    project_id: str = Field(..., description="项目ID")
    document_ids: Optional[List[str]] = Field(default=None, description="文档ID列表")
    compliance_standards: List[str] = Field(..., description="合规标准列表")
    check_level: str = Field(default="standard", description="检查级别")
    include_details: bool = Field(default=True, description="是否包含详细信息")
    
    @validator("check_level")
    def validate_check_level(cls, v):
        allowed_levels = ["basic", "standard", "strict"]
        if v not in allowed_levels:
            raise ValueError(f"检查级别必须是以下之一: {allowed_levels}")
        return v


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求"""
    
    project_id: str = Field(..., description="项目ID")
    document_ids: Optional[List[str]] = Field(default=None, description="文档ID列表")
    detection_types: List[str] = Field(default=["all"], description="检测类型")
    sensitivity: float = Field(default=0.7, description="敏感度", ge=0.1, le=1.0)
    include_context: bool = Field(default=True, description="是否包含上下文")
    
    @validator("detection_types")
    def validate_detection_types(cls, v):
        allowed_types = ["all", "financial", "technical", "timeline", "resource", "quality"]
        for detection_type in v:
            if detection_type not in allowed_types:
                raise ValueError(f"检测类型必须是以下之一: {allowed_types}")
        return v


class ReportGenerationRequest(BaseModel):
    """报告生成请求"""
    
    project_id: str = Field(..., description="项目ID")
    report_type: str = Field(..., description="报告类型")
    template_id: Optional[str] = Field(default=None, description="模板ID")
    sections: Optional[List[str]] = Field(default=None, description="报告章节")
    include_charts: bool = Field(default=True, description="是否包含图表")
    include_recommendations: bool = Field(default=True, description="是否包含建议")
    output_format: str = Field(default="markdown", description="输出格式")
    language: str = Field(default="zh-CN", description="报告语言")
    
    @validator("report_type")
    def validate_report_type(cls, v):
        allowed_types = [
            "executive_summary", "risk_assessment", "compliance_report", 
            "technical_review", "project_status", "comprehensive"
        ]
        if v not in allowed_types:
            raise ValueError(f"报告类型必须是以下之一: {allowed_types}")
        return v
    
    @validator("output_format")
    def validate_output_format(cls, v):
        allowed_formats = ["markdown", "html", "pdf", "docx", "json"]
        if v not in allowed_formats:
            raise ValueError(f"输出格式必须是以下之一: {allowed_formats}")
        return v


# 响应模型
class RiskItem(BaseModel):
    """风险项"""
    
    risk_id: str = Field(..., description="风险ID")
    category: str = Field(..., description="风险类别")
    title: str = Field(..., description="风险标题")
    description: str = Field(..., description="风险描述")
    severity: str = Field(..., description="严重程度")
    probability: float = Field(..., description="发生概率")
    impact: float = Field(..., description="影响程度")
    risk_score: float = Field(..., description="风险分数")
    source_documents: List[str] = Field(..., description="来源文档")
    recommendations: Optional[List[str]] = Field(default=None, description="建议措施")
    mitigation_strategies: Optional[List[str]] = Field(default=None, description="缓解策略")


class RiskAssessmentResponse(BaseModel):
    """风险评估响应"""
    
    project_id: str = Field(..., description="项目ID")
    assessment_type: str = Field(..., description="评估类型")
    overall_risk_level: str = Field(..., description="整体风险等级")
    overall_risk_score: float = Field(..., description="整体风险分数")
    risk_items: List[RiskItem] = Field(..., description="风险项列表")
    risk_distribution: Dict[str, int] = Field(..., description="风险分布")
    recommendations: List[str] = Field(..., description="总体建议")
    assessment_metadata: Dict[str, Any] = Field(..., description="评估元数据")
    processing_time: float = Field(..., description="处理时间")
    timestamp: datetime = Field(..., description="评估时间")


class ComplianceIssue(BaseModel):
    """合规问题"""
    
    issue_id: str = Field(..., description="问题ID")
    standard: str = Field(..., description="合规标准")
    requirement: str = Field(..., description="要求")
    status: str = Field(..., description="状态")
    severity: str = Field(..., description="严重程度")
    description: str = Field(..., description="问题描述")
    source_documents: List[str] = Field(..., description="来源文档")
    remediation_actions: Optional[List[str]] = Field(default=None, description="修复措施")


class ComplianceCheckResponse(BaseModel):
    """合规性检查响应"""
    
    project_id: str = Field(..., description="项目ID")
    compliance_standards: List[str] = Field(..., description="合规标准")
    overall_compliance_score: float = Field(..., description="整体合规分数")
    compliance_status: str = Field(..., description="合规状态")
    compliance_issues: List[ComplianceIssue] = Field(..., description="合规问题")
    compliance_summary: Dict[str, Any] = Field(..., description="合规摘要")
    recommendations: List[str] = Field(..., description="建议")
    processing_time: float = Field(..., description="处理时间")
    timestamp: datetime = Field(..., description="检查时间")


class AnomalyItem(BaseModel):
    """异常项"""
    
    anomaly_id: str = Field(..., description="异常ID")
    anomaly_type: str = Field(..., description="异常类型")
    title: str = Field(..., description="异常标题")
    description: str = Field(..., description="异常描述")
    severity: str = Field(..., description="严重程度")
    confidence: float = Field(..., description="置信度")
    source_documents: List[str] = Field(..., description="来源文档")
    context: Optional[str] = Field(default=None, description="上下文")
    suggested_actions: Optional[List[str]] = Field(default=None, description="建议措施")


class AnomalyDetectionResponse(BaseModel):
    """异常检测响应"""
    
    project_id: str = Field(..., description="项目ID")
    detection_types: List[str] = Field(..., description="检测类型")
    anomaly_count: int = Field(..., description="异常数量")
    anomaly_items: List[AnomalyItem] = Field(..., description="异常项列表")
    anomaly_distribution: Dict[str, int] = Field(..., description="异常分布")
    overall_health_score: float = Field(..., description="整体健康分数")
    recommendations: List[str] = Field(..., description="建议")
    processing_time: float = Field(..., description="处理时间")
    timestamp: datetime = Field(..., description="检测时间")


class ReportSection(BaseModel):
    """报告章节"""
    
    section_id: str = Field(..., description="章节ID")
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    charts: Optional[List[Dict[str, Any]]] = Field(default=None, description="图表数据")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="章节元数据")


class ReportGenerationResponse(BaseModel):
    """报告生成响应"""
    
    project_id: str = Field(..., description="项目ID")
    report_type: str = Field(..., description="报告类型")
    report_id: str = Field(..., description="报告ID")
    title: str = Field(..., description="报告标题")
    sections: List[ReportSection] = Field(..., description="报告章节")
    summary: str = Field(..., description="报告摘要")
    recommendations: List[str] = Field(..., description="建议")
    output_format: str = Field(..., description="输出格式")
    report_url: Optional[str] = Field(default=None, description="报告URL")
    metadata: Dict[str, Any] = Field(..., description="报告元数据")
    processing_time: float = Field(..., description="处理时间")
    timestamp: datetime = Field(..., description="生成时间")


# API端点
@router.post(
    "/risk-assessment",
    response_model=RiskAssessmentResponse,
    summary="项目风险评估",
    description="对项目进行智能风险评估，识别潜在风险并提供缓解建议",
)
async def assess_project_risks(request: RiskAssessmentRequest):
    """项目风险评估"""
    start_time = time.time()
    
    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/reports/risk-assessment",
            method="POST",
            request_data={
                "project_id": request.project_id,
                "assessment_type": request.assessment_type,
                "document_count": len(request.document_ids) if request.document_ids else 0,
            },
        )
        
        # 使用简化的风险评估逻辑
        from ai_service.services.risk_assessment import SimpleRiskAnalyzer, AuditConfig
        
        # 初始化审计器
        config = AuditConfig()
        analyzer = SimpleRiskAnalyzer(config)
        
        # 模拟项目数据（实际应从数据库获取）
        project_data = {
            "id": request.project_id,
            "name": f"项目_{request.project_id}",
            "budget": "1000000",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "project_code": "PROJ-2024-001",
        }
        
        # 模拟文档数据（实际应从数据库获取）
        documents_data = [
            {
                "id": "doc_001",
                "name": "项目计划书.pdf",
                "type": "项目计划书",
                "content": "项目描述内容，包含预算、时间安排等信息",
                "file_path": "/docs/项目计划书.pdf",
                "size": 1024000,
            },
            {
                "id": "doc_002", 
                "name": "预算表.xlsx",
                "type": "预算表",
                "content": "详细预算分解，包含各项费用明细",
                "file_path": "/docs/预算表.xlsx",
                "size": 512000,
            }
        ]
        
        # 执行项目审计
        project_audit = analyzer.analyze_project(project_data, documents_data)
        
        # 转换为API响应格式
        risk_items = []
        for doc_audit in project_audit.document_audits:
            for audit_result in doc_audit.audit_results:
                if audit_result.issues:
                    risk_items.append(RiskItem(
                        risk_id=f"RISK_{doc_audit.document_id}_{audit_result.category.value}",
                        category=audit_result.category.value,
                        title=f"{doc_audit.document_name} - {audit_result.category.value}问题",
                        description="; ".join(audit_result.issues),
                        severity=audit_result.risk_level.value,
                        probability=0.8 if audit_result.risk_level.value == "高" else 0.5,
                        impact=(100 - audit_result.score) / 100,
                        risk_score=(100 - audit_result.score) / 100,
                        source_documents=[doc_audit.document_id],
                        recommendations=audit_result.suggestions,
                    ))
        
        # 计算风险分布
        risk_distribution = {"高风险": 0, "中风险": 0, "低风险": 0}
        for item in risk_items:
            if item.severity == "高":
                risk_distribution["高风险"] += 1
            elif item.severity == "中":
                risk_distribution["中风险"] += 1
            else:
                risk_distribution["低风险"] += 1
        
        response = RiskAssessmentResponse(
            project_id=request.project_id,
            assessment_type=request.assessment_type,
            overall_risk_level=project_audit.overall_risk.value,
            overall_risk_score=project_audit.overall_score / 100,
            risk_items=risk_items,
            risk_distribution=risk_distribution,
            recommendations=project_audit.recommendations,
            assessment_metadata={"model_version": "简化版1.0", "confidence": 0.90},
            processing_time=time.time() - start_time,
            timestamp=datetime.now(),
        )
        
        # 记录响应
        structured_logger.log_response(
            endpoint="/reports/risk-assessment",
            status_code=200,
            response_data={"risk_count": len(response.risk_items)},
        )
        
        return response
        
    except Exception as e:
        logger.error(f"风险评估失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"风险评估失败: {str(e)}",
        )


@router.post(
    "/compliance-check",
    response_model=ComplianceCheckResponse,
    summary="合规性检查",
    description="对项目进行合规性检查，识别合规问题并提供修复建议",
)
async def check_compliance(request: ComplianceCheckRequest):
    """合规性检查"""
    start_time = time.time()
    
    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/reports/compliance-check",
            method="POST",
            request_data={
                "project_id": request.project_id,
                "standards": request.compliance_standards,
                "check_level": request.check_level,
            },
        )
        
        # 使用合规性检查服务
        from ai_service.services.compliance_checker.compliance_api import complianceAPI
        
        # 模拟获取项目文档数据（实际应从数据库获取）
        documents_data = [
            {
                "id": "doc_001",
                "filename": "项目计划书.pdf",
                "content": "项目描述内容，包含预算、时间安排、审批信息等",
                "size_mb": 1.0,
                "project_id": request.project_id,
                "upload_date": "2024-01-01"
            },
            {
                "id": "doc_002",
                "filename": "预算表.xlsx", 
                "content": "详细预算分解，包含各项费用明细，负责人：张三，联系方式：13800138000",
                "size_mb": 0.5,
                "project_id": request.project_id,
                "upload_date": "2024-01-02"
            }
        ]
        
        # 执行项目合规性检查
        compliance_report = await complianceAPI.check_project_compliance(documents_data)
        
        # 转换为API响应格式
        compliance_issues = []
        for doc_result in compliance_report.document_results:
            for check_result in doc_result.check_results:
                if not check_result.passed:
                    compliance_issues.append(ComplianceIssue(
                        issue_id=f"COMP_{doc_result.document_id}_{check_result.rule_id}",
                        standard=check_result.rule_name,
                        requirement=check_result.rule_name,
                        status="不合规",
                        severity="高" if check_result.score < 50 else "中",
                        description="; ".join(check_result.issues),
                        source_documents=[doc_result.document_id],
                        remediation_actions=check_result.recommendations,
                    ))
        
        # 确定合规状态
        if compliance_report.overall_score >= 90:
            compliance_status = "完全合规"
        elif compliance_report.overall_score >= 70:
            compliance_status = "基本合规"
        else:
            compliance_status = "不合规"
        
        response = ComplianceCheckResponse(
            project_id=request.project_id,
            compliance_standards=request.compliance_standards,
            overall_compliance_score=compliance_report.overall_score / 100,
            compliance_status=compliance_status,
            compliance_issues=compliance_issues,
            compliance_summary={
                "总文档数": compliance_report.total_documents,
                "合规文档数": compliance_report.compliant_documents,
                "不合规文档数": compliance_report.total_documents - compliance_report.compliant_documents,
                "检查规则数": compliance_report.total_rules_checked,
                "通过规则数": compliance_report.total_rules_passed
            },
            recommendations=compliance_report.recommendations,
            processing_time=time.time() - start_time,
            timestamp=datetime.now(),
        )
        
        # 记录响应
        structured_logger.log_response(
            endpoint="/reports/compliance-check",
            status_code=200,
            response_data={"issue_count": len(response.compliance_issues)},
        )
        
        return response
        
    except Exception as e:
        logger.error(f"合规性检查失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合规性检查失败: {str(e)}",
        )


@router.post(
    "/anomaly-detection",
    response_model=AnomalyDetectionResponse,
    summary="异常检测",
    description="检测项目中的异常模式和潜在问题",
)
async def detect_anomalies(request: AnomalyDetectionRequest):
    """异常检测"""
    start_time = time.time()
    
    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/reports/anomaly-detection",
            method="POST",
            request_data={
                "project_id": request.project_id,
                "detection_types": request.detection_types,
                "sensitivity": request.sensitivity,
            },
        )
        
        # TODO: 实现异常检测逻辑
        # 1. 加载异常检测模型
        # 2. 分析项目数据
        # 3. 识别异常模式
        # 4. 计算异常分数
        # 5. 生成建议措施
        
        # 模拟响应（待实现）
        response = AnomalyDetectionResponse(
            project_id=request.project_id,
            detection_types=request.detection_types,
            anomaly_count=2,
            anomaly_items=[
                AnomalyItem(
                    anomaly_id="ANOM_001",
                    type="timeline",
                    title="项目进度异常",
                    description="项目进度明显滞后于计划",
                    severity="中等",
                    confidence=0.85,
                    source_documents=["timeline_doc_001"],
                    context="第三季度进度报告",
                    suggested_actions=["重新评估时间线", "增加资源投入"],
                )
            ],
            anomaly_distribution={"高异常": 0, "中异常": 2, "低异常": 1},
            overall_health_score=0.72,
            recommendations=["关注项目进度", "加强质量控制"],
            processing_time=time.time() - start_time,
            timestamp=datetime.now(),
        )
        
        # 记录响应
        structured_logger.log_response(
            endpoint="/reports/anomaly-detection",
            status_code=200,
            response_data={"anomaly_count": response.anomaly_count},
        )
        
        return response
        
    except Exception as e:
        logger.error(f"异常检测失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"异常检测失败: {str(e)}",
        )


@router.post(
    "/generate",
    response_model=ReportGenerationResponse,
    summary="智能报告生成",
    description="基于项目数据生成智能分析报告",
)
async def generate_report(request: ReportGenerationRequest):
    """智能报告生成"""
    start_time = time.time()
    
    try:
        # 记录请求
        structured_logger.log_request(
            endpoint="/reports/generate",
            method="POST",
            request_data={
                "project_id": request.project_id,
                "report_type": request.report_type,
                "output_format": request.output_format,
            },
        )
        
        # 使用新的智能报告生成服务
        from ai_service.services.report_generation.report_service import ReportService
        from ai_service.services.report_generation.report_models import (
            ReportRequest, ReportType, OutputFormat
        )
        
        # 初始化报告服务
        report_service = ReportService()
        
        # 转换请求格式
        report_type_mapping = {
            "executive_summary": ReportType.EXECUTIVE_SUMMARY,
            "risk_assessment": ReportType.RISK_ASSESSMENT,
            "compliance_report": ReportType.COMPLIANCE_CHECK,
            "technical_review": ReportType.TECHNICAL_REVIEW,
            "project_status": ReportType.PROJECT_STATUS,
            "comprehensive": ReportType.COMPREHENSIVE
        }
        
        output_format_mapping = {
            "html": OutputFormat.HTML,
            "pdf": OutputFormat.PDF,
            "markdown": OutputFormat.HTML,  # 默认使用HTML
            "docx": OutputFormat.WORD,
            "json": OutputFormat.HTML  # 默认使用HTML
        }
        
        # 创建报告请求
        report_req = ReportRequest(
            template_type=report_type_mapping.get(request.report_type, ReportType.COMPREHENSIVE),
            output_format=output_format_mapping.get(request.output_format, OutputFormat.HTML),
            project_id=request.project_id,
            title=f"项目{request.project_id}智能分析报告",
            author="AI报告生成系统",
            department="系统评审技术平台"
        )
        
        # 生成报告
        report_result = await report_service.generate_report(report_req)
        
        # 转换为API响应格式
        sections = []
        for section in report_result.sections:
            sections.append(ReportSection(
                section_id=section.id,
                title=section.title,
                content=section.content,
                charts=section.charts if hasattr(section, 'charts') else None,
                metadata=section.metadata if hasattr(section, 'metadata') else None
            ))
        
        response = ReportGenerationResponse(
            project_id=request.project_id,
            report_type=request.report_type,
            report_id=report_result.report_id,
            title=report_result.title,
            sections=sections,
            summary=report_result.summary,
            recommendations=report_result.recommendations,
            output_format=request.output_format,
            report_url=f"/reports/download/{report_result.report_id}",
            metadata={
                "template_version": "2.0",
                "generation_model": "智能报告生成系统",
                "language": request.language,
                "file_path": report_result.file_path,
                "file_size": report_result.file_size
            },
            processing_time=time.time() - start_time,
            timestamp=datetime.now(),
        )
        
        # 记录响应
        structured_logger.log_response(
            endpoint="/reports/generate",
            status_code=200,
            response_data={"report_id": response.report_id},
        )
        
        return response
        
    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}",
        )


@router.get(
    "/templates",
    summary="获取报告模板列表",
    description="获取可用的报告模板列表",
)
async def get_report_templates():
    """获取报告模板列表"""
    try:
        # 使用新的报告生成服务获取模板列表
        from ai_service.services.report_generation.report_service import ReportService
        
        report_service = ReportService()
        templates = report_service.get_available_templates()
        
        # 转换为API响应格式
        template_list = []
        for template_id, template in templates.items():
            template_list.append({
                "template_id": template_id,
                "name": template.name,
                "description": template.description,
                "sections": [section.title for section in template.sections],
                "charts": [chart.title for chart in template.charts] if template.charts else [],
                "output_formats": ["HTML", "PDF"],
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None
            })
        
        return {
            "templates": template_list,
            "total_count": len(template_list),
            "timestamp": datetime.now(),
        }
        
    except Exception as e:
        logger.error(f"获取报告模板失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告模板失败: {str(e)}",
        )


@router.get(
    "/list",
    summary="获取报告列表",
    description="获取已生成的报告列表",
)
async def list_reports(skip: int = 0, limit: int = 20):
    """获取报告列表"""
    try:
        from ai_service.services.report_generation.report_service import ReportService
        
        report_service = ReportService()
        reports = report_service.list_reports(skip=skip, limit=limit)
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "skip": skip,
            "limit": limit,
            "timestamp": datetime.now(),
        }
        
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告列表失败: {str(e)}",
        )


@router.get(
    "/status/{report_id}",
    summary="获取报告详情",
    description="获取指定报告的详细信息",
)
async def get_report_details(report_id: str):
    """获取报告详情"""
    try:
        from ai_service.services.report_generation.report_service import ReportService
        
        report_service = ReportService()
        report_info = report_service.get_report_info(report_id)
        
        if not report_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告 {report_id} 不存在",
            )
        
        return report_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取报告详情失败: {str(e)}",
        )


@router.get(
    "/download/{report_id}",
    summary="下载报告文件",
    description="下载指定的报告文件",
)
async def download_report(report_id: str):
    """下载报告文件"""
    try:
        from ai_service.services.report_generation.report_service import ReportService
        from fastapi.responses import FileResponse
        import os
        
        report_service = ReportService()
        report_info = report_service.get_report_info(report_id)
        
        if not report_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告 {report_id} 不存在",
            )
        
        file_path = report_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告文件不存在",
            )
        
        # 确定文件类型和媒体类型
        if file_path.endswith('.pdf'):
            media_type = 'application/pdf'
        elif file_path.endswith('.html'):
            media_type = 'text/html'
        else:
            media_type = 'application/octet-stream'
        
        filename = f"report_{report_id}.{file_path.split('.')[-1]}"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载报告失败: {str(e)}",
        )


@router.delete(
    "/{report_id}",
    summary="删除报告",
    description="删除指定的报告及其文件",
)
async def delete_report(report_id: str):
    """删除报告"""
    try:
        from ai_service.services.report_generation.report_service import ReportService
        
        report_service = ReportService()
        success = report_service.delete_report(report_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"报告 {report_id} 不存在",
            )
        
        return {
            "message": f"报告 {report_id} 已成功删除",
            "report_id": report_id,
            "timestamp": datetime.now(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除报告失败: {str(e)}",
        )