#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能优化API端点
提供数据库查询优化、索引管理和性能监控功能
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import asyncio
import logging

from app.core.logger import logger
from app.api.deps import get_current_user
from app.models.user import User
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import text


router = APIRouter()


class QueryOptimizationRequest(BaseModel):
    """查询优化请求模型"""
    query: str = Field(..., description="SQL查询语句")
    analyze_only: bool = Field(default=True, description="仅分析不执行")
    timeout: int = Field(default=30, description="超时时间（秒）")


class IndexRecommendation(BaseModel):
    """索引建议模型"""
    table_name: str
    column_names: List[str]
    index_type: str
    estimated_benefit: float
    reason: str
    sql_statement: str


class QueryAnalysisResult(BaseModel):
    """查询分析结果模型"""
    query: str
    execution_plan: Dict[str, Any]
    estimated_cost: float
    estimated_rows: int
    optimization_suggestions: List[str]
    index_recommendations: List[IndexRecommendation]
    performance_score: float


class DatabaseStatsResponse(BaseModel):
    """数据库统计响应模型"""
    connection_count: int
    active_queries: int
    slow_queries_count: int
    cache_hit_ratio: float
    avg_query_time: float
    total_size_mb: float
    index_usage_stats: Dict[str, Any]
    last_updated: datetime


