from datetime import datetime, timezone
from uuid import uuid4

from app.database.db import get_connection
from app.models.referral import ReferralStatus
from app.models.counselling_record import (
    CounsellingRecord,
    SessionStatus,
)
from app.services.referral import get_referral


def _normalize_datetime(value: datetime) -> datetime:
    """
    Normalize datetimes to timezone-aware UTC.

    SQLite may return datetime values without timezone information
    when the stored value does not contain an offset.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def create_counselling_record(
    referral_id: str,
    counsellor_id: str,
    session_date: datetime,
    session_summary: str,
    follow_up_required: bool = False,
    follow_up_date: datetime | None = None,
) -> CounsellingRecord:

    referral = get_referral(referral_id)

    if referral is None:
        raise ValueError("Referral not found.")

    if referral.assigned_counsellor is None:
        raise ValueError(
            "A counsellor must be assigned before creating a session record."
        )

    if referral.assigned_counsellor != counsellor_id:
        raise ValueError(
            "This counsellor is not assigned to the referral."
        )

    if referral.status == ReferralStatus.PENDING:
        raise ValueError(
            "The referral must be assigned before creating a session record."
        )

    record = CounsellingRecord(
        record_id=f"REC-{uuid4().hex[:8].upper()}",
        referral_id=referral_id,
        student_id=referral.student_id,
        counsellor_id=counsellor_id,
        session_date=session_date,
        session_summary=session_summary,
        follow_up_required=follow_up_required,
        follow_up_date=follow_up_date,
        status=SessionStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO counselling_records (
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
            record.record_id,
            record.referral_id,
            record.student_id,
            record.counsellor_id,
            _normalize_datetime(record.session_date).isoformat(),
            record.session_summary,
            1 if record.follow_up_required else 0,
            (
                _normalize_datetime(record.follow_up_date).isoformat()
                if record.follow_up_date
                else None
            ),
            record.status,
            record.created_at.isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    return record


def _row_to_record(row) -> CounsellingRecord:
    session_date = datetime.fromisoformat(row["session_date"])

    follow_up_date = (
        datetime.fromisoformat(row["follow_up_date"])
        if row["follow_up_date"]
        else None
    )

    created_at = datetime.fromisoformat(row["created_at"])

    return CounsellingRecord(
        record_id=row["record_id"],
        referral_id=row["referral_id"],
        student_id=row["student_id"],
        counsellor_id=row["counsellor_id"],
        session_date=session_date,
        session_summary=row["session_summary"],
        follow_up_required=bool(row["follow_up_required"]),
        follow_up_date=follow_up_date,
        status=row["status"],
        created_at=created_at,
    )


def get_counselling_records() -> list[CounsellingRecord]:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
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
        FROM counselling_records
        ORDER BY session_date DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [_row_to_record(row) for row in rows]


def get_counselling_record(
    record_id: str,
) -> CounsellingRecord | None:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
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
        FROM counselling_records
        WHERE record_id = ?
        """,
        (record_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return _row_to_record(row)


def complete_counselling_record(
    record_id: str,
) -> CounsellingRecord | None:

    record = get_counselling_record(record_id)

    if record is None:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE counselling_records
        SET status = ?
        WHERE record_id = ?
        """,
        (
            SessionStatus.COMPLETED,
            record_id,
        ),
    )

    connection.commit()
    connection.close()

    return get_counselling_record(record_id)


def get_follow_ups() -> list[CounsellingRecord]:

    records = get_counselling_records()

    return [
        record
        for record in records
        if record.follow_up_required
    ]


def get_due_follow_ups(
    current_time: datetime | None = None,
) -> list[CounsellingRecord]:

    if current_time is None:
        current_time = datetime.now(timezone.utc)

    current_time = _normalize_datetime(current_time)

    records = get_counselling_records()

    due_follow_ups = []

    for record in records:
        if not record.follow_up_required:
            continue

        if record.follow_up_date is None:
            continue

        follow_up_date = _normalize_datetime(
            record.follow_up_date
        )

        if (
            follow_up_date <= current_time
            and record.status != SessionStatus.COMPLETED
        ):
            due_follow_ups.append(record)

    return due_follow_ups


def complete_follow_up(
    record_id: str,
) -> CounsellingRecord | None:

    record = get_counselling_record(record_id)

    if record is None:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE counselling_records
        SET follow_up_required = 0
        WHERE record_id = ?
        """,
        (record_id,),
    )

    connection.commit()
    connection.close()

    return get_counselling_record(record_id)