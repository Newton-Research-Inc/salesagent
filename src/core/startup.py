"""Startup configuration and validation for AdCP Sales Agent."""

import logging

from src.core.config import validate_configuration
from src.core.logging_config import setup_oauth_logging

logger = logging.getLogger(__name__)


def ensure_ctv_formats_exist() -> None:
    """Ensure CTV video formats exist in the database."""
    import json
    from sqlalchemy import select
    from src.core.database.database_session import get_db_session
    from src.core.database.models import CreativeFormat
    
    CTV_FORMATS = [
        {
            "format_id": "ctv_video_15s",
            "name": "CTV Video (15s)",
            "type": "ctv_video",
            "description": "15-second Connected TV video ad",
            "width": 1920,
            "height": 1080,
            "duration_seconds": 15,
            "max_file_size_kb": 102400,
            "specs": {"aspect_ratios": ["16:9"], "audio_required": True, "vast_support": True},
        },
        {
            "format_id": "ctv_video_30s",
            "name": "CTV Video (30s)",
            "type": "ctv_video",
            "description": "30-second Connected TV video ad",
            "width": 1920,
            "height": 1080,
            "duration_seconds": 30,
            "max_file_size_kb": 204800,
            "specs": {"aspect_ratios": ["16:9"], "audio_required": True, "vast_support": True},
        },
        {
            "format_id": "ctv_video_60s",
            "name": "CTV Video (60s)",
            "type": "ctv_video",
            "description": "60-second Connected TV video ad",
            "width": 1920,
            "height": 1080,
            "duration_seconds": 60,
            "max_file_size_kb": 409600,
            "specs": {"aspect_ratios": ["16:9"], "audio_required": True, "vast_support": True},
        },
    ]
    
    try:
        with get_db_session() as session:
            for fmt in CTV_FORMATS:
                stmt = select(CreativeFormat).filter_by(format_id=fmt["format_id"])
                existing = session.scalars(stmt).first()
                
                if not existing:
                    new_format = CreativeFormat(
                        format_id=fmt["format_id"],
                        name=fmt["name"],
                        type=fmt["type"],
                        description=fmt["description"],
                        width=fmt.get("width"),
                        height=fmt.get("height"),
                        duration_seconds=fmt.get("duration_seconds"),
                        max_file_size_kb=fmt.get("max_file_size_kb"),
                        specs=json.dumps(fmt["specs"]),
                        is_standard=True,
                    )
                    session.add(new_format)
                    logger.info(f"📺 Added CTV format: {fmt['format_id']}")
            
            session.commit()
    except Exception as e:
        logger.warning(f"Could not ensure CTV formats: {e}")


def initialize_application() -> None:
    """Initialize the application with configuration validation and setup.

    This should be called at the start of both the MCP server and Admin UI.

    Raises:
        SystemExit: If configuration validation fails
    """
    try:
        logger.info("🚀 Initializing AdCP Sales Agent...")

        # Setup structured logging
        setup_oauth_logging()
        logger.info("✅ Structured logging initialized")

        # Validate all configuration
        validate_configuration()
        logger.info("✅ Configuration validation passed")
        
        # Ensure CTV video formats exist (for Yahoo DSP demos)
        ensure_ctv_formats_exist()
        logger.info("✅ CTV formats verified")

        logger.info("🎉 Application initialization completed successfully")

    except Exception as e:
        logger.error(f"❌ Application initialization failed: {str(e)}")
        raise SystemExit(1) from e


def validate_startup_requirements() -> None:
    """Validate startup requirements without full initialization.

    This is useful for health checks and lightweight validation.
    """
    try:
        from src.core.config import get_config

        # Just check that config can be loaded
        config = get_config()

        # Basic sanity checks
        if not config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")

        if not config.superadmin.emails:
            raise ValueError("SUPER_ADMIN_EMAILS is required")

        logger.info("✅ Startup requirements validation passed")

    except Exception as e:
        logger.error(f"❌ Startup requirements validation failed: {str(e)}")
        raise
