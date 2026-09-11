import type { UrgencyLevel, ReferralStatus } from '../../types/api'
import { Badge } from './Feedback'
import { titleCase } from '../../utils/format'

export function UrgencyBadge({ urgency }: { urgency: UrgencyLevel | string }) {
  const tone =
    urgency === 'crisis'
      ? 'danger'
      : urgency === 'urgent'
        ? 'warning'
        : urgency === 'support'
          ? 'info'
          : 'neutral'

  return <Badge tone={tone}>{titleCase(String(urgency))}</Badge>
}

export function StatusBadge({ status }: { status: ReferralStatus | string }) {
  const tone =
    status === 'completed'
      ? 'success'
      : status === 'in_progress'
        ? 'info'
        : status === 'assigned'
          ? 'warning'
          : 'neutral'

  return <Badge tone={tone}>{titleCase(String(status))}</Badge>
}

export function OutcomeBadge({ outcome }: { outcome: string }) {
  return (
    <Badge tone={outcome === 'success' ? 'success' : 'danger'}>
      {titleCase(outcome)}
    </Badge>
  )
}
