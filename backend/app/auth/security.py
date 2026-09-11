import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings
from app.database.db import get_connection


TOKEN_EXPIRY_SECONDS = settings.token_expiry_seconds

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 200_000


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "your_username",
                "password": "your_password",
            }
        }
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    must_change_password: bool = False


class CurrentUser(BaseModel):
    username: str
    role: str
    student_id: str | None = None
    must_change_password: bool = False


def validate_password_policy(password: str) -> None:
    """
    Enforce the institutional password policy.

    Requirements:
    - at least 10 characters
    - at least one uppercase letter
    - at least one lowercase letter
    - at least one digit
    """

    if len(password) < 10:
        raise ValueError(
            "Password must be at least 10 characters long."
        )

    if not any(char.isupper() for char in password):
        raise ValueError(
            "Password must include at least one uppercase letter."
        )

    if not any(char.islower() for char in password):
        raise ValueError(
            "Password must include at least one lowercase letter."
        )

    if not any(char.isdigit() for char in password):
        raise ValueError(
            "Password must include at least one digit."
        )


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.
    """

    validate_password_policy(password)
    return hash_password_material(password)


def hash_password_material(password: str) -> str:
    """
    Hash password bytes without enforcing the interactive policy.

    Used for bootstrap/seed of established demo accounts only.
    """

    salt = base64.urlsafe_b64encode(
        secrets.token_bytes(16)
    ).decode("ascii")

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.urlsafe_b64decode(salt.encode("ascii")),
        PASSWORD_HASH_ITERATIONS,
    )

    derived_encoded = base64.urlsafe_b64encode(
        derived
    ).decode("ascii")

    return (
        f"{PASSWORD_HASH_ALGORITHM}$"
        f"{PASSWORD_HASH_ITERATIONS}$"
        f"{salt}$"
        f"{derived_encoded}"
    )


def _get_secret_key() -> str:
    """
    Return the authentication signing secret.

    The secret must be supplied through application
    configuration and must not be hardcoded in source code.
    """

    secret_key = settings.auth_secret_key

    if not secret_key:
        raise RuntimeError(
            "AUTH_SECRET_KEY is not configured. "
            "Set it in the environment or .env file."
        )

    return secret_key


def _verify_password_hash(
    password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against a PBKDF2-HMAC-SHA256 hash.

    Stored format:

        pbkdf2_sha256$iterations$salt$derived_key
    """

    try:
        (
            algorithm,
            iterations_text,
            salt_encoded,
            hash_encoded,
        ) = stored_hash.split("$")

        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False

        iterations = int(iterations_text)

        if iterations <= 0:
            return False

        salt = base64.urlsafe_b64decode(
            salt_encoded.encode("ascii")
        )

        expected_hash = base64.urlsafe_b64decode(
            hash_encoded.encode("ascii")
        )

        derived_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            derived_hash,
            expected_hash,
        )

    except (
        ValueError,
        TypeError,
        UnicodeError,
    ):
        return False


def verify_password(
    username: str,
    password: str,
) -> dict | None:
    """
    Authenticate a user against the encrypted database.

    Only active users can authenticate.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                username,
                password_hash,
                role,
                student_id,
                active,
                temporary_password,
                password_changed_once
            FROM users
            WHERE username = ?
            """,
            (username,),
        )

        row = cursor.fetchone()

    finally:
        connection.close()

    if row is None:
        return None

    if not bool(row["active"]):
        return None

    if not _verify_password_hash(
        password,
        row["password_hash"],
    ):
        return None

    temporary_password = bool(row["temporary_password"])
    password_changed_once = bool(row["password_changed_once"])
    must_change_password = (
        temporary_password and not password_changed_once
    )

    return {
        "username": row["username"],
        "password_hash": row["password_hash"],
        "role": row["role"],
        "student_id": row["student_id"],
        "temporary_password": temporary_password,
        "password_changed_once": password_changed_once,
        "must_change_password": must_change_password,
    }


