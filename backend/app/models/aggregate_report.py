from pydantic import BaseModel


class AggregateReport(BaseModel):
    report_type: str

    total_referrals: int
    total_counselling_records: int
    total_follow_ups: int
    total_accommodations: int

    referral_by_urgency: dict[str, int]
    referral_by_source: dict[str, int]
    referral_by_status: dict[str, int]
    accommodation_by_type: dict[str, int]

    privacy_threshold: int
    breakdown_available: bool