"""权限中间件

实现API请求的权限验证和审计日志记录
"""

import time
import json
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.security_service import SecurityService
from app.core.security.threat_detector import ThreatDetector


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限验证中间件"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/health",
            "/favicon.ico"
        ]
        self.security_service = SecurityService()
        self.threat_detector = ThreatDetector()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 检查是否需要跳过权限验证
        if self._should_skip_auth(request.url.path):
            response = await call_next(request)
            return response
        
        # 获取数据库会话
        db = SessionLocal()
        try:
            # 验证用户身份
            user = await self._authenticate_user(request, db)
            if not user:
                return self._create_unauthorized_response()
            
            # 检查用户状态
            if not user.is_active:
                return self._create_forbidden_response("用户账户已被禁用")
            
            # 威胁检测
            threat_result = await self._check_threats(request, user, client_ip, db)
            if threat_result:
                return threat_result
            
            # 将用户信息添加到请求状态
            request.state.current_user = user
            request.state.db = db
            
            # 处理请求
            response = await call_next(request)
            
            # 记录审计日志
            await self._log_request(request, response, user, start_time, db)
            
            return response
            
        except HTTPException as e:
            # 记录失败的请求
            await self._log_failed_request(request, e, start_time, client_ip, db)
            raise
        except Exception as e:
            # 记录系统错误
            await self._log_system_error(request, e, start_time, client_ip, db)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="内部服务器错误"
            )
        finally:
            db.close()
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _should_skip_auth(self, path: str) -> bool:
        """检查是否应该跳过认证"""
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)
    
    async def _authenticate_user(self, request: Request, db: Session) -> Optional[User]:
        """验证用户身份"""
        try:
            # 获取Authorization头
            authorization = request.headers.get("authorization")
            if not authorization:
                return None
            
            # 解析Bearer token
            if not authorization.startswith("Bearer "):
                return None
            
            token = authorization[7:]  # 移除"Bearer "前缀
            
            # 验证token
            payload = verify_token(token)
            if not payload:
                return None
            
            # 获取用户
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
            
        except Exception:
            return None
    
    async def _check_threats(self, request: Request, user: User, client_ip: str, db: Session) -> Optional[Response]:
        """检查威胁"""
        try:
            # 检查IP黑名单
            if self.threat_detector.is_ip_blacklisted(client_ip):
                await self.security_service.create_security_event(
                    db,
                    event_type="BLACKLISTED_IP_ACCESS",
                    level="HIGH",
                    description=f"黑名单IP访问: {client_ip}",
                    source_ip=client_ip,
                    user_id=user.id,
                    request_path=str(request.url.path),
                    request_method=request.method
                )
                return self._create_forbidden_response("访问被拒绝")
            
            # 检查暴力破解
            if await self._check_brute_force(client_ip, user.id, db):
                return self._create_forbidden_response("请求过于频繁，请稍后再试")
            
            # 检查异常访问模式
            await self._check_anomaly_patterns(request, user, client_ip, db)
            
            return None
            
        except Exception as e:
            # 威胁检测失败不应该阻止正常请求
            print(f"威胁检测错误: {e}")
            return None
    
    async def _check_brute_force(self, client_ip: str, user_id: int, db: Session) -> bool:
        """检查暴力破解攻击"""
        # 检查最近5分钟内的失败请求数量
        recent_failures = db.query(AuditLog).filter(
            AuditLog.source_ip == client_ip,
            AuditLog.user_id == user_id,
            AuditLog.status_code >= 400,
            AuditLog.created_at >= time.time() - 300  # 5分钟
        ).count()
        
        if recent_failures > 10:  # 5分钟内超过10次失败
            await self.security_service.create_security_event(
                db,
                event_type="BRUTE_FORCE_ATTACK",
                level="HIGH",
                description=f"检测到暴力破解攻击: IP {client_ip}, 用户 {user_id}",
                source_ip=client_ip,
                user_id=user_id
            )
            return True
        
        return False
    
    async def _check_anomaly_patterns(self, request: Request, user: User, client_ip: str, db: Session):
        """检查异常访问模式"""
        try:
            # 检查夜间访问（22:00-06:00）
            current_hour = time.localtime().tm_hour
            if current_hour >= 22 or current_hour <= 6:
                await self.security_service.create_security_event(
                    db,
                    event_type="NIGHT_ACCESS",
                    level="MEDIUM",
                    description=f"夜间访问: 用户 {user.username} 在 {current_hour}:00 访问系统",
                    source_ip=client_ip,
                    user_id=user.id,
                    request_path=str(request.url.path),
                    request_method=request.method
                )
            
            # 检查敏感操作
            sensitive_paths = ["/api/v1/users/", "/api/v1/permissions/", "/api/v1/roles/"]
            if any(str(request.url.path).startswith(path) for path in sensitive_paths):
                if request.method in ["POST", "PUT", "DELETE"]:
                    await self.security_service.create_security_event(
                        db,
                        event_type="SENSITIVE_OPERATION",
                        level="MEDIUM",
                        description=f"敏感操作: {request.method} {request.url.path}",
                        source_ip=client_ip,
                        user_id=user.id,
                        request_path=str(request.url.path),
                        request_method=request.method
                    )
            
        except Exception as e:
            print(f"异常模式检查错误: {e}")
    
    async def _log_request(self, request: Request, response: Response, user: User, start_time: float, db: Session):
        """记录请求审计日志"""
        try:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 获取请求体（如果是POST/PUT请求）
            request_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    # 注意：这里可能需要根据实际情况调整
                    # 因为request body可能已经被消费了
                    pass
                except Exception:
                    pass
            
            # 创建审计日志
            audit_log = AuditLog(
                user_id=user.id,
                username=user.username,
                action=f"{request.method} {request.url.path}",
                resource_type="API",
                resource_id=None,
                request_method=request.method,
                request_path=str(request.url.path),
                request_query=str(request.url.query) if request.url.query else None,
                request_body=request_body,
                response_status=response.status_code,
                status_code=response.status_code,
                source_ip=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                process_time=process_time,
                created_at=time.time()
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            print(f"记录审计日志失败: {e}")
            db.rollback()
    
    async def _log_failed_request(self, request: Request, error: HTTPException, start_time: float, client_ip: str, db: Session):
        """记录失败的请求"""
        try:
            process_time = time.time() - start_time
            
            audit_log = AuditLog(
                user_id=None,
                username="anonymous",
                action=f"{request.method} {request.url.path}",
                resource_type="API",
                resource_id=None,
                request_method=request.method,
                request_path=str(request.url.path),
                request_query=str(request.url.query) if request.url.query else None,
                response_status=error.status_code,
                status_code=error.status_code,
                error_message=str(error.detail),
                source_ip=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                process_time=process_time,
                created_at=time.time()
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            print(f"记录失败请求日志失败: {e}")
            db.rollback()
    
    async def _log_system_error(self, request: Request, error: Exception, start_time: float, client_ip: str, db: Session):
        """记录系统错误"""
        try:
            process_time = time.time() - start_time
            
            audit_log = AuditLog(
                user_id=None,
                username="system",
                action=f"{request.method} {request.url.path}",
                resource_type="API",
                resource_id=None,
                request_method=request.method,
                request_path=str(request.url.path),
                request_query=str(request.url.query) if request.url.query else None,
                response_status=500,
                status_code=500,
                error_message=str(error),
                source_ip=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                process_time=process_time,
                created_at=time.time()
            )
            
            db.add(audit_log)
            db.commit()
            
            # 创建安全事件
            await self.security_service.create_security_event(
                db,
                event_type="SYSTEM_ERROR",
                level="HIGH",
                description=f"系统错误: {str(error)}",
                source_ip=client_ip,
                request_path=str(request.url.path),
                request_method=request.method
            )
            
        except Exception as e:
            print(f"记录系统错误日志失败: {e}")
            db.rollback()
    
    def _create_unauthorized_response(self) -> Response:
        """创建未授权响应"""
        return Response(
            content=json.dumps({"detail": "未授权访问"}),
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"content-type": "application/json"}
        )
    
    def _create_forbidden_response(self, message: str = "访问被禁止") -> Response:
        """创建禁止访问响应"""
        return Response(
            content=json.dumps({"detail": message}),
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"content-type": "application/json"}
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """请求频率限制中间件"""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # {ip: [(timestamp, count), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # 清理过期的记录
        self._cleanup_expired_records(current_time)
        
        # 检查请求频率
        if self._is_rate_limited(client_ip, current_time):
            return Response(
                content=json.dumps({"detail": "请求过于频繁，请稍后再试"}),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"content-type": "application/json"}
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        # 处理请求
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期的记录"""
        cutoff_time = current_time - self.window_seconds
        
        for ip in list(self.request_counts.keys()):
            # 过滤掉过期的记录
            self.request_counts[ip] = [
                (timestamp, count) for timestamp, count in self.request_counts[ip]
                if timestamp > cutoff_time
            ]
            
            # 如果没有记录了，删除这个IP
            if not self.request_counts[ip]:
                del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超过频率限制"""
        if client_ip not in self.request_counts:
            return False
        
        # 计算当前窗口内的请求总数
        total_requests = sum(count for _, count in self.request_counts[client_ip])
        return total_requests >= self.max_requests
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append((current_time, 1))