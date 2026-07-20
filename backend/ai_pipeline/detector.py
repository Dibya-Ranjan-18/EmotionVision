"""
AI Pipeline – Face Detector
Uses MediaPipe Solutions API (built-in, no model download required)
for reliable face detection on all platforms including Render free tier.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MediaPipe Solutions API (built-in, no separate model download needed)
# ---------------------------------------------------------------------------
_MP_AVAILABLE = False
_mp_face_detection = None
_mp_face_mesh = None

try:
    import mediapipe as mp
    _mp_face_detection = mp.solutions.face_detection
    _mp_face_mesh = mp.solutions.face_mesh
    _MP_AVAILABLE = True
    logger.info(f"MediaPipe {mp.__version__} Solutions API available.")
except Exception as e:
    logger.error(f"MediaPipe not available: {e}")


class FaceDetector:
    """
    Detects faces using MediaPipe Solutions API (v0.10+).
    No model file downloads required — models are bundled with mediapipe.
    """

    def __init__(self, min_detection_confidence: float = 0.25):
        self.min_confidence = min_detection_confidence
        self._face_detection = None
        self._face_mesh = None
        self._init_detector()

    def _init_detector(self):
        if not _MP_AVAILABLE:
            logger.error("MediaPipe not available — face detection disabled.")
            return
        try:
            self._face_detection = _mp_face_detection.FaceDetection(
                model_selection=1,  # 1 = full range (better for webcam)
                min_detection_confidence=self.min_confidence,
            )
            logger.info("MediaPipe FaceDetection Solutions API initialised.")
        except Exception as e:
            logger.error(f"FaceDetection init failed: {e}")

        try:
            self._face_mesh = _mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                refine_landmarks=False,
                min_detection_confidence=self.min_confidence,
                min_tracking_confidence=0.25,
            )
            logger.info("MediaPipe FaceMesh Solutions API initialised.")
        except Exception as e:
            logger.warning(f"FaceMesh init failed (non-critical): {e}")

    # ------------------------------------------------------------------

    def detect(self, frame_bgr: np.ndarray) -> list:
        """
        Detect faces in a BGR frame.
        Returns list of { bbox, confidence, landmarks, mesh_landmarks }.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []

        # Lazy retry if detector failed to init
        if self._face_detection is None and _MP_AVAILABLE:
            logger.info("Retrying MediaPipe detector initialization...")
            self._init_detector()

        if self._face_detection is None:
            logger.warning("FaceDetection not initialized — skipping frame.")
            return []

        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        try:
            detection_result = self._face_detection.process(frame_rgb)
        except Exception as e:
            logger.error(f"MediaPipe detection error: {e}")
            return []

        frame_rgb.flags.writeable = True

        if not detection_result.detections:
            return []

        results = []
        for det in detection_result.detections:
            bb = det.location_data.relative_bounding_box
            x = max(0, int(bb.xmin * w))
            y = max(0, int(bb.ymin * h))
            bw = min(int(bb.width * w), w - x)
            bh = min(int(bb.height * h), h - y)

            if bw <= 0 or bh <= 0:
                continue

            confidence = det.score[0] if det.score else 0.5

            # Get face mesh landmarks if available
            mesh_landmarks = self._get_mesh_landmarks(frame_rgb)

            results.append({
                'bbox': (x, y, bw, bh),
                'confidence': float(confidence),
                'landmarks': None,
                'mesh_landmarks': mesh_landmarks,
            })

        logger.info(f"Detected {len(results)} face(s)")
        return results

    def _get_mesh_landmarks(self, frame_rgb: np.ndarray):
        """Get face mesh landmarks."""
        if not self._face_mesh:
            return None
        try:
            result = self._face_mesh.process(frame_rgb)
            if result.multi_face_landmarks:
                return result.multi_face_landmarks[0]
        except Exception as e:
            logger.debug(f"FaceMesh error: {e}")
        return None

    def release(self):
        """Release MediaPipe resources."""
        try:
            if self._face_detection:
                self._face_detection.close()
            if self._face_mesh:
                self._face_mesh.close()
        except Exception:
            pass
