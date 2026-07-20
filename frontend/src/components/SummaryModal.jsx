import React from 'react'
import { useSession } from '../context/SessionContext'
import { exportPDF } from '../services/api'

const EMOTION_META = {
  happy:    { emoji: '😊', gradient: 'linear-gradient(135deg,#FFD700,#ff9a00)' },
  sad:      { emoji: '😢', gradient: 'linear-gradient(135deg,#4A90E2,#357abd)' },
  angry:    { emoji: '😠', gradient: 'linear-gradient(135deg,#E74C3C,#c0392b)' },
  neutral:  { emoji: '😐', gradient: 'linear-gradient(135deg,#95A5A6,#7f8c8d)' },
  fear:     { emoji: '😨', gradient: 'linear-gradient(135deg,#8E44AD,#6c3483)' },
  surprise: { emoji: '😲', gradient: 'linear-gradient(135deg,#E67E22,#ca6f1e)' },
  disgust:  { emoji: '🤢', gradient: 'linear-gradient(135deg,#27AE60,#1e8449)' },
}

function formatDuration(secs) {
  if (!secs) return '0s'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

export default function SummaryModal({ onClose }) {
  const { state } = useSession()
  const { summary, sessionId } = state
  if (!summary) return null

  const { duration_seconds, dominant_emotion, avg_confidence,
          total_frames, avg_fps, emotion_changes, emotion_distribution } = summary

  const dom = dominant_emotion?.toLowerCase()
  const meta = EMOTION_META[dom] || { emoji: '❓', gradient: 'var(--gradient-brand)' }

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true"
         aria-label="Session Summary">
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          padding: '24px 24px 0',
          textAlign: 'center',
          background: meta.gradient,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '8px', WebkitTextFillColor: 'initial' }}>
            {meta.emoji}
          </div>
          <h2 style={{ fontWeight: 800, fontSize: '1.6rem', marginBottom: '4px' }}>
            Session Complete
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', WebkitTextFillColor: 'initial' }}>
            Here's your emotion analysis summary
          </p>
        </div>

        {/* Stats grid */}
        <div style={{ padding: '20px 24px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px',
            marginBottom: '20px',
          }}>
            {[
              { label: 'Duration', value: formatDuration(duration_seconds) },
              { label: 'Dominant Emotion', value: `${meta.emoji} ${dominant_emotion || '—'}` },
              { label: 'Avg Confidence', value: `${avg_confidence?.toFixed(1)}%` },
              { label: 'Frames Processed', value: (total_frames || 0).toLocaleString() },
              { label: 'Average FPS', value: avg_fps?.toFixed(1) || '0' },
              { label: 'Emotion Changes', value: emotion_changes || 0 },
            ].map((item, idx) => (
              <div key={idx} style={{
                padding: '12px', borderRadius: 'var(--radius-md)',
                background: 'var(--bg-card)', border: 'var(--glass-border)',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '1.2rem', fontWeight: 800,
                              background: meta.gradient,
                              WebkitBackgroundClip: 'text',
                              WebkitTextFillColor: 'transparent',
                              backgroundClip: 'text', textTransform: 'capitalize' }}>
                  {item.value}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)',
                              fontWeight: 500, marginTop: '4px',
                              textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {item.label}
                </div>
              </div>
            ))}
          </div>

          {/* Emotion distribution */}
          {emotion_distribution && Object.keys(emotion_distribution).length > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)',
                            textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px' }}>
                Emotion Breakdown
              </div>
              {Object.entries(emotion_distribution)
                .sort(([,a],[,b]) => b - a)
                .map(([emo, count]) => {
                  const total = Object.values(emotion_distribution).reduce((a, b) => a + b, 0)
                  const pct = ((count / total) * 100).toFixed(1)
                  const m = EMOTION_META[emo] || { emoji: '❓', gradient: 'var(--gradient-brand)' }
                  return (
                    <div key={emo} style={{ marginBottom: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between',
                                    fontSize: '0.8rem', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                        <span>{m.emoji} {emo} &nbsp;
                          <span style={{ color: 'var(--text-muted)' }}>({count} frames)</span>
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', fontWeight: 700 }}>
                          {pct}%
                        </span>
                      </div>
                      <div className="confidence-bar-track">
                        <div className="confidence-bar-fill"
                             style={{ width: `${pct}%`, background: m.gradient }} />
                      </div>
                    </div>
                  )
                })}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a
              id="btn-download-pdf"
              href={exportPDF(sessionId)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary-custom"
            >
              <i className="bi bi-file-earmark-pdf-fill" />
              Download PDF Report
            </a>
            <button className="btn-ghost" onClick={onClose} id="btn-close-summary">
              <i className="bi bi-x-circle" /> Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
