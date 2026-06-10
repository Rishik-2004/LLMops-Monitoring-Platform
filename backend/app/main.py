"""
LLMOps Monitoring Platform - Main FastAPI Application
Enterprise-grade LLM observability and monitoring platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import structlog
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.redis_client import redis_client
from app.api.v1.router import api_router
from app.core.logging_config import setup_logging
from app.monitoring.telemetry import setup_telemetry
from app.core.security import get_password_hash
from app.db.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

setup_logging()
logger = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting LLMOps Monitoring Platform", version=settings.APP_VERSION)
    
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")

    # Seed default admin user
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.email == "admin@llmops.dev"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@llmops.dev",
                username="admin",
                full_name="Platform Admin",
                hashed_password=get_password_hash("Admin@1234"),
                role=UserRole.SUPERADMIN,
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created", email="admin@llmops.dev")
        else:
            logger.info("Admin user already exists")
    
    # Initialize Redis
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning("Redis connection failed at startup - continuing without Redis", error=str(e))
    
    # Setup telemetry
    setup_telemetry()
    logger.info("OpenTelemetry initialized")
    
    yield
    
    # Cleanup
    await engine.dispose()
    await redis_client.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="LLMOps Monitoring Platform",
    description="""
    ## Enterprise-Grade LLM Observability & Monitoring Platform
    
    Monitor, evaluate, and optimize your AI applications with production-grade observability.
    
    ### Features
    - 🔍 **Real-time Monitoring** - Track LLM requests, responses, tokens, costs, and latency
    - 🤖 **AI Copilot** - Agentic assistant powered by LangGraph for operational insights
    - 📊 **Analytics Dashboard** - Comprehensive metrics and trend analysis
    - 🛡️ **Security Layer** - Prompt injection detection, toxicity filtering
    - ⚡ **Evaluation Engine** - RAGAS + DeepEval quality metrics
    - 🔔 **Alert System** - Configurable alerts for cost, latency, errors
    - 📚 **RAG Knowledge Base** - Semantic search over monitoring documentation
    """,
    version=settings.APP_VERSION,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - allow all origins (JWT auth uses headers, not cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", f"req_{int(start_time * 1000)}")
    
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        request_id=request_id,
    )
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    response.headers["X-Request-ID"] = request_id
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(process_time, 2),
        request_id=request_id,
    )
    
    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
async def root():
    return {
        "name": "LLMOps Monitoring Platform",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    health = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {}
    }
    
    # Check database
    try:
        async with engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # Check Redis
    try:
        await redis_client.ping()
        health["services"]["redis"] = "healthy"
    except Exception as e:
        health["services"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    return health


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
