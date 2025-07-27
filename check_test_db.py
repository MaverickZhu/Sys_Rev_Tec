import sqlite3
import os

def check_test_db():
    db_path = 'test.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # 检查文档表
    if tables:
        try:
            cursor.execute("SELECT id, filename, original_filename FROM documents;")
            docs = cursor.fetchall()
            print(f"Documents: {docs}")
        except Exception as e:
            print(f"Error querying documents: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_test_db()