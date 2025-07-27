import sqlite3

try:
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print('All tables in database:')
    table_names = [table[0] for table in tables]
    for table_name in table_names:
        print(f'- {table_name}')
    
    # 检查documents表是否存在
    documents_table_exists = 'documents' in table_names
    print(f'\nDocuments table exists: {documents_table_exists}')
    
    if documents_table_exists:
        cursor.execute('SELECT id, filename FROM documents ORDER BY id')
        rows = cursor.fetchall()
        print('\nDocuments in database:')
        for row in rows:
            print(f'ID: {row[0]}, Filename: {row[1]}')
        print(f'Total documents: {len(rows)}')
    else:
        print('\nDocuments table does not exist')
        
except sqlite3.Error as e:
    print(f'Database error: {e}')
except Exception as e:
    print(f'Error: {e}')
finally:
    if 'conn' in locals():
        conn.close()