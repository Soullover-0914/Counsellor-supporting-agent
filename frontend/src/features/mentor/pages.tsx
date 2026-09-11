import { useCallback } from 'react'
import { listReferrals } from '../../api/referrals'
import { listResources } from '../../api/resources'
import { RoleDashboard } from '../shared/RoleDashboard'
import { SupportRequestForm } from '../support/SupportRequestForm'
import { ReferralsWorkspace } from '../referrals/ReferralsWorkspace'
import { ResourcesDirectory } from '../resources/ResourcesDirectory'

export function MentorDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, resources] = await Promise.all([listReferrals(), listResources()])
    return [
      { label: 'Visible referrals', value: referrals.length },
      { label: 'Pending referrals', value: referrals.filter((r) => r.status === 'pending').length },
      { label: 'Resources', value: resources.filter((r) => r.active).length },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Mentor workspace"
      description="Refer students to authorised support and monitor referral workflow status available to mentors."
      loadStats={loadStats}
      actions={[
        { label: 'Refer a student', to: '/mentor/support' },
        { label: 'Referral queue', to: '/mentor/referrals' },
      ]}
    />
  )
}

export function MentorSupportPage() {
  return (
    <SupportRequestForm
      defaultSource="mentor_referral"
      allowStudentIdEdit
      heading="Refer a student"
      description="Submit a mentor referral for authorised human review. This system does not provide counselling."
    />
  )
}

export function MentorReferralsPage() {
  return (
    <ReferralsWorkspace
      title="Mentor referral view"
      description="Referral status visible to mentors. Assignment and clinical actions remain with authorised counselling staff."
    />
  )
}

export function MentorResourcesPage() {
  return <ResourcesDirectory />
}

export function FacultyDashboard() {
  const loadStats = useCallback(async () => {
    const [referrals, resources] = await Promise.all([listReferrals(), listResources()])
    return [
      { label: 'Visible referrals', value: referrals.length },
      { label: 'Pending referrals', value: referrals.filter((r) => r.status === 'pending').length },
      { label: 'Resources', value: resources.filter((r) => r.active).length },
    ]
  }, [])

  return (
    <RoleDashboard
      title="Faculty workspace"
      description="Refer students for support and review referral workflow information available to faculty."
      loadStats={loadStats}
      actions={[
        { label: 'Refer a student', to: '/faculty/support' },
        { label: 'Referral queue', to: '/faculty/referrals' },
      ]}
    />
  )
}

export function FacultySupportPage() {
  return (
    <SupportRequestForm
      defaultSource="faculty_referral"
      allowStudentIdEdit
      heading="Refer a student"
      description="Submit a faculty referral for authorised human review. Counselling reasons remain restricted from academic accommodation views."
    />
  )
}

export function FacultyReferralsPage() {
  return (
    <ReferralsWorkspace
      title="Faculty referral view"
      description="Referral workflow visibility for faculty. Sensitive counselling records are not available in this role."
    />
  )
}

export function FacultyResourcesPage() {
  return <ResourcesDirectory />
}
