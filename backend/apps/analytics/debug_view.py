"""
Diagnostic endpoint to test face detection directly on Render backend.
GET /api/debug/ — Returns system info and face detection test results.
"""
import sys
import cv2
import numpy as np
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import path

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

        # Test OpenCV Haar cascade using bundled file
        try:
            import os as _os
            ai_pipeline_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'ai_pipeline')
            bundled_cascade = _os.path.join(ai_pipeline_dir, 'haarcascade_frontalface_default.xml')
            info['bundled_cascade_path'] = bundled_cascade
            info['bundled_cascade_exists'] = _os.path.exists(bundled_cascade)

            if _os.path.exists(bundled_cascade):
                haar = cv2.CascadeClassifier(bundled_cascade)
                info['haar_cascade'] = 'loaded' if not haar.empty() else 'EMPTY/FAILED'
            else:
                # Fallback to cv2.data.haarcascades
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                info['cv2_data_path'] = cascade_path
                info['cv2_data_exists'] = _os.path.exists(cascade_path)
                haar = cv2.CascadeClassifier(cascade_path)
                info['haar_cascade'] = 'loaded' if not haar.empty() else 'EMPTY/FAILED'
        except Exception as e:
            info['haar_cascade'] = f'ERROR: {e}'
            haar = None

        # Create a synthetic test image (128x128 gray gradient - no real face)
        try:
            test_img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Draw a simple oval to simulate a face
            cv2.ellipse(test_img, (320, 240), (100, 130), 0, 0, 360, (180, 150, 130), -1)
            cv2.ellipse(test_img, (285, 210), (20, 25), 0, 0, 360, (80, 60, 50), -1)  # left eye
            cv2.ellipse(test_img, (355, 210), (20, 25), 0, 0, 360, (80, 60, 50), -1)  # right eye

            gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces_detected = haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
            info['haar_test_faces'] = int(len(faces_detected)) if hasattr(faces_detected, '__len__') else 0
        except Exception as e:
            info['haar_test_faces'] = f'ERROR: {e}'

        # Test MediaPipe model files
        import os
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai_pipeline', '_models')
        info['models_dir_exists'] = os.path.exists(models_dir)
        if os.path.exists(models_dir):
            info['model_files'] = os.listdir(models_dir)
        else:
            info['model_files'] = []

        return Response(info)
