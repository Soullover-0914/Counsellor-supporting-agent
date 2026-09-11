import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from app.agents.counselling_agent.agent import analyze_request
from app.agents.counselling_agent.schemas import (
    CounsellingRequest,
    UrgencyLevel,
)
from app.core.config import settings
from app.database.db import DATABASE_PATH, get_connection
from app.auth.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)


BASE_URL = "http://127.0.0.1:8000"


USERS = {
    "student001": ("student123", "student", "STU001"),
    "student002": ("student123", "student", "STU002"),
    "counsellor001": ("counsellor123", "counsellor", None),
    "mentor001": ("mentor123", "mentor", None),
    "faculty001": ("faculty123", "faculty", None),
    "hod001": ("hod123", "hod", None),
    "dean001": ("dean123", "dean", None),
    "admin001": ("admin123", "admin", None),
}


RESULTS = []


def record(name, passed, details=""):
    RESULTS.append(bool(passed))

    print(
        f"{name}: "
        f"{'PASS' if passed else 'FAIL'}"
        + (f" | {details}" if details else "")
    )


def request(method, path, data=None, token=None):
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = (
        json.dumps(data).encode("utf-8")
        if data is not None
        else None
    )

    request_object = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request_object,
            timeout=10,
        ) as response:

            raw = response.read().decode("utf-8")

            try:
                response_body = json.loads(raw)
            except json.JSONDecodeError:
                response_body = raw

            return response.status, response_body

    except urllib.error.HTTPError as error:

        raw = error.read().decode("utf-8")

        try:
            response_body = json.loads(raw)
        except json.JSONDecodeError:
            response_body = raw

        return error.code, response_body

    except Exception as exc:
        return 0, str(exc)


def login(username, password):
    return request(
        "POST",
        "/api/v1/counselling/auth/login",
        {
            "username": username,
            "password": password,
        },
    )


def get_token(username, password):
    status, body = login(username, password)

    if (
        status == 200
        and isinstance(body, dict)
    ):
        return body.get("access_token")

    return None


def contains_sensitive_password_data(value):
    text = json.dumps(
        value,
        default=str,
    ).lower()

    return (
        "password_hash" in text
        or "pbkdf2_sha256" in text
        or "student123" in text
        or "counsellor123" in text
        or "mentor123" in text
        or "faculty123" in text
        or "hod123" in text
        or "dean123" in text
        or "admin123" in text
    )


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


print_header(
    "PHASE 19.4.8 FULL SYSTEM REGRESSION "
    "AND PRODUCTION READINESS VALIDATION"
)


# ============================================================
# 1. CONFIGURATION VALIDATION
# ============================================================

print_header("1. CONFIGURATION VALIDATION")

config_valid = (
    bool(settings.auth_secret_key)
    and bool(settings.database_encryption_key)
    and settings.token_expiry_seconds > 0
    and settings.environment in {
        "development",
        "testing",
        "production",
    }
)

record(
    "CONFIGURATION_VALID",
    config_valid,
    (
        f"ENVIRONMENT={settings.environment} | "
        f"TOKEN_EXPIRY={settings.token_expiry_seconds}"
    ),
)


# ============================================================
# 2. DATABASE / SQLCIPHER VALIDATION
# ============================================================

print_header("2. ENCRYPTED DATABASE VALIDATION")

database_exists = DATABASE_PATH.exists()

record(
    "ENCRYPTED_DATABASE_EXISTS",
    database_exists,
    str(DATABASE_PATH),
)

db_connection_ok = False
table_count = 0
user_count = 0

if database_exists:
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        )

        tables = [
            row["name"]
            for row in cursor.fetchall()
        ]

        table_count = len(tables)

        cursor.execute(
            "SELECT COUNT(*) AS count FROM users"
        )

        user_count = cursor.fetchone()["count"]

        connection.close()

        db_connection_ok = True

    except Exception as exc:
        print(
            "DATABASE_CONNECTION_ERROR:",
            type(exc).__name__,
            str(exc),
        )

