"""
generate_submission_docs.py — Generate complete Unstop submission files:
1. Brief_Project_Description.docx (and .pdf)
2. Short_Pitch_Presentation.pdf
3. Short_Pitch_Presentation.pptx
"""

import os
from pathlib import Path

# --- Paths ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "submission"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. GENERATE BRIEF PROJECT DESCRIPTION (.docx)
def create_docx():
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Title
    p_title = doc.add_paragraph()
    run_title = p_title.add_run("LiveScribe — On-Device Real-Time AI Meeting Intelligence")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run("Snapdragon® AI Lab Build & Present Challenge 2026 | Submission Document\nAuthor: Kshitij Jaiswal | GitHub: https://github.com/SlayerHADES/LiveScribe")
    run_sub.font.size = Pt(10)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_heading("1. Problem Statement", level=1)
    doc.add_paragraph(
        "Existing meeting and lecture transcription tools rely entirely on cloud servers. "
        "This introduces severe data privacy risks for confidential business discussions, IP-sensitive research, and personal notes. "
        "Furthermore, cloud tools fail completely when internet connectivity is unavailable — such as in flight, in basement labs, or in low-connectivity classrooms."
    )

    doc.add_heading("2. Solution Overview", level=1)
    doc.add_paragraph(
        "LiveScribe is an on-device, real-time AI live transcription and meeting intelligence platform running 100% locally on the Snapdragon® Hexagon NPU via ONNX Runtime's QNN Execution Provider (QNNExecutionProvider). "
        "No audio or transcript data ever leaves the device."
    )

    doc.add_heading("3. Key Capabilities & Product Features", level=1)
    features = [
        ("Real-Time Speech Recognition", "Sub-300ms latency continuous streaming transcription using Whisper-base ONNX quantized models running locally on the Hexagon NPU."),
        ("Local LLM Meeting Intelligence", "On-demand AI summarization extracting executive briefs, key decisions, and action items with automatic owner assignment."),
        ("Contextual Ask AI with Timestamp Citations", "Embedded assistant allowing users to ask questions about the conversation, with clickable timestamp citations (e.g. '📍 10:43 — Kshitij M.') that auto-scroll to the exact transcript moment."),
        ("Real-Time Telemetry & Offline Proof", "In-app benchmark panel displaying live CPU %, process memory, NPU provider status, and an OS-level network indicator proving 100% functionality with Wi-Fi disabled."),
        ("Notes Export", "One-click export of structured Markdown reports containing executive summaries, decision lists, task tables, and full transcripts."),
    ]
    for title, desc in features:
        p = doc.add_paragraph(style='List Bullet')
        r1 = p.add_run(f"{title}: ")
        r1.bold = True
        p.add_run(desc)

    doc.add_heading("4. Hardware & Technical Architecture", level=1)
    doc.add_paragraph(
        "- Hardware Target: Snapdragon® X Elite / Plus (Qualcomm Hexagon NPU)\n"
        "- Inference Runtime: ONNX Runtime with QNN Execution Provider (QNNExecutionProvider)\n"
        "- Backend Engine: Python FastAPI, WebSocket streaming (WS /ws/transcribe)\n"
        "- Frontend UI: Venture-backed SaaS studio UI (Linear + Raycast + Chatbase + Reevo aesthetic) with HTML5 Canvas audio visualizers and Cmd+K command palette."
    )

    doc.add_heading("5. NPU Benchmarks & Performance", level=1)
    table = doc.add_table(rows=5, cols=3)
    table.style = 'Table Grid'
    headers = ["Feature / Metric", "Cloud Tools", "LiveScribe (Snapdragon NPU)"]
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True

    data = [
        ("Works Offline", "No", "Yes (100% Local / Airplane Mode)"),
        ("Audio Data Privacy", "Sent to Cloud (Risk)", "0 Bytes Leave Device"),
        ("Inference Hardware", "Remote Cloud GPU Cluster", "Qualcomm Hexagon NPU"),
        ("Chunk Latency", "1000 - 3000 ms", "~300 ms / chunk"),
    ]
    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = text

    filepath = OUTPUT_DIR / "Brief_Project_Description.docx"
    doc.save(filepath)
    print(f"Created: {filepath}")


