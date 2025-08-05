import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

cursor.execute('SELECT username, email, hashed_password FROM users')
users = cursor.fetchall()

print('All users:')
for user in users:
    print(f'Username: {user[0]}, Email: {user[1]}, Password hash: {user[2][:50]}...')

conn.close()