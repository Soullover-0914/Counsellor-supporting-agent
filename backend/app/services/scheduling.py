from datetime import datetime, timezone
from uuid import uuid4

from app.database.db import get_connection
from app.models.referral import ReferralStatus
from app.services.referral import get_referral


def schedule_counselling_session(
    referral_id: str,
    counsellor_id: str,
    appointment_time: datetime,
):
    referral = get_referral(referral_id)

    if referral is None:
        raise ValueError("Referral not found.")

    # A counsellor must be assigned first.
    if referral.assigned_counsellor is None:
        raise ValueError(
            "A counsellor must be assigned before scheduling a session."
        )

    # The requested counsellor must match the assigned counsellor.
    if referral.assigned_counsellor != counsellor_id:
        raise ValueError(
            "This counsellor is not assigned to the referral."
        )

    # Completed referrals cannot receive a new session.
    if referral.status == ReferralStatus.COMPLETED:
        raise ValueError(
            "A completed referral cannot be scheduled."
        )

    appointment = {
        "appointment_id": f"APT-{uuid4().hex[:8].upper()}",
        "referral_id": referral_id,
        "student_id": referral.student_id,
        "counsellor_id": counsellor_id,
        "appointment_time": appointment_time,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc),
    }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO appointments (
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
            appointment["appointment_id"],
            appointment["referral_id"],
            appointment["student_id"],
            appointment["counsellor_id"],
            appointment["appointment_time"].isoformat(),
            appointment["status"],
            appointment["created_at"].isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    return appointment


def _row_to_appointment(row):
    return {
        "appointment_id": row["appointment_id"],
        "referral_id": row["referral_id"],
        "student_id": row["student_id"],
        "counsellor_id": row["counsellor_id"],
        "appointment_time": datetime.fromisoformat(
            row["appointment_time"]
        ),
        "status": row["status"],
        "created_at": datetime.fromisoformat(
            row["created_at"]
        ),
    }


def get_appointments():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            appointment_id,
            referral_id,
            student_id,
            counsellor_id,
            appointment_time,
            status,
            created_at
        FROM appointments
        ORDER BY appointment_time ASC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [_row_to_appointment(row) for row in rows]


def get_appointment(appointment_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            appointment_id,
            referral_id,
            student_id,
            counsellor_id,
            appointment_time,
            status,
            created_at
        FROM appointments
        WHERE appointment_id = ?
        """,
        (appointment_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return _row_to_appointment(row)