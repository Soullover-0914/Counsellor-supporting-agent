from pathlib import Path

from sqlcipher3 import dbapi2 as sqlite

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    BASE_DIR / "counselling_agent_encrypted.db"
)


def _get_encryption_key() -> str:
    """
    Return the SQLCipher encryption key from application
    configuration.

    The encryption key must not be hardcoded in source code.
    """

    encryption_key = settings.database_encryption_key

    if not encryption_key:
        raise RuntimeError(
            "DATABASE_ENCRYPTION_KEY is not configured. "
            "Set it in the environment or .env file."
        )

    return encryption_key


def get_connection():
    """
    Open a connection to the encrypted SQLCipher database.
    """

    connection = sqlite.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    connection.row_factory = sqlite.Row

    encryption_key = _get_encryption_key()

    connection.execute(
        f"PRAGMA key = '{encryption_key}'"
    )

    connection.execute(
        "PRAGMA cipher_compatibility = 4"
    )

    return connection


def init_db():
    """
    Initialize all Agent 66 database tables.

    The database is encrypted using SQLCipher.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # ============================================================
    # USERS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            student_id TEXT,
            email TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            temporary_password INTEGER NOT NULL DEFAULT 0,
            password_changed_once INTEGER NOT NULL DEFAULT 0,
            full_name TEXT,
            branch TEXT,
            year TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # ============================================================
    # STUDENT REGISTRATION REQUESTS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registration_requests (
            registration_id TEXT PRIMARY KEY,
            student_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            email TEXT NOT NULL,
            username TEXT NOT NULL,
            branch TEXT NOT NULL,
            year TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewed_by TEXT
        )
    """)

    _ensure_user_auth_columns(cursor)

    # ============================================================
    # REFERRALS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            source TEXT NOT NULL,
            urgency TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_counsellor TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # ============================================================
    # COUNSELLING RECORDS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counselling_records (
            record_id TEXT PRIMARY KEY,
            referral_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            counsellor_id TEXT NOT NULL,
            session_date TEXT NOT NULL,
            session_summary TEXT NOT NULL,
            follow_up_required INTEGER NOT NULL DEFAULT 0,
            follow_up_date TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (referral_id)
                REFERENCES referrals(referral_id)
        )
    """)

    # ============================================================
    # APPOINTMENTS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id TEXT PRIMARY KEY,
            referral_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            counsellor_id TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # ============================================================
    # ACCOMMODATIONS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accommodations (
            accommodation_id TEXT PRIMARY KEY,
            referral_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            accommodation_type TEXT NOT NULL,
            academic_contact TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ============================================================
    # CRISIS ESCALATIONS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            escalation_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ============================================================
    # WELLBEING RESOURCES
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            resource_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            description TEXT NOT NULL,
            contact TEXT,
            availability TEXT,
            location TEXT,
            emergency INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ============================================================
    # AUDIT LOGS
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            outcome TEXT NOT NULL,
            human_approved INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()
def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _ensure_column(
    cursor,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> bool:
    columns = _table_columns(cursor, table_name)
    if column_name in columns:
        return False

    cursor.execute(
        f"ALTER TABLE {table_name} "
        f"ADD COLUMN {column_name} {column_definition}"
    )
    return True


def _ensure_user_auth_columns(cursor) -> None:
    """
    Migrate existing encrypted databases safely.

    Existing seeded accounts are treated as fully established
    (not temporary-password accounts).
    """

    added_temporary = _ensure_column(
        cursor,
        "users",
        "temporary_password",
        "INTEGER NOT NULL DEFAULT 0",
    )
    added_changed = _ensure_column(
        cursor,
        "users",
        "password_changed_once",
        "INTEGER NOT NULL DEFAULT 0",
    )
    _ensure_column(cursor, "users", "email", "TEXT")
    _ensure_column(cursor, "users", "full_name", "TEXT")
    _ensure_column(cursor, "users", "branch", "TEXT")
    _ensure_column(cursor, "users", "year", "TEXT")

    if added_temporary or added_changed:
        cursor.execute(
            """
            UPDATE users
            SET
                temporary_password = 0,
                password_changed_once = 1
            WHERE temporary_password = 0
            """
        )
