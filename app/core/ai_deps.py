# -*- coding: utf-8 -*-
"""
AI服务依赖注入模块
提供AI相关服务的依赖注入和生命周期管理
"""

from functools import lru_cache
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.ai_config import AIConfig, get_ai_config
from app.db.session import get_db
from app.utils.ai_integration import AIIntegrationService
from app.utils.vector_service import VectorService
from app.utils.knowledge_graph import KnowledgeGraphService
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_ai_integration_service(
    config: AIConfig = Depends(get_ai_config)
) -> AIIntegrationService:
    """获取AI集成服务实例"""
    try:
        service = AIIntegrationService(config)
        logger.info("AI集成服务初始化成功")
        return service
    except Exception as e:
        logger.error(f"AI集成服务初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI集成服务初始化失败"
        )


@lru_cache()
def get_vector_service(
    config: AIConfig = Depends(get_ai_config)
) -> VectorService:
    """获取向量服务实例"""
    try:
        service = VectorService(config)
        logger.info("向量服务初始化成功")
        return service
    except Exception as e:
        logger.error(f"向量服务初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="向量服务初始化失败"
        )


@lru_cache()
def get_knowledge_graph_service(
    config: AIConfig = Depends(get_ai_config),
    ai_service: AIIntegrationService = Depends(get_ai_integration_service)
) -> KnowledgeGraphService:
    """获取知识图谱服务实例"""
    try:
        service = KnowledgeGraphService(ai_service, config)
        logger.info("知识图谱服务初始化成功")
        return service
    except Exception as e:
        logger.error(f"知识图谱服务初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="知识图谱服务初始化失败"
        )


@lru_cache()
def get_cache_service() -> CacheManager:
    """获取缓存服务实例"""
    try:
        service = CacheManager()
        logger.info("缓存服务初始化成功")
        return service
    except Exception as e:
        logger.error(f"缓存服务初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="缓存服务初始化失败"
        )


@lru_cache()
def get_text_processor() -> TextProcessor:
    """获取文本处理器实例"""
    try:
        processor = TextProcessor()
        logger.info("文本处理器初始化成功")
        return processor
    except Exception as e:
        logger.error(f"文本处理器初始化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文本处理器初始化失败"
        )


def check_ai_enabled(
    config: AIConfig = Depends(get_ai_config)
) -> bool:
    """检查AI功能是否启用"""
    if not config.is_ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI功能未启用"
        )
    return True


def check_vector_enabled(
    config: AIConfig = Depends(get_ai_config)
) -> bool:
    """检查向量化功能是否启用"""
    if not config.is_vector_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="向量化功能未启用"
        )
    return True


def check_search_enabled(
    config: AIConfig = Depends(get_ai_config)
) -> bool:
    """检查搜索功能是否启用"""
    if not config.is_search_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="搜索功能未启用"
        )
    return True


def check_knowledge_graph_enabled(
    config: AIConfig = Depends(get_ai_config)
) -> bool:
    """检查知识图谱功能是否启用"""
    if not config.is_knowledge_graph_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="知识图谱功能未启用"
        )
    return True


def check_analysis_enabled(
    config: AIConfig = Depends(get_ai_config)
) -> bool:
    """检查文档分析功能是否启用"""
    if not config.is_analysis_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="文档分析功能未启用"
        )
    return True


