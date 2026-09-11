import { useEffect, useState } from 'react'
import { listAuditLogs } from '../../api/audit'
import { ApiError, type AuditLog } from '../../types/api'
import { Alert, EmptyState, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Field'
import { OutcomeBadge } from '../../components/ui/StatusBadges'
import { formatDateTime, titleCase } from '../../utils/format'

export function AuditLogsWorkspace() {
  const [items, setItems] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setItems(await listAuditLogs(100))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load audit logs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filtered = items.filter((item) => {
    const q = query.trim().toLowerCase()
    if (!q) return true
    return (
      item.actor_id.toLowerCase().includes(q) ||
      item.action.toLowerCase().includes(q) ||
      item.resource_type.toLowerCase().includes(q) ||
      (item.resource_id ?? '').toLowerCase().includes(q)
    )
  })

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Audit logs</h1>
          <p>Metadata-only accountability trail for authorised institutional review.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => void load()}>
          Refresh
        </Button>
      </header>

      <Input
        aria-label="Search audit logs"
        placeholder="Search actor, action, or resource"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ maxWidth: 360 }}
      />

      {loading ? (
        <Skeleton height={240} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load audit logs">
          {error}
        </Alert>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No audit events"
          description="Audit metadata will appear here as authorised actions occur."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Role</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Resource ID</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.audit_id}>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>{item.actor_id}</td>
                  <td>{titleCase(item.actor_role)}</td>
                  <td>{item.action}</td>
                  <td>{item.resource_type}</td>
                  <td>{item.resource_id ?? '—'}</td>
                  <td>
                    <OutcomeBadge outcome={item.outcome} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
