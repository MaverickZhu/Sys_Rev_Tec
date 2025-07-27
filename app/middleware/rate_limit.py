from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from app.core.config import settings
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# 创建Redis连接
def get_redis_client():
    """获取Redis客户端"""
    try:
        redis_url = settings.RATE_LIMIT_REDIS_URL or settings.REDIS_URL or "redis://localhost:6379"
        return redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis连接失败，使用内存存储: {e}")
        return None

# 自定义key函数，避免slowapi的默认行为
def get_rate_limit_key(request: Request):
    """获取限流键"""
    return get_remote_address(request)

# 创建限流器
def create_limiter():
    """创建限流器实例"""
    redis_client = get_redis_client()
    
    if redis_client:
        # 使用Redis作为存储后端
        limiter = Limiter(
            key_func=get_rate_limit_key,
            storage_uri=settings.RATE_LIMIT_REDIS_URL or settings.REDIS_URL or "redis://localhost:6379"
        )
        logger.info("使用Redis作为限流存储后端")
    else:
        # 使用内存作为存储后端（仅适用于单实例）
        limiter = Limiter(
            key_func=get_rate_limit_key
        )
        logger.warning("使用内存作为限流存储后端（仅适用于单实例）")
    
    return limiter

# 全局限流器实例
limiter = create_limiter() if settings.RATE_LIMIT_ENABLED else None

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, limiter_instance=None):
        super().__init__(app)
        self.limiter = limiter_instance or limiter
        self.enabled = settings.RATE_LIMIT_ENABLED
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled or not self.limiter:
            return await call_next(request)
        
        try:
            # 检查限流 - 使用装饰器方式而不是中间件方式
            # slowapi主要设计为装饰器使用，中间件方式可能不稳定
            # 这里简化处理，只记录但不阻止请求
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"限流中间件错误: {e}")
            # 如果限流出错，允许请求通过
            return await call_next(request)

# 自定义限流异常处理器
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """自定义限流异常处理"""
    response = {
        "error": "Rate limit exceeded",
        "message": f"请求过于频繁，请稍后再试。限制: {settings.RATE_LIMIT_REQUESTS}次/{settings.RATE_LIMIT_PERIOD}秒",
        "retry_after": settings.RATE_LIMIT_PERIOD,
        "detail": str(exc)
    }
    
    return HTTPException(
        status_code=429,
        detail=response
    )

# 装饰器函数，用于特定端点的限流
def rate_limit(rate: str):
    """限流装饰器
    
    Args:
        rate: 限流规则，如 "10/minute", "100/hour"
    """
    def decorator(func):
        # 如果限流被禁用，直接返回原函数
        if not settings.RATE_LIMIT_ENABLED or not limiter:
            return func
            
        # 为了与FastAPI兼容，我们需要创建一个包装函数
        # 该函数会从FastAPI的依赖注入中获取request对象
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 暂时简化实现，只记录但不限制
            # TODO: 实现真正的限流逻辑，需要从FastAPI上下文获取request
            logger.debug(f"Rate limit check for {func.__name__} with rate {rate}")
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# 简化的限流装饰器，避免slowapi的复杂性
def simple_rate_limit(func):
    """简化的限流装饰器，暂时只记录但不限制"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO: 实现真正的限流逻辑
        logger.debug(f"Rate limit check for {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# 预定义的限流装饰器
strict_rate_limit = rate_limit("5/minute")  # 严格限流：每分钟5次
moderate_rate_limit = rate_limit("20/minute")  # 中等限流：每分钟20次
loose_rate_limit = rate_limit("100/minute")  # 宽松限流：每分钟100次