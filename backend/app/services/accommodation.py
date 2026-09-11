from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.accommodation import (
    AcademicAccommodation,
    AccommodationStatus,
)
from app.services.referral import get_referral
from app.database.db import get_connection


def create_accommodation(
    referral_id: str,
    accommodation_type: str,
    academic_contact: str,
    start_date=None,
    end_date=None,
) -> AcademicAccommodation:

    referral = get_referral(referral_id)

    if referral is None:
        raise ValueError("Referral not found.")

    if not referral.assigned_counsellor:
        raise ValueError(
            "A counsellor must be assigned before requesting an accommodation."
        )

    if start_date and end_date and end_date < start_date:
        raise ValueError(
            "end_date cannot be earlier than start_date."
        )

    accommodation = AcademicAccommodation(
        accommodation_id=f"ACC-{uuid4().hex[:8].upper()}",
        referral_id=referral_id,
        student_id=referral.student_id,
        accommodation_type=accommodation_type,
        academic_contact=academic_contact,
        start_date=start_date,
        end_date=end_date,
        status=AccommodationStatus.REQUESTED,
        created_at=datetime.now(timezone.utc),
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO accommodations (
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
            accommodation.accommodation_id,
            accommodation.referral_id,
            accommodation.student_id,
            accommodation.accommodation_type,
            accommodation.academic_contact,
            (
                accommodation.start_date.isoformat()
                if accommodation.start_date
                else ""
            ),
            (
                accommodation.end_date.isoformat()
                if accommodation.end_date
                else ""
            ),
            accommodation.status,
            accommodation.created_at.isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    return accommodation


def _parse_date(value):
    if not value:
        return None

    return date.fromisoformat(value)


def _row_to_accommodation(row) -> AcademicAccommodation:
    return AcademicAccommodation(
        accommodation_id=row["accommodation_id"],
        referral_id=row["referral_id"],
        student_id=row["student_id"],
        accommodation_type=row["accommodation_type"],
        academic_contact=row["academic_contact"],
        start_date=_parse_date(row["start_date"]),
        end_date=_parse_date(row["end_date"]),
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_accommodations() -> list[AcademicAccommodation]:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            accommodation_id,
            referral_id,
            student_id,
            accommodation_type,
            academic_contact,
            start_date,
            end_date,
            status,
            created_at
        FROM accommodations
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        _row_to_accommodation(row)
        for row in rows
    ]


def get_accommodation(
    accommodation_id: str,
) -> AcademicAccommodation | None:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            accommodation_id,
            referral_id,
            student_id,
            accommodation_type,
            academic_contact,
            start_date,
            end_date,
            status,
            created_at
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return _row_to_accommodation(row)


def update_accommodation_status(
    accommodation_id: str,
    new_status: str,
) -> AcademicAccommodation | None:

    accommodation = get_accommodation(accommodation_id)

    if accommodation is None:
        return None

    allowed_statuses = {
        AccommodationStatus.REQUESTED,
        AccommodationStatus.APPROVED,
        AccommodationStatus.REJECTED,
        AccommodationStatus.COMPLETED,
    }

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid accommodation status: {new_status}"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE accommodations
        SET status = ?
        WHERE accommodation_id = ?
        """,
        (
            new_status,
            accommodation_id,
        ),
    )

    connection.commit()
    connection.close()

    return get_accommodation(accommodation_id)