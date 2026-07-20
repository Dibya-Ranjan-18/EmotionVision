"""
AI Pipeline – Face Detector
Uses MediaPipe FaceDetector (Tasks API v0.10+) for multi-face detection,
with FaceLandmarker for mesh landmarks.
MediaPipe models are downloaded on first use from Google's CDN.
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
    logger.warning(f"MediaPipe Tasks API not available: {e}.")

# Model asset paths — downloaded on first use to a writable /tmp dir (works on Render)
_MODELS_DIR = os.environ.get('MEDIAPIPE_MODELS_DIR', '/tmp/mediapipe_models')
_FACE_DETECTOR_MODEL = os.path.join(_MODELS_DIR, 'blaze_face_short_range.tflite')
_FACE_LANDMARKER_MODEL = os.path.join(_MODELS_DIR, 'face_landmarker.task')

_MODEL_URLS = {
    _FACE_DETECTOR_MODEL: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
    _FACE_LANDMARKER_MODEL: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
}


def _ensure_model(path: str, url: str) -> bool:
    """Download model file if it doesn't exist."""
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logger.info(f"Downloading MediaPipe model: {os.path.basename(path)} ...")
    try:
        urllib.request.urlretrieve(url, path)
        size_kb = os.path.getsize(path) // 1024
        logger.info(f"Downloaded {os.path.basename(path)} ({size_kb} KB)")
        return True
    except Exception as e:
        logger.error(f"Could not download model from {url}: {e}")
        if os.path.exists(path):
            os.remove(path)
        return False


class FaceDetector:
    """
    Detects faces using MediaPipe Tasks API (v0.10+).
    Downloads model files on first use if not cached.
    """

    def __init__(self, min_detection_confidence: float = 0.25):
        self.min_confidence = min_detection_confidence
        self._mp_detector = None
        self._mp_landmarker = None
        self._init_detector()

    def _init_detector(self):
        if _MP_AVAILABLE:
            try:
                self._init_mp_tasks()
                logger.info("FaceDetector ready using MediaPipe.")
            except Exception as e:
                logger.error(f"MediaPipe FaceDetector init failed: {e}")
        else:
            logger.error("MediaPipe is not available. Face detection will return empty results.")

    def _init_mp_tasks(self):
        # Face detector model
        if _ensure_model(_FACE_DETECTOR_MODEL, _MODEL_URLS[_FACE_DETECTOR_MODEL]):
            opts = mp_vision.FaceDetectorOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=_FACE_DETECTOR_MODEL),
                min_detection_confidence=self.min_confidence,
            )
            self._mp_detector = mp_vision.FaceDetector.create_from_options(opts)
            logger.info("MediaPipe FaceDetector (Tasks) initialised.")

        # Face landmarker model (for mesh landmarks used in behavior analysis)
        if _ensure_model(_FACE_LANDMARKER_MODEL, _MODEL_URLS[_FACE_LANDMARKER_MODEL]):
            lm_opts = mp_vision.FaceLandmarkerOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=_FACE_LANDMARKER_MODEL),
                num_faces=5,
                min_face_detection_confidence=0.25,
                min_face_presence_score=0.25,
                min_tracking_confidence=0.25,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )
            self._mp_landmarker = mp_vision.FaceLandmarker.create_from_options(lm_opts)
            logger.info("MediaPipe FaceLandmarker (Tasks) initialised.")

    # ------------------------------------------------------------------

    def detect(self, frame_bgr: np.ndarray) -> list:
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
                logger.warning(f"MediaPipe detect error: {e}")
                return []

        # No detector available
        logger.warning("No face detector available. Returning empty results.")
        return []

    def _detect_mp(self, frame_bgr, h, w):
        """MediaPipe Tasks-based detection."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = np.ascontiguousarray(frame_rgb)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        detection_result = self._mp_detector.detect(mp_image)

        results = []
        for det in detection_result.detections:
            bbox_mp = det.bounding_box
            x = max(0, bbox_mp.origin_x)
            y = max(0, bbox_mp.origin_y)
            bw = min(bbox_mp.width, w - x)
            bh = min(bbox_mp.height, h - y)

            if bw <= 0 or bh <= 0:
                continue

            confidence = det.categories[0].score if det.categories else 0.5

            # Get mesh landmarks if landmarker is available
            mesh_landmarks = self._get_mesh_landmarks(frame_rgb, h, w)

            results.append({
                'bbox': (x, y, bw, bh),
                'confidence': float(confidence),
                'landmarks': None,
                'mesh_landmarks': mesh_landmarks,
            })

        return results

    def _get_mesh_landmarks(self, frame_rgb, h, w):
        """Get face mesh landmarks using FaceLandmarker."""
        if not self._mp_landmarker:
            return None
        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            lm_result = self._mp_landmarker.detect(mp_image)
            if lm_result.face_landmarks:
                return lm_result.face_landmarks[0]
        except Exception as e:
            logger.debug(f"Landmarker error: {e}")
        return None
