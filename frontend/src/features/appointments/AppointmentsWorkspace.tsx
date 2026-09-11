import { useEffect, useState } from 'react'
import { listAppointments } from '../../api/appointments'
import { ApiError, type Appointment } from '../../types/api'
import { Alert, EmptyState, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { formatDateTime } from '../../utils/format'

export function AppointmentsWorkspace() {
  const [items, setItems] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setItems(await listAppointments())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load appointments.')
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
          <h1>Appointments</h1>
          <p>Scheduled counselling sessions from the institutional calendar.</p>
        </div>
        <Button type="button" variant="secondary" onClick={() => void load()}>
          Refresh
        </Button>
      </header>

      {loading ? (
        <Skeleton height={220} />
      ) : error ? (
        <Alert tone="danger" title="Unable to load appointments">
          {error}
        </Alert>
      ) : items.length === 0 ? (
        <EmptyState
          title="No upcoming appointments"
          description="Scheduled sessions will appear here once a referral has been assigned and booked."
        />
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Appointment</th>
                <th>Referral</th>
                <th>Student</th>
                <th>Counsellor</th>
                <th>When</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.appointment_id}>
                  <td>{item.appointment_id}</td>
                  <td>{item.referral_id}</td>
                  <td>{item.student_id}</td>
                  <td>{item.counsellor_id}</td>
                  <td>{formatDateTime(item.appointment_time)}</td>
                  <td>{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
