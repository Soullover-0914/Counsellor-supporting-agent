import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { ProtectedRoute } from '../components/routing/ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'
import { FacultyDemoPage } from '../pages/FacultyDemoPage'
import { SignupPage } from '../pages/SignupPage'
import { ChangePasswordPage } from '../pages/ChangePasswordPage'
import { PrivacyPage } from '../pages/PrivacyPage'
import { TermsPage } from '../pages/TermsPage'
import { AccessRestrictedPage } from '../pages/AccessRestrictedPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { Skeleton } from '../components/ui/Feedback'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME } from '../auth/roles'

const StudentDashboard = lazy(() =>
  import('../features/student/pages').then((m) => ({
    default: m.StudentDashboard,
  })),
)

const StudentSupportPage = lazy(() =>
  import('../features/student/pages').then((m) => ({
    default: m.StudentSupportPage,
  })),
)

const StudentResourcesPage = lazy(() =>
  import('../features/student/pages').then((m) => ({
    default: m.StudentResourcesPage,
  })),
)

const CounsellorDashboard = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorDashboard,
  })),
)

const CounsellorReferralsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorReferralsPage,
  })),
)

const CounsellorAppointmentsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorAppointmentsPage,
  })),
)

const CounsellorRecordsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorRecordsPage,
  })),
)

const CounsellorFollowUpsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorFollowUpsPage,
  })),
)

const CounsellorEscalationsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorEscalationsPage,
  })),
)

const CounsellorAccommodationsPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorAccommodationsPage,
  })),
)

const CounsellorResourcesPage = lazy(() =>
  import('../features/counsellor/pages').then((m) => ({
    default: m.CounsellorResourcesPage,
  })),
)

const MentorDashboard = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.MentorDashboard,
  })),
)

const MentorSupportPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.MentorSupportPage,
  })),
)

const MentorReferralsPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.MentorReferralsPage,
  })),
)

const MentorResourcesPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.MentorResourcesPage,
  })),
)

const FacultyDashboard = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.FacultyDashboard,
  })),
)

const FacultySupportPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.FacultySupportPage,
  })),
)

const FacultyReferralsPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.FacultyReferralsPage,
  })),
)

const FacultyResourcesPage = lazy(() =>
  import('../features/mentor/pages').then((m) => ({
    default: m.FacultyResourcesPage,
  })),
)

const HodDashboard = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.HodDashboard,
  })),
)

const DeanDashboard = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.DeanDashboard,
  })),
)

const AdminDashboard = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.AdminDashboard,
  })),
)

const LeadershipReferralsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipReferralsPage,
  })),
)

const LeadershipAppointmentsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipAppointmentsPage,
  })),
)

const LeadershipAccommodationsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipAccommodationsPage,
  })),
)

const LeadershipReportsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipReportsPage,
  })),
)

const LeadershipAuditPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipAuditPage,
  })),
)

const LeadershipEscalationsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipEscalationsPage,
  })),
)

const LeadershipResourcesPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.LeadershipResourcesPage,
  })),
)

const AdminRegistrationsPage = lazy(() =>
  import('../features/leadership/pages').then((m) => ({
    default: m.AdminRegistrationsPage,
  })),
)

function RouteFallback() {
  return (
    <div className="app-page" aria-busy="true">
      <Skeleton height={28} width={240} />
      <Skeleton height={180} />
    </div>
  )
}

