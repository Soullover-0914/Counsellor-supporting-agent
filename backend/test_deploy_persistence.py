"""
Deploy persistence smoke checks for Agent 66.

Usage:
  set BASE_URL=https://agent66-counselling.onrender.com
  python test_deploy_persistence.py
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get(
    "BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

RESULTS: list[bool] = []


def record(name: str, passed: bool, details: str = "") -> None:
    RESULTS.append(bool(passed))
    print(
        f"{name}: {'PASS' if passed else 'FAIL'}"
        + (f" | {details}" if details else "")
    )


def request(method: str, path: str, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = (
        json.dumps(data).encode("utf-8")
        if data is not None
        else None
    )

    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def main() -> None:
    print(f"BASE_URL={BASE_URL}")

    status, health = request("GET", "/health")
    record(
        "HEALTH",
        status == 200
        and isinstance(health, dict)
        and health.get("status") == "healthy",
        str(health),
    )

    if isinstance(health, dict):
        record(
            "STORAGE_PATH",
            str(health.get("storage_path", "")).endswith("/var/data")
            or health.get("storage_path") == "/var/data"
            or BASE_URL.startswith("http://127.0.0.1"),
            str(health.get("storage_path")),
        )
        record(
            "DATABASE_PRESENT",
            health.get("database_present") is True
            or BASE_URL.startswith("http://127.0.0.1"),
            str(health.get("database_present")),
        )

    status, login = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "admin001", "password": "admin123"},
    )
    token = login.get("access_token") if isinstance(login, dict) else None
    record(
        "AUTH_LOGIN",
        status == 200 and bool(token),
        f"STATUS={status}",
    )

    status, me_role = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "hod001", "password": "hod123"},
    )
    hod_token = (
        me_role.get("access_token") if isinstance(me_role, dict) else None
    )
    record("RBAC_HOD_LOGIN", status == 200 and bool(hod_token))

    status, referrals = request(
        "GET",
        "/api/v1/counselling/referrals",
        token=hod_token,
    )
    referral_count = len(referrals) if isinstance(referrals, list) else 0
    record(
        "REFERRALS_PRESENT",
        status == 200 and referral_count > 0,
        f"COUNT={referral_count}",
    )

    status, resources = request(
        "GET",
        "/api/v1/counselling/resources",
        token=token,
    )
    resource_count = len(resources) if isinstance(resources, list) else 0
    record(
        "RESOURCES_PRESENT",
        status == 200 and resource_count > 0,
        f"COUNT={resource_count}",
    )

    status, records = request(
        "GET",
        "/api/v1/counselling/records",
        token=token,
    )
    # Admin may or may not list records depending on RBAC; counsellor path:
    if status != 200:
        status_c, counsellor = request(
            "POST",
            "/api/v1/counselling/auth/login",
            {
                "username": "counsellor001",
                "password": "counsellor123",
            },
        )
        c_token = (
            counsellor.get("access_token")
            if isinstance(counsellor, dict)
            else None
        )
        status, records = request(
            "GET",
            "/api/v1/counselling/records",
            token=c_token,
        )
        record("COUNSELLOR_LOGIN_FOR_RECORDS", status_c == 200)

    record_count = len(records) if isinstance(records, list) else 0
    record(
        "RECORDS_PRESENT",
        status == 200 and record_count > 0,
        f"COUNT={record_count}",
    )

    status, bad = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "admin001", "password": "wrong-password"},
    )
    record("AUTH_REJECTS_BAD_PASSWORD", status == 401)

    passed = sum(1 for item in RESULTS if item)
    total = len(RESULTS)
    print(f"\nRESULT {passed}/{total}")
    raise SystemExit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
