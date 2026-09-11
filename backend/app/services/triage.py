from app.agents.counselling_agent.schemas import UrgencyLevel


URGENT_INDICATORS = [
    "panic",
    "overwhelmed",
    "cannot cope",
    "can't cope",
    "unable to cope",
    "severe stress",
    "extreme stress",
    "not sleeping",
    "unable to sleep",
]


SUPPORT_INDICATORS = [
    "stressed",
    "stress",
    "anxious",
    "anxiety",
    "worried",
    "lonely",
    "isolated",
    "sad",
    "upset",
    "struggling",
    "overthinking",
]


def determine_urgency(message: str) -> UrgencyLevel:
    """
    Determines preliminary support urgency.

    Crisis detection is handled separately and must be
    checked before this function is used.
    """

    normalized = message.lower().strip()

    if any(indicator in normalized for indicator in URGENT_INDICATORS):
        return UrgencyLevel.URGENT

    if any(indicator in normalized for indicator in SUPPORT_INDICATORS):
        return UrgencyLevel.SUPPORT

    return UrgencyLevel.NORMAL