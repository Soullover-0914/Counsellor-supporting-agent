import { useEffect, useState } from 'react'
import { listEscalations } from '../../api/escalations'
import { ApiError, type CrisisEscalation } from '../../types/api'
import { Alert, EmptyState, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { formatDateTime } from '../../utils/format'

export function EscalationsWorkspace() {
  const [items, setItems] = useState<CrisisEscalation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setItems(await listEscalations())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load escalations.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Crisis escalations</h1>
          <p>High-priority safety escalations requiring immediate human attention.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => void load()}>
          Refresh
        </Button>
      </header>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load escalations">
          {error}
        </Alert>
      ) : items.length === 0 ? (
        <EmptyState
          title="No crisis escalations"
          description="Immediate escalations will appear here when safety risks are identified."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Escalation</th>
                <th>Student</th>
                <th>Severity</th>
                <th>Reason</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.escalation_id}>
                  <td>{item.escalation_id}</td>
                  <td>{item.student_id}</td>
                  <td>
                    <span className="badge badge-danger">{item.severity}</span>
                  </td>
                  <td>{item.reason}</td>
                  <td>{formatDateTime(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
