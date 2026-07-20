import React, { useRef, useEffect } from 'react'
import { useSession } from '../context/SessionContext'

const EMOTION_META = {
  happy:    { emoji: '😊', gradient: 'linear-gradient(135deg,#FFD700,#ff9a00)' },
  sad:      { emoji: '😢', gradient: 'linear-gradient(135deg,#4A90E2,#357abd)' },
  angry:    { emoji: '😠', gradient: 'linear-gradient(135deg,#E74C3C,#c0392b)' },
  neutral:  { emoji: '😐', gradient: 'linear-gradient(135deg,#95A5A6,#7f8c8d)' },
  fear:     { emoji: '😨', gradient: 'linear-gradient(135deg,#8E44AD,#6c3483)' },
  surprise: { emoji: '😲', gradient: 'linear-gradient(135deg,#E67E22,#ca6f1e)' },
  disgust:  { emoji: '🤢', gradient: 'linear-gradient(135deg,#27AE60,#1e8449)' },
  uncertain:{ emoji: '❓', gradient: 'linear-gradient(135deg,#7F8C8D,#5d6d7e)' },
}

export default function EmotionCard() {
  const { state } = useSession()
  const { currentEmotion, currentConfidence, currentEmoji, currentColor,
          isUncertain, isActive, allScores } = state

  const prevEmotion = useRef(null)
  const cardRef = useRef(null)

  // Trigger pop animation when emotion changes
  useEffect(() => {
    if (currentEmotion && currentEmotion !== prevEmotion.current) {
      prevEmotion.current = currentEmotion
      if (cardRef.current) {
        cardRef.current.classList.remove('animate-pop')
        void cardRef.current.offsetWidth // reflow
        cardRef.current.classList.add('animate-pop')
      }
    }
  }, [currentEmotion])

  const emotion = isUncertain ? 'uncertain' : (currentEmotion || 'uncertain')
  const meta = EMOTION_META[emotion] || EMOTION_META.uncertain
  const displayLabel = isUncertain ? 'Uncertain' : (currentEmotion || 'Waiting…')

  return (
    <div className="glass-card" id="emotion" style={{ height: '100%' }}>
      <div className="card-header-custom">
        <i className="bi bi-emoji-smile-fill" style={{ color: 'var(--brand-primary)' }} />
        <span className="section-title" style={{ fontSize: '0.9rem' }}>Current Emotion</span>
      </div>

      <div className="card-body-custom" style={{ textAlign: 'center', padding: '10px 14px' }}>
        {!isActive ? (
          <div style={{ padding: '20px 0', color: 'var(--text-muted)' }}>
            <i className="bi bi-play-circle" style={{ fontSize: '2.2rem', display: 'block', marginBottom: '8px' }} />
            <div style={{ fontSize: '0.8rem' }}>Start a session to begin analysis</div>
          </div>
        ) : (
          <>
            {/* Emoji */}
            <div ref={cardRef} style={{
              fontSize: '3.5rem',
              lineHeight: 1.1,
              marginBottom: '8px',
              filter: `drop-shadow(0 0 16px ${currentColor}50)`,
            }}>
              {meta.emoji}
            </div>

            {/* Emotion label */}
            <div style={{
              fontSize: '1.6rem',
              fontWeight: 800,
              color: meta.color,
              marginBottom: '4px',
              textTransform: 'capitalize',
              letterSpacing: '-0.3px',
              textShadow: `0 0 10px ${meta.color}40`,
            }}>
              {displayLabel}
            </div>

            {/* Confidence */}
            <div style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono)',
              marginBottom: '10px',
            }}>
              {isUncertain
                ? 'Low confidence — uncertain'
                : `${currentConfidence.toFixed(1)}% confidence`}
            </div>

            {/* All emotion scores mini-bars (2-column layout to fit height perfectly) */}
            {allScores && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px 16px',
                textAlign: 'left',
                marginTop: '12px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                paddingTop: '10px'
              }}>
                {/* Left Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {['happy', 'sad', 'neutral', 'angry'].map((emo) => {
                    const score = allScores[emo] || 0.0
                    const m = EMOTION_META[emo] || EMOTION_META.uncertain
                    return (
                      <div key={emo}>
                        <div style={{
                          display: 'flex', justifyContent: 'space-between',
                          fontSize: '0.65rem', marginBottom: '2px',
                          color: 'var(--text-secondary)',
                        }}>
                          <span style={{ textTransform: 'capitalize' }}>{m.emoji} {emo}</span>
                          <span style={{ fontFamily: 'var(--font-mono)' }}>{score.toFixed(0)}%</span>
                        </div>
                        <div className="confidence-bar-track" style={{ height: '4px' }}>
                          <div className="confidence-bar-fill" style={{
                            width: `${Math.min(score, 100)}%`,
                            background: m.gradient,
                          }} />
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Right Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {['fear', 'surprise', 'disgust'].map((emo) => {
                    const score = allScores[emo] || 0.0
                    const m = EMOTION_META[emo] || EMOTION_META.uncertain
                    return (
                      <div key={emo}>
                        <div style={{
                          display: 'flex', justifyContent: 'space-between',
                          fontSize: '0.65rem', marginBottom: '2px',
                          color: 'var(--text-secondary)',
                        }}>
                          <span style={{ textTransform: 'capitalize' }}>{m.emoji} {emo}</span>
                          <span style={{ fontFamily: 'var(--font-mono)' }}>{score.toFixed(0)}%</span>
                        </div>
                        <div className="confidence-bar-track" style={{ height: '4px' }}>
                          <div className="confidence-bar-fill" style={{
                            width: `${Math.min(score, 100)}%`,
                            background: m.gradient,
                          }} />
                        </div>
                      </div>
                    )
                  })}
                  {/* Empty item placeholder to keep column alignment clean */}
                  <div style={{ height: '14px' }} />
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div style={{
              marginTop: '10px',
              fontSize: '0.65rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}>
              {new Date().toLocaleTimeString()}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
