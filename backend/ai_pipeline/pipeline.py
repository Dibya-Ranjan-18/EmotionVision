"""
AI Pipeline – Orchestrator
Ties together the detector, preprocessor, emotion analyser,
and behavior analyser into a single process_frame() call.
"""

import time
import logging
import numpy as np

from .detector import FaceDetector
from .preprocessor import ImagePreprocessor
from .emotion_analyzer import get_analyser, release_analyser, get_emotion_meta, EMOTION_META
from .behavior_analyzer import BehaviorAnalyser

logger = logging.getLogger(__name__)


class EmotionPipeline:
    """
    Full AI pipeline for real-time emotion and behaviour analysis.
    One instance is created per session and reused across frames.
    """

    def __init__(self, session_id: int):
        self.session_id = session_id
        self._detector = FaceDetector(min_detection_confidence=0.25)
        self._preprocessor = ImagePreprocessor(padding_ratio=0.2)
        self._emotion_analyser = get_analyser(session_id)
        self._behavior_analyser = BehaviorAnalyser()
        self._frame_count = 0
        self._fps_times: list = []
        logger.info(f"EmotionPipeline initialised for session {session_id}.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_frame(self, frame_bgr: np.ndarray) -> dict:
        """
        Run the full pipeline on a single BGR frame.

        Returns:
            {
              'faces': list[FaceResult],
              'face_count': int,
              'fps': float,
              'processing_time_ms': float,
              'frame_number': int,
              'primary': FaceResult | None,    # highest confidence face
            }

        Where FaceResult = {
          'face_index': int,
          'bbox': (x, y, w, h),
          'detection_confidence': float,
          'emotion': str,
          'raw_emotion': str,
          'confidence': float,
          'all_scores': dict,
          'is_uncertain': bool,
          'emoji': str,
          'color': str,
          'behavior': dict,
          'quality_ok': bool,
          'quality_score': float,
          'quality_issues': list,
        }
        """
        t_start = time.perf_counter()
        self._frame_count += 1

        # Track FPS
        now = time.time()
        self._fps_times.append(now)
        self._fps_times = [t for t in self._fps_times if now - t < 2.0]
        fps = len(self._fps_times) / 2.0

        # --- Detect faces ---
        detected_faces = self._detector.detect(frame_bgr)
        face_count = len(detected_faces)

        face_results = []

        for idx, face in enumerate(detected_faces):
            bbox = face['bbox']

            # --- Preprocess ---
            pre = self._preprocessor.preprocess(frame_bgr, bbox)

            # --- Emotion analysis ---
            emotion_result = {'smoothed_emotion': 'uncertain', 'smoothed_confidence': 0.0,
                              'raw_emotion': 'uncertain', 'raw_confidence': 0.0,
                              'all_scores': {}, 'is_uncertain': True,
                              'emoji': '❓', 'color': '#7F8C8D'}

            if pre['face_rgb'] is not None and pre['quality_ok']:
                emotion_result = self._emotion_analyser.analyse(pre['face_rgb'], face_index=idx)
            elif pre['face_rgb'] is not None:
                # Still run but mark low quality
                emotion_result = self._emotion_analyser.analyse(pre['face_rgb'], face_index=idx)
                emotion_result['is_uncertain'] = True

            # --- Behavior analysis ---
            behavior = self._behavior_analyser.analyse(
                mesh_landmarks=face.get('mesh_landmarks'),
                frame_shape=frame_bgr.shape,
                face_index=idx,
                face_count=face_count,
            )

            face_results.append({
                'face_index': idx,
                'bbox': bbox,
                'detection_confidence': round(float(face.get('confidence', 0.0)), 3),
                'emotion': emotion_result['smoothed_emotion'],
                'raw_emotion': emotion_result['raw_emotion'],
                'confidence': emotion_result['smoothed_confidence'],
                'all_scores': emotion_result['all_scores'],
                'is_uncertain': emotion_result['is_uncertain'],
                'emoji': emotion_result['emoji'],
                'color': emotion_result['color'],
                'behavior': behavior,
                'quality_ok': pre['quality_ok'],
                'quality_score': pre['quality_score'],
                'quality_issues': pre['issues'],
            })

        # Primary face = highest detection confidence
        primary = None
        if face_results:
            primary = max(face_results, key=lambda f: f['detection_confidence'])

        t_end = time.perf_counter()
        processing_ms = round((t_end - t_start) * 1000, 2)

        return {
            'faces': face_results,
            'face_count': face_count,
            'fps': round(fps, 1),
            'processing_time_ms': processing_ms,
            'frame_number': self._frame_count,
            'primary': primary,
        }

    def release(self):
        """Release resources when session ends."""
        self._detector.release()
        release_analyser(self.session_id)
        self._behavior_analyser.reset()
        logger.info(f"EmotionPipeline released for session {self.session_id}.")


# ---------------------------------------------------------------------------
# Session-scoped pipeline registry
# ---------------------------------------------------------------------------
_pipelines: dict[int, EmotionPipeline] = {}


def get_pipeline(session_id: int) -> EmotionPipeline:
    """Get or create pipeline for a session."""
    if session_id not in _pipelines:
        _pipelines[session_id] = EmotionPipeline(session_id)
    return _pipelines[session_id]


def release_pipeline(session_id: int):
    """Release and destroy pipeline for a completed session."""
    pipeline = _pipelines.pop(session_id, None)
    if pipeline:
        pipeline.release()
