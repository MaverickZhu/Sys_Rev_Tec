import os
import redis.asyncio as redis
import asyncio

async def test_redis():
    print('REDIS_URL from env:', os.getenv('REDIS_URL'))
    url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    print('Using URL:', url)
    
    try:
        client = redis.Redis.from_url(url)
        await client.ping()
        print('Redis connection successful')
        await client.close()
    except Exception as e:
        print('Redis connection failed:', e)

if __name__ == '__main__':
    asyncio.run(test_redis())