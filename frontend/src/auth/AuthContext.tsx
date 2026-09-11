import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  changePassword as changePasswordRequest,
  login as loginRequest,
} from '../api/auth'
import { configureApiClient } from '../api/client'
import { isRole } from './roles'
import {
  buildSession,
  clearStoredSession,
  loadStoredSession,
  storeSession,
} from './session'
import type { AuthSession, ChangePasswordRequest, UserRole } from '../types/api'

interface AuthContextValue {
  session: AuthSession | null
  isAuthenticated: boolean
  isBootstrapping: boolean
  login: (username: string, password: string) => Promise<AuthSession>
  logout: () => void
  completePasswordChange: (payload: ChangePasswordRequest) => Promise<AuthSession>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  const logout = useCallback(() => {
    clearStoredSession()
    setSession(null)
  }, [])

  useEffect(() => {
    configureApiClient({
      getAccessToken: () =>
        session?.accessToken ?? loadStoredSession()?.accessToken ?? null,
      onUnauthorized: () => {
        clearStoredSession()
        setSession(null)
      },
    })
  }, [session])

  useEffect(() => {
    const stored = loadStoredSession()
    setSession(stored)
    setIsBootstrapping(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const response = await loginRequest({ username, password })
    if (!isRole(response.role)) {
      throw new Error('Unrecognized account role returned by the server.')
    }

    const next = buildSession(
      response.access_token,
      response.token_type,
      response.username,
      response.role as UserRole,
      Boolean(response.must_change_password),
    )
    storeSession(next)
    setSession(next)
    return next
  }, [])

  const completePasswordChange = useCallback(
    async (payload: ChangePasswordRequest) => {
      const response = await changePasswordRequest(payload)
      if (!isRole(response.role)) {
        throw new Error('Unrecognized account role returned by the server.')
      }
      const next = buildSession(
        response.access_token,
        response.token_type,
        response.username,
        response.role as UserRole,
        false,
      )
      storeSession(next)
      setSession(next)
      return next
    },
    [],
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      isAuthenticated: Boolean(session),
      isBootstrapping,
      login,
      logout,
      completePasswordChange,
    }),
    [session, isBootstrapping, login, logout, completePasswordChange],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
