"""Main FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import bookmarks, widgets, sections
from app.services.database import init_db, get_db
from app.services.scheduler import scheduler_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Home Sweet Home application...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["bookmarks"])
app.include_router(widgets.router, prefix="/api/widgets", tags=["widgets"])
app.include_router(sections.router)


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
