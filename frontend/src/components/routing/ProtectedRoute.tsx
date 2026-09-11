import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import type { UserRole } from '../../types/api'
import { Skeleton } from '../ui/Feedback'

export function ProtectedRoute({ roles }: { roles?: UserRole[] }) {
  const { session, isAuthenticated, isBootstrapping } = useAuth()
  const location = useLocation()

  if (isBootstrapping) {
    return (
      <div className="policy-page" aria-busy="true">
        <Skeleton height={28} width={220} />
        <div style={{ height: 12 }} />
        <Skeleton height={160} />
      </div>
    )
  }

  if (!isAuthenticated || !session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (
    session.mustChangePassword &&
    location.pathname !== '/change-password'
  ) {
    return <Navigate to="/change-password" replace />
  }

  if (roles && !roles.includes(session.role)) {
    return <Navigate to="/access-restricted" replace />
  }

  return <Outlet />
}
