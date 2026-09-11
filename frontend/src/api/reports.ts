import { apiGet } from './client'
import type { AggregateReport } from '../types/api'

const BASE = '/api/v1/counselling'

export function getAggregateReport() {
  return apiGet<AggregateReport>(`${BASE}/reports/aggregate`)
}
