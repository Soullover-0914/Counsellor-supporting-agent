import { ApiError, type ApiErrorCode } from '../types/api'

const configuredBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim()

/** Empty base uses the Vite proxy in development. */
export const API_BASE_URL = configuredBase ?? ''

type TokenGetter = () => string | null
type UnauthorizedHandler = () => void

let getAccessToken: TokenGetter = () => null
let onUnauthorized: UnauthorizedHandler = () => undefined

export function configureApiClient(options: {
  getAccessToken: TokenGetter
  onUnauthorized?: UnauthorizedHandler
}) {
  getAccessToken = options.getAccessToken
  if (options.onUnauthorized) {
    onUnauthorized = options.onUnauthorized
  }
}

function mapStatusToCode(status: number): ApiErrorCode {
  switch (status) {
    case 400:
      return 'bad_request'
    case 401:
      return 'unauthorized'
    case 403:
      return 'forbidden'
    case 404:
      return 'not_found'
    case 409:
      return 'conflict'
    case 422:
      return 'validation'
    case 429:
      return 'rate_limited'
    default:
      if (status >= 500) return 'server'
      return 'unknown'
  }
}

function friendlyMessage(status: number, detail: unknown): string {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (
    detail &&
    typeof detail === 'object' &&
    'detail' in detail &&
    typeof (detail as { detail: unknown }).detail === 'string'
  ) {
    return (detail as { detail: string }).detail
  }

  switch (status) {
    case 400:
      return 'The request could not be processed. Please review the information submitted.'
    case 401:
      return 'Your session is invalid or has expired. Please sign in again.'
    case 403:
      return 'You do not have permission to access this resource.'
    case 404:
      return 'The requested record could not be found.'
    case 409:
      return 'This action conflicts with the current state of the record.'
    case 422:
      return 'Some fields need correction before this can be submitted.'
    case 429:
      return 'Too many requests were sent. Please wait briefly and try again.'
    case 500:
    case 502:
    case 503:
    case 504:
      return 'The counselling support service is temporarily unavailable. Please try again shortly.'
    default:
      return 'An unexpected error occurred. Please try again.'
  }
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers)

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }

  if (auth) {
    const token = getAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })
  } catch {
    throw new ApiError(
      'Unable to reach the counselling support service. Confirm the backend is running.',
      0,
      'network',
    )
  }

  if (response.status === 401) {
    onUnauthorized()
  }

  if (!response.ok) {
    const body = await parseBody(response)
    const detail =
      body && typeof body === 'object' && 'detail' in body
        ? (body as { detail: unknown }).detail
        : body

    throw new ApiError(
      friendlyMessage(response.status, detail ?? body),
      response.status,
      mapStatusToCode(response.status),
      detail ?? body,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  const body = await parseBody(response)
  return body as T
}

export function apiGet<T>(path: string, auth = true) {
  return apiRequest<T>(path, { method: 'GET' }, auth)
}

export function apiPost<T>(path: string, data?: unknown, auth = true) {
  return apiRequest<T>(
    path,
    {
      method: 'POST',
      body: data === undefined ? undefined : JSON.stringify(data),
    },
    auth,
  )
}

export function apiPatch<T>(path: string, data?: unknown, auth = true) {
  return apiRequest<T>(
    path,
    {
      method: 'PATCH',
      body: data === undefined ? undefined : JSON.stringify(data),
    },
    auth,
  )
}