record(
    "SQLCIPHER_CONNECTION",
    db_connection_ok,
    f"TABLE_COUNT={table_count} | USER_COUNT={user_count}",
)


plain_sqlite_header = False
encrypted_header = False

if database_exists:

    try:
        with open(
            DATABASE_PATH,
            "rb",
        ) as database_file:

            header = database_file.read(16)

        plain_sqlite_header = (
            header == b"SQLite format 3\x00"
        )

        encrypted_header = not plain_sqlite_header

        print(
            "FILE_HEADER:",
            header,
        )

    except Exception as exc:

        print(
            "DATABASE_HEADER_ERROR:",
            type(exc).__name__,
            str(exc),
        )

record(
    "DATABASE_NOT_PLAIN_SQLITE",
    not plain_sqlite_header,
)

record(
    "DATABASE_ENCRYPTED_HEADER",
    encrypted_header,
)


# ============================================================
# 3. ALL USER AUTHENTICATION
# ============================================================

print_header("3. ALL USER AUTHENTICATION")

tokens = {}

all_users_authenticated = True

for username, (
    password,
    expected_role,
    expected_student_id,
) in USERS.items():

    status, body = login(
        username,
        password,
    )

    token = None

    if isinstance(body, dict):
        token = body.get("access_token")

    user_passed = (
        status == 200
        and bool(token)
        and isinstance(body, dict)
        and body.get("username") == username
        and body.get("role") == expected_role
        and not contains_sensitive_password_data(body)
    )

    tokens[username] = token

    record(
        f"LOGIN_{username}",
        user_passed,
        f"STATUS={status}",
    )

    all_users_authenticated = (
        all_users_authenticated
        and user_passed
    )

record(
    "ALL_USERS_AUTHENTICATE",
    all_users_authenticated,
)

# Reuse authenticated tokens throughout the regression suite.
student001_token = tokens.get("student001")
student002_token = tokens.get("student002")
counsellor_token = tokens.get("counsellor001")
mentor_token = tokens.get("mentor001")
faculty_token = tokens.get("faculty001")
hod_token = tokens.get("hod001")
dean_token = tokens.get("dean001")
admin_token = tokens.get("admin001")


# ============================================================
# 4. WRONG PASSWORD REJECTION
# ============================================================

print_header("4. WRONG PASSWORD REJECTION")

wrong_passwords_rejected = True

for username in USERS:

    status, body = login(
        username,
        "definitely-wrong-password",
    )

    rejected = (
        status == 401
        and not (
            isinstance(body, dict)
            and body.get("access_token")
        )
    )

    record(
        f"WRONG_PASSWORD_{username}",
        rejected,
        f"STATUS={status}",
    )

    wrong_passwords_rejected = (
        wrong_passwords_rejected
        and rejected
    )

record(
    "ALL_WRONG_PASSWORDS_REJECTED",
    wrong_passwords_rejected,
)


# ============================================================
# 5. TOKEN CREATION / DECODING
# ============================================================

print_header("5. TOKEN VALIDATION")

counsellor_token = tokens.get(
    "counsellor001"
)

student_token = tokens.get(
    "student001"
)

token_validation_pass = False

try:

    current_user = decode_access_token(
        counsellor_token
    )

    token_validation_pass = (
        current_user.username
        == "counsellor001"
        and current_user.role
        == "counsellor"
    )

except Exception as exc:

    print(
        "TOKEN_DECODE_ERROR:",
        type(exc).__name__,
        str(exc),
    )

record(
    "TOKEN_CREATION_AND_DECODING",
    token_validation_pass,
)


# ============================================================
# 6. RBAC API VALIDATION
# ============================================================

print_header("6. API RBAC VALIDATION")

counsellor_referrals_status, counsellor_referrals_body = request(
    "GET",
    "/api/v1/counselling/referrals",
    token=counsellor_token,
)

record(
    "COUNSELLOR_REFERRALS_ACCESS",
    counsellor_referrals_status == 200,
    f"STATUS={counsellor_referrals_status}",
)


