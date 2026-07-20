from django.apps import AppConfig


class EmotionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emotion'
    label = 'emotion'
    verbose_name = 'Emotion Detection'