class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self._ai_service: Optional[AIIntegrationService] = None
        self._vector_service: Optional[VectorService] = None
        self._kg_service: Optional[KnowledgeGraphService] = None
        self._cache_service: Optional[CacheManager] = None
        self._text_processor: Optional[TextProcessor] = None
        self._config: Optional[AIConfig] = None
    
    def initialize(
        self,
        config: AIConfig,
        db: Session
    ) -> None:
        """初始化所有AI服务"""
        try:
            self._config = config
            
            # 初始化基础服务
            self._cache_service = CacheManager()
            self._text_processor = TextProcessor()
            
            # 初始化AI集成服务
            if config.is_ai_enabled():
                self._ai_service = AIIntegrationService(config)
                
                # 初始化向量服务
                if config.is_vector_enabled():
                    self._vector_service = VectorService(config)
                
                # 初始化知识图谱服务
                if config.is_knowledge_graph_enabled():
                    self._kg_service = KnowledgeGraphService(
                        self._ai_service, config
                    )
            
            logger.info("AI服务管理器初始化完成")
            
        except Exception as e:
            logger.error(f"AI服务管理器初始化失败: {e}")
            raise
    
    def get_ai_service(self) -> AIIntegrationService:
        """获取AI集成服务"""
        if not self._ai_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI服务未初始化"
            )
        return self._ai_service
    
    def get_vector_service(self) -> VectorService:
        """获取向量服务"""
        if not self._vector_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="向量服务未初始化"
            )
        return self._vector_service
    
    def get_knowledge_graph_service(self) -> KnowledgeGraphService:
        """获取知识图谱服务"""
        if not self._kg_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="知识图谱服务未初始化"
            )
        return self._kg_service
    
    def get_cache_service(self) -> CacheManager:
        """获取缓存服务"""
        if not self._cache_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="缓存服务未初始化"
            )
        return self._cache_service
    
    def get_text_processor(self) -> TextProcessor:
        """获取文本处理器"""
        if not self._text_processor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="文本处理器未初始化"
            )
        return self._text_processor
    
    async def health_check(self) -> dict:
        """健康检查"""
        health_status = {
            "ai_service": False,
            "vector_service": False,
            "knowledge_graph_service": False,
            "cache_service": False,
            "text_processor": False,
        }
        
        try:
            # 检查AI服务
            if self._ai_service:
                health_status["ai_service"] = await self._ai_service.health_check()
            
            # 检查向量服务
            if self._vector_service:
                health_status["vector_service"] = await self._vector_service.health_check()
            
            # 检查知识图谱服务
            if self._kg_service:
                health_status["knowledge_graph_service"] = await self._kg_service.health_check()
            
            # 检查缓存服务
            if self._cache_service:
                health_status["cache_service"] = self._cache_service.health_check()
            
            # 检查文本处理器
            if self._text_processor:
                health_status["text_processor"] = True
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
        
        return health_status
    
    def shutdown(self) -> None:
        """关闭所有服务"""
        try:
            if self._vector_service:
                # 向量服务可能需要清理资源
                pass
            
            if self._cache_service:
                # 缓存服务可能需要清理资源
                pass
            
            logger.info("AI服务管理器已关闭")
            
        except Exception as e:
            logger.error(f"AI服务管理器关闭失败: {e}")


# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()


def get_ai_service_manager() -> AIServiceManager:
    """获取AI服务管理器实例"""
    return ai_service_manager


# 便捷的依赖注入函数
def get_ai_service(
    manager: AIServiceManager = Depends(get_ai_service_manager),
    _: bool = Depends(check_ai_enabled)
) -> AIIntegrationService:
    """获取AI集成服务（带启用检查）"""
    return manager.get_ai_service()


def get_vector_service_dep(
    manager: AIServiceManager = Depends(get_ai_service_manager),
    _: bool = Depends(check_vector_enabled)
) -> VectorService:
    """获取向量服务（带启用检查）"""
    return manager.get_vector_service()


def get_knowledge_graph_service_dep(
    manager: AIServiceManager = Depends(get_ai_service_manager),
    _: bool = Depends(check_knowledge_graph_enabled)
) -> KnowledgeGraphService:
    """获取知识图谱服务（带启用检查）"""
    return manager.get_knowledge_graph_service()


def get_cache_service_dep(
    manager: AIServiceManager = Depends(get_ai_service_manager)
) -> CacheManager:
    """获取缓存服务"""
    return manager.get_cache_service()


def get_text_processor_dep(
    manager: AIServiceManager = Depends(get_ai_service_manager)
) -> TextProcessor:
    """获取文本处理器"""
    return manager.get_text_processor()