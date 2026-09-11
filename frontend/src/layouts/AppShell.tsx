import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  LogOut,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  X,
} from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { navigationForRole, ROLE_LABELS } from '../auth/roles'
import { Button } from '../components/ui/Button'
import { PageTransition } from '../components/motion/PageTransition'

function brandTitle(pathname: string) {
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length <= 1) return 'Workspace'
  return parts[parts.length - 1]
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function AppShell() {
  const { session, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const reduceMotion = useReducedMotion()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  if (!session) return null

  const nav = navigationForRole(session.role)

  const onLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const NavItems = ({ onNavigate }: { onNavigate?: () => void }) => (
    <nav className="sidebar-nav" aria-label="Primary">
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          onClick={onNavigate}
        >
          <item.icon size={18} aria-hidden />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className={`shell${collapsed ? ' is-collapsed' : ''}`}>
      <aside className="sidebar" aria-label="Application sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden>
            66
          </div>
          {!collapsed ? (
            <div className="brand-copy">
              <strong>Agent 66</strong>
              <span>Counselling Support</span>
            </div>
          ) : null}
        </div>
        <NavItems />
        <div className="sidebar-footer">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed((value) => !value)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            style={{ color: 'var(--white)', width: '100%' }}
          >
            {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            {!collapsed ? <span>Collapse</span> : null}
          </Button>
        </div>
      </aside>

      <div className="shell-main">
        <header className="topbar">
          <div className="topbar-left">
            <Button
              className="mobile-nav-toggle"
              variant="secondary"
              size="sm"
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={18} />
            </Button>
            <div>
              <div className="topbar-title">{brandTitle(location.pathname)}</div>
            </div>
          </div>
          <div className="topbar-right">
            <span className="privacy-chip">
              <ShieldCheck size={14} aria-hidden />
              Authorised access
            </span>
            <div className="user-chip">
              <strong>{session.username}</strong>
              <span>{ROLE_LABELS[session.role]}</span>
            </div>
            <Button variant="secondary" size="sm" onClick={onLogout}>
              <LogOut size={16} aria-hidden />
              Sign out
            </Button>
          </div>
        </header>

        <main className="content">
          <PageTransition key={location.pathname}>
            <Outlet />
          </PageTransition>
        </main>

        <footer className="app-footer">
          <div>Agent 66 · Counselling Support System</div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/terms">Terms of Use</Link>
          </div>
        </footer>
      </div>

      <div className="mobile-drawer">
        <AnimatePresence>
          {mobileOpen ? (
            <>
              <motion.div
                className="drawer-backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.18 }}
                onClick={() => setMobileOpen(false)}
              />
              <motion.div
                className="mobile-drawer-panel"
                initial={reduceMotion ? false : { x: -24, opacity: 0.9 }}
                animate={{ x: 0, opacity: 1 }}
                exit={reduceMotion ? undefined : { x: -24, opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.22 }}
              >
                <div className="sidebar-brand">
                  <div className="brand-mark" aria-hidden>
                    66
                  </div>
                  <div className="brand-copy">
                    <strong>Agent 66</strong>
                    <span>Counselling Support</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label="Close navigation"
                    onClick={() => setMobileOpen(false)}
                    style={{ marginLeft: 'auto', color: 'var(--white)' }}
                  >
                    <X size={18} />
                  </Button>
                </div>
                <NavItems onNavigate={() => setMobileOpen(false)} />
              </motion.div>
            </>
          ) : null}
        </AnimatePresence>
      </div>
    </div>
  )
}