student_referrals_status, _ = request(
    "GET",
    "/api/v1/counselling/referrals",
    token=student_token,
)

record(
    "STUDENT_REFERRAL_QUEUE_DENIED",
    student_referrals_status == 403,
    f"STATUS={student_referrals_status}",
)


counsellor_records_status, counsellor_records_body = request(
    "GET",
    "/api/v1/counselling/records",
    token=counsellor_token,
)

record(
    "COUNSELLOR_RECORD_LIST_ACCESS",
    counsellor_records_status == 200,
    f"STATUS={counsellor_records_status}",
)


student_records_status, _ = request(
    "GET",
    "/api/v1/counselling/records",
    token=student_token,
)

record(
    "STUDENT_RECORD_LIST_DENIED",
    student_records_status == 403,
    f"STATUS={student_records_status}",
)


counsellor_audit_status, _ = request(
    "GET",
    "/api/v1/counselling/audit-logs",
    token=counsellor_token,
)

record(
    "COUNSELLOR_AUDIT_LOG_DENIED",
    counsellor_audit_status == 403,
    f"STATUS={counsellor_audit_status}",
)


student_audit_status, _ = request(
    "GET",
    "/api/v1/counselling/audit-logs",
    token=student_token,
)

record(
    "STUDENT_AUDIT_LOG_DENIED",
    student_audit_status == 403,
    f"STATUS={student_audit_status}",
)


no_token_status, _ = request(
    "GET",
    "/api/v1/counselling/referrals",
)

record(
    "NO_TOKEN_PROTECTED_ENDPOINT_DENIED",
    no_token_status in (401, 403),
    f"STATUS={no_token_status}",
)


# ============================================================
# 7. SENSITIVE DATA EXPOSURE
# ============================================================

print_header("7. SENSITIVE DATA EXPOSURE")

student_login_status, student_login_body = login(
    "student001",
    "student123",
)

record(
    "NO_PASSWORD_HASH_IN_LOGIN",
    not contains_sensitive_password_data(
        student_login_body
    ),
)


record(
    "NO_PASSWORD_HASH_IN_RECORD_RESPONSE",
    not contains_sensitive_password_data(
        counsellor_records_body
    ),
)


# ============================================================
# 8. CRISIS DETECTION
# ============================================================

print_header("8. CRISIS SAFETY VALIDATION")

normal_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I am having difficulty managing "
        "my academic schedule and would like support."
    ),
    consent=True,
)

normal_result = analyze_request(
    normal_request
)

record(
    "NORMAL_REQUEST_NO_IMMEDIATE_ESCALATION",
    (
        normal_result.immediate_escalation is False
        and normal_result.urgency
        != UrgencyLevel.CRISIS
    ),
    f"STATUS={normal_result.status}",
)


crisis_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I am thinking about hurting myself "
        "and I do not feel safe right now."
    ),
    consent=True,
)

crisis_result = analyze_request(
    crisis_request
)

crisis_detected = (
    crisis_result.status
    == "immediate_escalation"
    and crisis_result.urgency
    == UrgencyLevel.CRISIS
    and crisis_result.route_to_human is True
    and crisis_result.immediate_escalation is True
)

record(
    "CRISIS_IMMEDIATE_ESCALATION",
    crisis_detected,
    f"STATUS={crisis_result.status}",
)


crisis_no_consent_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I may hurt myself and I am not safe."
    ),
    consent=False,
)

crisis_no_consent_result = analyze_request(
    crisis_no_consent_request
)

crisis_bypasses_consent = (
    crisis_no_consent_result.status
    == "immediate_escalation"
    and crisis_no_consent_result.route_to_human
    is True
    and crisis_no_consent_result.immediate_escalation
    is True
)

record(
    "CRISIS_BYPASSES_CONSENT",
    crisis_bypasses_consent,
)


emergency_resources = (
    crisis_result.crisis_resources
    or []
)

approved_emergency_resource_present = any(
    getattr(resource, "resource_id", None)
    and getattr(resource, "name", None)
    and getattr(resource, "contact", None)
    for resource in emergency_resources
)

