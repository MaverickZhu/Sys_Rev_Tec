import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app import crud, models, schemas
from app.core.config import settings
from app.utils.ai_integration import AIIntegrationService
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor

# 配置日志
logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    知识图谱服务 - 管理实体提取、关系构建和图谱分析
    """
    
    def __init__(self):
        self.ai_service = AIIntegrationService()
        self.cache_manager = CacheManager()
        self.text_processor = TextProcessor()
        self.graph = nx.DiGraph()  # 使用NetworkX构建图谱
        self.entity_types = {
            "PERSON": "人员",
            "ORGANIZATION": "组织机构",
            "LOCATION": "地点",
            "DATE": "日期",
            "MONEY": "金额",
            "PERCENT": "百分比",
            "PRODUCT": "产品",
            "EVENT": "事件",
            "LAW": "法律法规",
            "TECHNOLOGY": "技术",
            "CONCEPT": "概念",
            "DOCUMENT": "文档",
            "PROJECT": "项目"
        }
        self.relation_types = {
            "BELONGS_TO": "属于",
            "WORKS_FOR": "工作于",
            "LOCATED_IN": "位于",
            "OCCURRED_ON": "发生于",
            "RELATED_TO": "相关于",
            "PART_OF": "部分",
            "DEPENDS_ON": "依赖于",
            "SIMILAR_TO": "相似于",
            "MENTIONS": "提及",
            "CONTAINS": "包含",
            "REFERENCES": "引用",
            "IMPLEMENTS": "实现",
            "COMPLIES_WITH": "符合"
        }
    
    async def extract_entities_from_document(
        self,
        db: Session,
        document_id: int,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        从文档中提取实体
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            force_refresh: 是否强制刷新
        
        Returns:
            实体提取结果
        """
        try:
            # 检查缓存
            cache_key = f"entities:{document_id}"
            if not force_refresh:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached entities for document {document_id}")
                    return json.loads(cached_result)
            
            # 获取文档
            document = crud.document.get(db=db, id=document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # 获取文档文本
            text_content = self._get_document_text(document)
            if not text_content:
                raise ValueError("No text content found in document")
            
            # 使用AI服务提取实体
            extraction_result = await self.ai_service.extract_entities(
                text=text_content,
                entity_types=list(self.entity_types.keys())
            )
            
            # 处理提取结果
            entities = []
            for entity_data in extraction_result.get("entities", []):
                # 创建或更新实体
                entity = await self._create_or_update_entity(
                    db=db,
                    name=entity_data["text"],
                    entity_type=entity_data["label"],
                    confidence=entity_data.get("confidence", 0.8),
                    document_id=document_id,
                    start_pos=entity_data.get("start", 0),
                    end_pos=entity_data.get("end", 0)
                )
                entities.append(entity)
            
            # 提取关系
            relations = await self._extract_relations(
                db=db,
                document_id=document_id,
                entities=entities,
                text_content=text_content
            )
            
            result = {
                "document_id": document_id,
                "entities": [
                    {
                        "id": e.id,
                        "name": e.entity_name,
                        "type": e.entity_type,
                        "confidence": e.confidence,
                        "mentions": e.mention_count
                    }
                    for e in entities
                ],
                "relations": [
                    {
                        "id": r.id,
                        "source": r.source_entity_id,
                        "target": r.target_entity_id,
                        "type": r.relation_type,
                        "confidence": r.confidence
                    }
                    for r in relations
                ],
                "extraction_time": datetime.utcnow().isoformat(),
                "total_entities": len(entities),
                "total_relations": len(relations)
            }
            
            # 缓存结果
            await self.cache_manager.set(
                cache_key,
                json.dumps(result, default=str),
                expire_time=3600  # 1小时缓存
            )
            
            logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from document {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract entities from document {document_id}: {str(e)}")
            raise
    
    def _get_document_text(self, document: models.Document) -> str:
        """
        获取文档文本内容
        """
        text_parts = []
        
        if document.extracted_text:
            text_parts.append(document.extracted_text)
        
        if document.ocr_text:
            text_parts.append(document.ocr_text)
        
        if document.ai_summary:
            text_parts.append(f"摘要: {document.ai_summary}")
        
        return "\n\n".join(text_parts)
    
    async def _create_or_update_entity(
        self,
        db: Session,
        name: str,
        entity_type: str,
        confidence: float,
        document_id: int,
        start_pos: int = 0,
        end_pos: int = 0
    ) -> models.KnowledgeGraph:
        """
        创建或更新实体
        """
        try:
            # 查找现有实体
            existing_entity = crud.knowledge_graph.get_by_name_and_type(
                db=db, entity_name=name, entity_type=entity_type
            )
            
            if existing_entity:
                # 更新现有实体
                update_data = {
                    "mention_count": existing_entity.mention_count + 1,
                    "confidence": max(existing_entity.confidence, confidence),
                    "last_mentioned_at": datetime.utcnow()
                }
                
                # 更新属性（合并新信息）
                properties = existing_entity.properties or {}
                properties[f"document_{document_id}"] = {
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "confidence": confidence
                }
                update_data["properties"] = properties
                
                entity = crud.knowledge_graph.update(
                    db=db, db_obj=existing_entity, obj_in=update_data
                )
            else:
                # 创建新实体
                entity_data = schemas.KnowledgeGraphCreate(
                    entity_name=name,
                    entity_type=entity_type,
                    confidence=confidence,
                    mention_count=1,
                    properties={
                        f"document_{document_id}": {
                            "start_pos": start_pos,
                            "end_pos": end_pos,
                            "confidence": confidence
                        }
                    },
                    description=f"{self.entity_types.get(entity_type, entity_type)}: {name}"
                )
                entity = crud.knowledge_graph.create(db=db, obj_in=entity_data)
            
            return entity
            
        except Exception as e:
            logger.error(f"Failed to create/update entity {name}: {str(e)}")
            raise
    
    async def _extract_relations(
        self,
        db: Session,
        document_id: int,
        entities: List[models.KnowledgeGraph],
        text_content: str
    ) -> List[models.KnowledgeGraphRelation]:
        """
        提取实体间关系
        """
        try:
            relations = []
            
            # 使用AI服务提取关系
            entity_pairs = [(e1, e2) for i, e1 in enumerate(entities) for e2 in entities[i+1:]]
            
            for entity1, entity2 in entity_pairs:
                # 检查实体是否在同一句子或段落中
                if self._entities_are_related(entity1.entity_name, entity2.entity_name, text_content):
                    # 使用AI确定关系类型
                    relation_type = await self._determine_relation_type(
                        entity1.entity_name, entity1.entity_type,
                        entity2.entity_name, entity2.entity_type,
                        text_content
                    )
                    
                    if relation_type:
                        # 检查关系是否已存在
                        existing_relation = crud.knowledge_graph_relation.get_by_entities(
                            db=db,
                            source_entity_id=entity1.id,
                            target_entity_id=entity2.id,
                            relation_type=relation_type
                        )
                        
                        if existing_relation:
                            # 更新现有关系
                            update_data = {
                                "confidence": min(existing_relation.confidence + 0.1, 1.0),
                                "mention_count": existing_relation.mention_count + 1
                            }
                            relation = crud.knowledge_graph_relation.update(
                                db=db, db_obj=existing_relation, obj_in=update_data
                            )
                        else:
                            # 创建新关系
                            relation_data = schemas.KnowledgeGraphRelationCreate(
                                source_entity_id=entity1.id,
                                target_entity_id=entity2.id,
                                relation_type=relation_type,
                                confidence=0.7,
                                mention_count=1,
                                properties={
                                    "document_id": document_id,
                                    "extracted_from": "ai_analysis"
                                }
                            )
                            relation = crud.knowledge_graph_relation.create(db=db, obj_in=relation_data)
                        
                        relations.append(relation)
            
            return relations
            
        except Exception as e:
            logger.error(f"Failed to extract relations: {str(e)}")
            return []
    
    def _entities_are_related(self, entity1: str, entity2: str, text: str) -> bool:
        """
        检查两个实体是否在文本中相关
        """
        try:
            # 简单的共现检查
            sentences = text.split('。')
            for sentence in sentences:
                if entity1 in sentence and entity2 in sentence:
                    return True
            
            # 检查段落级别的共现
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                if entity1 in paragraph and entity2 in paragraph:
                    # 如果在同一段落且距离不太远
                    pos1 = paragraph.find(entity1)
                    pos2 = paragraph.find(entity2)
                    if abs(pos1 - pos2) < 200:  # 200字符内
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _determine_relation_type(
        self,
        entity1_name: str, entity1_type: str,
        entity2_name: str, entity2_type: str,
        context: str
    ) -> Optional[str]:
        """
        使用AI确定关系类型
        """
        try:
            # 基于实体类型的规则
            type_rules = {
                ("PERSON", "ORGANIZATION"): "WORKS_FOR",
                ("ORGANIZATION", "LOCATION"): "LOCATED_IN",
                ("EVENT", "DATE"): "OCCURRED_ON",
                ("PRODUCT", "ORGANIZATION"): "BELONGS_TO",
                ("DOCUMENT", "PERSON"): "MENTIONS",
                ("PROJECT", "ORGANIZATION"): "BELONGS_TO",
                ("TECHNOLOGY", "PRODUCT"): "IMPLEMENTS",
                ("LAW", "ORGANIZATION"): "COMPLIES_WITH"
            }
            
            # 检查类型规则
            rule_key = (entity1_type, entity2_type)
            if rule_key in type_rules:
                return type_rules[rule_key]
            
            # 反向检查
            reverse_key = (entity2_type, entity1_type)
            if reverse_key in type_rules:
                return type_rules[reverse_key]
            
            # 使用AI分析上下文
            relation_prompt = f"""
            分析以下文本中两个实体之间的关系：
            实体1: {entity1_name} (类型: {entity1_type})
            实体2: {entity2_name} (类型: {entity2_type})
            
            上下文: {context[:500]}...
            
            可能的关系类型: {', '.join(self.relation_types.keys())}
            
            请返回最合适的关系类型，如果没有明确关系则返回RELATED_TO。
            """
            
            ai_result = await self.ai_service._call_llm(
                prompt=relation_prompt,
                max_tokens=50
            )
            
            # 解析AI结果
            predicted_relation = ai_result.strip().upper()
            if predicted_relation in self.relation_types:
                return predicted_relation
            
            # 默认关系
            return "RELATED_TO"
            
        except Exception as e:
            logger.error(f"Failed to determine relation type: {str(e)}")
            return "RELATED_TO"
    
    async def build_knowledge_graph(
        self,
        db: Session,
        document_ids: Optional[List[int]] = None,
        rebuild: bool = False
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            db: 数据库会话
            document_ids: 要处理的文档ID列表
            rebuild: 是否重建图谱
        
        Returns:
            构建结果
        """
        try:
            start_time = datetime.utcnow()
            
            if rebuild:
                # 清空现有图谱
                self.graph.clear()
                logger.info("Cleared existing knowledge graph")
            
            # 获取要处理的文档
            if document_ids:
                documents = [crud.document.get(db=db, id=doc_id) for doc_id in document_ids]
                documents = [doc for doc in documents if doc]
            else:
                documents = crud.document.get_multi(db=db, limit=1000)
            
            total_entities = 0
            total_relations = 0
            
            # 处理每个文档
            for document in documents:
                try:
                    # 提取实体和关系
                    extraction_result = await self.extract_entities_from_document(
                        db=db, document_id=document.id, force_refresh=rebuild
                    )
                    
                    total_entities += extraction_result["total_entities"]
                    total_relations += extraction_result["total_relations"]
                    
                    # 添加到NetworkX图
                    await self._add_to_networkx_graph(
                        extraction_result["entities"],
                        extraction_result["relations"]
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process document {document.id}: {str(e)}")
                    continue
            
            # 计算图谱统计信息
            graph_stats = self._calculate_graph_statistics()
            
            build_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "build_time": build_time,
                "processed_documents": len(documents),
                "total_entities": total_entities,
                "total_relations": total_relations,
                "graph_statistics": graph_stats,
                "built_at": datetime.utcnow().isoformat()
            }
            
            # 缓存图谱数据
            await self.cache_manager.set(
                "knowledge_graph_stats",
                json.dumps(result, default=str),
                expire_time=1800  # 30分钟缓存
            )
            
            logger.info(f"Knowledge graph built successfully in {build_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {str(e)}")
            raise
    
    async def _add_to_networkx_graph(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ):
        """
        将实体和关系添加到NetworkX图
        """
        try:
            # 添加节点
            for entity in entities:
                self.graph.add_node(
                    entity["id"],
                    name=entity["name"],
                    type=entity["type"],
                    confidence=entity["confidence"],
                    mentions=entity["mentions"]
                )
            
            # 添加边
            for relation in relations:
                self.graph.add_edge(
                    relation["source"],
                    relation["target"],
                    type=relation["type"],
                    confidence=relation["confidence"]
                )
            
        except Exception as e:
            logger.error(f"Failed to add to NetworkX graph: {str(e)}")
    
    def _calculate_graph_statistics(self) -> Dict[str, Any]:
        """
        计算图谱统计信息
        """
        try:
            if not self.graph.nodes():
                return {}
            
            # 基础统计
            stats = {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "density": nx.density(self.graph),
                "is_connected": nx.is_weakly_connected(self.graph)
            }
            
            # 节点度数统计
            degrees = dict(self.graph.degree())
            if degrees:
                stats["average_degree"] = sum(degrees.values()) / len(degrees)
                stats["max_degree"] = max(degrees.values())
                stats["min_degree"] = min(degrees.values())
            
            # 中心性分析
            try:
                centrality = nx.degree_centrality(self.graph)
                top_central_nodes = sorted(
                    centrality.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                stats["top_central_entities"] = [
                    {
                        "id": node_id,
                        "centrality": centrality_score,
                        "name": self.graph.nodes[node_id].get("name", "Unknown")
                    }
                    for node_id, centrality_score in top_central_nodes
                ]
            except:
                stats["top_central_entities"] = []
            
            # 连通组件
            try:
                components = list(nx.weakly_connected_components(self.graph))
                stats["connected_components"] = len(components)
                stats["largest_component_size"] = max(len(comp) for comp in components) if components else 0
            except:
                stats["connected_components"] = 0
                stats["largest_component_size"] = 0
            
            # 实体类型分布
            entity_types = {}
            for node_id in self.graph.nodes():
                entity_type = self.graph.nodes[node_id].get("type", "Unknown")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            stats["entity_type_distribution"] = entity_types
            
            # 关系类型分布
            relation_types = {}
            for edge in self.graph.edges(data=True):
                relation_type = edge[2].get("type", "Unknown")
                relation_types[relation_type] = relation_types.get(relation_type, 0) + 1
            stats["relation_type_distribution"] = relation_types
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate graph statistics: {str(e)}")
            return {}
    
    async def search_entities(
        self,
        db: Session,
        query: str,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.5,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索实体
        
        Args:
            db: 数据库会话
            query: 搜索查询
            entity_types: 实体类型过滤
            min_confidence: 最小置信度
            max_results: 最大结果数
        
        Returns:
            搜索结果
        """
        try:
            # 使用数据库搜索
            entities = crud.knowledge_graph.search_entities(
                db=db,
                query=query,
                entity_types=entity_types,
                min_confidence=min_confidence,
                limit=max_results
            )
            
            results = []
            for entity in entities:
                # 获取相关关系
                relations = crud.knowledge_graph_relation.get_by_entity(
                    db=db, entity_id=entity.id
                )
                
                result = {
                    "id": entity.id,
                    "name": entity.entity_name,
                    "type": entity.entity_type,
                    "type_label": self.entity_types.get(entity.entity_type, entity.entity_type),
                    "confidence": entity.confidence,
                    "mention_count": entity.mention_count,
                    "description": entity.description,
                    "properties": entity.properties,
                    "created_at": entity.created_at,
                    "last_mentioned_at": entity.last_mentioned_at,
                    "relation_count": len(relations)
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search entities: {str(e)}")
            raise
    
    async def get_entity_relations(
        self,
        db: Session,
        entity_id: int,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        获取实体关系网络
        
        Args:
            db: 数据库会话
            entity_id: 实体ID
            relation_types: 关系类型过滤
            max_depth: 最大深度
        
        Returns:
            关系网络
        """
        try:
            # 获取实体
            entity = crud.knowledge_graph.get(db=db, id=entity_id)
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # 构建关系网络
            network = {
                "center_entity": {
                    "id": entity.id,
                    "name": entity.entity_name,
                    "type": entity.entity_type,
                    "confidence": entity.confidence
                },
                "nodes": [],
                "edges": [],
                "statistics": {}
            }
            
            visited_entities = set([entity_id])
            current_level = [entity_id]
            
            for depth in range(max_depth):
                next_level = []
                
                for current_entity_id in current_level:
                    # 获取直接关系
                    relations = crud.knowledge_graph_relation.get_by_entity(
                        db=db, entity_id=current_entity_id
                    )
                    
                    for relation in relations:
                        # 过滤关系类型
                        if relation_types and relation.relation_type not in relation_types:
                            continue
                        
                        # 确定目标实体
                        target_entity_id = (
                            relation.target_entity_id
                            if relation.source_entity_id == current_entity_id
                            else relation.source_entity_id
                        )
                        
                        # 添加边
                        network["edges"].append({
                            "id": relation.id,
                            "source": relation.source_entity_id,
                            "target": relation.target_entity_id,
                            "type": relation.relation_type,
                            "type_label": self.relation_types.get(relation.relation_type, relation.relation_type),
                            "confidence": relation.confidence,
                            "mention_count": relation.mention_count
                        })
                        
                        # 添加目标实体到下一层
                        if target_entity_id not in visited_entities:
                            visited_entities.add(target_entity_id)
                            next_level.append(target_entity_id)
                            
                            # 获取实体信息
                            target_entity = crud.knowledge_graph.get(db=db, id=target_entity_id)
                            if target_entity:
                                network["nodes"].append({
                                    "id": target_entity.id,
                                    "name": target_entity.entity_name,
                                    "type": target_entity.entity_type,
                                    "type_label": self.entity_types.get(target_entity.entity_type, target_entity.entity_type),
                                    "confidence": target_entity.confidence,
                                    "mention_count": target_entity.mention_count,
                                    "depth": depth + 1
                                })
                
                current_level = next_level
                if not current_level:
                    break
            
            # 计算网络统计
            network["statistics"] = {
                "total_nodes": len(network["nodes"]) + 1,  # +1 for center entity
                "total_edges": len(network["edges"]),
                "max_depth_reached": depth + 1,
                "relation_type_counts": {}
            }
            
            # 统计关系类型
            for edge in network["edges"]:
                rel_type = edge["type"]
                network["statistics"]["relation_type_counts"][rel_type] = \
                    network["statistics"]["relation_type_counts"].get(rel_type, 0) + 1
            
            return network
            
        except Exception as e:
            logger.error(f"Failed to get entity relations: {str(e)}")
            raise
    
    async def find_shortest_path(
        self,
        db: Session,
        source_entity_id: int,
        target_entity_id: int
    ) -> Dict[str, Any]:
        """
        查找两个实体间的最短路径
        
        Args:
            db: 数据库会话
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
        
        Returns:
            最短路径信息
        """
        try:
            # 检查实体是否存在于图中
            if source_entity_id not in self.graph.nodes() or target_entity_id not in self.graph.nodes():
                return {
                    "path_found": False,
                    "message": "One or both entities not found in knowledge graph"
                }
            
            # 查找最短路径
            try:
                path = nx.shortest_path(
                    self.graph,
                    source=source_entity_id,
                    target=target_entity_id
                )
                
                # 构建路径详情
                path_details = []
                for i in range(len(path) - 1):
                    current_node = path[i]
                    next_node = path[i + 1]
                    
                    # 获取边信息
                    edge_data = self.graph.get_edge_data(current_node, next_node)
                    
                    path_details.append({
                        "from_entity": {
                            "id": current_node,
                            "name": self.graph.nodes[current_node].get("name", "Unknown"),
                            "type": self.graph.nodes[current_node].get("type", "Unknown")
                        },
                        "to_entity": {
                            "id": next_node,
                            "name": self.graph.nodes[next_node].get("name", "Unknown"),
                            "type": self.graph.nodes[next_node].get("type", "Unknown")
                        },
                        "relation": {
                            "type": edge_data.get("type", "Unknown"),
                            "confidence": edge_data.get("confidence", 0.0)
                        }
                    })
                
                return {
                    "path_found": True,
                    "path_length": len(path) - 1,
                    "entity_path": path,
                    "path_details": path_details
                }
                
            except nx.NetworkXNoPath:
                return {
                    "path_found": False,
                    "message": "No path found between the entities"
                }
            
        except Exception as e:
            logger.error(f"Failed to find shortest path: {str(e)}")
            raise
    
    async def get_knowledge_graph_statistics(self, db: Session) -> Dict[str, Any]:
        """
        获取知识图谱统计信息
        """
        try:
            # 检查缓存
            cached_stats = await self.cache_manager.get("knowledge_graph_stats")
            if cached_stats:
                return json.loads(cached_stats)
            
            # 数据库统计
            entity_stats = crud.knowledge_graph.get_statistics(db=db)
            relation_stats = crud.knowledge_graph_relation.get_statistics(db=db)
            
            # NetworkX图统计
            graph_stats = self._calculate_graph_statistics()
            
            # 合并统计信息
            combined_stats = {
                "database_statistics": {
                    "entities": entity_stats,
                    "relations": relation_stats
                },
                "graph_statistics": graph_stats,
                "entity_types": self.entity_types,
                "relation_types": self.relation_types,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # 缓存结果
            await self.cache_manager.set(
                "knowledge_graph_stats",
                json.dumps(combined_stats, default=str),
                expire_time=1800  # 30分钟缓存
            )
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge graph statistics: {str(e)}")
            raise
    
    async def export_graph_data(
        self,
        db: Session,
        format_type: str = "json",
        include_properties: bool = True
    ) -> Dict[str, Any]:
        """
        导出知识图谱数据
        
        Args:
            db: 数据库会话
            format_type: 导出格式 (json, gexf, graphml)
            include_properties: 是否包含属性
        
        Returns:
            导出的图谱数据
        """
        try:
            if format_type == "json":
                # JSON格式导出
                nodes = []
                edges = []
                
                for node_id in self.graph.nodes():
                    node_data = {
                        "id": node_id,
                        "name": self.graph.nodes[node_id].get("name", "Unknown"),
                        "type": self.graph.nodes[node_id].get("type", "Unknown"),
                        "confidence": self.graph.nodes[node_id].get("confidence", 0.0),
                        "mentions": self.graph.nodes[node_id].get("mentions", 0)
                    }
                    
                    if include_properties:
                        # 从数据库获取完整属性
                        entity = crud.knowledge_graph.get(db=db, id=node_id)
                        if entity:
                            node_data["properties"] = entity.properties
                            node_data["description"] = entity.description
                    
                    nodes.append(node_data)
                
                for edge in self.graph.edges(data=True):
                    edge_data = {
                        "source": edge[0],
                        "target": edge[1],
                        "type": edge[2].get("type", "Unknown"),
                        "confidence": edge[2].get("confidence", 0.0)
                    }
                    edges.append(edge_data)
                
                return {
                    "format": "json",
                    "nodes": nodes,
                    "edges": edges,
                    "metadata": {
                        "total_nodes": len(nodes),
                        "total_edges": len(edges),
                        "exported_at": datetime.utcnow().isoformat()
                    }
                }
            
            elif format_type == "gexf":
                # GEXF格式导出
                import io
                buffer = io.StringIO()
                nx.write_gexf(self.graph, buffer)
                return {
                    "format": "gexf",
                    "data": buffer.getvalue(),
                    "metadata": {
                        "exported_at": datetime.utcnow().isoformat()
                    }
                }
            
            elif format_type == "graphml":
                # GraphML格式导出
                import io
                buffer = io.StringIO()
                nx.write_graphml(self.graph, buffer)
                return {
                    "format": "graphml",
                    "data": buffer.getvalue(),
                    "metadata": {
                        "exported_at": datetime.utcnow().isoformat()
                    }
                }
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
        except Exception as e:
            logger.error(f"Failed to export graph data: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {}
            }
            
            # 检查AI服务
            try:
                ai_health = await self.ai_service.health_check()
                health_status["services"]["ai_integration"] = ai_health["status"]
            except:
                health_status["services"]["ai_integration"] = "unhealthy"
            
            # 检查缓存
            try:
                await self.cache_manager.set("kg_health_check", "ok", expire_time=60)
                cached_value = await self.cache_manager.get("kg_health_check")
                if cached_value == "ok":
                    health_status["services"]["cache"] = "healthy"
                else:
                    health_status["services"]["cache"] = "unhealthy"
            except:
                health_status["services"]["cache"] = "unhealthy"
            
            # 检查图谱状态
            try:
                graph_info = {
                    "nodes": self.graph.number_of_nodes(),
                    "edges": self.graph.number_of_edges()
                }
                health_status["graph_info"] = graph_info
                health_status["services"]["knowledge_graph"] = "healthy"
            except:
                health_status["services"]["knowledge_graph"] = "unhealthy"
            
            # 检查整体状态
            unhealthy_services = [k for k, v in health_status["services"].items() if v == "unhealthy"]
            if unhealthy_services:
                health_status["status"] = "degraded"
                health_status["unhealthy_services"] = unhealthy_services
            
            return health_status
            
        except Exception as e:
            logger.error(f"Knowledge graph health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }