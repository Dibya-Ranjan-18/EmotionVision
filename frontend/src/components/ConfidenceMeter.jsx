import React from 'react'
import { useSession } from '../context/SessionContext'

const EMOTION_GRADIENTS = {
  happy:    'linear-gradient(135deg,#FFD700,#ff9a00)',
  sad:      'linear-gradient(135deg,#4A90E2,#357abd)',
  angry:    'linear-gradient(135deg,#E74C3C,#c0392b)',
  neutral:  'linear-gradient(135deg,#95A5A6,#7f8c8d)',
  fear:     'linear-gradient(135deg,#8E44AD,#6c3483)',
  surprise: 'linear-gradient(135deg,#E67E22,#ca6f1e)',
  disgust:  'linear-gradient(135deg,#27AE60,#1e8449)',
  uncertain:'linear-gradient(135deg,#7F8C8D,#5d6d7e)',
}

export default function ConfidenceMeter() {
  const { state } = useSession()
  const { currentEmotion, currentConfidence, currentColor, isUncertain, isActive } = state

  const emotion = isUncertain ? 'uncertain' : (currentEmotion || 'uncertain')
  const gradient = EMOTION_GRADIENTS[emotion] || EMOTION_GRADIENTS.uncertain
  const pct = Math.min(Math.max(currentConfidence, 0), 100)

  const levelColor = pct >= 75 ? 'var(--success)'
                   : pct >= 50 ? 'var(--warning)'
                   : 'var(--danger)'

  return (
    <div className="glass-card" id="confidence">
      <div className="card-header-custom" style={{ padding: '6px 12px' }}>
        <i className="bi bi-speedometer" style={{ color: 'var(--brand-primary)' }} />
        <span className="section-title" style={{ fontSize: '0.8rem' }}>Confidence Meter</span>
      </div>

      <div className="card-body-custom" style={{ padding: '8px 12px', height: 'calc(100% - 36px)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        {!isActive ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '6px 0', fontSize: '0.75rem' }}>
            No active session
          </div>
        ) : (
          <div style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'capitalize', fontWeight: 600 }}>
                {emotion} Confidence
              </span>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: levelColor }}>
                {pct.toFixed(0)}<span style={{ fontSize: '0.9rem' }}>%</span>
              </span>
            </div>

            {/* Glowing Segmented LED Bar */}
            <div style={{ display: 'flex', gap: '3px', margin: '8px 0', justifyContent: 'space-between', width: '100%' }}>
              {Array.from({ length: 20 }).map((_, idx) => {
                const active = idx < Math.round((pct / 100) * 20)
                return (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      height: '14px',
                      borderRadius: '1px',
                      background: active ? gradient : 'rgba(255, 255, 255, 0.05)',
                      boxShadow: active ? `0 0 8px ${levelColor}80` : 'none',
                      transition: 'all 0.2s ease',
                    }}
                  />
                )
              })}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              <span>0%</span>
              <span style={{ color: levelColor, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                ● {pct >= 75 ? 'High Level' : pct >= 50 ? 'Medium Level' : 'Low Level'}
              </span>
              <span>100%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