record(
    "APPROVED_EMERGENCY_RESOURCE_PRESENT",
    approved_emergency_resource_present,
    f"COUNT={len(emergency_resources)}",
)


# ============================================================
# 9. CONSENT CONTROL
# ============================================================

print_header("9. CONSENT CONTROL")

no_consent_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I am stressed and would like someone "
        "to talk to me."
    ),
    consent=False,
)

no_consent_result = analyze_request(
    no_consent_request
)

record(
    "NORMAL_NO_CONSENT_BLOCKED",
    (
        no_consent_result.status
        == "consent_required"
        and no_consent_result.route_to_human
        is False
        and no_consent_result.immediate_escalation
        is False
    ),
    f"STATUS={no_consent_result.status}",
)


# ============================================================
# 10. COUNSELLING ANALYSIS API
# ============================================================

print_header("10. COUNSELLING ANALYSIS API")

analysis_status, analysis_body = request(
    "POST",
    "/api/v1/counselling/analyze",
    {
        "student_id": "STU001",
        "source": "self_referral",
        "message": (
            "I am finding it difficult to manage "
            "my studies and would like support."
        ),
        "consent": True,
    },
)

record(
    "ANALYZE_ENDPOINT_REACHABLE",
    analysis_status == 200,
    f"STATUS={analysis_status}",
)


# ============================================================
# 11. REFERRAL QUEUE
# ============================================================

print_header("11. REFERRAL QUEUE")

referrals_status, referrals_body = request(
    "GET",
    "/api/v1/counselling/referrals",
    token=counsellor_token,
)

referrals_are_list = isinstance(
    referrals_body,
    list,
)

record(
    "REFERRAL_QUEUE_RETURNS_LIST",
    referrals_status == 200
    and referrals_are_list,
    f"COUNT={len(referrals_body) if referrals_are_list else 0}",
)


referral_id = None

if referrals_are_list and referrals_body:

    for referral in referrals_body:

        if (
            isinstance(referral, dict)
            and referral.get("referral_id")
        ):

            referral_id = referral[
                "referral_id"
            ]

            break

record(
    "EXISTING_REFERRAL_AVAILABLE_FOR_WORKFLOW",
    bool(referral_id),
    f"REFERRAL_ID={referral_id}",
)


# ============================================================
# 12. REFERRAL RETRIEVAL / ASSIGNMENT / STATUS
# ============================================================

print_header(
    "12. REFERRAL RETRIEVAL / ASSIGNMENT / STATUS"
)

if referral_id:

    referral_status, referral_body = request(
        "GET",
        f"/api/v1/counselling/referrals/{referral_id}",
        token=counsellor_token,
    )

    record(
        "REFERRAL_RETRIEVAL",
        referral_status == 200,
        f"STATUS={referral_status}",
    )


    assignment_status, assignment_body = request(
        "PATCH",
        f"/api/v1/counselling/referrals/{referral_id}/assign",
        {
            "counsellor_id": "counsellor001"
        },
        token=counsellor_token,
    )

    record(
        "REFERRAL_ASSIGNMENT",
        assignment_status == 200,
        f"STATUS={assignment_status}",
    )


    current_referral_status = None

    if isinstance(
        assignment_body,
        dict,
    ):
        current_referral_status = (
            assignment_body.get("status")
        )


    status_change_status, status_change_body = request(
        "PATCH",
        f"/api/v1/counselling/referrals/{referral_id}/status",
        {
            "status": "in_progress"
        },
        token=counsellor_token,
    )

    status_change_passed = (
        status_change_status == 200
        or status_change_status == 422
    )

    record(
        "REFERRAL_STATUS_ENDPOINT_REACHABLE",
        status_change_passed,
        f"STATUS={status_change_status}",
    )

else:

    record(
        "REFERRAL_RETRIEVAL",
        False,
        "No referral available",
    )

    record(
        "REFERRAL_ASSIGNMENT",
        False,
        "No referral available",
    )

    record(
        "REFERRAL_STATUS_ENDPOINT_REACHABLE",
        False,
        "No referral available",
    )


