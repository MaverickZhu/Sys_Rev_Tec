from fastapi import status
from sqlalchemy import text

from app.db.session import engine

"""
数据库查询性能优化

本文件包含数据库索引创建和查询优化的相关配置。

针对系统中的常用查询场景，添加合适的索引以提升查询性能。
"""


def create_database_indexes():
    """创建数据库索引以优化查询性能"""

    indexes = [
        # 项目表索引
        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);",
        "CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(project_category);",
        "CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);",
        "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_projects_budget_amount ON projects(budget_amount);",
        "CREATE INDEX IF NOT EXISTS idx_projects_procurement_method ON projects(procurement_method);",
        "CREATE INDEX IF NOT EXISTS idx_projects_review_stage ON projects(review_stage);",
        "CREATE INDEX IF NOT EXISTS idx_projects_risk_level ON projects(risk_level);",
        "CREATE INDEX IF NOT EXISTS idx_projects_tags ON projects USING gin(tags);",  # GIN索引用于JSON数组搜索
        # 文档表索引
        "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_documents_uploader_id ON documents(uploader_id);",
        "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_document_category ON documents(document_category);",
        "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);",
        "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_documents_is_processed ON documents(is_processed);",
        "CREATE INDEX IF NOT EXISTS idx_documents_is_ocr_processed ON documents(is_ocr_processed);",
        "CREATE INDEX IF NOT EXISTS idx_documents_review_stage ON documents(review_stage);",
        "CREATE INDEX IF NOT EXISTS idx_documents_compliance_status ON documents(compliance_status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);",
        # OCR结果表索引
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_document_id ON ocr_results(document_id);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_processed_by ON ocr_results(processed_by);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_status ON ocr_results(status);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_ocr_engine ON ocr_results(ocr_engine);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_created_at ON ocr_results(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_filename ON ocr_results(filename);",
        # 用户表索引
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);",
        "CREATE INDEX IF NOT EXISTS idx_users_reviewer_level ON users(reviewer_level);",
        "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);",
        # 角色表索引
        "CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);",
        "CREATE INDEX IF NOT EXISTS idx_roles_is_active ON roles(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_roles_parent_role_id ON roles(parent_role_id);",
        "CREATE INDEX IF NOT EXISTS idx_roles_level ON roles(level);",
        # 用户会话表索引
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);",
        # 审计日志表索引
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_status ON audit_logs(status);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address ON audit_logs(ip_address);",
        # 问题表索引
        "CREATE INDEX IF NOT EXISTS idx_issues_project_id ON issues(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_issues_reporter_id ON issues(reporter_id);",
        "CREATE INDEX IF NOT EXISTS idx_issues_assignee_id ON issues(assignee_id);",
        "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);",
        "CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority);",
        "CREATE INDEX IF NOT EXISTS idx_issues_issue_type ON issues(issue_type);",
        "CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_issues_due_date ON issues(due_date);",
        # 项目对比表索引
        "CREATE INDEX IF NOT EXISTS idx_project_comparisons_project_a_id ON project_comparisons(project_a_id);",
        "CREATE INDEX IF NOT EXISTS idx_project_comparisons_project_b_id ON project_comparisons(project_b_id);",
        "CREATE INDEX IF NOT EXISTS idx_project_comparisons_comparison_type ON project_comparisons(comparison_type);",
        "CREATE INDEX IF NOT EXISTS idx_project_comparisons_created_by ON project_comparisons(created_by);",
        "CREATE INDEX IF NOT EXISTS idx_project_comparisons_created_at ON project_comparisons(created_at);",
        # 文档标注表索引
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_document_id ON document_annotations(document_id);",
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_annotator_id ON document_annotations(annotator_id);",
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_annotation_type ON document_annotations(annotation_type);",
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_status ON document_annotations(status);",
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_importance ON document_annotations(importance);",
        "CREATE INDEX IF NOT EXISTS idx_document_annotations_created_at ON document_annotations(created_at);",
        # 合规性检查表索引
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_document_id ON compliance_checks(document_id);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_rule_id ON compliance_checks(rule_id);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_check_result ON compliance_checks(check_result);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_checker_id ON compliance_checks(checker_id);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_check_method ON compliance_checks(check_method);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_created_at ON compliance_checks(created_at);",
        # 合规规则表索引
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_rule_code ON compliance_rules(rule_code);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_category ON compliance_rules(category);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_subcategory ON compliance_rules(subcategory);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_applicable_stage ON compliance_rules(applicable_stage);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_severity ON compliance_rules(severity);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_is_active ON compliance_rules(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_is_automated ON compliance_rules(is_automated);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_rules_effective_date ON compliance_rules(effective_date);",
        # 复合索引 - 针对常用的多字段查询
        "CREATE INDEX IF NOT EXISTS idx_projects_owner_status ON projects(owner_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_projects_category_status ON projects(project_category, status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_project_status ON documents(project_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_project_category ON documents(project_id, document_category);",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_document_status ON ocr_results(document_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_users_role_active ON users(role_id, is_active);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);",
        "CREATE INDEX IF NOT EXISTS idx_issues_project_status ON issues(project_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_compliance_checks_document_result ON compliance_checks(document_id, check_result);",
        # 全文搜索索引 (PostgreSQL)
        "CREATE INDEX IF NOT EXISTS idx_projects_title_search ON projects USING gin(to_tsvector('chinese', title));",
        "CREATE INDEX IF NOT EXISTS idx_projects_description_search ON projects USING gin(to_tsvector('chinese', description));",
        "CREATE INDEX IF NOT EXISTS idx_documents_extracted_text_search ON documents USING gin(to_tsvector('chinese', extracted_text));",
        "CREATE INDEX IF NOT EXISTS idx_documents_ocr_text_search ON documents USING gin(to_tsvector('chinese', ocr_text));",
        "CREATE INDEX IF NOT EXISTS idx_ocr_results_text_search ON ocr_results USING gin(to_tsvector('chinese', extracted_text));",
    ]

    with engine.connect() as connection:
        for index_sql in indexes:
            try:
                connection.execute(text(index_sql))
                print(f"✓ 索引创建成功: {index_sql.split()[5]}")
            except Exception as e:
                print(f"✗ 索引创建失败: {index_sql.split()[5]} - {str(e)}")

        connection.commit()

    print("数据库索引优化完成！")


