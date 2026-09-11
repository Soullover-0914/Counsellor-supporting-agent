from app.agents.counselling_agent.agent import analyze_request
from app.agents.counselling_agent.schemas import CounsellingRequest


print("=" * 60)
print("PHASE 19.4.7 CRISIS SAFETY VALIDATION")
print("=" * 60)


# ============================================================
# TEST 1 — NORMAL REQUEST
# ============================================================

normal_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I am having difficulty managing my academic schedule "
        "and would like support."
    ),
    consent=True,
)

normal_result = analyze_request(normal_request)

print(
    "NORMAL_STATUS:",
    normal_result.status,
)

print(
    "NORMAL_URGENCY:",
    normal_result.urgency,
)

print(
    "NORMAL_ROUTE_TO_HUMAN:",
    normal_result.route_to_human,
)

print(
    "NORMAL_IMMEDIATE_ESCALATION:",
    normal_result.immediate_escalation,
)


# ============================================================
# TEST 2 — CRISIS REQUEST WITH CONSENT
# ============================================================

crisis_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I am thinking about hurting myself and I do not "
        "feel safe right now."
    ),
    consent=True,
)

crisis_result = analyze_request(crisis_request)

print(
    "CRISIS_STATUS:",
    crisis_result.status,
)

print(
    "CRISIS_URGENCY:",
    crisis_result.urgency,
)

print(
    "CRISIS_ROUTE_TO_HUMAN:",
    crisis_result.route_to_human,
)

print(
    "CRISIS_IMMEDIATE_ESCALATION:",
    crisis_result.immediate_escalation,
)

print(
    "CRISIS_RESOURCE_COUNT:",
    len(crisis_result.crisis_resources or []),
)


# ============================================================
# TEST 3 — CRISIS WITHOUT CONSENT
# ============================================================

crisis_no_consent_request = CounsellingRequest(
    student_id="STU001",
    source="self_referral",
    message=(
        "I may hurt myself and I am not safe."
    ),
    consent=False,
)

crisis_no_consent_result = analyze_request(
    crisis_no_consent_request
)

print(
    "CRISIS_NO_CONSENT_STATUS:",
    crisis_no_consent_result.status,
)

print(
    "CRISIS_NO_CONSENT_ROUTE_TO_HUMAN:",
    crisis_no_consent_result.route_to_human,
)

print(
    "CRISIS_NO_CONSENT_IMMEDIATE_ESCALATION:",
    crisis_no_consent_result.immediate_escalation,
)


# ============================================================
# TEST 4 — VERIFY EMERGENCY RESOURCE
# ============================================================

emergency_resource_valid = False

for resource in crisis_result.crisis_resources or []:

    if (
        getattr(resource, "resource_id", None)
        and getattr(resource, "name", None)
        and getattr(resource, "contact", None)
    ):
        emergency_resource_valid = True

        print(
            "EMERGENCY_RESOURCE:",
            resource.resource_id,
            "|",
            resource.name,
            "| CONTACT_PRESENT:",
            bool(resource.contact),
        )


print(
    "APPROVED_EMERGENCY_RESOURCE_PRESENT:",
    emergency_resource_valid,
)


# ============================================================
# TEST 5 — VERIFY CRISIS BYPASSES CONSENT
# ============================================================

crisis_bypasses_consent = (
    crisis_no_consent_result.status
    == "immediate_escalation"
    and crisis_no_consent_result.route_to_human
    and crisis_no_consent_result.immediate_escalation
)


print(
    "CRISIS_BYPASSES_CONSENT:",
    crisis_bypasses_consent,
)


# ============================================================
# FINAL RESULT
# ============================================================

all_passed = (
    normal_result.status == "no_immediate_concern"
    and normal_result.route_to_human is False
    and normal_result.immediate_escalation is False
    and crisis_result.status == "immediate_escalation"
    and crisis_result.route_to_human is True
    and crisis_result.immediate_escalation is True
    and len(crisis_result.crisis_resources or []) > 0
    and crisis_no_consent_result.status
    == "immediate_escalation"
    and crisis_no_consent_result.route_to_human is True
    and crisis_no_consent_result.immediate_escalation is True
    and emergency_resource_valid
    and crisis_bypasses_consent
)


print("=" * 60)
print(
    "CRISIS_SAFETY_VALIDATION_PASS:",
    all_passed,
)
print("=" * 60)