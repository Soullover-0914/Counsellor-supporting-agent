import { Link } from 'react-router-dom'
import { ShieldOff } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME } from '../auth/roles'

export function AccessRestrictedPage() {
  const { session } = useAuth()
  const home = session ? ROLE_HOME[session.role] : '/login'

  return (
    <div className="policy-page">
      <div className="card" style={{ maxWidth: 560 }}>
        <ShieldOff size={28} aria-hidden color="var(--danger)" />
        <h1 style={{ marginTop: '0.85rem' }}>Access restricted</h1>
        <p style={{ color: 'var(--ink-secondary)', marginTop: '0.5rem' }}>
          You do not have permission to view this area. Access in Agent 66 is
          controlled by institutional role authorisation. If you believe this is
          incorrect, contact your counselling support administrator.
        </p>
        <div style={{ display: 'flex', gap: '0.65rem', marginTop: '1.1rem', alignItems: 'center' }}>
          <Link to={home}>
            <Button type="button">Return to workspace</Button>
          </Link>
          <Link to="/privacy">Privacy Policy</Link>
        </div>
      </div>
    </div>
  )
}
