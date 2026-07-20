"""
AI Pipeline – Image Preprocessor
Handles face alignment, quality check, and brightness/contrast normalisation
before passing the face region to emotion analysis.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Target size for emotion model input
FACE_TARGET_SIZE = (224, 224)


class ImagePreprocessor:
    """
    Preprocesses a detected face region for emotion analysis.

    Steps:
      1. Crop face from frame using bounding box (with padding)
      2. Quality check (blur detection, min size)
      3. Brightness & contrast normalisation (CLAHE)
      4. Resize to model input size
    """

    def __init__(self, padding_ratio: float = 0.2):
        """
        Args:
            padding_ratio: How much to pad bounding box on each side (0.2 = 20%).
        """
        self.padding_ratio = padding_ratio
        # CLAHE for adaptive histogram equalisation
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess(self, frame_bgr: np.ndarray, bbox: tuple) -> dict:
        """
        Preprocess a face region for emotion analysis.

        Args:
            frame_bgr: Full BGR frame from webcam.
            bbox: (x, y, w, h) bounding box of the face.

        Returns:
            {
              'face_rgb': np.ndarray | None,   # preprocessed RGB face for model
              'quality_ok': bool,
              'quality_score': float,          # 0.0 – 1.0
              'issues': list[str],             # detected quality issues
            }
        """
        issues = []
        x, y, w, h = bbox
        fh, fw = frame_bgr.shape[:2]

        # --- 1. Pad bounding box ---
        pad_x = int(w * self.padding_ratio)
        pad_y = int(h * self.padding_ratio)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(fw, x + w + pad_x)
        y2 = min(fh, y + h + pad_y)
        face_crop = frame_bgr[y1:y2, x1:x2]

        if face_crop.size == 0:
            return {'face_rgb': None, 'quality_ok': False, 'quality_score': 0.0, 'issues': ['empty crop']}

        # --- 2. Minimum size check ---
        cw, ch = face_crop.shape[1], face_crop.shape[0]
        if cw < 32 or ch < 32:
            issues.append('face too small')

        # --- 3. Blur detection (Laplacian variance) ---
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        quality_score = min(1.0, blur_score / 200.0)  # normalise
        if blur_score < 30:
            issues.append('blurry face')

        # --- 3.1 Brightness check (Under-lit / Over-lit) ---
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 60.0:
            issues.append('poor lighting (too dark)')
        elif mean_brightness > 220.0:
            issues.append('poor lighting (too bright)')

        # --- 4. Brightness / contrast normalisation ---
        normalised = self._normalise_brightness(face_crop)

        # --- 5. Resize to target ---
        face_resized = cv2.resize(normalised, FACE_TARGET_SIZE, interpolation=cv2.INTER_AREA)

        # Convert BGR → RGB for model
        face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)

        quality_ok = len(issues) == 0 and quality_score > 0.1

        return {
            'face_rgb': face_rgb,
            'quality_ok': quality_ok,
            'quality_score': round(quality_score, 3),
            'issues': issues,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalise_brightness(self, face_bgr: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE to L-channel in LAB colourspace for perceptual normalisation.
        This handles under-lit / over-lit conditions robustly.
        """
        try:
            lab = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2LAB)
            l_ch, a_ch, b_ch = cv2.split(lab)
            l_eq = self._clahe.apply(l_ch)
            merged = cv2.merge([l_eq, a_ch, b_ch])
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        except cv2.error:
            return face_bgr

    @staticmethod
    def decode_base64_frame(b64_string: str) -> np.ndarray | None:
        """
        Decode a base64-encoded JPEG string sent by the browser into a BGR ndarray.
        Strips the data URI prefix if present.
        """
        import base64
        try:
            if ',' in b64_string:
                b64_string = b64_string.split(',', 1)[1]
            img_bytes = base64.b64decode(b64_string)
            arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return frame
        except Exception as exc:
            logger.error(f"Failed to decode base64 frame: {exc}")
            return None
