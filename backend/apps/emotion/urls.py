"""
Emotion App – URL Configuration
"""
from django.urls import path
from .views import ProcessFrameView, LiveDataView

urlpatterns = [
    path('process-frame/', ProcessFrameView.as_view(), name='process-frame'),
    path('live-data/', LiveDataView.as_view(), name='live-data'),
]
