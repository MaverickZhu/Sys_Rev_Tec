from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 检查所有表
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [row[0] for row in result]
    print(f"数据库中的表: {tables}")
    
    # 如果users表存在，检查其结构
    if 'users' in tables:
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = list(result)
        print(f"users表结构: {columns}")
    else:
        print("users表不存在")
        
finally:
    db.close()