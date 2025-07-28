# Risk Analyzer
# 风险分析器 - 核心风险评估逻辑

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass

from .risk_models import RiskFactor, RiskLevel
from .risk_scorer import RiskScorer

logger = logging.getLogger(__name__)

@dataclass
class RiskAssessmentResult:
    """风险评估结果"""
    project_id: str
    overall_score: float
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    assessment_time: datetime
    confidence: float

class RiskAnalyzer:
    """风险分析器 - 政府采购项目风险评估"""
    
    def __init__(self):
        self.scorer = RiskScorer()
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8,
            'critical': 1.0
        }
        
    def analyze_project_risk(self, project_data: Dict) -> RiskAssessmentResult:
        """分析项目风险
        
        Args:
            project_data: 项目数据字典
            
        Returns:
            RiskAssessmentResult: 风险评估结果
        """
        try:
            logger.info(f"开始分析项目风险: {project_data.get('project_id', 'Unknown')}")
            
            # 提取风险因子
            risk_factors = self._extract_risk_factors(project_data)
            
            # 计算风险评分
            overall_score = self.scorer.calculate_overall_score(risk_factors)
            
            # 确定风险等级
            risk_level = self._determine_risk_level(overall_score)
            
            # 生成建议
            recommendations = self._generate_recommendations(risk_factors, risk_level)
            
            # 计算置信度
            confidence = self._calculate_confidence(risk_factors)
            
            result = RiskAssessmentResult(
                project_id=project_data.get('project_id', ''),
                overall_score=overall_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                recommendations=recommendations,
                assessment_time=datetime.now(),
                confidence=confidence
            )
            
            logger.info(f"风险分析完成: 评分={overall_score:.2f}, 等级={risk_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"风险分析失败: {str(e)}")
            raise
    
    def _extract_risk_factors(self, project_data: Dict) -> List[RiskFactor]:
        """提取风险因子"""
        risk_factors = []
        
        # 1. 预算风险
        budget_risk = self._analyze_budget_risk(project_data)
        if budget_risk:
            risk_factors.append(budget_risk)
        
        # 2. 时间风险
        timeline_risk = self._analyze_timeline_risk(project_data)
        if timeline_risk:
            risk_factors.append(timeline_risk)
        
        # 3. 供应商风险
        vendor_risk = self._analyze_vendor_risk(project_data)
        if vendor_risk:
            risk_factors.append(vendor_risk)
        
        # 4. 合规风险
        compliance_risk = self._analyze_compliance_risk(project_data)
        if compliance_risk:
            risk_factors.append(compliance_risk)
        
        # 5. 技术风险
        technical_risk = self._analyze_technical_risk(project_data)
        if technical_risk:
            risk_factors.append(technical_risk)
        
        return risk_factors
    
    def _analyze_budget_risk(self, project_data: Dict) -> Optional[RiskFactor]:
        """分析预算风险"""
        try:
            budget = project_data.get('budget', 0)
            estimated_cost = project_data.get('estimated_cost', 0)
            
            if budget <= 0 or estimated_cost <= 0:
                return None
            
            # 计算预算偏差
            budget_variance = abs(budget - estimated_cost) / budget
            
            # 风险评分
            if budget_variance > 0.3:
                score = 0.9
                description = f"预算偏差过大: {budget_variance:.1%}"
            elif budget_variance > 0.15:
                score = 0.6
                description = f"预算偏差较大: {budget_variance:.1%}"
            elif budget_variance > 0.05:
                score = 0.3
                description = f"预算偏差适中: {budget_variance:.1%}"
            else:
                score = 0.1
                description = f"预算偏差较小: {budget_variance:.1%}"
            
            return RiskFactor(
                name="预算风险",
                category="财务",
                score=score,
                weight=0.25,
                description=description,
                evidence={"budget": budget, "estimated_cost": estimated_cost, "variance": budget_variance}
            )
            
        except Exception as e:
            logger.warning(f"预算风险分析失败: {str(e)}")
            return None
    
    def _analyze_timeline_risk(self, project_data: Dict) -> Optional[RiskFactor]:
        """分析时间风险"""
        try:
            start_date = project_data.get('start_date')
            end_date = project_data.get('end_date')
            
            if not start_date or not end_date:
                return None
            
            # 计算项目周期
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            duration_days = (end_date - start_date).days
            
            # 基于项目规模评估时间风险
            budget = project_data.get('budget', 0)
            
            # 预期时间（基于预算的经验公式）
            expected_days = max(30, min(365, budget / 100000 * 30))
            
            time_variance = abs(duration_days - expected_days) / expected_days
            
            if time_variance > 0.5:
                score = 0.8
                description = f"项目周期异常: {duration_days}天 (预期{expected_days:.0f}天)"
            elif time_variance > 0.3:
                score = 0.5
                description = f"项目周期偏长: {duration_days}天 (预期{expected_days:.0f}天)"
            else:
                score = 0.2
                description = f"项目周期合理: {duration_days}天"
            
            return RiskFactor(
                name="时间风险",
                category="进度",
                score=score,
                weight=0.2,
                description=description,
                evidence={"duration_days": duration_days, "expected_days": expected_days}
            )
            
        except Exception as e:
            logger.warning(f"时间风险分析失败: {str(e)}")
            return None
    
    def _analyze_vendor_risk(self, project_data: Dict) -> Optional[RiskFactor]:
        """分析供应商风险"""
        try:
            vendors = project_data.get('vendors', [])
            
            if not vendors:
                return RiskFactor(
                    name="供应商风险",
                    category="供应商",
                    score=0.7,
                    weight=0.2,
                    description="缺少供应商信息",
                    evidence={"vendor_count": 0}
                )
            
            vendor_count = len(vendors)
            
            # 分析供应商数量风险
            if vendor_count < 3:
                score = 0.6
                description = f"供应商数量不足: {vendor_count}家"
            elif vendor_count > 10:
                score = 0.4
                description = f"供应商数量过多: {vendor_count}家"
            else:
                score = 0.2
                description = f"供应商数量适中: {vendor_count}家"
            
            # 分析供应商资质
            qualified_vendors = sum(1 for v in vendors if v.get('qualified', False))
            qualification_rate = qualified_vendors / vendor_count if vendor_count > 0 else 0
            
            if qualification_rate < 0.5:
                score = max(score, 0.8)
                description += f", 资质合格率低: {qualification_rate:.1%}"
            
            return RiskFactor(
                name="供应商风险",
                category="供应商",
                score=score,
                weight=0.2,
                description=description,
                evidence={
                    "vendor_count": vendor_count,
                    "qualified_vendors": qualified_vendors,
                    "qualification_rate": qualification_rate
                }
            )
            
        except Exception as e:
            logger.warning(f"供应商风险分析失败: {str(e)}")
            return None
    
    def _analyze_compliance_risk(self, project_data: Dict) -> Optional[RiskFactor]:
        """分析合规风险"""
        try:
            # 检查必要文档
            required_docs = ['procurement_plan', 'budget_approval', 'technical_specs']
            available_docs = project_data.get('documents', [])
            
            missing_docs = [doc for doc in required_docs if doc not in available_docs]
            compliance_rate = (len(required_docs) - len(missing_docs)) / len(required_docs)
            
            if compliance_rate < 0.7:
                score = 0.9
                description = f"合规文档缺失严重: {len(missing_docs)}项"
            elif compliance_rate < 0.9:
                score = 0.5
                description = f"合规文档部分缺失: {len(missing_docs)}项"
            else:
                score = 0.1
                description = "合规文档完整"
            
            return RiskFactor(
                name="合规风险",
                category="合规",
                score=score,
                weight=0.25,
                description=description,
                evidence={
                    "required_docs": required_docs,
                    "missing_docs": missing_docs,
                    "compliance_rate": compliance_rate
                }
            )
            
        except Exception as e:
            logger.warning(f"合规风险分析失败: {str(e)}")
            return None
    
    def _analyze_technical_risk(self, project_data: Dict) -> Optional[RiskFactor]:
        """分析技术风险"""
        try:
            project_type = project_data.get('project_type', '').lower()
            complexity = project_data.get('complexity', 'medium').lower()
            
            # 基于项目类型和复杂度评估技术风险
            high_risk_types = ['software', 'it', 'system', 'network']
            is_high_risk_type = any(risk_type in project_type for risk_type in high_risk_types)
            
            base_score = 0.3
            if is_high_risk_type:
                base_score += 0.3
            
            if complexity == 'high':
                base_score += 0.3
            elif complexity == 'low':
                base_score -= 0.1
            
            score = min(0.9, max(0.1, base_score))
            
            description = f"技术风险评估: 类型={project_type}, 复杂度={complexity}"
            
            return RiskFactor(
                name="技术风险",
                category="技术",
                score=score,
                weight=0.1,
                description=description,
                evidence={
                    "project_type": project_type,
                    "complexity": complexity,
                    "is_high_risk_type": is_high_risk_type
                }
            )
            
        except Exception as e:
            logger.warning(f"技术风险分析失败: {str(e)}")
            return None
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """确定风险等级"""
        if score >= self.risk_thresholds['critical']:
            return RiskLevel.CRITICAL
        elif score >= self.risk_thresholds['high']:
            return RiskLevel.HIGH
        elif score >= self.risk_thresholds['medium']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor], risk_level: RiskLevel) -> List[str]:
        """生成风险缓解建议"""
        recommendations = []
        
        # 基于风险因子生成具体建议
        for factor in risk_factors:
            if factor.score > 0.6:
                if factor.category == "财务":
                    recommendations.append("建议重新评估项目预算，确保成本估算准确性")
                elif factor.category == "进度":
                    recommendations.append("建议制定详细的项目时间计划，设置关键里程碑")
                elif factor.category == "供应商":
                    recommendations.append("建议扩大供应商范围，加强资质审查")
                elif factor.category == "合规":
                    recommendations.append("建议补充完善相关合规文档")
                elif factor.category == "技术":
                    recommendations.append("建议进行技术可行性评估，制定风险应对方案")
        
        # 基于整体风险等级生成建议
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("项目风险极高，建议暂停项目并进行全面风险评估")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("项目风险较高，建议制定详细的风险缓解计划")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("项目风险适中，建议加强关键环节监控")
        
        return list(set(recommendations))  # 去重
    
    def _calculate_confidence(self, risk_factors: List[RiskFactor]) -> float:
        """计算评估置信度"""
        if not risk_factors:
            return 0.3
        
        # 基于风险因子的完整性和数据质量计算置信度
        data_completeness = len(risk_factors) / 5  # 假设最多5个风险因子
        
        # 基于证据数据的完整性
        evidence_scores = []
        for factor in risk_factors:
            evidence_count = len(factor.evidence) if factor.evidence else 0
            evidence_scores.append(min(1.0, evidence_count / 3))  # 假设每个因子最多3个证据
        
        evidence_completeness = np.mean(evidence_scores) if evidence_scores else 0.5
        
        # 综合置信度
        confidence = (data_completeness * 0.6 + evidence_completeness * 0.4)
        return min(0.95, max(0.3, confidence))