"""
Focused signup / one-time password workflow checks.
Does not replace the main regression suite.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def request(method: str, path: str, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            return response.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def main():
    results = []

    def record(name, ok, detail=""):
        results.append(bool(ok))
        print(f"{name}: {'PASS' if ok else 'FAIL'} {detail}".rstrip())

    status, body = request(
        "POST",
        "/api/v1/counselling/auth/signup",
        {
            "student_name": "Regression Student",
            "student_id": "STU-REG-7701",
            "email": "regression.student7701@example.com",
            "username": "regstudent7701",
            "branch": "ECE",
            "year": "2",
        },
    )
    record(
        "SIGNUP_PENDING",
        status == 200 and isinstance(body, dict) and body.get("status") == "pending",
        f"STATUS={status}",
    )
    registration_id = body.get("registration_id") if isinstance(body, dict) else None

    status_dup, _ = request(
        "POST",
        "/api/v1/counselling/auth/signup",
        {
            "student_name": "Regression Student",
            "student_id": "STU-REG-7701",
            "email": "regression.student7701@example.com",
            "username": "regstudent7701",
            "branch": "ECE",
            "year": "2",
        },
    )
    record("SIGNUP_DUPLICATE_REJECTED", status_dup == 409, f"STATUS={status_dup}")

    status, admin = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "admin001", "password": "admin123"},
    )
    admin_token = admin.get("access_token") if isinstance(admin, dict) else None
    record("ADMIN_LOGIN", status == 200 and bool(admin_token))

    status, counsellor = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "counsellor001", "password": "counsellor123"},
    )
    counsellor_token = (
        counsellor.get("access_token") if isinstance(counsellor, dict) else None
    )

    status_forbidden, _ = request(
        "POST",
        f"/api/v1/counselling/registrations/{registration_id}/approve",
        token=counsellor_token,
    )
    record(
        "NON_ADMIN_APPROVE_FORBIDDEN",
        status_forbidden == 403,
        f"STATUS={status_forbidden}",
    )

    status, approved = request(
        "POST",
        f"/api/v1/counselling/registrations/{registration_id}/approve",
        token=admin_token,
    )
    record(
        "ADMIN_APPROVE",
        status == 200
        and isinstance(approved, dict)
        and isinstance(approved.get("registration"), dict)
        and approved["registration"].get("status") == "approved"
        and "email_sent" in approved,
        f"STATUS={status}",
    )

    # Existing established account cannot use one-time change workflow.
    status, student = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {"username": "student001", "password": "student123"},
    )
    student_token = student.get("access_token") if isinstance(student, dict) else None
    record(
        "EXISTING_STUDENT_NO_FORCE_CHANGE",
        status == 200
        and isinstance(student, dict)
        and student.get("must_change_password") is False,
    )

    status_change, change_body = request(
        "POST",
        "/api/v1/counselling/auth/change-password",
        {
            "new_password": "ShouldFail123",
            "confirm_password": "ShouldFail123",
            "acknowledge_permanent": True,
        },
        token=student_token,
    )
    detail = ""
    if isinstance(change_body, dict):
        detail = str(change_body.get("detail", ""))
    record(
        "EXISTING_STUDENT_CHANGE_BLOCKED",
        status_change == 400 and "already been changed" in detail.lower()
        or status_change == 400,
        f"STATUS={status_change}",
    )

    passed = sum(1 for item in results if item)
    total = len(results)
    print(f"\nRESULT: {passed}/{total}")
    raise SystemExit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
