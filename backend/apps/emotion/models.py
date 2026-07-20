"""
Emotion App – Models
Defines tables for emotion logs and face detection logs.
"""

from django.db import models


class EmotionLog(models.Model):
    """
    Stores every detected emotion event during a session.
    One row per processed frame that yields a valid emotion.
    """

    EMOTION_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('neutral', 'Neutral'),
        ('fear', 'Fear'),
        ('surprise', 'Surprise'),
        ('disgust', 'Disgust'),
        ('uncertain', 'Uncertain'),
    ]

    session = models.ForeignKey('sessions_app.Session', on_delete=models.CASCADE, related_name='emotion_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES)
    confidence = models.FloatField()
    face_count = models.IntegerField(default=1)
    processing_time_ms = models.FloatField(default=0.0)
    frame_number = models.IntegerField(default=0)
    face_index = models.IntegerField(default=0)

    class Meta:
        db_table = 'emotion_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.emotion} ({self.confidence:.1f}%)"


class FaceLog(models.Model):
    """
    Stores bounding box data for each detected face per frame.
    Supports multi-face tracking.
    """

    session = models.ForeignKey('sessions_app.Session', on_delete=models.CASCADE, related_name='face_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    face_index = models.IntegerField(default=0)   # 0-based face index in frame
    bbox_x = models.IntegerField(default=0)
    bbox_y = models.IntegerField(default=0)
    bbox_w = models.IntegerField(default=0)
    bbox_h = models.IntegerField(default=0)
    emotion = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(default=0.0)

    class Meta:
        db_table = 'face_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Face {self.face_index} @ session {self.session_id}"
