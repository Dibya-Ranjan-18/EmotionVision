/**
 * useWebcam — Manages webcam initialization and video element binding.
 */
import { useEffect, useRef, useState, useCallback } from 'react'

export function useWebcam() {
  const videoRef  = useRef(null)
  const streamRef = useRef(null)
  const [isReady, setIsReady] = useState(false)
  const [error, setError]     = useState(null)
  const [devices, setDevices] = useState([])
  const [activeDeviceId, setActiveDeviceId] = useState(null)

  const startCamera = useCallback(async (deviceId = null) => {
    // Stop any existing stream first
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
    }
    setError(null)
    setIsReady(false)

    const constraints = {
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user',
        ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
      },
      audio: false,
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play()
          setIsReady(true)
        }
      }

      // Enumerate devices for camera switching
      const allDevices = await navigator.mediaDevices.enumerateDevices()
      const cams = allDevices.filter(d => d.kind === 'videoinput')
      setDevices(cams)
      setActiveDeviceId(stream.getVideoTracks()[0]?.getSettings()?.deviceId || null)
    } catch (err) {
      const msg = err.name === 'NotAllowedError'
        ? 'Camera permission denied. Please allow camera access in your browser.'
        : err.name === 'NotFoundError'
        ? 'No camera found. Please connect a webcam.'
        : `Camera error: ${err.message}`
      setError(msg)
      setIsReady(false)
    }
  }, [])

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsReady(false)
  }, [])

  // Auto-start on mount
  useEffect(() => {
    startCamera()
    return () => stopCamera()
  }, [])

  return { videoRef, isReady, error, devices, activeDeviceId, startCamera, stopCamera }
}
