#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务启动脚本
用于快速启动和测试AI服务
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_service.config import get_settings
from ai_service.utils.logging import setup_logging


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    settings = get_settings()
    
    # 检查必需的环境变量
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'OLLAMA_BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请检查 .env 文件或环境变量配置")
        return False
    
    print("✅ 环境配置检查通过")
    return True


async def check_dependencies():
    """检查依赖服务"""
    print("🔍 检查依赖服务...")
    
    settings = get_settings()
    
    # 检查数据库连接
    try:
        from ai_service.database import get_vector_db
        db = await get_vector_db()
        await db.health_check()
        await db.close()
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    # 检查Redis连接
    try:
        from ai_service.utils.cache import get_cache_manager
        cache = await get_cache_manager()
        await cache.set("test_key", "test_value", ttl=10)
        value = await cache.get("test_key")
        if value != "test_value":
            raise Exception("Redis读写测试失败")
        await cache.delete("test_key")
        print("✅ Redis连接正常")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False
    
    # 检查Ollama服务
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                print("✅ Ollama服务正常")
            else:
                print(f"⚠️ Ollama服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ollama服务检查失败: {e}")
        print("注意: Ollama服务可选，但建议启动以获得完整功能")
    
    return True


def install_dependencies():
    """安装依赖包"""
    print("📦 检查并安装依赖包...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt 文件不存在")
        return False
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖包安装完成")
            return True
        else:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 依赖包安装异常: {e}")
        return False


def start_ai_service():
    """启动AI服务"""
    print("🚀 启动AI服务...")
    
    try:
        import uvicorn
        from ai_service.main import app
        
        settings = get_settings()
        
        # 启动配置
        config = {
            "app": "ai_service.main:app",
            "host": settings.AI_SERVICE_HOST,
            "port": settings.AI_SERVICE_PORT,
            "reload": settings.DEBUG,
            "log_level": "debug" if settings.DEBUG else "info",
            "access_log": True,
            "use_colors": True
        }
        
        print(f"🌐 服务地址: http://{settings.AI_SERVICE_HOST}:{settings.AI_SERVICE_PORT}")
        print(f"📚 API文档: http://{settings.AI_SERVICE_HOST}:{settings.AI_SERVICE_PORT}/docs")
        print(f"📊 健康检查: http://{settings.AI_SERVICE_HOST}:{settings.AI_SERVICE_PORT}/health")
        print(f"📈 指标监控: http://{settings.AI_SERVICE_HOST}:{settings.AI_SERVICE_PORT}/metrics")
        
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)


async def main():
    """主函数"""
    print("🎯 AI服务启动器")
    print("=" * 50)
    
    # 设置日志
    setup_logging()
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 安装依赖（可选）
    install_deps = input("是否检查并安装依赖包? (y/N): ").lower().strip()
    if install_deps in ['y', 'yes']:
        if not install_dependencies():
            sys.exit(1)
    
    # 检查依赖服务
    if not await check_dependencies():
        print("\n⚠️ 部分依赖服务检查失败，但仍可以启动服务")
        continue_start = input("是否继续启动服务? (y/N): ").lower().strip()
        if continue_start not in ['y', 'yes']:
            sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # 启动服务
    start_ai_service()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见!")
    except Exception as e:
        print(f"❌ 启动器异常: {e}")
        sys.exit(1)