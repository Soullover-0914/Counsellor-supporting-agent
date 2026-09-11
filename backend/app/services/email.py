"""
Centralised institutional email recipients and SMTP delivery.

Provider secrets must come from environment configuration.
Plaintext passwords must never be logged.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("agent66.email")


ROLE_EMAIL_RECIPIENTS = {
    "admin": settings.email_admin,
    "hod": settings.email_hod,
    "faculty": settings.email_faculty,
    "counsellor": settings.email_counsellor,
    "mentor": settings.email_mentor,
}


def email_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_from_email
        and settings.smtp_username
        and settings.smtp_password
    )


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """
    Send a plain-text email.

    Returns True on success, False on soft failure.
    Never raises to callers for delivery failures.
    """

    if not to_email:
        logger.warning("email_skipped_missing_recipient")
        return False

    if not email_configured():
        logger.warning(
            "email_skipped_smtp_not_configured recipient_domain=%s",
            to_email.split("@")[-1] if "@" in to_email else "unknown",
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    )
    message["To"] = to_email
    message.set_content(body)

    # Gmail app passwords are often stored with spaces for readability.
    smtp_password = settings.smtp_password.replace(" ", "").strip()
    smtp_username = settings.smtp_username.strip()

    try:
        with smtplib.SMTP(
            settings.smtp_host.strip(),
            settings.smtp_port,
            timeout=12,
        ) as server:
            if settings.smtp_use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()

            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logger.info(
            "email_sent subject=%s recipient_domain=%s",
            subject,
            to_email.split("@")[-1],
        )
        return True

    except smtplib.SMTPAuthenticationError as exc:
        # SMTP replies never include the password; safe to log code + brief reply.
        logger.error(
            "email_delivery_failed subject=%s error_type=SMTPAuthenticationError "
            "smtp_code=%s smtp_error=%s hint=check_app_password_and_restart_backend",
            subject,
            getattr(exc, "smtp_code", None),
            (exc.smtp_error.decode() if isinstance(exc.smtp_error, bytes) else exc.smtp_error),
        )
        return False

    except Exception as exc:
        logger.error(
            "email_delivery_failed subject=%s error_type=%s detail=%s",
            subject,
            type(exc).__name__,
            str(exc)[:200],
        )
        return False


def notify_admin_signup_request(
    *,
    student_name: str,
    student_id: str,
    email: str,
    username: str,
) -> bool:
    admin_email = ROLE_EMAIL_RECIPIENTS["admin"]
    body = (
        "A new student registration request has been submitted.\n\n"
        f"Student:\n{student_name}\n\n"
        f"Student ID:\n{student_id}\n\n"
        f"Email:\n{email}\n\n"
        f"Username:\n{username}\n\n"
        "Please review the pending registration in Agent 66.\n"
    )
    return send_email(
        to_email=admin_email,
        subject="Agent 66 — New Student Registration Request",
        body=body,
    )


def notify_student_registration_approved(
    *,
    to_email: str,
    username: str,
    temporary_password: str,
) -> bool:
    body = (
        "Your Agent 66 registration request has been accepted.\n\n"
        "Status: Approved\n\n"
        "You can now sign in with the temporary credentials below.\n\n"
        f"Username:\n{username}\n\n"
        f"Temporary password:\n{temporary_password}\n\n"
        f"Login:\n{settings.app_login_url}\n\n"
        "Important:\n"
        "This is a temporary password.\n"
        "You must change your password after your first login.\n\n"
        "Your password can be changed only once through the "
        "initial password-change process.\n"
    )
    return send_email(
        to_email=to_email,
        subject="Agent 66 — Registration Accepted",
        body=body,
    )
