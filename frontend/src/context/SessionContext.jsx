/**
 * SessionContext — Global state for the active analysis session.
 * Wraps the entire app so any component can read session state.
 */
import React, { createContext, useContext, useReducer, useCallback } from 'react'

const SessionContext = createContext(null)

const initialState = {
  sessionId: null,
  isActive: false,
  isStarting: false,
  isStopping: false,

  // Live data from last processed frame
  currentEmotion: null,
  currentConfidence: 0,
  currentEmoji: '❓',
  currentColor: '#7F8C8D',
  isUncertain: true,
  allScores: {},
  faceCount: 0,
  fps: 0,
  processingTimeMs: 0,
  frameNumber: 0,

  // Behavior
  behavior: null,

  // Multi-face data
  faces: [],
  primaryFace: null,

  // Timeline (in-memory, newest last)
  timeline: [],

  // Distribution counts
  distribution: {},

  // Session stats
  startTime: null,
  totalEmotionChanges: 0,
  totalFrames: 0,
  dominantEmotion: null,
  avgConfidence: 0,

  // Summary (after stop)
  summary: null,

  // Error
  error: null,

  // Theme
  theme: localStorage.getItem('ev-theme') || 'dark',
}

function reducer(state, action) {
  switch (action.type) {
    case 'SESSION_STARTING':
      return { ...state, isStarting: true, error: null }

    case 'SESSION_STARTED':
      return {
        ...state,
        isStarting: false,
        isActive: true,
        sessionId: action.payload.session_id,
        startTime: new Date(),
        timeline: [],
        distribution: {},
        totalEmotionChanges: 0,
        totalFrames: 0,
        summary: null,
        error: null,
      }

    case 'SESSION_STOPPING':
      return { ...state, isStopping: true }

    case 'SESSION_STOPPED':
      return {
        ...state,
        isStopping: false,
        isActive: false,
        summary: action.payload,
      }

    case 'FRAME_RESULT': {
      const r = action.payload
      const primary = r.primary

      // Build timeline entry
      const newEntry = primary
        ? {
            timestamp: new Date(r.timestamp),
            timeLabel: new Date(r.timestamp).toLocaleTimeString(),
            emotion: primary.emotion,
            confidence: primary.confidence,
            emoji: primary.emoji,
            color: primary.color,
            faceCount: r.face_count,
          }
        : null

      const newTimeline = newEntry
        ? [...state.timeline.slice(-199), newEntry]
        : state.timeline

      // Distribution update
      const newDist = { ...state.distribution }
      if (primary && !primary.is_uncertain) {
        newDist[primary.emotion] = (newDist[primary.emotion] || 0) + 1
      }

      // Count emotion changes
      const lastEmotion = state.timeline.length > 0
        ? state.timeline[state.timeline.length - 1].emotion
        : null
      const newChanges = (newEntry && lastEmotion && newEntry.emotion !== lastEmotion)
        ? state.totalEmotionChanges + 1
        : state.totalEmotionChanges

      return {
        ...state,
        faces: r.faces || [],
        primaryFace: primary || null,
        currentEmotion: primary?.emotion || null,
        currentConfidence: primary?.confidence || 0,
        currentEmoji: primary?.emoji || '❓',
        currentColor: primary?.color || '#7F8C8D',
        isUncertain: primary?.is_uncertain ?? true,
        allScores: primary?.all_scores || {},
        faceCount: r.face_count || 0,
        fps: r.fps || 0,
        processingTimeMs: r.processing_time_ms || 0,
        frameNumber: r.frame_number || 0,
        behavior: primary?.behavior || null,
        timeline: newTimeline,
        distribution: newDist,
        totalFrames: state.totalFrames + 1,
        totalEmotionChanges: newChanges,
        error: null,
      }
    }

    case 'SET_ERROR':
      return { ...state, error: action.payload, isStarting: false, isStopping: false }

    case 'CLEAR_ERROR':
      return { ...state, error: null }

    case 'TOGGLE_THEME': {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('ev-theme', newTheme)
      document.documentElement.setAttribute('data-theme', newTheme)
      return { ...state, theme: newTheme }
    }

    default:
      return state
  }
}

export function SessionProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  // Apply saved theme on mount
  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', state.theme)
  }, [])

  const sessionStarting = useCallback(() => dispatch({ type: 'SESSION_STARTING' }), [])
  const sessionStarted  = useCallback((data) => dispatch({ type: 'SESSION_STARTED', payload: data }), [])
  const sessionStopping = useCallback(() => dispatch({ type: 'SESSION_STOPPING' }), [])
  const sessionStopped  = useCallback((data) => dispatch({ type: 'SESSION_STOPPED', payload: data }), [])
  const frameResult     = useCallback((data) => dispatch({ type: 'FRAME_RESULT', payload: data }), [])
  const setError        = useCallback((msg) => dispatch({ type: 'SET_ERROR', payload: msg }), [])
  const clearError      = useCallback(() => dispatch({ type: 'CLEAR_ERROR' }), [])
  const toggleTheme     = useCallback(() => dispatch({ type: 'TOGGLE_THEME' }), [])

  return (
    <SessionContext.Provider value={{
      state,
      sessionStarting, sessionStarted,
      sessionStopping, sessionStopped,
      frameResult, setError, clearError,
      toggleTheme,
    }}>
      {children}
    </SessionContext.Provider>
  )
}

export const useSession = () => {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used inside SessionProvider')
  return ctx
}
