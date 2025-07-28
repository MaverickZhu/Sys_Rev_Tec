"""AI dependency injection module."""

from functools import lru_cache
from typing import Optional

from app.core.ai_config import AIConfig
from app.utils.ai_integration import AIIntegrationService
from app.utils.cache import CacheManager
from app.utils.knowledge_graph import KnowledgeGraphService
from app.utils.text_processing import TextProcessor
from app.utils.vector_service import VectorService


@lru_cache
def get_ai_config() -> AIConfig:
    """Get AI configuration instance."""
    return AIConfig()


def get_ai_integration_service() -> Optional[AIIntegrationService]:
    """Get AI integration service if enabled."""
    config = get_ai_config()
    if not config.AI_ENABLED:
        return None

    return AIIntegrationService()


def get_vector_service() -> Optional[VectorService]:
    """Get vector service if enabled."""
    config = get_ai_config()
    if not config.VECTOR_ENABLED:
        return None

    return VectorService()


def get_knowledge_graph_service() -> Optional[KnowledgeGraphService]:
    """Get knowledge graph service if enabled."""
    config = get_ai_config()
    if not config.KNOWLEDGE_GRAPH_ENABLED:
        return None

    return KnowledgeGraphService()


def get_cache_service() -> Optional[CacheManager]:
    """Get cache service if enabled."""
    config = get_ai_config()
    if not config.AI_CACHE_ENABLED:
        return None

    return CacheManager(default_ttl=config.AI_CACHE_TTL)


def get_text_processor() -> TextProcessor:
    """Get text processor instance."""
    return TextProcessor()


def is_ai_enabled() -> bool:
    """Check if AI features are enabled."""
    config = get_ai_config()
    return config.AI_ENABLED


def is_vectorization_enabled() -> bool:
    """Check if vectorization is enabled."""
    config = get_ai_config()
    return config.VECTOR_ENABLED and config.AI_ENABLED


def is_semantic_search_enabled() -> bool:
    """Check if semantic search is enabled."""
    config = get_ai_config()
    return config.SEARCH_ENABLED and config.VECTOR_ENABLED and config.AI_ENABLED


def is_knowledge_graph_enabled() -> bool:
    """Check if knowledge graph is enabled."""
    config = get_ai_config()
    return config.KNOWLEDGE_GRAPH_ENABLED and config.AI_ENABLED


def is_document_analysis_enabled() -> bool:
    """Check if document analysis is enabled."""
    config = get_ai_config()
    return config.DOCUMENT_ANALYSIS_ENABLED and config.AI_ENABLED


def is_risk_assessment_enabled() -> bool:
    """Check if risk assessment is enabled."""
    config = get_ai_config()
    return config.RISK_ASSESSMENT_ENABLED and config.AI_ENABLED


def is_compliance_analysis_enabled() -> bool:
    """Check if compliance analysis is enabled."""
    config = get_ai_config()
    return config.COMPLIANCE_ANALYSIS_ENABLED and config.AI_ENABLED


def get_ai_service_health() -> dict:
    """Get health status of all AI services."""
    config = get_ai_config()
    health = {
        "ai_enabled": config.AI_ENABLED,
        "vectorization_enabled": is_vectorization_enabled(),
        "semantic_search_enabled": is_semantic_search_enabled(),
        "knowledge_graph_enabled": is_knowledge_graph_enabled(),
        "document_analysis_enabled": is_document_analysis_enabled(),
        "risk_assessment_enabled": is_risk_assessment_enabled(),
        "compliance_analysis_enabled": is_compliance_analysis_enabled(),
        "services": {},
    }

    # Check individual services
    ai_service = get_ai_integration_service()
    if ai_service:
        health["services"]["ai_integration"] = "available"
    else:
        health["services"]["ai_integration"] = "disabled"

    vector_service = get_vector_service()
    if vector_service:
        health["services"]["vector_store"] = "available"
    else:
        health["services"]["vector_store"] = "disabled"

    kg_service = get_knowledge_graph_service()
    if kg_service:
        health["services"]["knowledge_graph"] = "available"
    else:
        health["services"]["knowledge_graph"] = "disabled"

    cache_service = get_cache_service()
    if cache_service:
        health["services"]["cache"] = "available"
    else:
        health["services"]["cache"] = "disabled"

    return health
