from fastapi import APIRouter, Depends, HTTPException


# ============================================================
# AGENT
# ============================================================

from app.agents.counselling_agent.agent import analyze_request

from app.agents.counselling_agent.schemas import (
    CounsellingRequest,
    CounsellingResponse,
)


# ============================================================
# AUTHENTICATION / RBAC
# ============================================================

from app.auth.security import (
    LoginRequest,
    TokenResponse,
    change_user_password,
    create_access_token,
    get_current_user,
    require_roles,
    verify_password,
    verify_student_access,
)


# ============================================================
# MODELS
# ============================================================

from app.models.referral import (
    AssignCounsellorRequest,
    Referral,
    ScheduleAppointmentRequest,
    UpdateReferralStatusRequest,
)

from app.models.counselling_record import (
    CounsellingRecord,
    CreateCounsellingRecordRequest,
)

from app.models.accommodation import (
    AcademicAccommodation,
    CreateAccommodationRequest,
    UpdateAccommodationStatusRequest,
)

from app.models.resource import (
    WellbeingResource,
    CreateResourceRequest,
)

from app.models.aggregate_report import (
    AggregateReport,
)

from app.models.registration import (
    ApproveRegistrationResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    RegistrationRequest,
    RejectRegistrationRequest,
    SignupRequest,
    SignupResponse,
)


# ============================================================
# SERVICES
# ============================================================

from app.services.referral import (
    assign_counsellor,
    create_referral,
    get_referral,
    get_referrals,
    update_referral_status,
)

from app.services.scheduling import (
    get_appointment,
    get_appointments,
    schedule_counselling_session,
)

from app.services.escalation import (
    create_crisis_escalation,
    get_escalations,
)

from app.services.counselling_record import (
    complete_counselling_record,
    create_counselling_record,
    get_counselling_record,
    get_counselling_records,
    get_follow_ups,
    get_due_follow_ups,
    complete_follow_up,
)

from app.services.accommodation import (
    create_accommodation,
    get_accommodation,
    get_accommodations,
    update_accommodation_status,
)

from app.services.resources import (
    create_resource,
    deactivate_resource,
    get_resource,
    get_resources,
    get_resources_by_type,
)

from app.services.aggregate_report import (
    generate_aggregate_report,
)

from app.services.audit import (
    create_audit_event,
    get_audit_log,
    get_audit_logs,
)

from app.services.registration import (
    approve_registration,
    create_registration_request,
    get_registration_request,
    list_registration_requests,
    reject_registration,
    resend_temporary_credentials,
)
from app.services.email import (
    email_configured,
    email_status,
    mask_email,
    notify_student_registration_approved,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/counselling",
    tags=["Agent 66 - Counselling Support"],
)


# ============================================================
# AUDIT HELPERS
# ============================================================

def _actor_id(current_user) -> str:
    """
    Extract the authenticated actor identifier.

    Supports both:
    - CurrentUser Pydantic objects
    - dictionaries used by login/system audit events
    """

    if isinstance(current_user, dict):
        return str(
            current_user.get(
                "username",
                current_user.get("user_id", "unknown"),
            )
        )

    username = getattr(
        current_user,
        "username",
        None,
    )

    if username is not None:
        return str(username)

    return str(current_user)


def _actor_role(current_user) -> str:
    """
    Extract the authenticated actor role.

    Supports both:
    - CurrentUser Pydantic objects
    - dictionaries used by login/system audit events
    """

    if isinstance(current_user, dict):
        return str(
            current_user.get(
                "role",
                "unknown",
            )
        )

    role = getattr(
        current_user,
        "role",
        None,
    )

    if role is not None:
        return str(role)

    return "unknown"


