import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

export function Breadcrumbs({
  items,
}: {
  items: Array<{ label: string; to?: string }>
}) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        return (
          <span key={`${item.label}-${index}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            {item.to && !isLast ? <Link to={item.to}>{item.label}</Link> : <span aria-current={isLast ? 'page' : undefined}>{item.label}</span>}
            {!isLast ? <ChevronRight size={14} aria-hidden /> : null}
          </span>
        )
      })}
    </nav>
  )
}
