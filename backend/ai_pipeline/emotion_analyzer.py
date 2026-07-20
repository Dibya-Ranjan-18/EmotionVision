"""
AI Pipeline – Emotion Analyser
Uses FER (Facial Emotion Recognition) library with OpenCV backend.
Implements temporal smoothing over a rolling window of predictions.
Falls back to OpenCV DNN-based Haar + rule-based estimation when FER
is unavailable.
"""

import cv2
import numpy as np
import logging
from collections import deque, Counter

logger = logging.getLogger(__name__)

# Confidence threshold below which we return "uncertain"
CONFIDENCE_THRESHOLD = 35.0

# Smoothing window — last N predictions per face
SMOOTHING_WINDOW = 5

# Emotion display metadata
EMOTION_META = {
    'happy':    {'emoji': '😊', 'color': '#FFD700', 'label': 'Happy'},
    'sad':      {'emoji': '😢', 'color': '#4A90E2', 'label': 'Sad'},
    'angry':    {'emoji': '😠', 'color': '#E74C3C', 'label': 'Angry'},
    'neutral':  {'emoji': '😐', 'color': '#95A5A6', 'label': 'Neutral'},
    'fear':     {'emoji': '😨', 'color': '#8E44AD', 'label': 'Fear'},
    'surprise': {'emoji': '😲', 'color': '#E67E22', 'label': 'Surprise'},
    'disgust':  {'emoji': '🤢', 'color': '#27AE60', 'label': 'Disgust'},
    'uncertain':{'emoji': '❓', 'color': '#7F8C8D', 'label': 'Uncertain'},
}

# Try to import HSEmotionRecognizer
try:
    from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
    _HSE_AVAILABLE = True
    logger.info("HSEmotionONNX library available.")
except ImportError:
    _HSE_AVAILABLE = False
    logger.warning("HSEmotionONNX library not available. Using fallback emotion estimator.")

HSE_EMOTION_MAP = {
    'anger': 'angry',
    'contempt': 'disgust',
    'disgust': 'disgust',
    'fear': 'fear',
    'happiness': 'happy',
    'neutral': 'neutral',
    'sadness': 'sad',
    'surprise': 'surprise',
}


