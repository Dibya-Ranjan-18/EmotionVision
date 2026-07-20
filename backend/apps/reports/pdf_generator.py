"""
Reports App – PDF Generation Service
Generates a professional PDF report using ReportLab with embedded charts.
"""

import io
import os
import logging
from datetime import datetime
from collections import Counter

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, PageBreak,
)
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# Colour palette matching the UI
PALETTE = {
    'happy':    '#FFD700',
    'sad':      '#4A90E2',
    'angry':    '#E74C3C',
    'neutral':  '#95A5A6',
    'fear':     '#8E44AD',
    'surprise': '#E67E22',
    'disgust':  '#27AE60',
    'uncertain':'#7F8C8D',
}

EMOTION_EMOJIS = {
    'happy': '😊', 'sad': '😢', 'angry': '😠', 'neutral': '😐',
    'fear': '😨', 'surprise': '😲', 'disgust': '🤢', 'uncertain': '❓',
}


class PDFReportGenerator:
    """Generates a professional PDF analytics report for a session."""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=26,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=6,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            spaceAfter=20,
        ))
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a1a2e'),
            spaceBefore=16,
            spaceAfter=8,
        ))
        self.styles.add(ParagraphStyle(
            'MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6c757d'),
        ))
        self.styles.add(ParagraphStyle(
            'MetricValue',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#1a1a2e'),
            fontName='Helvetica-Bold',
        ))

    def generate(self, session_data: dict) -> str:
        """
        Generate the PDF report.

        Args:
            session_data: Dict returned by SessionSummaryView.

        Returns:
            Absolute path to the generated PDF file.
        """
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []
        story += self._build_header(session_data)
        story += self._build_session_info(session_data)
        story += self._build_statistics(session_data)
        story += self._build_pie_chart(session_data)
        story += self._build_timeline_table(session_data)
        story += self._build_behavior_summary(session_data)
        story += self._build_ai_insights(session_data)
        story += self._build_footer()

        doc.build(story)
        logger.info(f"PDF report generated: {self.output_path}")
        return self.output_path

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_header(self, data):
        elements = []
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("EmotionVision AI", self.styles['CustomTitle']))
        elements.append(Paragraph(
            "Real-Time Emotion & Behavior Analysis Report",
            self.styles['CustomSubtitle']
        ))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6c63ff')))
        elements.append(Spacer(1, 0.5 * cm))
        return elements

    def _build_session_info(self, data):
        elements = [Paragraph("Session Information", self.styles['SectionHeader'])]
        analytics = data.get('analytics', {})
        dominant = analytics.get('dominant_emotion', 'N/A').capitalize()
        emoji = EMOTION_EMOJIS.get(analytics.get('dominant_emotion', '').lower(), '')

        dur = data.get('duration_seconds') or 0
        minutes, seconds = divmod(int(dur), 60)

        rows = [
            ['Session ID', str(data.get('session_id', 'N/A'))],
            ['Date', datetime.now().strftime('%B %d, %Y')],
            ['Start Time', data.get('start_time', 'N/A')[:19].replace('T', ' ')],
            ['End Time', (data.get('end_time') or 'N/A')[:19].replace('T', ' ')],
            ['Duration', f"{minutes}m {seconds}s"],
            ['Dominant Emotion', f"{emoji} {dominant}"],
            ['Status', data.get('status', 'N/A').capitalize()],
        ]

        table = Table(rows, colWidths=[5 * cm, 11 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (1, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        return elements

    def _build_statistics(self, data):
        elements = [Paragraph("Session Statistics", self.styles['SectionHeader'])]
        analytics = data.get('analytics', {})

        stats = [
            ['Metric', 'Value'],
            ['Total Frames Processed', str(analytics.get('total_frames', 0))],
            ['Average FPS', f"{analytics.get('avg_fps', 0):.1f}"],
            ['Average Confidence', f"{analytics.get('avg_confidence', 0):.1f}%"],
            ['Total Emotion Changes', str(data.get('emotion_changes', 0))],
            ['Detection Accuracy Estimate', f"{analytics.get('detection_accuracy_estimate', 0):.1f}%"],
        ]

        table = Table(stats, colWidths=[9 * cm, 7 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c63ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(table)
        return elements

    def _build_pie_chart(self, data):
        elements = [Paragraph("Emotion Distribution", self.styles['SectionHeader'])]
        distribution = data.get('analytics', {}).get('emotion_distribution', {}) or \
                       data.get('distribution', {})

        if not distribution:
            elements.append(Paragraph("No emotion data available.", self.styles['Normal']))
            return elements

        labels = [k.capitalize() for k in distribution.keys()]
        sizes  = list(distribution.values())
        clrs   = [PALETTE.get(k, '#999') for k in distribution.keys()]

        fig, ax = plt.subplots(figsize=(5, 4))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=clrs,
            autopct='%1.1f%%', startangle=90,
            textprops={'fontsize': 9}
        )
        for at in autotexts:
            at.set_fontsize(8)
        ax.set_title('Emotion Distribution', fontsize=11, fontweight='bold', pad=10)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        img = RLImage(buf, width=10 * cm, height=8 * cm)
        elements.append(img)
        return elements

    def _build_timeline_table(self, data):
        elements = [Paragraph("Emotion Timeline (Last 30 entries)", self.styles['SectionHeader'])]
        timeline = data.get('timeline', [])[-30:]

        if not timeline:
            elements.append(Paragraph("No timeline data available.", self.styles['Normal']))
            return elements

        rows = [['Time', 'Emotion', 'Confidence', 'Faces']]
        for entry in timeline:
            rows.append([
                entry.get('timestamp', ''),
                entry.get('emotion', '').capitalize(),
                f"{entry.get('confidence', 0):.1f}%",
                str(entry.get('face_count', 1)),
            ])

        table = Table(rows, colWidths=[3.5*cm, 5*cm, 4.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('ALIGN', (2, 0), (3, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)
        return elements

    def _build_behavior_summary(self, data):
        elements = [Paragraph("Behavior Summary", self.styles['SectionHeader'])]
        beh = data.get('behavior_summary', {})

        rows = [
            ['Total Blinks Detected', str(beh.get('total_blinks', 0))],
            ['Smile Frames', str(beh.get('smile_frames', 0))],
        ]
        table = Table(rows, colWidths=[9 * cm, 7 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        return elements

    def _build_ai_insights(self, data):
        elements = [Paragraph("AI Insights & Recommendations", self.styles['SectionHeader'])]
        analytics = data.get('analytics', {})
        dominant = analytics.get('dominant_emotion', 'neutral').lower()

        insights = {
            'happy':   "The subject maintained a positive emotional state throughout the session. Continue engaging activities.",
            'sad':     "Signs of sadness were detected. Consider a short walk, hydration, or a break from screen time.",
            'angry':   "Elevated frustration was detected. Practice deep breathing: inhale for 4s, hold 4s, exhale 4s.",
            'neutral': "A calm, neutral state was maintained — ideal for focused work or study.",
            'fear':    "Anxiety indicators were detected. Slow deep breathing and grounding exercises are recommended.",
            'surprise':"Frequent surprise responses may indicate high engagement or unexpected stimuli.",
            'disgust': "Discomfort signals detected. A short break and a change of environment may help.",
        }
        text = insights.get(dominant, "Session completed successfully.")
        elements.append(Paragraph(f"<b>Dominant emotion: {dominant.capitalize()}</b>", self.styles['Normal']))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(text, self.styles['Normal']))
        return elements

    def _build_footer(self):
        elements = [
            Spacer(1, 1 * cm),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')),
            Spacer(1, 0.3 * cm),
            Paragraph(
                f"Generated by EmotionVision AI Platform · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ParagraphStyle('Footer', parent=self.styles['Normal'],
                               fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
            ),
        ]
        return elements
