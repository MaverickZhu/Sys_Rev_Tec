import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 检查表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name;')
tables = cursor.fetchall()
print('Tables:', [t[0] for t in tables])

# 检查用户数量
try:
    cursor.execute('SELECT COUNT(*) FROM users;')
    user_count = cursor.fetchone()[0]
    print(f'User count: {user_count}')
    
    if user_count > 0:
        cursor.execute('SELECT id, username, email, is_superuser FROM users LIMIT 5;')
        users = cursor.fetchall()
        print('Users:', users)
except Exception as e:
    print(f'Error querying users: {e}')

# 检查角色和权限
try:
    cursor.execute('SELECT COUNT(*) FROM roles;')
    role_count = cursor.fetchone()[0]
    print(f'Role count: {role_count}')
    
    cursor.execute('SELECT COUNT(*) FROM permissions;')
    perm_count = cursor.fetchone()[0]
    print(f'Permission count: {perm_count}')
except Exception as e:
    print(f'Error querying roles/permissions: {e}')

conn.close()