"""报告生成API接口

提供报告生成的RESTful API端点
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .report_models import (
    ReportTemplate, ReportData, ReportConfig, ReportMetadata,
    ReportResult, ReportRequest, OutputFormat, ReportType
)
from .report_service import ReportService

# 创建路由器
router = APIRouter(prefix="/api/reports", tags=["reports"])

# 全局报告服务实例
report_service = None


def get_report_service() -> ReportService:
    """获取报告服务实例"""
    global report_service
    if report_service is None:
        # 使用相对于当前文件的路径
        current_dir = Path(__file__).parent
        template_dir = current_dir / "templates"
        output_dir = current_dir / "outputs"
        report_service = ReportService(
            template_dir=str(template_dir),
            output_dir=str(output_dir)
        )
    return report_service


# API模型定义
class ReportGenerationRequest(BaseModel):
    """报告生成请求模型"""
    template_id: str = Field(..., description="模板ID")
    report_type: ReportType = Field(..., description="报告类型")
    output_format: OutputFormat = Field(default=OutputFormat.HTML, description="输出格式")
    title: str = Field(..., description="报告标题")
    subtitle: Optional[str] = Field(None, description="报告副标题")
    author: str = Field(..., description="报告作者")
    department: Optional[str] = Field(None, description="部门")
    description: Optional[str] = Field(None, description="报告描述")
    data: Dict[str, Any] = Field(default_factory=dict, description="报告数据")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="自定义配置")


class ReportListResponse(BaseModel):
    """报告列表响应模型"""
    reports: List[Dict[str, Any]] = Field(..., description="报告列表")
    total: int = Field(..., description="总数量")


class TemplateListResponse(BaseModel):
    """模板列表响应模型"""
    templates: List[Dict[str, Any]] = Field(..., description="模板列表")
    total: int = Field(..., description="总数量")


class ReportStatusResponse(BaseModel):
    """报告状态响应模型"""
    report_id: str = Field(..., description="报告ID")
    status: str = Field(..., description="状态")
    progress: Optional[float] = Field(None, description="进度")
    message: Optional[str] = Field(None, description="状态消息")


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates():
    """获取可用模板列表"""
    try:
        service = get_report_service()
        templates = service.get_available_templates()
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """获取模板详情"""
    try:
        service = get_report_service()
        template = service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")
        
        return {
            "id": template.id,
            "name": template.name,
            "type": template.report_type.value,
            "description": template.description,
            "sections": [{
                "id": section.id,
                "title": section.title,
                "order": section.order,
                "show_in_toc": section.show_in_toc,
                "charts": [chart.dict() for chart in section.charts]
            } for section in template.sections],
            "variables": template.variables
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.post("/generate", response_model=ReportResult)
async def generate_report(request: ReportGenerationRequest, background_tasks: BackgroundTasks):
    """生成报告"""
    try:
        service = get_report_service()
        
        # 构建报告请求
        metadata = ReportMetadata(
            title=request.title,
            subtitle=request.subtitle,
            author=request.author,
            department=request.department,
            description=request.description,
            created_at=datetime.now(),
            version="1.0"
        )
        
        config = ReportConfig(
            template_id=request.template_id,
            output_format=request.output_format,
            **request.custom_config
        )
        
        # 如果没有提供数据，使用示例数据
        if not request.data:
            report_data = service.create_sample_data(request.report_type)
        else:
            report_data = ReportData(**request.data)
        
        report_request = ReportRequest(
            report_type=request.report_type,
            metadata=metadata,
            config=config,
            data=report_data
        )
        
        # 生成报告
        result = service.generate_report(report_request)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/", response_model=ReportListResponse)
async def list_reports():
    """获取报告列表"""
    try:
        service = get_report_service()
        reports = service.list_reports()
        return ReportListResponse(
            reports=reports,
            total=len(reports)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")


@router.get("/{report_id}")
async def get_report_info(report_id: str):
    """获取报告信息"""
    try:
        service = get_report_service()
        report_info = service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        return {
            "report_id": report_id,
            "title": report_info['request'].metadata.title,
            "type": report_info['request'].report_type.value,
            "format": report_info['request'].config.output_format.value,
            "generated_at": report_info['generated_at'],
            "file_path": report_info['output_path'],
            "file_exists": os.path.exists(report_info['output_path'])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告信息失败: {str(e)}")


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """下载报告文件"""
    try:
        service = get_report_service()
        report_info = service.get_report_info(report_id)
        if not report_info:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        file_path = report_info['output_path']
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="报告文件不存在")
        
        # 确定媒体类型
        file_ext = Path(file_path).suffix.lower()
        media_type = {
            '.pdf': 'application/pdf',
            '.html': 'text/html',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }.get(file_ext, 'application/octet-stream')
        
        filename = f"{report_info['request'].metadata.title}_{report_id[:8]}{file_ext}"
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """删除报告"""
    try:
        service = get_report_service()
        success = service.delete_report(report_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        return {"message": "报告删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")


@router.post("/sample-data/{report_type}")
async def get_sample_data(report_type: ReportType):
    """获取示例数据"""
    try:
        service = get_report_service()
        sample_data = service.create_sample_data(report_type)
        return sample_data.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取示例数据失败: {str(e)}")


@router.post("/validate")
async def validate_report_request(request: ReportGenerationRequest):
    """验证报告生成请求"""
    try:
        service = get_report_service()
        
        # 构建报告请求
        metadata = ReportMetadata(
            title=request.title,
            subtitle=request.subtitle,
            author=request.author,
            department=request.department,
            description=request.description,
            created_at=datetime.now(),
            version="1.0"
        )
        
        config = ReportConfig(
            template_id=request.template_id,
            output_format=request.output_format,
            **request.custom_config
        )
        
        report_data = ReportData(**request.data) if request.data else service.create_sample_data(request.report_type)
        
        report_request = ReportRequest(
            report_type=request.report_type,
            metadata=metadata,
            config=config,
            data=report_data
        )
        
        # 验证请求
        errors = service.validate_report_request(report_request)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证请求失败: {str(e)}")


@router.post("/templates/upload")
async def upload_template(file: UploadFile = File(...)):
    """上传自定义模板"""
    try:
        if not file.filename.endswith('.html'):
            raise HTTPException(status_code=400, detail="只支持HTML模板文件")
        
        service = get_report_service()
        template_path = Path(service.template_dir) / file.filename
        
        # 保存文件
        with open(template_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return {
            "message": "模板上传成功",
            "template_id": template_path.stem,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传模板失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        service = get_report_service()
        templates = service.get_available_templates()
        
        return {
            "status": "healthy",
            "service": "report_generation",
            "templates_count": len(templates),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "report_generation",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }