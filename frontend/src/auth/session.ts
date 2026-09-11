import type { AuthSession, UserRole } from '../types/api'

const STORAGE_KEY = 'agent66.session'

interface TokenPayload {
  username?: string
  role?: string
  student_id?: string | null
  must_change_password?: boolean
  exp?: number
}

export function decodeTokenPayload(token: string): TokenPayload | null {
  try {
    const [encoded] = token.split('.')
    if (!encoded) return null

    const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    const json = atob(padded)
    return JSON.parse(json) as TokenPayload
  } catch {
    return null
  }
}

export function isTokenExpired(token: string, skewSeconds = 30): boolean {
  const payload = decodeTokenPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 <= Date.now() + skewSeconds * 1000
}

export function buildSession(
  accessToken: string,
  tokenType: string,
  username: string,
  role: UserRole,
  mustChangePassword?: boolean,
): AuthSession {
  const payload = decodeTokenPayload(accessToken)
  return {
    accessToken,
    tokenType,
    username,
    role,
    studentId: payload?.student_id ?? null,
    mustChangePassword:
      mustChangePassword ?? Boolean(payload?.must_change_password),
  }
}

export function loadStoredSession(): AuthSession | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthSession
    if (!parsed?.accessToken || !parsed.username || !parsed.role) return null
    if (isTokenExpired(parsed.accessToken)) {
      clearStoredSession()
      return null
    }
    const payload = decodeTokenPayload(parsed.accessToken)
    return {
      ...parsed,
      mustChangePassword:
        parsed.mustChangePassword ?? Boolean(payload?.must_change_password),
    }
  } catch {
    clearStoredSession()
    return null
  }
}

export function storeSession(session: AuthSession) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession() {
  sessionStorage.removeItem(STORAGE_KEY)
}
