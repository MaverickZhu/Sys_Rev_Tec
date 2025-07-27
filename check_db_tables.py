import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("数据库中的表:")
for table in tables:
    print(f"- {table[0]}")

# 检查users表是否存在
if ('users',) in tables:
    print("\nusers表存在")
    # 获取users表的结构
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print("users表结构:")
    for col in columns:
        print(f"  {col[1]} {col[2]}")
else:
    print("\nusers表不存在")

conn.close()