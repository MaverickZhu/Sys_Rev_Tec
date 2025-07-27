from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Only add security headers in production or when explicitly enabled
        if settings.is_production or getattr(settings, 'ENABLE_SECURITY_HEADERS', False):
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # XSS protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Content Security Policy (CSP)
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp_policy
            
            # Strict Transport Security (HSTS) - only for HTTPS
            if getattr(settings, 'FORCE_HTTPS', False):
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Permissions policy
            response.headers["Permissions-Policy"] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )
        
        # Add custom server header (use English name for HTTP headers)
        app_name_en = "Gov-Procurement-System"  # English version for HTTP headers
        response.headers["Server"] = f"{app_name_en}/{settings.VERSION}"
        
        return response

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """HTTPS redirect middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Only redirect in production when HTTPS is forced
        if (settings.is_production and 
            getattr(settings, 'FORCE_HTTPS', False) and 
            request.url.scheme == "http"):
            
            # Build HTTPS URL
            https_url = request.url.replace(scheme="https")
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=str(https_url), status_code=301)
        
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        import time
        
        start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response