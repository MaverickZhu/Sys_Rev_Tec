# 配置日志

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import networkx as nx
from sqlalchemy.orm import Session

from app import crud, schemas
from app.models.document import Document
from app.models.vector import KnowledgeGraph, KnowledgeGraphRelation
from app.utils.ai_integration import AIIntegrationService
from app.utils.cache import CacheManager
from app.utils.text_processing import TextProcessor

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
            "PROJECT": "项目",
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
            "COMPLIES_WITH": "符合",
        }

    async def extract_entities_from_document(
        self, db: Session, document_id: int, force_refresh: bool = False
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
                text=text_content, entity_types=list(self.entity_types.keys())
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
                    end_pos=entity_data.get("end", 0),
                )
                entities.append(entity)

            # 提取关系
            relations = await self._extract_relations(
                db=db,
                document_id=document_id,
                entities=entities,
                text_content=text_content,
            )

            result = {
                "document_id": document_id,
                "entities": [
                    {
                        "id": e.id,
                        "name": e.entity_name,
                        "type": e.entity_type,
                        "confidence": e.confidence,
                        "mentions": e.mention_count,
                    }
                    for e in entities
                ],
                "relations": [
                    {
                        "id": r.id,
                        "source": r.source_entity_id,
                        "target": r.target_entity_id,
                        "type": r.relation_type,
                        "confidence": r.confidence,
                    }
                    for r in relations
                ],
                "extraction_time": datetime.utcnow().isoformat(),
                "total_entities": len(entities),
                "total_relations": len(relations),
            }

            # 缓存结果
            await self.cache_manager.set(
                cache_key,
                json.dumps(result, default=str),
                expire_time=3600,  # 1小时缓存
            )

            logger.info(
                f"Extracted {len(entities)} entities and "
                f"{len(relations)} relations from document {document_id}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to extract entities from document {document_id}: " f"{str(e)}"
            )
            raise

    def _get_document_text(self, document: Document) -> str:
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
        end_pos: int = 0,
    ) -> KnowledgeGraph:
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
                    "last_mentioned_at": datetime.utcnow(),
                }

                # 更新属性(合并新信息)
                properties = existing_entity.properties or {}
                properties[f"document_{document_id}"] = {
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "confidence": confidence,
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
                            "confidence": confidence,
                        }
                    },
                    description=(
                        f"{self.entity_types.get(entity_type, entity_type)}: " f"{name}"
                    ),
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
        entities: List[KnowledgeGraph],
        text_content: str,
    ) -> List[KnowledgeGraphRelation]:
        """
        提取实体间关系
        """
        try:
            relations = []

            # 使用AI服务提取关系
            entity_pairs = [
                (e1, e2) for i, e1 in enumerate(entities) for e2 in entities[i + 1 :]
            ]

            for entity1, entity2 in entity_pairs:
                # 检查实体是否在同一句子或段落中
                if self._entities_are_related(
                    entity1.entity_name, entity2.entity_name, text_content
                ):
                    # 使用AI确定关系类型
                    relation_type = await self._determine_relation_type(
                        entity1.entity_name,
                        entity1.entity_type,
                        entity2.entity_name,
                        entity2.entity_type,
                        text_content,
                    )

                    if relation_type:
                        # 检查关系是否已存在
                        existing_relation = (
                            crud.knowledge_graph_relation.get_by_entities(
                                db=db,
                                source_entity_id=entity1.id,
                                target_entity_id=entity2.id,
                                relation_type=relation_type,
                            )
                        )

                        if existing_relation:
                            # 更新现有关系
                            update_data = {
                                "confidence": min(
                                    existing_relation.confidence + 0.1, 1.0
                                ),
                                "mention_count": existing_relation.mention_count + 1,
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
                                    "extracted_from": "ai_analysis",
                                },
                            )
                            relation = crud.knowledge_graph_relation.create(
                                db=db, obj_in=relation_data
                            )

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
            sentences = text.split("。")
            for sentence in sentences:
                if entity1 in sentence and entity2 in sentence:
                    return True

            # 检查段落级别的共现
            paragraphs = text.split("\n\n")
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
        entity1_name: str,
        entity1_type: str,
        entity2_name: str,
        entity2_type: str,
        context: str,
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
                ("LAW", "ORGANIZATION"): "COMPLIES_WITH",
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
            prompt = f"""
            分析以下文本中两个实体之间的关系：
            实体1: {entity1_name} (类型: {entity1_type})
            实体2: {entity2_name} (类型: {entity2_type})

            上下文: {context[:500]}...

            请从以下关系类型中选择最合适的一个：
            {', '.join(self.relation_types.keys())}

            只返回关系类型，不要其他内容。
            """

            ai_result = await self.ai_service.analyze_text(prompt)
            relation_type = ai_result.get("result", "").strip().upper()

            if relation_type in self.relation_types:
                return relation_type

            # 默认关系
            return "RELATED_TO"

        except Exception as e:
            logger.error(f"Failed to determine relation type: {str(e)}")
            return "RELATED_TO"

    async def build_knowledge_graph(
        self, db: Session, document_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        """
        try:
            # 获取所有实体和关系
            if document_ids:
                entities = crud.knowledge_graph.get_by_documents(
                    db=db, document_ids=document_ids
                )
                relations = crud.knowledge_graph_relation.get_by_documents(
                    db=db, document_ids=document_ids
                )
            else:
                entities = crud.knowledge_graph.get_multi(db=db, limit=1000)
                relations = crud.knowledge_graph_relation.get_multi(db=db, limit=1000)

            # 构建NetworkX图
            self.graph.clear()

            # 添加节点
            for entity in entities:
                self.graph.add_node(
                    entity.id,
                    name=entity.entity_name,
                    type=entity.entity_type,
                    confidence=entity.confidence,
                    mentions=entity.mention_count,
                    properties=entity.properties or {},
                )

            # 添加边
            for relation in relations:
                self.graph.add_edge(
                    relation.source_entity_id,
                    relation.target_entity_id,
                    type=relation.relation_type,
                    confidence=relation.confidence,
                    mentions=relation.mention_count,
                    properties=relation.properties or {},
                )

            # 计算图谱统计信息
            stats = {
                "total_entities": len(entities),
                "total_relations": len(relations),
                "entity_types": {},
                "relation_types": {},
                "graph_density": nx.density(self.graph),
                "connected_components": nx.number_connected_components(
                    self.graph.to_undirected()
                ),
            }

            # 统计实体类型分布
            for entity in entities:
                entity_type = entity.entity_type
                stats["entity_types"][entity_type] = (
                    stats["entity_types"].get(entity_type, 0) + 1
                )

            # 统计关系类型分布
            for relation in relations:
                relation_type = relation.relation_type
                stats["relation_types"][relation_type] = (
                    stats["relation_types"].get(relation_type, 0) + 1
                )

            return {
                "graph": {
                    "nodes": [
                        {
                            "id": node_id,
                            **data,
                        }
                        for node_id, data in self.graph.nodes(data=True)
                    ],
                    "edges": [
                        {
                            "source": source,
                            "target": target,
                            **data,
                        }
                        for source, target, data in self.graph.edges(data=True)
                    ],
                },
                "statistics": stats,
                "build_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {str(e)}")
            raise

    async def find_entity_connections(
        self, db: Session, entity_id: int, max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        查找实体的连接关系
        """
        try:
            # 获取实体
            entity = crud.knowledge_graph.get(db=db, id=entity_id)
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")

            # 构建子图
            if entity_id not in self.graph:
                await self.build_knowledge_graph(db)

            if entity_id not in self.graph:
                return {
                    "entity": {
                        "id": entity.id,
                        "name": entity.entity_name,
                        "type": entity.entity_type,
                    },
                    "connections": [],
                    "paths": [],
                }

            # 获取指定深度内的所有连接
            connections = []
            paths = []

            # 使用BFS查找连接
            visited = set()
            queue = [(entity_id, 0, [entity_id])]

            while queue:
                current_id, depth, path = queue.pop(0)

                if depth >= max_depth or current_id in visited:
                    continue

                visited.add(current_id)

                # 获取邻居节点
                for neighbor_id in self.graph.neighbors(current_id):
                    if neighbor_id not in visited:
                        # 获取边信息
                        edge_data = self.graph.get_edge_data(current_id, neighbor_id)
                        neighbor_data = self.graph.nodes[neighbor_id]

                        connection = {
                            "entity": {
                                "id": neighbor_id,
                                "name": neighbor_data["name"],
                                "type": neighbor_data["type"],
                            },
                            "relation": {
                                "type": edge_data["type"],
                                "confidence": edge_data["confidence"],
                            },
                            "depth": depth + 1,
                            "path": path + [neighbor_id],
                        }
                        connections.append(connection)

                        # 添加到队列继续搜索
                        queue.append((neighbor_id, depth + 1, path + [neighbor_id]))

            # 查找最短路径
            for connection in connections:
                target_id = connection["entity"]["id"]
                try:
                    shortest_path = nx.shortest_path(self.graph, entity_id, target_id)
                    if len(shortest_path) > 2:  # 不包括直接连接
                        paths.append(
                            {
                                "target": connection["entity"],
                                "path": shortest_path,
                                "length": len(shortest_path) - 1,
                            }
                        )
                except nx.NetworkXNoPath:
                    continue

            return {
                "entity": {
                    "id": entity.id,
                    "name": entity.entity_name,
                    "type": entity.entity_type,
                },
                "connections": connections,
                "paths": sorted(paths, key=lambda x: x["length"])[
                    :10
                ],  # 最短的10条路径
                "total_connections": len(connections),
            }

        except Exception as e:
            logger.error(f"Failed to find entity connections: {str(e)}")
            raise

    async def search_entities(
        self, db: Session, query: str, entity_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索实体
        """
        try:
            # 使用数据库搜索
            entities = crud.knowledge_graph.search(
                db=db, query=query, entity_types=entity_types
            )

            results = []
            for entity in entities:
                # 获取相关关系数量
                relation_count = crud.knowledge_graph_relation.count_by_entity(
                    db=db, entity_id=entity.id
                )

                results.append(
                    {
                        "id": entity.id,
                        "name": entity.entity_name,
                        "type": entity.entity_type,
                        "confidence": entity.confidence,
                        "mentions": entity.mention_count,
                        "relations": relation_count,
                        "description": entity.description,
                        "properties": entity.properties or {},
                    }
                )

            return sorted(results, key=lambda x: x["confidence"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to search entities: {str(e)}")
            return []

    async def get_entity_timeline(
        self, db: Session, entity_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取实体时间线
        """
        try:
            # 获取实体
            entity = crud.knowledge_graph.get(db=db, id=entity_id)
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")

            # 获取相关文档和时间信息
            timeline_events = []

            # 从属性中提取文档信息
            properties = entity.properties or {}
            for key, value in properties.items():
                if key.startswith("document_"):
                    document_id = int(key.split("_")[1])
                    document = crud.document.get(db=db, id=document_id)
                    if document:
                        timeline_events.append(
                            {
                                "date": document.created_at.isoformat(),
                                "event": (f"在文档 '{document.title}' 中被提及"),
                                "document_id": document_id,
                                "confidence": value.get("confidence", 0.8),
                            }
                        )

            # 按时间排序
            timeline_events.sort(key=lambda x: x["date"])

            return timeline_events

        except Exception as e:
            logger.error(f"Failed to get entity timeline: {str(e)}")
            return []

    async def export_graph_data(
        self, db: Session, format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        导出图谱数据
        """
        try:
            # 构建完整图谱
            graph_data = await self.build_knowledge_graph(db)

            if format_type == "json":
                return graph_data
            elif format_type == "gexf":
                # 导出为GEXF格式(Gephi可读)
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".gexf", delete=False
                ) as f:
                    nx.write_gexf(self.graph, f.name)
                    with open(f.name, "r", encoding="utf-8") as gexf_file:
                        gexf_content = gexf_file.read()
                    os.unlink(f.name)

                return {
                    "format": "gexf",
                    "content": gexf_content,
                    "statistics": graph_data["statistics"],
                }
            else:
                raise ValueError(f"Unsupported format: {format_type}")

        except Exception as e:
            logger.error(f"Failed to export graph data: {str(e)}")
            raise
