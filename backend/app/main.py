"""FastAPI Application Factory & Entry Point for AI Resume Builder Platform."""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.v1.router import api_v1_router
from .config import settings
from .core.middleware import SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resume_builder.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} [{settings.environment}]")
    logger.info(f"Storage directory: {settings.storage_path}")
    logger.info(f"CORS origins configured: {settings.cors_origins}")
    if settings.is_production:
        logger.info("Production mode active: Interactive Swagger docs disabled, HSTS active, Cloudflare Access JWT validation enforced.")
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance with security hardening."""
    # In production, disable interactive docs to prevent attacker reconnaissance
    docs_url = "/docs" if not settings.is_production else None
    redoc_url = "/redoc" if not settings.is_production else None
    openapi_url = "/openapi.json" if not settings.is_production else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="High-performance backend API for the AI Resume Builder Platform.",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # 1. Security Headers Middleware (OWASP recommended security headers)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Configure CORS with strict method and header definitions
    cors_methods = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"] if settings.is_production else ["*"]
    cors_headers = [
        "Content-Type",
        "Authorization",
        "Cf-Access-Jwt-Assertion",
        "Cf-Access-Authenticated-User-Email",
        "X-Requested-With",
        "Accept",
    ] if settings.is_production else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=cors_methods,
        allow_headers=cors_headers,
    )

    # 3. Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    # 4. Global exception handler to prevent leaking database tracebacks or internal credentials
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. System administrators have been notified."},
        )

    # 5. Root landing endpoint
    @app.get("/", tags=["Root"])
    def root_endpoint():
        info = {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "health": f"{settings.api_v1_prefix}/health",
            "ready": f"{settings.api_v1_prefix}/health/ready",
            "providers": f"{settings.api_v1_prefix}/system/providers",
        }
        if not settings.is_production:
            info["docs"] = "/docs"
        return info

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
