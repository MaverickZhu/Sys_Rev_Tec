import requests
import json

# 测试创建用户
print("=== 测试创建用户 ===")
user_data = {"username": "testuser", "password": "testpassword123"}
response = requests.post("http://localhost:8000/api/v1/users/", json=user_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
if response.status_code == 200:
    print("用户创建成功")

# 测试重复用户名
print("\n=== 测试重复用户名 ===")
response2 = requests.post("http://localhost:8000/api/v1/users/", json=user_data)
print(f"Status: {response2.status_code}")
print(f"Response: {response2.text}")
try:
    data = response2.json()
    print(f"JSON: {data}")
except:
    print("无法解析JSON")

# 测试登录
print("\n=== 测试登录 ===")
login_data = {"username": "testuser", "password": "testpassword123"}
response3 = requests.post("http://localhost:8000/api/v1/login/access-token", data=login_data)
print(f"Status: {response3.status_code}")
print(f"Response: {response3.text}")
try:
    data = response3.json()
    print(f"JSON: {data}")
except:
    print("无法解析JSON")