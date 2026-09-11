from app.agents.counselling_agent.schemas import (
    CounsellingRequest,
    CounsellingResponse,
    CrisisResource,
    UrgencyLevel,
)
from app.safety.crisis import detect_crisis
from app.services.resources import get_resources_by_type
from app.services.triage import determine_urgency


def _get_crisis_resources() -> list[CrisisResource]:
    """
    Return active institution-approved emergency resources.

    Crisis responses must surface approved contact information
    rather than inventing or generating emergency contacts.
    """

    resources = get_resources_by_type("emergency")

    return [
        CrisisResource(
            resource_id=resource.resource_id,
            name=resource.name,
            contact=resource.contact,
            availability=resource.availability,
            location=resource.location,
        )
        for resource in resources
        if resource.active and resource.emergency
    ]


def analyze_request(
    request: CounsellingRequest,
) -> CounsellingResponse:

    # ========================================================
    # 1. CRISIS CHECK — HIGHEST PRIORITY
    # ========================================================
    #
    # Crisis detection MUST happen before consent checking.
    #
    # Any indication of self-harm, suicidal ideation, or
    # immediate safety risk bypasses normal workflow gates.
    # ========================================================

    if detect_crisis(request.message):

        crisis_resources = _get_crisis_resources()

        return CounsellingResponse(
            status="immediate_escalation",
            urgency=UrgencyLevel.CRISIS,
            route_to_human=True,
            immediate_escalation=True,
            reason=(
                "The message contains an indication of possible "
                "immediate safety risk."
            ),
            recommended_action=(
                "Immediately escalate to the designated human authority "
                "and use the approved crisis support contacts provided."
            ),
            crisis_resources=crisis_resources,
        )

    # ========================================================
    # 2. CONSENT CHECK
    # ========================================================
    #
    # Consent is required for normal counselling referral
    # workflows.
    #
    # Crisis cases have already been handled above.
    # ========================================================

    if not request.consent:
        return CounsellingResponse(
            status="consent_required",
            urgency=UrgencyLevel.NORMAL,
            route_to_human=False,
            immediate_escalation=False,
            reason=(
                "Student consent is required before creating "
                "a counselling referral."
            ),
            recommended_action="Request consent from the student.",
            crisis_resources=None,
        )

    # ========================================================
    # 3. NORMAL TRIAGE
    # ========================================================

    urgency = determine_urgency(request.message)

    if urgency == UrgencyLevel.URGENT:
        return CounsellingResponse(
            status="urgent_support",
            urgency=UrgencyLevel.URGENT,
            route_to_human=True,
            immediate_escalation=False,
            reason=(
                "The message contains indicators that may require "
                "prompt professional support."
            ),
            recommended_action=(
                "Route the referral promptly to a professional counsellor."
            ),
            crisis_resources=None,
        )

    if urgency == UrgencyLevel.SUPPORT:
        return CounsellingResponse(
            status="support_recommended",
            urgency=UrgencyLevel.SUPPORT,
            route_to_human=True,
            immediate_escalation=False,
            reason=(
                "The message suggests that professional support "
                "may be beneficial."
            ),
            recommended_action=(
                "Offer and route the student to professional "
                "counselling support."
            ),
            crisis_resources=None,
        )

    return CounsellingResponse(
        status="no_immediate_concern",
        urgency=UrgencyLevel.NORMAL,
        route_to_human=False,
        immediate_escalation=False,
        reason=(
            "No immediate support indicator was detected in "
            "the submitted message."
        ),
        recommended_action=(
            "Provide access to wellbeing resources if requested."
        ),
        crisis_resources=None,
    )