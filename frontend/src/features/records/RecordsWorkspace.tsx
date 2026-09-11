import { useEffect, useState } from 'react'
import {
  completeCounsellingRecord,
  listCounsellingRecords,
} from '../../api/records'
import { ApiError, type CounsellingRecord } from '../../types/api'
import { Alert, EmptyState, PrivacyChip, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { Drawer } from '../../components/ui/Overlay'
import { useToast } from '../../components/ui/Toast'
import { formatDateTime } from '../../utils/format'
import { FolderLock } from 'lucide-react'

export function RecordsWorkspace() {
  const { pushToast } = useToast()
  const [records, setRecords] = useState<CounsellingRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<CounsellingRecord | null>(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setRecords(await listCounsellingRecords())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const onComplete = async () => {
    if (!selected) return
    setBusy(true)
    try {
      const next = await completeCounsellingRecord(selected.record_id)
      setSelected(next)
      setRecords((current) =>
        current.map((item) => (item.record_id === next.record_id ? next : item)),
      )
      pushToast({ tone: 'success', title: 'Record marked complete' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Could not complete record',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Counselling records</h1>
          <p>Restricted professional session documentation.</p>
        </div>
        <PrivacyChip>
          <FolderLock size={14} aria-hidden /> Confidential counselling record
        </PrivacyChip>
      </header>

      <Alert tone="warning" title="Restricted information">
        Session summaries are confidential. Do not copy them into email, chat, or
        shared academic systems.
      </Alert>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load counselling records">
          {error}
        </Alert>
      ) : records.length === 0 ? (
        <EmptyState
          title="No counselling records"
          description="Confidential session records will appear here after authorised counsellors create them."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Record</th>
                <th>Referral</th>
                <th>Student</th>
                <th>Counsellor</th>
                <th>Session date</th>
                <th>Follow-up</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr
                  key={record.record_id}
                  className="is-clickable"
                  onClick={() => setSelected(record)}
                >
                  <td>{record.record_id}</td>
                  <td>{record.referral_id}</td>
                  <td>{record.student_id}</td>
                  <td>{record.counsellor_id}</td>
                  <td>{formatDateTime(record.session_date)}</td>
                  <td>{record.follow_up_status}</td>
                  <td>{record.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Drawer
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        title="Confidential counselling record"
        description={selected?.record_id}
      >
        {selected ? (
          <div style={{ display: 'grid', gap: '0.85rem' }}>
            <div className="grid-2">
              <div>
                <div className="field-label">Student</div>
                <div>{selected.student_id}</div>
              </div>
              <div>
                <div className="field-label">Referral</div>
                <div>{selected.referral_id}</div>
              </div>
              <div>
                <div className="field-label">Session date</div>
                <div>{formatDateTime(selected.session_date)}</div>
              </div>
              <div>
                <div className="field-label">Status</div>
                <div>{selected.status}</div>
              </div>
            </div>
            <div>
              <div className="field-label">Session summary</div>
              <p
                style={{
                  marginTop: '0.35rem',
                  whiteSpace: 'pre-wrap',
                  background: 'var(--surface-muted)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem',
                }}
              >
                {selected.session_summary}
              </p>
            </div>
            {selected.status !== 'completed' ? (
              <Button type="button" loading={busy} onClick={() => void onComplete()}>
                Mark record complete
              </Button>
            ) : null}
          </div>
        ) : null}
      </Drawer>
    </div>
  )
}
