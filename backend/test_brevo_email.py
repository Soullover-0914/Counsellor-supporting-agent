"""
Brevo transactional email unit tests.

These tests never send real email. The Brevo HTTP call is mocked.
"""

from __future__ import annotations

import io
import json
import logging
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

os.environ.setdefault("DATABASE_ENCRYPTION_KEY", "unit-test-encryption-key")
os.environ.setdefault("AUTH_SECRET_KEY", "unit-test-auth-secret-key-32bytes-min")
os.environ["BREVO_API_KEY"] = "xkeysib-test-not-real"
os.environ["BREVO_FROM_EMAIL"] = "noreply@example.com"
os.environ["BREVO_FROM_NAME"] = "Agent 66"
os.environ["EMAIL_ADMIN"] = "231fa04543@gmail.com"
os.environ["APP_LOGIN_URL"] = "http://127.0.0.1:5173/login"

from app.services import email as email_service


class _FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _http_error(status: int, payload: dict | None = None) -> HTTPError:
    body = json.dumps(payload or {"message": "error"}).encode("utf-8")
    return HTTPError(
        url="https://api.brevo.com/v3/smtp/email",
        code=status,
        msg="error",
        hdrs=None,
        fp=io.BytesIO(body),
    )


class BrevoEmailTests(unittest.TestCase):
    def setUp(self):
        self.audit_patch = patch(
            "app.services.email.create_audit_event",
            return_value=None,
        )
        self.audit_patch.start()
        self.addCleanup(self.audit_patch.stop)

    def test_configuration_exists(self):
        self.assertTrue(email_service.email_configured())
        self.assertEqual(email_service.active_email_provider(), "brevo")
        status = email_service.email_status()
        self.assertTrue(status["configured"])
        self.assertTrue(status["brevo_api_key_set"])
        self.assertNotIn("xkeysib-test-not-real", json.dumps(status))

    def test_missing_api_key_fails_safely(self):
        with patch.dict(os.environ, {"BREVO_API_KEY": ""}, clear=False):
            with patch.object(email_service.settings, "brevo_api_key", ""):
                ok, reason = email_service.send_email(
                    to_email="student@example.com",
                    subject="t",
                    body="b",
                )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_NOT_CONFIGURED")

    def test_successful_brevo_request(self):
        fake = _FakeResponse(201, {"messageId": "abc-123"})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="Agent 66 — Registration Approved",
                body="Username:\nstudentx\nTemporary password:\nTempValue1",
            )
            mocked.assert_called_once()
            request = mocked.call_args[0][0]
            self.assertEqual(request.full_url, email_service.BREVO_ENDPOINT)
            self.assertEqual(request.get_header("Api-key"), "xkeysib-test-not-real")
            payload = json.loads(request.data.decode("utf-8"))
            self.assertEqual(payload["sender"]["email"], "noreply@example.com")
            self.assertEqual(payload["to"][0]["email"], "student@example.com")
            self.assertIn("htmlContent", payload)
            self.assertIn("textContent", payload)
        self.assertTrue(ok)
        self.assertEqual(reason, "EMAIL_ACCEPTED")

    def test_brevo_401(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(401, {"message": "Key not found"}),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_HTTP_401")

    def test_brevo_400(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(400, {"message": "invalid sender"}),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_HTTP_400")

    def test_brevo_timeout(self):
        with patch("urllib.request.urlopen", side_effect=TimeoutError()):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_TIMEOUT")

    def test_brevo_403(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(403, {"message": "invalid sender"}),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_HTTP_403")

    def test_brevo_429(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(429, {"message": "rate limited"}),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_HTTP_429")

    def test_brevo_500(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=_http_error(500, {"message": "server error"}),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_HTTP_500")

    def test_brevo_connection_failure(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=URLError("connection refused"),
        ):
            ok, reason = email_service.send_email(
                to_email="student@example.com",
                subject="t",
                body="b",
            )
        self.assertFalse(ok)
        self.assertEqual(reason, "EMAIL_FAILED_CONNECTION")

    def test_admin_signup_email_uses_brevo(self):
        fake = _FakeResponse(201, {"messageId": "admin-1"})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            ok = email_service.notify_admin_signup_request(
                student_name="Swaroop",
                student_id="231FA04B14",
                email="student@example.com",
                username="Swaroop014",
            )
            payload = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        self.assertTrue(ok)
        self.assertEqual(payload["to"][0]["email"], "231fa04543@gmail.com")
        self.assertIn("New Student Registration Request", payload["subject"])

    def test_approval_email_uses_brevo_and_login_url(self):
        fake = _FakeResponse(201, {"messageId": "cred-1"})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            ok, reason = email_service.notify_student_registration_approved(
                to_email="student@example.com",
                username="Swaroop014",
                temporary_password="TempPass12",
            )
            payload = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        self.assertTrue(ok)
        self.assertEqual(reason, "EMAIL_ACCEPTED")
        self.assertEqual(payload["subject"], "Agent 66 — Registration Approved")
        self.assertIn("Swaroop014", payload["textContent"])
        self.assertIn("TempPass12", payload["textContent"])
        self.assertIn("http://127.0.0.1:5173/login", payload["textContent"])
        self.assertIn("change your password", payload["textContent"].lower())

    def test_api_key_not_in_logs(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("agent66.email")
        logger.addHandler(handler)
        try:
            with patch(
                "urllib.request.urlopen",
                side_effect=_http_error(401, {"message": "Key not found"}),
            ):
                email_service.send_email(
                    to_email="student@example.com",
                    subject="t",
                    body="b",
                )
            output = stream.getvalue()
        finally:
            logger.removeHandler(handler)
        self.assertNotIn("xkeysib-test-not-real", output)
        self.assertIn("HTTP 401", output)

    def test_smtp_module_not_used(self):
        import inspect
        source = inspect.getsource(email_service)
        self.assertNotIn("smtplib", source)
        self.assertNotIn("SMTP_HOST", source)
        self.assertNotIn("smtp.gmail.com", source)

    def test_resend_credentials_uses_brevo(self):
        import inspect
        from app.services import registration

        source = inspect.getsource(registration.resend_temporary_credentials)
        self.assertIn("notify_student_registration_approved", source)
        self.assertNotIn("smtplib", source)
        self.assertNotIn("SMTP_HOST", inspect.getsource(registration))

    def test_temporary_password_not_stored_plaintext(self):
        import inspect
        from app.services import registration

        source = inspect.getsource(registration)
        self.assertIn("hash_password(temporary_password)", source)
        self.assertIn("temporary_password = 1", source)
        self.assertNotIn("SET temporary_password = ?", source)

    def test_compatibility_aliases(self):
        self.assertIs(
            email_service.send_admin_signup_notification,
            email_service.notify_admin_signup_request,
        )
        fake = _FakeResponse(201, {"messageId": "alias-1"})
        with patch("urllib.request.urlopen", return_value=fake):
            ok, reason = email_service.send_temporary_credentials(
                to_email="student@example.com",
                username="Swaroop014",
                temporary_password="TempPass12",
            )
        self.assertTrue(ok)
        self.assertEqual(reason, "EMAIL_ACCEPTED")


class SecretScanTests(unittest.TestCase):
    def test_email_status_omits_secrets(self):
        payload = json.dumps(email_service.email_status())
        self.assertNotIn("xkeysib-test-not-real", payload)
        self.assertNotIn("BREVO_API_KEY=", payload)

    def test_frontend_has_no_brevo_key(self):
        root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "frontend", "src")
        )
        hits = []
        for dirpath, _, files in os.walk(root):
            for name in files:
                if not name.endswith((".ts", ".tsx", ".js", ".jsx")):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
                if "BREVO_API_KEY" in text or "xkeysib-" in text:
                    hits.append(path)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
