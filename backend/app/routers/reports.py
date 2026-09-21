"""
backend/app/routers/reports.py
------------------------------
Endpoints for infrastructure deficiency audits and route performance reports,
offering both JSON payloads and downloadable ReportLab PDF formats.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.analytics_engine import (
    compute_infra_deficiency_score,
    compute_route_delay,
)
from ..services.pdf_report import (
    generate_infra_deficiency_report,
    generate_route_performance_report,
)

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
)


@router.get("/infrastructure-deficiency")
def get_infra_deficiency(
    route_id: Optional[str] = Query(None, description="Optional route filter"),
    db: Session = Depends(get_db),
):
    """
    Returns corridor infrastructure audit summary (expected vs observed signage/assets).
    """
    return compute_infra_deficiency_score(db, route_id)


@router.get("/infrastructure-deficiency.pdf")
def download_infra_deficiency_pdf(
    route_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Generates and returns the official Infrastructure Deficiency Audit PDF.
    """
    data = compute_infra_deficiency_score(db, route_id)
    pdf_bytes = generate_infra_deficiency_report(data)
    filename = f"infra_deficiency_{route_id or 'all_routes'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/route-performance")
def get_route_performance(
    route_id: str = Query("ROUTE-RED", description="Route identifier to audit"),
    db: Session = Depends(get_db),
):
    """
    Returns route transit time delay and congestion variance metrics.
    """
    return compute_route_delay(db, route_id)


@router.get("/route-performance.pdf")
def download_route_performance_pdf(
    route_id: str = Query("ROUTE-RED"),
    db: Session = Depends(get_db),
):
    """
    Generates and returns the official Route Performance & Congestion PDF.
    """
    data = compute_route_delay(db, route_id)
    pdf_bytes = generate_route_performance_report(data)
    filename = f"route_performance_{route_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
