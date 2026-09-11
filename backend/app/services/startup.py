"""
Production startup safety checks and database boot sequence.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from app.core.config import settings
from app.database.db import DATABASE_PATH, init_db
from app.services.bootstrap import (
    database_file_exists,
    run_first_boot_seed,
    should_run_first_boot_seed,
)

logger = logging.getLogger("agent66.startup")


def _is_production() -> bool:
    return settings.environment.strip().lower() == "production"


def verify_production_secrets() -> None:
    if not _is_production():
        return

    if not settings.auth_secret_key:
        raise RuntimeError(
            "AUTH_SECRET_KEY is required in production."
        )

    if not settings.database_encryption_key:
        raise RuntimeError(
            "DATABASE_ENCRYPTION_KEY is required in production."
        )


def verify_persistent_storage() -> Path:
    """
    Ensure the database directory exists and is writable.

    Production expects DATABASE_PATH under /var/data on Render.
    """

    db_path = Path(DATABASE_PATH)
    data_dir = db_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    probe = data_dir / ".agent66_write_probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Persistent storage is not writable: {data_dir}"
        ) from exc

    if _is_production():
        expected = Path("/var/data")
        if data_dir.resolve() != expected.resolve() and not str(
            data_dir
        ).startswith("/var/data"):
            logger.warning(
                "Production DATABASE_PATH is not under /var/data "
                "(current=%s). Attach a Render persistent disk.",
                data_dir,
            )

    return data_dir


def initialize_application() -> None:
    """
    Run once at process import / startup.
    """

    if _is_production():
        logger.info("Production mode detected")
    else:
        logger.info(
            "Application environment=%s",
            settings.environment,
        )

    verify_production_secrets()
    data_dir = verify_persistent_storage()
    logger.info("Persistent storage verified path=%s", data_dir)

    existed_before = database_file_exists()
    init_db()
    logger.info(
        "Encrypted database loaded path=%s existed_before=%s",
        DATABASE_PATH,
        existed_before,
    )

    if should_run_first_boot_seed(
        seed_enabled=settings.seed_demo_users
    ):
        run_first_boot_seed()
        logger.info("Database ready (first-boot seed applied)")
    else:
        logger.info("Database ready (existing data preserved)")

    # Helpful for operators inspecting container logs
    if os.environ.get("DATABASE_PATH"):
        logger.info(
            "DATABASE_PATH=%s",
            os.environ.get("DATABASE_PATH"),
        )
