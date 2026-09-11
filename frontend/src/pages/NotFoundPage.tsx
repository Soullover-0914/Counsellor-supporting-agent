import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'

export function NotFoundPage() {
  return (
    <div className="policy-page">
      <div className="card" style={{ maxWidth: 520 }}>
        <h1>Page not found</h1>
        <p style={{ color: 'var(--ink-secondary)', marginTop: '0.5rem' }}>
          The page you requested is not part of Agent 66, or the link may be
          incorrect.
        </p>
        <div style={{ marginTop: '1rem' }}>
          <Link to="/login">
            <Button type="button">Go to sign in</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
