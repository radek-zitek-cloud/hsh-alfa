"""Database connection and initialization."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

# Create session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created", extra={"operation": "session_creation"})
            yield session
            await session.commit()
            logger.debug("Database session committed", extra={"operation": "session_commit"})
        except Exception as e:
            # Log expected HTTP exceptions at debug level
            error_type = type(e).__name__
            if error_type in ("HTTPException", "RequestValidationError"):
                logger.debug(
                    "Database transaction rolled back due to expected error",
                    extra={"operation": "session_rollback", "error_type": error_type},
                )
            else:
                logger.warning(
                    "Database transaction rolled back due to error",
                    extra={"operation": "session_rollback", "error_type": error_type},
                )
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("Database session closed", extra={"operation": "session_close"})


async def init_db():
    """Initialize database tables."""
    logger.info(
        "Initializing database",
        extra={
            "operation": "database_init",
            "database_url": (
                settings.DATABASE_URL.replace(
                    settings.DATABASE_URL.split("@")[0].split("://")[1], "***"
                )
                if "@" in settings.DATABASE_URL
                else "***"
            ),
        },
    )
    try:
        async with engine.begin() as conn:
            # Import models to register them
            from app.models import bookmark  # noqa: F401
            from app.models import section  # noqa: F401
            from app.models import widget  # noqa: F401

            await conn.run_sync(Base.metadata.create_all)
        logger.info(
            "Database initialization completed successfully",
            extra={
                "operation": "database_init_complete",
                "tables": ["bookmark", "section", "widget"],
            },
        )
    except Exception as e:
        logger.error(
            "Database initialization failed",
            extra={"operation": "database_init_failed", "error_type": type(e).__name__},
            exc_info=True,
        )
        raise
