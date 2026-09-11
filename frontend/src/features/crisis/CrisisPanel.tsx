import type { CrisisResource } from '../../types/api'
import { AlertTriangle, MapPin, Phone, Clock } from 'lucide-react'

export function CrisisPanel({
  reason,
  recommendedAction,
  resources,
}: {
  reason: string
  recommendedAction: string
  resources: CrisisResource[] | null | undefined
}) {
  return (
    <section className="crisis-panel" role="alert" aria-live="assertive">
      <div style={{ display: 'flex', gap: '0.7rem', alignItems: 'flex-start' }}>
        <AlertTriangle size={22} aria-hidden color="var(--crisis)" />
        <div>
          <h2>Immediate human support required</h2>
          <p style={{ marginTop: '0.55rem', color: 'var(--ink-secondary)' }}>
            {reason}
          </p>
          <p style={{ marginTop: '0.55rem', fontWeight: 600 }}>
            {recommendedAction}
          </p>
          <p style={{ marginTop: '0.75rem', color: 'var(--ink-secondary)' }}>
            This request has been treated as a high-priority safety escalation.
            It does not enter the normal referral queue delay. Please use the
            institution-approved contacts below and follow local emergency
            procedures if anyone is in immediate danger.
          </p>
        </div>
      </div>

      <div style={{ marginTop: '1.15rem' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '0.65rem' }}>
          Approved crisis support contacts
        </h3>
        {resources && resources.length > 0 ? (
          <div className="grid-2">
            {resources.map((resource) => (
              <article key={resource.resource_id} className="card">
                <h4 className="card-title">{resource.name}</h4>
                {resource.contact ? (
                  <p style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                    <Phone size={15} aria-hidden />
                    <span>{resource.contact}</span>
                  </p>
                ) : null}
                {resource.availability ? (
                  <p
                    className="card-meta"
                    style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', marginTop: '0.35rem' }}
                  >
                    <Clock size={15} aria-hidden />
                    {resource.availability}
                  </p>
                ) : null}
                {resource.location ? (
                  <p
                    className="card-meta"
                    style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', marginTop: '0.35rem' }}
                  >
                    <MapPin size={15} aria-hidden />
                    {resource.location}
                  </p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--ink-secondary)' }}>
            No approved crisis contacts were returned by the system at this time.
            Contact your institution&apos;s designated emergency or counselling
            authority immediately through established local channels.
          </p>
        )}
      </div>
    </section>
  )
}
