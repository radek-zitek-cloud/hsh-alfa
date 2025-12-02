"""Tests for logging configuration module."""

import logging
import os
from unittest.mock import patch

from app.logging_config import setup_logging


class TestSetupLoggingThirdPartyLogLevels:
    """Tests for configurable third-party library log levels."""

    def test_default_uvicorn_access_log_level(self):
        """Test default uvicorn.access log level is WARNING."""
        setup_logging()
        assert logging.getLogger("uvicorn.access").level == logging.WARNING

    def test_default_uvicorn_error_log_level(self):
        """Test default uvicorn.error log level is INFO."""
        setup_logging()
        assert logging.getLogger("uvicorn.error").level == logging.INFO

    def test_default_sqlalchemy_engine_log_level(self):
        """Test default sqlalchemy.engine log level is WARNING."""
        setup_logging()
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING

    def test_default_apscheduler_log_level(self):
        """Test default apscheduler log level is INFO."""
        setup_logging()
        assert logging.getLogger("apscheduler").level == logging.INFO

    def test_custom_uvicorn_access_log_level(self):
        """Test custom uvicorn.access log level."""
        setup_logging(uvicorn_access_log_level="DEBUG")
        assert logging.getLogger("uvicorn.access").level == logging.DEBUG

    def test_custom_uvicorn_error_log_level(self):
        """Test custom uvicorn.error log level."""
        setup_logging(uvicorn_error_log_level="ERROR")
        assert logging.getLogger("uvicorn.error").level == logging.ERROR

    def test_custom_sqlalchemy_engine_log_level(self):
        """Test custom sqlalchemy.engine log level."""
        setup_logging(sqlalchemy_engine_log_level="CRITICAL")
        assert logging.getLogger("sqlalchemy.engine").level == logging.CRITICAL

    def test_custom_apscheduler_log_level(self):
        """Test custom apscheduler log level."""
        setup_logging(apscheduler_log_level="WARNING")
        assert logging.getLogger("apscheduler").level == logging.WARNING

    def test_all_custom_log_levels(self):
        """Test setting all custom log levels at once."""
        setup_logging(
            log_level="DEBUG",
            uvicorn_access_log_level="ERROR",
            uvicorn_error_log_level="CRITICAL",
            sqlalchemy_engine_log_level="DEBUG",
            apscheduler_log_level="ERROR",
        )
        assert logging.getLogger("uvicorn.access").level == logging.ERROR
        assert logging.getLogger("uvicorn.error").level == logging.CRITICAL
        assert logging.getLogger("sqlalchemy.engine").level == logging.DEBUG
        assert logging.getLogger("apscheduler").level == logging.ERROR

    def test_invalid_log_level_falls_back_to_default(self):
        """Test that invalid log level falls back to default."""
        # Invalid log level should fall back to default (WARNING for uvicorn.access)
        setup_logging(uvicorn_access_log_level="INVALID_LEVEL")
        assert logging.getLogger("uvicorn.access").level == logging.WARNING

    def test_case_insensitive_log_levels(self):
        """Test that log levels are case insensitive."""
        setup_logging(
            uvicorn_access_log_level="debug",
            uvicorn_error_log_level="Error",
            sqlalchemy_engine_log_level="WARNING",
            apscheduler_log_level="CrItIcAl",
        )
        assert logging.getLogger("uvicorn.access").level == logging.DEBUG
        assert logging.getLogger("uvicorn.error").level == logging.ERROR
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
        assert logging.getLogger("apscheduler").level == logging.CRITICAL


class TestSettingsThirdPartyLogLevels:
    """Tests for Settings class with third-party log level configurations."""

    def test_settings_default_log_levels(self):
        """Test Settings has correct default log levels."""
        from app.config import Settings

        settings = Settings(SECRET_KEY="a-secure-secret-key-with-sufficient-length-123456")
        assert settings.UVICORN_ACCESS_LOG_LEVEL == "WARNING"
        assert settings.UVICORN_ERROR_LOG_LEVEL == "INFO"
        assert settings.SQLALCHEMY_ENGINE_LOG_LEVEL == "WARNING"
        assert settings.APSCHEDULER_LOG_LEVEL == "INFO"

    def test_settings_custom_log_levels_from_env(self):
        """Test Settings picks up custom log levels from environment."""
        from app.config import Settings

        with patch.dict(
            os.environ,
            {
                "UVICORN_ACCESS_LOG_LEVEL": "DEBUG",
                "UVICORN_ERROR_LOG_LEVEL": "WARNING",
                "SQLALCHEMY_ENGINE_LOG_LEVEL": "ERROR",
                "APSCHEDULER_LOG_LEVEL": "CRITICAL",
            },
            clear=False,
        ):
            settings = Settings(SECRET_KEY="a-secure-secret-key-with-sufficient-length-123456")
            assert settings.UVICORN_ACCESS_LOG_LEVEL == "DEBUG"
            assert settings.UVICORN_ERROR_LOG_LEVEL == "WARNING"
            assert settings.SQLALCHEMY_ENGINE_LOG_LEVEL == "ERROR"
            assert settings.APSCHEDULER_LOG_LEVEL == "CRITICAL"