# 2. GENERATE SHORT PITCH PRESENTATION (.pdf)
def create_pdf_presentation():
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    pdf_path = OUTPUT_DIR / "Short_Pitch_Presentation.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(letter),
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('SlideTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('SlideSub', parent=styles['Normal'], fontName='Helvetica', fontSize=12, leading=16, textColor=colors.HexColor('#64748B'))
    body_style = ParagraphStyle('SlideBody', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=16, textColor=colors.HexColor('#334155'))
    bullet_style = ParagraphStyle('SlideBullet', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#1E293B'))

    story = []

    # Slide 1: Title
    story.append(Paragraph("LiveScribe", ParagraphStyle('MainTitle', fontName='Helvetica-Bold', fontSize=36, leading=40, textColor=colors.HexColor('#0284C7'))))
    story.append(Paragraph("Your Conversation, Understood in Real Time — On-Device Snapdragon® AI", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Presenter:</b> Kshitij Jaiswal | <b>Challenge:</b> Snapdragon® AI Lab Build & Present 2026", sub_style))
    story.append(Paragraph("<b>GitHub:</b> https://github.com/SlayerHADES/LiveScribe", sub_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("• <b>100% Private:</b> Audio & transcripts never leave the device.<br/>• <b>Sub-300ms Latency:</b> Real-time streaming Whisper speech recognition.<br/>• <b>Zero Internet Required:</b> Fully functional in Airplane Mode on the Hexagon NPU.", body_style))
    story.append(PageBreak())

    # Slide 2: Problem
    story.append(Paragraph("1. The Problem", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("• <b>Cloud Dependency:</b> Existing tools (Otter, Fathom, Fireflies) upload raw microphone audio to remote GPU servers.", bullet_style))
    story.append(Paragraph("• <b>Privacy Risks:</b> Executive meetings, financial reviews, and IP research exposed to cloud leaks.", bullet_style))
    story.append(Paragraph("• <b>Connectivity Failure:</b> Cloud speech tools fail completely in flight, in basement labs, or in low-signal areas.", bullet_style))
    story.append(PageBreak())

    # Slide 3: Solution
    story.append(Paragraph("2. The Solution — LiveScribe", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("• <b>On-Device Hexagon NPU Processing:</b> End-to-end execution of STT and LLM summarization locally via ONNX Runtime QNN Provider.", bullet_style))
    story.append(Paragraph("• <b>Real-Time Visualizer & Streaming:</b> Canvas audio visualizer with word-by-word streaming text animation.", bullet_style))
    story.append(Paragraph("• <b>Automated Meeting Intelligence:</b> Instant generation of executive briefs, decision lists, and task owner tables.", bullet_style))
    story.append(PageBreak())

    # Slide 4: Architecture
    story.append(Paragraph("3. Technical Architecture", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Pipeline Flow:</b><br/>Microphone Audio (16kHz PCM) → WebSocket Stream → ONNX Runtime QNN Provider → Hexagon NPU → Whisper Transcript → Local LLM Summarization", body_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("• <b>Backend:</b> Python FastAPI, WebSocket streaming (`WS /ws/transcribe`)", bullet_style))
    story.append(Paragraph("• <b>Frontend:</b> Venture-backed SaaS studio UI (Linear + Raycast + Chatbase + Reevo aesthetic) with HTML5 Canvas visualizer and Cmd+K command palette.", bullet_style))
    story.append(PageBreak())

    # Slide 5: NPU Benchmarks
    story.append(Paragraph("4. Why NPU — Performance Benchmarks", title_style))
    story.append(Spacer(1, 15))

    table_data = [
        [Paragraph("<b>Metric</b>", bullet_style), Paragraph("<b>Cloud Tools</b>", bullet_style), Paragraph("<b>LiveScribe (Hexagon NPU)</b>", bullet_style)],
        [Paragraph("Connectivity", bullet_style), Paragraph("Requires Active Internet", bullet_style), Paragraph("<b>100% Offline (Airplane Mode)</b>", bullet_style)],
        [Paragraph("Data Privacy", bullet_style), Paragraph("Sent to Remote Cloud", bullet_style), Paragraph("<b>0 Bytes Leave Laptop</b>", bullet_style)],
        [Paragraph("Hardware", bullet_style), Paragraph("Remote GPU Cluster", bullet_style), Paragraph("<b>Qualcomm Hexagon NPU</b>", bullet_style)],
        [Paragraph("Chunk Latency", bullet_style), Paragraph("1000 - 3000 ms", bullet_style), Paragraph("<b>~300 ms / chunk</b>", bullet_style)],
    ]
    t = Table(table_data, colWidths=[180, 220, 260])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())

    # Slide 6: UX & Export
    story.append(Paragraph("5. Interactive AI & Notes Export", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("• <b>Timestamp Citing AI:</b> Ask AI assistant cites clickable timestamps (`📍 10:43 — Kshitij M.`) auto-scrolling to exact transcript lines.", bullet_style))
    story.append(Paragraph("• <b>Raycast Command Palette:</b> Cmd+K search modal with instant query match highlighting.", bullet_style))
    story.append(Paragraph("• <b>One-Click Markdown Export:</b> Generates complete meeting notes document (`LiveScribe_Meeting_Notes.md`).", bullet_style))

    doc.build(story)
    print(f"Created: {pdf_path}")


# 3. GENERATE SHORT PITCH PRESENTATION (.pptx)
def create_pptx_presentation():
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    def add_header(slide, title_text, category_text="LIVESCRIBE PRESENTATION"):
        # Header background banner
        txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.2))
        tf = txBox.text_frame
        tf.word_wrap = True

        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = RGBColor(14, 165, 233)

        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.size = Pt(28)
        p1.font.bold = True
        p1.font.color.rgb = RGBColor(15, 23, 42)

    # Slide 1: Title
    slide1 = prs.slides.add_slide(blank_layout)
    txBox = slide1.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "LIVESCRIBE"
    p0.font.size = Pt(44)
    p0.font.bold = True
    p0.font.color.rgb = RGBColor(14, 165, 233)

    p1 = tf.add_paragraph()
    p1.text = "Your Conversation, Understood in Real Time — On-Device Snapdragon® AI"
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(15, 23, 42)

    p2 = tf.add_paragraph()
    p2.text = "\nPresenter: Kshitij Jaiswal | Challenge: Snapdragon® AI Lab Build & Present 2026\nGitHub: https://github.com/SlayerHADES/LiveScribe"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(100, 116, 139)

    # Slide 2: Problem
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "1. The Problem")
    txBox = slide2.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    bullets = [
        "Cloud Dependency: Existing transcription tools (Otter, Fathom) send raw mic audio to remote GPU servers.",
        "Data Privacy Exposure: Financial reviews, executive strategy, and IP research exposed to cloud breaches.",
        "Connectivity Failure: Cloud tools fail completely in flight, in basement labs, or in low-signal areas."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(51, 65, 85)

    # Slide 3: Solution
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "2. The Solution — LiveScribe")
    txBox = slide3.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    bullets = [
        "On-Device Hexagon NPU Processing: STT and LLM summarization executed locally via ONNX Runtime QNN Provider.",
        "Real-Time Waveform & Streaming: HTML5 Canvas audio visualizer with word-by-word streaming text animation.",
        "Automated Meeting Intelligence: Instant generation of executive summaries, decision lists, and task owner tables."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(51, 65, 85)

    # Slide 4: Architecture
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "3. Technical Architecture & Pipeline")
    txBox = slide4.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    bullets = [
        "Pipeline: Microphone Audio (16kHz PCM) → WebSocket Stream → ONNX Runtime QNN Provider → Hexagon NPU → Whisper Transcript → Local LLM Summarization",
        "Backend: Python FastAPI, WebSocket streaming (WS /ws/transcribe)",
        "Frontend: Venture-backed SaaS studio UI (Linear + Raycast + Chatbase + Reevo aesthetic) with Cmd+K command palette."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(51, 65, 85)

    # Slide 5: NPU Benchmarks
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "4. Why NPU — Performance Benchmarks")
    txBox = slide5.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    bullets = [
        "Connectivity: 100% Offline (Works in Airplane Mode)",
        "Data Privacy: 0 Bytes Leave the Laptop",
        "Inference Hardware: Qualcomm Hexagon NPU via QNNExecutionProvider",
        "Chunk Latency: ~300 ms / chunk"
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(51, 65, 85)

    # Slide 6: UX & Export
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "5. Interactive AI & Notes Export")
    txBox = slide6.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    bullets = [
        "Timestamp Citing AI: Ask AI assistant cites clickable timestamps (📍 10:43 — Kshitij M.) auto-scrolling to exact transcript lines.",
        "Raycast Command Palette: Cmd+K search modal with instant query match highlighting.",
        "One-Click Markdown Export: Generates complete meeting notes document (LiveScribe_Meeting_Notes.md)."
    ]
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(51, 65, 85)

    pptx_path = OUTPUT_DIR / "Short_Pitch_Presentation.pptx"
    prs.save(pptx_path)
    print(f"Created: {pptx_path}")


if __name__ == "__main__":
    create_docx()
    create_pdf_presentation()
    create_pptx_presentation()
    print("\n[SUCCESS] All submission documents generated in docs/submission/")
