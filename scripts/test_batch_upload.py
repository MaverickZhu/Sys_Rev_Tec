#!/usr/bin/env python3
"""
批量文档上传功能测试脚本

测试批量上传API的功能，包括：
1. 批量上传多个文件
2. 文件类型验证
3. 文件数量限制
4. 错误处理
"""

import requests
import json
import tempfile
import os
from pathlib import Path

# API配置
BASE_URL = "http://localhost:8001/api/v1"
headers = {"Content-Type": "application/json"}

def create_test_user():
    """创建测试用户"""
    import random
    import time
    random_suffix = random.randint(10000, 99999)
    user_data = {
        "username": f"batchtest_{random_suffix}_{int(time.time())}",
        "email": f"batchtest_{random_suffix}_{int(time.time())}@example.com",
        "password": "testpassword123",
        "full_name": "Batch Test User"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data, headers=headers)
    if response.status_code == 200:
        print("✓ 测试用户创建成功")
        return response.json(), user_data
    else:
        print(f"✗ 用户创建失败: {response.text}")
        return None, None

def login_user(username, password):
    """用户登录"""
    login_data = {
        "username": username,
        "password": password
    }
    
    # 使用form data格式而不是JSON
    response = requests.post(f"{BASE_URL}/login/access-token", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print("✓ 用户登录成功")
        return token
    else:
        print(f"✗ 用户登录失败: {response.text}")
        return None

def create_test_project(token):
    """创建测试项目"""
    import time
    project_data = {
        "name": "批量上传测试项目",
        "description": "用于测试批量文档上传功能的项目",
        "project_code": f"BATCH-TEST-{int(time.time())}",
        "project_type": "货物"
    }
    
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=auth_headers)
    if response.status_code == 200:
        result = response.json()
        project_id = result["id"]
        print("✓ 测试项目创建成功")
        return project_id
    else:
        print(f"✗ 项目创建失败: {response.text}")
        return None

def create_test_files():
    """创建测试文件"""
    test_files = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建不同类型的测试文件
    files_to_create = [
        ("test_document1.txt", "这是第一个测试文档的内容。\n包含一些中文文本用于测试。"),
        ("test_document2.txt", "This is the second test document.\nIt contains English text for testing."),
        ("test_document3.txt", "第三个测试文档\n用于验证批量上传功能"),
        ("readme.txt", "README文件\n项目说明文档"),
        ("notes.txt", "笔记文件\n包含重要信息")
    ]
    
    for filename, content in files_to_create:
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        test_files.append(file_path)
    
    print(f"✓ 创建了 {len(test_files)} 个测试文件")
    return test_files

