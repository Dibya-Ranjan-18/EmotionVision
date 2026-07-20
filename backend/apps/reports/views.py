"""
Reports App – Views
GET /api/export-pdf/?session_id=<id>  → Generate and serve PDF report
"""

import os
import logging
from django.conf import settings
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from ..sessions_app.models import Session
from ..analytics.models import Report
from ..analytics.views import SessionSummaryView
from .pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ExportPDFView(APIView):
    """GET /api/export-pdf/ — Generate and return a PDF report for a session."""

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        # Gather session summary data
        summary_view = SessionSummaryView()
        summary_view.request = request
        summary_response = summary_view.get(request)
        if summary_response.status_code != 200:
            return Response({'error': 'Failed to get session summary'}, status=500)

        session_data = summary_response.data

        # Build output path
        reports_dir = settings.REPORTS_DIR
        file_name = f"emotionvision_report_session_{session_id}_{session.start_time.strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = str(reports_dir / file_name)

        # Generate PDF
        try:
            generator = PDFReportGenerator(output_path)
            generator.generate(session_data)
        except Exception as exc:
            logger.error(f"PDF generation failed: {exc}", exc_info=True)
            return Response({'error': f'PDF generation failed: {str(exc)}'}, status=500)

        # Save report record
        Report.objects.create(
            session=session,
            file_path=output_path,
            file_name=file_name,
        )

        # Serve file as download
        response = FileResponse(
            open(output_path, 'rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response
