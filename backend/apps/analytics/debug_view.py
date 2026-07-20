"""
Diagnostic endpoint - GET /api/debug/
Tests MediaPipe Tasks API face detection with detailed error reporting.
"""
import sys
import os
import cv2
import numpy as np
import logging
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)

MODELS_DIR = '/tmp/mediapipe_models'
DETECTOR_MODEL = os.path.join(MODELS_DIR, 'blaze_face_short_range.tflite')
DETECTOR_URL = 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'


class DebugView(APIView):
    """GET /api/debug/ — AI pipeline diagnostics."""

    def get(self, request):
        info = {
            'python': sys.version,
            'opencv': cv2.__version__,
        }

        # MediaPipe version + available attributes
        try:
            import mediapipe as mp
            info['mediapipe'] = mp.__version__
            info['has_solutions'] = hasattr(mp, 'solutions')
            info['has_tasks'] = hasattr(mp, 'tasks')
        except Exception as e:
            info['mediapipe'] = f'IMPORT ERROR: {e}'

        # Check model files
        info['models_dir'] = MODELS_DIR
        info['models_dir_exists'] = os.path.exists(MODELS_DIR)
        if os.path.exists(MODELS_DIR):
            files = {}
            for f in os.listdir(MODELS_DIR):
                fpath = os.path.join(MODELS_DIR, f)
                files[f] = os.path.getsize(fpath)
            info['model_files'] = files
        else:
            info['model_files'] = {}

        # Download model if not present or too small
        import urllib.request
        if not os.path.exists(DETECTOR_MODEL) or os.path.getsize(DETECTOR_MODEL) < 100000:
            try:
                os.makedirs(MODELS_DIR, exist_ok=True)
                urllib.request.urlretrieve(DETECTOR_URL, DETECTOR_MODEL)
                info['download'] = f'downloaded {os.path.getsize(DETECTOR_MODEL)} bytes'
            except Exception as e:
                info['download_error'] = str(e)
        else:
            info['download'] = f'already exists ({os.path.getsize(DETECTOR_MODEL)} bytes)'

        # Try Tasks API initialization
        try:
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            from mediapipe.tasks.python.core import base_options as mp_base_options

            opts = mp_vision.FaceDetectorOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=DETECTOR_MODEL),
                min_detection_confidence=0.1,
            )
            detector = mp_vision.FaceDetector.create_from_options(opts)
            info['tasks_api_init'] = 'SUCCESS'

            # Test detection on synthetic image
            test_img = np.zeros((480, 640, 3), dtype=np.uint8)
            test_img[:] = (60, 60, 60)
            cv2.ellipse(test_img, (320, 240), (100, 130), 0, 0, 360, (180, 150, 130), -1)
            cv2.ellipse(test_img, (285, 210), (18, 22), 0, 0, 360, (40, 40, 80), -1)
            cv2.ellipse(test_img, (355, 210), (18, 22), 0, 0, 360, (40, 40, 80), -1)
            cv2.ellipse(test_img, (320, 280), (50, 20), 0, 0, 180, (100, 70, 70), -1)

            rgb = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
            rgb = np.ascontiguousarray(rgb)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect(mp_image)
            info['synthetic_detections'] = len(result.detections)
            info['tasks_api_detection'] = 'WORKING'
        except Exception as e:
            info['tasks_api_error'] = str(e)
            info['tasks_api_traceback'] = traceback.format_exc()[-800:]

        # hsemotion
        try:
            from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
            info['hsemotion_onnx'] = 'available'
        except Exception as e:
            info['hsemotion_onnx'] = f'ERROR: {e}'

        return Response(info)
