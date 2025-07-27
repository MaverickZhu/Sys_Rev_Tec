import sqlite3
import os

db_path = 'test.db'
print(f'Database file path: {os.path.abspath(db_path)}')
print(f'Database file exists: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    print(f'Database file size: {os.path.getsize(db_path)} bytes')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f'\nNumber of tables found: {len(tables)}')
    print('All tables in database:')
    
    if tables:
        for table in tables:
            table_name = table[0]
            print(f'- {table_name}')
            
            # 获取表的行数
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'  Rows: {count}')
    else:
        print('No tables found in database')
    
    # 特别检查documents表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    documents_exists = cursor.fetchone() is not None
    print(f'\nDocuments table exists: {documents_exists}')
    
    if documents_exists:
        cursor.execute('SELECT * FROM documents LIMIT 5')
        rows = cursor.fetchall()
        print(f'Sample documents (first 5): {rows}')
        
except sqlite3.Error as e:
    print(f'Database error: {e}')
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'conn' in locals():
        conn.close()