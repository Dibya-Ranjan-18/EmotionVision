import threading
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class EmotionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emotion'
    label = 'emotion'
    verbose_name = 'Emotion Detection'

    def ready(self):
        """Pre-download MediaPipe models on server startup (background thread)."""
        def _preload():
            try:
                logger.info("Pre-warming AI pipeline: downloading MediaPipe models...")
                from ai_pipeline.detector import _ensure_model, _FACE_DETECTOR_MODEL, _FACE_LANDMARKER_MODEL, _MODEL_URLS
                _ensure_model(_FACE_DETECTOR_MODEL, _MODEL_URLS[_FACE_DETECTOR_MODEL])
                _ensure_model(_FACE_LANDMARKER_MODEL, _MODEL_URLS[_FACE_LANDMARKER_MODEL])
                logger.info("MediaPipe models pre-downloaded successfully.")
            except Exception as e:
                logger.warning(f"Model pre-download failed (will retry on first request): {e}")

        # Run in background thread so server starts immediately
        t = threading.Thread(target=_preload, daemon=True)
        t.start()
