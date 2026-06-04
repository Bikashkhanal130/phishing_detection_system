"""
pdf_utils.py
------------
Builds a PDF of a user's search history using reportlab and returns the bytes.
The Flask endpoint streams these bytes to the Android app as a download.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_history_pdf(user, history_items) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Phishing Detector — Search History", styles["Title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f"User: {user.full_name} ({user.email})", styles["Normal"]))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Paragraph(f"Total checks: {len(history_items)}", styles["Normal"]))
    story.append(Spacer(1, 6 * mm))

    # Table header + rows
    data = [["#", "Date", "URL", "Result", "Confidence"]]
    wrap = styles["BodyText"]
    for i, item in enumerate(history_items, start=1):
        date_str = item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-"
        data.append([
            str(i),
            date_str,
            Paragraph(item.url, wrap),
            item.result,
            f"{item.confidence:.1f}%",
        ])

    table = Table(data, colWidths=[10 * mm, 30 * mm, 85 * mm, 22 * mm, 23 * mm], repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d7de")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fb")]),
    ])
    # Colour the Result column
    for row_idx, item in enumerate(history_items, start=1):
        c = colors.HexColor("#c0392b") if item.result.lower() == "phishing" else colors.HexColor("#1e8e3e")
        style.add("TEXTCOLOR", (3, row_idx), (3, row_idx), c)
        style.add("FONTNAME", (3, row_idx), (3, row_idx), "Helvetica-Bold")
    table.setStyle(style)
    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
