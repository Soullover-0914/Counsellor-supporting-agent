export type UserRole =
  | 'student'
  | 'counsellor'
  | 'mentor'
  | 'faculty'
  | 'hod'
  | 'dean'
  | 'admin'

export type ReferralSource =
  | 'self_referral'
  | 'mentor_referral'
  | 'faculty_referral'

export type UrgencyLevel = 'normal' | 'support' | 'urgent' | 'crisis'

export type ReferralStatus =
  | 'pending'
  | 'assigned'
  | 'in_progress'
  | 'completed'

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  username: string
  role: UserRole
  must_change_password?: boolean
}

export interface AuthSession {
  accessToken: string
  tokenType: string
  username: string
  role: UserRole
  /** Present for student accounts; sourced from the signed token payload. */
  studentId: string | null
  mustChangePassword: boolean
}

export interface SignupRequest {
  student_name: string
  student_id: string
  email: string
  username: string
  branch: string
  year: string
}

export interface SignupResponse {
  registration_id: string
  status: 'pending' | 'approved' | 'rejected'
  message: string
}

export interface RegistrationRequest {
  registration_id: string
  student_name: string
  student_id: string
  email: string
  username: string
  branch: string
  year: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
}

export interface ApproveRegistrationResponse {
  registration: RegistrationRequest
  email_sent: boolean
  message: string
}

export interface ChangePasswordRequest {
  new_password: string
  confirm_password: string
  acknowledge_permanent: boolean
}

export interface ChangePasswordResponse {
  message: string
  access_token: string
  token_type: string
  username: string
  role: UserRole
  must_change_password: boolean
}

export interface CrisisResource {
  resource_id: string
  name: string
  contact: string | null
  availability: string | null
  location: string | null
}

export interface CounsellingRequest {
  student_id: string
  source: ReferralSource
  message: string
  consent: boolean
}

export interface CounsellingResponse {
  status: string
  urgency: UrgencyLevel
  route_to_human: boolean
  immediate_escalation: boolean
  reason: string
  recommended_action: string
  crisis_resources: CrisisResource[] | null
}

export interface Referral {
  referral_id: string
  student_id: string
  source: string
  urgency: UrgencyLevel
  status: ReferralStatus
  assigned_counsellor: string | null
  created_at: string
}

export interface AssignCounsellorRequest {
  counsellor_id: string
}

export interface UpdateReferralStatusRequest {
  status: ReferralStatus
}

export interface ScheduleAppointmentRequest {
  counsellor_id: string
  appointment_time: string
}

export interface Appointment {
  appointment_id: string
  referral_id: string
  student_id: string
  counsellor_id: string
  appointment_time: string
  status: string
  created_at: string
}

export interface CounsellingRecord {
  record_id: string
  referral_id: string
  student_id: string
  counsellor_id: string
  session_date: string
  session_summary: string
  follow_up_required: boolean
  follow_up_date: string | null
  follow_up_status: string
  status: string
  created_at: string
}

export interface CreateCounsellingRecordRequest {
  counsellor_id: string
  session_date: string
  session_summary: string
  follow_up_required?: boolean
  follow_up_date?: string | null
}

export interface AcademicAccommodation {
  accommodation_id: string
  referral_id: string
  student_id: string
  accommodation_type: string
  academic_contact: string
  start_date: string | null
  end_date: string | null
  status: string
  created_at: string
}

export interface CreateAccommodationRequest {
  accommodation_type: string
  academic_contact: string
  start_date?: string | null
  end_date?: string | null
}

export interface UpdateAccommodationStatusRequest {
  status: string
}

export interface WellbeingResource {
  resource_id: string
  name: string
  resource_type: string
  description: string
  contact: string | null
  availability: string | null
  location: string | null
  emergency: boolean
  active: boolean
}

export interface CreateResourceRequest {
  name: string
  resource_type: string
  description: string
  contact?: string | null
  availability?: string | null
  location?: string | null
  emergency?: boolean
}

export interface AggregateReport {
  report_type: string
  total_referrals: number
  total_counselling_records: number
  total_follow_ups: number
  total_accommodations: number
  referral_by_urgency: Record<string, number>
  referral_by_source: Record<string, number>
  referral_by_status: Record<string, number>
  accommodation_by_type: Record<string, number>
  privacy_threshold: number
  breakdown_available: boolean
}

export interface AuditLog {
  audit_id: string
  actor_id: string
  actor_role: string
  action: string
  resource_type: string
  resource_id: string | null
  outcome: string
  human_approved: boolean | null
  created_at: string
}

export interface CrisisEscalation {
  escalation_id: string
  student_id: string
  reason: string
  severity: string
  created_at: string
}

export type ApiErrorCode =
  | 'bad_request'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'validation'
  | 'rate_limited'
  | 'server'
  | 'network'
  | 'unavailable'
  | 'unknown'

export class ApiError extends Error {
  status: number
  code: ApiErrorCode
  details?: unknown

  constructor(
    message: string,
    status: number,
    code: ApiErrorCode,
    details?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}
