"""
Centralised institutional email delivery via Brevo Transactional Email API.

The frontend never talks to Brevo. Secrets stay server-side.
Plaintext passwords and API keys are never logged.

Brevo transport uses the official brevo-python SDK.
"""

from __future__ import annotations

import html
import logging
import os
from typing import Tuple

from brevo import Brevo
from brevo.core.api_error import ApiError

from app.core.config import settings
from app.services.audit import create_audit_event

logger = logging.getLogger("agent66.email")

ROLE_EMAIL_RECIPIENTS = {
    "admin": settings.email_admin,
    "hod": settings.email_hod,
    "faculty": settings.email_faculty,
    "counsellor": settings.email_counsellor,
    "mentor": settings.email_mentor,
}


def _env(name: str, fallback: str = "") -> str:
    value = os.environ.get(name)

    if value is None or str(value).strip() == "":
        return fallback

    return str(value).strip()


def _brevo_api_key() -> str:
    return _env("BREVO_API_KEY", settings.brevo_api_key)


def _from_email() -> str:
    return _env("BREVO_FROM_EMAIL", settings.brevo_from_email)


def _from_name() -> str:
    return _env("BREVO_FROM_NAME", settings.brevo_from_name) or "Agent 66"


def _login_url() -> str:
    return _env("APP_LOGIN_URL", settings.app_login_url)


def _admin_email() -> str:
    return _env("EMAIL_ADMIN", ROLE_EMAIL_RECIPIENTS["admin"])


def email_configured() -> bool:
    return bool(
        _brevo_api_key()
        and _from_email()
    )


def active_email_provider() -> str:
    if email_configured():
        return "brevo"

    return "none"


def email_status() -> dict[str, bool | str]:
    """
    Safe status for admin diagnostics.

    Never exposes:
    - API key
    - temporary password
    - authorization headers
    """

    return {
        "configured": email_configured(),
        "provider": active_email_provider(),
        "brevo_api_key_set": bool(_brevo_api_key()),
        "brevo_from_email_set": bool(_from_email()),
        "app_login_url": _login_url(),
        "hint": (
            "Set BREVO_API_KEY and BREVO_FROM_EMAIL. "
            "SMTP is no longer used for delivery."
        ),
    }


def mask_email(address: str) -> str:
    if not address or "@" not in address:
        return "unknown"

    local, _, domain = address.partition("@")

    if len(local) <= 2:
        visible = local[:1] + "***"
    else:
        visible = local[:2] + "***"

    return f"{visible}@{domain}"


def _audit_email(
    action: str,
    outcome: str,
    resource_id: str | None = None,
) -> None:
    try:
        create_audit_event(
            actor_id="system",
            actor_role="system",
            action=action,
            resource_type="email",
            resource_id=resource_id,
            outcome=outcome,
        )
    except Exception:
        logger.warning(
            "email_audit_failed action=%s",
            action,
        )


def _text_to_html(text: str) -> str:
    escaped = html.escape(text)

    return (
        '<html><body style="font-family:sans-serif;line-height:1.5">'
        + escaped.replace("\n", "<br/>")
        + "</body></html>"
    )


def _brevo_client() -> Brevo:
    """
    Create the official Brevo API client.

    The API key remains server-side and is never returned or logged.
    """

    api_key = _brevo_api_key()

    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not configured")

    return Brevo(
        api_key=api_key,
        timeout=30.0,
    )


