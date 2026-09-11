from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.agents.counselling_agent.schemas import UrgencyLevel


class ReferralStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Referral(BaseModel):
    referral_id: str
    student_id: str
    source: str
    urgency: UrgencyLevel
    status: ReferralStatus = ReferralStatus.PENDING
    assigned_counsellor: str | None = None
    created_at: datetime


class AssignCounsellorRequest(BaseModel):
    counsellor_id: str


class UpdateReferralStatusRequest(BaseModel):
    status: ReferralStatus


class ScheduleAppointmentRequest(BaseModel):
    counsellor_id: str
    appointment_time: datetime