import { apiGet, apiPatch, apiPost } from './client'
import type {
  AcademicAccommodation,
  CreateAccommodationRequest,
  UpdateAccommodationStatusRequest,
} from '../types/api'

const BASE = '/api/v1/counselling'

export function createAccommodation(
  referralId: string,
  payload: CreateAccommodationRequest,
) {
  return apiPost<AcademicAccommodation>(
    `${BASE}/referrals/${encodeURIComponent(referralId)}/accommodations`,
    payload,
  )
}

export function listAccommodations() {
  return apiGet<AcademicAccommodation[]>(`${BASE}/accommodations`)
}

export function getAccommodation(accommodationId: string) {
  return apiGet<AcademicAccommodation>(
    `${BASE}/accommodations/${encodeURIComponent(accommodationId)}`,
  )
}

export function updateAccommodationStatus(
  accommodationId: string,
  payload: UpdateAccommodationStatusRequest,
) {
  return apiPatch<AcademicAccommodation>(
    `${BASE}/accommodations/${encodeURIComponent(accommodationId)}/status`,
    payload,
  )
}
