"""Main FastAPI application entry point."""
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import bookmarks, widgets, sections, preferences
from app.services.database import init_db, get_db
from app.services.scheduler import scheduler_service
from app.services.rate_limit import limiter
from app.exceptions import AppException

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Validate critical configuration on startup
if not settings.SECRET_KEY or settings.SECRET_KEY == "change-this-in-production":
    raise ValueError(
        "SECRET_KEY must be set to a secure random value. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """
        Log request details and response status.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            }
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log errors
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                }
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
            }
        )

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""

    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        """
        Initialize request size limit middleware.

        Args:
            app: FastAPI application
            max_size: Maximum request body size in bytes
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        """
        Check request size before processing.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response or 413 error if too large
        """
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large",
                    "max_size": self.max_size,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Home Sweet Home application...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Run migrations
    try:
        from app.services.database import engine
        from app.migrations.add_clicks_to_bookmarks import run_migration as run_clicks_migration
        from app.migrations.create_preferences_table import run_migration as run_preferences_migration
        await run_clicks_migration(engine)
        await run_preferences_migration(engine)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Continue startup even if migration fails
        # This prevents breaking the application if migration has issues

    # Initialize default sections
    async for db in get_db():
        try:
            from app.api.sections import initialize_default_sections
            await initialize_default_sections(db)
            logger.info("Default sections initialized")
        finally:
            await db.close()
        break

    # Start scheduler if enabled
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.start()
        logger.info("Scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if settings.SCHEDULER_ENABLED:
        await scheduler_service.shutdown()
        logger.info("Scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Self-hosted customizable browser homepage with widgets",
    lifespan=lifespan
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global exception handler for custom exceptions
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Global handler for custom application exceptions.

    Args:
        request: HTTP request that caused the exception
        exc: Application exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error": exc.message,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)  # 1MB limit

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Be specific about allowed methods
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(widgets.router, prefix="/api/widgets", tags=["widgets"])
app.include_router(sections.router)
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
