"""
Optional first-boot demo accounts for empty production databases.

Enabled only when SEED_DEMO_USERS=true.
Existing usernames are never overwritten.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.auth.security import hash_password_material
from app.database.db import get_connection

logger = logging.getLogger("agent66.bootstrap")

# Matches the local/dev accounts used in regression tests.
# Passwords are intentionally the known demo values for continuity.
DEMO_USERS: list[tuple[str, str, str, str | None]] = [
    ("student001", "student123", "student", "STU001"),
    ("student002", "student123", "student", "STU002"),
    ("counsellor001", "counsellor123", "counsellor", None),
    ("mentor001", "mentor123", "mentor", None),
    ("faculty001", "faculty123", "faculty", None),
    ("hod001", "hod123", "hod", None),
    ("dean001", "dean123", "dean", None),
    ("admin001", "admin123", "admin", None),
]


def seed_demo_users_if_enabled(enabled: bool) -> int:
    if not enabled:
        return 0

    created = 0
    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for username, password, role, student_id in DEMO_USERS:
            cursor.execute(
                "SELECT 1 FROM users WHERE username = ?",
                (username,),
            )
            if cursor.fetchone() is not None:
                continue

            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash,
                    role,
                    student_id,
                    email,
                    active,
                    temporary_password,
                    password_changed_once,
                    full_name,
                    branch,
                    year,
                    created_at
                )
                VALUES (?, ?, ?, ?, NULL, 1, 0, 1, ?, NULL, NULL, ?)
                """,
                (
                    username,
                    hash_password_material(password),
                    role,
                    student_id,
                    username,
                    now,
                ),
            )
            created += 1

        connection.commit()
    finally:
        connection.close()

    if created:
        logger.info("demo_users_seeded count=%s", created)
    else:
        logger.info("demo_users_seed_skipped_all_exist")

    return created
