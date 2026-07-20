"""
Analytics App – Views
GET /api/session-summary/?session_id=<id>  → Full summary for a completed session
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response

from ..sessions_app.models import Session
from ..emotion.models import EmotionLog
from ..behavior.models import BehaviorLog
from ..analytics.models import SessionAnalytics

logger = logging.getLogger(__name__)


class SessionSummaryView(APIView):
    """GET /api/session-summary/ — Returns full analytics for a session."""

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        # Timeline
        logs = EmotionLog.objects.filter(session=session).order_by('timestamp')
        timeline = [{
            'timestamp': log.timestamp.strftime('%H:%M:%S'),
            'emotion': log.emotion,
            'confidence': log.confidence,
            'face_count': log.face_count,
        } for log in logs]

        # Distribution
        from django.db.models import Count, Avg
        dist_qs = logs.values('emotion').annotate(count=Count('id'))
        distribution = {row['emotion']: row['count'] for row in dist_qs}

        # Emotion changes
        emotion_changes = 0
        prev = None
        for e in logs.values_list('emotion', flat=True):
            if prev and e != prev:
                emotion_changes += 1
            prev = e

        # Analytics record
        try:
            analytics = session.analytics
            analytics_data = {
                'dominant_emotion': analytics.dominant_emotion,
                'avg_confidence': analytics.avg_confidence,
                'total_frames': analytics.total_frames,
                'avg_fps': analytics.avg_fps,
                'total_emotion_changes': analytics.total_emotion_changes,
                'face_count_max': analytics.face_count_max,
                'detection_accuracy_estimate': analytics.detection_accuracy_estimate,
                'emotion_distribution': analytics.emotion_distribution,
            }
        except SessionAnalytics.DoesNotExist:
            avg_conf = logs.aggregate(avg=Avg('confidence'))['avg'] or 0.0
            analytics_data = {
                'dominant_emotion': session.dominant_emotion,
                'avg_confidence': round(avg_conf, 2),
                'total_frames': logs.count(),
                'avg_fps': session.avg_fps,
                'total_emotion_changes': emotion_changes,
                'face_count_max': 0,
                'detection_accuracy_estimate': min(99.0, avg_conf * 1.05),
                'emotion_distribution': distribution,
            }

        # Behavior summary
        beh_logs = BehaviorLog.objects.filter(session=session)
        blink_total = sum(b.blink_count for b in beh_logs)
        smile_frames = beh_logs.filter(smile_detected=True).count()

        return Response({
            'session_id': session.id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration_seconds': session.duration_seconds,
            'status': session.status,
            'timeline': timeline,
            'distribution': distribution,
            'emotion_changes': emotion_changes,
            'analytics': analytics_data,
            'behavior_summary': {
                'total_blinks': blink_total,
                'smile_frames': smile_frames,
            },
        })
