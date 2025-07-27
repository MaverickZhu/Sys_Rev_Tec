import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.ocr import OCRResult
from app.utils.text_processing import TextProcessor
from app.utils.cache import CacheManager

# 配置日志
logger = logging.getLogger(__name__)


class AIIntegrationService:
    """
    AI集成服务 - 统一管理各种AI模型的调用
    """
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.cache_manager = CacheManager()
        self.supported_models = {
            "embedding": {
                "openai": ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                "azure_openai": ["text-embedding-ada-002"],
                "ollama": ["nomic-embed-text", "mxbai-embed-large"],
                "huggingface": ["sentence-transformers/all-MiniLM-L6-v2"]
            },
            "llm": {
                "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                "azure_openai": ["gpt-35-turbo", "gpt-4"],
                "ollama": ["llama2", "mistral", "codellama"],
                "anthropic": ["claude-3-sonnet", "claude-3-haiku"]
            }
        }
    
    async def vectorize_document(
        self,
        document: Document,
        model_name: str = "bge-m3:latest",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        对文档进行向量化处理
        
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
            cache_key = f"vectorize:{document.id}:{model_name}:{chunk_size}:{chunk_overlap}"
            if not force_refresh:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached vectorization for document {document.id}")
                    return json.loads(cached_result)
            
            # 获取文档文本内容
            document_text = await self._get_document_text(document)
            if not document_text:
                raise ValueError("No text content found in document")
            
            # 文本预处理和分块
            chunks = self.text_processor.chunk_text(
                text=document_text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            logger.info(f"Document {document.id} split into {len(chunks)} chunks")
            
            # 向量化每个分块
            vectorized_chunks = []
            for i, chunk in enumerate(chunks):
                try:
                    # 获取文本向量
                    embedding = await self._get_text_embedding(
                        text=chunk["text"],
                        model_name=model_name
                    )
                    
                    # 分析文本主题和重要性
                    topic_info = await self._analyze_chunk_topic(chunk["text"])
                    
                    vectorized_chunks.append({
                        "index": i,
                        "text": chunk["text"],
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"],
                        "embedding": embedding,
                        "topic": topic_info.get("category"),
                        "importance": topic_info.get("importance_score", 0.5),
                        "keywords": topic_info.get("keywords", [])
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to vectorize chunk {i} of document {document.id}: {str(e)}")
                    continue
            
            result = {
                "document_id": document.id,
                "model_name": model_name,
                "total_chunks": len(vectorized_chunks),
                "embedding_dimension": len(vectorized_chunks[0]["embedding"]) if vectorized_chunks else 0,
                "chunks": vectorized_chunks,
                "processing_time": datetime.utcnow().isoformat(),
                "text_length": len(document_text)
            }
            
            # 缓存结果
            await self.cache_manager.set(
                cache_key, 
                json.dumps(result, default=str),
                ttl=3600  # 1小时缓存
            )
            
            logger.info(f"Successfully vectorized document {document.id} with {len(vectorized_chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Document vectorization failed for document {document.id}: {str(e)}")
            raise
    
    async def analyze_document(
        self,
        document: Document,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        对文档进行AI智能分析
        
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
                analysis_result["keywords"] = await self._extract_keywords(document_text)
            
            # 文档分类
            if "classification" in analysis_types:
                analysis_result["classification"] = await self._classify_document(document_text)
            
            # 风险评估
            if "risk_assessment" in analysis_types:
                analysis_result["risk_assessment"] = await self._assess_risk(document_text)
            
            # 合规性分析
            if "compliance_analysis" in analysis_types:
                analysis_result["compliance_analysis"] = await self._analyze_compliance(document_text)
            
            # 实体提取
            if "entity_extraction" in analysis_types:
                analysis_result["entities"] = await self._extract_entities(document_text)
            
            # 情感分析
            if "sentiment_analysis" in analysis_types:
                analysis_result["sentiment"] = await self._analyze_sentiment(document_text)
            
            logger.info(f"Successfully analyzed document {document.id} with types: {analysis_types}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Document analysis failed for document {document.id}: {str(e)}")
            raise
    
    async def semantic_search(
        self,
        query: str,
        document_embeddings: List[Dict[str, Any]],
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            document_embeddings: 文档向量列表
            similarity_threshold: 相似度阈值
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        try:
            # 获取查询向量
            query_embedding = await self._get_text_embedding(query)
            
            # 计算相似度
            similarities = []
            for doc_emb in document_embeddings:
                similarity = self._calculate_cosine_similarity(
                    query_embedding, 
                    doc_emb["embedding"]
                )
                if similarity >= similarity_threshold:
                    similarities.append({
                        "document_id": doc_emb["document_id"],
                        "chunk_index": doc_emb["chunk_index"],
                        "similarity": similarity,
                        "text": doc_emb["text"],
                        "metadata": doc_emb.get("metadata", {})
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:max_results]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            raise
    
    async def _get_document_text(self, document: Document) -> str:
        """
        获取文档的文本内容
        """
        text_content = ""
        
        # 优先使用提取的文本
        if document.extracted_text:
            text_content = document.extracted_text
        # 其次使用OCR文本
        elif document.ocr_text:
            text_content = document.ocr_text
        # 最后尝试从文件内容获取
        elif document.content:
            text_content = document.content
        
        return text_content.strip() if text_content else ""
    
    async def _get_text_embedding(
        self, 
        text: str, 
        model_name: str = "bge-m3:latest"
    ) -> List[float]:
        """
        获取文本的向量表示
        """
        try:
            # 检查缓存
            cache_key = f"embedding:{model_name}:{hash(text)}"
            cached_embedding = await self.cache_manager.get(cache_key)
            if cached_embedding:
                return json.loads(cached_embedding)
            
            # 优先使用Ollama，然后是OpenAI
            if settings.OLLAMA_BASE_URL and model_name in self.supported_models["embedding"]["ollama"]:
                embedding = await self._get_ollama_embedding(text, model_name)
            elif model_name.startswith("text-embedding") and settings.OPENAI_API_KEY:
                embedding = await self._get_openai_embedding(text, model_name)
            elif settings.OLLAMA_BASE_URL:
                # 默认使用Ollama的嵌入模型
                embedding = await self._get_ollama_embedding(text, "bge-m3:latest")
            elif settings.OPENAI_API_KEY:
                # 默认使用OpenAI
                embedding = await self._get_openai_embedding(text, "text-embedding-ada-002")
            else:
                raise Exception("No embedding service available")
            
            # 缓存结果
            await self.cache_manager.set(
                cache_key,
                json.dumps(embedding),
                ttl=86400  # 24小时缓存
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to get text embedding: {str(e)}")
            # 返回随机向量作为fallback
            return np.random.rand(384).tolist()  # Ollama嵌入通常是384维
    
    async def _get_openai_embedding(self, text: str, model_name: str) -> List[float]:
        """
        使用OpenAI API获取文本向量
        """
        try:
            import openai
            
            # 配置OpenAI客户端
            if settings.AZURE_OPENAI_ENDPOINT:
                # 使用Azure OpenAI
                client = openai.AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
            else:
                # 使用OpenAI
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.embeddings.create(
                model=model_name,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            raise
    
    async def _get_ollama_embedding(self, text: str, model_name: str) -> List[float]:
        """
        使用Ollama获取文本向量
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model_name,
                    "prompt": text
                }
                
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["embedding"]
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ollama embedding failed: {str(e)}")
            raise
    
    async def _analyze_chunk_topic(self, text: str) -> Dict[str, Any]:
        """
        分析文本块的主题和重要性
        """
        try:
            # 使用简单的关键词分析
            keywords = self.text_processor.extract_keywords(text, max_keywords=5)
            
            # 计算重要性分数（基于文本长度、关键词密度等）
            importance_score = min(1.0, len(text) / 1000 * 0.5 + len(keywords) / 10 * 0.5)
            
            # 简单的主题分类
            topic_keywords = {
                "technical": ["技术", "系统", "开发", "代码", "API", "数据库"],
                "business": ["业务", "商业", "市场", "客户", "销售", "收入"],
                "legal": ["法律", "合同", "协议", "条款", "法规", "合规"],
                "financial": ["财务", "金融", "预算", "成本", "投资", "收益"]
            }
            
            category = "general"
            max_score = 0
            
            for cat, cat_keywords in topic_keywords.items():
                score = sum(1 for keyword in cat_keywords if keyword in text)
                if score > max_score:
                    max_score = score
                    category = cat
            
            return {
                "category": category,
                "importance_score": importance_score,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Topic analysis failed: {str(e)}")
            return {
                "category": "general",
                "importance_score": 0.5,
                "keywords": []
            }
    
    async def _generate_summary(self, text: str) -> str:
        """
        生成文档摘要
        """
        try:
            # 使用LLM生成摘要
            prompt = f"请为以下文档生成一个简洁的摘要（不超过200字）：\n\n{text[:2000]}..."
            summary = await self._call_llm(prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            # 简单的摘要fallback
            sentences = text.split('。')[:3]
            return '。'.join(sentences) + '。'
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词
        """
        try:
            return self.text_processor.extract_keywords(text, max_keywords=10)
        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return []
    
    async def _classify_document(self, text: str) -> Dict[str, Any]:
        """
        文档分类
        """
        try:
            # 简单的基于关键词的分类
            categories = {
                "技术文档": ["API", "系统", "开发", "代码", "技术"],
                "业务文档": ["业务", "流程", "需求", "用户", "功能"],
                "法律文档": ["合同", "协议", "法律", "条款", "合规"],
                "财务文档": ["财务", "预算", "成本", "收入", "投资"]
            }
            
            scores = {}
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in text)
                scores[category] = score
            
            best_category = max(scores, key=scores.get) if scores else "其他"
            confidence = scores.get(best_category, 0) / 10
            
            return {
                "category": best_category,
                "confidence": min(1.0, confidence),
                "all_scores": scores
            }
            
        except Exception as e:
            logger.error(f"Document classification failed: {str(e)}")
            return {"category": "其他", "confidence": 0.0}
    
    async def _assess_risk(self, text: str) -> Dict[str, Any]:
        """
        风险评估
        """
        try:
            risk_keywords = {
                "high": ["风险", "危险", "威胁", "安全", "漏洞", "攻击"],
                "medium": ["注意", "警告", "问题", "错误", "异常"],
                "low": ["正常", "安全", "稳定", "可靠"]
            }
            
            risk_score = 0
            for level, keywords in risk_keywords.items():
                count = sum(1 for keyword in keywords if keyword in text)
                if level == "high":
                    risk_score += count * 3
                elif level == "medium":
                    risk_score += count * 2
                else:
                    risk_score -= count
            
            risk_level = "low"
            if risk_score > 10:
                risk_level = "high"
            elif risk_score > 5:
                risk_level = "medium"
            
            return {
                "risk_level": risk_level,
                "risk_score": max(0, risk_score),
                "assessment_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            return {"risk_level": "unknown", "risk_score": 0}
    
    async def _analyze_compliance(self, text: str) -> Dict[str, Any]:
        """
        合规性分析
        """
        try:
            compliance_keywords = {
                "GDPR": ["个人数据", "隐私", "数据保护", "同意"],
                "SOX": ["财务报告", "内控", "审计", "合规"],
                "ISO27001": ["信息安全", "安全管理", "风险管理"]
            }
            
            compliance_scores = {}
            for standard, keywords in compliance_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                compliance_scores[standard] = score
            
            return {
                "compliance_scores": compliance_scores,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {str(e)}")
            return {"compliance_scores": {}}
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        实体提取
        """
        try:
            # 简单的实体提取（可以集成更复杂的NER模型）
            import re
            
            entities = []
            
            # 提取邮箱
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            for email in emails:
                entities.append({"type": "email", "value": email, "confidence": 0.9})
            
            # 提取电话号码
            phones = re.findall(r'\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b', text)
            for phone in phones:
                entities.append({"type": "phone", "value": phone, "confidence": 0.8})
            
            # 提取日期
            dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b', text)
            for date in dates:
                entities.append({"type": "date", "value": date, "confidence": 0.7})
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        情感分析
        """
        try:
            # 简单的情感分析
            positive_words = ["好", "优秀", "成功", "满意", "高兴", "喜欢"]
            negative_words = ["坏", "失败", "问题", "错误", "不满", "讨厌"]
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                sentiment = "positive"
                score = min(1.0, positive_count / 10)
            elif negative_count > positive_count:
                sentiment = "negative"
                score = min(1.0, negative_count / 10)
            else:
                sentiment = "neutral"
                score = 0.5
            
            return {
                "sentiment": sentiment,
                "score": score,
                "positive_count": positive_count,
                "negative_count": negative_count
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {"sentiment": "neutral", "score": 0.5}
    
    async def _call_llm(self, prompt: str, model_name: str = "gpt-3.5-turbo") -> str:
        """
        调用大语言模型
        """
        try:
            # 这里可以根据配置调用不同的LLM
            if settings.OPENAI_API_KEY:
                return await self._call_openai_llm(prompt, model_name)
            elif settings.OLLAMA_BASE_URL:
                return await self._call_ollama_llm(prompt, "llama2")
            else:
                # Fallback to simple text processing
                return prompt[:200] + "..."
                
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return "AI分析暂时不可用"
    
    async def _call_openai_llm(self, prompt: str, model_name: str) -> str:
        """
        调用OpenAI LLM
        """
        try:
            import openai
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI LLM call failed: {str(e)}")
            raise
    
    async def _call_ollama_llm(self, prompt: str, model_name: str) -> str:
        """
        调用Ollama LLM
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False
                }
                
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["response"]
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ollama LLM call failed: {str(e)}")
            raise
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        """
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {str(e)}")
            return 0.0
    
    def get_supported_models(self) -> Dict[str, Any]:
        """
        获取支持的模型列表
        """
        return self.supported_models
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # 检查OpenAI连接
        if settings.OPENAI_API_KEY:
            try:
                await self._get_text_embedding("test", "text-embedding-ada-002")
                health_status["services"]["openai"] = "healthy"
            except:
                health_status["services"]["openai"] = "unhealthy"
        
        # 检查Ollama连接
        if settings.OLLAMA_BASE_URL:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{settings.OLLAMA_BASE_URL}/api/tags") as response:
                        if response.status == 200:
                            health_status["services"]["ollama"] = "healthy"
                        else:
                            health_status["services"]["ollama"] = "unhealthy"
            except:
                health_status["services"]["ollama"] = "unhealthy"
        
        # 检查缓存服务
        try:
            await self.cache_manager.set("health_check", "ok", expire_time=60)
            cached_value = await self.cache_manager.get("health_check")
            if cached_value == "ok":
                health_status["services"]["cache"] = "healthy"
            else:
                health_status["services"]["cache"] = "unhealthy"
        except:
            health_status["services"]["cache"] = "unhealthy"
        
        # 检查整体状态
        unhealthy_services = [k for k, v in health_status["services"].items() if v == "unhealthy"]
        if unhealthy_services:
            health_status["status"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
        
        return health_status