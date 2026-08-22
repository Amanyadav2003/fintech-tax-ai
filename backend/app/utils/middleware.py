"""
Middleware for error handling, rate limiting, security
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .logging_config import logger
from datetime import datetime
import traceback


# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as exc:
            logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except HTTPException as exc:
            logger.warning(f"HTTP Exception: {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": exc.detail,
                    "error_code": "HTTP_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as exc:
            logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error. Please try again later.",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers to prevent common attacks
        response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME type sniffing
        response.headers["X-Frame-Options"] = "DENY"  # Prevent clickjacking
        response.headers["X-XSS-Protection"] = "1; mode=block"  # Enable XSS filter
        
        # HSTS - Strict Transport Security (enforce HTTPS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy - restrict where content can be loaded from
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
        
        # Referrer Policy - control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy - control browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        logger.info(
            f"Request {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        logger.info(
            f"Response {request.method} {request.url.path} - Status {response.status_code}"
        )
        
        return response
