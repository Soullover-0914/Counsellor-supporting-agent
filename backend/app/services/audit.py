from datetime import datetime, timezone
from uuid import uuid4

from app.database.db import get_connection


def create_audit_event(
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    outcome: str = "success",
    human_approved: bool | None = None,
) -> dict:
    """
    Create a metadata-only audit event.

    The audit log intentionally does not store:
    - counselling session summaries
    - crisis message contents
    - diagnosis information
    - clinical notes
    - unnecessary sensitive student information
    """

    event = {
        "audit_id": f"AUD-{uuid4().hex[:8].upper()}",
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "human_approved": human_approved,
        "created_at": datetime.now(timezone.utc),
    }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO audit_logs (
            audit_id,
            actor_id,
            actor_role,
            action,
            resource_type,
            resource_id,
            outcome,
            human_approved,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["audit_id"],
            event["actor_id"],
            event["actor_role"],
            event["action"],
            event["resource_type"],
            event["resource_id"],
            event["outcome"],
            (
                None
                if event["human_approved"] is None
                else int(event["human_approved"])
            ),
            event["created_at"].isoformat(),
        ),
    )

    connection.commit()
    connection.close()

    return event


def get_audit_logs(
    limit: int = 100,
) -> list[dict]:
    """
    Return recent audit events.

    RBAC must be enforced by the API layer before
    exposing audit logs to a user.
    """

    if limit < 1:
        limit = 1

    if limit > 500:
        limit = 500

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            audit_id,
            actor_id,
            actor_role,
            action,
            resource_type,
            resource_id,
            outcome,
            human_approved,
            created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "audit_id": row["audit_id"],
            "actor_id": row["actor_id"],
            "actor_role": row["actor_role"],
            "action": row["action"],
            "resource_type": row["resource_type"],
            "resource_id": row["resource_id"],
            "outcome": row["outcome"],
            "human_approved": (
                None
                if row["human_approved"] is None
                else bool(row["human_approved"])
            ),
            "created_at": datetime.fromisoformat(
                row["created_at"]
            ),
        }
        for row in rows
    ]


def get_audit_log(
    audit_id: str,
) -> dict | None:
    """
    Retrieve one audit event by audit ID.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            audit_id,
            actor_id,
            actor_role,
            action,
            resource_type,
            resource_id,
            outcome,
            human_approved,
            created_at
        FROM audit_logs
        WHERE audit_id = ?
        """,
        (audit_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "audit_id": row["audit_id"],
        "actor_id": row["actor_id"],
        "actor_role": row["actor_role"],
        "action": row["action"],
        "resource_type": row["resource_type"],
        "resource_id": row["resource_id"],
        "outcome": row["outcome"],
        "human_approved": (
            None
            if row["human_approved"] is None
            else bool(row["human_approved"])
        ),
        "created_at": datetime.fromisoformat(
            row["created_at"]
        ),
    }