def _audit(
    current_user,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    outcome: str = "success",
    human_approved: bool | None = None,
):
    """
    Write a metadata-only audit event.

    Sensitive counselling content is deliberately never
    passed to this function.
    """

    try:
        return create_audit_event(
            actor_id=_actor_id(current_user),
            actor_role=_actor_role(current_user),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            human_approved=human_approved,
        )

    except Exception:
        # Audit failures must not expose sensitive information
        # or break the primary counselling workflow.
        #
        # Production deployment should additionally send
        # audit-write failures to a secure operational monitor.
        return None


# ============================================================
# 0. AUTHENTICATION
# ============================================================

@router.post(
    "/auth/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
):
    user = verify_password(
        username=request.username,
        password=request.password,
    )

    if user is None:
        _audit(
            {
                "username": request.username,
                "role": "unknown",
            },
            action="login_failed",
            resource_type="authentication",
            outcome="failure",
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        username=request.username,
        role=user["role"],
        student_id=user["student_id"],
        must_change_password=user["must_change_password"],
    )

    _audit(
        {
            "username": request.username,
            "role": user["role"],
        },
        action="login_success",
        resource_type="authentication",
        outcome="success",
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=request.username,
        role=user["role"],
        must_change_password=user["must_change_password"],
    )


@router.post(
    "/auth/signup",
    response_model=SignupResponse,
)
async def signup(
    request: SignupRequest,
):
    try:
        registration = create_registration_request(request)

    except ValueError as exc:
        _audit(
            {
                "username": request.username,
                "role": "anonymous",
            },
            action="signup_requested",
            resource_type="registration_request",
            outcome="failure",
        )
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    _audit(
        {
            "username": request.username,
            "role": "anonymous",
        },
        action="signup_requested",
        resource_type="registration_request",
        resource_id=registration.registration_id,
        outcome="success",
    )

    return SignupResponse(
        registration_id=registration.registration_id,
        status=registration.status,
        message=(
            "Registration submitted for administrator review. "
            "Your account will not be activated until approval."
        ),
    )


