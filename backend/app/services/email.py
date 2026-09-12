"""
Centralised institutional email delivery.

Priority order (production-safe):
1. Brevo HTTP API   (BREVO_API_KEY)  — works on Render free/paid
2. Resend HTTP API  (RESEND_API_KEY) — works on Render free/paid
3. SMTP (Gmail etc.) — works locally / paid Render; often blocked on free

Plaintext passwords are never logged.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import socket
import urllib.error
import urllib.request
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


def _env(name: str, fallback: str = "") -> str:
    value = os.environ.get(name)
    if value is None or str(value).strip() == "":
        return fallback
    return str(value).strip()


def _smtp_settings() -> dict[str, str | int | bool]:
    host = _env("SMTP_HOST", settings.smtp_host)
    username = _env("SMTP_USERNAME", settings.smtp_username)
    password = _env("SMTP_PASSWORD", settings.smtp_password).replace(" ", "")
    from_email = _env("SMTP_FROM_EMAIL", settings.smtp_from_email)
    from_name = _env("SMTP_FROM_NAME", settings.smtp_from_name)
    port_raw = _env("SMTP_PORT", str(settings.smtp_port or 465))
    try:
        port = int(port_raw)
    except ValueError:
        port = 465

    use_tls_raw = _env(
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
    if _env("BREVO_API_KEY") or _env("RESEND_API_KEY"):
        return bool(_env("SMTP_FROM_EMAIL", settings.smtp_from_email))
    cfg = _smtp_settings()
    return bool(
        cfg["host"]
        and cfg["from_email"]
        and cfg["username"]
        and cfg["password"]
    )


def active_email_provider() -> str:
    if _env("BREVO_API_KEY"):
        return "brevo_http"
    if _env("RESEND_API_KEY"):
        return "resend_http"
    if email_configured():
        return "smtp"
    return "none"


def email_status() -> dict[str, bool | str]:
    cfg = _smtp_settings()
    return {
        "configured": email_configured(),
        "provider": active_email_provider(),
        "brevo_api_key_set": bool(_env("BREVO_API_KEY")),
        "resend_api_key_set": bool(_env("RESEND_API_KEY")),
        "smtp_host_set": bool(cfg["host"]),
        "smtp_username_set": bool(cfg["username"]),
        "smtp_password_set": bool(cfg["password"]),
        "smtp_from_email_set": bool(cfg["from_email"]),
        "smtp_port": str(cfg["port"]),
        "app_login_url": _env("APP_LOGIN_URL", settings.app_login_url),
        "hint": (
            "Prefer BREVO_API_KEY or RESEND_API_KEY on Render. "
            "Free Render instances block outbound SMTP ports 25/465/587."
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


def _http_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict,
    timeout: float = 20,
) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return int(response.status), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), body


def _send_via_brevo(
    *,
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    api_key: str,
) -> Tuple[bool, str]:
    status, response_body = _http_json(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": api_key,
        },
        payload={
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body,
        },
    )
    if 200 <= status < 300:
        return True, "sent_via_brevo"
    logger.error(
        "brevo_send_failed status=%s body=%s",
        status,
        response_body[:200],
    )
    return False, f"brevo_http_{status}"


def _send_via_resend(
    *,
    to_email: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
    api_key: str,
) -> Tuple[bool, str]:
    status, response_body = _http_json(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload={
            "from": f"{from_name} <{from_email}>",
            "to": [to_email],
            "subject": subject,
            "text": body,
        },
    )
    if 200 <= status < 300:
        return True, "sent_via_resend"
    logger.error(
        "resend_send_failed status=%s body=%s",
        status,
        response_body[:200],
    )
    return False, f"resend_http_{status}"


def _deliver_on_port(
    message: EmailMessage,
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_starttls: bool,
) -> None:
    # Force IPv4 — Render IPv6 SMTP paths commonly hang.
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        ipv4 = infos[0][4][0] if infos else host
    except OSError:
        ipv4 = host

    if port == 465 or not use_starttls:
        with smtplib.SMTP_SSL(ipv4, port, timeout=12) as server:
            server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(ipv4, port, timeout=12) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(message)


def _send_via_smtp(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> Tuple[bool, str]:
    cfg = _smtp_settings()
    if not (
        cfg["host"]
        and cfg["from_email"]
        and cfg["username"]
        and cfg["password"]
    ):
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

    attempts: list[tuple[int, bool]] = [(465, False), (587, True)]
    configured = (int(cfg["port"]), bool(cfg["use_tls"]))
    if configured not in attempts:
        attempts.insert(0, configured)

    for port, use_starttls in attempts:
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
                "email_sent provider=smtp recipient=%s port=%s",
                mask_email(to_email),
                port,
            )
            return True, f"sent_via_smtp_{port}"
        except smtplib.SMTPAuthenticationError:
            errors.append(f"auth_{port}")
        except Exception as exc:
            errors.append(f"{type(exc).__name__}_{port}")
            logger.error(
                "smtp_failed port=%s error_type=%s detail=%s",
                port,
                type(exc).__name__,
                str(exc)[:160],
            )

    return False, errors[0] if errors else "smtp_failed"


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> Tuple[bool, str]:
    if not to_email:
        return False, "missing_recipient"

    from_email = _env("SMTP_FROM_EMAIL", settings.smtp_from_email)
    from_name = _env("SMTP_FROM_NAME", settings.smtp_from_name) or "Agent 66"

    brevo_key = _env("BREVO_API_KEY")
    if brevo_key and from_email:
        ok, reason = _send_via_brevo(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            api_key=brevo_key,
        )
        if ok:
            return ok, reason

    resend_key = _env("RESEND_API_KEY")
    if resend_key and from_email:
        ok, reason = _send_via_resend(
            to_email=to_email,
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            api_key=resend_key,
        )
        if ok:
            return ok, reason

    return _send_via_smtp(to_email=to_email, subject=subject, body=body)


def send_email_with_timeout(
    *,
    to_email: str,
    subject: str,
    body: str,
    timeout_seconds: float = 30,
) -> Tuple[bool, str]:
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
                "email_delivery_timed_out recipient=%s",
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
    admin_email = _env("EMAIL_ADMIN", ROLE_EMAIL_RECIPIENTS["admin"])
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
    login_url = _env("APP_LOGIN_URL", settings.app_login_url)
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
        timeout_seconds=30,
    )
