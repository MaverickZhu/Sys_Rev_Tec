#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查询性能分析工具
用于分析API端点的数据库查询性能，识别慢查询和N+1查询问题
"""

import time
import logging
from sqlalchemy import event, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_performance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabasePerformanceAnalyzer:
    """数据库性能分析器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # 性能统计数据
        self.query_stats = defaultdict(list)
        self.slow_queries = []
        self.query_patterns = Counter()
        self.total_queries = 0
        self.total_time = 0
        
        # 配置查询监听器
        self._setup_query_listeners()
    
    def _setup_query_listeners(self):
        """设置查询监听器"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
            context._query_parameters = parameters
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                total_time = time.time() - context._query_start_time
                
                # 统计查询信息
                self.total_queries += 1
                self.total_time += total_time
                
                # 记录查询模式
                query_pattern = self._extract_query_pattern(statement)
                self.query_patterns[query_pattern] += 1
                
                # 记录查询统计
                self.query_stats[query_pattern].append({
                    'time': total_time,
                    'statement': statement[:200] + '...' if len(statement) > 200 else statement,
                    'parameters': str(parameters)[:100] if parameters else None,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 记录慢查询
                if total_time > 0.1:  # 超过100ms的查询
                    self.slow_queries.append({
                        'time': total_time,
                        'statement': statement,
                        'parameters': parameters,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.warning(f"慢查询检测: {total_time:.3f}s - {statement[:100]}...")
    
    def _extract_query_pattern(self, statement: str) -> str:
        """提取查询模式"""
        # 简化SQL语句，提取查询模式
        statement = statement.strip().upper()
        
        if statement.startswith('SELECT'):
            # 提取表名
            if ' FROM ' in statement:
                parts = statement.split(' FROM ')[1].split()
                table_name = parts[0] if parts else 'unknown'
                return f"SELECT_FROM_{table_name}"
            return "SELECT_UNKNOWN"
        elif statement.startswith('INSERT'):
            if ' INTO ' in statement:
                parts = statement.split(' INTO ')[1].split()
                table_name = parts[0] if parts else 'unknown'
                return f"INSERT_INTO_{table_name}"
            return "INSERT_UNKNOWN"
        elif statement.startswith('UPDATE'):
            parts = statement.split()
            table_name = parts[1] if len(parts) > 1 else 'unknown'
            return f"UPDATE_{table_name}"
        elif statement.startswith('DELETE'):
            if ' FROM ' in statement:
                parts = statement.split(' FROM ')[1].split()
                table_name = parts[0] if parts else 'unknown'
                return f"DELETE_FROM_{table_name}"
            return "DELETE_UNKNOWN"
        else:
            return "OTHER"
    
    def analyze_table_indexes(self) -> Dict:
        """分析表索引情况"""
        logger.info("分析数据库表索引...")
        
        index_info = {}
        session = self.Session()
        
        try:
            # 获取所有表名
            tables_result = session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ))
            tables = [row[0] for row in tables_result]
            
            for table in tables:
                # 获取表的索引信息
                indexes_result = session.execute(text(f"PRAGMA index_list('{table}')"))
                indexes = []
                
                for index_row in indexes_result:
                    index_name = index_row[1]
                    # 获取索引详细信息
                    index_info_result = session.execute(text(f"PRAGMA index_info('{index_name}')"))
                    columns = [col_row[2] for col_row in index_info_result]
                    indexes.append({
                        'name': index_name,
                        'columns': columns,
                        'unique': bool(index_row[2])
                    })
                
                index_info[table] = indexes
                logger.info(f"表 {table}: {len(indexes)} 个索引")
        
        except Exception as e:
            logger.error(f"分析索引时出错: {e}")
        finally:
            session.close()
        
        return index_info
    
    def suggest_indexes(self) -> List[str]:
        """建议添加的索引"""
        suggestions = []
        
        # 基于查询模式建议索引
        for pattern, count in self.query_patterns.most_common(10):
            if 'SELECT_FROM_' in pattern:
                table_name = pattern.replace('SELECT_FROM_', '').lower()
                
                # 检查是否有WHERE子句的常用字段
                queries = self.query_stats.get(pattern, [])
                if queries:
                    # 分析查询语句中的WHERE条件
                    common_conditions = self._analyze_where_conditions(queries)
                    for condition in common_conditions:
                        suggestions.append(
                            f"CREATE INDEX idx_{table_name}_{condition} ON {table_name}({condition});"
                        )
        
        # 通用索引建议
        common_suggestions = [
            "CREATE INDEX idx_projects_status ON projects(status);",
            "CREATE INDEX idx_projects_created_at ON projects(created_at);",
            "CREATE INDEX idx_users_username ON users(username);",
            "CREATE INDEX idx_users_email ON users(email);",
            "CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);",
            "CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);"
        ]
        
        suggestions.extend(common_suggestions)
        return list(set(suggestions))  # 去重
    
    def _analyze_where_conditions(self, queries: List[Dict]) -> List[str]:
        """分析WHERE条件中的常用字段"""
        conditions = []
        
        for query in queries:
            statement = query['statement'].upper()
            if ' WHERE ' in statement:
                where_part = statement.split(' WHERE ')[1]
                # 简单的字段提取（实际应用中可能需要更复杂的解析）
                if 'STATUS' in where_part:
                    conditions.append('status')
                if 'CREATED_AT' in where_part:
                    conditions.append('created_at')
                if 'USER_ID' in where_part:
                    conditions.append('user_id')
                if 'USERNAME' in where_part:
                    conditions.append('username')
        
        return list(set(conditions))
    
    def generate_performance_report(self) -> Dict:
        """生成性能报告"""
        logger.info("生成性能分析报告...")
        
        # 计算统计信息
        avg_query_time = self.total_time / self.total_queries if self.total_queries > 0 else 0
        slow_query_percentage = len(self.slow_queries) / self.total_queries * 100 if self.total_queries > 0 else 0
        
        # 查询模式统计
        pattern_stats = {}
        for pattern, queries in self.query_stats.items():
            times = [q['time'] for q in queries]
            pattern_stats[pattern] = {
                'count': len(queries),
                'avg_time': sum(times) / len(times) if times else 0,
                'max_time': max(times) if times else 0,
                'min_time': min(times) if times else 0
            }
        
        report = {
            'summary': {
                'total_queries': self.total_queries,
                'total_time': self.total_time,
                'avg_query_time': avg_query_time,
                'slow_queries_count': len(self.slow_queries),
                'slow_query_percentage': slow_query_percentage,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'query_patterns': dict(self.query_patterns.most_common(10)),
            'pattern_statistics': pattern_stats,
            'slow_queries': self.slow_queries[:10],  # 只显示前10个慢查询
            'index_analysis': self.analyze_table_indexes(),
            'index_suggestions': self.suggest_indexes()
        }
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f"db_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"性能报告已保存到: {filename}")
        return filename
    
    def print_summary(self, report: Dict):
        """打印报告摘要"""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("数据库性能分析报告")
        print("="*60)
        print(f"总查询数: {summary['total_queries']}")
        print(f"总耗时: {summary['total_time']:.3f}s")
        print(f"平均查询时间: {summary['avg_query_time']:.3f}s")
        print(f"慢查询数量: {summary['slow_queries_count']}")
        print(f"慢查询比例: {summary['slow_query_percentage']:.1f}%")
        
        print("\n最常见的查询模式:")
        for pattern, count in list(report['query_patterns'].items())[:5]:
            stats = report['pattern_statistics'].get(pattern, {})
            print(f"  {pattern}: {count}次, 平均耗时: {stats.get('avg_time', 0):.3f}s")
        
        if report['slow_queries']:
            print("\n慢查询示例:")
            for i, query in enumerate(report['slow_queries'][:3], 1):
                print(f"  {i}. {query['time']:.3f}s - {query['statement'][:80]}...")
        
        print("\n索引建议:")
        for suggestion in report['index_suggestions'][:5]:
            print(f"  {suggestion}")
        
        print("="*60)

def main():
    """主函数"""
    # 数据库连接配置
    DATABASE_URL = "sqlite:///./app/app.db"
    
    print("启动数据库性能分析...")
    analyzer = DatabasePerformanceAnalyzer(DATABASE_URL)
    
    print("分析器已启动，正在监控数据库查询...")
    print("请在另一个终端中运行API服务并执行一些操作")
    print("按 Ctrl+C 停止监控并生成报告")
    
    try:
        # 模拟一些查询来测试分析器
        session = analyzer.Session()
        
        # 执行一些测试查询
        test_queries = [
            "SELECT * FROM users WHERE username = 'admin'",
            "SELECT * FROM projects WHERE status = 'active'",
            "SELECT COUNT(*) FROM audit_logs WHERE timestamp > datetime('now', '-1 day')",
            "SELECT p.*, u.username FROM projects p JOIN users u ON p.created_by = u.id"
        ]
        
        print("\n执行测试查询...")
        for query in test_queries:
            try:
                result = session.execute(text(query))
                result.fetchall()
                print(f"✓ 执行查询: {query[:50]}...")
                time.sleep(0.1)  # 模拟查询间隔
            except Exception as e:
                print(f"✗ 查询失败: {query[:50]}... - {e}")
        
        session.close()
        
        # 等待用户操作
        input("\n按回车键生成性能报告...")
        
    except KeyboardInterrupt:
        print("\n停止监控...")
    
    # 生成并保存报告
    report = analyzer.generate_performance_report()
    filename = analyzer.save_report(report)
    analyzer.print_summary(report)
    
    print(f"\n详细报告已保存到: {filename}")

if __name__ == "__main__":
    main()