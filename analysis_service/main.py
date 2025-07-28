#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析服务主入口
政府采购项目智能分析引擎的核心服务

主要功能:
- 整合风险评估、合规检查、异常检测、智能报告四大模块
- 提供统一的分析API接口
- 支持批量分析和实时分析
- 提供分析结果缓存和历史记录
- 集成监控和日志系统

作者: AI开发团队
创建时间: 2025-07-28
版本: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入各个分析模块
from .risk_assessment.risk_analyzer import RiskAnalyzer
from .risk_assessment.risk_models import RiskLevel, RiskCategory, ProjectRiskProfile
from .compliance_check.compliance_engine import ComplianceEngine
from .compliance_check.compliance_models import ComplianceStatus, ComplianceReport
from .anomaly_detection.anomaly_detector import AnomalyDetector
from .anomaly_detection.anomaly_models import AnomalyType, AnomalyResult
from .intelligent_reporting.report_generator import ReportGenerator
from .intelligent_reporting.report_models import (
    ReportRequest, ReportResult, TemplateType, ReportFormat, ReportPriority
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="智能分析服务",
    description="政府采购项目智能分析引擎",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic模型定义
class AnalysisRequest(BaseModel):
    """分析请求模型"""
    project_id: int
    document_ids: List[int]
    analysis_types: List[str]  # ["risk", "compliance", "anomaly", "report"]
    options: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # "low", "normal", "high", "urgent"

class AnalysisResponse(BaseModel):
    """分析响应模型"""
    analysis_id: str
    status: str
    results: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class BatchAnalysisRequest(BaseModel):
    """批量分析请求模型"""
    requests: List[AnalysisRequest]
    batch_options: Optional[Dict[str, Any]] = None

class ReportGenerationRequest(BaseModel):
    """报告生成请求模型"""
    title: str
    project_id: int
    template_type: str
    format: str = "html"
    data: Dict[str, Any]
    created_by: str
    priority: str = "normal"

# 全局分析引擎实例
class AnalysisService:
    """智能分析服务核心类"""
    
    def __init__(self):
        """初始化分析服务"""
        self.risk_analyzer = RiskAnalyzer()
        self.compliance_engine = ComplianceEngine()
        self.anomaly_detector = AnomalyDetector()
        self.report_generator = ReportGenerator()
        
        # 分析历史记录
        self.analysis_history: Dict[str, AnalysisResponse] = {}
        
        logger.info("智能分析服务初始化完成")
    
    async def perform_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        执行综合分析
        
        Args:
            request: 分析请求
            
        Returns:
            AnalysisResponse: 分析结果
        """
        analysis_id = f"ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.project_id}"
        
        try:
            logger.info(f"开始执行分析: {analysis_id}")
            
            results = {}
            
            # 风险评估
            if "risk" in request.analysis_types:
                logger.info("执行风险评估分析")
                risk_result = await self._perform_risk_analysis(request)
                results["risk_assessment"] = risk_result
            
            # 合规检查
            if "compliance" in request.analysis_types:
                logger.info("执行合规检查分析")
                compliance_result = await self._perform_compliance_analysis(request)
                results["compliance_check"] = compliance_result
            
            # 异常检测
            if "anomaly" in request.analysis_types:
                logger.info("执行异常检测分析")
                anomaly_result = await self._perform_anomaly_analysis(request)
                results["anomaly_detection"] = anomaly_result
            
            # 创建响应
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                results=results,
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            # 保存到历史记录
            self.analysis_history[analysis_id] = response
            
            logger.info(f"分析完成: {analysis_id}")
            return response
            
        except Exception as e:
            logger.error(f"分析失败: {analysis_id}, 错误: {str(e)}")
            
            error_response = AnalysisResponse(
                analysis_id=analysis_id,
                status="failed",
                results={},
                created_at=datetime.now(),
                error_message=str(e)
            )
            
            self.analysis_history[analysis_id] = error_response
            return error_response
    
    async def _perform_risk_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """执行风险评估分析"""
        # 模拟项目数据
        project_data = {
            "project_id": request.project_id,
            "budget": 1000000,
            "duration_days": 180,
            "supplier_count": 5,
            "document_count": len(request.document_ids),
            "complexity_score": 0.7
        }
        
        # 执行风险分析
        risk_result = await self.risk_analyzer.analyze_project_risk(project_data)
        
        return {
            "overall_risk_level": risk_result.overall_risk_level.value,
            "risk_score": risk_result.risk_score,
            "risk_factors": [asdict(factor) for factor in risk_result.risk_factors],
            "recommendations": risk_result.recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _perform_compliance_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """执行合规检查分析"""
        # 模拟项目数据
        project_data = {
            "project_id": request.project_id,
            "documents": request.document_ids,
            "budget": 1000000,
            "procurement_method": "public_tender"
        }
        
        # 执行合规检查
        compliance_result = await self.compliance_engine.check_compliance(project_data)
        
        return {
            "overall_status": compliance_result.overall_status.value,
            "compliance_score": compliance_result.compliance_score,
            "violations": [asdict(violation) for violation in compliance_result.violations],
            "recommendations": compliance_result.recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def _perform_anomaly_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """执行异常检测分析"""
        # 模拟项目数据
        project_data = {
            "project_id": request.project_id,
            "documents": request.document_ids,
            "historical_data": [],
            "behavioral_patterns": {}
        }
        
        # 执行异常检测
        anomaly_results = await self.anomaly_detector.detect_anomalies(project_data)
        
        return {
            "anomaly_count": len(anomaly_results),
            "anomalies": [asdict(anomaly) for anomaly in anomaly_results],
            "risk_level": "medium" if anomaly_results else "low",
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def generate_report(self, request: ReportGenerationRequest) -> ReportResult:
        """
        生成智能报告
        
        Args:
            request: 报告生成请求
            
        Returns:
            ReportResult: 报告生成结果
        """
        # 转换为内部报告请求格式
        report_request = ReportRequest(
            title=request.title,
            project_id=request.project_id,
            template_type=TemplateType(request.template_type),
            format=ReportFormat(request.format),
            data=request.data,
            created_by=request.created_by,
            priority=ReportPriority(request.priority)
        )
        
        # 生成报告
        result = await self.report_generator.generate_report(report_request)
        
        return result
    
    async def batch_analysis(self, batch_request: BatchAnalysisRequest) -> List[AnalysisResponse]:
        """
        批量分析
        
        Args:
            batch_request: 批量分析请求
            
        Returns:
            List[AnalysisResponse]: 批量分析结果
        """
        logger.info(f"开始批量分析，共 {len(batch_request.requests)} 个请求")
        
        # 并发执行分析
        tasks = [self.perform_analysis(req) for req in batch_request.requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_response = AnalysisResponse(
                    analysis_id=f"BATCH_ERROR_{i}",
                    status="failed",
                    results={},
                    created_at=datetime.now(),
                    error_message=str(result)
                )
                processed_results.append(error_response)
            else:
                processed_results.append(result)
        
        logger.info(f"批量分析完成，成功 {len([r for r in processed_results if r.status == 'completed'])} 个")
        return processed_results
    
    def get_analysis_history(self, analysis_id: Optional[str] = None) -> Union[AnalysisResponse, List[AnalysisResponse]]:
        """
        获取分析历史记录
        
        Args:
            analysis_id: 分析ID，如果为None则返回所有记录
            
        Returns:
            分析记录或记录列表
        """
        if analysis_id:
            return self.analysis_history.get(analysis_id)
        else:
            return list(self.analysis_history.values())

# 创建全局服务实例
analysis_service = AnalysisService()

# API路由定义
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "智能分析服务",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "risk_analyzer": "active",
            "compliance_engine": "active",
            "anomaly_detector": "active",
            "report_generator": "active"
        }
    }

@app.post("/analysis", response_model=AnalysisResponse)
async def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    创建分析任务
    
    Args:
        request: 分析请求
        background_tasks: 后台任务
        
    Returns:
        AnalysisResponse: 分析结果
    """
    try:
        result = await analysis_service.perform_analysis(request)
        return result
    except Exception as e:
        logger.error(f"分析请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/batch", response_model=List[AnalysisResponse])
async def create_batch_analysis(request: BatchAnalysisRequest):
    """
    创建批量分析任务
    
    Args:
        request: 批量分析请求
        
    Returns:
        List[AnalysisResponse]: 批量分析结果
    """
    try:
        results = await analysis_service.batch_analysis(request)
        return results
    except Exception as e:
        logger.error(f"批量分析请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    """
    获取分析结果
    
    Args:
        analysis_id: 分析ID
        
    Returns:
        AnalysisResponse: 分析结果
    """
    result = analysis_service.get_analysis_history(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析记录未找到")
    return result

@app.get("/analysis", response_model=List[AnalysisResponse])
async def list_analyses():
    """
    获取所有分析记录
    
    Returns:
        List[AnalysisResponse]: 分析记录列表
    """
    return analysis_service.get_analysis_history()

@app.post("/reports/generate")
async def generate_report(request: ReportGenerationRequest):
    """
    生成智能报告
    
    Args:
        request: 报告生成请求
        
    Returns:
        报告生成结果
    """
    try:
        result = await analysis_service.generate_report(request)
        return {
            "report_id": result.metadata.report_id,
            "status": result.metadata.status.value,
            "title": result.metadata.title,
            "format": result.metadata.format.value,
            "created_at": result.metadata.created_at.isoformat(),
            "file_size": result.metadata.file_size,
            "summary": result.summary
        }
    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """
    获取服务统计信息
    
    Returns:
        统计信息
    """
    history = analysis_service.get_analysis_history()
    
    total_analyses = len(history)
    completed_analyses = len([h for h in history if h.status == "completed"])
    failed_analyses = len([h for h in history if h.status == "failed"])
    
    return {
        "total_analyses": total_analyses,
        "completed_analyses": completed_analyses,
        "failed_analyses": failed_analyses,
        "success_rate": completed_analyses / total_analyses if total_analyses > 0 else 0,
        "service_uptime": "运行中",
        "last_analysis": history[-1].created_at.isoformat() if history else None
    }

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )