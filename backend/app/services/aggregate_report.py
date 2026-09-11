from app.models.aggregate_report import AggregateReport
from app.services.referral import get_referrals
from app.services.counselling_record import get_counselling_records
from app.services.accommodation import get_accommodations


# Privacy protection:
# Detailed aggregate breakdowns are only exposed when
# the total number of referrals reaches this threshold.
MINIMUM_GROUP_SIZE = 5


def generate_aggregate_report() -> AggregateReport:
    referrals = get_referrals()
    counselling_records = get_counselling_records()
    accommodations = get_accommodations()

    total_referrals = len(referrals)
    total_counselling_records = len(counselling_records)

    total_follow_ups = sum(
        1
        for record in counselling_records
        if record.follow_up_required
    )

    total_accommodations = len(accommodations)

    # --------------------------------------------------------
    # Privacy protection
    # --------------------------------------------------------

    if total_referrals < MINIMUM_GROUP_SIZE:
        return AggregateReport(
            report_type="anonymous_aggregate",
            total_referrals=total_referrals,
            total_counselling_records=total_counselling_records,
            total_follow_ups=total_follow_ups,
            total_accommodations=total_accommodations,
            referral_by_urgency={},
            referral_by_source={},
            referral_by_status={},
            accommodation_by_type={},
            privacy_threshold=MINIMUM_GROUP_SIZE,
            breakdown_available=False,
        )

    # --------------------------------------------------------
    # Referral urgency
    # --------------------------------------------------------

    referral_by_urgency: dict[str, int] = {}

    for referral in referrals:
        urgency = str(referral.urgency)

        referral_by_urgency[urgency] = (
            referral_by_urgency.get(urgency, 0) + 1
        )

    # --------------------------------------------------------
    # Referral source
    # --------------------------------------------------------

    referral_by_source: dict[str, int] = {}

    for referral in referrals:
        source = str(referral.source)

        referral_by_source[source] = (
            referral_by_source.get(source, 0) + 1
        )

    # --------------------------------------------------------
    # Referral status
    # --------------------------------------------------------

    referral_by_status: dict[str, int] = {}

    for referral in referrals:
        status = str(referral.status)

        referral_by_status[status] = (
            referral_by_status.get(status, 0) + 1
        )

    # --------------------------------------------------------
    # Accommodation type
    # --------------------------------------------------------

    accommodation_by_type: dict[str, int] = {}

    for accommodation in accommodations:
        accommodation_type = accommodation.accommodation_type

        accommodation_by_type[accommodation_type] = (
            accommodation_by_type.get(accommodation_type, 0) + 1
        )

    return AggregateReport(
        report_type="anonymous_aggregate",
        total_referrals=total_referrals,
        total_counselling_records=total_counselling_records,
        total_follow_ups=total_follow_ups,
        total_accommodations=total_accommodations,
        referral_by_urgency=referral_by_urgency,
        referral_by_source=referral_by_source,
        referral_by_status=referral_by_status,
        accommodation_by_type=accommodation_by_type,
        privacy_threshold=MINIMUM_GROUP_SIZE,
        breakdown_available=True,
    )