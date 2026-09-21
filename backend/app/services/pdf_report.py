"""
backend/app/services/pdf_report.py
-----------------------------------
ReportLab-based PDF generator for Municipal PWD Work Orders and Incident Reports.
Compliant with Windows environments (no GTK/WeasyPrint requirements).
"""
import io
from datetime import datetime, timezone
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    colors = None
    letter = None
    SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = None
    getSampleStyleSheet = ParagraphStyle = None

from .. import models


def generate_incident_pdf(incident: models.Incident) -> bytes:
    """
    Generate a formal Municipal PWD Road Defect Inspection & Work Order PDF.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Please install reportlab to generate PDFs.")
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


def generate_infra_deficiency_report(data: list) -> bytes:
    """
    Generates a formal Infrastructure Deficiency & Missing Assets PDF Report.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Please install reportlab to generate PDFs.")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#00236f"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    heading2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Heading2"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=6,
    )
    normal_style = styles["Normal"]

    story.append(Paragraph("MUNICIPAL TRANSPORT GRID — INFRASTRUCTURE DEFICIENCY AUDIT", title_style))
    story.append(Paragraph(f"CityVision Platform // Corridor Compliance Report // Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    story.append(Spacer(1, 8))

    table_data = [["Route Corridor", "Expected Assets", "Observed Assets", "Missing Count", "Deficiency Score", "Compliance Rating"]]
    for item in data:
        table_data.append([
            item.get("route_id", "Unknown"),
            str(item.get("expected_assets", 0)),
            str(item.get("observed_assets", 0)),
            str(item.get("missing_assets", 0)),
            f"{item.get('deficiency_score', 0):.1f}%",
            item.get("status", "Unknown"),
        ])

    t = Table(table_data, colWidths=[110, 85, 85, 80, 85, 95])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Recommended Corrective Actions:", heading2_style))
    story.append(Paragraph("1. Priority deployment of missing pedestrian crossing / zebra signage along Route Red.", normal_style))
    story.append(Paragraph("2. Replacement of damaged speed limit signboards on Route Blue corridor.", normal_style))
    story.append(Paragraph("3. Schedule field inspection for verified deficiency corridors within 7 business days.", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Auditor Signature:</b> ___________________________   <b>Authority Seal:</b> ____________", normal_style))

    doc.build(story)
    return buf.getvalue()


def generate_route_performance_report(data: dict) -> bytes:
    """
    Generates a formal Transit Corridor Performance & Congestion PDF Report.
    """
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed. Please install reportlab to generate PDFs.")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#00236f"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    normal_style = styles["Normal"]

    story.append(Paragraph("TRANSIT AUTHORITY — ROUTE PERFORMANCE & DELAY REPORT", title_style))
    story.append(Paragraph(f"CityVision Platform // Corridor Analysis // Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    story.append(Spacer(1, 8))

    overview = [
        [Paragraph("<b>Route Corridor:</b>", normal_style), Paragraph(str(data.get("route_id", "N/A")), normal_style)],
        [Paragraph("<b>Baseline Transit Time:</b>", normal_style), Paragraph(f"{data.get('baseline_minutes', 0)} mins", normal_style)],
        [Paragraph("<b>Actual Observed Transit Time:</b>", normal_style), Paragraph(f"{data.get('actual_minutes', 0)} mins", normal_style)],
        [Paragraph("<b>Delay Variance:</b>", normal_style), Paragraph(f"+{data.get('delay_minutes', 0)} mins", normal_style)],
        [Paragraph("<b>Corridor Status:</b>", normal_style), Paragraph(str(data.get("status", "Nominal")), normal_style)],
        [Paragraph("<b>Mean Congestion Index:</b>", normal_style), Paragraph(str(data.get("avg_congestion_index", 1.0)), normal_style)],
        [Paragraph("<b>Sample Data Points:</b>", normal_style), Paragraph(str(data.get("sample_count", 0)), normal_style)],
    ]

    t = Table(overview, colWidths=[180, 360])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5dd")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>Transport Commissioner Signature:</b> ___________________________", normal_style))

    doc.build(story)
    return buf.getvalue()