class EmotionAnalyser:
    """
    Analyses emotion from a preprocessed face image.
    Maintains per-session smoothing buffers.
    """

    def __init__(self, session_id: int = 0, mtcnn: bool = False):
        """
        Args:
            session_id: Used to scope the smoothing buffer.
            mtcnn: Whether to use MTCNN for FER face detection (slower but more accurate).
        """
        self.session_id = session_id
        # Smoothing deques: face_index → deque of (emotion, confidence)
        self._buffers: dict[int, deque] = {}
        self._detector = None
        self._init_model(mtcnn)

    def _init_model(self, mtcnn: bool):
        if _HSE_AVAILABLE:
            try:
                self._detector = HSEmotionRecognizer(model_name='enet_b0_8_best_vgaf')
                logger.info("HSEmotionRecognizer initialized successfully.")
            except Exception as exc:
                logger.error(f"Failed to init HSEmotionRecognizer: {exc}")
                self._detector = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(self, face_rgb: np.ndarray, face_index: int = 0) -> dict:
        """
        Analyse the emotion of a preprocessed RGB face image.

        Args:
            face_rgb: RGB face image (any size).
            face_index: Which face this belongs to (for smoothing buffer).

        Returns:
            {
              'raw_emotion': str,
              'raw_confidence': float,
              'smoothed_emotion': str,
              'smoothed_confidence': float,
              'all_scores': dict,    # {emotion: confidence%}
              'is_uncertain': bool,
              'emoji': str,
              'color': str,
            }
        """
        # Ensure buffer exists
        if face_index not in self._buffers:
            self._buffers[face_index] = deque(maxlen=SMOOTHING_WINDOW)

        raw_emotion, raw_confidence, all_scores = self._run_inference(face_rgb)

        # Push to smoothing buffer
        if raw_emotion and raw_confidence >= CONFIDENCE_THRESHOLD:
            self._buffers[face_index].append((raw_emotion, raw_confidence))
        elif raw_emotion:
            # Low confidence — push "uncertain" so it dampens transitions
            self._buffers[face_index].append(('uncertain', raw_confidence))

        smoothed_emotion, smoothed_confidence = self._smooth(face_index)
        is_uncertain = smoothed_confidence < CONFIDENCE_THRESHOLD

        meta = EMOTION_META.get(smoothed_emotion, EMOTION_META['uncertain'])

        return {
            'raw_emotion': raw_emotion or 'uncertain',
            'raw_confidence': round(raw_confidence, 2),
            'smoothed_emotion': smoothed_emotion,
            'smoothed_confidence': round(smoothed_confidence, 2),
            'all_scores': all_scores,
            'is_uncertain': is_uncertain,
            'emoji': meta['emoji'],
            'color': meta['color'],
        }

    def reset_buffer(self, face_index: int = None):
        """Reset smoothing buffer for a face or all faces."""
        if face_index is None:
            self._buffers.clear()
        elif face_index in self._buffers:
            self._buffers[face_index].clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_inference(self, face_rgb: np.ndarray) -> tuple[str, float, dict]:
        """Run emotion inference on a face crop."""
        if self._detector and _HSE_AVAILABLE:
            return self._hse_inference(face_rgb)
        else:
            face_bgr = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2BGR)
            return self._fallback_inference(face_bgr)

    def _hse_inference(self, face_rgb: np.ndarray) -> tuple[str, float, dict]:
        """Use HSEmotionRecognizer for ONNX-based inference."""
        try:
            emotion_str, scores = self._detector.predict_emotions(face_rgb, logits=False)
            
            # Map HSEmotion class names to standard keys and scale to 0-100%
            all_scores = {}
            for idx, score_val in enumerate(scores):
                class_name = self._detector.idx_to_class[idx].lower()
                mapped_emo = HSE_EMOTION_MAP.get(class_name, 'uncertain')
                score_pct = float(score_val * 100)
                all_scores[mapped_emo] = max(all_scores.get(mapped_emo, 0.0), round(score_pct, 2))

            top_emotion = HSE_EMOTION_MAP.get(emotion_str.lower(), 'uncertain')
            top_confidence = all_scores.get(top_emotion, 0.0)

            return top_emotion, top_confidence, all_scores

        except Exception as exc:
            logger.error(f"HSEmotion inference error: {exc}")
            return 'neutral', 40.0, {}


    def _fallback_inference(self, face_bgr: np.ndarray) -> tuple[str, float, dict]:
        """
        Lightweight fallback using OpenCV image features.
        Uses brightness and edge density as crude emotion proxies.
        Not production-accurate; exists so the app runs without FER.
        """
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.sum(edges > 0)) / edges.size

        # Very crude heuristic
        if edge_density > 0.15:
            emotion, confidence = 'surprise', 55.0
        elif mean_brightness > 160:
            emotion, confidence = 'happy', 60.0
        elif mean_brightness < 80:
            emotion, confidence = 'sad', 52.0
        else:
            emotion, confidence = 'neutral', 65.0

        all_scores = {e: 0.0 for e in EMOTION_META if e != 'uncertain'}
        all_scores[emotion] = confidence
        return emotion, confidence, all_scores

    def _smooth(self, face_index: int) -> tuple[str, float]:
        """
        Compute smoothed emotion from the rolling buffer.
        Returns the mode emotion and mean confidence of matching entries.
        """
        buf = self._buffers.get(face_index)
        if not buf:
            return 'uncertain', 0.0

        emotions = [e for e, _ in buf]
        confidences = [c for _, c in buf]

        # Mode of emotions
        counter = Counter(emotions)
        dominant = counter.most_common(1)[0][0]

        # Mean confidence of dominant emotion entries
        dominant_confs = [c for e, c in buf if e == dominant]
        mean_conf = float(np.mean(dominant_confs)) if dominant_confs else 0.0

        return dominant, round(mean_conf, 2)


# Singleton per session — managed by the pipeline
_analysers: dict[int, EmotionAnalyser] = {}


def get_analyser(session_id: int) -> EmotionAnalyser:
    """Get or create a session-scoped EmotionAnalyser."""
    if session_id not in _analysers:
        _analysers[session_id] = EmotionAnalyser(session_id=session_id)
    return _analysers[session_id]


def release_analyser(session_id: int):
    """Release analyser for a completed session."""
    _analysers.pop(session_id, None)


def get_emotion_meta(emotion: str) -> dict:
    return EMOTION_META.get(emotion.lower(), EMOTION_META['uncertain'])
