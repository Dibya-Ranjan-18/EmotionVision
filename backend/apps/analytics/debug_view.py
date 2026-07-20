"""
Diagnostic endpoint to test face detection directly on Render backend.
GET /api/debug/ — Returns system info and face detection test results.
"""
import sys
import os
import cv2
import numpy as np
import logging
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class DebugView(APIView):
    """GET /api/debug/ — returns AI pipeline diagnostics."""

    def get(self, request):
        info = {
            'python': sys.version,
            'opencv': cv2.__version__,
        }

        # Test MediaPipe availability
        try:
            import mediapipe as mp
            info['mediapipe'] = mp.__version__
        except Exception as e:
            info['mediapipe'] = f'UNAVAILABLE: {e}'

        # Test HSEmotionONNX
        try:
            from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
            info['hsemotion_onnx'] = 'available'
        except Exception as e:
            info['hsemotion_onnx'] = f'UNAVAILABLE: {e}'

        # Check MediaPipe models directory (/tmp/mediapipe_models)
        models_dir = os.environ.get('MEDIAPIPE_MODELS_DIR', '/tmp/mediapipe_models')
        info['models_dir'] = models_dir
        info['models_dir_exists'] = os.path.exists(models_dir)
        if os.path.exists(models_dir):
            info['model_files'] = os.listdir(models_dir)
        else:
            info['model_files'] = []

        # Try to download models now
        try:
            from ai_pipeline.detector import _ensure_model, _FACE_DETECTOR_MODEL, _FACE_LANDMARKER_MODEL, _MODEL_URLS
            info['face_detector_model_path'] = _FACE_DETECTOR_MODEL
            info['face_detector_exists'] = os.path.exists(_FACE_DETECTOR_MODEL)

            if not os.path.exists(_FACE_DETECTOR_MODEL):
                info['download_attempt'] = 'downloading...'
                ok = _ensure_model(_FACE_DETECTOR_MODEL, _MODEL_URLS[_FACE_DETECTOR_MODEL])
                info['download_result'] = 'success' if ok else 'FAILED'
                info['face_detector_exists_after'] = os.path.exists(_FACE_DETECTOR_MODEL)
            else:
                info['download_attempt'] = 'skipped (already exists)'
        except Exception as e:
            info['download_error'] = str(e)

        # Try to initialize FaceDetector directly
        try:
            from ai_pipeline.detector import FaceDetector
            fd = FaceDetector()
            info['detector_mp_detector'] = 'initialized' if fd._mp_detector else 'None (FAILED)'
            info['detector_mp_landmarker'] = 'initialized' if fd._mp_landmarker else 'None'
        except Exception as e:
            info['detector_init_error'] = str(e)

        return Response(info)
