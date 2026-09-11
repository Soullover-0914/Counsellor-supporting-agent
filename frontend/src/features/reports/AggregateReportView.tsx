import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getAggregateReport } from '../../api/reports'
import { ApiError, type AggregateReport } from '../../types/api'
import { Alert, EmptyState, PrivacyChip, Skeleton } from '../../components/ui/Feedback'
import { Button } from '../../components/ui/Button'
import { FadeItem, Stagger } from '../../components/motion/PageTransition'

function toChartData(map: Record<string, number>) {
  return Object.entries(map).map(([name, value]) => ({ name, value }))
}

export function AggregateReportView() {
  const [report, setReport] = useState<AggregateReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setReport(await getAggregateReport())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load report.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const empty = useMemo(() => {
    if (!report) return true
    return (
      report.total_referrals === 0 &&
      report.total_counselling_records === 0 &&
      report.total_follow_ups === 0 &&
      report.total_accommodations === 0
    )
  }, [report])

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Aggregate reports</h1>
          <p>Anonymous institutional demand and workflow patterns.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <PrivacyChip>No individual counselling records</PrivacyChip>
          <Button type="button" variant="secondary" onClick={() => void load()}>
            Refresh
          </Button>
        </div>
      </header>

      {loading ? (
        <div className="grid-3">
          <Skeleton height={100} />
          <Skeleton height={100} />
          <Skeleton height={100} />
        </div>
      ) : error ? (
        <Alert tone="danger" title="Unable to load aggregate report">
          {error}
        </Alert>
      ) : !report || empty ? (
        <EmptyState
          title="No aggregate data available"
          description="Anonymous totals will appear here once referrals and related workflow activity exist."
        />
      ) : (
        <>
          <Stagger className="grid-3">
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Referrals</div>
                <div className="value">{report.total_referrals}</div>
              </div>
            </FadeItem>
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Counselling records</div>
                <div className="value">{report.total_counselling_records}</div>
              </div>
            </FadeItem>
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Follow-ups</div>
                <div className="value">{report.total_follow_ups}</div>
              </div>
            </FadeItem>
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Accommodations</div>
                <div className="value">{report.total_accommodations}</div>
              </div>
            </FadeItem>
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Privacy threshold</div>
                <div className="value">{report.privacy_threshold}</div>
              </div>
            </FadeItem>
            <FadeItem>
              <div className="stat-tile">
                <div className="label">Breakdown available</div>
                <div className="value" style={{ fontSize: '1.2rem', marginTop: '0.7rem' }}>
                  {report.breakdown_available ? 'Yes' : 'No'}
                </div>
              </div>
            </FadeItem>
          </Stagger>

          {report.breakdown_available ? (
            <div className="grid-2" style={{ marginTop: '0.25rem' }}>
              <ChartCard title="Referrals by support priority" data={toChartData(report.referral_by_urgency)} />
              <ChartCard title="Referrals by source" data={toChartData(report.referral_by_source)} />
              <ChartCard title="Referrals by status" data={toChartData(report.referral_by_status)} />
              <ChartCard title="Accommodations by type" data={toChartData(report.accommodation_by_type)} />
            </div>
          ) : (
            <Alert tone="info" title="Breakdown withheld">
              Detailed breakdowns are unavailable under the current privacy
              threshold settings.
            </Alert>
          )}
        </>
      )}
    </div>
  )
}

function ChartCard({
  title,
  data,
}: {
  title: string
  data: Array<{ name: string; value: number }>
}) {
  return (
    <section className="card">
      <h2 style={{ fontSize: '1.05rem', marginBottom: '0.75rem' }}>{title}</h2>
      {data.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No distribution data.</p>
      ) : (
        <div style={{ width: '100%', height: 240 }}>
          <ResponsiveContainer>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#65c2f5" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#65c2f5" radius={[4, 4, 0, 0]} isAnimationActive />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}
