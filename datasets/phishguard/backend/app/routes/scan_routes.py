"""
scan_routes.py
==============
Scan endpoints (all require a Bearer JWT):
    POST   /api/scans
    GET    /api/scans/history?page=1&limit=20
    DELETE /api/scans/{id}
    GET    /api/scans/export   -> PDF (ReportLab)
"""

import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=schemas.ScanResponse, status_code=status.HTTP_201_CREATED)
def create_scan(
    body: schemas.ScanCreateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    scan = models.ScanHistory(
        user_id=user.id,
        url=body.url,
        is_phishing=body.is_phishing,
        confidence=body.confidence,
        domain=body.domain,
        features_json=body.features_json,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/history", response_model=schemas.ScanHistoryPage)
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    base = db.query(models.ScanHistory).filter(models.ScanHistory.user_id == user.id)
    total = base.count()
    items = (
        base.order_by(models.ScanHistory.scanned_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"page": page, "limit": limit, "total": total, "items": items}


@router.delete("/{scan_id}", response_model=schemas.MessageResponse)
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    scan = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.id == scan_id, models.ScanHistory.user_id == user.id)
        .first()
    )
    if scan is None:
        # Either doesn't exist or doesn't belong to this user -> 404 (don't leak).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return {"message": "Scan deleted"}


@router.get("/export")
def export_pdf(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Generate a PDF report of the user's scan history with ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )

    scans = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.user_id == user.id)
        .order_by(models.ScanHistory.scanned_at.desc())
        .all()
    )

    total = len(scans)
    phishing = sum(1 for s in scans if s.is_phishing)
    safe = total - phishing

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="PhishGuard Scan History Report")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9)
    cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=10)

    elements = []
    elements.append(Paragraph("PhishGuard — Scan History Report", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"User: {user.name or '-'} ({user.email})", small))
    elements.append(
        Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", small)
    )
    elements.append(Spacer(1, 10))

    # Summary box.
    summary_data = [["Total scans", "Phishing detected", "Safe URLs"], [str(total), str(phishing), str(safe)]]
    summary = Table(summary_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(summary)
    elements.append(Spacer(1, 14))

    # Scan table.
    header = ["No.", "Date & Time", "URL", "Result", "Confidence %"]
    rows = [header]
    for idx, s in enumerate(scans, start=1):
        dt = s.scanned_at.strftime("%Y-%m-%d %H:%M") if s.scanned_at else "-"
        result = "PHISHING" if s.is_phishing else "SAFE"
        conf = f"{round(s.confidence * 100, 1)}" if s.confidence <= 1 else f"{round(s.confidence, 1)}"
        rows.append([str(idx), dt, Paragraph(s.url, cell), result, conf])

    table = Table(rows, colWidths=[12 * mm, 30 * mm, 85 * mm, 22 * mm, 23 * mm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]
    # Colour the result cells.
    for i, s in enumerate(scans, start=1):
        if s.is_phishing:
            style.append(("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#C62828")))
        else:
            style.append(("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#2E7D32")))
    table.setStyle(TableStyle(style))
    elements.append(table)

    doc.build(elements)
    buf.seek(0)

    safe_name = (user.name or "user").replace(" ", "_")
    filename = f"scan_history_{safe_name}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
