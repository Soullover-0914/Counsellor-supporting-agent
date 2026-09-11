import { apiGet, apiPatch, apiPost } from './client'
import type {
  CounsellingRecord,
  CreateCounsellingRecordRequest,
} from '../types/api'

const BASE = '/api/v1/counselling'

export function createCounsellingRecord(
  referralId: string,
  payload: CreateCounsellingRecordRequest,
) {
  return apiPost<CounsellingRecord>(
    `${BASE}/referrals/${encodeURIComponent(referralId)}/records`,
    payload,
  )
}

export function listCounsellingRecords() {
  return apiGet<CounsellingRecord[]>(`${BASE}/records`)
}

export function getCounsellingRecord(recordId: string) {
  return apiGet<CounsellingRecord>(
    `${BASE}/records/${encodeURIComponent(recordId)}`,
  )
}

export function completeCounsellingRecord(recordId: string) {
  return apiPatch<CounsellingRecord>(
    `${BASE}/records/${encodeURIComponent(recordId)}/complete`,
  )
}
