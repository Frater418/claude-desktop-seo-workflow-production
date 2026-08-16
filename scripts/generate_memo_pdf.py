import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

pdf_canonical = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/docs/jesse-walkthrough-memo.pdf")
pdf_desktop = Path("C:/Users/offic/Desktop/Heartweb/jesse-walkthrough-memo.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header
        self.drawString(54, 800, "Heartweb / Hardware Design | SEO-Workflow Modernisierung")
        self.drawRightString(541, 800, "Executive Walkthrough Memo")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 792, 541, 792)
        # Footer
        self.line(54, 48, 541, 48)
        self.drawString(54, 36, "Autor: Raphael Rechberger | Vertraulich fuer Jesse Jensen")
        self.drawRightString(541, 36, f"Seite {self._pageNumber} von {page_count}")
        self.restoreState()

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#475569"),
    spaceAfter=12
)

h2_style = ParagraphStyle(
    "SectionH2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#1e293b"),
    spaceBefore=10,
    spaceAfter=6
)

body_style = ParagraphStyle(
    "BodyDark",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#334155"),
    spaceAfter=6
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#1e293b")
)

table_cell_bold = ParagraphStyle(
    "TableCellBold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#0f172a")
)

def build_pdf(filename):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=60
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Modernisierung des SEO-Workflows fuer Claude Desktop", title_style))
    story.append(Paragraph("<b>An:</b> Jesse Jensen &nbsp;|&nbsp; <b>Von:</b> Raphael Rechberger &nbsp;|&nbsp; <b>Datum:</b> 16. August 2026<br/><b>GitHub:</b> https://github.com/Frater418/claude-desktop-seo-workflow-production", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    summary_text = (
        "Hi Jesse, basierend auf unserem Onboarding-Call habe ich deinen bestehenden Prompt-Workflow (Schritte 0 bis 4) "
        "analysiert und in eine hochgradig skalierbare, fehlertolerante Produktionsarchitektur fuer die Claude Desktop App "
        "ueberfuehrt. Die inhaltliche Substanz deines Workflows (Pillars, Cluster, 120-Tage-Logik, lokale Pflichtseiten) "
        "wurde vollstaendig beibehalten. Wir haben das Rad nicht neu erfunden, sondern ein stabiles technisches Fundament darum "
        "gebaut, damit du bei mehreren parallelen Kunden-Rollouts maximale Entlastung hast und Claude niemals den Kontext verliert."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))

    # Comparison Table
    story.append(Paragraph("2. Was wir ZUSAETZLICH gebaut und optimiert haben", h2_style))
    
    table_data = [
        [
            Paragraph("Workflow-Bereich", table_header_style),
            Paragraph("Bisheriger Stand (Manuelle Reibung)", table_header_style),
            Paragraph("Modernisierter Standard (Produktionsgewinn)", table_header_style)
        ],
        [
            Paragraph("<b>Projekt-Status</b>", table_cell_bold),
            Paragraph("Kontext musste aus Chatverlauf gesucht werden; Kontextverlust bei Neustarts.", table_cell_style),
            Paragraph("<b>manifest.json</b> als maschinenlesbarer Single Source of Truth Status pro Projekt.", table_cell_style)
        ],
        [
            Paragraph("<b>Design & CI</b>", table_cell_bold),
            Paragraph("Design aus Schritt 1c ging verloren; CSS in Schritt 4 neu erraten.", table_cell_style),
            Paragraph("<b>design-system.css</b> persistiert Farb- und Typo-Tokens fuer konsistente HTML-Seiten.", table_cell_style)
        ],
        [
            Paragraph("<b>Keyword-Check</b>", table_cell_bold),
            Paragraph("45-60 Min. pro Pillar: Keywords einzeln in Ahrefs pruefen und abtippen.", table_cell_style),
            Paragraph("<b>AgentSEO MCP</b> liefert verifizierte SV/KD-Daten vollautomatisch in 2 Min.", table_cell_style)
        ],
        [
            Paragraph("<b>120-Tage-Plan</b>", table_cell_bold),
            Paragraph("LLM verrechnet sich bei 17 Wochen mit variierenden Stundensummen.", table_cell_style),
            Paragraph("<b>Deterministischer Solver</b> garantiert exakt 10-15h/Woche und lokale Pflichtseiten.", table_cell_style)
        ],
        [
            Paragraph("<b>Tagesgeschaeft (4)</b>", table_cell_bold),
            Paragraph("Schritt 4 ueberladen (Briefing, Schema und HTML gleichzeitig brachen oft ab).", table_cell_style),
            Paragraph("<b>Trennung in 4a (Texter-Briefing) & 4b (HTML)</b> inkl. Notion-Frontmatter.", table_cell_style)
        ],
        [
            Paragraph("<b>Qualitaetssicherung</b>", table_cell_bold),
            Paragraph("Keine formalen Zwischenstopps oder Qualitaets-Gates.", table_cell_style),
            Paragraph("<b>7 verbindliche Quality Gates</b> & striktes Fail-Fast ohne Schaetzdaten.", table_cell_style)
        ]
    ]

    t = Table(table_data, colWidths=[90, 195, 202])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Role Workflow
    story.append(Paragraph("3. Zusammenarbeit im Team (Jesse, Copywriter, Entwicklung)", h2_style))
    story.append(Paragraph("<b>1. Fuer Jesse & Raphael (Strategie & Rollout):</b> Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige, mathematisch gepruefte 120-Tage-Roadmap, die direkt in Notion uebernommen werden kann.", body_style))
    story.append(Paragraph("<b>2. Fuer die Copywriter (Regina, Katja, Alexander):</b> Schritt 4a erzeugt glasklare Briefings mit Suchintention, Gliederung, FAQ-Antworten, internen Links und Notion-Frontmatter, ohne verwirrenden HTML-Code.", body_style))
    story.append(Paragraph("<b>3. Fuer die Web-Entwicklung:</b> Erhaelt aus 1b den Menuebaum (HTML) und aus 4b direkt einsatzbereite Landingpages mit integriertem Schema.org Markup.", body_style))
    story.append(Spacer(1, 6))

    # Next Steps for Call
    story.append(Paragraph("4. Vorbereitung auf unseren anstehenden Call", h2_style))
    story.append(Paragraph("Im Call koennen wir direkt das GitHub-Repo aufrufen und besprechen:<br/>"
                           "&bull; Live-Walkthrough durch die README.md und das interaktive Menuediagramm.<br/>"
                           "&bull; Einrichten deiner claude_desktop_config.json fuer den AgentSEO MCP-Server.<br/>"
                           "&bull; Start des ersten Test-Rollouts an einem echten Kundenprojekt.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully: {filename}")

build_pdf(pdf_canonical)
build_pdf(pdf_desktop)
