import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../../types/api'
import { Alert, Skeleton } from '../../components/ui/Feedback'
import { FadeItem, Stagger } from '../../components/motion/PageTransition'
import { Button } from '../../components/ui/Button'

export function RoleDashboard({
  title,
  description,
  loadStats,
  actions,
}: {
  title: string
  description: string
  loadStats: () => Promise<Array<{ label: string; value: string | number }>>
  actions?: Array<{ label: string; to: string }>
}) {
  const [stats, setStats] = useState<Array<{ label: string; value: string | number }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const next = await loadStats()
        if (active) setStats(next)
      } catch (err) {
        if (active) {
          setError(err instanceof ApiError ? err.message : 'Unable to load dashboard.')
        }
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => {
      active = false
    }
  }, [loadStats])

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {actions ? (
          <div style={{ display: 'flex', gap: '0.55rem', flexWrap: 'wrap' }}>
            {actions.map((action) => (
              <Link key={action.to} to={action.to}>
                <Button type="button" variant="secondary">
                  {action.label}
                </Button>
              </Link>
            ))}
          </div>
        ) : null}
      </header>

      {loading ? (
        <div className="grid-3">
          <Skeleton height={96} />
          <Skeleton height={96} />
          <Skeleton height={96} />
        </div>
      ) : error ? (
        <Alert tone="danger" title="Dashboard unavailable">
          {error}
        </Alert>
      ) : (
        <Stagger className="grid-3">
          {stats.map((stat) => (
            <FadeItem key={stat.label}>
              <div className="stat-tile">
                <div className="label">{stat.label}</div>
                <div className="value">{stat.value}</div>
              </div>
            </FadeItem>
          ))}
        </Stagger>
      )}
    </div>
  )
}

export function SimplePage({ children }: { children: ReactNode }) {
  return <>{children}</>
}
