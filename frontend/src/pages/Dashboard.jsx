import React, { useState, useEffect } from 'react'
import { useSession } from '../context/SessionContext'

import CameraFeed      from '../components/CameraFeed'
import EmotionCard     from '../components/EmotionCard'
import ConfidenceMeter from '../components/ConfidenceMeter'
import SummaryModal    from '../components/SummaryModal'

export default function Dashboard() {
  const { state } = useSession()
  const { summary } = state
  const [showSummary, setShowSummary] = useState(false)

  // Auto-show summary when session ends
  useEffect(() => {
    if (summary) setShowSummary(true)
  }, [summary])

  return (
    <main className="main-content" id="main">
      <div className="responsive-dashboard-grid">
        {/* Left: Camera Feed */}
        <div style={{ height: '100%' }}>
          <CameraFeed />
        </div>

        {/* Right: Emotion + Confidence stacked */}
        <div className="right-column-stack">
          <div className="right-card-wrapper-top">
            <EmotionCard />
          </div>
          <div className="right-card-wrapper-bottom">
            <ConfidenceMeter />
          </div>
        </div>
      </div>

      {/* Session Summary Modal */}
      {showSummary && summary && (
        <SummaryModal onClose={() => setShowSummary(false)} />
      )}
    </main>
  )
}
