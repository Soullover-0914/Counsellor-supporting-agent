from datetime import date, datetime

from pydantic import BaseModel, Field


class AccommodationStatus:
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class AcademicAccommodation(BaseModel):
    accommodation_id: str
    referral_id: str
    student_id: str

    accommodation_type: str = Field(
        ...,
        min_length=1,
    )

    academic_contact: str = Field(
        ...,
        min_length=1,
    )

    start_date: date | None = None
    end_date: date | None = None

    status: str = AccommodationStatus.REQUESTED

    created_at: datetime


class CreateAccommodationRequest(BaseModel):
    accommodation_type: str = Field(
        ...,
        min_length=1,
    )

    academic_contact: str = Field(
        ...,
        min_length=1,
    )

    start_date: date | None = None
    end_date: date | None = None


class UpdateAccommodationStatusRequest(BaseModel):
    status: str