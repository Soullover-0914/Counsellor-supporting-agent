from datetime import datetime, timezone
from uuid import uuid4

from app.database.db import get_connection

from app.agents.counselling_agent.schemas import (
    CounsellingRequest,
    UrgencyLevel,
)

from app.models.referral import (
    Referral,
    ReferralStatus,
)


# ============================================================
# CREATE REFERRAL
# ============================================================

def create_referral(
    request: CounsellingRequest,
    urgency: UrgencyLevel,
) -> Referral:

    referral = Referral(
        referral_id=f"REF-{uuid4().hex[:8].upper()}",
        student_id=request.student_id,
        source=request.source.value,
        urgency=urgency,
        status=ReferralStatus.PENDING,
        assigned_counsellor=None,
        created_at=datetime.now(timezone.utc),
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO referrals (
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
        (
            referral.referral_id,
            referral.student_id,
            referral.source,
            referral.urgency.value,
            referral.status.value,
            referral.assigned_counsellor,
            referral.created_at.isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    return referral


# ============================================================
# GET ALL REFERRALS
# ============================================================

def get_referrals() -> list[Referral]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            referral_id,
            student_id,
            source,
            urgency,
            status,
            assigned_counsellor,
            created_at
        FROM referrals
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        Referral(
            referral_id=row["referral_id"],
            student_id=row["student_id"],
            source=row["source"],
            urgency=UrgencyLevel(row["urgency"]),
            status=ReferralStatus(row["status"]),
            assigned_counsellor=row["assigned_counsellor"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


# ============================================================
# GET SINGLE REFERRAL
# ============================================================

def get_referral(
    referral_id: str,
) -> Referral | None:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            referral_id,
            student_id,
            source,
            urgency,
            status,
            assigned_counsellor,
            created_at
        FROM referrals
        WHERE referral_id = ?
        """,
        (referral_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return Referral(
        referral_id=row["referral_id"],
        student_id=row["student_id"],
        source=row["source"],
        urgency=UrgencyLevel(row["urgency"]),
        status=ReferralStatus(row["status"]),
        assigned_counsellor=row["assigned_counsellor"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ============================================================
# ASSIGN COUNSELLOR
# ============================================================

def assign_counsellor(
    referral_id: str,
    counsellor_id: str,
) -> Referral | None:

    referral = get_referral(referral_id)

    if referral is None:
        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE referrals
        SET
            assigned_counsellor = ?,
            status = ?
        WHERE referral_id = ?
        """,
        (
            counsellor_id,
            ReferralStatus.ASSIGNED.value,
            referral_id,
        ),
    )

    connection.commit()

    connection.close()

    return get_referral(referral_id)


# ============================================================
# UPDATE REFERRAL STATUS
# ============================================================

def update_referral_status(
    referral_id: str,
    new_status: ReferralStatus,
) -> Referral | None:

    referral = get_referral(referral_id)

    if referral is None:
        return None

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if (
        new_status
        in {
            ReferralStatus.ASSIGNED,
            ReferralStatus.IN_PROGRESS,
        }
        and referral.assigned_counsellor is None
    ):
        raise ValueError(
            "A counsellor must be assigned before changing "
            "the referral to this status."
        )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE referrals
        SET status = ?
        WHERE referral_id = ?
        """,
        (
            new_status.value,
            referral_id,
        ),
    )

    connection.commit()

    connection.close()

    return get_referral(referral_id)