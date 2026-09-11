import { apiGet, apiPatch, apiPost } from './client'
import type { CreateResourceRequest, WellbeingResource } from '../types/api'

const BASE = '/api/v1/counselling'

export function listResources() {
  return apiGet<WellbeingResource[]>(`${BASE}/resources`)
}

export function listResourcesByType(resourceType: string) {
  return apiGet<WellbeingResource[]>(
    `${BASE}/resources/type/${encodeURIComponent(resourceType)}`,
  )
}

export function getResource(resourceId: string) {
  return apiGet<WellbeingResource>(
    `${BASE}/resources/${encodeURIComponent(resourceId)}`,
  )
}

export function createResource(payload: CreateResourceRequest) {
  return apiPost<WellbeingResource>(`${BASE}/resources`, payload)
}

export function deactivateResource(resourceId: string) {
  return apiPatch<WellbeingResource>(
    `${BASE}/resources/${encodeURIComponent(resourceId)}/deactivate`,
  )
}
