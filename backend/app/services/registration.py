"""
Student registration request workflow.

Pending signup → admin review → approve/reject.
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from uuid import uuid4

from app.auth.security import hash_password, validate_password_policy
from app.database.db import get_connection
from app.models.registration import (
    RegistrationRequest,
    RegistrationStatus,
    SignupRequest,
)
from app.services.email import (
    mask_email,
    notify_admin_signup_request,
    notify_student_registration_approved,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_registration(row) -> RegistrationRequest:
    return RegistrationRequest(
        registration_id=row["registration_id"],
        student_name=row["student_name"],
        student_id=row["student_id"],
        email=row["email"],
        username=row["username"],
        branch=row["branch"],
        year=row["year"],
        status=RegistrationStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        reviewed_at=(
            datetime.fromisoformat(row["reviewed_at"])
            if row["reviewed_at"]
            else None
        ),
        reviewed_by=row["reviewed_by"],
    )


def _username_taken(username: str) -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        )
        if cursor.fetchone() is not None:
            return True

        cursor.execute(
            """
            SELECT 1
            FROM registration_requests
            WHERE username = ?
              AND status = ?
            """,
            (username, RegistrationStatus.PENDING.value),
        )
        return cursor.fetchone() is not None
    finally:
        connection.close()


def _student_id_taken(student_id: str) -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE student_id = ?
              AND active = 1
            """,
            (student_id,),
        )
        if cursor.fetchone() is not None:
            return True

        cursor.execute(
            """
            SELECT 1
            FROM registration_requests
            WHERE student_id = ?
              AND status = ?
            """,
            (student_id, RegistrationStatus.PENDING.value),
        )
        return cursor.fetchone() is not None
    finally:
        connection.close()


