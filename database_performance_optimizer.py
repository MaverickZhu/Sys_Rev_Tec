#!/usr/bin/env python3
"""
数据库性能优化工具

根据2025-08-04工作计划执行数据库性能优化任务：
1. 创建和优化数据库索引
2. 分析查询性能
3. 优化数据库配置
4. 生成性能报告

修复了事务处理和权限问题
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_optimization.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self, database_url: str = None):
        """初始化数据库优化器"""
        if database_url is None:
            # 默认连接到本地PostgreSQL
            database_url = "postgresql://sys_rev_user:CHANGE_PASSWORD@127.0.0.1:5432/sys_rev_tec_prod"
        
        try:
            self.engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
            logger.info(f"连接到数据库: {database_url}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def create_indexes(self) -> Dict[str, Any]:
        """创建数据库索引"""
        logger.info("开始创建数据库索引...")
        
        indexes = [
            # 项目表索引
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);",
            "CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(project_category);",
            "CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);",
            "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_projects_budget ON projects(budget);",
            
            # 文档表索引
            "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_documents_uploader_id ON documents(uploader_id);",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);",
            "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);",
            
            # 用户表索引
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
            
            # 审计日志表索引
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);",
            
            # 复合索引
            "CREATE INDEX IF NOT EXISTS idx_projects_owner_status ON projects(owner_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_documents_project_status ON documents(project_id, status);",
        ]
        
        results = {
            "total_indexes": len(indexes),
            "created_successfully": 0,
            "failed": 0,
            "details": []
        }
        
        with self.engine.connect() as connection:
            for index_sql in indexes:
                try:
                    connection.execute(text(index_sql))
                    index_name = index_sql.split()[5] if len(index_sql.split()) > 5 else "unknown"
                    results["created_successfully"] += 1
                    results["details"].append({
                        "index": index_name,
                        "status": "success",
                        "sql": index_sql
                    })
                    logger.info(f"✓ 索引创建成功: {index_name}")
                except Exception as e:
                    index_name = index_sql.split()[5] if len(index_sql.split()) > 5 else "unknown"
                    results["failed"] += 1
                    results["details"].append({
                        "index": index_name,
                        "status": "failed",
                        "error": str(e),
                        "sql": index_sql
                    })
                    logger.warning(f"✗ 索引创建失败: {index_name} - {str(e)}")
        
        logger.info(f"索引创建完成: 成功 {results['created_successfully']}, 失败 {results['failed']}")
        return results
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析数据库性能"""
        logger.info("开始分析数据库性能...")
        
        analysis_results = {
            "table_stats": [],
            "index_usage": [],
            "database_size": None,
            "connection_stats": None
        }
        
        queries = {
            "table_stats": """
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC;
            """,
            
            "index_usage": """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC;
            """,
            
            "database_size": """
                SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;
            """,
            
            "connection_stats": """
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity;
            """
        }
        
        with self.engine.connect() as connection:
            for query_name, query_sql in queries.items():
                try:
                    result = connection.execute(text(query_sql))
                    if query_name in ["database_size", "connection_stats"]:
                        row = result.fetchone()
                        if row:
                            analysis_results[query_name] = dict(row._mapping)
                    else:
                        analysis_results[query_name] = [dict(row._mapping) for row in result]
                    
                    logger.info(f"✓ 性能分析完成: {query_name}")
                except Exception as e:
                    logger.warning(f"✗ 性能分析失败: {query_name} - {str(e)}")
                    analysis_results[query_name] = []
        
        return analysis_results
    
    def optimize_settings(self) -> Dict[str, Any]:
        """优化数据库设置"""
        logger.info("开始优化数据库设置...")
        
        results = {
            "analyze_completed": False,
            "vacuum_completed": False,
            "reindex_completed": False,
            "details": []
        }
        
        # 使用独立连接执行ANALYZE
        try:
            with self.engine.connect() as connection:
                connection.execute(text("ANALYZE;"))
                results["analyze_completed"] = True
                results["details"].append({"operation": "ANALYZE", "status": "success"})
                logger.info("✓ ANALYZE 操作完成")
        except Exception as e:
            results["details"].append({"operation": "ANALYZE", "status": "failed", "error": str(e)})
            logger.warning(f"✗ ANALYZE 操作失败: {str(e)}")
        
        # VACUUM 需要在自动提交模式下执行
        try:
            with self.engine.connect() as connection:
                # 对每个用户表执行VACUUM
                tables_result = connection.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))
                tables = [row[0] for row in tables_result]
                
                for table in tables:
                    try:
                        connection.execute(text(f"VACUUM ANALYZE {table};"))
                        logger.info(f"✓ VACUUM ANALYZE 完成: {table}")
                    except Exception as e:
                        logger.warning(f"✗ VACUUM ANALYZE 失败: {table} - {str(e)}")
                
                results["vacuum_completed"] = True
                results["details"].append({"operation": "VACUUM", "status": "success"})
        except Exception as e:
            results["details"].append({"operation": "VACUUM", "status": "failed", "error": str(e)})
            logger.warning(f"✗ VACUUM 操作失败: {str(e)}")
        
        return results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整的性能优化报告"""
        logger.info("生成数据库优化报告...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_optimization": {
                "indexes": self.create_indexes(),
                "performance_analysis": self.analyze_performance(),
                "settings_optimization": self.optimize_settings()
            },
            "recommendations": [
                "定期运行 VACUUM ANALYZE 清理死元组并更新统计信息",
                "监控慢查询日志，优化执行时间超过100ms的查询",
                "检查未使用的索引，删除不必要的索引以减少写入开销",
                "对于大表，考虑分区策略",
                "配置合适的 shared_buffers 和 work_mem 参数",
                "监控数据库连接数，避免连接池耗尽",
                "定期备份数据库并测试恢复流程"
            ],
            "summary": {
                "total_tasks": 3,
                "completed_tasks": 0,
                "success_rate": 0.0
            }
        }
        
        # 计算成功率
        completed_tasks = 0
        if report["database_optimization"]["indexes"]["created_successfully"] > 0:
            completed_tasks += 1
        if report["database_optimization"]["performance_analysis"]["table_stats"]:
            completed_tasks += 1
        if report["database_optimization"]["settings_optimization"]["analyze_completed"]:
            completed_tasks += 1
        
        report["summary"]["completed_tasks"] = completed_tasks
        report["summary"]["success_rate"] = (completed_tasks / 3) * 100
        
        return report

def main():
    """主函数"""
    try:
        optimizer = DatabaseOptimizer()
        
        # 生成优化报告
        report = optimizer.generate_report()
        
        # 保存报告到文件
        with open('database_optimization_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        success_rate = report["summary"]["success_rate"]
        completed_tasks = report["summary"]["completed_tasks"]
        total_tasks = report["summary"]["total_tasks"]
        
        logger.info(f"数据库优化完成 - 成功率: {success_rate:.1f}% ({completed_tasks}/{total_tasks})")
        logger.info("优化报告已保存到: database_optimization_report.json")
        
        print(f"\n✅ 数据库优化完成！成功率: {success_rate:.1f}%")
        
        # 根据成功率返回退出码
        return 0 if success_rate >= 80 else 1
        
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        print(f"\n❌ 数据库优化失败: {e}")
        return 1

if __name__ == "__main__":
    exit(main())