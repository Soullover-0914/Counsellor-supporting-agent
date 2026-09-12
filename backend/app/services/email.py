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

    Render injects secrets as env vars; reading them at send-time avoids
    stale empty values if the process was started before secrets were saved.
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
        "app_login_url": settings.app_login_url,
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


def _deliver(message: EmailMessage, cfg: dict[str, str | int | bool]) -> None:
    host = str(cfg["host"])
    port = int(cfg["port"])
    username = str(cfg["username"])
    password = str(cfg["password"])
    use_tls = bool(cfg["use_tls"])

    if port == 465 or not use_tls:
        with smtplib.SMTP_SSL(host, port, timeout=20) as server:
            server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(message)


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

    cfg = _smtp_settings()
    if not (
        cfg["host"]
        and cfg["from_email"]
        and cfg["username"]
        and cfg["password"]
    ):
        logger.warning(
            "email_skipped_smtp_not_configured recipient_domain=%s",
            to_email.split("@")[-1] if "@" in to_email else "unknown",
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
    message["To"] = to_email
    message.set_content(body)

    try:
        _deliver(message, cfg)
        logger.info(
            "email_sent subject=%s recipient=%s",
            subject,
            mask_email(to_email),
        )
        return True

    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "email_delivery_failed subject=%s error_type=SMTPAuthenticationError "
            "smtp_code=%s smtp_error=%s hint=check_app_password_on_render_env",
            subject,
            getattr(exc, "smtp_code", None),
            (
                exc.smtp_error.decode()
                if isinstance(exc.smtp_error, bytes)
                else exc.smtp_error
            ),
        )
        return False

    except Exception as exc:
        # Fallback: some hosts prefer implicit SSL on 465.
        if int(cfg["port"]) == 587:
            try:
                cfg_ssl = dict(cfg)
                cfg_ssl["port"] = 465
                cfg_ssl["use_tls"] = False
                _deliver(message, cfg_ssl)
                logger.info(
                    "email_sent_via_ssl_fallback subject=%s recipient=%s",
                    subject,
                    mask_email(to_email),
                )
                return True
            except Exception as ssl_exc:
                logger.error(
                    "email_delivery_failed subject=%s error_type=%s detail=%s "
                    "ssl_fallback_type=%s ssl_fallback_detail=%s",
                    subject,
                    type(exc).__name__,
                    str(exc)[:160],
                    type(ssl_exc).__name__,
                    str(ssl_exc)[:160],
                )
                return False

        logger.error(
            "email_delivery_failed subject=%s error_type=%s detail=%s",
            subject,
            type(exc).__name__,
            str(exc)[:200],
        )
        return False


def send_email_with_timeout(
    *,
    to_email: str,
    subject: str,
    body: str,
    timeout_seconds: float = 25,
) -> bool:
    """Send email in a worker thread so the API request cannot hang forever."""

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            send_email,
            to_email=to_email,
            subject=subject,
            body=body,
        )
        try:
            return bool(future.result(timeout=timeout_seconds))
        except FuturesTimeout:
            logger.error(
                "email_delivery_timed_out subject=%s recipient=%s",
                subject,
                mask_email(to_email),
            )
            return False


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
    return send_email_with_timeout(
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
        timeout_seconds=25,
    )