function HomeRedirect() {
  const { session, isAuthenticated, isBootstrapping } = useAuth()

  if (isBootstrapping) return null

  if (isAuthenticated && session) {
    if (session.mustChangePassword) {
      return <Navigate to="/change-password" replace />
    }

    return <Navigate to={ROLE_HOME[session.role]} replace />
  }

  return <Navigate to="/login" replace />
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/faculty-demo" element={<FacultyDemoPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route
            path="/access-restricted"
            element={<AccessRestrictedPage />}
          />

          <Route element={<ProtectedRoute />}>
            <Route
              path="/change-password"
              element={<ChangePasswordPage />}
            />
          </Route>

          <Route element={<ProtectedRoute roles={['student']} />}>
            <Route element={<AppShell />}>
              <Route path="/student" element={<StudentDashboard />} />
              <Route
                path="/student/support"
                element={<StudentSupportPage />}
              />
              <Route
                path="/student/resources"
                element={<StudentResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['counsellor']} />}>
            <Route element={<AppShell />}>
              <Route
                path="/counsellor"
                element={<CounsellorDashboard />}
              />
              <Route
                path="/counsellor/referrals"
                element={<CounsellorReferralsPage />}
              />
              <Route
                path="/counsellor/appointments"
                element={<CounsellorAppointmentsPage />}
              />
              <Route
                path="/counsellor/records"
                element={<CounsellorRecordsPage />}
              />
              <Route
                path="/counsellor/followups"
                element={<CounsellorFollowUpsPage />}
              />
              <Route
                path="/counsellor/escalations"
                element={<CounsellorEscalationsPage />}
              />
              <Route
                path="/counsellor/accommodations"
                element={<CounsellorAccommodationsPage />}
              />
              <Route
                path="/counsellor/resources"
                element={<CounsellorResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['mentor']} />}>
            <Route element={<AppShell />}>
              <Route path="/mentor" element={<MentorDashboard />} />
              <Route
                path="/mentor/support"
                element={<MentorSupportPage />}
              />
              <Route
                path="/mentor/referrals"
                element={<MentorReferralsPage />}
              />
              <Route
                path="/mentor/resources"
                element={<MentorResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['faculty']} />}>
            <Route element={<AppShell />}>
              <Route
                path="/faculty"
                element={<FacultyDashboard />}
              />
              <Route
                path="/faculty/support"
                element={<FacultySupportPage />}
              />
              <Route
                path="/faculty/referrals"
                element={<FacultyReferralsPage />}
              />
              <Route
                path="/faculty/resources"
                element={<FacultyResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['hod']} />}>
            <Route element={<AppShell />}>
              <Route path="/hod" element={<HodDashboard />} />
              <Route
                path="/hod/referrals"
                element={<LeadershipReferralsPage />}
              />
              <Route
                path="/hod/appointments"
                element={<LeadershipAppointmentsPage />}
              />
              <Route
                path="/hod/accommodations"
                element={<LeadershipAccommodationsPage />}
              />
              <Route
                path="/hod/reports"
                element={<LeadershipReportsPage />}
              />
              <Route
                path="/hod/audit"
                element={<LeadershipAuditPage />}
              />
              <Route
                path="/hod/resources"
                element={<LeadershipResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['dean']} />}>
            <Route element={<AppShell />}>
              <Route path="/dean" element={<DeanDashboard />} />
              <Route
                path="/dean/referrals"
                element={<LeadershipReferralsPage />}
              />
              <Route
                path="/dean/escalations"
                element={<LeadershipEscalationsPage />}
              />
              <Route
                path="/dean/accommodations"
                element={<LeadershipAccommodationsPage />}
              />
              <Route
                path="/dean/reports"
                element={<LeadershipReportsPage />}
              />
              <Route
                path="/dean/audit"
                element={<LeadershipAuditPage />}
              />
              <Route
                path="/dean/resources"
                element={<LeadershipResourcesPage />}
              />
            </Route>
          </Route>

          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route element={<AppShell />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route
                path="/admin/registrations"
                element={<AdminRegistrationsPage />}
              />
              <Route
                path="/admin/referrals"
                element={<LeadershipReferralsPage />}
              />
              <Route
                path="/admin/escalations"
                element={<LeadershipEscalationsPage />}
              />
              <Route
                path="/admin/accommodations"
                element={<LeadershipAccommodationsPage />}
              />
              <Route
                path="/admin/reports"
                element={<LeadershipReportsPage />}
              />
              <Route
                path="/admin/audit"
                element={<LeadershipAuditPage />}
              />
              <Route
                path="/admin/resources"
                element={<LeadershipResourcesPage />}
              />
            </Route>
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}