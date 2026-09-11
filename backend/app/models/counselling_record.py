from datetime import datetime

from pydantic import BaseModel, Field


class SessionStatus:
    ACTIVE = "active"
    COMPLETED = "completed"


class FollowUpStatus:
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    COMPLETED = "completed"


class CounsellingRecord(BaseModel):
    record_id: str
    referral_id: str
    student_id: str
    counsellor_id: str
    session_date: datetime

    session_summary: str = Field(
        ...,
        min_length=1,
    )

    follow_up_required: bool = False
    follow_up_date: datetime | None = None
    follow_up_status: str = FollowUpStatus.NOT_REQUIRED

    status: str = SessionStatus.ACTIVE
    created_at: datetime


class CreateCounsellingRecordRequest(BaseModel):
    counsellor_id: str
    session_date: datetime
    session_summary: str = Field(
        ...,
        min_length=1,
    )

    follow_up_required: bool = False
    follow_up_date: datetime | None = None