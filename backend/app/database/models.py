from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


# ============================================================
# REFERRAL TABLE
# ============================================================

class ReferralDB(Base):

    __tablename__ = "referrals"

    referral_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    student_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    urgency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    assigned_counsellor: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


# ============================================================
# RESTRICTED COUNSELLING RECORD TABLE
# ============================================================

class CounsellingRecordDB(Base):

    __tablename__ = "counselling_records"

    record_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    referral_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    student_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    counsellor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    session_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    session_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    follow_up_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    follow_up_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


# ============================================================
# APPOINTMENT TABLE
# ============================================================

class AppointmentDB(Base):

    __tablename__ = "appointments"

    appointment_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    referral_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    student_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    counsellor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    appointment_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="scheduled",
    )


# ============================================================
# ACADEMIC ACCOMMODATION TABLE
# ============================================================

class AccommodationDB(Base):

    __tablename__ = "accommodations"

    accommodation_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    referral_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    student_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    accommodation_type: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    academic_contact: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    start_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    end_date: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="requested",
    )