# ============================================================
# 13. APPOINTMENT SCHEDULING
# ============================================================

print_header("13. APPOINTMENT SCHEDULING")

appointment_id = None

if referral_id:

    appointment_status, appointment_body = request(
        "POST",
        f"/api/v1/counselling/referrals/{referral_id}/schedule",
        {
            "counsellor_id": "counsellor001",
            "appointment_time": (
                "2027-01-15T10:30:00"
            ),
        },
        token=counsellor_token,
    )

    record(
        "APPOINTMENT_SCHEDULING_ENDPOINT",
        appointment_status in (200, 201, 409, 422),
        f"STATUS={appointment_status}",
    )

    if isinstance(
        appointment_body,
        dict,
    ):
        appointment_id = (
            appointment_body.get(
                "appointment_id"
            )
        )


    appointments_status, appointments_body = request(
        "GET",
        "/api/v1/counselling/appointments",
        token=counsellor_token,
    )

    record(
        "APPOINTMENT_LIST_ACCESS",
        appointments_status == 200,
        f"STATUS={appointments_status}",
    )

else:

    record(
        "APPOINTMENT_SCHEDULING_ENDPOINT",
        False,
        "No referral available",
    )

    record(
        "APPOINTMENT_LIST_ACCESS",
        False,
        "No referral available",
    )


# ============================================================
# 14. RESTRICTED COUNSELLING RECORDS
# ============================================================

print_header("14. RESTRICTED COUNSELLING RECORDS")

records_status, records_body = request(
    "GET",
    "/api/v1/counselling/records",
    token=counsellor_token,
)

record(
    "COUNSELLOR_RESTRICTED_RECORD_LIST",
    records_status == 200,
    f"STATUS={records_status}",
)


student_records_status, _ = request(
    "GET",
    "/api/v1/counselling/records",
    token=student_token,
)

record(
    "STUDENT_RESTRICTED_RECORD_LIST_DENIED",
    student_records_status == 403,
    f"STATUS={student_records_status}",
)


record_id = None

if isinstance(
    records_body,
    list,
):

    for record_item in records_body:

        if (
            isinstance(record_item, dict)
            and record_item.get("record_id")
        ):

            record_id = record_item[
                "record_id"
            ]

            break


record(
    "COUNSELLING_RECORD_EXISTS",
    bool(record_id),
    f"RECORD_ID={record_id}",
)


if record_id:

    student_record_detail_status, _ = request(
        "GET",
        f"/api/v1/counselling/records/{record_id}",
        token=student_token,
    )

    record(
        "STUDENT_CANNOT_ACCESS_OTHER_RECORD",
        student_record_detail_status in (
            403,
            404,
        ),
        f"STATUS={student_record_detail_status}",
    )

    counsellor_record_detail_status, record_detail_body = request(
        "GET",
        f"/api/v1/counselling/records/{record_id}",
        token=counsellor_token,
    )

    record(
        "COUNSELLOR_RECORD_DETAIL_ACCESS",
        counsellor_record_detail_status == 200,
        f"STATUS={counsellor_record_detail_status}",
    )

    record(
        "NO_SENSITIVE_PASSWORD_DATA_IN_RECORD",
        not contains_sensitive_password_data(
            record_detail_body
        ),
    )

else:

    record(
        "STUDENT_CANNOT_ACCESS_OTHER_RECORD",
        False,
        "No record available",
    )

    record(
        "COUNSELLOR_RECORD_DETAIL_ACCESS",
        False,
        "No record available",
    )

    record(
        "NO_SENSITIVE_PASSWORD_DATA_IN_RECORD",
        False,
        "No record available",
    )


# ============================================================
# 15. FOLLOW-UP TRACKING
# ============================================================

print_header("15. FOLLOW-UP TRACKING")

follow_ups_status, follow_ups_body = request(
    "GET",
    "/api/v1/counselling/follow-ups",
    token=counsellor_token,
)

