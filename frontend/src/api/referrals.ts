import { apiGet, apiPatch, apiPost } from './client'
import type {
  Appointment,
  AssignCounsellorRequest,
  Referral,
  ScheduleAppointmentRequest,
  UpdateReferralStatusRequest,
} from '../types/api'

const BASE = '/api/v1/counselling'

export function listReferrals() {
  return apiGet<Referral[]>(`${BASE}/referrals`)
}

export function getReferral(referralId: string) {
  return apiGet<Referral>(`${BASE}/referrals/${encodeURIComponent(referralId)}`)
}

export function assignReferral(referralId: string, payload: AssignCounsellorRequest) {
  return apiPatch<Referral>(
    `${BASE}/referrals/${encodeURIComponent(referralId)}/assign`,
    payload,
  )
}

export function updateReferralStatus(
  referralId: string,
  payload: UpdateReferralStatusRequest,
) {
  return apiPatch<Referral>(
    `${BASE}/referrals/${encodeURIComponent(referralId)}/status`,
    payload,
  )
}

export function scheduleReferral(
  referralId: string,
  payload: ScheduleAppointmentRequest,
) {
  return apiPost<Appointment>(
    `${BASE}/referrals/${encodeURIComponent(referralId)}/schedule`,
    payload,
  )
}
