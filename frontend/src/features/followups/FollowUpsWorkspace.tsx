import { useEffect, useState } from 'react'
import {
  completeFollowUp,
  listDueFollowUps,
  listFollowUps,
} from '../../api/followups'
import { ApiError, type CounsellingRecord } from '../../types/api'
import { Alert, EmptyState, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { useToast } from '../../components/ui/Toast'
import { formatDateTime } from '../../utils/format'

export function FollowUpsWorkspace() {
  const { pushToast } = useToast()
  const [tab, setTab] = useState<'all' | 'due'>('all')
  const [items, setItems] = useState<CounsellingRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = async (nextTab = tab) => {
    setLoading(true)
    setError(null)
    try {
      const data =
        nextTab === 'due' ? await listDueFollowUps() : await listFollowUps()
      setItems(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load follow-ups.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(tab)
  }, [tab])

  const onComplete = async (recordId: string) => {
    setBusyId(recordId)
    try {
      await completeFollowUp(recordId)
      pushToast({ tone: 'success', title: 'Follow-up completed' })
      await load(tab)
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Follow-up update failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Follow-ups</h1>
          <p>Track required follow-up actions linked to counselling records.</p>
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="Follow-up views">
        <button
          type="button"
          className="tab"
          role="tab"
          aria-selected={tab === 'all'}
          onClick={() => setTab('all')}
        >
          All follow-ups
        </button>
        <button
          type="button"
          className="tab"
          role="tab"
          aria-selected={tab === 'due'}
          onClick={() => setTab('due')}
        >
          Due
        </button>
      </div>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load follow-ups">
          {error}
        </Alert>
      ) : items.length === 0 ? (
        <EmptyState
          title={tab === 'due' ? 'No due follow-ups' : 'No follow-ups required'}
          description="Follow-up actions will appear here when counselling records require them."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Record</th>
                <th>Referral</th>
                <th>Student</th>
                <th>Follow-up date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.record_id}>
                  <td>{item.record_id}</td>
                  <td>{item.referral_id}</td>
                  <td>{item.student_id}</td>
                  <td>{formatDateTime(item.follow_up_date)}</td>
                  <td>{item.follow_up_status}</td>
                  <td>
                    {item.follow_up_status !== 'completed' ? (
                      <Button
                        type="button"
                        size="sm"
                        loading={busyId === item.record_id}
                        onClick={() => void onComplete(item.record_id)}
                      >
                        Complete
                      </Button>
                    ) : (
                      '—'
                    )}
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
