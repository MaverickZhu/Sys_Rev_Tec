#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI集成服务模块
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import numpy as np
import openai
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)


class AIIntegrationService:
    """AI集成服务 - 统一管理各种AI模型的调用"""

    def __init__(self):
        self.text_processor = TextProcessor()
        self.cache_manager = CacheManager()
        self.supported_models = {
            "embedding": {
                "openai": [
                    "text-embedding-ada-002",
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                ],
                "azure_openai": ["text-embedding-ada-002"],
                "ollama": ["nomic-embed-text", "mxbai-embed-large"],
                "huggingface": ["sentence-transformers/all-MiniLM-L6-v2"],
            },
            "llm": {
                "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                "azure_openai": ["gpt-35-turbo", "gpt-4"],
                "ollama": ["llama2", "mistral", "codellama"],
                "anthropic": ["claude-3-sonnet", "claude-3-haiku"],
            },
        }

    async def vectorize_document(
        self,
        document: Document,
        model_name: str = "bge-m3:latest",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """对文档进行向量化处理

        Args:
            document: 文档对象
            model_name: 向量化模型名称
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
            force_refresh: 是否强制刷新缓存

        Returns:
            向量化结果字典
        """
        try:
            # 检查缓存
            cache_key = (
                f"vectorize:{document.id}:{model_name}:{chunk_size}:{chunk_overlap}"
            )
            if not force_refresh:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(
                        f"Using cached vectorization for document {document.id}"
                    )
                    return json.loads(cached_result)

            # 获取文档文本内容
            document_text = await self._get_document_text(document)
            if not document_text:
                raise ValueError("No text content found in document")

            # 文本预处理和分块
            chunks = self.text_processor.chunk_text(
                text=document_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            logger.info(f"Document {document.id} split into {len(chunks)} chunks")

            # 向量化每个分块
            vectorized_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    # 获取文本向量
                    embedding = await self._get_text_embedding(
                        text=chunk["text"], model_name=model_name
                    )

                    # 分析文本主题和重要性
                    topic_info = await self._analyze_chunk_topic(chunk["text"])

                    vectorized_chunks.append(
                        {
                            "index": i,
                            "text": chunk["text"],
                            "start_char": chunk["start_char"],
                            "end_char": chunk["end_char"],
                            "embedding": embedding,
                            "topic": topic_info.get("category"),
                            "importance": topic_info.get("importance_score", 0.5),
                            "keywords": topic_info.get("keywords", []),
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to vectorize chunk {i} of document {document.id}: {str(e)}"
                    )
                    continue

            result = {
                "document_id": document.id,
                "model_name": model_name,
                "total_chunks": len(vectorized_chunks),
                "embedding_dimension": (
                    len(vectorized_chunks[0]["embedding"]) if vectorized_chunks else 0
                ),
                "chunks": vectorized_chunks,
                "processing_time": datetime.utcnow().isoformat(),
                "text_length": len(document_text),
            }

            # 缓存结果
            await self.cache_manager.set(
                cache_key,
                json.dumps(result, default=str),
                ttl=3600,  # 1小时缓存
            )

            logger.info(
                f"Successfully vectorized document {document.id} with {len(vectorized_chunks)} chunks"
            )
            return result

        except Exception as e:
            logger.error(
                f"Document vectorization failed for document {document.id}: {str(e)}"
            )
            raise

    async def analyze_document(
        self, document: Document, analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """对文档进行AI智能分析

        Args:
            document: 文档对象
            analysis_types: 分析类型列表

        Returns:
            分析结果字典
        """
        if analysis_types is None:
            analysis_types = ["summary", "keywords", "classification"]

        try:
            # 获取文档文本内容
            document_text = await self._get_document_text(document)
            if not document_text:
                raise ValueError("No text content found in document")

            analysis_result = {}

            # 文档摘要
            if "summary" in analysis_types:
                analysis_result["summary"] = await self._generate_summary(document_text)

            # 关键词提取
            if "keywords" in analysis_types:
                analysis_result["keywords"] = await self._extract_keywords(
                    document_text
                )

            # 文档分类
            if "classification" in analysis_types:
                analysis_result["classification"] = await self._classify_document(
                    document_text
                )

            return analysis_result

        except Exception as e:
            logger.error(
                f"Document analysis failed for document {document.id}: {str(e)}"
            )
            raise

    async def _get_document_text(self, document: Document) -> str:
        """获取文档文本内容"""
        # 这里应该根据文档类型获取文本内容
        # 简化实现，直接返回文档内容
        return getattr(document, "content", "") or getattr(document, "text", "")

    async def _get_text_embedding(self, text: str, model_name: str) -> List[float]:
        """获取文本向量"""
        # 简化实现，返回模拟向量
        return [0.1] * 768

    async def _analyze_chunk_topic(self, text: str) -> Dict[str, Any]:
        """分析文本块主题"""
        return {"category": "general", "importance_score": 0.5, "keywords": []}

    async def _generate_summary(self, text: str) -> str:
        """生成文档摘要"""
        return "这是一个模拟的文档摘要"

    async def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        return ["关键词1", "关键词2"]

    async def _classify_document(self, text: str) -> str:
        """文档分类"""
        return "general"


# 全局AI集成服务实例
ai_service = AIIntegrationService()