record(
    "FOLLOW_UP_LIST_ACCESS",
    follow_ups_status == 200,
    f"STATUS={follow_ups_status}",
)


due_follow_ups_status, due_follow_ups_body = request(
    "GET",
    "/api/v1/counselling/follow-ups/due",
    token=counsellor_token,
)

record(
    "DUE_FOLLOW_UP_LIST_ACCESS",
    due_follow_ups_status == 200,
    f"STATUS={due_follow_ups_status}",
)


# ============================================================
# 16. ACADEMIC ACCOMMODATION
# ============================================================

print_header("16. ACADEMIC ACCOMMODATION")

accommodations_status, accommodations_body = request(
    "GET",
    "/api/v1/counselling/accommodations",
    token=counsellor_token,
)

record(
    "ACCOMMODATION_LIST_ACCESS",
    accommodations_status == 200,
    f"STATUS={accommodations_status}",
)


accommodation_data_is_non_clinical = True

if isinstance(
    accommodations_body,
    list,
):

    for accommodation in accommodations_body:

        if isinstance(
            accommodation,
            dict,
        ):

            forbidden_reason_fields = {
                "reason",
                "diagnosis",
                "diagnosis_code",
                "mental_health_reason",
                "clinical_reason",
                "session_summary",
            }

            if any(
                field in accommodation
                for field in forbidden_reason_fields
            ):
                accommodation_data_is_non_clinical = False


record(
    "ACCOMMODATION_DOES_NOT_DISCLOSE_COUNSELLING_REASON",
    accommodation_data_is_non_clinical,
)


# ============================================================
# 17. WELLBEING RESOURCE DIRECTORY
# ============================================================

print_header("17. WELLBEING RESOURCE DIRECTORY")

resources_status, resources_body = request(
    "GET",
    "/api/v1/counselling/resources",
    token=student_token,
)

resources_are_list = isinstance(
    resources_body,
    list,
)

record(
    "STUDENT_RESOURCE_DIRECTORY_ACCESS",
    resources_status == 200
    and resources_are_list,
    f"COUNT={len(resources_body) if resources_are_list else 0}",
)


emergency_resources_status, emergency_resources_body = request(
    "GET",
    "/api/v1/counselling/resources/type/emergency",
    token=student_token,
)

emergency_resources_valid = (
    emergency_resources_status == 200
    and isinstance(
        emergency_resources_body,
        list,
    )
)

record(
    "EMERGENCY_RESOURCE_DIRECTORY_ACCESS",
    emergency_resources_valid,
    f"STATUS={emergency_resources_status}",
)


emergency_resource_has_contact = any(
    isinstance(resource, dict)
    and resource.get("active") is True
    and resource.get("emergency") is True
    and resource.get("contact")
    for resource in (
        emergency_resources_body
        if isinstance(
            emergency_resources_body,
            list,
        )
        else []
    )
)

record(
    "EMERGENCY_RESOURCE_HAS_APPROVED_CONTACT",
    emergency_resource_has_contact,
)


# ============================================================
# 18. ANONYMOUS AGGREGATE REPORTING
# ============================================================

print_header("18. ANONYMOUS AGGREGATE REPORTING")

aggregate_status, aggregate_body = request(
    "GET",
    "/api/v1/counselling/reports/aggregate",
    token=admin_token,
)

aggregate_reachable = (
    aggregate_status == 200
    and isinstance(
        aggregate_body,
        dict,
    )
)

record(
    "AGGREGATE_REPORT_ACCESS",
    aggregate_reachable,
    f"STATUS={aggregate_status}",
)


aggregate_has_student_identity = False

if isinstance(
    aggregate_body,
    dict,
):

    aggregate_text = json.dumps(
        aggregate_body,
        default=str,
    )

    aggregate_has_student_identity = (
        "student_id" in aggregate_text
        or "student001" in aggregate_text
        or "student002" in aggregate_text
    )

record(
    "AGGREGATE_REPORT_DOES_NOT_EXPOSE_STUDENT_ID",
    not aggregate_has_student_identity,
)


