import { useEffect, useMemo, useState } from 'react'
import {
  createResource,
  deactivateResource,
  listResources,
} from '../../api/resources'
import { ApiError, type WellbeingResource } from '../../types/api'
import { Button } from '../../components/ui/Button'
import { Field, Input, Select, Textarea } from '../../components/ui/Field'
import { Alert, EmptyState, PrivacyChip, Skeleton } from '../../components/ui/Feedback'
import { Dialog } from '../../components/ui/Overlay'
import { useToast } from '../../components/ui/Toast'
import { BookOpen, MapPin, Phone, Clock, ShieldAlert } from 'lucide-react'
import { FadeItem, Stagger } from '../../components/motion/PageTransition'

const TYPES = ['all', 'counselling', 'wellbeing', 'emergency', 'academic'] as const

export function ResourcesDirectory({
  canManage = false,
}: {
  canManage?: boolean
}) {
  const { pushToast } = useToast()
  const [resources, setResources] = useState<WellbeingResource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<(typeof TYPES)[number]>('all')
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({
    name: '',
    resource_type: 'wellbeing',
    description: '',
    contact: '',
    availability: '',
    location: '',
    emergency: false,
  })
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listResources()
      setResources(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load resources.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filtered = useMemo(() => {
    return resources.filter((resource) => {
      if (!resource.active) return false
      if (typeFilter === 'all') return true
      return resource.resource_type === typeFilter
    })
  }, [resources, typeFilter])

  const onCreate = async () => {
    if (!form.name.trim() || !form.description.trim()) {
      pushToast({
        tone: 'error',
        title: 'Missing information',
        message: 'Name and description are required.',
      })
      return
    }
    setSaving(true)
    try {
      await createResource({
        name: form.name.trim(),
        resource_type: form.resource_type,
        description: form.description.trim(),
        contact: form.contact.trim() || null,
        availability: form.availability.trim() || null,
        location: form.location.trim() || null,
        emergency: form.emergency,
      })
      setCreateOpen(false)
      setForm({
        name: '',
        resource_type: 'wellbeing',
        description: '',
        contact: '',
        availability: '',
        location: '',
        emergency: false,
      })
      pushToast({ tone: 'success', title: 'Resource added' })
      await load()
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Could not add resource',
        message: err instanceof ApiError ? err.message : undefined,
      })
    } finally {
      setSaving(false)
    }
  }

  const onDeactivate = async (resourceId: string) => {
    try {
      await deactivateResource(resourceId)
      pushToast({ tone: 'success', title: 'Resource deactivated' })
      await load()
    } catch (err) {
      pushToast({
        tone: 'error',
        title: 'Deactivation failed',
        message: err instanceof ApiError ? err.message : undefined,
      })
    }
  }

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>Support resources</h1>
          <p>Institution-approved wellbeing and support directory.</p>
        </div>
        {canManage ? (
          <Button type="button" onClick={() => setCreateOpen(true)}>
            Add resource
          </Button>
        ) : null}
      </header>

      <div className="toolbar">
        <div className="toolbar-group">
          <label htmlFor="resource-type" className="field-label">
            Resource type
          </label>
          <Select
            id="resource-type"
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(event.target.value as (typeof TYPES)[number])
            }
            style={{ width: 220 }}
          >
            {TYPES.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? 'All types' : type}
              </option>
            ))}
          </Select>
        </div>
        <PrivacyChip>Directory contacts only</PrivacyChip>
      </div>

      {loading ? (
        <div className="grid-2">
          <Skeleton height={140} />
          <Skeleton height={140} />
        </div>
      ) : error ? (
        <Alert tone="danger" title="Unable to load resources">
          {error}
        </Alert>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No resources available"
          description="No active wellbeing resources were returned for this view."
        />
      ) : (
        <Stagger className="grid-2">
          {filtered.map((resource) => (
            <FadeItem key={resource.resource_id}>
              <article className="card card-interactive">
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem' }}>
                  <h2 className="card-title" style={{ display: 'flex', gap: '0.45rem', alignItems: 'center' }}>
                    <BookOpen size={18} aria-hidden />
                    {resource.name}
                  </h2>
                  {resource.emergency ? (
                    <span className="badge badge-danger" style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                      <ShieldAlert size={12} aria-hidden />
                      Emergency
                    </span>
                  ) : (
                    <span className="badge badge-neutral">{resource.resource_type}</span>
                  )}
                </div>
                <p style={{ marginTop: '0.55rem', color: 'var(--ink-secondary)' }}>
                  {resource.description}
                </p>
                <div style={{ marginTop: '0.75rem', display: 'grid', gap: '0.35rem' }}>
                  {resource.contact ? (
                    <p className="card-meta" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <Phone size={14} aria-hidden /> {resource.contact}
                    </p>
                  ) : null}
                  {resource.availability ? (
                    <p className="card-meta" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <Clock size={14} aria-hidden /> {resource.availability}
                    </p>
                  ) : null}
                  {resource.location ? (
                    <p className="card-meta" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <MapPin size={14} aria-hidden /> {resource.location}
                    </p>
                  ) : null}
                </div>
                {canManage ? (
                  <div style={{ marginTop: '0.9rem' }}>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => void onDeactivate(resource.resource_id)}
                    >
                      Deactivate
                    </Button>
                  </div>
                ) : null}
              </article>
            </FadeItem>
          ))}
        </Stagger>
      )}

      <Dialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Add wellbeing resource"
        description="Only institution-approved contacts should be added."
        footer={
          <>
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="button" loading={saving} onClick={() => void onCreate()}>
              Save resource
            </Button>
          </>
        }
      >
        <div style={{ display: 'grid', gap: '0.8rem' }}>
          <Field label="Name" htmlFor="res-name">
            <Input
              id="res-name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </Field>
          <Field label="Type" htmlFor="res-type">
            <Select
              id="res-type"
              value={form.resource_type}
              onChange={(e) => setForm((f) => ({ ...f, resource_type: e.target.value }))}
            >
              <option value="counselling">counselling</option>
              <option value="wellbeing">wellbeing</option>
              <option value="emergency">emergency</option>
              <option value="academic">academic</option>
            </Select>
          </Field>
          <Field label="Description" htmlFor="res-desc">
            <Textarea
              id="res-desc"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            />
          </Field>
          <Field label="Contact" htmlFor="res-contact">
            <Input
              id="res-contact"
              value={form.contact}
              onChange={(e) => setForm((f) => ({ ...f, contact: e.target.value }))}
            />
          </Field>
          <Field label="Availability" htmlFor="res-availability">
            <Input
              id="res-availability"
              value={form.availability}
              onChange={(e) => setForm((f) => ({ ...f, availability: e.target.value }))}
            />
          </Field>
          <Field label="Location" htmlFor="res-location">
            <Input
              id="res-location"
              value={form.location}
              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            />
          </Field>
          <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={form.emergency}
              onChange={(e) => setForm((f) => ({ ...f, emergency: e.target.checked }))}
            />
            Mark as emergency resource
          </label>
        </div>
      </Dialog>
    </div>
  )
}
