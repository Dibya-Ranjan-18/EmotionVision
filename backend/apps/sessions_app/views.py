"""
Sessions App – Views
POST /api/start-session/   → Creates a new session, returns session_id
POST /api/stop-session/    → Closes session, computes analytics
"""

import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Session
from .serializers import SessionSerializer
from ..emotion.models import EmotionLog
from ..behavior.models import BehaviorLog
from ..analytics.models import SessionAnalytics
from ai_pipeline.pipeline import release_pipeline

logger = logging.getLogger(__name__)


class StartSessionView(APIView):
    """POST /api/start-session/ — Creates and returns a new session."""

    def post(self, request):
        session = Session.objects.create(status='active')
        logger.info(f"Session {session.id} started.")
        return Response({
            'session_id': session.id,
            'start_time': session.start_time.isoformat(),
            'status': session.status,
        }, status=status.HTTP_201_CREATED)


class StopSessionView(APIView):
    """POST /api/stop-session/ — Closes session and computes summary analytics."""

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        try:
            session = Session.objects.get(id=session_id, status='active')
        except Session.DoesNotExist:
            return Response({'error': 'Session not found or already closed'}, status=404)

        session.end_time = timezone.now()
        session.status = 'completed'

        # Aggregate emotion logs
        logs = EmotionLog.objects.filter(session=session)
        total_frames = logs.count()
        session.total_frames = total_frames

        if total_frames > 0:
            from django.db.models import Avg
            avg_conf = logs.aggregate(avg=Avg('confidence'))['avg'] or 0.0
            session.avg_confidence = round(avg_conf, 2)

            # Dominant emotion
            from collections import Counter
            emotions = list(logs.values_list('emotion', flat=True))
            if emotions:
                dominant = Counter(emotions).most_common(1)[0][0]
                session.dominant_emotion = dominant

            # FPS
            fps_vals = list(logs.values_list('processing_time_ms', flat=True))
            valid_fps = [1000.0 / ms for ms in fps_vals if ms > 0]
            session.avg_fps = round(sum(valid_fps) / len(valid_fps), 1) if valid_fps else 0.0

        session.save()

        # Build emotion distribution
        from django.db.models import Count
        dist_qs = logs.values('emotion').annotate(count=Count('id'))
        distribution = {row['emotion']: row['count'] for row in dist_qs}

        # Emotion change count
        emotion_changes = 0
        prev = None
        for e in logs.order_by('timestamp').values_list('emotion', flat=True):
            if prev and e != prev:
                emotion_changes += 1
            prev = e

        # Save analytics
        SessionAnalytics.objects.update_or_create(
            session=session,
            defaults={
                'dominant_emotion': session.dominant_emotion,
                'avg_confidence': session.avg_confidence,
                'total_frames': total_frames,
                'avg_fps': session.avg_fps,
                'total_emotion_changes': emotion_changes,
                'emotion_distribution': distribution,
                'detection_accuracy_estimate': min(99.0, session.avg_confidence * 1.05),
            }
        )

        # Release AI pipeline
        release_pipeline(session_id)

        return Response({
            'session_id': session.id,
            'duration_seconds': session.duration_seconds,
            'dominant_emotion': session.dominant_emotion,
            'avg_confidence': session.avg_confidence,
            'total_frames': total_frames,
            'avg_fps': session.avg_fps,
            'emotion_changes': emotion_changes,
            'emotion_distribution': distribution,
            'status': 'completed',
        })
