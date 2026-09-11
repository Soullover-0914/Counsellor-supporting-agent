from enum import Enum

from pydantic import BaseModel, Field


class ReferralSource(str, Enum):
    SELF_REFERRAL = "self_referral"
    MENTOR_REFERRAL = "mentor_referral"
    FACULTY_REFERRAL = "faculty_referral"


class UrgencyLevel(str, Enum):
    NORMAL = "normal"
    SUPPORT = "support"
    URGENT = "urgent"
    CRISIS = "crisis"


class CounsellingRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    source: ReferralSource
    message: str = Field(..., min_length=1)
    consent: bool = False


class CrisisResource(BaseModel):
    """
    Approved emergency/support contact surfaced during
    a crisis response.

    Only approved resource-directory information should
    be placed in this structure.
    """

    resource_id: str
    name: str
    contact: str | None = None
    availability: str | None = None
    location: str | None = None


class CounsellingResponse(BaseModel):
    status: str
    urgency: UrgencyLevel
    route_to_human: bool
    immediate_escalation: bool
    reason: str
    recommended_action: str
    crisis_resources: list[CrisisResource] | None = None