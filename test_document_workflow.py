#!/usr/bin/env python3
"""
文档工作流测试脚本
测试完整的文档上传、搜索和管理流程
"""

import requests
import json
from pathlib import Path
import tempfile
import os
import random
import string

# API基础URL
BASE_URL = "http://localhost:8001/api/v1"

def create_test_user():
    """创建测试用户"""
    # 生成随机用户名避免冲突
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    username = f"testuser_{random_suffix}"
    
    user_data = {
        "username": username,
        "email": f"test_{random_suffix}@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code == 200:
        user_info = response.json()
        print(f"✅ 用户创建成功: {user_info['username']}")
        return user_info
    else:
        print(f"❌ 用户创建失败: {response.text}")
        return None

def login_user(username, password):
    """用户登录获取token"""
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/login/access-token", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ 登录成功，获取到token")
        return token
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def create_test_project(token):
    """创建测试项目"""
    headers = {"Authorization": f"Bearer {token}"}
    # 生成随机项目编号避免冲突
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    project_code = f"TEST-{random_suffix}"
    
    project_data = {
        "name": "测试项目",
        "description": "用于测试文档管理功能的项目",
        "project_code": project_code,
        "project_type": "货物",
        "priority": "medium",
        "risk_level": "low"
    }
    
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    if response.status_code == 200:
        project = response.json()
        print(f"✅ 项目创建成功: {project['name']} (ID: {project['id']})")
        return project
    else:
        print(f"❌ 项目创建失败: {response.text}")
        return None

def create_test_document():
    """创建测试文档文件"""
    # 创建临时文本文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是一个测试文档\n")
        f.write("包含一些测试内容用于搜索\n")
        f.write("文档管理系统测试\n")
        f.write("关键词: 测试, 文档, 搜索, 管理")
        return f.name

def upload_document(token, project_id, file_path):
    """上传文档到项目"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/plain')}
        data = {
            'document_category': '技术文档',
            'document_type': '测试文档',
            'summary': '这是一个用于测试搜索功能的文档'
        }
        
        response = requests.post(
            f"{BASE_URL}/documents/upload/{project_id}", 
            files=files, 
            data=data, 
            headers=headers
        )
    
    if response.status_code == 200:
        result = response.json()
        document = result['data']
        print(f"✅ 文档上传成功: {document['filename']} (ID: {document['document_id']})")
        return document
    else:
        print(f"❌ 文档上传失败: {response.text}")
        return None

def search_documents(token, query, project_id=None):
    """搜索文档"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {'q': query}
    if project_id:
        params['project_id'] = project_id
    
    response = requests.get(f"{BASE_URL}/documents/search", params=params, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        result = response_data['data']
        print(f"✅ 搜索成功: 找到 {result['total']} 个文档")
        for doc in result['documents']:
            print(f"   - {doc['filename']} (匹配度: {doc.get('match_score', 0)})")
        return result
    else:
        print(f"❌ 搜索失败: {response.text}")
        return None

def get_project_documents(token, project_id):
    """获取项目文档列表"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/documents/project/{project_id}", headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        result = response_data['data']
        print(f"✅ 获取项目文档成功: 共 {result['total']} 个文档")
        for doc in result['documents']:
            print(f"   - {doc['filename']} ({doc['document_category']})")
        return result
    else:
        print(f"❌ 获取项目文档失败: {response.text}")
        return None

def main():
    """主测试流程"""
    print("🚀 开始文档管理系统工作流测试\n")
    
    # 1. 创建用户
    print("1️⃣ 创建测试用户...")
    user = create_test_user()
    if not user:
        return
    
    # 2. 用户登录
    print("\n2️⃣ 用户登录...")
    token = login_user(user['username'], "testpassword123")
    if not token:
        return
    
    # 3. 创建项目
    print("\n3️⃣ 创建测试项目...")
    project = create_test_project(token)
    if not project:
        return
    
    # 4. 创建并上传文档
    print("\n4️⃣ 创建并上传测试文档...")
    test_file = create_test_document()
    try:
        document = upload_document(token, project['id'], test_file)
        if not document:
            return
    finally:
        # 清理临时文件
        os.unlink(test_file)
    
    # 5. 获取项目文档列表
    print("\n5️⃣ 获取项目文档列表...")
    get_project_documents(token, project['id'])
    
    # 6. 测试文档搜索
    print("\n6️⃣ 测试文档搜索功能...")
    search_documents(token, "测试")
    search_documents(token, "文档")
    search_documents(token, "管理")
    search_documents(token, "不存在的关键词")
    
    # 7. 在特定项目中搜索
    print("\n7️⃣ 在特定项目中搜索...")
    search_documents(token, "测试", project['id'])
    
    print("\n🎉 文档管理系统工作流测试完成！")

if __name__ == "__main__":
    main()