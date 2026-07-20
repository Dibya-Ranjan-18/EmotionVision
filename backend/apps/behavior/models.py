"""
Behavior App – Models
Stores human behavioral signals per frame: blink, smile, gaze, eye state.
"""

from django.db import models


class BehaviorLog(models.Model):
    """
    One row per processed frame capturing all behavioral signals
    detected by MediaPipe FaceMesh.
    """

    HEAD_DIRECTION_CHOICES = [
        ('center', 'Center'),
        ('left', 'Left'),
        ('right', 'Right'),
        ('up', 'Up'),
        ('down', 'Down'),
        ('unknown', 'Unknown'),
    ]

    session = models.ForeignKey('sessions_app.Session', on_delete=models.CASCADE, related_name='behavior_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    face_index = models.IntegerField(default=0)

    # Smile
    smile_detected = models.BooleanField(default=False)
    smile_score = models.FloatField(default=0.0)

    # Eye state
    left_eye_open = models.BooleanField(default=True)
    right_eye_open = models.BooleanField(default=True)
    blink_detected = models.BooleanField(default=False)
    blink_count = models.IntegerField(default=0)

    # Head direction
    head_direction = models.CharField(
        max_length=20,
        choices=HEAD_DIRECTION_CHOICES,
        default='center'
    )
    yaw_angle = models.FloatField(default=0.0)    # left/right rotation
    pitch_angle = models.FloatField(default=0.0)  # up/down rotation

    # Face presence
    face_present = models.BooleanField(default=True)
    face_count = models.IntegerField(default=1)

    class Meta:
        db_table = 'behavior_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return (
            f"Behavior [session={self.session_id}] "
            f"smile={self.smile_detected} blink={self.blink_detected} "
            f"head={self.head_direction}"
        )
