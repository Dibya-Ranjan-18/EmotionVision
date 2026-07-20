"""
Diagnostic endpoint - GET /api/debug/
Tests MediaPipe Solutions API face detection with a synthetic test image.
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
    """GET /api/debug/ — AI pipeline diagnostics."""

    def get(self, request):
        info = {
            'python': sys.version,
            'opencv': cv2.__version__,
        }

        # MediaPipe Solutions API test
        try:
            import mediapipe as mp
            info['mediapipe'] = mp.__version__
            info['mediapipe_solutions_face_detection'] = str(mp.solutions.face_detection)

            # Try init
            fd = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=0.1,
            )
            info['face_detection_init'] = 'SUCCESS'
            fd.close()
        except Exception as e:
            info['mediapipe_error'] = str(e)

        # hsemotion test
        try:
            from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
            info['hsemotion_onnx'] = 'available'
        except Exception as e:
            info['hsemotion_onnx'] = f'UNAVAILABLE: {e}'

        # Test FaceDetector from our pipeline
        try:
            from ai_pipeline.detector import FaceDetector, _MP_AVAILABLE
            info['mp_available_flag'] = _MP_AVAILABLE
            fd = FaceDetector(min_detection_confidence=0.1)
            info['face_detection_initialized'] = fd._face_detection is not None
            info['face_mesh_initialized'] = fd._face_mesh is not None

            # Test on a synthetic 640x480 image with a skin-colored ellipse
            test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 80  # dark background
            cv2.ellipse(test_frame, (320, 240), (100, 130), 0, 0, 360, (180, 150, 130), -1)
            cv2.ellipse(test_frame, (285, 210), (18, 22), 0, 0, 360, (80, 60, 50), -1)
            cv2.ellipse(test_frame, (355, 210), (18, 22), 0, 0, 360, (80, 60, 50), -1)

            detections = fd.detect(test_frame)
            info['synthetic_test_detections'] = len(detections)
            fd.release()
        except Exception as e:
            import traceback
            info['face_detector_error'] = str(e)
            info['face_detector_traceback'] = traceback.format_exc()

        return Response(info)
