import { motion, useReducedMotion } from 'framer-motion'
import './AuthFlowVisual.css'

/**
 * Shared Agent 66 authentication visual.
 * Abstract balance/flow motif — calm institutional metaphor.
 */
export function AuthFlowVisual() {
  const reduceMotion = useReducedMotion()

  if (reduceMotion) {
    return (
      <div className="auth-flow" aria-hidden>
        <svg viewBox="0 0 320 420" className="auth-flow-svg auth-flow-static">
          <path
            d="M40 340 C90 260, 110 210, 160 180 C210 150, 240 120, 280 70"
            className="auth-flow-path"
          />
          <circle cx="160" cy="118" r="18" className="auth-flow-node" />
          <path
            d="M118 170 C140 150, 180 150, 202 170 L210 250 C190 270, 130 270, 110 250 Z"
            className="auth-flow-form"
          />
          <text x="160" y="330" textAnchor="middle" className="auth-flow-mark">
            66
          </text>
        </svg>
      </div>
    )
  }

  return (
    <div className="auth-flow" aria-hidden>
      <svg viewBox="0 0 320 420" className="auth-flow-svg">
        <motion.path
          d="M28 360 C70 300, 95 250, 130 210 C160 175, 190 145, 230 110 C255 90, 275 70, 295 48"
          className="auth-flow-path"
          fill="none"
          initial={{ pathLength: 0, opacity: 0.2 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 2.4, ease: [0.22, 1, 0.36, 1] }}
        />
        <motion.circle
          cx="160"
          cy="118"
          r="18"
          className="auth-flow-node"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.55, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        />
        <motion.path
          d="M118 170 C140 150, 180 150, 202 170 L214 248 C194 272, 126 272, 106 248 Z"
          className="auth-flow-form"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 0.92, y: 0 }}
          transition={{ delay: 0.9, duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
        <motion.path
          d="M106 248 C126 268, 194 268, 214 248"
          className="auth-flow-path"
          fill="none"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 0.8 }}
          transition={{ delay: 1.2, duration: 0.8 }}
        />
        <motion.g
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.7, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        >
          <rect
            x="126"
            y="292"
            width="68"
            height="68"
            rx="14"
            className="auth-flow-badge"
          />
          <text x="160" y="336" textAnchor="middle" className="auth-flow-mark">
            66
          </text>
        </motion.g>
      </svg>
    </div>
  )
}
