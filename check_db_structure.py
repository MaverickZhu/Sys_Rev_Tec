#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库结构
"""

import sqlite3
import os

def check_database_structure():
    """检查数据库结构"""
    db_path = './app/app.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    print(f"检查数据库: {db_path}")
    print("="*50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("数据库中没有表")
            return
        
        print(f"数据库中的表 ({len(tables)}个):")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 表: {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            if columns:
                print("  字段:")
                for col in columns:
                    col_id, name, data_type, not_null, default_val, pk = col
                    pk_str = " (主键)" if pk else ""
                    not_null_str = " NOT NULL" if not_null else ""
                    default_str = f" DEFAULT {default_val}" if default_val else ""
                    print(f"    - {name}: {data_type}{not_null_str}{default_str}{pk_str}")
            
            # 获取表中的记录数
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"  记录数: {count}")
            except Exception as e:
                print(f"  记录数: 无法获取 ({e})")
            
            # 获取索引信息
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            if indexes:
                print("  索引:")
                for idx in indexes:
                    idx_name = idx[1]
                    unique = "唯一" if idx[2] else "普通"
                    print(f"    - {idx_name} ({unique})")
        
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database_structure()