def _send_with_brevo_sdk(
    *,
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
) -> tuple[bool, str]:
    """
    Send one transactional email through Brevo's official SDK.

    Returns:
        (True, "EMAIL_ACCEPTED")
        or
        (False, failure token)
    """

    client = _brevo_client()

    try:
        from brevo.transactional_emails import (
            SendTransacEmailRequestSender,
            SendTransacEmailRequestToItem,
        )

        result = client.transactional_emails.send_transac_email(
            subject=subject,
            html_content=_text_to_html(body),
            text_content=body,
            sender=SendTransacEmailRequestSender(
                name=_from_name(),
                email=_from_email(),
            ),
            to=[
                SendTransacEmailRequestToItem(
                    email=to_email,
                    **(
                        {"name": to_name}
                        if to_name
                        else {}
                    ),
                )
            ],
            request_options={
                "max_retries": 0,
                "timeout_in_seconds": 30,
            },
        )

        message_id = getattr(
            result,
            "message_id",
            "",
        )

        logger.info(
            "Brevo email request accepted recipient=%s message_id=%s",
            mask_email(to_email),
            message_id or "none",
        )

        return True, "EMAIL_ACCEPTED"

    except ApiError as exc:
        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        logger.error(
            "Brevo email request failed: HTTP %s",
            status_code or "unknown",
        )

        if status_code:
            return False, f"EMAIL_FAILED_HTTP_{status_code}"

        return False, "EMAIL_FAILED_API"

    except TimeoutError:
        logger.error(
            "Brevo email request failed: timeout"
        )

        return False, "EMAIL_FAILED_TIMEOUT"

    except Exception as exc:
        logger.error(
            "Brevo email request failed: %s",
            type(exc).__name__,
        )

        return False, "EMAIL_FAILED_CONNECTION"


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    to_name: str = "",
) -> Tuple[bool, str]:
    """
    Submit a transactional email to Brevo.

    Returns:
        (accepted, status_code)

    accepted=True means Brevo accepted the message for processing.
    It does NOT mean the recipient mailbox has delivered it.
    """

    if not to_email:
        logger.warning(
            "email_skipped_missing_recipient"
        )

        return (
            False,
            "EMAIL_FAILED_MISSING_RECIPIENT",
        )

    if not email_configured():
        logger.warning(
            "email_skipped_brevo_not_configured recipient=%s",
            mask_email(to_email),
        )

        return (
            False,
            "EMAIL_NOT_CONFIGURED",
        )

    return _send_with_brevo_sdk(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        body=body,
    )


def send_email_with_timeout(
    *,
    to_email: str,
    subject: str,
    body: str,
    timeout_seconds: float = 30,
    to_name: str = "",
) -> Tuple[bool, str]:
    """
    Compatibility wrapper.

    Brevo SDK uses its own request timeout.
    """

    _ = timeout_seconds

    return send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        to_name=to_name,
    )


def notify_admin_signup_request(
    *,
    student_name: str,
    student_id: str,
    email: str,
    username: str,
) -> bool:
    admin_email = _admin_email()

    body = (
        "A new student registration request has been submitted.\n\n"
        f"Student:\n{student_name}\n\n"
        f"Student ID:\n{student_id}\n\n"
        f"Email:\n{email}\n\n"
        f"Username:\n{username}\n\n"
        "Please review the pending registration in Agent 66.\n"
    )

    _audit_email(
        "signup_email_requested",
        "success",
        username,
    )

    ok, reason = send_email(
        to_email=admin_email,
        subject="Agent 66 — New Student Registration Request",
        body=body,
        to_name="Administrator",
    )

    _audit_email(
        "signup_email_accepted"
        if ok
        else "signup_email_failed",
        "success"
        if ok
        else "failure",
        username,
    )

    _ = reason

    return ok


def notify_student_registration_approved(
    *,
    to_email: str,
    username: str,
    temporary_password: str,
) -> Tuple[bool, str]:
    login_url = _login_url()

    body = (
        "Your Agent 66 registration request has been approved.\n\n"
        "Status: Approved\n\n"
        "You can now sign in with the temporary credentials below.\n\n"
        f"Username:\n{username}\n\n"
        f"Temporary password:\n{temporary_password}\n\n"
        f"Login URL:\n{login_url}\n\n"
        "Important:\n"
        "This is a temporary password.\n"
        "You must change your password after your first login.\n\n"
        "Your password can be changed only once through the "
        "initial password-change process.\n"
    )

    _audit_email(
        "temporary_credential_email_requested",
        "success",
        username,
    )

    ok, reason = send_email(
        to_email=to_email,
        subject="Agent 66 — Registration Approved",
        body=body,
        to_name=username,
    )

    _audit_email(
        "temporary_credential_email_accepted"
        if ok
        else "temporary_credential_email_failed",
        "success"
        if ok
        else "failure",
        username,
    )

    return ok, reason


send_admin_signup_notification = notify_admin_signup_request

send_temporary_credentials = notify_student_registration_approved