from datetime import datetime, timezone
from uuid import uuid4

from app.database.db import get_connection


class EscalationEvent:
    def __init__(
        self,
        escalation_id: str,
        student_id: str,
        reason: str,
        severity: str,
        created_at: datetime,
    ):
        self.escalation_id = escalation_id
        self.student_id = student_id
        self.reason = reason
        self.severity = severity
        self.created_at = created_at


def create_crisis_escalation(
    student_id: str,
    reason: str,
) -> EscalationEvent:

    event = EscalationEvent(
        escalation_id=f"ESC-{uuid4().hex[:8].upper()}",
        student_id=student_id,
        reason=reason,
        severity="CRITICAL",
        created_at=datetime.now(timezone.utc),
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO escalations (
            escalation_id,
            student_id,
            reason,
            severity,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event.escalation_id,
            event.student_id,
            event.reason,
            event.severity,
            event.created_at.isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    # IMPORTANT:
    # In production this function will connect to the
    # institution's designated emergency notification channel.
    #
    # Examples:
    # - counselling cell notification
    # - designated safety officer
    # - emergency contact workflow
    #
    # We do NOT pretend that a real notification was sent here.

    return event


def _row_to_escalation(row) -> EscalationEvent:
    return EscalationEvent(
        escalation_id=row["escalation_id"],
        student_id=row["student_id"],
        reason=row["reason"],
        severity=row["severity"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def get_escalations() -> list[EscalationEvent]:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            escalation_id,
            student_id,
            reason,
            severity,
            created_at
        FROM escalations
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [_row_to_escalation(row) for row in rows]