def _email_taken(email: str) -> bool:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM users
            WHERE lower(email) = lower(?)
              AND active = 1
            """,
            (email,),
        )
        if cursor.fetchone() is not None:
            return True

        cursor.execute(
            """
            SELECT 1
            FROM registration_requests
            WHERE lower(email) = lower(?)
              AND status = ?
            """,
            (email, RegistrationStatus.PENDING.value),
        )
        return cursor.fetchone() is not None
    finally:
        connection.close()


def create_registration_request(
    request: SignupRequest,
) -> RegistrationRequest:
    if _username_taken(request.username):
        raise ValueError(
            "That username is already in use or has a pending registration."
        )

    if _student_id_taken(request.student_id):
        raise ValueError(
            "That student ID already has an active account or pending registration."
        )

    if _email_taken(request.email):
        raise ValueError(
            "That email already has an active account or pending registration."
        )

    registration = RegistrationRequest(
        registration_id=f"REG-{uuid4().hex[:8].upper()}",
        student_name=request.student_name,
        student_id=request.student_id,
        email=request.email,
        username=request.username,
        branch=request.branch,
        year=request.year,
        status=RegistrationStatus.PENDING,
        created_at=_now(),
        reviewed_at=None,
        reviewed_by=None,
    )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO registration_requests (
                registration_id,
                student_name,
                student_id,
                email,
                username,
                branch,
                year,
                status,
                created_at,
                reviewed_at,
                reviewed_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registration.registration_id,
                registration.student_name,
                registration.student_id,
                registration.email,
                registration.username,
                registration.branch,
                registration.year,
                registration.status.value,
                registration.created_at.isoformat(),
                None,
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    # Soft-fail email: registration remains pending regardless.
    notify_admin_signup_request(
        student_name=registration.student_name,
        student_id=registration.student_id,
        email=registration.email,
        username=registration.username,
    )

    return registration


def list_registration_requests(
    status: str | None = None,
) -> list[RegistrationRequest]:
    connection = get_connection()
    try:
        cursor = connection.cursor()

        if status:
            cursor.execute(
                """
                SELECT *
                FROM registration_requests
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status,),
            )
        else:
            cursor.execute(
                """
                SELECT *
                FROM registration_requests
                ORDER BY created_at DESC
                """
            )

        return [_row_to_registration(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_registration_request(
    registration_id: str,
) -> RegistrationRequest | None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT *
            FROM registration_requests
            WHERE registration_id = ?
            """,
            (registration_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_registration(row)
    finally:
        connection.close()


def generate_temporary_password(length: int = 14) -> str:
    """
    Cryptographically secure temporary password.

    Never derive from student identity fields.
    """

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(
            secrets.choice(alphabet) for _ in range(length)
        )
        try:
            validate_password_policy(password)
            return password
        except ValueError:
            continue


def approve_registration(
    registration_id: str,
    reviewed_by: str,
) -> tuple[RegistrationRequest, str | None]:
    """
    Approve a pending registration and create the student account.

    Returns (registration, temporary_password).
    temporary_password is None when the request was already approved
    (idempotent retry after a gateway timeout) or when no new credential
    was issued.
    """

    registration = get_registration_request(registration_id)

    if registration is None:
        raise ValueError("Registration request not found.")

    # Idempotent: a prior approve may have committed before the HTTP
    # response reached the browser (common with provider/gateway timeouts).
    if registration.status == RegistrationStatus.APPROVED:
        return registration, None

    if registration.status != RegistrationStatus.PENDING:
        raise ValueError(
            "Only pending registration requests can be approved."
        )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (registration.username,),
        )
        if cursor.fetchone() is not None:
            raise ValueError(
                "Cannot approve: username is already associated with an account."
            )

        cursor.execute(
            """
            SELECT 1 FROM users
            WHERE student_id = ? AND active = 1
            """,
            (registration.student_id,),
        )
        if cursor.fetchone() is not None:
            raise ValueError(
                "Cannot approve: student ID already has an active account."
            )
    finally:
        connection.close()

    temporary_password = generate_temporary_password()
    password_hash = hash_password(temporary_password)
    reviewed_at = _now()

    connection = get_connection()
    try:
        cursor = connection.cursor()

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
            VALUES (?, ?, ?, ?, ?, 1, 1, 0, ?, ?, ?, ?)
            """,
            (
                registration.username,
                password_hash,
                "student",
                registration.student_id,
                registration.email,
                registration.student_name,
                registration.branch,
                registration.year,
                reviewed_at.isoformat(),
            ),
        )

        cursor.execute(
            """
            UPDATE registration_requests
            SET
                status = ?,
                reviewed_at = ?,
                reviewed_by = ?
            WHERE registration_id = ?
            """,
            (
                RegistrationStatus.APPROVED.value,
                reviewed_at.isoformat(),
                reviewed_by,
                registration_id,
            ),
        )

        connection.commit()
    finally:
        connection.close()

    updated = get_registration_request(registration_id)
    assert updated is not None
    return updated, temporary_password


def reject_registration(
    registration_id: str,
    reviewed_by: str,
) -> RegistrationRequest:
    registration = get_registration_request(registration_id)

    if registration is None:
        raise ValueError("Registration request not found.")

    if registration.status != RegistrationStatus.PENDING:
        raise ValueError(
            "Only pending registration requests can be rejected."
        )

    reviewed_at = _now()
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE registration_requests
            SET
                status = ?,
                reviewed_at = ?,
                reviewed_by = ?
            WHERE registration_id = ?
            """,
            (
                RegistrationStatus.REJECTED.value,
                reviewed_at.isoformat(),
                reviewed_by,
                registration_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    updated = get_registration_request(registration_id)
    assert updated is not None
    return updated


def resend_temporary_credentials(
    registration_id: str,
) -> tuple[bool, str]:
    """
    Re-issue a new temporary password for an approved registration
    that has not completed the one-time password change.

    Password is updated only after the email is accepted by the provider.
    If the user row is missing but the registration is approved, recreate it.
    """

    registration = get_registration_request(registration_id)

    if registration is None:
        raise ValueError(
            "Registration request not found. Refresh the page — "
            "this request may have been cleared or belongs to an old database."
        )

    if registration.status != RegistrationStatus.APPROVED:
        raise ValueError(
            "Credentials can only be reissued for approved registrations."
        )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                username,
                email,
                temporary_password,
                password_changed_once,
                active
            FROM users
            WHERE username = ?
            """,
            (registration.username,),
        )
        user = cursor.fetchone()

        if user is None:
            # Approved registration without user row (DB cleanup / partial failure).
            temporary_password = generate_temporary_password()
            password_hash = hash_password(temporary_password)
            now = _now().isoformat()
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
                VALUES (?, ?, ?, ?, ?, 1, 1, 0, ?, ?, ?, ?)
                """,
                (
                    registration.username,
                    password_hash,
                    "student",
                    registration.student_id,
                    registration.email,
                    registration.student_name,
                    registration.branch,
                    registration.year,
                    now,
                ),
            )
            connection.commit()

            email_sent, reason = notify_student_registration_approved(
                to_email=registration.email,
                username=registration.username,
                temporary_password=temporary_password,
            )
            temporary_password = ""
            if not email_sent:
                raise ValueError(
                    "Account was recreated but Brevo did not accept the email "
                    f"({reason}). Set BREVO_API_KEY and BREVO_FROM_EMAIL, "
                    "then use Resend temporary credentials again."
                )
            return True, (
                "Credential email accepted by Brevo for "
                f"{mask_email(registration.email)}."
            )

        if not bool(user["active"]):
            raise ValueError("Student account is inactive.")

        if bool(user["password_changed_once"]):
            raise ValueError(
                "Password has already been changed and temporary "
                "credentials cannot be reissued."
            )

        recipient = user["email"] or registration.email
        temporary_password = generate_temporary_password()

        email_sent, reason = notify_student_registration_approved(
            to_email=recipient,
            username=registration.username,
            temporary_password=temporary_password,
        )

        if not email_sent:
            temporary_password = ""
            raise ValueError(
                "Brevo did not accept the credential email "
                f"({reason}). The temporary password was NOT changed. "
                "Set BREVO_API_KEY and BREVO_FROM_EMAIL, then use "
                "Resend temporary credentials again."
            )

        password_hash = hash_password(temporary_password)
        temporary_password = ""

        cursor.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                temporary_password = 1,
                password_changed_once = 0
            WHERE username = ?
            """,
            (password_hash, registration.username),
        )
        connection.commit()
    finally:
        connection.close()

    return True, (
        "Credential email accepted by Brevo for "
        f"{mask_email(recipient)}."
    )
