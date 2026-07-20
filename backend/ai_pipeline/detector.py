"""
AI Pipeline – Face Detector
Uses MediaPipe Tasks API (v0.10+) for face detection.
Model files are downloaded on first use to /tmp/mediapipe_models/.
"""

import cv2
import numpy as np
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

# MediaPipe Tasks API
_MP_AVAILABLE = False
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    from mediapipe.tasks.python.core import base_options as mp_base_options
    _MP_AVAILABLE = True
    logger.info(f"MediaPipe {mp.__version__} Tasks API available.")
except Exception as e:
    logger.error(f"MediaPipe Tasks API not available: {e}")

# Model paths - use /tmp which is writable on Render free tier
_MODELS_DIR = '/tmp/mediapipe_models'
_FACE_DETECTOR_MODEL = os.path.join(_MODELS_DIR, 'blaze_face_short_range.tflite')
_FACE_DETECTOR_URL = 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite'


def _ensure_model() -> bool:
    """Download face detector model if not present or too small."""
    min_size = 100_000  # ~700KB expected
    if os.path.exists(_FACE_DETECTOR_MODEL) and os.path.getsize(_FACE_DETECTOR_MODEL) >= min_size:
        logger.info(f"Model already present: {os.path.getsize(_FACE_DETECTOR_MODEL)} bytes")
        return True
    os.makedirs(_MODELS_DIR, exist_ok=True)
    logger.info(f"Downloading face detector model from {_FACE_DETECTOR_URL}...")
    try:
        urllib.request.urlretrieve(_FACE_DETECTOR_URL, _FACE_DETECTOR_MODEL)
        size = os.path.getsize(_FACE_DETECTOR_MODEL)
        logger.info(f"Downloaded model: {size} bytes")
        return size >= min_size
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        if os.path.exists(_FACE_DETECTOR_MODEL):
            os.remove(_FACE_DETECTOR_MODEL)
        return False


class FaceDetector:
    """
    Detects faces using MediaPipe Tasks API.
    Downloads model on first use.
    """

    def __init__(self, min_detection_confidence: float = 0.25):
        self.min_confidence = min_detection_confidence
        self._detector = None
        self._init_detector()

    def _init_detector(self):
        if not _MP_AVAILABLE:
            logger.error("MediaPipe not available.")
            return
        if not _ensure_model():
            logger.error("Model download failed — face detection disabled.")
            return
        try:
            opts = mp_vision.FaceDetectorOptions(
                base_options=mp_base_options.BaseOptions(model_asset_path=_FACE_DETECTOR_MODEL),
                min_detection_confidence=self.min_confidence,
            )
            self._detector = mp_vision.FaceDetector.create_from_options(opts)
            logger.info(f"FaceDetector initialized. Model: {_FACE_DETECTOR_MODEL}")
        except Exception as e:
            logger.error(f"FaceDetector init failed: {e}", exc_info=True)
            self._detector = None

    def detect(self, frame_bgr: np.ndarray) -> list:
        """
        Detect faces in a BGR frame.
        Returns list of dicts with bbox, confidence, mesh_landmarks.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        # Retry init if detector not ready
        if self._detector is None and _MP_AVAILABLE:
            logger.info("Detector not initialized — retrying init...")
            self._init_detector()

        if self._detector is None:
            logger.warning("Detector still not initialized — returning empty.")
            return []

        h, w = frame_bgr.shape[:2]
        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frame_rgb = np.ascontiguousarray(frame_rgb)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            detection_result = self._detector.detect(mp_image)
        except Exception as e:
            logger.error(f"Detection error: {e}", exc_info=True)
            return []

        results = []
        for det in (detection_result.detections or []):
            bb = det.bounding_box
            x = max(0, bb.origin_x)
            y = max(0, bb.origin_y)
            bw = min(bb.width, w - x)
            bh = min(bb.height, h - y)
            if bw <= 0 or bh <= 0:
                continue
            confidence = det.categories[0].score if det.categories else 0.5
            results.append({
                'bbox': (x, y, bw, bh),
                'confidence': float(confidence),
                'landmarks': None,
                'mesh_landmarks': None,
            })

        logger.info(f"Detected {len(results)} face(s) in {h}x{w} frame.")
        return results

    def release(self):
        pass
