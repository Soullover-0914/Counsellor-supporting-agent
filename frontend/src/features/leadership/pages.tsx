import { useCallback } from 'react'
import { listReferrals } from '../../api/referrals'
import { listAppointments } from '../../api/appointments'
import { listAccommodations } from '../../api/accommodations'
import { getAggregateReport } from '../../api/reports'
import { listEscalations } from '../../api/escalations'
import { RoleDashboard } from '../shared/RoleDashboard'
import { ReferralsWorkspace } from '../referrals/ReferralsWorkspace'
import { AppointmentsWorkspace } from '../appointments/AppointmentsWorkspace'
import { AccommodationsWorkspace } from '../accommodations/AccommodationsWorkspace'
import { AggregateReportView } from '../reports/AggregateReportView'
import { AuditLogsWorkspace } from '../audit/AuditLogsWorkspace'
import { EscalationsWorkspace } from '../escalations/EscalationsWorkspace'
import { ResourcesDirectory } from '../resources/ResourcesDirectory'
import { RegistrationsWorkspace } from '../admin/RegistrationsWorkspace'

export function HodDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, appointments, accommodations, report] = await Promise.all([
      listReferrals(),
      listAppointments(),
      listAccommodations(),
      getAggregateReport(),
    ])
    return [
      { label: 'Referrals', value: referrals.length },
      { label: 'Appointments', value: appointments.length },
      { label: 'Accommodations', value: accommodations.length },
      { label: 'Aggregate referrals', value: report.total_referrals },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Head of Department workspace"
      description="Oversight of referral operations, accommodations, and anonymous aggregate reporting."
      loadStats={loadStats}
      actions={[
        { label: 'Aggregate reports', to: '/hod/reports' },
        { label: 'Audit logs', to: '/hod/audit' },
      ]}
    />
  )
}

export function DeanDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, escalations, accommodations, report] = await Promise.all([
      listReferrals(),
      listEscalations(),
      listAccommodations(),
      getAggregateReport(),
    ])
    return [
      { label: 'Referrals', value: referrals.length },
      { label: 'Escalations', value: escalations.length },
      { label: 'Accommodations', value: accommodations.length },
      { label: 'Aggregate referrals', value: report.total_referrals },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Dean workspace"
      description="Institutional oversight across referrals, escalations, accommodations, and audit accountability."
      loadStats={loadStats}
      actions={[
        { label: 'Escalations', to: '/dean/escalations' },
        { label: 'Aggregate reports', to: '/dean/reports' },
      ]}
    />
  )
}

export function AdminDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, escalations, accommodations, report] = await Promise.all([
      listReferrals(),
      listEscalations(),
      listAccommodations(),
      getAggregateReport(),
    ])
    return [
      { label: 'Referrals', value: referrals.length },
      { label: 'Escalations', value: escalations.length },
      { label: 'Accommodations', value: accommodations.length },
      { label: 'Aggregate referrals', value: report.total_referrals },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Administration workspace"
      description="Operational administration for counselling-support workflows, reporting, and audit review."
      loadStats={loadStats}
      actions={[
        { label: 'Audit logs', to: '/admin/audit' },
        { label: 'Aggregate reports', to: '/admin/reports' },
      ]}
    />
  )
}

export function LeadershipReferralsPage() {
  return <ReferralsWorkspace canManage />
}

export function LeadershipAppointmentsPage() {
  return <AppointmentsWorkspace />
}

export function LeadershipAccommodationsPage() {
  return <AccommodationsWorkspace canUpdateStatus />
}

export function LeadershipReportsPage() {
  return <AggregateReportView />
}

export function LeadershipAuditPage() {
  return <AuditLogsWorkspace />
}

export function LeadershipEscalationsPage() {
  return <EscalationsWorkspace />
}

export function LeadershipResourcesPage() {
  return <ResourcesDirectory canManage />
}

export function AdminRegistrationsPage() {
  return <RegistrationsWorkspace />
}

