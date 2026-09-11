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

    status, body = request(
        "POST",
        "/api/v1/counselling/auth/login",
        {
            "username": username,
            "password": password,
        },
    )

    token = None

    if isinstance(body, dict):
        token = body.get("access_token")

    return status, body, token


print("=" * 60)
print("PHASE 19.4.5 API AUTHENTICATION REGRESSION")
print("=" * 60)


# ------------------------------------------------------------
# VALID STUDENT LOGIN
# ------------------------------------------------------------

student_status, student_body, student_token = login(
    "student001",
    "student123",
)

print(
    "STUDENT_LOGIN:",
    student_status,
    "| TOKEN:",
    bool(student_token),
)


# ------------------------------------------------------------
# VALID COUNSELLOR LOGIN
# ------------------------------------------------------------

counsellor_status, counsellor_body, counsellor_token = login(
    "counsellor001",
    "counsellor123",
)

print(
    "COUNSELLOR_LOGIN:",
    counsellor_status,
    "| TOKEN:",
    bool(counsellor_token),
)


# ------------------------------------------------------------
# INVALID LOGIN
# ------------------------------------------------------------

invalid_status, _, _ = login(
    "student001",
    "wrongpassword",
)

print(
    "INVALID_LOGIN_STATUS:",
    invalid_status,
    "| EXPECTED_401:",
    invalid_status == 401,
)


# ------------------------------------------------------------
# COUNSELLOR -> REFERRALS
# Expected: 200
# ------------------------------------------------------------

counsellor_referrals_status, _ = request(
    "GET",
    "/api/v1/counselling/referrals",
    token=counsellor_token,
)

print(
    "COUNSELLOR_REFERRALS_STATUS:",
    counsellor_referrals_status,
    "| EXPECTED_200:",
    counsellor_referrals_status == 200,
)


# ------------------------------------------------------------
# STUDENT -> REFERRALS
# Expected: 403
# ------------------------------------------------------------

student_referrals_status, _ = request(
    "GET",
    "/api/v1/counselling/referrals",
    token=student_token,
)

print(
    "STUDENT_REFERRALS_STATUS:",
    student_referrals_status,
    "| EXPECTED_403:",
    student_referrals_status == 403,
)


# ------------------------------------------------------------
# COUNSELLOR -> COUNSELLING RECORDS
# Expected: 200
# ------------------------------------------------------------

counsellor_records_status, _ = request(
    "GET",
    "/api/v1/counselling/records",
    token=counsellor_token,
)

print(
    "COUNSELLOR_RECORDS_STATUS:",
    counsellor_records_status,
    "| EXPECTED_200:",
    counsellor_records_status == 200,
)


# ------------------------------------------------------------
# STUDENT -> COUNSELLING RECORDS
# Expected: 403
# ------------------------------------------------------------

student_records_status, _ = request(
    "GET",
    "/api/v1/counselling/records",
    token=student_token,
)

print(
    "STUDENT_RECORDS_STATUS:",
    student_records_status,
    "| EXPECTED_403:",
    student_records_status == 403,
)


# ------------------------------------------------------------
# COUNSELLOR -> AUDIT LOGS
# Expected: 403
# ------------------------------------------------------------

counsellor_audit_status, _ = request(
    "GET",
    "/api/v1/counselling/audit-logs",
    token=counsellor_token,
)

print(
    "COUNSELLOR_AUDIT_STATUS:",
    counsellor_audit_status,
    "| EXPECTED_403:",
    counsellor_audit_status == 403,
)


# ------------------------------------------------------------
# NO TOKEN -> PROTECTED ENDPOINT
# Expected: 401 or 403
# ------------------------------------------------------------

no_token_status, _ = request(
    "GET",
    "/api/v1/counselling/referrals",
)

print(
    "NO_TOKEN_STATUS:",
    no_token_status,
    "| EXPECTED_401_OR_403:",
    no_token_status in (401, 403),
)


# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

all_passed = (
    student_status == 200
    and bool(student_token)
    and counsellor_status == 200
    and bool(counsellor_token)
    and invalid_status == 401
    and counsellor_referrals_status == 200
    and student_referrals_status == 403
    and counsellor_records_status == 200
    and student_records_status == 403
    and counsellor_audit_status == 403
    and no_token_status in (401, 403)
)


print("=" * 60)
print(
    "API_RBAC_REGRESSION_PASS:",
    all_passed,
)
print("=" * 60)