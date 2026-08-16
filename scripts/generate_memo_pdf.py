import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
        self.drawString(54, 800, "Heartweb / Hardware Design | SEO-Workflow & Notion-Bridge")
        self.drawRightString(541, 800, "Technisches Briefing")
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
    fontSize=17,
    leading=21,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=4
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9.5,
    leading=13,
    textColor=colors.HexColor("#475569"),
    spaceAfter=10
)

h2_style = ParagraphStyle(
    "SectionH2",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#1e293b"),
    spaceBefore=8,
    spaceAfter=4
)

body_style = ParagraphStyle(
    "BodyDark",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor("#334155"),
    spaceAfter=5
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10.5,
    textColor=colors.white
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10.5,
    textColor=colors.HexColor("#1e293b")
)

table_cell_bold = ParagraphStyle(
    "TableCellBold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=10.5,
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
    story.append(Paragraph("Technisches Briefing: Claude Desktop zu Notion Bridge", title_style))
    story.append(Paragraph("<b>An:</b> Jesse Jensen &nbsp;|&nbsp; <b>Von:</b> Raphael Rechberger &nbsp;|&nbsp; <b>Datum:</b> 16. August 2026<br/><b>GitHub:</b> https://github.com/Frater418/claude-desktop-seo-workflow-production", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    # Executive Summary
    story.append(Paragraph("1. Ausgangslage & Zielsetzung", h2_style))
    summary_text = (
        "Wie im Onboarding besprochen, steht Heartweb vor dem Skalierungsschritt von ad-hoc Steuerung hin zu einer zentralen "
        "Notion-Plattform. Wir haben deinen SEO-Workflow nicht neu erfunden, sondern ein deterministisches, datenbank-kompatibles "
        "Fundament geschaffen. Das System laeuft lokal in Claude Desktop, erzeugt aber standardisierte Datenstrukturen "
        "(JSON/YAML-Frontmatter), die nahtlos in dein neues Notion-Setup einfliessen und spaeter per API/Webhook vollautomatisiert werden koennen."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))

    # Comparison Table
    story.append(Paragraph("2. Die 6 technischen Bausteine im Ueberblick", h2_style))
    
    table_data = [
        [
            Paragraph("Baustein / Prompt", table_header_style),
            Paragraph("Lokale Claude Desktop Pipeline", table_header_style),
            Paragraph("Zukuenftige Notion- & Automations-Bridge", table_header_style)
        ],
        [
            Paragraph("<b>0. manifest.json</b>", table_cell_bold),
            Paragraph("Maschinenlesbarer Single Source of Truth Zustand.", table_cell_style),
            Paragraph("Bildet 1:1 die Notion Mandanten-/Projekt-Datenbank ab.", table_cell_style)
        ],
        [
            Paragraph("<b>1c. design-system.css</b>", table_cell_bold),
            Paragraph("Screenshot-Extraktion von Farben, Typo und Buttons.", table_cell_style),
            Paragraph("Sichert visuelle CI-Konsistenz bis zur Landingpage.", table_cell_style)
        ],
        [
            Paragraph("<b>2. AgentSEO MCP</b>", table_cell_bold),
            Paragraph("Zieht Suchvolumen und KD vollautomatisch per API.", table_cell_style),
            Paragraph("Eliminiert 45-60 Min. manuelles Ahrefs-Abtippen pro Pillar.", table_cell_style)
        ],
        [
            Paragraph("<b>3. Python Solver</b>", table_cell_bold),
            Paragraph("Deterministische Bin-Packing Berechnung der 17 Wochen.", table_cell_style),
            Paragraph("Garantiert exakt 10-15h/Woche und 100% lokale Pflichtseiten.", table_cell_style)
        ],
        [
            Paragraph("<b>4a. Content-Briefing</b>", table_cell_bold),
            Paragraph("SERP-Intent Check, EEAT und Schema JSON-LD.", table_cell_style),
            Paragraph("Liefert Notion-Frontmatter fuer Regina, Katja, Alexander.", table_cell_style)
        ],
        [
            Paragraph("<b>4b. HTML-Generator</b>", table_cell_bold),
            Paragraph("Erzeugt autarke Landingpages im Design-System.", table_cell_style),
            Paragraph("Direkte Uebergabe an Web-Entwickler / WordPress.", table_cell_style)
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
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Notion Roadmap
    story.append(Paragraph("3. Zukuenftige Automations-Roadmap (Notion Integration)", h2_style))
    story.append(Paragraph("<b>Stufe 1 (Direkter MCP-Push):</b> Sobald die Agentur das Notion-Setup live schaltet, binden wir den Notion-MCP-Server in Claude Desktop ein. Die Roadmaps und Briefings werden per Tool-Call direkt als Datenbank-Eintraege angelegt.", body_style))
    story.append(Paragraph("<b>Stufe 2 (Event-Driven Pipeline via n8n):</b> Ein n8n-Workflow ueberwacht den Output-Ordner, parst das YAML-Frontmatter der Briefings, erstellt die Notion-Karten und weist diese per Auto-Tagging an Regina, Katja oder Alexander zu inklusive Slack-Notification.", body_style))
    story.append(Spacer(1, 4))

    # Next Steps for Call
    story.append(Paragraph("4. Gespraechspunkte fuer unseren Call", h2_style))
    story.append(Paragraph("&bull; Kurzer Walkthrough durch das GitHub-Repo und das interaktive Menuediagramm.<br/>"
                           "&bull; Abgleich der Frontmatter-Felder mit der Datenbankstruktur eurer Notion-Agentur.<br/>"
                           "&bull; Konfiguration der Claude Desktop App fuer den ersten gemeinsamen Kundenlauf.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully: {filename}")

build_pdf(pdf_canonical)
build_pdf(pdf_desktop)
