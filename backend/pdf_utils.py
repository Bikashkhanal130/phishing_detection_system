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
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def build_history_pdf(user, history_items, page_width=None, page_height=None) -> bytes:
    """
    page_width/page_height: optional page size in points. When given (the app
    passes the phone's screen size), the PDF page matches that aspect ratio
    so it fills the screen instead of showing as an A4 sheet with dead space.
    Falls back to A4 when not provided.
    """
    buffer = io.BytesIO()
    pagesize = (page_width, page_height) if page_width and page_height else A4
    margin = 10 * mm
    doc = SimpleDocTemplate(
        buffer, pagesize=pagesize,
        topMargin=margin, bottomMargin=margin,
        leftMargin=margin, rightMargin=margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HistoryTitle", parent=styles["Title"], fontSize=20, leading=24,
    )
    info_style = ParagraphStyle(
        "HistoryInfo", parent=styles["Normal"], fontSize=11, leading=15,
    )
    cell_style = ParagraphStyle(
        "HistoryCell", parent=styles["BodyText"], fontSize=10, leading=13,
    )
    safe_style = ParagraphStyle(
        "ResultSafe", parent=cell_style, textColor=colors.HexColor("#1e8e3e"),
        fontName="Helvetica-Bold",
    )
    phishing_style = ParagraphStyle(
        "ResultPhishing", parent=cell_style, textColor=colors.HexColor("#c0392b"),
        fontName="Helvetica-Bold",
    )

    story = []

    story.append(Paragraph("Phishing Detector — Search History", title_style))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f"User: {user.full_name} ({user.email})", info_style))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", info_style))
    story.append(Paragraph(f"Total checks: {len(history_items)}", info_style))
    story.append(Spacer(1, 6 * mm))

    # Table header + rows. Every text cell is a Paragraph (not a plain string)
    # so it wraps instead of overflowing on the narrower phone-sized pages.
    data = [["#", "Date", "URL", "Result", "Confidence"]]
    for i, item in enumerate(history_items, start=1):
        date_str = item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "-"
        result_style = phishing_style if item.result.lower() == "phishing" else safe_style
        data.append([
            str(i),
            Paragraph(date_str, cell_style),
            Paragraph(item.url, cell_style),
            Paragraph(item.result, result_style),
            Paragraph(f"{item.confidence:.1f}%", cell_style),
        ])

    available_width = pagesize[0] - 2 * margin
    col_fractions = [0.05, 0.20, 0.40, 0.17, 0.18]
    col_widths = [f * available_width for f in col_fractions]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d7de")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fb")]),
    ])
    table.setStyle(style)
    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
