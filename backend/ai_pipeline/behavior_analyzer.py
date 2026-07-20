"""
AI Pipeline – Behavior Analyser
Extracts real-time behavioral signals from MediaPipe FaceMesh landmarks:
  - Smile detection (mouth aspect ratio)
  - Eye open/closed (eye aspect ratio)
  - Blink detection (EAR threshold crossing)
  - Head direction (yaw/pitch from 3D face model)
  - Face count & face presence
"""

import cv2
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MediaPipe FaceMesh landmark indices
# ---------------------------------------------------------------------------
# Left eye landmarks (EAR calculation)
LEFT_EYE_TOP    = [159, 160, 161]
LEFT_EYE_BOTTOM = [145, 144, 163]
LEFT_EYE_LEFT   = 33
LEFT_EYE_RIGHT  = 133

# Right eye landmarks
RIGHT_EYE_TOP    = [386, 385, 384]
RIGHT_EYE_BOTTOM = [374, 373, 380]
RIGHT_EYE_LEFT   = 362
RIGHT_EYE_RIGHT  = 263

# Mouth landmarks for smile / mouth aspect ratio
MOUTH_LEFT   = 61
MOUTH_RIGHT  = 291
MOUTH_TOP    = 13
MOUTH_BOTTOM = 14
MOUTH_TOP2   = 312
MOUTH_BOTTOM2 = 317

# Head pose estimation landmarks (3D model points)
NOSE_TIP     = 1
CHIN         = 152
LEFT_EYE_C   = 226
RIGHT_EYE_C  = 446
LEFT_MOUTH   = 57
RIGHT_MOUTH  = 287

# EAR blink threshold
EAR_BLINK_THRESHOLD = 0.21
# MAR smile threshold (mouth aspect ratio)
MAR_SMILE_THRESHOLD = 0.35


