import { apiGet, apiPatch } from './client'
import type { CounsellingRecord } from '../types/api'

const BASE = '/api/v1/counselling'

export function listFollowUps() {
  return apiGet<CounsellingRecord[]>(`${BASE}/follow-ups`)
}

export function listDueFollowUps() {
  return apiGet<CounsellingRecord[]>(`${BASE}/follow-ups/due`)
}

export function completeFollowUp(recordId: string) {
  return apiPatch<CounsellingRecord>(
    `${BASE}/follow-ups/${encodeURIComponent(recordId)}/complete`,
  )
}
