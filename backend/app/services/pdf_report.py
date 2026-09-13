"""
backend/app/services/pdf_report.py
-----------------------------------
ReportLab-based PDF generator for Municipal PWD Work Orders and Incident Reports.
Compliant with Windows environments (no GTK/WeasyPrint requirements).
"""
import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .. import models


def generate_incident_pdf(incident: models.Incident) -> bytes:
    """
    Generate a formal Municipal PWD Road Defect Inspection & Work Order PDF.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#00236f"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=14,
    )
    heading2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=10,
        spaceAfter=6,
    )
    normal_style = styles["Normal"]

    # Header
    story.append(Paragraph("MUNICIPAL TRANSIT GRID — ROAD DEFECT WORK ORDER", title_style))
    story.append(Paragraph(f"CityVision Platform // Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
    story.append(Spacer(1, 10))

    # Incident Overview Table
    overview_data = [
        [Paragraph("<b>Work Order ID:</b>", normal_style), Paragraph(f"WO-{incident.incident_id}", normal_style)],
        [Paragraph("<b>Defect Category:</b>", normal_style), Paragraph(incident.anomaly_type, normal_style)],
        [Paragraph("<b>Operational Severity:</b>", normal_style), Paragraph(incident.severity, normal_style)],
        [Paragraph("<b>Priority Score (0-100):</b>", normal_style), Paragraph(str(incident.priority_score), normal_style)],
        [Paragraph("<b>Current Lifecycle Status:</b>", normal_style), Paragraph(incident.status, normal_style)],
        [Paragraph("<b>GPS Coordinates:</b>", normal_style), Paragraph(f"{incident.latitude:.6f}, {incident.longitude:.6f}", normal_style)],
        [Paragraph("<b>Observation Count:</b>", normal_style), Paragraph(f"{incident.confirmation_count} (Across {incident.unique_bus_count} unique transit vehicles)", normal_style)],
        [Paragraph("<b>First Observed:</b>", normal_style), Paragraph(incident.first_detected_at.strftime("%Y-%m-%d %H:%M:%S"), normal_style)],
        [Paragraph("<b>Latest Sensed:</b>", normal_style), Paragraph(incident.last_detected_at.strftime("%Y-%m-%d %H:%M:%S"), normal_style)],
    ]

    t_overview = Table(overview_data, colWidths=[180, 360])
    t_overview.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9ff")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_overview)
    story.append(Spacer(1, 14))

    # Observations Section
    story.append(Paragraph("Sensing Lineage (Chronological Vehicle Observations)", heading2_style))
    obs_rows = [["Bus ID", "Route", "Timestamp", "Speed (km/h)", "Confidence"]]
    for obs in incident.observations[:10]:
        obs_rows.append([
            obs.bus_id,
            obs.route_id,
            obs.timestamp.strftime("%H:%M:%S"),
            f"{obs.speed_kmh:.1f}",
            f"{obs.confidence:.1%}",
        ])

    if len(obs_rows) > 1:
        t_obs = Table(obs_rows, colWidths=[100, 100, 140, 100, 100])
        t_obs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ]))
        story.append(t_obs)
    else:
        story.append(Paragraph("No individual sensor observations recorded.", normal_style))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Municipal Action Authorization:</b> ___________________________   <b>Date:</b> ____________", normal_style))

    doc.build(story)
    return buf.getvalue()
