"""
Centralised institutional email recipients and SMTP delivery.

Provider secrets must come from environment configuration.
Plaintext passwords must never be logged.
"""

from __future__ import annotations

import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from email.message import EmailMessage
from typing import Tuple

from app.core.config import settings

logger = logging.getLogger("agent66.email")


ROLE_EMAIL_RECIPIENTS = {
    "admin": settings.email_admin,
    "hod": settings.email_hod,
    "faculty": settings.email_faculty,
    "counsellor": settings.email_counsellor,
    "mentor": settings.email_mentor,
}


def _smtp_settings() -> dict[str, str | int | bool]:
    """
    Read SMTP settings from process environment first, then settings.
    """

    def env(name: str, fallback: str = "") -> str:
        value = os.environ.get(name)
        if value is None or value.strip() == "":
            return fallback
        return value.strip()

    host = env("SMTP_HOST", settings.smtp_host)
    username = env("SMTP_USERNAME", settings.smtp_username)
    password = env("SMTP_PASSWORD", settings.smtp_password).replace(" ", "")
    from_email = env("SMTP_FROM_EMAIL", settings.smtp_from_email)
    from_name = env("SMTP_FROM_NAME", settings.smtp_from_name)
    port_raw = env("SMTP_PORT", str(settings.smtp_port or 587))
    try:
        port = int(port_raw)
    except ValueError:
        port = 587

    use_tls_raw = env(
        "SMTP_USE_TLS",
        "true" if settings.smtp_use_tls else "false",
    ).lower()
    use_tls = use_tls_raw in {"1", "true", "yes", "on"}

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "from_name": from_name or "Agent 66",
        "use_tls": use_tls,
    }


def email_configured() -> bool:
    cfg = _smtp_settings()
    return bool(
        cfg["host"]
        and cfg["from_email"]
        and cfg["username"]
        and cfg["password"]
    )


def email_status() -> dict[str, bool | str]:
    """Safe status for admin diagnostics (no secrets)."""

    cfg = _smtp_settings()
    return {
        "configured": email_configured(),
        "smtp_host_set": bool(cfg["host"]),
        "smtp_username_set": bool(cfg["username"]),
        "smtp_password_set": bool(cfg["password"]),
        "smtp_from_email_set": bool(cfg["from_email"]),
        "smtp_port": str(cfg["port"]),
        "app_login_url": (
            os.environ.get("APP_LOGIN_URL", "").strip()
            or settings.app_login_url
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


def _deliver_on_port(
    message: EmailMessage,
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_starttls: bool,
) -> None:
    if port == 465 or not use_starttls:
        with smtplib.SMTP_SSL(host, port, timeout=15) as server:
            server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(message)


def _attempt_ports(
    host: str,
    configured_port: int,
    use_tls: bool,
) -> list[tuple[int, bool]]:
    """
    Build SMTP attempt order.

    Gmail / many cloud hosts work more reliably on 465 (SSL) from Render.
    """

    attempts: list[tuple[int, bool]] = []
    host_l = host.lower()

    if "gmail.com" in host_l or "google.com" in host_l:
        attempts.extend([(465, False), (587, True)])
    else:
        attempts.append((configured_port, use_tls))
        if configured_port != 465:
            attempts.append((465, False))
        if configured_port != 587:
            attempts.append((587, True))

    # Deduplicate while preserving order
    seen: set[tuple[int, bool]] = set()
    ordered: list[tuple[int, bool]] = []
    for item in attempts:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> Tuple[bool, str]:
    """
    Send a plain-text email.

    Returns (success, reason_code). Never raises to callers.
    """

    if not to_email:
        logger.warning("email_skipped_missing_recipient")
        return False, "missing_recipient"

    cfg = _smtp_settings()
    if not (
        cfg["host"]
        and cfg["from_email"]
        and cfg["username"]
        and cfg["password"]
    ):
        logger.warning(
            "email_skipped_smtp_not_configured recipient=%s",
            mask_email(to_email),
        )
        return False, "smtp_not_configured"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
    message["To"] = to_email
    message.set_content(body)

    host = str(cfg["host"])
    username = str(cfg["username"])
    password = str(cfg["password"])
    errors: list[str] = []

    for port, use_starttls in _attempt_ports(
        host,
        int(cfg["port"]),
        bool(cfg["use_tls"]),
    ):
        try:
            _deliver_on_port(
                message,
                host=host,
                port=port,
                username=username,
                password=password,
                use_starttls=use_starttls,
            )
            logger.info(
                "email_sent subject=%s recipient=%s port=%s",
                subject,
                mask_email(to_email),
                port,
            )
            return True, f"sent_via_{port}"
        except smtplib.SMTPAuthenticationError as exc:
            detail = (
                exc.smtp_error.decode()
                if isinstance(exc.smtp_error, bytes)
                else str(exc.smtp_error)
            )
            errors.append(f"auth_{port}:{detail[:80]}")
            logger.error(
                "email_auth_failed port=%s recipient=%s",
                port,
                mask_email(to_email),
            )
        except Exception as exc:
            errors.append(f"{type(exc).__name__}_{port}")
            logger.error(
                "email_delivery_failed port=%s error_type=%s detail=%s",
                port,
                type(exc).__name__,
                str(exc)[:160],
            )

    reason = errors[0] if errors else "delivery_failed"
    return False, reason


def send_email_with_timeout(
    *,
    to_email: str,
    subject: str,
    body: str,
    timeout_seconds: float = 35,
) -> Tuple[bool, str]:
    """Send email in a worker thread so the API cannot hang forever."""

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            send_email,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeout:
            logger.error(
                "email_delivery_timed_out subject=%s recipient=%s",
                subject,
                mask_email(to_email),
            )
            return False, "timeout"


def notify_admin_signup_request(
    *,
    student_name: str,
    student_id: str,
    email: str,
    username: str,
) -> bool:
    admin_email = (
        os.environ.get("EMAIL_ADMIN", "").strip()
        or ROLE_EMAIL_RECIPIENTS["admin"]
    )
    body = (
        "A new student registration request has been submitted.\n\n"
        f"Student:\n{student_name}\n\n"
        f"Student ID:\n{student_id}\n\n"
        f"Email:\n{email}\n\n"
        f"Username:\n{username}\n\n"
        "Please review the pending registration in Agent 66.\n"
    )
    ok, _reason = send_email_with_timeout(
        to_email=admin_email,
        subject="Agent 66 — New Student Registration Request",
        body=body,
        timeout_seconds=20,
    )
    return ok


def notify_student_registration_approved(
    *,
    to_email: str,
    username: str,
    temporary_password: str,
) -> Tuple[bool, str]:
    login_url = (
        os.environ.get("APP_LOGIN_URL", "").strip()
        or settings.app_login_url
    )
    body = (
        "Your Agent 66 registration request has been accepted.\n\n"
        "Status: Approved\n\n"
        "You can now sign in with the temporary credentials below.\n\n"
        f"Username:\n{username}\n\n"
        f"Temporary password:\n{temporary_password}\n\n"
        f"Login:\n{login_url}\n\n"
        "Important:\n"
        "This is a temporary password.\n"
        "You must change your password after your first login.\n\n"
        "Your password can be changed only once through the "
        "initial password-change process.\n"
    )
    return send_email_with_timeout(
        to_email=to_email,
        subject="Agent 66 — Registration Accepted",
        body=body,
        timeout_seconds=35,
    )
