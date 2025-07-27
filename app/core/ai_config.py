# -*- coding: utf-8 -*-
"""
AI集成配置模块
提供AI服务的配置管理，包括向量化、LLM、知识图谱等功能的配置
"""

import os
from typing import Dict, List, Optional, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """AI集成配置类"""
    
    model_config = {"extra": "allow"}
    
    # === 基础配置 ===
    AI_ENABLED: bool = Field(default=True, description="是否启用AI功能")
    AI_SERVICE_URL: Optional[str] = Field(default=None, description="AI服务URL")
    AI_API_TIMEOUT: int = Field(default=30, description="AI API超时时间(秒)")
    AI_MAX_RETRIES: int = Field(default=3, description="AI API最大重试次数")
    
    # === 向量化配置 ===
    VECTOR_ENABLED: bool = Field(default=True, description="是否启用向量化功能")
    VECTOR_MODEL: str = Field(default="text-embedding-ada-002", description="默认向量化模型")
    VECTOR_DIMENSION: int = Field(default=1536, description="向量维度")
    VECTOR_CHUNK_SIZE: int = Field(default=1000, description="文档分块大小")
    VECTOR_CHUNK_OVERLAP: int = Field(default=200, description="分块重叠大小")
    VECTOR_BATCH_SIZE: int = Field(default=10, description="向量化批处理大小")
    
    # === OpenAI配置 ===
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API密钥")
    OPENAI_API_BASE: Optional[str] = Field(default=None, description="OpenAI API基础URL")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI模型")
    OPENAI_MAX_TOKENS: int = Field(default=4000, description="OpenAI最大令牌数")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="OpenAI温度参数")
    
    # === Azure OpenAI配置 ===
    AZURE_OPENAI_ENABLED: bool = Field(default=False, description="是否启用Azure OpenAI")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, description="Azure OpenAI API密钥")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, description="Azure OpenAI端点")
    AZURE_OPENAI_API_VERSION: str = Field(default="2023-12-01-preview", description="Azure OpenAI API版本")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = Field(default=None, description="Azure OpenAI部署名称")
    
    # === Ollama配置 ===
    OLLAMA_ENABLED: bool = Field(default=False, description="是否启用Ollama")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama基础URL")
    OLLAMA_MODEL: str = Field(default="llama2", description="Ollama模型")
    OLLAMA_EMBEDDING_MODEL: str = Field(default="nomic-embed-text", description="Ollama嵌入模型")
    
    # === HuggingFace配置 ===
    HUGGINGFACE_ENABLED: bool = Field(default=False, description="是否启用HuggingFace")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API密钥")
    HUGGINGFACE_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="HuggingFace模型")
    
    # === 向量存储配置 ===
    VECTOR_STORE_TYPE: str = Field(default="memory", description="向量存储类型: memory, chroma, pinecone, weaviate")
    
    # Chroma配置
    CHROMA_ENABLED: bool = Field(default=False, description="是否启用Chroma")
    CHROMA_HOST: str = Field(default="localhost", description="Chroma主机")
    CHROMA_PORT: int = Field(default=8000, description="Chroma端口")
    CHROMA_COLLECTION_NAME: str = Field(default="documents", description="Chroma集合名称")
    
    # Pinecone配置
    PINECONE_ENABLED: bool = Field(default=False, description="是否启用Pinecone")
    PINECONE_API_KEY: Optional[str] = Field(default=None, description="Pinecone API密钥")
    PINECONE_ENVIRONMENT: Optional[str] = Field(default=None, description="Pinecone环境")
    PINECONE_INDEX_NAME: str = Field(default="documents", description="Pinecone索引名称")
    
    # Weaviate配置
    WEAVIATE_ENABLED: bool = Field(default=False, description="是否启用Weaviate")
    WEAVIATE_URL: str = Field(default="http://localhost:8080", description="Weaviate URL")
    WEAVIATE_API_KEY: Optional[str] = Field(default=None, description="Weaviate API密钥")
    WEAVIATE_CLASS_NAME: str = Field(default="Document", description="Weaviate类名")
    
    # === 语义搜索配置 ===
    SEARCH_ENABLED: bool = Field(default=True, description="是否启用语义搜索")
    SEARCH_TOP_K: int = Field(default=10, description="搜索返回的最大结果数")
    SEARCH_SIMILARITY_THRESHOLD: float = Field(default=0.7, description="搜索相似度阈值")
    SEARCH_RERANK_ENABLED: bool = Field(default=False, description="是否启用搜索重排序")
    
    # === 知识图谱配置 ===
    KNOWLEDGE_GRAPH_ENABLED: bool = Field(default=True, description="是否启用知识图谱")
    ENTITY_EXTRACTION_MODEL: str = Field(default="gpt-3.5-turbo", description="实体提取模型")
    RELATION_EXTRACTION_MODEL: str = Field(default="gpt-3.5-turbo", description="关系提取模型")
    ENTITY_CONFIDENCE_THRESHOLD: float = Field(default=0.8, description="实体置信度阈值")
    RELATION_CONFIDENCE_THRESHOLD: float = Field(default=0.7, description="关系置信度阈值")
    
    # === 文档分析配置 ===
    DOCUMENT_ANALYSIS_ENABLED: bool = Field(default=True, description="是否启用文档分析")
    SUMMARY_MAX_LENGTH: int = Field(default=500, description="摘要最大长度")
    KEYWORDS_MAX_COUNT: int = Field(default=20, description="关键词最大数量")
    CLASSIFICATION_CATEGORIES: List[str] = Field(
        default=[
            "技术文档", "商务文档", "法律文档", "财务文档", 
            "管理文档", "合同文档", "报告文档", "其他"
        ],
        description="文档分类类别"
    )
    
    # === 风险评估配置 ===
    RISK_ASSESSMENT_ENABLED: bool = Field(default=True, description="是否启用风险评估")
    RISK_LEVELS: List[str] = Field(
        default=["低风险", "中风险", "高风险", "极高风险"],
        description="风险等级"
    )
    RISK_FACTORS: List[str] = Field(
        default=[
            "技术风险", "商务风险", "法律风险", "财务风险",
            "时间风险", "质量风险", "安全风险", "合规风险"
        ],
        description="风险因素"
    )
    
    # === 合规性分析配置 ===
    COMPLIANCE_ANALYSIS_ENABLED: bool = Field(default=True, description="是否启用合规性分析")
    COMPLIANCE_RULES_PATH: Optional[str] = Field(default=None, description="合规规则文件路径")
    COMPLIANCE_THRESHOLD: float = Field(default=0.8, description="合规性阈值")
    
    # === 缓存配置 ===
    AI_CACHE_ENABLED: bool = Field(default=True, description="是否启用AI缓存")
    AI_CACHE_TTL: int = Field(default=3600, description="AI缓存过期时间(秒)")
    AI_CACHE_MAX_SIZE: int = Field(default=1000, description="AI缓存最大条目数")
    
    # === 监控配置 ===
    AI_MONITORING_ENABLED: bool = Field(default=True, description="是否启用AI监控")
    AI_METRICS_ENABLED: bool = Field(default=True, description="是否启用AI指标")
    AI_LOGGING_LEVEL: str = Field(default="INFO", description="AI日志级别")
    
    # === 性能配置 ===
    AI_WORKER_COUNT: int = Field(default=4, description="AI工作进程数")
    AI_QUEUE_SIZE: int = Field(default=100, description="AI任务队列大小")
    AI_BATCH_PROCESSING: bool = Field(default=True, description="是否启用批处理")
    


    def get_vector_config(self) -> Dict[str, Any]:
        """获取向量化配置"""
        return {
            "enabled": self.VECTOR_ENABLED,
            "model": self.VECTOR_MODEL,
            "dimension": self.VECTOR_DIMENSION,
            "chunk_size": self.VECTOR_CHUNK_SIZE,
            "chunk_overlap": self.VECTOR_CHUNK_OVERLAP,
            "batch_size": self.VECTOR_BATCH_SIZE,
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        config = {
            "openai": {
                "enabled": bool(self.OPENAI_API_KEY),
                "api_key": self.OPENAI_API_KEY,
                "api_base": self.OPENAI_API_BASE,
                "model": self.OPENAI_MODEL,
                "max_tokens": self.OPENAI_MAX_TOKENS,
                "temperature": self.OPENAI_TEMPERATURE,
            },
            "azure_openai": {
                "enabled": self.AZURE_OPENAI_ENABLED,
                "api_key": self.AZURE_OPENAI_API_KEY,
                "endpoint": self.AZURE_OPENAI_ENDPOINT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
                "deployment_name": self.AZURE_OPENAI_DEPLOYMENT_NAME,
            },
            "ollama": {
                "enabled": self.OLLAMA_ENABLED,
                "base_url": self.OLLAMA_BASE_URL,
                "model": self.OLLAMA_MODEL,
                "embedding_model": self.OLLAMA_EMBEDDING_MODEL,
            },
        }
        return config
    
    def get_vector_store_config(self) -> Dict[str, Any]:
        """获取向量存储配置"""
        config = {
            "type": self.VECTOR_STORE_TYPE,
            "chroma": {
                "enabled": self.CHROMA_ENABLED,
                "host": self.CHROMA_HOST,
                "port": self.CHROMA_PORT,
                "collection_name": self.CHROMA_COLLECTION_NAME,
            },
            "pinecone": {
                "enabled": self.PINECONE_ENABLED,
                "api_key": self.PINECONE_API_KEY,
                "environment": self.PINECONE_ENVIRONMENT,
                "index_name": self.PINECONE_INDEX_NAME,
            },
            "weaviate": {
                "enabled": self.WEAVIATE_ENABLED,
                "url": self.WEAVIATE_URL,
                "api_key": self.WEAVIATE_API_KEY,
                "class_name": self.WEAVIATE_CLASS_NAME,
            },
        }
        return config
    
    def get_search_config(self) -> Dict[str, Any]:
        """获取搜索配置"""
        return {
            "enabled": self.SEARCH_ENABLED,
            "top_k": self.SEARCH_TOP_K,
            "similarity_threshold": self.SEARCH_SIMILARITY_THRESHOLD,
            "rerank_enabled": self.SEARCH_RERANK_ENABLED,
        }
    
    def get_knowledge_graph_config(self) -> Dict[str, Any]:
        """获取知识图谱配置"""
        return {
            "enabled": self.KNOWLEDGE_GRAPH_ENABLED,
            "entity_extraction_model": self.ENTITY_EXTRACTION_MODEL,
            "relation_extraction_model": self.RELATION_EXTRACTION_MODEL,
            "entity_confidence_threshold": self.ENTITY_CONFIDENCE_THRESHOLD,
            "relation_confidence_threshold": self.RELATION_CONFIDENCE_THRESHOLD,
        }
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """获取文档分析配置"""
        return {
            "enabled": self.DOCUMENT_ANALYSIS_ENABLED,
            "summary_max_length": self.SUMMARY_MAX_LENGTH,
            "keywords_max_count": self.KEYWORDS_MAX_COUNT,
            "classification_categories": self.CLASSIFICATION_CATEGORIES,
            "risk_assessment": {
                "enabled": self.RISK_ASSESSMENT_ENABLED,
                "levels": self.RISK_LEVELS,
                "factors": self.RISK_FACTORS,
            },
            "compliance": {
                "enabled": self.COMPLIANCE_ANALYSIS_ENABLED,
                "rules_path": self.COMPLIANCE_RULES_PATH,
                "threshold": self.COMPLIANCE_THRESHOLD,
            },
        }
    
    def is_ai_enabled(self) -> bool:
        """检查AI功能是否启用"""
        return self.AI_ENABLED
    
    def is_vector_enabled(self) -> bool:
        """检查向量化功能是否启用"""
        return self.AI_ENABLED and self.VECTOR_ENABLED
    
    def is_search_enabled(self) -> bool:
        """检查搜索功能是否启用"""
        return self.AI_ENABLED and self.SEARCH_ENABLED
    
    def is_knowledge_graph_enabled(self) -> bool:
        """检查知识图谱功能是否启用"""
        return self.AI_ENABLED and self.KNOWLEDGE_GRAPH_ENABLED
    
    def is_analysis_enabled(self) -> bool:
        """检查文档分析功能是否启用"""
        return self.AI_ENABLED and self.DOCUMENT_ANALYSIS_ENABLED


# 全局AI配置实例
ai_config = AIConfig()


def get_ai_config() -> AIConfig:
    """获取AI配置实例"""
    return ai_config