"""
CORS / preflight tests for Agent 66.

These tests never call Brevo, never open the production database,
and never print secrets.
"""

from __future__ import annotations

import unittest
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.cors import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    configured_cors_origins,
    parse_origin_list,
)

LOCAL_ORIGIN = "http://127.0.0.1:5173"
PRODUCTION_FRONTEND_ORIGIN = "https://frontend-pi-fawn-59ukp6dnl5.vercel.app"
DISALLOWED_ORIGIN = "https://evil.example"
RESEND_PATH = "/api/v1/counselling/registrations/REG-0B947F08/resend-credentials"
APPROVE_PATH = "/api/v1/counselling/registrations/REG-0B947F08/approve"


def _cors_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_cors_origins(),
        allow_credentials=True,
        allow_methods=list(CORS_ALLOW_METHODS),
        allow_headers=list(CORS_ALLOW_HEADERS),
        expose_headers=[],
    )

    @app.post(RESEND_PATH)
    @app.post(APPROVE_PATH)
    def protected(authorization: str | None = Header(default=None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = authorization.split(" ", 1)[1]
        if token == "student-token":
            raise HTTPException(status_code=403, detail="Forbidden")
        if token != "admin-token":
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"email_sent": True}

    return app


class CorsConfigTests(unittest.TestCase):
    def test_parse_normalizes_whitespace_and_trailing_slash(self):
        origins = parse_origin_list(
            " http://127.0.0.1:5173/ , ,https://frontend-pi-fawn-59ukp6dnl5.vercel.app/ "
        )
        self.assertEqual(
            origins,
            [
                "http://127.0.0.1:5173",
                "https://frontend-pi-fawn-59ukp6dnl5.vercel.app",
            ],
        )

    def test_configured_origins_include_local_origins(self):
        origins = configured_cors_origins()
        self.assertIn(LOCAL_ORIGIN, origins)
        self.assertIn("http://localhost:5173", origins)
        self.assertNotIn("*", origins)

    def test_production_origin_can_be_configured_from_environment(self):
        previous_value = os.environ.get("CORS_ALLOWED_ORIGINS")

        try:
            os.environ["CORS_ALLOWED_ORIGINS"] = (
                f"{PRODUCTION_FRONTEND_ORIGIN},{LOCAL_ORIGIN}"
            )

            origins = configured_cors_origins()

            self.assertIn(PRODUCTION_FRONTEND_ORIGIN, origins)
            self.assertIn(LOCAL_ORIGIN, origins)
            self.assertNotIn("*", origins)

        finally:
            if previous_value is None:
                os.environ.pop("CORS_ALLOWED_ORIGINS", None)
            else:
                os.environ["CORS_ALLOWED_ORIGINS"] = previous_value


class CorsMiddlewareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(_cors_app())

    def _preflight(self, origin: str, path: str = RESEND_PATH):
        return self.client.options(
            path,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

    def test_local_origin_receives_cors_headers(self):
        response = self._preflight(LOCAL_ORIGIN)
        self.assertIn(response.status_code, (200, 204))
        self.assertEqual(response.headers.get("access-control-allow-origin"), LOCAL_ORIGIN)
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_production_frontend_origin_receives_cors_headers(self):
        response = self._preflight(PRODUCTION_FRONTEND_ORIGIN, APPROVE_PATH)
        self.assertIn(response.status_code, (200, 204))
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            PRODUCTION_FRONTEND_ORIGIN,
        )
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_preflight_allows_authorization_header(self):
        response = self._preflight(LOCAL_ORIGIN)
        allowed = (response.headers.get("access-control-allow-headers") or "").lower()
        self.assertIn("authorization", allowed)
        methods = (response.headers.get("access-control-allow-methods") or "").upper()
        self.assertIn("POST", methods)
        self.assertIn("OPTIONS", methods)

    def test_unconfigured_origin_is_not_allowed(self):
        response = self._preflight(DISALLOWED_ORIGIN)
        self.assertNotEqual(
            response.headers.get("access-control-allow-origin"),
            DISALLOWED_ORIGIN,
        )

    def test_authentication_still_required(self):
        response = self.client.post(
            RESEND_PATH,
            headers={"Origin": LOCAL_ORIGIN},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("access-control-allow-origin"), LOCAL_ORIGIN)

    def test_authorization_header_is_accepted(self):
        response = self.client.post(
            RESEND_PATH,
            headers={
                "Origin": LOCAL_ORIGIN,
                "Authorization": "Bearer admin-token",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), LOCAL_ORIGIN)

    def test_rbac_student_cannot_resend(self):
        response = self.client.post(
            RESEND_PATH,
            headers={
                "Origin": LOCAL_ORIGIN,
                "Authorization": "Bearer student-token",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers.get("access-control-allow-origin"), LOCAL_ORIGIN)


if __name__ == "__main__":
    unittest.main()
