import { useCallback } from 'react'
import { listResources } from '../../api/resources'
import { RoleDashboard } from '../shared/RoleDashboard'
import { SupportRequestForm } from '../support/SupportRequestForm'
import { ResourcesDirectory } from '../resources/ResourcesDirectory'
import { Alert } from '../../components/ui/Feedback'
import { useAuth } from '../../auth/AuthContext'

export function StudentDashboard() {
  const { session } = useAuth()
  const loadStats = useCallback(async () => {
    const resources = await listResources()
    return [
      { label: 'Signed-in account', value: session?.username ?? '—' },
      { label: 'Active resources', value: resources.filter((r) => r.active).length },
      { label: 'Workspace', value: 'Private' },
    ]
  }, [session?.username])

  return (
    <>
      <RoleDashboard
        title="Student workspace"
        description="A calm private space to request authorised human support and browse approved resources."
        loadStats={loadStats}
        actions={[
          { label: 'Request support', to: '/student/support' },
          { label: 'Browse resources', to: '/student/resources' },
        ]}
      />
      <Alert tone="info" title="Privacy note">
        Referral queues, counselling notes, and internal escalations are not shown
        in the student workspace. Support staff manage those workflows separately.
      </Alert>
    </>
  )
}

export function StudentSupportPage() {
  return (
    <SupportRequestForm
      defaultSource="self_referral"
      heading="Request support"
      description="Connect with authorised human support. Agent 66 routes your request; it does not provide counselling or diagnosis."
    />
  )
}

export function StudentResourcesPage() {
  return <ResourcesDirectory />
}
