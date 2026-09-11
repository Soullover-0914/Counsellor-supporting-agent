import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { signup } from '../api/auth'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME } from '../auth/roles'
import { ApiError } from '../types/api'
import { Button } from '../components/ui/Button'
import { Field, Input } from '../components/ui/Field'
import { Alert } from '../components/ui/Feedback'
import { AuthFlowVisual } from '../components/auth/AuthFlowVisual'
import '../components/auth/AuthFlowVisual.css'

export function SignupPage() {
  const { isAuthenticated, session, isBootstrapping } = useAuth()
  const reduceMotion = useReducedMotion()

  const [form, setForm] = useState({
    student_name: '',
    student_id: '',
    email: '',
    username: '',
    branch: '',
    year: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!isBootstrapping && isAuthenticated && session) {
    return (
      <Navigate
        to={session.mustChangePassword ? '/change-password' : ROLE_HOME[session.role]}
        replace
      />
    )
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const nextErrors: Record<string, string> = {}
    if (!form.student_name.trim()) nextErrors.student_name = 'Student name is required.'
    if (!form.student_id.trim()) nextErrors.student_id = 'Student ID is required.'
    if (!form.email.trim()) nextErrors.email = 'Institutional email is required.'
    if (!form.username.trim()) nextErrors.username = 'Username is required.'
    if (!form.branch.trim()) nextErrors.branch = 'Branch or department is required.'
    if (!form.year.trim()) nextErrors.year = 'Year is required.'
    setErrors(nextErrors)
    setFormError(null)
    setSuccess(null)
    if (Object.keys(nextErrors).length) return

    setLoading(true)
    try {
      const response = await signup({
        student_name: form.student_name.trim(),
        student_id: form.student_id.trim(),
        email: form.email.trim(),
        username: form.username.trim(),
        branch: form.branch.trim(),
        year: form.year.trim(),
      })
      setSuccess(response.message)
      setForm({
        student_name: '',
        student_id: '',
        email: '',
        username: '',
        branch: '',
        year: '',
      })
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : 'Registration could not be submitted.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-visual-pane">
        <AuthFlowVisual />
      </div>

      <motion.section
        className="auth-panel"
        initial={reduceMotion ? false : { opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: reduceMotion ? 0 : 0.35, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="login-brand">
          <div className="brand-mark" aria-hidden>
            66
          </div>
          <div>
            <h1>Student registration</h1>
            <p className="login-subtitle">Agent 66 Counselling Support System</p>
          </div>
        </div>

        <Alert tone="info" icon={<Shield size={18} aria-hidden />}>
          Registration requests are reviewed by an authorised administrator. Your
          account will not be activated until approval.
        </Alert>

        <Alert tone="info">
          Agent 66 connects students with authorised human support. It does not
          provide counselling or diagnosis.
        </Alert>

        <form className="login-form" onSubmit={onSubmit} noValidate>
          <Field label="Student name" htmlFor="student_name" error={errors.student_name}>
            <Input
              id="student_name"
              value={form.student_name}
              invalid={Boolean(errors.student_name)}
              onChange={(e) => setForm((f) => ({ ...f, student_name: e.target.value }))}
            />
          </Field>
          <Field label="Student ID" htmlFor="student_id" error={errors.student_id}>
            <Input
              id="student_id"
              value={form.student_id}
              invalid={Boolean(errors.student_id)}
              onChange={(e) => setForm((f) => ({ ...f, student_id: e.target.value }))}
            />
          </Field>
          <Field label="Institutional email" htmlFor="email" error={errors.email}>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={form.email}
              invalid={Boolean(errors.email)}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </Field>
          <Field label="Username" htmlFor="signup_username" error={errors.username}>
            <Input
              id="signup_username"
              autoComplete="username"
              value={form.username}
              invalid={Boolean(errors.username)}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            />
          </Field>
          <Field label="Branch / department" htmlFor="branch" error={errors.branch}>
            <Input
              id="branch"
              value={form.branch}
              invalid={Boolean(errors.branch)}
              onChange={(e) => setForm((f) => ({ ...f, branch: e.target.value }))}
            />
          </Field>
          <Field label="Year" htmlFor="year" error={errors.year}>
            <Input
              id="year"
              value={form.year}
              invalid={Boolean(errors.year)}
              onChange={(e) => setForm((f) => ({ ...f, year: e.target.value }))}
            />
          </Field>

          {formError ? (
            <Alert tone="danger" title="Registration unsuccessful">
              {formError}
            </Alert>
          ) : null}
          {success ? (
            <Alert tone="success" title="Registration submitted">
              {success}
            </Alert>
          ) : null}

          <Button type="submit" loading={loading} className="login-submit">
            Submit registration request
          </Button>
        </form>

        <div className="auth-switch">
          <span>Already registered?</span>
          <Link to="/login">Sign in</Link>
        </div>

        <div className="login-links">
          <Link to="/privacy">Privacy Policy</Link>
          <Link to="/terms">Terms of Use</Link>
        </div>
      </motion.section>
    </div>
  )
}
