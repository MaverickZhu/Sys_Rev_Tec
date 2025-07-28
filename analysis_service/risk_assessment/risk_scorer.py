# Risk Scorer
# 风险评分器 - 计算和量化风险评分

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .risk_models import RiskFactor, RiskLevel, RiskWeight

logger = logging.getLogger(__name__)

class RiskScorer:
    """风险评分器 - 负责计算各种风险评分"""
    
    def __init__(self, custom_weights: Optional[RiskWeight] = None):
        """初始化风险评分器
        
        Args:
            custom_weights: 自定义权重配置
        """
        self.weights = custom_weights or RiskWeight()
        self.scoring_methods = {
            'weighted_average': self._weighted_average_score,
            'max_risk': self._max_risk_score,
            'monte_carlo': self._monte_carlo_score,
            'fuzzy_logic': self._fuzzy_logic_score
        }
        
    def calculate_overall_score(self, 
                              risk_factors: List[RiskFactor], 
                              method: str = 'weighted_average') -> float:
        """计算总体风险评分
        
        Args:
            risk_factors: 风险因子列表
            method: 评分方法 ('weighted_average', 'max_risk', 'monte_carlo', 'fuzzy_logic')
            
        Returns:
            float: 总体风险评分 (0-1)
        """
        if not risk_factors:
            logger.warning("没有风险因子，返回默认评分0.5")
            return 0.5
        
        try:
            scoring_func = self.scoring_methods.get(method, self._weighted_average_score)
            score = scoring_func(risk_factors)
            
            # 确保评分在有效范围内
            score = max(0.0, min(1.0, score))
            
            logger.info(f"使用{method}方法计算总体风险评分: {score:.3f}")
            return score
            
        except Exception as e:
            logger.error(f"计算总体风险评分失败: {str(e)}")
            return 0.5
    
    def _weighted_average_score(self, risk_factors: List[RiskFactor]) -> float:
        """加权平均评分方法"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for factor in risk_factors:
            weight = factor.weight if factor.weight > 0 else self.weights.get_weight(factor.category)
            total_weighted_score += factor.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return total_weighted_score / total_weight
    
    def _max_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """最大风险评分方法 - 取最高风险因子的评分"""
        max_score = max(factor.score for factor in risk_factors)
        
        # 考虑其他风险因子的影响（降权）
        other_scores = [factor.score for factor in risk_factors if factor.score != max_score]
        if other_scores:
            avg_other = np.mean(other_scores)
            # 最大风险占80%，其他风险平均值占20%
            return max_score * 0.8 + avg_other * 0.2
        
        return max_score
    
    def _monte_carlo_score(self, risk_factors: List[RiskFactor], iterations: int = 1000) -> float:
        """蒙特卡洛模拟评分方法"""
        scores = []
        
        for _ in range(iterations):
            # 为每个风险因子生成随机变化
            simulation_score = 0.0
            total_weight = 0.0
            
            for factor in risk_factors:
                # 假设风险评分服从正态分布，标准差为评分的10%
                std_dev = factor.score * 0.1
                simulated_score = np.random.normal(factor.score, std_dev)
                simulated_score = max(0.0, min(1.0, simulated_score))
                
                weight = factor.weight if factor.weight > 0 else self.weights.get_weight(factor.category)
                simulation_score += simulated_score * weight
                total_weight += weight
            
            if total_weight > 0:
                scores.append(simulation_score / total_weight)
        
        return np.mean(scores) if scores else 0.5
    
    def _fuzzy_logic_score(self, risk_factors: List[RiskFactor]) -> float:
        """模糊逻辑评分方法"""
        # 简化的模糊逻辑实现
        low_membership = []
        medium_membership = []
        high_membership = []
        
        for factor in risk_factors:
            score = factor.score
            
            # 计算隶属度函数
            low_mem = max(0, min(1, (0.4 - score) / 0.4)) if score <= 0.4 else 0
            medium_mem = max(0, min(1, (score - 0.2) / 0.3)) if 0.2 <= score <= 0.5 else \
                        max(0, min(1, (0.8 - score) / 0.3)) if 0.5 < score <= 0.8 else 0
            high_mem = max(0, min(1, (score - 0.6) / 0.4)) if score >= 0.6 else 0
            
            low_membership.append(low_mem)
            medium_membership.append(medium_mem)
            high_membership.append(high_mem)
        
        # 聚合隶属度
        low_agg = max(low_membership) if low_membership else 0
        medium_agg = max(medium_membership) if medium_membership else 0
        high_agg = max(high_membership) if high_membership else 0
        
        # 去模糊化（重心法）
        numerator = low_agg * 0.2 + medium_agg * 0.5 + high_agg * 0.8
        denominator = low_agg + medium_agg + high_agg
        
        return numerator / denominator if denominator > 0 else 0.5
    
    def calculate_category_scores(self, risk_factors: List[RiskFactor]) -> Dict[str, float]:
        """计算各类别的风险评分
        
        Returns:
            Dict[str, float]: 各类别的风险评分
        """
        category_scores = {}
        category_factors = {}
        
        # 按类别分组
        for factor in risk_factors:
            category = factor.category
            if category not in category_factors:
                category_factors[category] = []
            category_factors[category].append(factor)
        
        # 计算各类别评分
        for category, factors in category_factors.items():
            if len(factors) == 1:
                category_scores[category] = factors[0].score
            else:
                # 多个因子取加权平均
                total_score = sum(f.score * f.weight for f in factors)
                total_weight = sum(f.weight for f in factors)
                category_scores[category] = total_score / total_weight if total_weight > 0 else 0.5
        
        return category_scores
    
    def calculate_risk_velocity(self, 
                              current_factors: List[RiskFactor],
                              previous_factors: List[RiskFactor]) -> float:
        """计算风险变化速度
        
        Args:
            current_factors: 当前风险因子
            previous_factors: 之前的风险因子
            
        Returns:
            float: 风险变化速度 (负值表示风险降低，正值表示风险增加)
        """
        current_score = self.calculate_overall_score(current_factors)
        previous_score = self.calculate_overall_score(previous_factors)
        
        return current_score - previous_score
    
    def calculate_confidence_score(self, risk_factors: List[RiskFactor]) -> float:
        """计算评分置信度
        
        Args:
            risk_factors: 风险因子列表
            
        Returns:
            float: 置信度评分 (0-1)
        """
        if not risk_factors:
            return 0.3
        
        confidence_factors = []
        
        for factor in risk_factors:
            # 基于证据数据的完整性
            evidence_score = 0.5
            if factor.evidence:
                evidence_count = len(factor.evidence)
                evidence_score = min(1.0, evidence_count / 5)  # 假设5个证据为满分
            
            # 基于描述的详细程度
            description_score = 0.5
            if factor.description:
                desc_length = len(factor.description)
                description_score = min(1.0, desc_length / 100)  # 假设100字符为满分
            
            # 基于权重的合理性
            weight_score = 1.0 if 0.05 <= factor.weight <= 0.5 else 0.7
            
            factor_confidence = (evidence_score * 0.4 + 
                               description_score * 0.3 + 
                               weight_score * 0.3)
            confidence_factors.append(factor_confidence)
        
        # 整体置信度
        base_confidence = np.mean(confidence_factors)
        
        # 基于风险因子数量的调整
        factor_count_bonus = min(0.2, len(risk_factors) / 10 * 0.2)
        
        total_confidence = base_confidence + factor_count_bonus
        return min(0.95, max(0.3, total_confidence))
    
    def calculate_impact_probability_score(self, 
                                         impact: float, 
                                         probability: float) -> float:
        """基于影响和概率计算风险评分
        
        Args:
            impact: 影响程度 (0-1)
            probability: 发生概率 (0-1)
            
        Returns:
            float: 风险评分
        """
        # 使用风险矩阵方法
        risk_score = impact * probability
        
        # 非线性调整，高影响高概率的风险应该被放大
        if impact > 0.7 and probability > 0.7:
            risk_score = min(1.0, risk_score * 1.2)
        elif impact > 0.8 or probability > 0.8:
            risk_score = min(1.0, risk_score * 1.1)
        
        return risk_score
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """标准化评分列表
        
        Args:
            scores: 原始评分列表
            
        Returns:
            List[float]: 标准化后的评分列表
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [0.5] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]
    
    def get_scoring_summary(self, risk_factors: List[RiskFactor]) -> Dict[str, any]:
        """获取评分摘要
        
        Returns:
            Dict: 包含各种评分方法结果的摘要
        """
        summary = {
            'factor_count': len(risk_factors),
            'scoring_methods': {}
        }
        
        # 计算各种方法的评分
        for method_name in self.scoring_methods.keys():
            try:
                score = self.calculate_overall_score(risk_factors, method_name)
                summary['scoring_methods'][method_name] = {
                    'score': score,
                    'risk_level': self._score_to_risk_level(score).value
                }
            except Exception as e:
                logger.warning(f"计算{method_name}评分失败: {str(e)}")
                summary['scoring_methods'][method_name] = {
                    'score': None,
                    'error': str(e)
                }
        
        # 添加类别评分
        summary['category_scores'] = self.calculate_category_scores(risk_factors)
        
        # 添加置信度
        summary['confidence'] = self.calculate_confidence_score(risk_factors)
        
        return summary
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """将评分转换为风险等级"""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW