import { useEffect, useMemo, useState } from 'react'
import {
  assignReferral,
  listReferrals,
  scheduleReferral,
  updateReferralStatus,
} from '../../api/referrals'
import { createAccommodation } from '../../api/accommodations'
import { createCounsellingRecord } from '../../api/records'
import {
  ApiError,
  type Referral,
  type ReferralStatus,
} from '../../types/api'
import { Button } from '../../components/ui/Button'
import { Field, Input, Select, Textarea } from '../../components/ui/Field'
import { Alert, EmptyState, PrivacyChip, Skeleton } from '../../components/ui/Feedback'
import { Drawer, Dialog } from '../../components/ui/Overlay'
import { StatusBadge, UrgencyBadge } from '../../components/ui/StatusBadges'
import { useToast } from '../../components/ui/Toast'
import {
  formatDateTime,
  fromDatetimeLocalValue,
  titleCase,
  toDatetimeLocalValue,
} from '../../utils/format'
import { useAuth } from '../../auth/AuthContext'

export function ReferralsWorkspace({
  canManage = false,
  canRecord = false,
  title = 'Referral queue',
  description = 'Review and manage support referrals routed for human attention.',
}: {
  canManage?: boolean
  canRecord?: boolean
  title?: string
  description?: string
}) {
  const { session } = useAuth()
  const { pushToast } = useToast()
  const [referrals, setReferrals] = useState<Referral[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | ReferralStatus>('all')
  const [selected, setSelected] = useState<Referral | null>(null)
  const [assignId, setAssignId] = useState('')
  const [statusValue, setStatusValue] = useState<ReferralStatus>('pending')
  const [scheduleTime, setScheduleTime] = useState(toDatetimeLocalValue())
  const [busy, setBusy] = useState(false)

  const [recordOpen, setRecordOpen] = useState(false)
  const [recordSummary, setRecordSummary] = useState('')
  const [followUpRequired, setFollowUpRequired] = useState(false)
  const [followUpDate, setFollowUpDate] = useState(toDatetimeLocalValue())

  const [accOpen, setAccOpen] = useState(false)
  const [accType, setAccType] = useState('')
  const [accContact, setAccContact] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listReferrals()
      setReferrals(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load referrals.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return referrals
      .filter((item) => (statusFilter === 'all' ? true : item.status === statusFilter))
      .filter((item) => {
        if (!q) return true
        return (
          item.referral_id.toLowerCase().includes(q) ||
          item.student_id.toLowerCase().includes(q) ||
          (item.assigned_counsellor ?? '').toLowerCase().includes(q)
        )
      })
      .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))
  }, [referrals, query, statusFilter])

  const openReferral = (referral: Referral) => {
    setSelected(referral)
    setAssignId(referral.assigned_counsellor ?? session?.username ?? '')
    setStatusValue(referral.status)
    setScheduleTime(toDatetimeLocalValue())
  }

  const refreshSelected = (next: Referral) => {
    setSelected(next)
    setReferrals((current) =>
      current.map((item) => (item.referral_id === next.referral_id ? next : item)),
    )
  }

  const onAssign = async () => {
    if (!selected || !assignId.trim()) return
    setBusy(true)
    try {
      const next = await assignReferral(selected.referral_id, {
        counsellor_id: assignId.trim(),
      })
      refreshSelected(next)
      pushToast({ tone: 'success', title: 'Counsellor assigned' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Assignment failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusy(false)
    }
  }

  const onStatus = async () => {
    if (!selected) return
    setBusy(true)
    try {
      const next = await updateReferralStatus(selected.referral_id, {
        status: statusValue,
      })
      refreshSelected(next)
      pushToast({ tone: 'success', title: 'Referral status updated' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Status update failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusy(false)
    }
  }

  const onSchedule = async () => {
    if (!selected || !assignId.trim()) return
    setBusy(true)
    try {
      await scheduleReferral(selected.referral_id, {
        counsellor_id: assignId.trim(),
        appointment_time: fromDatetimeLocalValue(scheduleTime),
      })
      pushToast({ tone: 'success', title: 'Appointment scheduled' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Scheduling failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusy(false)
    }
  }

  const onCreateRecord = async () => {
    if (!selected || !recordSummary.trim()) return
    setBusy(true)
    try {
      await createCounsellingRecord(selected.referral_id, {
        counsellor_id: session?.username ?? assignId.trim(),
        session_date: fromDatetimeLocalValue(toDatetimeLocalValue()),
        session_summary: recordSummary.trim(),
        follow_up_required: followUpRequired,
        follow_up_date: followUpRequired
          ? fromDatetimeLocalValue(followUpDate)
          : null,
      })
      setRecordOpen(false)
      setRecordSummary('')
      pushToast({
        tone: 'success',
        title: 'Counselling record created',
        message: 'Confidential session details were saved securely.',
      })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Record creation failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setBusy(false)
    }
  }

  const onCreateAccommodation = async () => {
    if (!selected || !accType.trim() || !accContact.trim()) return
    setBusy(true)
    try {
      await createAccommodation(selected.referral_id, {
        accommodation_type: accType.trim(),
        academic_contact: accContact.trim(),
      })
      setAccOpen(false)
      setAccType('')
      setAccContact('')
      pushToast({ tone: 'success', title: 'Accommodation request created' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Accommodation request failed',
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
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <PrivacyChip>Authorised access only</PrivacyChip>
      </header>

      <div className="toolbar">
        <div className="toolbar-group">
          <Input
            aria-label="Search referrals"
            placeholder="Search by referral, student, or counsellor"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ minWidth: 260 }}
          />
          <Select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as 'all' | ReferralStatus)}
            style={{ width: 180 }}
          >
            <option value="all">All statuses</option>
            <option value="pending">pending</option>
            <option value="assigned">assigned</option>
            <option value="in_progress">in_progress</option>
            <option value="completed">completed</option>
          </Select>
        </div>
        <Button type="button" variant="secondary" onClick={() => void load()}>
          Refresh
        </Button>
      </div>

      {loading ? (
        <Skeleton height={240} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load referrals">
          {error}
        </Alert>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No referrals currently available"
          description="No referrals match this view. New routed requests will appear here."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Referral</th>
                <th>Student</th>
                <th>Source</th>
                <th>Support priority</th>
                <th>Status</th>
                <th>Assigned</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((referral) => (
                <tr
                  key={referral.referral_id}
                  className="is-clickable"
                  onClick={() => openReferral(referral)}
                >
                  <td>{referral.referral_id}</td>
                  <td>{referral.student_id}</td>
                  <td>{titleCase(referral.source)}</td>
                  <td>
                    <UrgencyBadge urgency={referral.urgency} />
                  </td>
                  <td>
                    <StatusBadge status={referral.status} />
                  </td>
                  <td>{referral.assigned_counsellor ?? '—'}</td>
                  <td>{formatDateTime(referral.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Drawer
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        title={selected?.referral_id ?? 'Referral'}
        description="Referral workflow details"
      >
        {selected ? (
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div className="grid-2">
              <div>
                <div className="field-label">Student</div>
                <div>{selected.student_id}</div>
              </div>
              <div>
                <div className="field-label">Source</div>
                <div>{titleCase(selected.source)}</div>
              </div>
              <div>
                <div className="field-label">Support priority</div>
                <UrgencyBadge urgency={selected.urgency} />
              </div>
              <div>
                <div className="field-label">Status</div>
                <StatusBadge status={selected.status} />
              </div>
            </div>

            {canManage ? (
              <>
                <Field label="Assign counsellor" htmlFor="assign-counsellor">
                  <Input
                    id="assign-counsellor"
                    value={assignId}
                    onChange={(e) => setAssignId(e.target.value)}
                  />
                </Field>
                <Button type="button" loading={busy} onClick={() => void onAssign()}>
                  Assign counsellor
                </Button>

                <Field label="Update status" htmlFor="referral-status">
                  <Select
                    id="referral-status"
                    value={statusValue}
                    onChange={(e) => setStatusValue(e.target.value as ReferralStatus)}
                  >
                    <option value="pending">pending</option>
                    <option value="assigned">assigned</option>
                    <option value="in_progress">in_progress</option>
                    <option value="completed">completed</option>
                  </Select>
                </Field>
                <Button type="button" variant="secondary" loading={busy} onClick={() => void onStatus()}>
                  Save status
                </Button>

                <Field label="Schedule appointment" htmlFor="appointment-time">
                  <Input
                    id="appointment-time"
                    type="datetime-local"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                  />
                </Field>
                <Button type="button" variant="secondary" loading={busy} onClick={() => void onSchedule()}>
                  Schedule session
                </Button>

                <Button type="button" variant="secondary" onClick={() => setAccOpen(true)}>
                  Request academic accommodation
                </Button>
              </>
            ) : null}

            {canRecord ? (
              <Button type="button" onClick={() => setRecordOpen(true)}>
                Create counselling record
              </Button>
            ) : null}
          </div>
        ) : null}
      </Drawer>

      <Dialog
        open={recordOpen}
        onClose={() => setRecordOpen(false)}
        title="Create confidential counselling record"
        description="Session narrative is restricted and will not appear in notifications."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setRecordOpen(false)}>
              Cancel
            </Button>
            <Button type="button" loading={busy} onClick={() => void onCreateRecord()}>
              Save record
            </Button>
          </>
        }
      >
        <div style={{ display: 'grid', gap: '0.8rem' }}>
          <Alert tone="warning" title="Confidential counselling record">
            Only authorised counsellors should enter session information.
          </Alert>
          <Field label="Session summary" htmlFor="session-summary">
            <Textarea
              id="session-summary"
              value={recordSummary}
              onChange={(e) => setRecordSummary(e.target.value)}
            />
          </Field>
          <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={followUpRequired}
              onChange={(e) => setFollowUpRequired(e.target.checked)}
            />
            Follow-up required
          </label>
          {followUpRequired ? (
            <Field label="Follow-up date" htmlFor="follow-up-date">
              <Input
                id="follow-up-date"
                type="datetime-local"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
              />
            </Field>
          ) : null}
        </div>
      </Dialog>

      <Dialog
        open={accOpen}
        onClose={() => setAccOpen(false)}
        title="Request academic accommodation"
        description="Academic contacts receive accommodation details only — not counselling reasons."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setAccOpen(false)}>
              Cancel
            </Button>
            <Button type="button" loading={busy} onClick={() => void onCreateAccommodation()}>
              Create request
            </Button>
          </>
        }
      >
        <div style={{ display: 'grid', gap: '0.8rem' }}>
          <Field label="Accommodation type" htmlFor="acc-type">
            <Input
              id="acc-type"
              value={accType}
              onChange={(e) => setAccType(e.target.value)}
            />
          </Field>
          <Field label="Academic contact" htmlFor="acc-contact">
            <Input
              id="acc-contact"
              value={accContact}
              onChange={(e) => setAccContact(e.target.value)}
            />
          </Field>
        </div>
      </Dialog>
    </div>
  )
}
