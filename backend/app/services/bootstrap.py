"""
First-boot bootstrap for empty Agent 66 databases.

Runs only when the encrypted database file did not previously exist
(or the users table is completely empty). Existing production data is
never overwritten or re-seeded.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.auth.security import hash_password_material
from app.database.db import DATABASE_PATH, get_connection
from app.services.resources import seed_default_resources

logger = logging.getLogger("agent66.bootstrap")

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


def database_file_exists() -> bool:
    path = Path(DATABASE_PATH)
    return path.is_file() and path.stat().st_size > 0


def users_table_is_empty() -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        row = cursor.fetchone()
        return int(row["count"]) == 0
    finally:
        connection.close()


def should_run_first_boot_seed(*, seed_enabled: bool) -> bool:
    """
    Seed only on a true first boot.

    - seed_enabled must be true (SEED_DEMO_USERS)
    - database file was missing before init, OR users table is empty
    """

    if not seed_enabled:
        logger.info("First-boot seed disabled (SEED_DEMO_USERS is false)")
        return False

    if users_table_is_empty():
        return True

    logger.info(
        "Existing database preserved — first-boot seed skipped"
    )
    return False


def _seed_users(cursor, now: str) -> int:
    created = 0
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
    return created


def _seed_operational_demo(cursor, now: str) -> None:
    """Insert demo referrals and related records for empty first-boot DBs."""

    today = datetime.now(timezone.utc).date()
    tomorrow = (
        datetime.now(timezone.utc) + timedelta(days=1)
    ).replace(microsecond=0).isoformat()
    next_week = (today + timedelta(days=7)).isoformat()
    today_date = today.isoformat()

    demo_referrals = [
        (
            "REF-DEMO01",
            "STU001",
            "self_referral",
            "support",
            "assigned",
            "counsellor001",
            now,
        ),
        (
            "REF-DEMO02",
            "STU002",
            "mentor_referral",
            "urgent",
            "pending",
            None,
            now,
        ),
        (
            "REF-DEMO03",
            "STU001",
            "faculty_referral",
            "normal",
            "in_progress",
            "counsellor001",
            now,
        ),
    ]

    for row in demo_referrals:
        cursor.execute(
            """
            INSERT OR IGNORE INTO referrals (
                referral_id,
                student_id,
                source,
                urgency,
                status,
                assigned_counsellor,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    cursor.execute(
        """
        INSERT OR IGNORE INTO counselling_records (
            record_id,
            referral_id,
            student_id,
            counsellor_id,
            session_date,
            session_summary,
            follow_up_required,
            follow_up_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "REC-DEMO01",
            "REF-DEMO01",
            "STU001",
            "counsellor001",
            now,
            "Initial supportive intake completed. Student agreed to follow-up.",
            1,
            next_week,
            "active",
            now,
        ),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO appointments (
            appointment_id,
            referral_id,
            student_id,
            counsellor_id,
            appointment_time,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "APT-DEMO01",
            "REF-DEMO01",
            "STU001",
            "counsellor001",
            tomorrow,
            "scheduled",
            now,
        ),
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO accommodations (
            accommodation_id,
            referral_id,
            student_id,
            accommodation_type,
            academic_contact,
            start_date,
            end_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ACC-DEMO01",
            "REF-DEMO03",
            "STU001",
            "deadline_extension",
            "faculty001",
            today_date,
            next_week,
            "requested",
            now,
        ),
    )


def repair_invalid_demo_rows() -> int:
    """
    Repair first-boot demo rows that used invalid urgency/source/date formats.

    Safe to run on every startup; only updates known bad demo values.
    """

    connection = get_connection()
    fixed = 0
    try:
        cursor = connection.cursor()

        repairs = [
            (
                """
                UPDATE referrals
                SET urgency = 'support', source = 'self_referral'
                WHERE referral_id = 'REF-DEMO01'
                  AND (urgency = 'medium' OR source = 'self_request')
                """,
            ),
            (
                """
                UPDATE referrals
                SET urgency = 'urgent'
                WHERE referral_id = 'REF-DEMO02'
                  AND urgency IN ('medium', 'high')
                """,
            ),
            (
                """
                UPDATE referrals
                SET urgency = 'normal'
                WHERE referral_id = 'REF-DEMO03'
                  AND urgency IN ('medium', 'low')
                """,
            ),
            (
                """
                UPDATE accommodations
                SET
                    start_date = substr(start_date, 1, 10),
                    end_date = substr(end_date, 1, 10)
                WHERE accommodation_id = 'ACC-DEMO01'
                  AND (
                    instr(start_date, 'T') > 0
                    OR instr(end_date, 'T') > 0
                  )
                """,
            ),
        ]

        for (sql,) in repairs:
            cursor.execute(sql)
            fixed += cursor.rowcount

        connection.commit()
    finally:
        connection.close()

    if fixed:
        logger.info("demo_row_repair_applied changes=%s", fixed)

    return fixed


def run_first_boot_seed() -> dict[str, int | bool]:
    """
    Populate a brand-new database with demo users and sample workflow data.
    """

    now = datetime.now(timezone.utc).isoformat()
    connection = get_connection()
    users_created = 0
    try:
        cursor = connection.cursor()
        users_created = _seed_users(cursor, now)
        connection.commit()
    finally:
        connection.close()

    seed_default_resources()

    connection = get_connection()
    try:
        cursor = connection.cursor()
        _seed_operational_demo(cursor, now)
        connection.commit()
    finally:
        connection.close()

    logger.info(
        "First-boot seed complete users_created=%s",
        users_created,
    )
    return {
        "seeded": True,
        "users_created": users_created,
    }


# Backwards-compatible name used by older main.py call sites
def seed_demo_users_if_enabled(enabled: bool) -> int:
    if not should_run_first_boot_seed(seed_enabled=enabled):
        return 0
    result = run_first_boot_seed()
    return int(result["users_created"])
