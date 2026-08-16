import os
import pypdf
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

pdf_canonical = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/docs/jesse-walkthrough-memo.pdf")
pdf_desktop_hw = Path("C:/Users/offic/Desktop/Heartweb/jesse-walkthrough-memo.pdf")
pdf_desktop_main = Path("C:/Users/offic/Desktop/jesse-walkthrough-memo.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header
        self.drawString(54, 802, "Heartweb / Hardware Design | SEO-Workflow & Notion-Bridge")
        self.drawRightString(541, 802, "Technisches Briefing")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 794, 541, 794)
        # Footer
        self.line(54, 45, 541, 45)
        self.drawString(54, 34, "Autor: Raphael Rechberger | Vertraulich fuer Jesse Jensen")
        self.drawRightString(541, 34, f"Seite {self._pageNumber} von {page_count}")
        self.restoreState()

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=4
)

meta_style = ParagraphStyle(
    "DocMeta",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#475569"),
    spaceAfter=8
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
    spaceAfter=4
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.white
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#1e293b")
)

table_cell_bold = ParagraphStyle(
    "TableCellBold",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#0f172a")
)

def build_2page_pdf(filename):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    story = []

    # ==================== PAGE 1 ====================
    story.append(Paragraph("Technisches Briefing & Architektur-Bridge: Claude Desktop zu Notion", title_style))
    story.append(Paragraph("<b>Empfaenger:</b> Jesse Jensen &nbsp;|&nbsp; <b>Autor:</b> Raphael Rechberger &nbsp;|&nbsp; <b>Datum:</b> 16. August 2026<br/><b>GitHub:</b> https://github.com/Frater418/claude-desktop-seo-workflow-production", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    story.append(Paragraph("1. Ausgangslage & Skalierungs-Ziel", h2_style))
    story.append(Paragraph(
        "Heartweb befindet sich im entscheidenden Skalierungsschritt: Die Abloesung der bisherigen ad-hoc Steuerung "
        "ueber Slack durch ein vollstaendig automatisiertes Operations-System in Notion. "
        "Bisher existierte dein SEO-Workflow (Pillars, Cluster, 120-Tage-Roadmap, lokale Landingpages) als Aneinanderreihung "
        "von Prompts. Bei mehreren parallelen Kundenprojekten fuehrten manuelle Zwischenschritte (z.B. Ahrefs-Abtippen), "
        "fehlender Zustandsspeicher und unstrukturierte Chat-Outputs zu hohem Zeitaufwand und Kontextverlust.<br/>"
        "<b>Unser Ziel:</b> Wir haben das Rad nicht neu erfunden, sondern ein <b>deterministisches, datenbank-kompatibles Fundament</b> "
        "gebaut. Das System laeuft lokal in Claude Desktop, erzeugt aber von Haus aus standardisierte JSON- und YAML-Strukturen, "
        "die nahtlos in euer neues Notion-Setup einfliessen und spaeter per API/Webhook vollautomatisiert werden koennen.",
        body_style
    ))

    story.append(Paragraph("2. Systematischer Vergleich: Bisheriger Ablauf vs. Neuer Standard", h2_style))
    
    t_data = [
        [
            Paragraph("Workflow-Bereich", table_header_style),
            Paragraph("Bisheriger Stand (Manuelle Reibung)", table_header_style),
            Paragraph("Modernisierter Standard (Produktionsgewinn)", table_header_style)
        ],
        [
            Paragraph("<b>Projekt-Status</b>", table_cell_bold),
            Paragraph("Kontext musste aus Chat gesucht werden; Kontextverlust bei Neustarts.", table_cell_style),
            Paragraph("<b>manifest.json</b> als maschinenlesbarer Single Source of Truth Status.", table_cell_style)
        ],
        [
            Paragraph("<b>Design & CI</b>", table_cell_bold),
            Paragraph("Design aus Schritt 1c ging verloren; CSS in Schritt 4 neu erraten.", table_cell_style),
            Paragraph("<b>design-system.css</b> persistiert Farb- und Typo-Tokens fuer alle HTML-Pages.", table_cell_style)
        ],
        [
            Paragraph("<b>Keyword-Check</b>", table_cell_bold),
            Paragraph("45-60 Min. pro Pillar: Keywords einzeln in Ahrefs pruefen und abtippen.", table_cell_style),
            Paragraph("<b>AgentSEO MCP</b> liefert verifizierte SV/KD-Daten vollautomatisch per API (2 Min.).", table_cell_style)
        ],
        [
            Paragraph("<b>120-Tage-Plan</b>", table_cell_bold),
            Paragraph("LLM verrechnet sich bei 17 Wochen mit variierenden Stundensummen.", table_cell_style),
            Paragraph("<b>Python Solver</b> garantiert exakt 10-15h/Woche und 100% lokale Pflichtseiten.", table_cell_style)
        ],
        [
            Paragraph("<b>Tagesgeschaeft (4)</b>", table_cell_bold),
            Paragraph("Schritt 4 ueberladen (Briefing, Schema und HTML brachen oft ab).", table_cell_style),
            Paragraph("<b>Trennung in 4a (Texter-Briefing) & 4b (HTML)</b> inkl. Notion-Frontmatter.", table_cell_style)
        ],
        [
            Paragraph("<b>Qualitaets-Doktrin</b>", table_cell_bold),
            Paragraph("Keine formalen Zwischenstopps oder Qualitaets-Gates.", table_cell_style),
            Paragraph("<b>7 verbindliche Quality Gates</b> & striktes Fail-Fast ohne Schaetzdaten.", table_cell_style)
        ]
    ]

    t = Table(t_data, colWidths=[85, 195, 207])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Die 6 technischen Hebel im Detail (Teil 1)", h2_style))
    story.append(Paragraph("<b>Hebel 1: Zentrales Projekt-Manifest (manifest.json):</b> Definiert das Datenmodell fuer Kunden-Metadaten, Zielgruppen, Status und Pfade. Validiert strikt gegen JSON Schema Draft 2020-12 und bildet 1:1 die Struktur eurer kuenftigen Notion-Projektdatenbank ab.", body_style))
    story.append(Paragraph("<b>Hebel 2: Persistentes Design-System (design-system.css):</b> Verhindert CSS-Drift. Die Farben, Typografien und Card-Stile werden einmalig in Schritt 1c extrahiert und stehen allen Folgeschritten verbindlich zur Verfuegung.", body_style))
    story.append(Paragraph("<b>Hebel 3: Automatisierte Keyword-Anreicherung (AgentSEO MCP):</b> Claude Desktop ruft direkt die REST-API ueber den MCP-Server auf. Bis zu 100 Keywords werden in Sekunden verifiziert.", body_style))

    # Force Page Break to ensure EXACT 2 pages
    story.append(PageBreak())

    # ==================== PAGE 2 ====================
    story.append(Paragraph("3. Die 6 technischen Hebel im Detail (Teil 2)", h2_style))
    story.append(Paragraph("<b>Hebel 4: Deterministischer 120-Tage-Solver (capacity_matrix_solver.py):</b> Loest das kombinatorische Problem mathematisch fehlerfrei. Alle 17 Wochen halten exakt das Budget von 10-15 Stunden ein. Lokale Pflicht-Landingpages werden garantiert in Phase 1 und 2 platziert.", body_style))
    story.append(Paragraph("<b>Hebel 5: Modulare Trennung in 4a (Briefing) und 4b (HTML):</b> Schritt 4a erzeugt ein reines redaktionelles Briefing mit standardisiertem YAML-Frontmatter (Pillar, Keyword, Suchvolumen, Prioritaet, Status) fuer eure Copywriter (Regina, Katja, Alexander). Schritt 4b erzeugt autarken HTML-Code fuer Web-Entwickler.", body_style))
    story.append(Paragraph("<b>Hebel 6: Strikte Fail-Fast- und Qualitaets-Doktrin:</b> Keine stillschweigenden Fallbacks oder Schaetzdaten. Bei fehlendem Key oder unvollstaendigen Daten stoppt der Prozess mit einem strukturierten Fehlercode.", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("4. Zukuenftige Automations-Roadmap (Notion- & n8n-Pipeline)", h2_style))
    story.append(Paragraph(
        "Da die erzeugten Briefings und Roadmaps bereits standardisierte Metadaten tragen, laesst sich die Pipeline in zwei Schritten vollautomatisieren:<br/>"
        "&bull; <b>Stufe 1 (Direkter MCP-Push):</b> Einbindung des offiziellen Notion-MCP-Servers in Claude Desktop. Roadmaps und Briefings werden per Tool-Call direkt als Datenbank-Eintraege angelegt.<br/>"
        "&bull; <b>Stufe 2 (Event-Driven n8n-Pipeline):</b> Ein n8n-Workflow ueberwacht den Output-Ordner oder das Git-Repo, liest das YAML-Frontmatter aus, erstellt die Notion-Karten und weist diese per Auto-Tagging an Regina, Katja oder Alexander zu inklusive Slack-Notification.",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("5. Rollenverteilung in der operativen Praxis", h2_style))
    story.append(Paragraph("<b>Fuer Jesse & Raphael (Strategie & Rollout):</b> Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige 120-Tage-Roadmap fuer Notion.", body_style))
    story.append(Paragraph("<b>Fuer die Copywriter (Regina, Katja, Alexander):</b> Erhalten aus 4a saubere Briefings mit Suchintention, Gliederung, FAQs und Verlinkungsvorgaben ohne stoerenden HTML-Code.", body_style))
    story.append(Paragraph("<b>Fuer die Web-Entwicklung / WordPress:</b> Erhaelt aus 1b den visuellen Menuebaum (HTML) und aus 4b direkt einsatzbereite Landingpages.", body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("6. Gespraechspunkte fuer unseren Call", h2_style))
    story.append(Paragraph(
        "&bull; <b>Live-Walkthrough:</b> Kurzer Blick auf das oeffentliche GitHub-Repository und die README-Landkarte.<br/>"
        "&bull; <b>Notion-Abgleich:</b> Abstimmung der Frontmatter-Felder mit der Datenbankstruktur eurer Agentur.<br/>"
        "&bull; <b>Pilot-Projekt:</b> Zuweisung des ersten Kunden-Cases (z.B. simCura) fuer den initialen Live-Durchlauf.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully: {filename}")

build_2page_pdf(pdf_canonical)
build_2page_pdf(pdf_desktop_hw)
build_2page_pdf(pdf_desktop_main)

reader = pypdf.PdfReader(str(pdf_desktop_hw))
print(f"VERIFIED PAGE COUNT: {len(reader.pages)}")
