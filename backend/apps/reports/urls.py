from django.urls import path
from .views import ExportPDFView

urlpatterns = [
    path('export-pdf/', ExportPDFView.as_view(), name='export-pdf'),
]
