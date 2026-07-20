"""
Emotion App – Views
POST /api/process-frame/   → Main AI endpoint: accepts base64 frame, returns full analysis
GET  /api/live-data/       → Returns latest emotion log for a session
"""

import logging
import time
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..sessions_app.models import Session
from ..emotion.models import EmotionLog, FaceLog
from ..behavior.models import BehaviorLog
from ai_pipeline.pipeline import get_pipeline
from ai_pipeline.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


class ProcessFrameView(APIView):
    """
    POST /api/process-frame/

    Request body:
    {
      "session_id": 1,
      "frame": "<base64 JPEG string>",   // data URL or raw base64
      "frame_number": 42
    }

    Response: Full AI analysis result for all detected faces.
    """

    def post(self, request):
        session_id = request.data.get('session_id')
        frame_b64  = request.data.get('frame')
        frame_num  = request.data.get('frame_number', 0)

        # --- Validate ---
        if not session_id or not frame_b64:
            return Response({'error': 'session_id and frame are required'}, status=400)

        try:
            session = Session.objects.get(id=session_id, status='active')
        except Session.DoesNotExist:
            return Response({'error': 'Active session not found'}, status=404)

        # --- Decode frame ---
        frame_bgr = ImagePreprocessor.decode_base64_frame(frame_b64)
        if frame_bgr is None:
            return Response({'error': 'Failed to decode frame'}, status=400)

        # --- Run AI pipeline ---
        pipeline = get_pipeline(session_id)
        result = pipeline.process_frame(frame_bgr)

        # --- Persist to DB ---
        primary = result.get('primary')
        if primary:
            emotion_label = primary['emotion'] if not primary['is_uncertain'] else 'uncertain'
            EmotionLog.objects.create(
                session=session,
                emotion=emotion_label,
                confidence=primary['confidence'],
                face_count=result['face_count'],
                processing_time_ms=result['processing_time_ms'],
                frame_number=frame_num,
                face_index=primary.get('face_index', 0),
            )

            # Behavior log
            beh = primary.get('behavior', {})
            if beh:
                BehaviorLog.objects.create(
                    session=session,
                    face_index=primary['face_index'],
                    smile_detected=beh.get('smile_detected', False),
                    smile_score=beh.get('smile_score', 0.0),
                    left_eye_open=beh.get('left_eye_open', True),
                    right_eye_open=beh.get('right_eye_open', True),
                    blink_detected=beh.get('blink_detected', False),
                    blink_count=beh.get('blink_count', 0),
                    head_direction=beh.get('head_direction', 'center'),
                    yaw_angle=beh.get('yaw_angle', 0.0),
                    pitch_angle=beh.get('pitch_angle', 0.0),
                    face_present=beh.get('face_present', True),
                    face_count=result['face_count'],
                )

        # Face logs
        for face in result['faces']:
            x, y, w, h = face['bbox']
            FaceLog.objects.create(
                session=session,
                face_index=face['face_index'],
                bbox_x=x, bbox_y=y, bbox_w=w, bbox_h=h,
                emotion=face['emotion'],
                confidence=face['confidence'],
            )

        # --- Serialise response ---
        def serialise_face(f):
            beh = f.get('behavior', {})
            return {
                'face_index': f['face_index'],
                'bbox': {'x': f['bbox'][0], 'y': f['bbox'][1], 'w': f['bbox'][2], 'h': f['bbox'][3]},
                'emotion': f['emotion'],
                'raw_emotion': f['raw_emotion'],
                'confidence': f['confidence'],
                'all_scores': f['all_scores'],
                'is_uncertain': f['is_uncertain'],
                'emoji': f['emoji'],
                'color': f['color'],
                'quality_ok': f['quality_ok'],
                'quality_score': f['quality_score'],
                'quality_issues': f['quality_issues'],
                'behavior': {
                    'smile_detected': beh.get('smile_detected', False),
                    'smile_score': beh.get('smile_score', 0.0),
                    'left_eye_open': beh.get('left_eye_open', True),
                    'right_eye_open': beh.get('right_eye_open', True),
                    'blink_detected': beh.get('blink_detected', False),
                    'blink_count': beh.get('blink_count', 0),
                    'head_direction': beh.get('head_direction', 'center'),
                    'yaw_angle': beh.get('yaw_angle', 0.0),
                    'pitch_angle': beh.get('pitch_angle', 0.0),
                    'face_present': beh.get('face_present', True),
                    'face_count': result['face_count'],
                }
            }

        return Response({
            'session_id': session_id,
            'frame_number': result['frame_number'],
            'face_count': result['face_count'],
            'fps': result['fps'],
            'processing_time_ms': result['processing_time_ms'],
            'faces': [serialise_face(f) for f in result['faces']],
            'primary': serialise_face(result['primary']) if result.get('primary') else None,
            'timestamp': timezone.now().isoformat(),
        })


class LiveDataView(APIView):
    """
    GET /api/live-data/?session_id=<id>&limit=<n>
    Returns recent emotion timeline entries for charting.
    """

    def get(self, request):
        session_id = request.query_params.get('session_id')
        limit = int(request.query_params.get('limit', 20))

        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        logs = EmotionLog.objects.filter(
            session_id=session_id
        ).order_by('-timestamp')[:limit]

        timeline = [{
            'timestamp': log.timestamp.isoformat(),
            'emotion': log.emotion,
            'confidence': log.confidence,
            'face_count': log.face_count,
            'processing_time_ms': log.processing_time_ms,
        } for log in reversed(list(logs))]

        # Emotion distribution
        from django.db.models import Count
        dist_qs = EmotionLog.objects.filter(session_id=session_id)\
                   .values('emotion').annotate(count=Count('id'))
        distribution = {row['emotion']: row['count'] for row in dist_qs}

        # Latest behavior
        latest_behavior = None
        beh_log = BehaviorLog.objects.filter(session_id=session_id).order_by('-timestamp').first()
        if beh_log:
            latest_behavior = {
                'smile_detected': beh_log.smile_detected,
                'smile_score': beh_log.smile_score,
                'left_eye_open': beh_log.left_eye_open,
                'right_eye_open': beh_log.right_eye_open,
                'blink_count': beh_log.blink_count,
                'head_direction': beh_log.head_direction,
                'yaw_angle': beh_log.yaw_angle,
                'pitch_angle': beh_log.pitch_angle,
                'face_count': beh_log.face_count,
            }

        return Response({
            'timeline': timeline,
            'distribution': distribution,
            'latest_behavior': latest_behavior,
            'total_logs': EmotionLog.objects.filter(session_id=session_id).count(),
        })
