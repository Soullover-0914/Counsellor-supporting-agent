"""
Exact-origin CORS allowlist for Agent 66.

Never pair wildcard origins with credentials.
"""

from __future__ import annotations

import os

from app.core.config import settings


CORS_ALLOW_METHODS = (
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
)

CORS_ALLOW_HEADERS = (
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
)


def normalize_origin(value: str) -> str:
    return value.strip().rstrip("/")


def parse_origin_list(*raw_values: str) -> list[str]:
    seen: list[str] = []

    for raw in raw_values:
        if not raw:
            continue

        for part in raw.split(","):
            origin = normalize_origin(part)

            if origin and origin not in seen:
                seen.append(origin)

    return seen


def configured_cors_origins() -> list[str]:
    """
    Build the exact browser-origin allowlist.

    Localhost origins remain available for local development.
    Production frontend origins must be supplied through
    CORS_ALLOWED_ORIGINS.

    The legacy CORS_ORIGINS variable is also accepted temporarily
    for backward compatibility.
    """

    return parse_origin_list(
        settings.cors_allowed_origins,
        os.environ.get("CORS_ALLOWED_ORIGINS", ""),
        os.environ.get("CORS_ORIGINS", ""),
    )