@router.get("/stats", summary="获取数据库性能统计")
async def get_database_stats(
    current_user: User = Depends(get_current_user)
):
    """
    获取数据库性能统计信息
    """
    db = SessionLocal()
    try:
        stats = {}
        
        # 获取连接统计
        connection_result = db.execute(text("""
            SELECT 
                count(*) as total_connections,
                count(CASE WHEN state = 'active' THEN 1 END) as active_connections
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """)).fetchone()
        
        stats['connection_count'] = connection_result.total_connections if connection_result else 0
        stats['active_queries'] = connection_result.active_connections if connection_result else 0
        
        # 获取慢查询统计
        slow_query_result = db.execute(text("""
            SELECT count(*) as slow_queries
            FROM pg_stat_statements 
            WHERE mean_exec_time > 1000
        """)).fetchone()
        
        stats['slow_queries_count'] = slow_query_result.slow_queries if slow_query_result else 0
        
        # 获取缓存命中率
        cache_result = db.execute(text("""
            SELECT 
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
            FROM pg_statio_user_tables
        """)).fetchone()
        
        stats['cache_hit_ratio'] = float(cache_result.cache_hit_ratio) if cache_result and cache_result.cache_hit_ratio else 0.0
        
        # 获取平均查询时间
        avg_time_result = db.execute(text("""
            SELECT avg(mean_exec_time) as avg_query_time
            FROM pg_stat_statements
        """)).fetchone()
        
        stats['avg_query_time'] = float(avg_time_result.avg_query_time) if avg_time_result and avg_time_result.avg_query_time else 0.0
        
        # 获取数据库大小
        size_result = db.execute(text("""
            SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
        """)).fetchone()
        
        stats['total_size_mb'] = float(size_result.size_mb) if size_result else 0.0
        
        # 获取索引使用统计
        index_stats = db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
            LIMIT 10
        """)).fetchall()
        
        stats['index_usage_stats'] = [
            {
                'schema': row.schemaname,
                'table': row.tablename,
                'index': row.indexname,
                'scans': row.idx_scan,
                'tuples_read': row.idx_tup_read,
                'tuples_fetched': row.idx_tup_fetch
            }
            for row in index_stats
        ]
        
        stats['last_updated'] = datetime.now()
        
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/analyze-query", summary="分析查询性能")
async def analyze_query(
    request: QueryOptimizationRequest,
    current_user: User = Depends(get_current_user)
) -> QueryAnalysisResult:
    """
    分析SQL查询的性能并提供优化建议
    """
    db = SessionLocal()
    try:
        query = request.query.strip()
        
        # 验证查询语句
        if not query or query.lower().startswith(('drop', 'delete', 'truncate', 'alter')):
            raise HTTPException(status_code=400, detail="不支持的查询类型")
        
        # 获取执行计划
        explain_query = f"EXPLAIN (ANALYZE {'' if request.analyze_only else 'true'}, BUFFERS, FORMAT JSON) {query}"
        
        try:
            result = db.execute(text(explain_query)).fetchone()
            execution_plan = result[0][0] if result else {}
        except Exception as e:
            logger.warning(f"获取执行计划失败: {e}")
            execution_plan = {"error": str(e)}
        
        # 分析执行计划并生成建议
        suggestions = _analyze_execution_plan(execution_plan)
        index_recommendations = _generate_index_recommendations(query, execution_plan)
        performance_score = _calculate_query_performance_score(execution_plan)
        
        return QueryAnalysisResult(
            query=query,
            execution_plan=execution_plan,
            estimated_cost=execution_plan.get('Plan', {}).get('Total Cost', 0),
            estimated_rows=execution_plan.get('Plan', {}).get('Plan Rows', 0),
            optimization_suggestions=suggestions,
            index_recommendations=index_recommendations,
            performance_score=performance_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/slow-queries", summary="获取慢查询列表")
async def get_slow_queries(
    limit: int = Query(20, description="返回数量限制", ge=1, le=100),
    min_duration: float = Query(1000.0, description="最小执行时间（毫秒）"),
    current_user: User = Depends(get_current_user)
):
    """
    获取慢查询列表
    """
    db = SessionLocal()
    try:
        slow_queries = db.execute(text("""
            SELECT 
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                max_exec_time,
                min_exec_time,
                stddev_exec_time,
                rows,
                100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            WHERE mean_exec_time > :min_duration
            ORDER BY mean_exec_time DESC 
            LIMIT :limit
        """), {"min_duration": min_duration, "limit": limit}).fetchall()
        
        queries_data = [
            {
                "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                "full_query": row.query,
                "calls": row.calls,
                "total_time_ms": float(row.total_exec_time),
                "avg_time_ms": float(row.mean_exec_time),
                "max_time_ms": float(row.max_exec_time),
                "min_time_ms": float(row.min_exec_time),
                "stddev_time_ms": float(row.stddev_exec_time) if row.stddev_exec_time else 0,
                "total_rows": row.rows,
                "cache_hit_percent": float(row.hit_percent) if row.hit_percent else 0
            }
            for row in slow_queries
        ]
        
        return {
            "status": "success",
            "data": {
                "queries": queries_data,
                "total_count": len(queries_data),
                "filter": {
                    "min_duration_ms": min_duration,
                    "limit": limit
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取慢查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/index-usage", summary="获取索引使用情况")
async def get_index_usage(
    table_name: Optional[str] = Query(None, description="表名过滤"),
    current_user: User = Depends(get_current_user)
):
    """
    获取索引使用情况统计
    """
    db = SessionLocal()
    try:
        base_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            JOIN pg_index ON pg_stat_user_indexes.indexrelid = pg_index.indexrelid
        """
        
        if table_name:
            query = base_query + " WHERE tablename = :table_name ORDER BY idx_scan DESC"
            params = {"table_name": table_name}
        else:
            query = base_query + " ORDER BY idx_scan DESC LIMIT 50"
            params = {}
        
        index_stats = db.execute(text(query), params).fetchall()
        
        # 查找未使用的索引
        unused_indexes = db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE idx_scan = 0
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 20
        """)).fetchall()
        
        return {
            "status": "success",
            "data": {
                "index_usage": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.idx_scan,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch,
                        "size": row.index_size
                    }
                    for row in index_stats
                ],
                "unused_indexes": [
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "size": row.index_size
                    }
                    for row in unused_indexes
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取索引使用情况失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/optimize-table", summary="优化表结构")
async def optimize_table(
    table_name: str = Body(..., description="表名"),
    operations: List[str] = Body(..., description="优化操作列表"),
    current_user: User = Depends(get_current_user)
):
    """
    执行表优化操作
    """
    db = SessionLocal()
    try:
        results = []
        
        for operation in operations:
            try:
                if operation == "vacuum":
                    # 执行VACUUM
                    db.execute(text(f"VACUUM ANALYZE {table_name}"))
                    results.append({"operation": "vacuum", "status": "success", "message": "表清理完成"})
                    
                elif operation == "reindex":
                    # 重建索引
                    db.execute(text(f"REINDEX TABLE {table_name}"))
                    results.append({"operation": "reindex", "status": "success", "message": "索引重建完成"})
                    
                elif operation == "analyze":
                    # 更新统计信息
                    db.execute(text(f"ANALYZE {table_name}"))
                    results.append({"operation": "analyze", "status": "success", "message": "统计信息更新完成"})
                    
                else:
                    results.append({"operation": operation, "status": "error", "message": "不支持的操作"})
                    
            except Exception as e:
                results.append({"operation": operation, "status": "error", "message": str(e)})
        
        db.commit()
        
        # 记录操作日志
        logger.info(f"用户 {current_user.username} 对表 {table_name} 执行了优化操作: {operations}")
        
        return {
            "status": "success",
            "data": {
                "table_name": table_name,
                "operations": results,
                "timestamp": datetime.now().isoformat()
            },
            "message": "表优化操作完成"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"表优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/recommendations", summary="获取优化建议")
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_user)
):
    """
    获取数据库优化建议
    """
    db = SessionLocal()
    try:
        recommendations = []
        
        # 检查未使用的索引
        unused_indexes = db.execute(text("""
            SELECT count(*) as count
            FROM pg_stat_user_indexes
            WHERE idx_scan = 0
        """)).fetchone()
        
        if unused_indexes and unused_indexes.count > 0:
            recommendations.append({
                "type": "index_cleanup",
                "priority": "medium",
                "title": "清理未使用的索引",
                "description": f"发现 {unused_indexes.count} 个未使用的索引，建议删除以节省存储空间",
                "action": "review_unused_indexes"
            })
        
        # 检查慢查询
        slow_queries = db.execute(text("""
            SELECT count(*) as count
            FROM pg_stat_statements
            WHERE mean_exec_time > 1000
        """)).fetchone()
        
        if slow_queries and slow_queries.count > 0:
            recommendations.append({
                "type": "query_optimization",
                "priority": "high",
                "title": "优化慢查询",
                "description": f"发现 {slow_queries.count} 个慢查询，建议进行优化",
                "action": "analyze_slow_queries"
            })
        
        # 检查缓存命中率
        cache_hit = db.execute(text("""
            SELECT 
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as hit_ratio
            FROM pg_statio_user_tables
        """)).fetchone()
        
        if cache_hit and cache_hit.hit_ratio and cache_hit.hit_ratio < 90:
            recommendations.append({
                "type": "memory_tuning",
                "priority": "medium",
                "title": "调整内存配置",
                "description": f"缓存命中率为 {cache_hit.hit_ratio:.1f}%，建议增加shared_buffers",
                "action": "tune_memory_settings"
            })
        
        # 检查表膨胀
        bloated_tables = db.execute(text("""
            SELECT count(*) as count
            FROM pg_stat_user_tables
            WHERE n_dead_tup > n_live_tup * 0.1
        """)).fetchone()
        
        if bloated_tables and bloated_tables.count > 0:
            recommendations.append({
                "type": "maintenance",
                "priority": "medium",
                "title": "执行表维护",
                "description": f"发现 {bloated_tables.count} 个表需要VACUUM操作",
                "action": "schedule_vacuum"
            })
        
        return {
            "status": "success",
            "data": {
                "recommendations": recommendations,
                "total_count": len(recommendations),
                "generated_at": datetime.now().isoformat()
            },
            "message": "优化建议生成完成"
        }
        
    except Exception as e:
        logger.error(f"生成优化建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


def _analyze_execution_plan(plan: Dict[str, Any]) -> List[str]:
    """
    分析执行计划并生成优化建议
    """
    suggestions = []
    
    if not plan or 'Plan' not in plan:
        return ["无法获取执行计划"]
    
    plan_node = plan['Plan']
    
    # 检查顺序扫描
    if plan_node.get('Node Type') == 'Seq Scan':
        suggestions.append("发现顺序扫描，考虑添加索引")
    
    # 检查嵌套循环
    if plan_node.get('Node Type') == 'Nested Loop':
        suggestions.append("发现嵌套循环连接，检查连接条件是否有索引")
    
    # 检查排序操作
    if plan_node.get('Node Type') == 'Sort':
        suggestions.append("发现排序操作，考虑添加排序字段的索引")
    
    # 检查高成本操作
    if plan_node.get('Total Cost', 0) > 1000:
        suggestions.append("查询成本较高，建议优化查询逻辑")
    
    return suggestions


def _generate_index_recommendations(query: str, plan: Dict[str, Any]) -> List[IndexRecommendation]:
    """
    基于查询和执行计划生成索引建议
    """
    recommendations = []
    
    # 这里可以实现更复杂的索引推荐逻辑
    # 目前提供基础示例
    
    if 'WHERE' in query.upper() and 'ORDER BY' in query.upper():
        recommendations.append(IndexRecommendation(
            table_name="example_table",
            column_names=["column1", "column2"],
            index_type="btree",
            estimated_benefit=0.8,
            reason="查询包含WHERE和ORDER BY条件",
            sql_statement="CREATE INDEX idx_example ON example_table (column1, column2);"
        ))
    
    return recommendations


def _calculate_query_performance_score(plan: Dict[str, Any]) -> float:
    """
    计算查询性能评分（0-100分）
    """
    if not plan or 'Plan' not in plan:
        return 0.0
    
    plan_node = plan['Plan']
    cost = plan_node.get('Total Cost', 0)
    
    # 简单的评分算法
    if cost < 10:
        return 95.0
    elif cost < 100:
        return 80.0
    elif cost < 1000:
        return 60.0
    elif cost < 10000:
        return 40.0
    else:
        return 20.0