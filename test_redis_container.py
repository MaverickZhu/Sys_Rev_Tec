#!/usr/bin/env python3
import redis.asyncio as redis
import asyncio
import os

async def test_redis():
    try:
        redis_url = os.getenv('REDIS_URL')
        print(f"Testing Redis connection with URL: {redis_url}")
        
        r = redis.Redis.from_url(redis_url)
        await r.ping()
        print("Redis connection successful!")
        await r.close()
        
    except Exception as e:
        print(f"Redis connection failed: {e}")
        
        # 尝试直接连接
        try:
            print("Trying direct connection to redis:6379...")
            r2 = redis.Redis(host='redis', port=6379, password='redis_password', db=0)
            await r2.ping()
            print("Direct Redis connection successful!")
            await r2.close()
        except Exception as e2:
            print(f"Direct Redis connection also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_redis())