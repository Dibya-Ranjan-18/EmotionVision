import React from 'react'
import { useSession } from '../context/SessionContext'

export default function Navbar() {
  const { state, toggleTheme } = useSession()
  const { isActive, fps, faceCount, theme } = state

  return (
    <nav className="navbar-custom" aria-label="Main navigation">

      {/* Brand */}
      <div className="navbar-brand">
        <i className="bi bi-eye-fill" style={{ fontSize: '1.4rem', WebkitTextFillColor: 'initial', color: '#6c63ff' }} />
        EmotionVision AI
      </div>

      <div className="navbar-spacer" />

      {/* Live status indicators */}
      {isActive && (
        <div className="d-flex align-items-center gap-3">
          <div className="d-none d-md-flex align-items-center gap-2"
               style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            <i className="bi bi-people-fill" style={{ color: 'var(--brand-primary)' }} />
            <span>{faceCount} face{faceCount !== 1 ? 's' : ''}</span>
          </div>
          <div className="d-none d-md-flex align-items-center gap-2"
               style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            <i className="bi bi-speedometer2" style={{ color: 'var(--success)' }} />
            <span>{fps} FPS</span>
          </div>
          <div className="stat-badge active">
            <span className="live-dot" /> LIVE
          </div>
        </div>
      )}

      {/* Theme toggle */}
      <button
        className="btn-ghost"
        onClick={toggleTheme}
        aria-label="Toggle theme"
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        style={{ padding: '7px 10px', marginLeft: '8px' }}
      >
        <i className={`bi ${theme === 'dark' ? 'bi-sun-fill' : 'bi-moon-fill'}`}
           style={{ fontSize: '1rem' }} />
      </button>
    </nav>
  )
}
