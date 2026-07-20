"""
AI Pipeline – Face Detector
Uses MediaPipe FaceDetector (Tasks API v0.10+) for multi-face detection,
with FaceLandmarker for mesh landmarks.
Falls back to OpenCV Haar cascade if MediaPipe is unavailable.
"""

import cv2
import numpy as np
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MediaPipe Tasks API import (v0.10+)
# ---------------------------------------------------------------------------
_MP_AVAILABLE = False
_FaceDetector = None
_FaceLandmarker = None
_RunningMode = None

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    from mediapipe.tasks.python.core import base_options as mp_base_options

    _MP_AVAILABLE = True
    logger.info(f"MediaPipe {mp.__version__} (Tasks API) available.")
except ImportError as e:
    logger.warning(f"MediaPipe Tasks API not available: {e}. Using OpenCV Haar fallback.")

# Model asset paths — downloaded on first use
_MODELS_DIR = os.path.join(os.path.dirname(__file__), '_models')
_FACE_DETECTOR_MODEL  = os.path.join(_MODELS_DIR, 'blaze_face_short_range.tflite')
_FACE_LANDMARKER_MODEL = os.path.join(_MODELS_DIR, 'face_landmarker.task')

_MODEL_URLS = {
    _FACE_DETECTOR_MODEL:  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
    _FACE_LANDMARKER_MODEL:'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
}


def _ensure_model(path: str, url: str):
    """Download model file if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        logger.info(f"Downloading MediaPipe model from {url}…")
        try:
            urllib.request.urlretrieve(url, path)
            logger.info(f"Downloaded: {path}")
        except Exception as e:
            logger.warning(f"Could not download model: {e}")
            return False
    return True


class FaceDetector:
    """
    Detects faces using MediaPipe Tasks API (v0.10+) or OpenCV Haar fallback.
    Returns list of face dicts with bbox, confidence, and landmarks.
    """

    def __init__(self, min_detection_confidence: float = 0.5):
        self.min_confidence = min_detection_confidence
        self._mp_detector    = None
        self._mp_landmarker  = None
        self._haar = None
        self._init_detector()

    def _init_detector(self):
        self._init_haar()  # Always initialize Haar cascade fallback
        if _MP_AVAILABLE:
            try:
                self._init_mp_tasks()
            except Exception as e:
                logger.warning(f"MediaPipe Tasks init failed ({e}), using Haar fallback.")

    def _init_mp_tasks(self):
        # Face detector
        if _ensure_model(_FACE_DETECTOR_MODEL, _MODEL_URLS[_FACE_DETECTOR_MODEL]):
            opts = mp_vision.FaceDetectorOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=_FACE_DETECTOR_MODEL),
                min_detection_confidence=self.min_confidence,
            )
            self._mp_detector = mp_vision.FaceDetector.create_from_options(opts)
            logger.info("MediaPipe FaceDetector (Tasks) initialised.")

        # Face landmarker
        if _ensure_model(_FACE_LANDMARKER_MODEL, _MODEL_URLS[_FACE_LANDMARKER_MODEL]):
            lm_opts = mp_vision.FaceLandmarkerOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=_FACE_LANDMARKER_MODEL),
                num_faces=5,
                min_face_detection_confidence=0.5,
                min_face_presence_score=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )
            self._mp_landmarker = mp_vision.FaceLandmarker.create_from_options(lm_opts)
            logger.info("MediaPipe FaceLandmarker (Tasks) initialised.")

    def _init_haar(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self._haar = cv2.CascadeClassifier(cascade_path)
        logger.info("OpenCV Haar cascade initialised.")

    # ------------------------------------------------------------------

    def detect(self, frame_bgr: np.ndarray) -> list[dict]:
        """
        Detect faces in a BGR frame.
        Returns list of { bbox, confidence, landmarks, mesh_landmarks }.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        h, w = frame_bgr.shape[:2]

        if self._mp_detector:
            try:
                return self._detect_mp(frame_bgr, h, w)
            except Exception as e:
                logger.warning(f"MediaPipe detect failed at runtime ({e}), falling back to Haar cascade.")
                return self._detect_haar(frame_bgr)
        else:
            return self._detect_haar(frame_bgr)

    def _detect_mp(self, frame_bgr, h, w):
        """MediaPipe Tasks-based detection."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        detection_result = self._mp_detector.detect(mp_image)
        mesh_per_face = []

        if self._mp_landmarker:
            lm_result = self._mp_landmarker.detect(mp_image)
            if lm_result.face_landmarks:
                for face_lm in lm_result.face_landmarks:
                    pts = [(lm.x * w, lm.y * h, lm.z) for lm in face_lm]
                    mesh_per_face.append(pts)

        results = []
        if detection_result.detections:
            for idx, det in enumerate(detection_result.detections):
                bb = det.bounding_box
                x  = max(0, bb.origin_x)
                y  = max(0, bb.origin_y)
                bw = min(bb.width,  w - x)
                bh = min(bb.height, h - y)

                score = det.categories[0].score if det.categories else 0.0

                results.append({
                    'bbox': (x, y, bw, bh),
                    'confidence': float(score),
                    'landmarks': {},
                    'mesh_landmarks': mesh_per_face[idx] if idx < len(mesh_per_face) else None,
                })

        return results

    def _detect_haar(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        # Apply histogram equalization for low-light enhancement
        gray = cv2.equalizeHist(gray)
        faces = self._haar.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3,
            minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
        )
        results = []
        for (x, y, fw, fh) in faces:
            results.append({
                'bbox': (int(x), int(y), int(fw), int(fh)),
                'confidence': 0.85,
                'landmarks': None,
                'mesh_landmarks': None,
            })
        return results

    def release(self):
        """Release MediaPipe resources."""
        if self._mp_detector:
            self._mp_detector.close()
        if self._mp_landmarker:
            self._mp_landmarker.close()