def create_access_token(
    username: str,
    role: str,
    student_id: str | None = None,
    must_change_password: bool = False,
) -> str:
    """
    Create an HMAC-SHA256 signed access token.
    """

    payload = {
        "username": username,
        "role": role,
        "student_id": student_id,
        "must_change_password": must_change_password,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }

    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    payload_encoded = base64.urlsafe_b64encode(
        payload_bytes
    ).decode("utf-8")

    signature = hmac.new(
        _get_secret_key().encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_encoded}.{signature}"


def decode_access_token(
    token: str,
) -> CurrentUser:
    """
    Validate an access token and return the authenticated user.
    """

    try:
        if not token:
            raise ValueError("Empty token")

        parts = token.split(".")

        if len(parts) != 2:
            raise ValueError(
                "Invalid token structure"
            )

        payload_encoded = parts[0]
        signature = parts[1]

        if not payload_encoded or not signature:
            raise ValueError(
                "Missing token components"
            )

        expected_signature = hmac.new(
            _get_secret_key().encode("utf-8"),
            payload_encoded.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            raise ValueError(
                "Invalid token signature"
            )

        payload_bytes = base64.urlsafe_b64decode(
            payload_encoded.encode("utf-8")
        )

        payload = json.loads(
            payload_bytes.decode("utf-8")
        )

        username = payload.get("username")
        role = payload.get("role")
        student_id = payload.get("student_id")
        exp = payload.get("exp")

        if not username:
            raise ValueError(
                "Username missing"
            )

        if not role:
            raise ValueError(
                "Role missing"
            )

        if exp is None:
            raise ValueError(
                "Expiration missing"
            )

        if int(exp) <= int(time.time()):
            raise ValueError(
                "Token expired"
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    username,
                    role,
                    student_id,
                    active,
                    temporary_password,
                    password_changed_once
                FROM users
                WHERE username = ?
                """,
                (username,),
            )

            user = cursor.fetchone()

        finally:
            connection.close()

        if user is None:
            raise ValueError(
                "User does not exist"
            )

        if not bool(user["active"]):
            raise ValueError(
                "User account is inactive"
            )

        if user["role"] != role:
            raise ValueError(
                "Invalid user role"
            )

        if user["student_id"] != student_id:
            raise ValueError(
                "Invalid student identity"
            )

        must_change_password = bool(
            user["temporary_password"]
        ) and not bool(
            user["password_changed_once"]
        )

        return CurrentUser(
            username=username,
            role=role,
            student_id=student_id,
            must_change_password=must_change_password,
        )

    except Exception as exc:
        print(
            f"[AUTH ERROR] "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
) -> CurrentUser:

    return decode_access_token(
        credentials.credentials
    )


def require_roles(*allowed_roles: str):

    def role_checker(
        current_user: CurrentUser = Depends(
            get_current_user
        ),
    ) -> CurrentUser:

        if current_user.must_change_password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You must complete the one-time password "
                    "change before accessing this resource."
                ),
            )

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to access this resource."
                ),
            )

        return current_user

    return role_checker


def change_user_password(
    username: str,
    new_password: str,
) -> dict:
    """
    Complete the one-time temporary password change.

    Backend-enforced lifecycle:
    temporary_password → first change → permanently locked.
    """

    validate_password_policy(new_password)

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                username,
                role,
                student_id,
                temporary_password,
                password_changed_once,
                active
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        user = cursor.fetchone()

        if user is None or not bool(user["active"]):
            raise ValueError("User account was not found.")

        if bool(user["password_changed_once"]):
            raise ValueError(
                "Your password has already been changed and "
                "cannot be changed again through this workflow."
            )

        if not bool(user["temporary_password"]):
            raise ValueError(
                "Password change through this workflow is only "
                "available for temporary credentials."
            )

        new_hash = hash_password(new_password)

        cursor.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                temporary_password = 0,
                password_changed_once = 1
            WHERE username = ?
            """,
            (new_hash, username),
        )
        connection.commit()

        return {
            "username": user["username"],
            "role": user["role"],
            "student_id": user["student_id"],
            "must_change_password": False,
        }

    finally:
        connection.close()


def verify_student_access(
    student_id: str,
    current_user: CurrentUser,
) -> None:

    if current_user.role == "student":

        if current_user.student_id != student_id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Students can access only "
                    "their own counselling information."
                ),
            )