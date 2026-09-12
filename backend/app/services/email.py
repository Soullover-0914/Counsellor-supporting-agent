"""
Centralised institutional email delivery via Brevo Transactional Email API.

The frontend never talks to Brevo. Secrets stay server-side.
Plaintext passwords and API keys are never logged.
"""

from __future__ import annotations

import html
import json
import logging
import os
import urllib.error
import urllib.request
from typing import Tuple

from app.core.config import settings
from app.services.audit import create_audit_event

logger = logging.getLogger("agent66.email")

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"

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
    return bool(_brevo_api_key() and _from_email())


def active_email_provider() -> str:
    if email_configured():
        return "brevo"
    return "none"


def email_status() -> dict[str, bool | str]:
    """Safe status for admin diagnostics (no secrets)."""

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


def _safe_body_snippet(body: str) -> str:
    """Log-safe fragment that never includes secrets."""

    lowered = body.lower()
    if "api-key" in lowered or "xkeysib" in lowered:
        return "[redacted]"
    return body[:180]


def _audit_email(action: str, outcome: str, resource_id: str | None = None) -> None:
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
        logger.warning("email_audit_failed action=%s", action)


def _text_to_html(text: str) -> str:
    escaped = html.escape(text)
    return (
        "<html><body style=\"font-family:sans-serif;line-height:1.5\">"
        + escaped.replace("\n", "<br/>")
        + "</body></html>"
    )


def _post_brevo(payload: dict) -> tuple[int, dict | str]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BREVO_ENDPOINT,
        data=data,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": _brevo_api_key(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {}
            return int(response.status), parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = _safe_body_snippet(raw)
        return int(exc.code), parsed
    except TimeoutError:
        return 0, "timeout"
    except urllib.error.URLError as exc:
        reason = type(exc.reason).__name__ if exc.reason else "URLError"
        return 0, reason


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    to_name: str = "",
) -> Tuple[bool, str]:
    """
    Submit a transactional email to Brevo.

    Returns (accepted, status_code) where status_code is EMAIL_ACCEPTED
    or a failure token. Acceptance is not the same as mailbox delivery.
    """

    if not to_email:
        logger.warning("email_skipped_missing_recipient")
        return False, "EMAIL_FAILED_MISSING_RECIPIENT"

    if not email_configured():
        logger.warning(
            "email_skipped_brevo_not_configured recipient=%s",
            mask_email(to_email),
        )
        return False, "EMAIL_NOT_CONFIGURED"

    payload = {
        "sender": {
            "name": _from_name(),
            "email": _from_email(),
        },
        "to": [
            {
                "email": to_email,
                **({"name": to_name} if to_name else {}),
            }
        ],
        "subject": subject,
        "textContent": body,
        "htmlContent": _text_to_html(body),
    }

    try:
        status, parsed = _post_brevo(payload)
    except TimeoutError:
        logger.error("Brevo email request failed: timeout")
        return False, "EMAIL_FAILED_TIMEOUT"
    except Exception as exc:
        logger.error(
            "Brevo email request failed: %s",
            type(exc).__name__,
        )
        return False, "EMAIL_FAILED_CONNECTION"

    if status == 0:
        token = str(parsed)
        if token == "timeout":
            logger.error("Brevo email request failed: timeout")
            return False, "EMAIL_FAILED_TIMEOUT"
        logger.error("Brevo email request failed: connection %s", token)
        return False, "EMAIL_FAILED_CONNECTION"

    if 200 <= status < 300:
        message_id = ""
        if isinstance(parsed, dict):
            message_id = str(parsed.get("messageId") or parsed.get("message_id") or "")
        logger.info(
            "Brevo email request accepted recipient=%s message_id=%s",
            mask_email(to_email),
            message_id or "none",
        )
        return True, "EMAIL_ACCEPTED"

    logger.error("Brevo email request failed: HTTP %s", status)
    return False, f"EMAIL_FAILED_HTTP_{status}"


def send_email_with_timeout(
    *,
    to_email: str,
    subject: str,
    body: str,
    timeout_seconds: float = 30,
    to_name: str = "",
) -> Tuple[bool, str]:
    """Compatibility wrapper. Brevo calls already use a socket timeout."""

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
    _audit_email("signup_email_requested", "success", username)
    ok, reason = send_email(
        to_email=admin_email,
        subject="Agent 66 — New Student Registration Request",
        body=body,
        to_name="Administrator",
    )
    _audit_email(
        "signup_email_accepted" if ok else "signup_email_failed",
        "success" if ok else "failure",
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
    _audit_email("temporary_credential_email_requested", "success", username)
    ok, reason = send_email(
        to_email=to_email,
        subject="Agent 66 — Registration Approved",
        body=body,
        to_name=username,
    )
    _audit_email(
        "temporary_credential_email_accepted" if ok else "temporary_credential_email_failed",
        "success" if ok else "failure",
        username,
    )
    return ok, reason


send_admin_signup_notification = notify_admin_signup_request
send_temporary_credentials = notify_student_registration_approved
