"""
Sessions App – Models
Defines the Session table: tracks each analysis session's lifecycle.
"""

from django.db import models


class Session(models.Model):
    """
    Represents one complete analysis session.
    A session begins when the user clicks 'Start' and ends on 'Stop'.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_frames = models.IntegerField(default=0)
    avg_fps = models.FloatField(default=0.0)
    dominant_emotion = models.CharField(max_length=50, blank=True)
    avg_confidence = models.FloatField(default=0.0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'sessions'
        ordering = ['-start_time']

    def __str__(self):
        return f"Session {self.id} [{self.status}] started {self.start_time}"

    @property
    def duration_seconds(self):
        """Return session duration in seconds, or None if still active."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
