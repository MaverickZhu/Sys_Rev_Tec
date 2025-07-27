#!/usr/bin/env python3

import requests
import json
from app.main import app
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.db.session import SessionLocal
from tests.utils.user import create_random_user

# 创建测试客户端
client = TestClient(app)

# 创建测试用户和认证头
db = SessionLocal()
try:
    user = create_random_user(db)
    access_token = create_access_token(subject=str(user.id))
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"Created user with ID: {user.id}")
    print(f"Access token: {access_token[:50]}...")
    
    # 测试搜索端点
    print("\nTesting search endpoint with auth...")
    response = client.get(f"{settings.API_V1_STR}/documents/search?q=test", headers=auth_headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Content: {response.text}")
    
    if response.status_code != 200:
        try:
            error_data = response.json()
            print(f"Error Details: {json.dumps(error_data, indent=2)}")
        except:
            print("Could not parse error response as JSON")
            
finally:
    db.close()

# 测试路由是否存在
print("\nTesting if route exists...")
from app.api.v1.api import api_router
print(f"Available routes:")
for route in api_router.routes:
    if hasattr(route, 'path'):
        print(f"  {route.methods} {route.path}")