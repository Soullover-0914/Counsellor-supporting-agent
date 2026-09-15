import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Shield } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { useAuth } from '../auth/AuthContext'
import { ROLE_HOME } from '../auth/roles'
import { ApiError } from '../types/api'
import { Button } from '../components/ui/Button'
import { Field, Input } from '../components/ui/Field'
import { Alert } from '../components/ui/Feedback'
import { AuthFlowVisual } from '../components/auth/AuthFlowVisual'
import '../components/auth/AuthFlowVisual.css'

export function LoginPage() {
  const { login, isAuthenticated, session, isBootstrapping } = useAuth()
  const navigate = useNavigate()
  const reduceMotion = useReducedMotion()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{
    username?: string
    password?: string
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!isBootstrapping && isAuthenticated && session) {
    if (session.mustChangePassword) {
      return <Navigate to="/change-password" replace />
    }

    return <Navigate to={ROLE_HOME[session.role]} replace />
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()

    const nextErrors: typeof errors = {}

    if (!username.trim()) {
      nextErrors.username = 'Username is required.'
    }

    if (!password) {
      nextErrors.password = 'Password is required.'
    }

    setErrors(nextErrors)
    setFormError(null)

    if (Object.keys(nextErrors).length) {
      return
    }

    setLoading(true)

    try {
      const next = await login(username.trim(), password)

      navigate(
        next.mustChangePassword
          ? '/change-password'
          : ROLE_HOME[next.role],
        { replace: true },
      )
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.message)
      } else {
        setFormError(
          'Sign-in could not be completed. Please try again.',
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const openFacultyDemo = () => {
    navigate('/faculty-demo')
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
        transition={{
          duration: reduceMotion ? 0 : 0.35,
          ease: [0.22, 1, 0.36, 1],
        }}
      >
        <div className="login-brand">
          <div className="brand-mark" aria-hidden>
            66
          </div>

          <div>
            <h1>Agent 66</h1>
            <p className="login-subtitle">
              Counselling Support System
            </p>
          </div>
        </div>

        <p className="login-message">
          Connecting students with authorised human support while
          protecting privacy and maintaining appropriate institutional
          safeguards.
        </p>

        <Alert
          tone="info"
          icon={<Shield size={18} aria-hidden />}
        >
          This system routes support requests to authorised personnel.
          It does not provide counselling, diagnosis, or emergency
          response by itself.
        </Alert>

        <form
          className="login-form"
          onSubmit={onSubmit}
          noValidate
        >
          <Field
            label="Username"
            htmlFor="username"
            error={errors.username}
          >
            <Input
              id="username"
              name="username"
              autoComplete="username"
              value={username}
              invalid={Boolean(errors.username)}
              onChange={(event) =>
                setUsername(event.target.value)
              }
            />
          </Field>

          <Field
            label="Password"
            htmlFor="password"
            error={errors.password}
          >
            <div className="input-affix">
              <Input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                invalid={Boolean(errors.password)}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
              />

              <button
                type="button"
                className="input-affix-btn"
                aria-label={
                  showPassword
                    ? 'Hide password'
                    : 'Show password'
                }
                onClick={() =>
                  setShowPassword((value) => !value)
                }
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>
            </div>
          </Field>

          {formError ? (
            <Alert
              tone="danger"
              title="Sign-in unsuccessful"
            >
              {formError}
            </Alert>
          ) : null}

          <Button
            type="submit"
            loading={loading}
            className="login-submit"
          >
            Sign in securely
          </Button>
        </form>

        <div className="auth-switch">
          <span>New student?</span>
          <Link to="/signup">Request registration</Link>
        </div>

        <div className="faculty-demo-entry">
          <button
            type="button"
            className="faculty-demo-button"
            onClick={openFacultyDemo}
          >
            Faculty Evaluation Demo
          </button>

          <p className="faculty-demo-note">
            Read-only demonstration using simulated data
          </p>
        </div>

        <div className="login-links">
          <Link to="/privacy">Privacy Policy</Link>
          <Link to="/terms">Terms of Use</Link>
        </div>
      </motion.section>
    </div>
  )
}