def analyze_query_performance():
    """分析查询性能并提供优化建议"""

    performance_queries = [
        # 检查表大小
        """
        SELECT
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats
        WHERE schemaname = 'public'
        ORDER BY tablename, attname;
        """,
        # 检查索引使用情况
        """
        SELECT
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC;
        """,
        # 检查慢查询
        """
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements
        WHERE mean_time > 100
        ORDER BY mean_time DESC
        LIMIT 10;
        """,
        # 检查表的统计信息
        """
        SELECT
            schemaname,
            tablename,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
        """,
    ]

    with engine.connect() as connection:
        for i, query in enumerate(performance_queries, 1):
            try:
                result = connection.execute(text(query))
                print(f"\n=== 性能分析查询 {i} ===")
                for row in result:
                    print(row)
            except Exception as e:
                print(f"查询 {i} 执行失败: {str(e)}")


def optimize_database_settings():
    """优化数据库设置"""

    optimization_queries = [
        # 更新表统计信息
        "ANALYZE;",
        # 清理死元组
        "VACUUM ANALYZE;",
        # 重建索引（如果需要）
        "REINDEX DATABASE postgres;",
    ]

    with engine.connect() as connection:
        for query in optimization_queries:
            try:
                connection.execute(text(query))
                print(f"✓ 优化操作完成: {query}")
            except Exception as e:
                print(f"✗ 优化操作失败: {query} - {str(e)}")

        connection.commit()

    print("数据库优化完成！")


def get_database_performance_report():
    """获取数据库性能报告"""

    report = {
        "table_sizes": [],
        "index_usage": [],
        "slow_queries": [],
        "recommendations": [],
    }

    # 获取表大小信息
    table_size_query = """
    SELECT
        tablename,
        pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
        pg_total_relation_size(tablename::regclass) as size_bytes
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(tablename::regclass) DESC;
    """

    # 获取索引使用情况
    index_usage_query = """
    SELECT
        indexrelname as index_name,
        relname as table_name,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes
    JOIN pg_stat_user_tables ON pg_stat_user_indexes.relid = pg_stat_user_tables.relid
    ORDER BY idx_scan DESC;
    """

    with engine.connect() as connection:
        try:
            # 获取表大小
            result = connection.execute(text(table_size_query))
            report["table_sizes"] = [dict(row) for row in result]

            # 获取索引使用情况
            result = connection.execute(text(index_usage_query))
            report["index_usage"] = [dict(row) for row in result]

        except Exception as e:
            print(f"获取性能报告失败: {str(e)}")

    # 生成优化建议
    recommendations = [
        "定期运行 VACUUM ANALYZE 清理死元组并更新统计信息",
        "监控慢查询日志，优化执行时间超过100ms的查询",
        "检查未使用的索引，删除不必要的索引以减少写入开销",
        "对于大表，考虑分区策略",
        "定期检查表的膨胀率，必要时进行 VACUUM FULL",
        "监控数据库连接数，避免连接池耗尽",
        "配置合适的 shared_buffers 和 work_mem 参数",
    ]

    report["recommendations"] = recommendations

    return report


if __name__ == "__main__":
    print("开始数据库优化...")
    create_database_indexes()
    analyze_query_performance()
    optimize_database_settings()

    print("\n生成性能报告...")
    report = get_database_performance_report()
    print(f"发现 {len(report['table_sizes'])} 个表")
    print(f"发现 {len(report['index_usage'])} 个索引")
    print("\n优化建议:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")
