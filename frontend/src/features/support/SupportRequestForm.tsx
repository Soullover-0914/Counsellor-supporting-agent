import { useMemo, useState, type FormEvent } from 'react'
import { analyzeCounsellingRequest } from '../../api/analyze'
import { useAuth } from '../../auth/AuthContext'
import { ApiError, type CounsellingResponse, type ReferralSource } from '../../types/api'
import { Button } from '../../components/ui/Button'
import { Field, Input, Select, Textarea } from '../../components/ui/Field'
import { Alert } from '../../components/ui/Feedback'
import { UrgencyBadge } from '../../components/ui/StatusBadges'
import { CrisisPanel } from '../crisis/CrisisPanel'
import { titleCase } from '../../utils/format'

interface SupportRequestFormProps {
  defaultSource: ReferralSource
  allowStudentIdEdit?: boolean
  heading?: string
  description?: string
}

export function SupportRequestForm({
  defaultSource,
  allowStudentIdEdit = false,
  heading = 'Request support',
  description = 'Agent 66 does not provide counselling or diagnosis. Submissions are reviewed and routed to authorised human support personnel.',
}: SupportRequestFormProps) {
  const { session } = useAuth()
  const presetStudentId = session?.studentId ?? ''

  const [studentId, setStudentId] = useState(presetStudentId)
  const [source, setSource] = useState<ReferralSource>(defaultSource)
  const [message, setMessage] = useState('')
  const [consent, setConsent] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CounsellingResponse | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const studentIdLocked = Boolean(presetStudentId) && !allowStudentIdEdit

  const priorityLabel = useMemo(() => {
    if (!result) return ''
    if (result.immediate_escalation) return 'Immediate escalation'
    if (result.route_to_human) return 'Human review recommended'
    return 'No immediate routing indicated'
  }, [result])

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const nextErrors: Record<string, string> = {}
    if (!studentId.trim()) nextErrors.student_id = 'Student identifier is required.'
    if (!message.trim()) nextErrors.message = 'Please describe the support need.'
    setErrors(nextErrors)
    setSubmitError(null)
    if (Object.keys(nextErrors).length) return

    setLoading(true)
    setResult(null)
    try {
      const response = await analyzeCounsellingRequest({
        student_id: studentId.trim(),
        source,
        message: message.trim(),
        consent,
      })
      setResult(response)
    } catch (error) {
      setSubmitError(
        error instanceof ApiError
          ? error.message
          : 'The support request could not be submitted.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-page">
      <header className="page-header">
        <div>
          <h1>{heading}</h1>
          <p>{description}</p>
        </div>
      </header>

      <form className="card" onSubmit={onSubmit} noValidate style={{ display: 'grid', gap: '0.9rem' }}>
        <Field
          label="Student identifier"
          htmlFor="student_id"
          error={errors.student_id}
          hint={
            studentIdLocked
              ? 'Using the student identity associated with your signed-in account.'
              : 'Enter the institutional student identifier for this request.'
          }
        >
          <Input
            id="student_id"
            value={studentId}
            readOnly={studentIdLocked}
            invalid={Boolean(errors.student_id)}
            onChange={(event) => setStudentId(event.target.value)}
          />
        </Field>

        <Field label="Referral source" htmlFor="source">
          <Select
            id="source"
            value={source}
            onChange={(event) => setSource(event.target.value as ReferralSource)}
          >
            <option value="self_referral">Self referral</option>
            <option value="mentor_referral">Mentor referral</option>
            <option value="faculty_referral">Faculty referral</option>
          </Select>
        </Field>

        <Field
          label="Support message"
          htmlFor="message"
          error={errors.message}
          hint="Share what support is needed. Do not include unnecessary sensitive third-party information."
        >
          <Textarea
            id="message"
            value={message}
            invalid={Boolean(errors.message)}
            onChange={(event) => setMessage(event.target.value)}
          />
        </Field>

        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start' }}>
          <input
            type="checkbox"
            checked={consent}
            onChange={(event) => setConsent(event.target.checked)}
            style={{ marginTop: '0.2rem' }}
          />
          <span>
            I consent to routing this request to authorised institutional support
            personnel for human review. Consent is required for standard referral
            workflows. Immediate safety concerns are escalated regardless.
          </span>
        </label>

        {submitError ? (
          <Alert tone="danger" title="Submission unsuccessful">
            {submitError}
          </Alert>
        ) : null}

        <div>
          <Button type="submit" loading={loading}>
            Submit support request
          </Button>
        </div>
      </form>

      {result ? (
        result.immediate_escalation ? (
          <CrisisPanel
            reason={result.reason}
            recommendedAction={result.recommended_action}
            resources={result.crisis_resources}
          />
        ) : (
          <section className="card" aria-live="polite">
            <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.25rem' }}>Request outcome</h2>
              <UrgencyBadge urgency={result.urgency} />
            </div>
            <p style={{ marginTop: '0.7rem', fontWeight: 600 }}>{priorityLabel}</p>
            <p style={{ marginTop: '0.45rem', color: 'var(--ink-secondary)' }}>
              Support priority: {titleCase(result.urgency)}. This is not a diagnosis.
            </p>
            <p style={{ marginTop: '0.7rem', color: 'var(--ink-secondary)' }}>{result.reason}</p>
            <p style={{ marginTop: '0.55rem' }}>{result.recommended_action}</p>
            {result.route_to_human ? (
              <Alert tone="success" title="Routed for human support" >
                Your request has been directed for authorised human review. Referral
                identifiers are managed by support staff and are not always returned
                in this confirmation view.
              </Alert>
            ) : result.status === 'consent_required' ? (
              <Alert tone="warning" title="Consent required">
                Provide consent to continue with a standard counselling referral
                workflow, unless this is an immediate safety concern.
              </Alert>
            ) : (
              <Alert tone="info" title="Next steps">
                No immediate referral routing was indicated. You may still browse
                approved wellbeing resources or submit again if circumstances change.
              </Alert>
            )}
          </section>
        )
      ) : null}
    </div>
  )
}
