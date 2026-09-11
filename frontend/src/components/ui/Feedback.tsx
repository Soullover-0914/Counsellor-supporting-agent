import type { ReactNode } from 'react'
import { cx } from '../../utils/format'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode
  tone?: Tone
}) {
  return <span className={cx('badge', `badge-${tone}`)}>{children}</span>
}

export function Alert({
  title,
  children,
  tone = 'info',
  icon,
}: {
  title?: string
  children: ReactNode
  tone?: Tone
  icon?: ReactNode
}) {
  return (
    <div className={cx('alert', `alert-${tone}`)} role="status">
      {icon}
      <div>
        {title ? <div className="alert-title">{title}</div> : null}
        <div className="alert-body">{children}</div>
      </div>
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  )
}

export function Skeleton({
  height = 16,
  width = '100%',
  radius,
}: {
  height?: number | string
  width?: number | string
  radius?: number | string
}) {
  return (
    <div
      className="skeleton"
      style={{ height, width, borderRadius: radius }}
      aria-hidden
    />
  )
}

export function PrivacyChip({ children }: { children: ReactNode }) {
  return <span className="privacy-chip">{children}</span>
}
