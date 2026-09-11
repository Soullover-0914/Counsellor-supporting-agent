import { apiGet } from './client'
import type { Appointment } from '../types/api'

const BASE = '/api/v1/counselling'

export function listAppointments() {
  return apiGet<Appointment[]>(`${BASE}/appointments`)
}

export function getAppointment(appointmentId: string) {
  return apiGet<Appointment>(
    `${BASE}/appointments/${encodeURIComponent(appointmentId)}`,
  )
}
