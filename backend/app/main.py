from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from .routes.tax_routes import router as tax_router
from .routes.auth_routes import router as auth_router
from .routes.chat_history_routes import router as chat_history_router
from .utils.database import init_db
from .utils.middleware import ErrorHandlingMiddleware, SecurityHeadersMiddleware, LoggingMiddleware, limiter
from .utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

# Initialize Sentry for error tracking (optional, disable if no Sentry account)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production")
    )

# Initialize FastAPI app
app = FastAPI(
    title="TaxMate AI - Production Ready",
    description="AI-powered tax filing and financial planning for India",
    version=os.getenv("APP_VERSION", "1.0.0"),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add rate limiter state
app.state.limiter = limiter

# CORS middleware - allow local frontend dev origins and merge with env overrides
default_local_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
for origin in default_local_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],  # FIXED: Specific headers only
    max_age=600,  # Preflight cache 10 minutes
)

# Trusted hosts middleware - Prevent host header injection attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# Custom middlewares (order matters)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

# Session cookie security configuration
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_HTTPONLY = os.getenv("SESSION_COOKIE_HTTPONLY", "true").lower() == "true"
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

if os.getenv("ENVIRONMENT") == "production":
    SESSION_COOKIE_SECURE = True  # Enforce HTTPS in production
    SESSION_COOKIE_SAMESITE = "Strict"  # Prevent CSRF attacks
    
logger.info(f"Session Cookie Security: Secure={SESSION_COOKIE_SECURE}, HttpOnly={SESSION_COOKIE_HTTPONLY}, SameSite={SESSION_COOKIE_SAMESITE}")

# Initialize database
@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Database initialized, application startup complete")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Application shutting down")

# Include routers
app.include_router(auth_router)
app.include_router(tax_router)
app.include_router(chat_history_router)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

# Root endpoint
@app.get("/", tags=["info"])
async def root():
    return {
        "message": "TaxMate AI - Tax Filing & Financial Planning Engine",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "docs_url": "/api/docs",
        "health_url": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    host = os.getenv("API_HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
