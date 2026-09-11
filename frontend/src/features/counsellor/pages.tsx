import { useCallback } from 'react'
import { listReferrals } from '../../api/referrals'
import { listAppointments } from '../../api/appointments'
import { listFollowUps } from '../../api/followups'
import { listEscalations } from '../../api/escalations'
import { RoleDashboard } from '../shared/RoleDashboard'
import { ReferralsWorkspace } from '../referrals/ReferralsWorkspace'
import { AppointmentsWorkspace } from '../appointments/AppointmentsWorkspace'
import { RecordsWorkspace } from '../records/RecordsWorkspace'
import { FollowUpsWorkspace } from '../followups/FollowUpsWorkspace'
import { EscalationsWorkspace } from '../escalations/EscalationsWorkspace'
import { AccommodationsWorkspace } from '../accommodations/AccommodationsWorkspace'
import { ResourcesDirectory } from '../resources/ResourcesDirectory'

export function CounsellorDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, appointments, followUps, escalations] = await Promise.all([
      listReferrals(),
      listAppointments(),
      listFollowUps(),
      listEscalations(),
    ])
    return [
      { label: 'Open referrals', value: referrals.filter((r) => r.status !== 'completed').length },
      { label: 'Appointments', value: appointments.length },
      { label: 'Follow-ups', value: followUps.length },
      { label: 'Escalations', value: escalations.length },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Counsellor workspace"
      description="Professional queue management for referrals, sessions, follow-ups, and escalations."
      loadStats={loadStats}
      actions={[
        { label: 'Referral queue', to: '/counsellor/referrals' },
        { label: 'Escalations', to: '/counsellor/escalations' },
      ]}
    />
  )
}

export function CounsellorReferralsPage() {
  return <ReferralsWorkspace canManage canRecord />
}

export function CounsellorAppointmentsPage() {
  return <AppointmentsWorkspace />
}

export function CounsellorRecordsPage() {
  return <RecordsWorkspace />
}

export function CounsellorFollowUpsPage() {
  return <FollowUpsWorkspace />
}

export function CounsellorEscalationsPage() {
  return <EscalationsWorkspace />
}

export function CounsellorAccommodationsPage() {
  return <AccommodationsWorkspace />
}

export function CounsellorResourcesPage() {
  return <ResourcesDirectory canManage />
}
