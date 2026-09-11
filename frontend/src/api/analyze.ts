import { apiPost } from './client'
import type { CounsellingRequest, CounsellingResponse } from '../types/api'

const BASE = '/api/v1/counselling'

export function analyzeCounsellingRequest(payload: CounsellingRequest) {
  // Backend analyze endpoint does not require auth; send without bearer.
  return apiPost<CounsellingResponse>(`${BASE}/analyze`, payload, false)
}
