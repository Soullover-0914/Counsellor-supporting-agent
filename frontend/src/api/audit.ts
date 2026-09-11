import { apiGet } from './client'
import type { AuditLog } from '../types/api'

const BASE = '/api/v1/counselling'

export function listAuditLogs(limit = 100) {
  return apiGet<AuditLog[]>(`${BASE}/audit-logs?limit=${limit}`)
}

export function getAuditLog(auditId: string) {
  return apiGet<AuditLog>(`${BASE}/audit-logs/${encodeURIComponent(auditId)}`)
}
