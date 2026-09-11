import json
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8000"


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


def login(username, password):

    return request(
        "POST",
        "/api/v1/counselling/auth/login",
        {
            "username": username,
            "password": password,
        },
    )


print("=" * 60)
print("PHASE 19.4.6 SENSITIVE DATA EXPOSURE TEST")
print("=" * 60)


# ------------------------------------------------------------
# LOGIN AS STUDENT
# ------------------------------------------------------------

student_status, student_body = login(
    "student001",
    "student123",
)

student_token = None

if isinstance(student_body, dict):
    student_token = student_body.get("access_token")


print(
    "STUDENT_LOGIN:",
    student_status,
    "| TOKEN:",
    bool(student_token),
)


# ------------------------------------------------------------
# LOGIN RESPONSE MUST NOT EXPOSE PASSWORD HASH
# ------------------------------------------------------------

student_login_text = json.dumps(student_body)

password_hash_exposed = (
    "password_hash" in student_login_text
    or "pbkdf2_sha256" in student_login_text
)

print(
    "PASSWORD_HASH_IN_LOGIN_RESPONSE:",
    password_hash_exposed,
)


# ------------------------------------------------------------
# LOGIN AS COUNSELLOR
# ------------------------------------------------------------

counsellor_status, counsellor_body = login(
    "counsellor001",
    "counsellor123",
)

counsellor_token = None

if isinstance(counsellor_body, dict):
    counsellor_token = counsellor_body.get("access_token")


print(
    "COUNSELLOR_LOGIN:",
    counsellor_status,
    "| TOKEN:",
    bool(counsellor_token),
)


# ------------------------------------------------------------
# COUNSELLOR COUNSELLING RECORD ACCESS
# ------------------------------------------------------------

record_status, record_body = request(
    "GET",
    "/api/v1/counselling/records",
    token=counsellor_token,
)

print(
    "COUNSELLOR_RECORD_ACCESS:",
    record_status,
    "| EXPECTED_200:",
    record_status == 200,
)


# ------------------------------------------------------------
# CHECK COUNSELLING RECORD RESPONSE FOR PASSWORD HASH
# ------------------------------------------------------------

record_text = json.dumps(record_body)

record_password_hash_exposed = (
    "password_hash" in record_text
    or "pbkdf2_sha256" in record_text
)

print(
    "PASSWORD_HASH_IN_RECORD_RESPONSE:",
    record_password_hash_exposed,
)


# ------------------------------------------------------------
# STUDENT MUST NOT LIST ALL COUNSELLING RECORDS
# ------------------------------------------------------------

student_record_status, student_record_body = request(
    "GET",
    "/api/v1/counselling/records",
    token=student_token,
)

print(
    "STUDENT_RECORD_LIST_ACCESS:",
    student_record_status,
    "| EXPECTED_403:",
    student_record_status == 403,
)


# ------------------------------------------------------------
# UNAUTHENTICATED RECORD ACCESS
# ------------------------------------------------------------

unauth_record_status, _ = request(
    "GET",
    "/api/v1/counselling/records",
)

print(
    "NO_TOKEN_RECORD_ACCESS:",
    unauth_record_status,
    "| EXPECTED_401_OR_403:",
    unauth_record_status in (401, 403),
)


# ------------------------------------------------------------
# COUNSELLOR MUST NOT ACCESS AUDIT LOGS
# ------------------------------------------------------------

audit_status, _ = request(
    "GET",
    "/api/v1/counselling/audit-logs",
    token=counsellor_token,
)

print(
    "COUNSELLOR_AUDIT_ACCESS:",
    audit_status,
    "| EXPECTED_403:",
    audit_status == 403,
)


# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

all_passed = (
    student_status == 200
    and bool(student_token)
    and not password_hash_exposed
    and counsellor_status == 200
    and bool(counsellor_token)
    and record_status == 200
    and not record_password_hash_exposed
    and student_record_status == 403
    and unauth_record_status in (401, 403)
    and audit_status == 403
)


print("=" * 60)
print(
    "SENSITIVE_DATA_EXPOSURE_TEST_PASS:",
    all_passed,
)
print("=" * 60)