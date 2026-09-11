from datetime import datetime
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator


class RegistrationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
)


class SignupRequest(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=120)
    student_id: str = Field(..., min_length=2, max_length=64)
    email: str = Field(..., min_length=5, max_length=254)
    username: str = Field(..., min_length=3, max_length=64)
    branch: str = Field(..., min_length=2, max_length=120)
    year: str = Field(..., min_length=1, max_length=32)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise ValueError("A valid institutional email address is required.")
        return normalized

    @field_validator("username", "student_id")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.strip()

    @field_validator("student_name", "branch", "year")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.strip().split())



class SignupResponse(BaseModel):
    registration_id: str
    status: RegistrationStatus
    message: str


class RegistrationRequest(BaseModel):
    registration_id: str
    student_name: str
    student_id: str
    email: str
    username: str
    branch: str
    year: str
    status: RegistrationStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: str | None = None


class RejectRegistrationRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=10, max_length=128)
    confirm_password: str = Field(..., min_length=10, max_length=128)
    acknowledge_permanent: bool = False


class ChangePasswordResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    username: str
    role: str
    must_change_password: bool = False
