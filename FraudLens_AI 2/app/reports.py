from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from datetime import datetime

def create_pdf(path, record, metadata, frames=None, pages=None):
    styles = getSampleStyleSheet()
    pages = pages or []
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm)
    story = [
        Paragraph("FraudLens AI – Media Authenticity Report", styles["Title"]),
        Paragraph("AI-powered image, video, and PDF page analysis with forensic observations", styles["Normal"]),
        Spacer(1, 8*mm),
    ]
    rows = [
        ["Field", "Result"],
        ["File", record["filename"]],
        ["Media type", record["media_type"].title()],
        ["Classification", record["classification"]],
        ["AI-generation likelihood", f'{record["ai_likelihood"]}%' if record["ai_likelihood"] is not None else "Unavailable"],
        ["Camera-origin likelihood", f'{record["camera_likelihood"]}%' if record["camera_likelihood"] is not None else "Unavailable"],
        ["SHA-256", record["sha256"]],
        ["Analyzed at (UTC)", record["created_at"]],
        ["Model", record["model_name"] or "Not available"],
    ]
    table = Table(rows, colWidths=[55*mm, 115*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 7),
        ("WORDWRAP", (0,0), (-1,-1), True),
    ]))
    story.append(table)
    story += [Spacer(1, 7*mm), Paragraph("Forensic metadata", styles["Heading2"])]
    for key, value in metadata.items():
        story.append(Paragraph(f"<b>{str(key)[:80]}:</b> {str(value)[:500]}", styles["BodyText"]))
    if frames:
        story += [Spacer(1, 5*mm), Paragraph("Video frame results", styles["Heading2"])]
        frame_rows = [["Frame", "Time (s)", "AI likelihood", "Classification"]]
        for f in frames:
            frame_rows.append([str(f["frame_number"]), str(f["timestamp_seconds"]),
                               f'{f["ai_likelihood"]}%' if f["ai_likelihood"] is not None else "Unavailable",
                               f["classification"] or "Unavailable"])
        ft = Table(frame_rows, repeatRows=1)
        ft.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E2E8F0")),
                                ("GRID",(0,0),(-1,-1),0.3,colors.grey),("PADDING",(0,0),(-1,-1),5)]))
        story.append(ft)
    if pages:
        story += [Spacer(1, 5*mm), Paragraph("PDF page analysis", styles["Heading2"])]
        page_rows = [["PDF page", "AI likelihood", "Classification"]]
        for page in pages:
            page_rows.append([str(page["page_number"]),
                              f'{page["ai_likelihood"]}%' if page["ai_likelihood"] is not None else "Unavailable",
                              page["classification"] or "Unavailable"])
        pt = Table(page_rows, repeatRows=1)
        pt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E2E8F0")),
                                ("GRID",(0,0),(-1,-1),0.3,colors.grey),
                                ("PADDING",(0,0),(-1,-1),5)]))
        story.append(pt)
    story += [Spacer(1, 8*mm),
              Paragraph("Important: Detector scores are estimates, not proof of origin or authenticity. "
                        "Results can be wrong, especially for new generators, edited, compressed, "
                        "or out-of-domain media. Use independent verification for important decisions.",
                        styles["Italic"])]
    doc.build(story)
