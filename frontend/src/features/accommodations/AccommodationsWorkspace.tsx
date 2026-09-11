import { useEffect, useState } from 'react'
import {
  listAccommodations,
  updateAccommodationStatus,
} from '../../api/accommodations'
import { ApiError, type AcademicAccommodation } from '../../types/api'
import { Alert, EmptyState, PrivacyChip, Skeleton } from '../../components/ui/Feedback'
import { Select } from '../../components/ui/Field'
import { useToast } from '../../components/ui/Toast'
import { formatDate, formatDateTime } from '../../utils/format'

const STATUSES = ['requested', 'approved', 'rejected', 'completed'] as const

export function AccommodationsWorkspace({
  canUpdateStatus = false,
}: {
  canUpdateStatus?: boolean
}) {
  const { pushToast } = useToast()
  const [items, setItems] = useState<AcademicAccommodation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setItems(await listAccommodations())
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'Unable to load accommodations.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const onStatus = async (id: string, status: string) => {
    setBusyId(id)
    try {
      const next = await updateAccommodationStatus(id, { status })
      setItems((current) =>
        current.map((item) =>
          item.accommodation_id === next.accommodation_id ? next : item,
        ),
      )
      pushToast({ tone: 'success', title: 'Accommodation status updated' })
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Status update failed',
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
          <h1>Academic accommodations</h1>
          <p>
            Privacy-preserving coordination of academic arrangements. Counselling
            reasons are not included in this view.
          </p>
        </div>
        <PrivacyChip>Academic information only</PrivacyChip>
      </header>

      <Alert tone="info" title="Separated from counselling content">
        This workspace shows accommodation type, academic contact, dates, and
        status. It does not display counselling session notes or referral reasons.
      </Alert>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load accommodations">
          {error}
        </Alert>
      ) : items.length === 0 ? (
        <EmptyState
          title="No accommodation requests"
          description="Academic accommodation requests will appear here when created from an assigned referral."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Accommodation</th>
                <th>Student</th>
                <th>Type</th>
                <th>Academic contact</th>
                <th>Start</th>
                <th>End</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.accommodation_id}>
                  <td>{item.accommodation_id}</td>
                  <td>{item.student_id}</td>
                  <td>{item.accommodation_type}</td>
                  <td>{item.academic_contact}</td>
                  <td>{formatDate(item.start_date)}</td>
                  <td>{formatDate(item.end_date)}</td>
                  <td>
                    {canUpdateStatus ? (
                      <Select
                        aria-label={`Status for ${item.accommodation_id}`}
                        value={item.status}
                        disabled={busyId === item.accommodation_id}
                        onChange={(e) => void onStatus(item.accommodation_id, e.target.value)}
                      >
                        {STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </Select>
                    ) : (
                      item.status
                    )}
                  </td>
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
