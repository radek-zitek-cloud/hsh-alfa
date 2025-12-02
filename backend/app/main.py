"""Main FastAPI application entry point."""

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import admin, auth, bookmarks, export_import, habits, preferences, sections, widgets
from app.config import settings
from app.exceptions import AppException
from app.logging_config import get_logger, setup_logging
from app.services.database import get_db, init_db
from app.services.rate_limit import limiter
from app.services.scheduler import scheduler_service

# Configure structured logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    uvicorn_access_log_level=settings.UVICORN_ACCESS_LOG_LEVEL,
    uvicorn_error_log_level=settings.UVICORN_ERROR_LOG_LEVEL,
    sqlalchemy_engine_log_level=settings.SQLALCHEMY_ENGINE_LOG_LEVEL,
    apscheduler_log_level=settings.APSCHEDULER_LOG_LEVEL,
)
logger = get_logger(__name__)

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
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log errors
            duration = time.time() - start_time
            logger.error(
                "Request failed with exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration": duration,
                },
                exc_info=True,
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response - treat 4xx client errors as info unless they indicate potential issues
        # 404 Not Found is expected for missing resources and should not be a warning
        # 400 Bad Request is expected for validation failures and should not be a warning
        # 422 Unprocessable Entity is expected for validation errors and should not be a warning
        if response.status_code < 400:
            log_level = "info"
        elif response.status_code in (400, 404, 422):
            # Expected client errors (bad request, not found, validation errors)
            log_level = "info"
        elif response.status_code < 500:
            log_level = "warning"
        else:
            log_level = "error"
        getattr(logger, log_level)(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": round(duration, 3),
                "response_time_ms": round(duration * 1000, 2),
            },
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
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            logger = get_logger(__name__)
            logger.warning(
                "Request body size limit exceeded",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "content_length": int(content_length),
                    "max_size": self.max_size,
                    "client_host": request.client.host if request.client else "unknown",
                },
            )
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large",
                    "max_size": self.max_size,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response with security headers added
        """
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by disallowing iframe embedding from other origins
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Content Security Policy - restrict resource loading
        # Allow same origin and inline styles (needed for some UI frameworks)
        csp_directives = [
            "default-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "script-src 'self'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'self'",
            "form-action 'self'",
            "base-uri 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # XSS Protection (legacy, but still supported by some browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy - control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy - restrict browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting application",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
        },
    )

    # Initialize database
    try:
        await init_db()
        logger.info(
            "Database initialized",
            extra={"database_url": settings.DATABASE_URL.split("://")[0] + "://***"},
        )
    except Exception as e:
        logger.critical("Failed to initialize database", extra={"error": str(e)}, exc_info=True)
        raise

    # Run migrations
    try:
        from app.migrations.add_clicks_to_bookmarks import run_migration as run_clicks_migration
        from app.migrations.add_performance_indexes import run_migration as run_indexes_migration
        from app.migrations.add_role_to_users import run_migration as run_role_migration
        from app.migrations.add_user_id_to_tables import run_migration as run_user_id_migration
        from app.migrations.create_habits_tables import run_migration as run_habits_migration
        from app.migrations.create_preferences_table import (
            run_migration as run_preferences_migration,
        )
        from app.migrations.create_users_table import run_migration as run_users_migration
        from app.services.database import engine

        logger.debug("Running database migrations")
        await run_clicks_migration(engine)
        await run_preferences_migration(engine)
        await run_users_migration(engine)
        await run_user_id_migration(engine)
        await run_role_migration(engine)
        await run_habits_migration(engine)
        await run_indexes_migration(engine)
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(
            "Migration failed",
            extra={"error_type": type(e).__name__, "error": str(e)},
            exc_info=True,
        )
        # Continue startup even if migration fails
        # This prevents breaking the application if migration has issues

    # Initialize default sections
    async for db in get_db():
        try:
            from app.api.sections import initialize_default_sections

            await initialize_default_sections(db)
            logger.info("Default sections initialized")
        except Exception as e:
            logger.error(
                "Failed to initialize default sections", extra={"error": str(e)}, exc_info=True
            )
        finally:
            await db.close()
        break

    # Register widget classes (required for widget type validation and data fetching)
    try:
        from app.widgets import register_all_widgets

        register_all_widgets()
        logger.info("Widget classes registered successfully")
    except Exception as e:
        logger.error("Failed to register widget classes", extra={"error": str(e)}, exc_info=True)

    # Start scheduler if enabled
    if settings.SCHEDULER_ENABLED:
        try:
            await scheduler_service.start()
            logger.info(
                "Scheduler started", extra={"scheduler_enabled": settings.SCHEDULER_ENABLED}
            )
        except Exception as e:
            logger.error("Failed to start scheduler", extra={"error": str(e)}, exc_info=True)

    logger.info("Application startup completed successfully")

    yield

    # Shutdown
    logger.info("Initiating application shutdown")

    if settings.SCHEDULER_ENABLED:
        try:
            await scheduler_service.shutdown()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error("Error stopping scheduler", extra={"error": str(e)}, exc_info=True)

    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Self-hosted customizable browser homepage with widgets",
    lifespan=lifespan,
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
    log_level = "warning" if exc.status_code < 500 else "error"
    getattr(logger, log_level)(
        "Application exception occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_message": exc.message,
            "exception_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size=1024 * 1024)  # 1MB limit
app.add_middleware(SecurityHeadersMiddleware)

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
app.include_router(auth.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(widgets.router, prefix="/api/widgets", tags=["widgets"])
app.include_router(habits.router, prefix="/api", tags=["habits"])
app.include_router(sections.router)
app.include_router(preferences.router, prefix="/api/preferences", tags=["preferences"])
app.include_router(export_import.router, prefix="/api", tags=["export-import"])
app.include_router(admin.router, prefix="/api", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
