"""
Analytics App – Models
Stores aggregated per-session statistics.
"""

from django.db import models
from ..sessions_app.models import Session


class SessionAnalytics(models.Model):
    """
    Computed once when a session ends; holds aggregated metrics.
    """

    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='analytics')
    dominant_emotion = models.CharField(max_length=50, blank=True)
    avg_confidence = models.FloatField(default=0.0)
    total_frames = models.IntegerField(default=0)
    avg_fps = models.FloatField(default=0.0)
    total_emotion_changes = models.IntegerField(default=0)
    face_count_max = models.IntegerField(default=0)
    detection_accuracy_estimate = models.FloatField(default=0.0)

    # Emotion distribution JSON: {"happy": 45, "sad": 10, ...}
    emotion_distribution = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics'

    def __str__(self):
        return f"Analytics for session {self.session_id}"


class Report(models.Model):
    """
    Tracks generated PDF reports linked to a session.
    """

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='reports')
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report [{self.file_name}] for session {self.session_id}"
