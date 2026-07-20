/**
 * useSession hook — manages session start/stop + frame streaming.
 * Handles webcam capture, base64 encoding, and API communication.
 */
import { useRef, useCallback } from 'react'
import { useSession } from '../context/SessionContext'
import { startSession, stopSession, processFrame } from '../services/api'

const FRAME_INTERVAL_MS = 200 // 5 fps stream (optimal for REST API)

export function useSessionControl(videoRef, canvasRef) {
  const { state, sessionStarting, sessionStarted, sessionStopping, sessionStopped,
          frameResult, setError } = useSession()

  const intervalRef  = useRef(null)
  const frameNumRef  = useRef(0)
  const isRunningRef = useRef(false)

  // ---------------------------------------------------------------
  // Capture one frame from <video> → base64 JPEG
  // ---------------------------------------------------------------
  const captureFrame = useCallback(() => {
    const video = videoRef.current
    if (!video) return null

    let targetW = video.videoWidth || 640
    let targetH = video.videoHeight || 480
    if (targetW <= 0 || targetH <= 0) return null

    const maxDim = 320
    if (targetW > maxDim) {
      const ratio = maxDim / targetW
      targetW = maxDim
      targetH = Math.round(targetH * ratio)
    }

    try {
      const offscreen = document.createElement('canvas')
      offscreen.width  = targetW
      offscreen.height = targetH
      const ctx = offscreen.getContext('2d')
      ctx.translate(offscreen.width, 0)
      ctx.scale(-1, 1)
      ctx.drawImage(video, 0, 0, offscreen.width, offscreen.height)
      return offscreen.toDataURL('image/jpeg', 0.4)
    } catch (e) {
      return null
    }
  }, [videoRef])

  // ---------------------------------------------------------------
  // Frame submission loop
  // ---------------------------------------------------------------
  const startFrameLoop = useCallback((sessionId) => {
    isRunningRef.current = true
    frameNumRef.current  = 0

    const sendNextFrame = async () => {
      if (!isRunningRef.current) return

      const frame = captureFrame()
      if (!frame) {
        // If webcam frame not available, retry after interval
        if (isRunningRef.current) {
          intervalRef.current = setTimeout(sendNextFrame, FRAME_INTERVAL_MS)
        }
        return
      }

      frameNumRef.current += 1
      try {
        const result = await processFrame(sessionId, frame, frameNumRef.current)
        if (isRunningRef.current) {
          frameResult(result)
          // Draw bounding boxes on canvas overlay
          drawBoundingBoxes(canvasRef.current, result, videoRef.current)
        }
      } catch (err) {
        console.warn('Frame processing error:', err)
        if (isRunningRef.current) {
          const status = err?.response?.status
          const errMsg = err?.response?.data?.error || err?.message || 'Network error'
          setError(`Frame error (${status || 'API'}): ${errMsg}`)
        }
      } finally {
        // Schedule next frame ONLY after previous request is finished!
        if (isRunningRef.current) {
          intervalRef.current = setTimeout(sendNextFrame, FRAME_INTERVAL_MS)
        }
      }
    }

    // Start loop
    sendNextFrame()
  }, [captureFrame, frameResult, canvasRef, videoRef, setError])

  const stopFrameLoop = useCallback(() => {
    isRunningRef.current = false
    if (intervalRef.current) {
      clearTimeout(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // ---------------------------------------------------------------
  // Start Session
  // ---------------------------------------------------------------
  const handleStart = useCallback(async () => {
    if (state.isActive) return
    try {
      sessionStarting()
      const data = await startSession()
      sessionStarted(data)
      startFrameLoop(data.session_id)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to start session. Is the backend running?')
    }
  }, [state.isActive, sessionStarting, sessionStarted, startFrameLoop, setError])

  // ---------------------------------------------------------------
  // Stop Session
  // ---------------------------------------------------------------
  const handleStop = useCallback(async () => {
    if (!state.isActive || !state.sessionId) return
    stopFrameLoop()
    try {
      sessionStopping()
      const data = await stopSession(state.sessionId)
      sessionStopped(data)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to stop session.')
    }
  }, [state.isActive, state.sessionId, stopFrameLoop, sessionStopping, sessionStopped, setError])

  return { handleStart, handleStop }
}

// ---------------------------------------------------------------
// Draw bounding boxes + emotion labels on overlay canvas
// ---------------------------------------------------------------
function drawBoundingBoxes(canvas, result, video) {
  if (!canvas || !video) return
  const ctx = canvas.getContext('2d')
  const rawW = video.videoWidth  || 640
  const rawH = video.videoHeight || 480
  const maxDim = 480

  let frameW = rawW
  let frameH = rawH
  if (rawW > maxDim) {
    const ratio = maxDim / rawW
    frameW = maxDim
    frameH = Math.round(rawH * ratio)
  }

  const scaleX = canvas.width  / frameW
  const scaleY = canvas.height / frameH

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  if (!result?.faces?.length) return

  result.faces.forEach(face => {
    const { x, y, w, h } = face.bbox
    const sx = x * scaleX
    const sy = y * scaleY
    const sw = w * scaleX
    const sh = h * scaleY

    // Box
    const isLowLight = face.quality_issues?.some(i => i.includes('too dark'))
    const isBrightLight = face.quality_issues?.some(i => i.includes('too bright'))
    const lightWarning = isLowLight ? ' ⚠️ Low Light' : (isBrightLight ? ' ⚠️ High Light' : '')

    ctx.strokeStyle = face.color || '#6c63ff'
    ctx.lineWidth   = 2
    ctx.shadowColor = face.color || '#6c63ff'
    ctx.shadowBlur  = 8
    
    if (isLowLight || isBrightLight) {
      ctx.setLineDash([6, 4])
    } else {
      ctx.setLineDash([])
    }
    
    ctx.strokeRect(sx, sy, sw, sh)
    ctx.setLineDash([])
    ctx.shadowBlur  = 0

    // Label background
    const label = `${face.emoji || ''} ${face.is_uncertain ? 'Uncertain' : face.emotion?.toUpperCase() || ''}${lightWarning}`
    const conf  = `${face.confidence?.toFixed(0)}%`
    ctx.font = 'bold 13px Inter, sans-serif'
    const textW = Math.max(ctx.measureText(label).width, ctx.measureText(conf).width) + 16
    const labelY = sy > 44 ? sy - 44 : sy + sh + 4

    ctx.fillStyle = 'rgba(0,0,0,0.75)'
    ctx.beginPath()
    ctx.roundRect(sx, labelY, textW, 40, 6)
    ctx.fill()

    // Label text
    ctx.fillStyle = face.color || '#6c63ff'
    ctx.fillText(label, sx + 8, labelY + 14)
    ctx.fillStyle = 'rgba(255,255,255,0.7)'
    ctx.font = '11px JetBrains Mono, monospace'
    ctx.fillText(conf, sx + 8, labelY + 30)
  })
}
