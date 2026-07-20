"""
Analytics App – URL Configuration
"""
from django.urls import path
from .views import SessionSummaryView
from .debug_view import DebugView

urlpatterns = [
    path('session-summary/', SessionSummaryView.as_view(), name='session-summary'),
    path('debug/', DebugView.as_view(), name='debug'),
]
