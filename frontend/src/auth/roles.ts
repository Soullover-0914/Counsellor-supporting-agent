import type { UserRole } from '../types/api'
import type { LucideIcon } from 'lucide-react'
import {
  AlertTriangle,
  BookOpen,
  Calendar,
  ClipboardList,
  FileText,
  FolderLock,
  Home,
  LifeBuoy,
  ScrollText,
  Shield,
  UserPlus,
  Users,
} from 'lucide-react'

export interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  end?: boolean
}

export const ROLE_HOME: Record<UserRole, string> = {
  student: '/student',
  counsellor: '/counsellor',
  mentor: '/mentor',
  faculty: '/faculty',
  hod: '/hod',
  dean: '/dean',
  admin: '/admin',
}

export const ROLE_LABELS: Record<UserRole, string> = {
  student: 'Student',
  counsellor: 'Counsellor',
  mentor: 'Mentor',
  faculty: 'Faculty',
  hod: 'Head of Department',
  dean: 'Dean',
  admin: 'Administrator',
}

export function navigationForRole(role: UserRole): NavItem[] {
  switch (role) {
    case 'student':
      return [
        { label: 'Dashboard', to: '/student', icon: Home, end: true },
        { label: 'Request Support', to: '/student/support', icon: LifeBuoy },
        { label: 'Resources', to: '/student/resources', icon: BookOpen },
      ]
    case 'counsellor':
      return [
        { label: 'Dashboard', to: '/counsellor', icon: Home, end: true },
        { label: 'Referral Queue', to: '/counsellor/referrals', icon: Users },
        { label: 'Appointments', to: '/counsellor/appointments', icon: Calendar },
        {
          label: 'Counselling Records',
          to: '/counsellor/records',
          icon: FolderLock,
        },
        { label: 'Follow-ups', to: '/counsellor/followups', icon: ClipboardList },
        { label: 'Escalations', to: '/counsellor/escalations', icon: AlertTriangle },
        { label: 'Accommodations', to: '/counsellor/accommodations', icon: FileText },
        { label: 'Resources', to: '/counsellor/resources', icon: BookOpen },
      ]
    case 'mentor':
      return [
        { label: 'Dashboard', to: '/mentor', icon: Home, end: true },
        { label: 'Refer a Student', to: '/mentor/support', icon: LifeBuoy },
        { label: 'Referral Queue', to: '/mentor/referrals', icon: Users },
        { label: 'Resources', to: '/mentor/resources', icon: BookOpen },
      ]
    case 'faculty':
      return [
        { label: 'Dashboard', to: '/faculty', icon: Home, end: true },
        { label: 'Refer a Student', to: '/faculty/support', icon: LifeBuoy },
        { label: 'Referral Queue', to: '/faculty/referrals', icon: Users },
        { label: 'Resources', to: '/faculty/resources', icon: BookOpen },
      ]
    case 'hod':
      return [
        { label: 'Dashboard', to: '/hod', icon: Home, end: true },
        { label: 'Referrals', to: '/hod/referrals', icon: Users },
        { label: 'Appointments', to: '/hod/appointments', icon: Calendar },
        { label: 'Accommodations', to: '/hod/accommodations', icon: FileText },
        { label: 'Aggregate Reports', to: '/hod/reports', icon: Shield },
        { label: 'Audit Logs', to: '/hod/audit', icon: ScrollText },
        { label: 'Resources', to: '/hod/resources', icon: BookOpen },
      ]
    case 'dean':
      return [
        { label: 'Dashboard', to: '/dean', icon: Home, end: true },
        { label: 'Referrals', to: '/dean/referrals', icon: Users },
        { label: 'Escalations', to: '/dean/escalations', icon: AlertTriangle },
        { label: 'Accommodations', to: '/dean/accommodations', icon: FileText },
        { label: 'Aggregate Reports', to: '/dean/reports', icon: Shield },
        { label: 'Audit Logs', to: '/dean/audit', icon: ScrollText },
        { label: 'Resources', to: '/dean/resources', icon: BookOpen },
      ]
    case 'admin':
      return [
        { label: 'Dashboard', to: '/admin', icon: Home, end: true },
        { label: 'Registrations', to: '/admin/registrations', icon: UserPlus },
        { label: 'Referrals', to: '/admin/referrals', icon: Users },
        { label: 'Escalations', to: '/admin/escalations', icon: AlertTriangle },
        { label: 'Accommodations', to: '/admin/accommodations', icon: FileText },
        { label: 'Aggregate Reports', to: '/admin/reports', icon: Shield },
        { label: 'Audit Logs', to: '/admin/audit', icon: ScrollText },
        { label: 'Resources', to: '/admin/resources', icon: BookOpen },
      ]
    default:
      return []
  }
}

export function isRole(value: string): value is UserRole {
  return (
    value === 'student' ||
    value === 'counsellor' ||
    value === 'mentor' ||
    value === 'faculty' ||
    value === 'hod' ||
    value === 'dean' ||
    value === 'admin'
  )
}
