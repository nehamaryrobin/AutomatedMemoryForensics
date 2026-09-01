import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.case import Case, EvidenceMetadata, TimelineEvent

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

router = APIRouter()

@router.get("/{case_id}/report/pdf")
async def generate_pdf_report(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generates a professional PDF report containing the case metadata, 
    risk score, findings, and timeline.
    """
    # 1. Fetch data
    result_case = await db.execute(select(Case).filter(Case.id == case_id))
    case = result_case.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    result_findings = await db.execute(select(EvidenceMetadata).filter(EvidenceMetadata.case_id == case_id))
    findings = result_findings.scalars().all()

    result_timeline = await db.execute(
        select(TimelineEvent)
        .filter(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.timestamp.asc())
    )
    timeline = result_timeline.scalars().all()

    # 2. Build PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RiskScore', fontName='Helvetica-Bold', fontSize=14, textColor=colors.red))
    styles.add(ParagraphStyle(name='SectionHeader', fontName='Helvetica-Bold', fontSize=14, spaceAfter=10, spaceBefore=20))
    styles.add(ParagraphStyle(name='FindingType', fontName='Helvetica-Bold', fontSize=12, textColor=colors.darkred))
    styles.add(ParagraphStyle(name='TimelineEvent', fontName='Helvetica', fontSize=10, leading=14))
    
    story = []

    # Title
    story.append(Paragraph("SIH Automated Memory Forensics Report", styles['Title']))
    story.append(Spacer(1, 20))

    # Case Summary
    story.append(Paragraph("Case Summary", styles['SectionHeader']))
    summary_data = [
        ["Case ID", case.id],
        ["Filename", case.filename],
        ["SHA-256", case.sha256],
        ["Status", case.status],
        ["Risk Score", f"{case.risk_score}"]
    ]
    t_summary = Table(summary_data, colWidths=[100, 350])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 20))

    # Findings
    story.append(Paragraph("Executive Findings", styles['SectionHeader']))
    if not findings:
        story.append(Paragraph("No suspicious artifacts detected.", styles['Normal']))
    else:
        for f in findings:
            story.append(Paragraph(f.finding_type, styles['FindingType']))
            story.append(Paragraph(f"Severity: {f.severity} | Confidence: {f.confidence*100:.0f}%", styles['Italic']))
            story.append(Paragraph(f.description, styles['Normal']))
            story.append(Spacer(1, 10))

    # Timeline
    story.append(Paragraph("Chronological Timeline", styles['SectionHeader']))
    if not timeline:
        story.append(Paragraph("No timeline events generated.", styles['Normal']))
    else:
        for event in timeline:
            time_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if event.timestamp else "Unknown Time"
            text = f"<b>{time_str}</b> - [{event.event_type}] {event.details}"
            story.append(Paragraph(text, styles['TimelineEvent']))
            story.append(Spacer(1, 5))

    # Build document
    doc.build(story)
    buffer.seek(0)

    # 3. Return StreamingResponse
    headers = {
        'Content-Disposition': f'attachment; filename="forensics_report_{case_id}.pdf"'
    }
    return StreamingResponse(buffer, headers=headers, media_type='application/pdf')