class BehaviorAnalyser:
    """
    Analyses per-face behavioral signals from MediaPipe FaceMesh landmarks.
    """

    def __init__(self):
        # Per-face blink state: face_index → {'prev_ear': float, 'blink_count': int}
        self._blink_state: dict[int, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(
        self,
        mesh_landmarks: Optional[list],  # list of (x, y, z) tuples from FaceMesh
        frame_shape: tuple,
        face_index: int = 0,
        face_count: int = 1,
    ) -> dict:
        """
        Compute behavioral signals for one face.

        Returns:
            {
              'smile_detected': bool,
              'smile_score': float,
              'left_eye_open': bool,
              'right_eye_open': bool,
              'blink_detected': bool,
              'blink_count': int,
              'head_direction': str,
              'yaw_angle': float,
              'pitch_angle': float,
              'face_present': bool,
              'face_count': int,
            }
        """
        if not mesh_landmarks:
            return self._empty_result(face_count, face_present=False)

        h, w = frame_shape[:2]
        pts = np.array([(x, y) for x, y, z in mesh_landmarks], dtype=np.float32)
        pts3d = np.array(mesh_landmarks, dtype=np.float64)

        # --- Eye state ---
        left_ear = self._eye_aspect_ratio(pts, LEFT_EYE_TOP, LEFT_EYE_BOTTOM,
                                           LEFT_EYE_LEFT, LEFT_EYE_RIGHT)
        right_ear = self._eye_aspect_ratio(pts, RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM,
                                            RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT)
        left_open = left_ear > EAR_BLINK_THRESHOLD
        right_open = right_ear > EAR_BLINK_THRESHOLD
        current_ear = (left_ear + right_ear) / 2.0

        # --- Blink detection ---
        state = self._blink_state.setdefault(face_index, {'prev_ear': 1.0, 'blink_count': 0})
        blink_detected = False
        if state['prev_ear'] > EAR_BLINK_THRESHOLD and current_ear <= EAR_BLINK_THRESHOLD:
            blink_detected = True
            state['blink_count'] += 1
        state['prev_ear'] = current_ear

        # --- Smile detection ---
        smile_score, smile_detected = self._smile_detection(pts)

        # --- Head direction ---
        head_dir, yaw, pitch = self._head_direction(pts3d, (h, w))

        return {
            'smile_detected': smile_detected,
            'smile_score': round(smile_score, 3),
            'left_eye_open': bool(left_open),
            'right_eye_open': bool(right_open),
            'blink_detected': blink_detected,
            'blink_count': state['blink_count'],
            'head_direction': head_dir,
            'yaw_angle': round(float(yaw), 2),
            'pitch_angle': round(float(pitch), 2),
            'face_present': True,
            'face_count': face_count,
        }

    def reset(self, face_index: int = None):
        if face_index is None:
            self._blink_state.clear()
        else:
            self._blink_state.pop(face_index, None)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _eye_aspect_ratio(
        self,
        pts: np.ndarray,
        top_indices: list,
        bottom_indices: list,
        left_idx: int,
        right_idx: int,
    ) -> float:
        """Compute Eye Aspect Ratio (EAR) using 6 landmark points."""
        try:
            top_pts = pts[top_indices]
            bot_pts = pts[bottom_indices]
            vert1 = np.linalg.norm(top_pts[0] - bot_pts[0])
            vert2 = np.linalg.norm(top_pts[1] - bot_pts[1])
            vert3 = np.linalg.norm(top_pts[2] - bot_pts[2])
            horiz = np.linalg.norm(pts[left_idx] - pts[right_idx])
            ear = (vert1 + vert2 + vert3) / (3.0 * horiz + 1e-6)
            return float(ear)
        except (IndexError, ZeroDivisionError):
            return 0.3  # default open

    def _smile_detection(self, pts: np.ndarray) -> tuple[float, bool]:
        """
        Compute Mouth Aspect Ratio (MAR) as a smile proxy.
        High MAR = open/wide mouth = smile.
        """
        try:
            mouth_width = np.linalg.norm(pts[MOUTH_LEFT] - pts[MOUTH_RIGHT])
            mouth_height = np.linalg.norm(pts[MOUTH_TOP] - pts[MOUTH_BOTTOM])
            mar = mouth_height / (mouth_width + 1e-6)
            # Also check corner lift (smile raises corners)
            left_corner_y = pts[MOUTH_LEFT][1]
            right_corner_y = pts[MOUTH_RIGHT][1]
            top_y = pts[MOUTH_TOP][1]
            corner_lift = top_y - (left_corner_y + right_corner_y) / 2.0
            smile_score = float(max(0.0, min(1.0, mar * 2 + corner_lift / 50.0)))
            return smile_score, smile_score > MAR_SMILE_THRESHOLD
        except (IndexError, ZeroDivisionError):
            return 0.0, False

    def _head_direction(
        self,
        pts3d: np.ndarray,
        frame_shape: tuple,
    ) -> tuple[str, float, float]:
        """
        Estimate head direction using solvePnP with 6 facial landmarks.
        Returns (direction_str, yaw_degrees, pitch_degrees).
        """
        h, w = frame_shape
        # 3D model points (generic face model, units mm)
        model_points = np.array([
            (0.0, 0.0, 0.0),         # Nose tip
            (0.0, -330.0, -65.0),    # Chin
            (-225.0, 170.0, -135.0), # Left eye corner
            (225.0, 170.0, -135.0),  # Right eye corner
            (-150.0, -150.0, -125.0),# Left mouth corner
            (150.0, -150.0, -125.0), # Right mouth corner
        ], dtype=np.float64)

        try:
            image_points = np.array([
                (pts3d[NOSE_TIP][0], pts3d[NOSE_TIP][1]),
                (pts3d[CHIN][0], pts3d[CHIN][1]),
                (pts3d[LEFT_EYE_C][0], pts3d[LEFT_EYE_C][1]),
                (pts3d[RIGHT_EYE_C][0], pts3d[RIGHT_EYE_C][1]),
                (pts3d[LEFT_MOUTH][0], pts3d[LEFT_MOUTH][1]),
                (pts3d[RIGHT_MOUTH][0], pts3d[RIGHT_MOUTH][1]),
            ], dtype=np.float64)

            focal_length = w
            center = (w / 2, h / 2)
            cam_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1],
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1))

            success, rot_vec, trans_vec = cv2.solvePnP(
                model_points, image_points, cam_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if not success:
                return 'unknown', 0.0, 0.0

            rot_mat, _ = cv2.Rodrigues(rot_vec)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)
            yaw   = angles[1] * 360   # horizontal
            pitch = angles[0] * 360   # vertical

            if yaw < -15:
                direction = 'left'
            elif yaw > 15:
                direction = 'right'
            elif pitch < -10:
                direction = 'down'
            elif pitch > 10:
                direction = 'up'
            else:
                direction = 'center'

            return direction, float(yaw), float(pitch)

        except Exception as exc:
            logger.debug(f"Head direction estimation failed: {exc}")
            return 'center', 0.0, 0.0

    @staticmethod
    def _empty_result(face_count: int, face_present: bool = False) -> dict:
        return {
            'smile_detected': False,
            'smile_score': 0.0,
            'left_eye_open': True,
            'right_eye_open': True,
            'blink_detected': False,
            'blink_count': 0,
            'head_direction': 'unknown',
            'yaw_angle': 0.0,
            'pitch_angle': 0.0,
            'face_present': face_present,
            'face_count': face_count,
        }
