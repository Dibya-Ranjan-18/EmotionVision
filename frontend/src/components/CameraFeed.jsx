import React, { useRef, useEffect } from 'react'
import { useWebcam } from '../hooks/useWebcam'
import { useSessionControl } from '../hooks/useSession'
import { useSession } from '../context/SessionContext'
import { exportPDF } from '../services/api'

export default function CameraFeed() {
  const canvasRef = useRef(null)
  const { videoRef, isReady, error: camError } = useWebcam()
  const { state } = useSession()
  const { handleStart, handleStop } = useSessionControl(videoRef, canvasRef)
  const { isActive, isStarting, isStopping, faceCount, fps, processingTimeMs, sessionId } = state

  // Sync canvas size to video element
  useEffect(() => {
    if (!videoRef.current || !canvasRef.current) return
    const video = videoRef.current
    const resize = () => {
      canvasRef.current.width  = video.offsetWidth
      canvasRef.current.height = video.offsetHeight
    }
    const observer = new ResizeObserver(resize)
    observer.observe(video)
    return () => observer.disconnect()
  }, [isReady])

  return (
    <div className="glass-card" id="camera">
      {/* Header */}
      <div className="card-header-custom">
        <i className="bi bi-camera-video-fill" style={{ color: 'var(--brand-primary)' }} />
        <span className="section-title" style={{ fontSize: '1rem' }}>Live Camera Feed</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
          {isActive && <span className="stat-badge active"><span className="live-dot" /> LIVE</span>}
          {!isActive && <span className="stat-badge inactive">STANDBY</span>}
        </div>
      </div>

      <div style={{ padding: '8px' }}>
        {/* Camera error */}
        {camError && (
          <div className="alert-custom alert-error" style={{ marginBottom: '8px', padding: '6px 12px' }}>
            <i className="bi bi-exclamation-triangle-fill" />
            <span>{camError}</span>
          </div>
        )}

        {/* Video container */}
        <div className={`camera-container ${isActive ? 'glow-ring' : ''}`} style={{ position: 'relative' }}>
          <video
            ref={videoRef}
            className="camera-video"
            autoPlay
            muted
            playsInline
            aria-label="Live webcam feed"
          />
          <canvas ref={canvasRef} className="camera-canvas" />

          {/* HUD overlay */}
          <div className="camera-overlay-top">
            <div className="camera-fps-badge">
              {isActive ? (
                <><i className="bi bi-speedometer2" /> {fps} FPS &nbsp;|&nbsp; {processingTimeMs}ms</>
              ) : (
                <><i className="bi bi-camera" /> Ready</>
              )}
            </div>
            <div className="camera-fps-badge" style={{ color: 'var(--brand-primary)' }}>
              <i className="bi bi-people-fill" /> {faceCount} face{faceCount !== 1 ? 's' : ''}
            </div>
          </div>

          {/* Floating Controls Overlay (Zoom-style) */}
          <div className="camera-controls-overlay">
            {!isActive ? (
              <button
                id="btn-start-session"
                className="btn-primary-custom"
                onClick={handleStart}
                disabled={isStarting || !isReady}
                aria-label="Start analysis session"
                style={{ borderRadius: 'var(--radius-sm)' }}
              >
                {isStarting ? (
                  <><div style={{ width:'14px',height:'14px',border:'2px solid rgba(255,255,255,0.4)',
                                  borderTopColor:'white',borderRadius:'50%',animation:'spin-slow 0.8s linear infinite', marginRight: '6px'}} />
                    Starting…</>
                ) : (
                  <><i className="bi bi-play-circle-fill" /> Start Session</>
                )}
              </button>
            ) : (
              <button
                id="btn-stop-session"
                className="btn-danger-custom"
                onClick={handleStop}
                disabled={isStopping}
                aria-label="Stop analysis session"
                style={{ borderRadius: 'var(--radius-sm)' }}
              >
                {isStopping ? (
                  <><div style={{ width:'14px',height:'14px',border:'2px solid rgba(255,255,255,0.4)',
                                  borderTopColor:'white',borderRadius:'50%',animation:'spin-slow 0.8s linear infinite', marginRight: '6px'}} />
                    Stopping…</>
                ) : (
                  <><i className="bi bi-stop-circle-fill" /> Stop Session</>
                )}
              </button>
            )}

            {/* Export PDF (only if session has run) */}
            {sessionId && !isActive && (
              <a
                id="btn-export-pdf"
                href={exportPDF(sessionId)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost"
                aria-label="Download PDF report"
                style={{ borderRadius: 'var(--radius-sm)', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
              >
                <i className="bi bi-file-earmark-pdf-fill" style={{ color: '#E74C3C' }} />
                Export PDF
              </a>
            )}
          </div>

          {/* No face warning */}
          {isActive && faceCount === 0 && (
            <div className="camera-no-face">
              <i className="bi bi-exclamation-circle" /> No face
            </div>
          )}

          {/* Waiting overlay */}
          {!isReady && !camError && (
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(0,0,0,0.8)',
              gap: '12px',
            }}>
              <div style={{ width: '32px', height: '32px', border: '3px solid var(--brand-primary)',
                            borderTopColor: 'transparent', borderRadius: '50%',
                            animation: 'spin-slow 1s linear infinite' }} />
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                Initialising camera…
              </span>
            </div>
          )}
        </div>

        {/* Error from session */}
        {state.error && (
          <div className="alert-custom alert-error" style={{ marginTop: '8px', padding: '6px 12px' }}>
            <i className="bi bi-exclamation-triangle-fill" />
            <span>{state.error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
