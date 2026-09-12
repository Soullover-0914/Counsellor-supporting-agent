import { useEffect, useMemo, useState } from 'react'
import {
  approveRegistration,
  listRegistrations,
  rejectRegistration,
  resendRegistrationCredentials,
} from '../../api/auth'
import { ApiError, type RegistrationRequest } from '../../types/api'
import { Alert, EmptyState, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { Select } from '../../components/ui/Field'
import { Dialog, Drawer } from '../../components/ui/Overlay'
import { StatusBadge } from '../../components/ui/StatusBadges'
import { useToast } from '../../components/ui/Toast'
import { formatDateTime, titleCase } from '../../utils/format'

export function RegistrationsWorkspace() {
  const { pushToast } = useToast()
  const [items, setItems] = useState<RegistrationRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all')
  const [selected, setSelected] = useState<RegistrationRequest | null>(null)
  const [confirm, setConfirm] = useState<'approve' | 'reject' | 'resend' | null>(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const next = await listRegistrations()
      setItems(next)
      setSelected((current) => {
        if (!current) return null
        return (
          next.find((item) => item.registration_id === current.registration_id) ??
          null
        )
      })
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'Unable to load registration requests.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return items
    return items.filter((item) => item.status === statusFilter)
  }, [items, statusFilter])

  useEffect(() => {
    if (!selected) return
    const visible = filtered.some(
      (item) => item.registration_id === selected.registration_id,
    )
    if (!visible) {
      setSelected(null)
      setConfirm(null)
    }
  }, [filtered, selected])

  const runAction = async () => {
    if (!selected || !confirm) return
    setBusy(true)
    try {
      if (confirm === 'approve') {
        const result = await approveRegistration(selected.registration_id)
        setStatusFilter('approved')
        setSelected(result.registration)
        pushToast({
          tone: result.email_sent ? 'success' : 'info',
          title: result.email_sent ? 'Registration accepted' : 'Approved — email issue',
          message: result.message,
        })
      } else if (confirm === 'reject') {
        const next = await rejectRegistration(selected.registration_id)
        setStatusFilter('rejected')
        setSelected(next)
        pushToast({ tone: 'success', title: 'Registration rejected' })
      } else {
        const result = await resendRegistrationCredentials(selected.registration_id)
        pushToast({
          tone: result.email_sent ? 'success' : 'error',
          title: result.email_sent ? 'Credentials emailed' : 'Email not delivered',
          message: result.message,
        })
      }
      setConfirm(null)
      await load()
    } catch (err) {
      if (err instanceof ApiError && (err.status === 400 || err.status === 404)) {
        setSelected(null)
        setConfirm(null)
        await load()
      }
      pushToast({
        tone: 'error',
        title: 'Action failed',
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
          <h1>Registration requests</h1>
          <p>Review pending student registrations before account activation.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => void load()}>
          Refresh
        </Button>
      </header>

      <div className="toolbar">
        <Select
          aria-label="Filter registration status"
          value={statusFilter}
          onChange={(e) =>
            setStatusFilter(e.target.value as typeof statusFilter)
          }
          style={{ width: 200 }}
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </Select>
      </div>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load registrations">
          {error}
        </Alert>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No registration requests"
          description="No student registration requests match this filter."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Request</th>
                <th>Student</th>
                <th>Student ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr
                  key={item.registration_id}
                  className="is-clickable"
                  onClick={() => setSelected(item)}
                >
                  <td>{item.registration_id}</td>
                  <td>{item.student_name}</td>
                  <td>{item.student_id}</td>
                  <td>{item.username}</td>
                  <td>{item.email}</td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{formatDateTime(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Drawer
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        title={selected?.registration_id ?? 'Registration'}
        description="Registration review"
      >
        {selected ? (
          <div style={{ display: 'grid', gap: '0.85rem' }}>
            <div className="grid-2">
              <div>
                <div className="field-label">Student</div>
                <div>{selected.student_name}</div>
              </div>
              <div>
                <div className="field-label">Student ID</div>
                <div>{selected.student_id}</div>
              </div>
              <div>
                <div className="field-label">Username</div>
                <div>{selected.username}</div>
              </div>
              <div>
                <div className="field-label">Email</div>
                <div>{selected.email}</div>
              </div>
              <div>
                <div className="field-label">Branch</div>
                <div>{selected.branch}</div>
              </div>
              <div>
                <div className="field-label">Year</div>
                <div>{selected.year}</div>
              </div>
              <div>
                <div className="field-label">Status</div>
                <div>{titleCase(selected.status)}</div>
              </div>
              <div>
                <div className="field-label">Reviewed by</div>
                <div>{selected.reviewed_by ?? '—'}</div>
              </div>
            </div>

            {selected.status === 'pending' ? (
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                <Button type="button" onClick={() => setConfirm('approve')}>
                  Approve
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setConfirm('reject')}
                >
                  Reject
                </Button>
              </div>
            ) : null}

            {selected.status === 'approved' ? (
              <Button type="button" variant="secondary" onClick={() => setConfirm('resend')}>
                Resend temporary credentials
              </Button>
            ) : null}
          </div>
        ) : null}
      </Drawer>

      <Dialog
        open={Boolean(confirm)}
        onClose={() => setConfirm(null)}
        title={
          confirm === 'approve'
            ? 'Approve registration?'
            : confirm === 'reject'
              ? 'Reject registration?'
              : 'Resend temporary credentials?'
        }
        description={
          confirm === 'approve'
            ? 'A student account will be created and a temporary password will be generated server-side.'
            : confirm === 'reject'
              ? 'The request will be marked rejected and will remain in the audit trail.'
              : 'A new temporary password will be generated only if the student has not completed the one-time password change.'
        }
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setConfirm(null)}>
              Cancel
            </Button>
            <Button type="button" loading={busy} onClick={() => void runAction()}>
              Confirm
            </Button>
          </>
        }
      >
        <p style={{ color: 'var(--ink-secondary)' }}>
          Temporary passwords are never displayed in this interface.
        </p>
      </Dialog>
    </div>
  )
}
