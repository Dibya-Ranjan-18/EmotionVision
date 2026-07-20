import axios from 'axios'

// Robustly resolve API base URL regardless of trailing slashes or /api prefix in env var
let rawBase = import.meta.env.VITE_API_URL || '/api'
rawBase = rawBase.trim().replace(/\/+$/, '')
if (!rawBase.endsWith('/api') && rawBase.startsWith('http')) {
  rawBase += '/api'
}
const BASE_URL = rawBase.endsWith('/') ? rawBase : `${rawBase}/`

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// ---------------------------------------------------------------
// Session APIs
// ---------------------------------------------------------------
export const startSession = () =>
  api.post('start-session/').then(r => r.data)

export const stopSession = (sessionId) =>
  api.post('stop-session/', { session_id: sessionId }).then(r => r.data)

// ---------------------------------------------------------------
// Frame Processing
// ---------------------------------------------------------------
export const processFrame = (sessionId, frameBase64, frameNumber) =>
  api.post('process-frame/', {
    session_id: sessionId,
    frame: frameBase64,
    frame_number: frameNumber,
  }).then(r => r.data)

// ---------------------------------------------------------------
// Live Data
// ---------------------------------------------------------------
export const getLiveData = (sessionId, limit = 20) =>
  api.get('live-data/', { params: { session_id: sessionId, limit } }).then(r => r.data)

// ---------------------------------------------------------------
// Session Summary
// ---------------------------------------------------------------
export const getSessionSummary = (sessionId) =>
  api.get('session-summary/', { params: { session_id: sessionId } }).then(r => r.data)

// ---------------------------------------------------------------
// PDF Export — returns a download URL
// ---------------------------------------------------------------
export const exportPDF = (sessionId) =>
  `${BASE_URL}export-pdf/?session_id=${sessionId}`

export default api
