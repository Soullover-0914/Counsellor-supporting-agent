import { apiGet, apiPost } from './client'
import type {
  ChangePasswordRequest,
  ChangePasswordResponse,
  LoginRequest,
  RegistrationRequest,
  SignupRequest,
  SignupResponse,
  TokenResponse,
} from '../types/api'

const BASE = '/api/v1/counselling'

export function login(payload: LoginRequest) {
  return apiPost<TokenResponse>(`${BASE}/auth/login`, payload, false)
}

export function signup(payload: SignupRequest) {
  return apiPost<SignupResponse>(`${BASE}/auth/signup`, payload, false)
}

export function changePassword(payload: ChangePasswordRequest) {
  return apiPost<ChangePasswordResponse>(`${BASE}/auth/change-password`, payload)
}

export function listRegistrations(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return apiGet<RegistrationRequest[]>(`${BASE}/registrations${query}`)
}

export function getRegistration(registrationId: string) {
  return apiGet<RegistrationRequest>(
    `${BASE}/registrations/${encodeURIComponent(registrationId)}`,
  )
}

export function approveRegistration(registrationId: string) {
  return apiPost<RegistrationRequest>(
    `${BASE}/registrations/${encodeURIComponent(registrationId)}/approve`,
  )
}

export function rejectRegistration(registrationId: string) {
  return apiPost<RegistrationRequest>(
    `${BASE}/registrations/${encodeURIComponent(registrationId)}/reject`,
    {},
  )
}

export function resendRegistrationCredentials(registrationId: string) {
  return apiPost<{ registration_id: string; email_sent: boolean; message: string }>(
    `${BASE}/registrations/${encodeURIComponent(registrationId)}/resend-credentials`,
  )
}