def batch_upload_documents(token, project_id, file_paths):
    """批量上传文档"""
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 准备文件数据
    files = []
    for file_path in file_paths:
        files.append(('files', (file_path.name, open(file_path, 'rb'), 'text/plain')))
    
    # 准备表单数据
    data = {
        'document_category': '测试文档',
        'document_type': '文本文件',
        'summary': '批量上传测试文档'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents/batch-upload/{project_id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # 关闭文件
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 批量上传成功")
            print(f"  - 总文件数: {result['data']['total_files']}")
            print(f"  - 成功上传: {result['data']['successful_uploads']}")
            print(f"  - 失败上传: {result['data']['failed_uploads_count']}")
            
            if result['data']['failed_uploads']:
                print("  失败的文件:")
                for failed in result['data']['failed_uploads']:
                    print(f"    - {failed['filename']}: {failed['error']}")
            
            return result['data']['uploaded_documents']
        else:
            print(f"✗ 批量上传失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 批量上传异常: {str(e)}")
        return None

def test_file_limit(token, project_id):
    """测试文件数量限制"""
    print("\n=== 测试文件数量限制 ===")
    
    # 创建超过限制数量的文件
    temp_dir = tempfile.mkdtemp()
    test_files = []
    
    for i in range(12):  # 创建12个文件，超过10个的限制
        file_path = Path(temp_dir) / f"test_file_{i+1}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"测试文件 {i+1} 的内容")
        test_files.append(file_path)
    
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = []
    for file_path in test_files:
        files.append(('files', (file_path.name, open(file_path, 'rb'), 'text/plain')))
    
    data = {
        'document_category': '测试文档',
        'document_type': '文本文件',
        'summary': '文件数量限制测试'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents/batch-upload/{project_id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # 关闭文件
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 400:
            print("✓ 文件数量限制验证成功")
            print(f"  错误信息: {response.json().get('detail', 'Unknown error')}")
        else:
            print(f"✗ 文件数量限制验证失败: {response.text}")
            
    except Exception as e:
        print(f"✗ 文件数量限制测试异常: {str(e)}")
    
    # 清理文件
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink()

def test_unsupported_file_type(token, project_id):
    """测试不支持的文件类型"""
    print("\n=== 测试不支持的文件类型 ===")
    
    # 创建不支持的文件类型
    temp_dir = tempfile.mkdtemp()
    unsupported_file = Path(temp_dir) / "test.xyz"
    
    with open(unsupported_file, 'w', encoding='utf-8') as f:
        f.write("不支持的文件类型测试")
    
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = [('files', (unsupported_file.name, open(unsupported_file, 'rb'), 'application/octet-stream'))]
    
    data = {
        'document_category': '测试文档',
        'document_type': '不支持类型',
        'summary': '文件类型测试'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/documents/batch-upload/{project_id}",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # 关闭文件
        files[0][1][1].close()
        
        if response.status_code == 400:
            print("✓ 不支持文件类型验证成功")
            print(f"  错误信息: {response.json().get('detail', 'Unknown error')}")
        else:
            print(f"✗ 不支持文件类型验证失败: {response.text}")
            
    except Exception as e:
        print(f"✗ 不支持文件类型测试异常: {str(e)}")
    
    # 清理文件
    if unsupported_file.exists():
        unsupported_file.unlink()

def get_project_documents(token, project_id):
    """获取项目文档列表"""
    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/documents/project/{project_id}", headers=auth_headers)
    if response.status_code == 200:
        result = response.json()
        documents = result["data"]["documents"]
        print(f"✓ 获取到 {len(documents)} 个文档")
        return documents
    else:
        print(f"✗ 获取文档列表失败: {response.text}")
        return []

def cleanup_test_files(file_paths):
    """清理测试文件"""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
            # 删除临时目录
            temp_dir = file_path.parent
            if temp_dir.exists() and not list(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception as e:
            print(f"清理文件失败: {e}")

def main():
    """主测试函数"""
    print("=== 批量文档上传功能测试 ===")
    
    # 1. 创建测试用户
    print("\n1. 创建测试用户")
    user_result = create_test_user()
    if not user_result:
        return
    
    # 2. 用户登录
    print("\n2. 用户登录")
    if isinstance(user_result, tuple):
        user_data = user_result[1]
        token = login_user(user_data["username"], user_data["password"])
    else:
        token = login_user("batch_test_user", "testpassword123")
    if not token:
        return
    
    # 3. 创建测试项目
    print("\n3. 创建测试项目")
    project_id = create_test_project(token)
    if not project_id:
        return
    
    # 4. 创建测试文件
    print("\n4. 创建测试文件")
    test_files = create_test_files()
    
    try:
        # 5. 批量上传文档
        print("\n5. 批量上传文档")
        uploaded_docs = batch_upload_documents(token, project_id, test_files)
        
        if uploaded_docs:
            # 6. 验证上传结果
            print("\n6. 验证上传结果")
            documents = get_project_documents(token, project_id)
            
            # 7. 测试文件数量限制
            test_file_limit(token, project_id)
            
            # 8. 测试不支持的文件类型
            test_unsupported_file_type(token, project_id)
            
            print("\n=== 批量上传功能测试完成 ===")
            print("✓ 所有测试项目已完成")
        else:
            print("\n✗ 批量上传失败，跳过后续测试")
    
    finally:
        # 清理测试文件
        cleanup_test_files(test_files)
        print("\n✓ 测试文件已清理")

if __name__ == "__main__":
    main()