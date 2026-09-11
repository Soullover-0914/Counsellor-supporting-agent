CRISIS_INDICATORS = [
    "kill myself",
    "killing myself",
    "suicide",
    "suicidal",
    "end my life",
    "ending my life",
    "take my own life",
    "taking my own life",
    "hurt myself",
    "hurting myself",
    "harm myself",
    "harming myself",
    "self harm",
    "self-harm",
    "want to die",
    "don't want to live",
    "do not want to live",
    "not safe",
    "feel unsafe",
    "feeling unsafe",
]


def detect_crisis(message: str) -> bool:
    """
    High-priority safety check.

    This is intentionally simple and deterministic.
    A positive match must bypass normal triage.
    """

    if not isinstance(message, str):
        return False

    normalized = message.lower().strip()

    return any(
        indicator in normalized
        for indicator in CRISIS_INDICATORS
    )