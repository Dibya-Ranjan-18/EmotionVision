"""
Analytics App – URL Configuration
"""
from django.urls import path
from .views import SessionSummaryView

urlpatterns = [
    path('session-summary/', SessionSummaryView.as_view(), name='session-summary'),
]