@router.post(
    "/auth/change-password",
    response_model=ChangePasswordResponse,
)
async def change_password(
    request: ChangePasswordRequest,
    current_user=Depends(get_current_user),
):
    if not request.acknowledge_permanent:
        raise HTTPException(
            status_code=400,
            detail=(
                "You must acknowledge that this password change "
                "is permanent before continuing."
            ),
        )

    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirmation do not match.",
        )

    try:
        updated = change_user_password(
            username=current_user.username,
            new_password=request.new_password,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="password_changed",
            resource_type="authentication",
            outcome="failure",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    token = create_access_token(
        username=updated["username"],
        role=updated["role"],
        student_id=updated["student_id"],
        must_change_password=False,
    )

    _audit(
        current_user,
        action="password_changed",
        resource_type="authentication",
        outcome="success",
        human_approved=True,
    )

    return ChangePasswordResponse(
        message=(
            "Your password has been changed successfully. "
            "This password cannot be changed again through the "
            "initial password-change workflow."
        ),
        access_token=token,
        token_type="bearer",
        username=updated["username"],
        role=updated["role"],
        must_change_password=False,
    )


@router.get(
    "/registrations",
    response_model=list[RegistrationRequest],
)
async def list_registrations(
    status: str | None = None,
    current_user=Depends(require_roles("admin")),
):
    registrations = list_registration_requests(status)

    _audit(
        current_user,
        action="registrations_list_accessed",
        resource_type="registration_request",
    )

    return registrations


@router.get(
    "/registrations/{registration_id}",
    response_model=RegistrationRequest,
)
async def retrieve_registration(
    registration_id: str,
    current_user=Depends(require_roles("admin")),
):
    registration = get_registration_request(registration_id)

    if registration is None:
        raise HTTPException(
            status_code=404,
            detail="Registration request not found",
        )

    _audit(
        current_user,
        action="registration_accessed",
        resource_type="registration_request",
        resource_id=registration_id,
    )

    return registration


@router.post(
    "/registrations/{registration_id}/approve",
    response_model=ApproveRegistrationResponse,
)
async def approve_registration_request(
    registration_id: str,
    current_user=Depends(require_roles("admin")),
):
    try:
        registration, temporary_password = approve_registration(
            registration_id=registration_id,
            reviewed_by=current_user.username,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="signup_approved",
            resource_type="registration_request",
            resource_id=registration_id,
            outcome="failure",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    email_sent = False
    email_reason = ""
    if temporary_password:
        email_sent, email_reason = notify_student_registration_approved(
            to_email=registration.email,
            username=registration.username,
            temporary_password=temporary_password,
        )

    _audit(
        current_user,
        action="signup_approved",
        resource_type="registration_request",
        resource_id=registration_id,
        outcome="success",
        human_approved=True,
    )

    _audit(
        current_user,
        action="temporary_credential_issued",
        resource_type="authentication",
        resource_id=registration.username,
        outcome="success" if (email_sent or temporary_password is None) else "failure",
        human_approved=True,
    )

    if temporary_password is None:
        message = (
            "Registration was already approved. "
            "If the student did not receive mail, use Resend temporary credentials."
        )
    elif email_sent:
        message = (
            "Registration accepted. Temporary credentials were emailed to "
            f"{mask_email(registration.email)}."
        )
    elif not email_configured():
        message = (
            "Registration accepted, but SMTP is not configured on the server. "
            "Set SMTP_* env vars on Render (use SMTP_PORT=465 for Gmail), "
            "then use Resend temporary credentials."
        )
    else:
        message = (
            "Registration accepted, but email delivery failed "
            f"({email_reason or 'unknown'}). "
            "Set SMTP_PORT=465 on Render and use Resend temporary credentials."
        )

    return ApproveRegistrationResponse(
        registration=registration,
        email_sent=email_sent,
        message=message,
    )


@router.post(
    "/registrations/{registration_id}/reject",
    response_model=RegistrationRequest,
)
async def reject_registration_request(
    registration_id: str,
    request: RejectRegistrationRequest | None = None,
    current_user=Depends(require_roles("admin")),
):
    try:
        registration = reject_registration(
            registration_id=registration_id,
            reviewed_by=current_user.username,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="signup_rejected",
            resource_type="registration_request",
            resource_id=registration_id,
            outcome="failure",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    _audit(
        current_user,
        action="signup_rejected",
        resource_type="registration_request",
        resource_id=registration_id,
        outcome="success",
        human_approved=True,
    )

    return registration


@router.post(
    "/registrations/{registration_id}/resend-credentials",
)
async def resend_registration_credentials(
    registration_id: str,
    current_user=Depends(require_roles("admin")),
):
    try:
        email_sent, detail = resend_temporary_credentials(
            registration_id
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="temporary_credential_issued",
            resource_type="registration_request",
            resource_id=registration_id,
            outcome="failure",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    _audit(
        current_user,
        action="temporary_credential_issued",
        resource_type="registration_request",
        resource_id=registration_id,
        outcome="success" if email_sent else "failure",
        human_approved=True,
    )

    registration = get_registration_request(registration_id)
    recipient = registration.email if registration else ""

    return {
        "registration_id": registration_id,
        "email_sent": email_sent,
        "recipient_masked": mask_email(recipient) if recipient else None,
        "message": detail,
    }


@router.get("/system/email-status")
async def get_email_status(
    current_user=Depends(require_roles("admin")),
):
    """Admin-only SMTP configuration check (no secrets returned)."""

    _audit(
        current_user,
        action="email_status_checked",
        resource_type="system",
        outcome="success",
    )
    return email_status()


@router.post("/system/reset-default-users")
async def reset_default_users(
    current_user=Depends(require_roles("admin")),
):
    """
    Admin-only cleanup:
    - delete all signup/approval registration requests
    - delete every user except the eight default accounts
    - remove operational rows for non-default student IDs
    """

    from app.services.bootstrap import reset_to_default_accounts

    result = reset_to_default_accounts()

    _audit(
        current_user,
        action="reset_default_users",
        resource_type="system",
        outcome="success",
        human_approved=True,
    )

    return {
        "message": (
            "Signup/approval registrations cleared. "
            "Only default accounts remain."
        ),
        **result,
    }


# ============================================================
# 1. COUNSELLING REQUEST ANALYSIS
# ============================================================

@router.post(
    "/analyze",
    response_model=CounsellingResponse,
)
async def analyze_counselling_request(
    request: CounsellingRequest,
):
    result = analyze_request(request)

    # Crisis cases must NOT enter the normal referral queue.
    if result.immediate_escalation:
        escalation = create_crisis_escalation(
            student_id=request.student_id,
            reason=result.reason,
        )

        _audit(
            {
                "username": "system",
                "role": "system",
            },
            action="crisis_escalation_created",
            resource_type="crisis_escalation",
            resource_id=escalation.escalation_id,
            outcome="success",
            human_approved=False,
        )

        return result

    # Create referral for support/urgent cases.
    if result.route_to_human:
        referral = create_referral(
            request=request,
            urgency=result.urgency,
        )

        _audit(
            {
                "username": "system",
                "role": "system",
            },
            action="referral_created",
            resource_type="referral",
            resource_id=referral.referral_id,
            outcome="success",
            human_approved=False,
        )

    return result


# ============================================================
# 2. REFERRAL QUEUE
# ============================================================

@router.get(
    "/referrals",
    response_model=list[Referral],
)
async def list_referrals(
    current_user=Depends(
        require_roles(
            "counsellor",
            "mentor",
            "faculty",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    referrals = get_referrals()

    _audit(
        current_user,
        action="referrals_list_accessed",
        resource_type="referral_queue",
    )

    return referrals


@router.get(
    "/referrals/{referral_id}",
    response_model=Referral,
)
async def retrieve_referral(
    referral_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
            "mentor",
            "faculty",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    referral = get_referral(referral_id)

    if referral is None:
        _audit(
            current_user,
            action="referral_access_failed",
            resource_type="referral",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Referral not found",
        )

    _audit(
        current_user,
        action="referral_accessed",
        resource_type="referral",
        resource_id=referral_id,
    )

    return referral


# ============================================================
# 3. COUNSELLOR ASSIGNMENT
# ============================================================

@router.patch(
    "/referrals/{referral_id}/assign",
    response_model=Referral,
)
async def assign_referral(
    referral_id: str,
    request: AssignCounsellorRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    referral = assign_counsellor(
        referral_id=referral_id,
        counsellor_id=request.counsellor_id,
    )

    if referral is None:
        _audit(
            current_user,
            action="counsellor_assignment_failed",
            resource_type="referral",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Referral not found",
        )

    _audit(
        current_user,
        action="counsellor_assigned",
        resource_type="referral",
        resource_id=referral_id,
        human_approved=True,
    )

    return referral


# ============================================================
# 4. REFERRAL STATUS
# ============================================================

@router.patch(
    "/referrals/{referral_id}/status",
    response_model=Referral,
)
async def change_referral_status(
    referral_id: str,
    request: UpdateReferralStatusRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    try:
        referral = update_referral_status(
            referral_id=referral_id,
            new_status=request.status,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="referral_status_change_failed",
            resource_type="referral",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if referral is None:
        _audit(
            current_user,
            action="referral_status_change_failed",
            resource_type="referral",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Referral not found",
        )

    _audit(
        current_user,
        action="referral_status_changed",
        resource_type="referral",
        resource_id=referral_id,
        human_approved=True,
    )

    return referral


# ============================================================
# 5. CRISIS ESCALATION
# ============================================================

@router.get(
    "/escalations",
)
async def list_escalations(
    current_user=Depends(
        require_roles(
            "counsellor",
            "dean",
            "admin",
        )
    ),
):
    escalations = get_escalations()

    _audit(
        current_user,
        action="crisis_escalations_accessed",
        resource_type="crisis_escalation_queue",
    )

    return escalations


# ============================================================
# 6. APPOINTMENT SCHEDULING
# ============================================================

@router.post(
    "/referrals/{referral_id}/schedule",
)
async def schedule_referral(
    referral_id: str,
    request: ScheduleAppointmentRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    try:
        appointment = schedule_counselling_session(
            referral_id=referral_id,
            counsellor_id=request.counsellor_id,
            appointment_time=request.appointment_time,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="appointment_creation_failed",
            resource_type="appointment",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    _audit(
        current_user,
        action="appointment_created",
        resource_type="appointment",
        resource_id=appointment["appointment_id"],
        human_approved=True,
    )

    return appointment


@router.get(
    "/appointments",
)
async def list_appointments(
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    appointments = get_appointments()

    _audit(
        current_user,
        action="appointments_list_accessed",
        resource_type="appointment_queue",
    )

    return appointments


@router.get(
    "/appointments/{appointment_id}",
)
async def retrieve_appointment(
    appointment_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    appointment = get_appointment(appointment_id)

    if appointment is None:
        _audit(
            current_user,
            action="appointment_access_failed",
            resource_type="appointment",
            resource_id=appointment_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    _audit(
        current_user,
        action="appointment_accessed",
        resource_type="appointment",
        resource_id=appointment_id,
    )

    return appointment


# ============================================================
# 7. RESTRICTED COUNSELLING RECORDS
# ============================================================

@router.post(
    "/referrals/{referral_id}/records",
    response_model=CounsellingRecord,
)
async def create_session_record(
    referral_id: str,
    request: CreateCounsellingRecordRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    try:
        record = create_counselling_record(
            referral_id=referral_id,
            counsellor_id=request.counsellor_id,
            session_date=request.session_date,
            session_summary=request.session_summary,
            follow_up_required=request.follow_up_required,
            follow_up_date=request.follow_up_date,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="counselling_record_creation_failed",
            resource_type="counselling_record",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # NEVER place session_summary or clinical information
    # inside an audit event.
    _audit(
        current_user,
        action="counselling_record_created",
        resource_type="counselling_record",
        resource_id=record.record_id,
        human_approved=True,
    )

    return record


@router.get(
    "/records",
    response_model=list[CounsellingRecord],
)
async def list_counselling_records(
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    """
    Return counselling records only to professional counsellors.

    Students must never receive the complete counselling-record
    collection because that would expose other students'
    restricted records.
    """

    records = get_counselling_records()

    _audit(
        current_user,
        action="counselling_records_list_accessed",
        resource_type="counselling_record",
    )

    return records


@router.get(
    "/records/{record_id}",
    response_model=CounsellingRecord,
)
async def retrieve_counselling_record(
    record_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
            "student",
        )
    ),
):
    record = get_counselling_record(record_id)

    if record is None:
        _audit(
            current_user,
            action="counselling_record_access_failed",
            resource_type="counselling_record",
            resource_id=record_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Counselling record not found",
        )

    # Students may access only their own counselling record.
    if current_user.role == "student":
        verify_student_access(
            record.student_id,
            current_user,
        )

    _audit(
        current_user,
        action="counselling_record_accessed",
        resource_type="counselling_record",
        resource_id=record_id,
    )

    return record


@router.patch(
    "/records/{record_id}/complete",
    response_model=CounsellingRecord,
)
async def complete_session_record(
    record_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    record = complete_counselling_record(record_id)

    if record is None:
        _audit(
            current_user,
            action="counselling_record_completion_failed",
            resource_type="counselling_record",
            resource_id=record_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Counselling record not found",
        )

    _audit(
        current_user,
        action="counselling_record_completed",
        resource_type="counselling_record",
        resource_id=record_id,
        human_approved=True,
    )

    return record


# ============================================================
# 8. FOLLOW-UP TRACKING
# ============================================================

@router.get(
    "/follow-ups",
    response_model=list[CounsellingRecord],
)
async def list_follow_ups(
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    follow_ups = get_follow_ups()

    _audit(
        current_user,
        action="follow_ups_accessed",
        resource_type="follow_up_queue",
    )

    return follow_ups


@router.get(
    "/follow-ups/due",
    response_model=list[CounsellingRecord],
)
async def list_due_follow_ups(
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    due_follow_ups = get_due_follow_ups()

    _audit(
        current_user,
        action="due_follow_ups_accessed",
        resource_type="follow_up_queue",
    )

    return due_follow_ups


@router.patch(
    "/follow-ups/{record_id}/complete",
    response_model=CounsellingRecord,
)
async def complete_follow_up_record(
    record_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
        )
    ),
):
    try:
        record = complete_follow_up(record_id)

    except ValueError as exc:
        _audit(
            current_user,
            action="follow_up_completion_failed",
            resource_type="follow_up",
            resource_id=record_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if record is None:
        _audit(
            current_user,
            action="follow_up_completion_failed",
            resource_type="follow_up",
            resource_id=record_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Counselling record not found",
        )

    _audit(
        current_user,
        action="follow_up_completed",
        resource_type="follow_up",
        resource_id=record_id,
        human_approved=True,
    )

    return record


# ============================================================
# 9. ACADEMIC ACCOMMODATION COORDINATION
# ============================================================

@router.post(
    "/referrals/{referral_id}/accommodations",
    response_model=AcademicAccommodation,
)
async def create_academic_accommodation(
    referral_id: str,
    request: CreateAccommodationRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    try:
        accommodation = create_accommodation(
            referral_id=referral_id,
            accommodation_type=request.accommodation_type,
            academic_contact=request.academic_contact,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="accommodation_creation_failed",
            resource_type="academic_accommodation",
            resource_id=referral_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    _audit(
        current_user,
        action="accommodation_created",
        resource_type="academic_accommodation",
        resource_id=accommodation.accommodation_id,
        human_approved=True,
    )

    return accommodation


@router.get(
    "/accommodations",
    response_model=list[AcademicAccommodation],
)
async def list_academic_accommodations(
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    accommodations = get_accommodations()

    _audit(
        current_user,
        action="accommodations_list_accessed",
        resource_type="academic_accommodation",
    )

    return accommodations


@router.get(
    "/accommodations/{accommodation_id}",
    response_model=AcademicAccommodation,
)
async def retrieve_academic_accommodation(
    accommodation_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    accommodation = get_accommodation(
        accommodation_id
    )

    if accommodation is None:
        _audit(
            current_user,
            action="accommodation_access_failed",
            resource_type="academic_accommodation",
            resource_id=accommodation_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Academic accommodation not found",
        )

    _audit(
        current_user,
        action="accommodation_accessed",
        resource_type="academic_accommodation",
        resource_id=accommodation_id,
    )

    return accommodation


@router.patch(
    "/accommodations/{accommodation_id}/status",
    response_model=AcademicAccommodation,
)
async def change_accommodation_status(
    accommodation_id: str,
    request: UpdateAccommodationStatusRequest,
    current_user=Depends(
        require_roles(
            "hod",
            "dean",
            "admin",
        )
    ),
):
    try:
        accommodation = update_accommodation_status(
            accommodation_id=accommodation_id,
            new_status=request.status,
        )

    except ValueError as exc:
        _audit(
            current_user,
            action="accommodation_status_change_failed",
            resource_type="academic_accommodation",
            resource_id=accommodation_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if accommodation is None:
        _audit(
            current_user,
            action="accommodation_status_change_failed",
            resource_type="academic_accommodation",
            resource_id=accommodation_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Academic accommodation not found",
        )

    _audit(
        current_user,
        action="accommodation_status_changed",
        resource_type="academic_accommodation",
        resource_id=accommodation_id,
        human_approved=True,
    )

    return accommodation


# ============================================================
# 10. WELLBEING RESOURCE DIRECTORY
# ============================================================

@router.get(
    "/resources",
    response_model=list[WellbeingResource],
)
async def list_wellbeing_resources(
    current_user=Depends(
        require_roles(
            "student",
            "counsellor",
            "mentor",
            "faculty",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    resources = get_resources()

    _audit(
        current_user,
        action="resources_list_accessed",
        resource_type="wellbeing_resource",
    )

    return resources


@router.get(
    "/resources/type/{resource_type}",
    response_model=list[WellbeingResource],
)
async def list_resources_by_type(
    resource_type: str,
    current_user=Depends(
        require_roles(
            "student",
            "counsellor",
            "mentor",
            "faculty",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    resources = get_resources_by_type(resource_type)

    _audit(
        current_user,
        action="resources_by_type_accessed",
        resource_type="wellbeing_resource",
    )

    return resources


@router.get(
    "/resources/{resource_id}",
    response_model=WellbeingResource,
)
async def retrieve_wellbeing_resource(
    resource_id: str,
    current_user=Depends(
        require_roles(
            "student",
            "counsellor",
            "mentor",
            "faculty",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    resource = get_resource(resource_id)

    if resource is None or not resource.active:
        _audit(
            current_user,
            action="resource_access_failed",
            resource_type="wellbeing_resource",
            resource_id=resource_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Wellbeing resource not found",
        )

    _audit(
        current_user,
        action="resource_accessed",
        resource_type="wellbeing_resource",
        resource_id=resource_id,
    )

    return resource


@router.post(
    "/resources",
    response_model=WellbeingResource,
)
async def add_wellbeing_resource(
    request: CreateResourceRequest,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    resource = create_resource(request)

    _audit(
        current_user,
        action="resource_created",
        resource_type="wellbeing_resource",
        resource_id=resource.resource_id,
        human_approved=True,
    )

    return resource


@router.patch(
    "/resources/{resource_id}/deactivate",
    response_model=WellbeingResource,
)
async def deactivate_wellbeing_resource(
    resource_id: str,
    current_user=Depends(
        require_roles(
            "counsellor",
            "hod",
            "dean",
            "admin",
        )
    ),
):
    resource = deactivate_resource(resource_id)

    if resource is None:
        _audit(
            current_user,
            action="resource_deactivation_failed",
            resource_type="wellbeing_resource",
            resource_id=resource_id,
            outcome="failure",
        )

        raise HTTPException(
            status_code=404,
            detail="Wellbeing resource not found",
        )

    _audit(
        current_user,
        action="resource_deactivated",
        resource_type="wellbeing_resource",
        resource_id=resource_id,
        human_approved=True,
    )

    return resource


# ============================================================
# 11. ANONYMOUS AGGREGATE REPORTING
# ============================================================

@router.get(
    "/reports/aggregate",
    response_model=AggregateReport,
)
async def get_anonymous_aggregate_report(
    current_user=Depends(
        require_roles(
            "hod",
            "dean",
            "admin",
        )
    ),
):
    report = generate_aggregate_report()

    _audit(
        current_user,
        action="aggregate_report_accessed",
        resource_type="aggregate_report",
    )

    return report


# ============================================================
# 12. AUDIT LOGGING
# ============================================================

@router.get(
    "/audit-logs",
)
async def list_audit_logs(
    limit: int = 100,
    current_user=Depends(
        require_roles(
            "hod",
            "dean",
            "admin",
        )
    ),
):
    logs = get_audit_logs(limit)

    return logs


@router.get(
    "/audit-logs/{audit_id}",
)
async def retrieve_audit_log(
    audit_id: str,
    current_user=Depends(
        require_roles(
            "hod",
            "dean",
            "admin",
        )
    ),
):
    log = get_audit_log(audit_id)

    if log is None:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found",
        )

    return log