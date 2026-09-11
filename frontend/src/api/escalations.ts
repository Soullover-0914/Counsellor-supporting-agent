import { apiGet } from './client'
import type { CrisisEscalation } from '../types/api'

const BASE = '/api/v1/counselling'

export function listEscalations() {
  return apiGet<CrisisEscalation[]>(`${BASE}/escalations`)
}