# ============================================================
# 19. CRISIS ESCALATION QUEUE
# ============================================================

print_header("19. CRISIS ESCALATION QUEUE")

escalations_status, escalations_body = request(
    "GET",
    "/api/v1/counselling/escalations",
    token=counsellor_token,
)

record(
    "CRISIS_ESCALATION_QUEUE_ACCESS",
    escalations_status == 200,
    f"STATUS={escalations_status}",
)


escalation_exists = (
    isinstance(
        escalations_body,
        list,
    )
    and len(escalations_body) > 0
)

record(
    "CRISIS_ESCALATION_RECORD_EXISTS",
    escalation_exists,
)


# ============================================================
# 20. AUDIT LOGGING
# ============================================================

print_header("20. AUDIT LOGGING")

audit_status, audit_body = request(
    "GET",
    "/api/v1/counselling/audit-logs?limit=50",
    token=admin_token,
)

audit_access_valid = (
    audit_status == 200
    and isinstance(
        audit_body,
        list,
    )
)

record(
    "ADMIN_AUDIT_LOG_ACCESS",
    audit_access_valid,
    f"STATUS={audit_status}",
)


audit_metadata_valid = True
audit_sensitive_content_found = False

if isinstance(
    audit_body,
    list,
):

    for audit in audit_body:

        if not isinstance(
            audit,
            dict,
        ):
            audit_metadata_valid = False
            continue

        required_metadata = {
            "audit_id",
            "actor_id",
            "actor_role",
            "action",
            "resource_type",
            "outcome",
            "created_at",
        }

        if not required_metadata.issubset(
            audit.keys()
        ):
            audit_metadata_valid = False

        audit_text = json.dumps(
            audit,
            default=str,
        ).lower()

        if (
            "password_hash" in audit_text
            or "pbkdf2_sha256" in audit_text
        ):
            audit_sensitive_content_found = True


record(
    "AUDIT_METADATA_COMPLETE",
    audit_metadata_valid,
)


record(
    "AUDIT_LOG_DOES_NOT_STORE_PASSWORD_HASH",
    not audit_sensitive_content_found,
)


# ============================================================
# 21. DATABASE USER TABLE VALIDATION
# ============================================================

print_header("21. DATABASE USER SECURITY VALIDATION")

user_hash_format_valid = True
user_hash_count = 0

try:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            username,
            password_hash,
            role,
            active
        FROM users
        ORDER BY username
        """
    )

    user_rows = cursor.fetchall()

    for row in user_rows:

        user_hash_count += 1

        stored_hash = row["password_hash"]

        valid_format = (
            isinstance(
                stored_hash,
                str,
            )
            and stored_hash.startswith(
                "pbkdf2_sha256$"
            )
            and len(
                stored_hash.split("$")
            ) == 4
        )

        if not valid_format:
            user_hash_format_valid = False

    connection.close()

except Exception as exc:

    user_hash_format_valid = False

    print(
        "USER_HASH_DATABASE_ERROR:",
        type(exc).__name__,
        str(exc),
    )

record(
    "ALL_DATABASE_PASSWORDS_USE_PBKDF2",
    user_hash_format_valid,
    f"USER_HASH_COUNT={user_hash_count}",
)


# ============================================================
# 22. SOURCE CODE SECURITY CHECKS
# ============================================================

print_header("22. SOURCE CODE SECURITY CHECKS")

security_file = Path(
    "app/auth/security.py"
)

database_file = Path(
    "app/database/db.py"
)

config_file = Path(
    "app/core/config.py"
)

gitignore_file = Path(
    ".gitignore"
)

security_text = (
    security_file.read_text(
        encoding="utf-8"
    )
    if security_file.exists()
    else ""
)

database_text = (
    database_file.read_text(
        encoding="utf-8"
    )
    if database_file.exists()
    else ""
)

config_text = (
    config_file.read_text(
        encoding="utf-8"
    )
    if config_file.exists()
    else ""
)

gitignore_text = (
    gitignore_file.read_text(
        encoding="utf-8"
    )
    if gitignore_file.exists()
    else ""
)


plaintext_passwords_in_security = any(
    value in security_text
    for value in [
        "student123",
        "counsellor123",
        "mentor123",
        "faculty123",
        "hod123",
        "dean123",
        "admin123",
    ]
)

record(
    "NO_PLAINTEXT_PASSWORDS_IN_SECURITY_SOURCE",
    not plaintext_passwords_in_security,
)


hardcoded_database_key = (
    "agent66-development-encryption-key"
    in database_text
)

record(
    "NO_HARDCODED_DATABASE_KEY_IN_DB_SOURCE",
    not hardcoded_database_key,
)


hardcoded_auth_key = (
    "agent66-development-secret-change-before-production"
    in security_text
)

record(
    "NO_HARDCODED_AUTH_KEY_IN_SECURITY_SOURCE",
    not hardcoded_auth_key,
)


env_protected = (
    ".env" in gitignore_text
    and "*.db" in gitignore_text
)

record(
    "ENV_AND_DATABASE_FILES_PROTECTED_BY_GITIGNORE",
    env_protected,
)


# ============================================================
# 23. PYTHON COMPILE VALIDATION
# ============================================================

print_header("23. PYTHON COMPILE VALIDATION")

compile_process = subprocess.run(
    [
        sys.executable,
        "-m",
        "compileall",
        "-q",
        "app",
    ],
    capture_output=True,
    text=True,
)

compile_passed = (
    compile_process.returncode == 0
)

record(
    "ALL_APPLICATION_MODULES_COMPILE",
    compile_passed,
    (
        compile_process.stderr.strip()
        if compile_process.stderr
        else "OK"
    ),
)


# ============================================================
# 24. EXISTING PHASE 19 TESTS
# ============================================================

print_header("24. EXISTING PHASE 19 TESTS")

existing_tests = [
    "test_phase19_4_5.py",
    "test_phase19_4_6.py",
    "test_phase19_4_7.py",
]

for test_file in existing_tests:

    test_path = Path(test_file)

    if not test_path.exists():

        record(
            f"EXISTING_TEST_{test_file}",
            False,
            "FILE_NOT_FOUND",
        )

        continue

    process = subprocess.run(
        [
            sys.executable,
            str(test_path),
        ],
        capture_output=True,
        text=True,
    )

    output = (
        process.stdout
        + "\n"
        + process.stderr
    )

    if test_file == "test_phase19_4_5.py":
        test_passed = (
            "API_RBAC_REGRESSION_PASS: True"
            in output
        )

    elif test_file == "test_phase19_4_6.py":
        test_passed = (
            "SENSITIVE_DATA_EXPOSURE_TEST_PASS: True"
            in output
        )

    elif test_file == "test_phase19_4_7.py":
        test_passed = (
            "CRISIS_SAFETY_VALIDATION_PASS: True"
            in output
        )

    else:
        test_passed = (
            process.returncode == 0
        )

    record(
        f"EXISTING_TEST_{test_file}",
        test_passed,
    )


# ============================================================
# 25. FINAL REGRESSION RESULT
# ============================================================

print_header(
    "FINAL PHASE 19.4.8 RESULT"
)

total_tests = len(RESULTS)
passed_tests = sum(
    1
    for result in RESULTS
    if result
)

failed_tests = (
    total_tests
    - passed_tests
)

all_passed = (
    failed_tests == 0
)

print(
    "TOTAL_TESTS:",
    total_tests,
)

print(
    "PASSED_TESTS:",
    passed_tests,
)

print(
    "FAILED_TESTS:",
    failed_tests,
)

print()

print(
    "PHASE_19_4_8_FULL_REGRESSION_PASS:",
    all_passed,
)

print("=" * 70)


if not all_passed:
    print(
        "PRODUCTION_READINESS_STATUS: "
        "NOT_READY"
    )
else:
    print(
        "PRODUCTION_READINESS_STATUS: "
        "READY_FOR_FINAL_REVIEW"
    )

print("=" * 70)