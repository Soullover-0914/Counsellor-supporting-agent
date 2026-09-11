from uuid import uuid4

from app.models.resource import (
    CreateResourceRequest,
    ResourceType,
    WellbeingResource,
)
from app.database.db import get_connection


def seed_default_resources():
    """
    Add approved example resources to the SQLite database.

    Institutions can replace these with their own verified resources.
    The seed operation is idempotent, so existing resources are not
    duplicated when the application restarts.
    """

    connection = get_connection()
    cursor = connection.cursor()

    default_resources = [
        WellbeingResource(
            resource_id="RES-001",
            name="University Counselling Cell",
            resource_type=ResourceType.COUNSELLING,
            description=(
                "Contact the university counselling cell "
                "for professional human support."
            ),
            contact="University counselling office",
            availability="Institution-defined",
            location="University campus",
            emergency=False,
            active=True,
        ),
        WellbeingResource(
            resource_id="RES-002",
            name="Student Wellbeing Support",
            resource_type=ResourceType.WELLBEING,
            description=(
                "Approved wellbeing resources and student "
                "support services provided by the institution."
            ),
            contact="Student affairs office",
            availability="Institution-defined",
            location="University campus",
            emergency=False,
            active=True,
        ),
        WellbeingResource(
            resource_id="RES-003",
            name="Campus Emergency Contact",
            resource_type=ResourceType.EMERGENCY,
            description=(
                "Use the institution's designated emergency "
                "contact when immediate safety assistance is required."
            ),
            contact="Institution-approved emergency contact",
            availability="24/7 if institution provides it",
            location="University campus",
            emergency=True,
            active=True,
        ),
    ]

    for resource in default_resources:
        cursor.execute(
            """
            INSERT OR IGNORE INTO resources (
                resource_id,
                name,
                resource_type,
                description,
                contact,
                availability,
                location,
                emergency,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resource.resource_id,
                resource.name,
                resource.resource_type,
                resource.description,
                resource.contact,
                resource.availability,
                resource.location,
                int(resource.emergency),
                int(resource.active),
            ),
        )

    connection.commit()
    connection.close()


def _row_to_resource(row) -> WellbeingResource:
    return WellbeingResource(
        resource_id=row["resource_id"],
        name=row["name"],
        resource_type=row["resource_type"],
        description=row["description"],
        contact=row["contact"],
        availability=row["availability"],
        location=row["location"],
        emergency=bool(row["emergency"]),
        active=bool(row["active"]),
    )


def get_resources() -> list[WellbeingResource]:
    seed_default_resources()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            resource_id,
            name,
            resource_type,
            description,
            contact,
            availability,
            location,
            emergency,
            active
        FROM resources
        WHERE active = 1
        ORDER BY resource_id ASC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        _row_to_resource(row)
        for row in rows
    ]


def get_resource(
    resource_id: str,
) -> WellbeingResource | None:

    seed_default_resources()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            resource_id,
            name,
            resource_type,
            description,
            contact,
            availability,
            location,
            emergency,
            active
        FROM resources
        WHERE resource_id = ?
        """,
        (resource_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return _row_to_resource(row)


def get_resources_by_type(
    resource_type: str,
) -> list[WellbeingResource]:

    seed_default_resources()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            resource_id,
            name,
            resource_type,
            description,
            contact,
            availability,
            location,
            emergency,
            active
        FROM resources
        WHERE resource_type = ?
          AND active = 1
        ORDER BY resource_id ASC
        """,
        (resource_type,),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        _row_to_resource(row)
        for row in rows
    ]


def create_resource(
    request: CreateResourceRequest,
) -> WellbeingResource:

    resource = WellbeingResource(
        resource_id=f"RES-{uuid4().hex[:8].upper()}",
        name=request.name,
        resource_type=request.resource_type,
        description=request.description,
        contact=request.contact,
        availability=request.availability,
        location=request.location,
        emergency=request.emergency,
        active=True,
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO resources (
            resource_id,
            name,
            resource_type,
            description,
            contact,
            availability,
            location,
            emergency,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resource.resource_id,
            resource.name,
            resource.resource_type,
            resource.description,
            resource.contact,
            resource.availability,
            resource.location,
            int(resource.emergency),
            int(resource.active),
        ),
    )

    connection.commit()
    connection.close()

    return resource


def deactivate_resource(
    resource_id: str,
) -> WellbeingResource | None:

    resource = get_resource(resource_id)

    if resource is None:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE resources
        SET active = 0
        WHERE resource_id = ?
        """,
        (resource_id,),
    )

    connection.commit()
    connection.close()

    return get_resource(resource_id)