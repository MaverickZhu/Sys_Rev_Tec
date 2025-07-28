# Risk Models
# 风险模型定义 - 数据结构和枚举类型

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"
    
    @property
    def color(self) -> str:
        """获取风险等级对应的颜色"""
        color_map = {
            RiskLevel.LOW: "#28a745",      # 绿色
            RiskLevel.MEDIUM: "#ffc107",   # 黄色
            RiskLevel.HIGH: "#fd7e14",     # 橙色
            RiskLevel.CRITICAL: "#dc3545"  # 红色
        }
        return color_map[self]
    
    @property
    def priority(self) -> int:
        """获取风险等级优先级（数值越大优先级越高）"""
        priority_map = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return priority_map[self]

class RiskCategory(Enum):
    """风险类别枚举"""
    FINANCIAL = "财务风险"
    SCHEDULE = "进度风险"
    VENDOR = "供应商风险"
    COMPLIANCE = "合规风险"
    TECHNICAL = "技术风险"
    OPERATIONAL = "运营风险"
    LEGAL = "法律风险"
    MARKET = "市场风险"

@dataclass
class RiskFactor:
    """风险因子数据模型"""
    name: str                    # 风险因子名称
    category: str               # 风险类别
    score: float                # 风险评分 (0-1)
    weight: float               # 权重 (0-1)
    description: str            # 描述
    evidence: Optional[Dict[str, Any]] = None  # 证据数据
    mitigation: Optional[str] = None           # 缓解措施
    impact: Optional[str] = None               # 影响描述
    probability: Optional[float] = None        # 发生概率
    
    @property
    def weighted_score(self) -> float:
        """加权评分"""
        return self.score * self.weight
    
    @property
    def risk_level(self) -> RiskLevel:
        """基于评分确定风险等级"""
        if self.score >= 0.8:
            return RiskLevel.CRITICAL
        elif self.score >= 0.6:
            return RiskLevel.HIGH
        elif self.score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'category': self.category,
            'score': self.score,
            'weight': self.weight,
            'weighted_score': self.weighted_score,
            'description': self.description,
            'risk_level': self.risk_level.value,
            'evidence': self.evidence,
            'mitigation': self.mitigation,
            'impact': self.impact,
            'probability': self.probability
        }

@dataclass
class ProjectRiskProfile:
    """项目风险档案"""
    project_id: str
    project_name: str
    assessment_date: datetime
    overall_risk_score: float
    overall_risk_level: RiskLevel
    risk_factors: list[RiskFactor]
    recommendations: list[str]
    assessor: str
    confidence_level: float
    
    @property
    def high_risk_factors(self) -> list[RiskFactor]:
        """获取高风险因子"""
        return [factor for factor in self.risk_factors if factor.score >= 0.6]
    
    @property
    def critical_risk_factors(self) -> list[RiskFactor]:
        """获取极高风险因子"""
        return [factor for factor in self.risk_factors if factor.score >= 0.8]
    
    def get_factors_by_category(self, category: str) -> list[RiskFactor]:
        """按类别获取风险因子"""
        return [factor for factor in self.risk_factors if factor.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'assessment_date': self.assessment_date.isoformat(),
            'overall_risk_score': self.overall_risk_score,
            'overall_risk_level': self.overall_risk_level.value,
            'risk_factors': [factor.to_dict() for factor in self.risk_factors],
            'recommendations': self.recommendations,
            'assessor': self.assessor,
            'confidence_level': self.confidence_level,
            'high_risk_factors_count': len(self.high_risk_factors),
            'critical_risk_factors_count': len(self.critical_risk_factors)
        }

@dataclass
class RiskThreshold:
    """风险阈值配置"""
    low_threshold: float = 0.3
    medium_threshold: float = 0.6
    high_threshold: float = 0.8
    critical_threshold: float = 1.0
    
    def get_risk_level(self, score: float) -> RiskLevel:
        """根据评分获取风险等级"""
        if score >= self.critical_threshold:
            return RiskLevel.CRITICAL
        elif score >= self.high_threshold:
            return RiskLevel.HIGH
        elif score >= self.medium_threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

@dataclass
class RiskWeight:
    """风险权重配置"""
    financial: float = 0.25      # 财务风险权重
    schedule: float = 0.20       # 进度风险权重
    vendor: float = 0.20         # 供应商风险权重
    compliance: float = 0.25     # 合规风险权重
    technical: float = 0.10      # 技术风险权重
    
    def __post_init__(self):
        """验证权重总和"""
        total = self.financial + self.schedule + self.vendor + self.compliance + self.technical
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"权重总和必须为1.0，当前为{total}")
    
    def get_weight(self, category: str) -> float:
        """根据类别获取权重"""
        weight_map = {
            '财务': self.financial,
            '进度': self.schedule,
            '供应商': self.vendor,
            '合规': self.compliance,
            '技术': self.technical
        }
        return weight_map.get(category, 0.1)  # 默认权重0.1

class RiskTrend(Enum):
    """风险趋势枚举"""
    INCREASING = "上升"
    STABLE = "稳定"
    DECREASING = "下降"
    UNKNOWN = "未知"

@dataclass
class RiskHistoryPoint:
    """风险历史数据点"""
    date: datetime
    risk_score: float
    risk_level: RiskLevel
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'date': self.date.isoformat(),
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'notes': self.notes
        }

@dataclass
class RiskMetrics:
    """风险指标统计"""
    total_projects: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    average_risk_score: float
    
    @property
    def risk_distribution(self) -> Dict[str, float]:
        """风险分布百分比"""
        if self.total_projects == 0:
            return {level.value: 0.0 for level in RiskLevel}
        
        return {
            RiskLevel.LOW.value: self.low_risk_count / self.total_projects * 100,
            RiskLevel.MEDIUM.value: self.medium_risk_count / self.total_projects * 100,
            RiskLevel.HIGH.value: self.high_risk_count / self.total_projects * 100,
            RiskLevel.CRITICAL.value: self.critical_risk_count / self.total_projects * 100
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'total_projects': self.total_projects,
            'risk_counts': {
                'low': self.low_risk_count,
                'medium': self.medium_risk_count,
                'high': self.high_risk_count,
                'critical': self.critical_risk_count
            },
            'average_risk_score': self.average_risk_score,
            'risk_distribution': self.risk_distribution
        }