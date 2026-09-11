import { useMemo, useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME } from '../auth/roles'
import { ApiError } from '../types/api'
import { Button } from '../components/ui/Button'
import { Field, Input } from '../components/ui/Field'
import { Alert } from '../components/ui/Feedback'
import { AuthFlowVisual } from '../components/auth/AuthFlowVisual'
import '../components/auth/AuthFlowVisual.css'

function validatePassword(password: string): string | null {
  if (password.length < 10) return 'Password must be at least 10 characters long.'
  if (!/[A-Z]/.test(password)) return 'Password must include at least one uppercase letter.'
  if (!/[a-z]/.test(password)) return 'Password must include at least one lowercase letter.'
  if (!/[0-9]/.test(password)) return 'Password must include at least one digit.'
  return null
}

export function ChangePasswordPage() {
  const { session, isAuthenticated, isBootstrapping, completePasswordChange, logout } =
    useAuth()
  const navigate = useNavigate()

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [acknowledge, setAcknowledge] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const passwordError = useMemo(() => validatePassword(newPassword), [newPassword])
  const canSubmit =
    !passwordError &&
    newPassword === confirmPassword &&
    acknowledge &&
    newPassword.length > 0

  if (isBootstrapping) return null

  if (!isAuthenticated || !session) {
    return <Navigate to="/login" replace />
  }

  if (!session.mustChangePassword && !success) {
    return <Navigate to={ROLE_HOME[session.role]} replace />
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (!canSubmit) return

    setLoading(true)
    try {
      const next = await completePasswordChange({
        new_password: newPassword,
        confirm_password: confirmPassword,
        acknowledge_permanent: true,
      })
      setSuccess(
        'Your password has been changed successfully. This password cannot be changed again through the initial password-change workflow.',
      )
      window.setTimeout(() => {
        navigate(ROLE_HOME[next.role], { replace: true })
      }, 1600)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Password change could not be completed.',
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
      <section className="auth-panel">
        <h1>Change temporary password</h1>
        <Alert tone="warning" icon={<ShieldAlert size={18} aria-hidden />}>
          Important: You can change your temporary password only once. After you
          confirm your new password, this password cannot be changed again through
          this workflow.
        </Alert>

        <form className="login-form" onSubmit={onSubmit} noValidate>
          <Field
            label="New password"
            htmlFor="new_password"
            error={newPassword ? passwordError ?? undefined : undefined}
            hint="At least 10 characters, with uppercase, lowercase, and a digit."
          >
            <Input
              id="new_password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
          </Field>
          <Field
            label="Confirm new password"
            htmlFor="confirm_password"
            error={
              confirmPassword && confirmPassword !== newPassword
                ? 'Passwords do not match.'
                : undefined
            }
          >
            <Input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </Field>

          <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-start' }}>
            <input
              type="checkbox"
              checked={acknowledge}
              onChange={(e) => setAcknowledge(e.target.checked)}
              style={{ marginTop: '0.2rem' }}
            />
            <span>I understand that this password change is permanent.</span>
          </label>

          {error ? (
            <Alert tone="danger" title="Password change unsuccessful">
              {error}
            </Alert>
          ) : null}
          {success ? (
            <Alert tone="success" title="Password updated">
              {success}
            </Alert>
          ) : null}

          <Button type="submit" loading={loading} disabled={!canSubmit}>
            Confirm password change
          </Button>
          <Button type="button" variant="secondary" onClick={logout}>
            Sign out
          </Button>
        </form>
      </section>
    </div>
  )
}
