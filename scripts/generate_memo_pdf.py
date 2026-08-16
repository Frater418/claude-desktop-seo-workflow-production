import os
import pypdf
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
from reportlab.pdfgen import canvas

pdf_canonical = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/docs/jesse-walkthrough-memo.pdf")
pdf_desktop_hw = Path("C:/Users/offic/Desktop/Heartweb/jesse-walkthrough-memo.pdf")
pdf_desktop_main = Path("C:/Users/offic/Desktop/jesse-walkthrough-memo.pdf")

class ProfessionalNumberedCanvas(canvas.Canvas):
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
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0f172a"))
        self.drawString(48, 804, "HEARTWEB / HARDWARE DESIGN")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(200, 804, "|  SEO-Workflow Architektur & Notion-Bridge")
        self.drawRightString(547, 804, "Executive Technical Memo")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(48, 796, 547, 796)
        
        # Footer
        self.line(48, 44, 547, 44)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(48, 32, "Autor: Raphael Rechberger  |  Vertraulich fuer Jesse Jensen  |  Repo: Frater418/claude-desktop-seo-workflow-production")
        self.drawRightString(547, 32, f"Seite {self._pageNumber} von {page_count}")
        self.restoreState()

styles = getSampleStyleSheet()

doc_title = ParagraphStyle(
    "DocTitle",
    fontName="Helvetica-Bold",
    fontSize=16,
    leading=20,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=4
)

meta_box_style = ParagraphStyle(
    "MetaBox",
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#475569")
)

h1_section = ParagraphStyle(
    "H1Section",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=10,
    spaceAfter=5
)

body_text = ParagraphStyle(
    "BodyTextCustom",
    fontName="Helvetica",
    fontSize=9,
    leading=13.5,
    textColor=colors.HexColor("#334155"),
    spaceAfter=6
)

bullet_text = ParagraphStyle(
    "BulletTextCustom",
    parent=body_text,
    leftIndent=12,
    spaceAfter=3
)

callout_text = ParagraphStyle(
    "CalloutText",
    fontName="Helvetica",
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#1e293b")
)

tbl_header = ParagraphStyle(
    "TblHeader",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=colors.white
)

tbl_cell = ParagraphStyle(
    "TblCell",
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#334155")
)

tbl_cell_bold = ParagraphStyle(
    "TblCellBold",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#0f172a")
)

def build_pdf(filename):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=54,
        bottomMargin=54
    )

    story = []

    # ==================== SEITE 1 ====================
    story.append(Paragraph("Technisches Briefing: Claude Desktop zu Notion Pipeline", doc_title))
    
    # Meta Block als Box
    meta_html = (
        "<b>Empfaenger:</b> Jesse Jensen &nbsp;|&nbsp; "
        "<b>Architektur & Autor:</b> Raphael Rechberger &nbsp;|&nbsp; "
        "<b>Datum:</b> 16. August 2026<br/>"
        "<b>GitHub Repository:</b> https://github.com/Frater418/claude-desktop-seo-workflow-production"
    )
    meta_table = Table([[Paragraph(meta_html, meta_box_style)]], colWidths=[499])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # 1. Ausgangslage
    story.append(Paragraph("1. Ausgangslage & Skalierungs-Ziel", h1_section))
    p1_text = (
        "Heartweb vollzieht aktuell den entscheidenden Skalierungsschritt: Die Abloesung der bisherigen ad-hoc Zuteilung "
        "ueber Slack durch eine strukturierte, automatisierte Operations-Zentrale in Notion.<br/>"
        "Bisher lief der operative SEO-Workflow (Pillars, Cluster, 120-Tage-Planung, lokale Landingpages) als Aneinanderreihung "
        "von Chat-Prompts. Bei mehreren parallelen Mandanten fuehrte das zu spuerbarer Reibung: 45 bis 60 Minuten manuelle "
        "Ahrefs-Klickarbeit pro Pillar, Kontextverlust bei neuen Sessions und unstrukturierte Chat-Outputs.<br/>"
        "<b>Was wir umgesetzt haben:</b> Wir haben deine bewaehrte Strategie 1:1 beibehalten, aber ein <b>deterministisches, "
        "datenbank-kompatibles Fundament</b> darum gebaut. Der Workflow laeuft lokal in Claude Desktop, erzeugt aber von Haus aus "
        "maschinenlesbare JSON/YAML-Payloads, die nahtlos in euer Notion-Setup einfliessen und spaeter per API vollautomatisiert werden koennen."
    )
    story.append(Paragraph(p1_text, body_text))
    story.append(Spacer(1, 4))

    # 2. Systematischer Vergleich (Tabelle)
    story.append(Paragraph("2. Systematischer Vergleich: Bisheriger Ablauf vs. Neuer Standard", h1_section))
    
    t_data = [
        [
            Paragraph("Workflow-Bereich", tbl_header),
            Paragraph("Bisheriger Stand (Manuelle Reibung)", tbl_header),
            Paragraph("Modernisierter Produktions-Standard", tbl_header)
        ],
        [
            Paragraph("<b>Projekt-Status</b>", tbl_cell_bold),
            Paragraph("Kontext musste im Chat gesucht werden; Verlust bei neuen Sessions.", tbl_cell),
            Paragraph("<b>manifest.json</b> als maschinenlesbarer Single Source of Truth Zustand.", tbl_cell)
        ],
        [
            Paragraph("<b>Design & CI</b>", tbl_cell_bold),
            Paragraph("Screenshot aus 1c ging verloren; CSS in Schritt 4 neu erraten.", tbl_cell),
            Paragraph("<b>design-system.css</b> sichert visuelle Tokens fuer alle Folgeschritte.", tbl_cell)
        ],
        [
            Paragraph("<b>Keyword-Check</b>", tbl_cell_bold),
            Paragraph("45-60 Min. pro Pillar: 25-40 Zeilen manuell in Ahrefs abtippen.", tbl_cell),
            Paragraph("<b>AgentSEO MCP</b> liefert verifizierte SV/KD-Daten per API (2 Min.).", tbl_cell)
        ],
        [
            Paragraph("<b>120-Tage-Plan</b>", tbl_cell_bold),
            Paragraph("LLMs verrechnen sich bei 17 Wochen mit variierenden Stundensummen.", tbl_cell),
            Paragraph("<b>Python Solver</b> garantiert exakt 10-15h/Woche & 100% Pflichtseiten.", tbl_cell)
        ],
        [
            Paragraph("<b>Tagesgeschaeft (4)</b>", tbl_cell_bold),
            Paragraph("Schritt 4 ueberladen (Briefing, Schema und HTML gleichzeitig).", tbl_cell),
            Paragraph("<b>Getrennt in 4a (Texter-Briefing) & 4b (HTML)</b> inkl. Notion-Frontmatter.", tbl_cell)
        ],
        [
            Paragraph("<b>Qualitaets-Doktrin</b>", tbl_cell_bold),
            Paragraph("Keine formalen Zwischenstopps oder Qualitaets-Gates.", tbl_cell),
            Paragraph("<b>7 verbindliche Quality Gates</b> & striktes Fail-Fast ohne Schaetzdaten.", tbl_cell)
        ]
    ]

    t = Table(t_data, colWidths=[85, 205, 209])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # 3. Erste 3 Hebel auf Seite 1
    story.append(Paragraph("3. Die technischen Kern-Hebel im Detail (Teil 1)", h1_section))
    story.append(Paragraph("<b>Hebel 1: Zentrales Projekt-Manifest (manifest.json)</b><br/>"
                           "Definiert das verbindliche Datenmodell fuer Kunden-Metadaten, Zielregionen, Phasenstatus und Dateipfade. "
                           "Validiert nach JSON Schema Draft 2020-12 und bildet 1:1 eure kuenftige Notion-Mandantendatenbank ab.", body_text))
    story.append(Paragraph("<b>Hebel 2: Persistentes Design-System (design-system.css)</b><br/>"
                           "Schluss mit erratenem CSS: Farbpalette, Typografie-Skala, Abstaende und Button-Stile werden in Schritt 1c "
                           "einmalig aus dem Website-Screenshot extrahiert und als globale CSS-Tokens fuer alle Landingpages gesichert.", body_text))
    story.append(Paragraph("<b>Hebel 3: Automatisierte Keyword-Anreicherung via AgentSEO MCP</b><br/>"
                           "Claude Desktop greift direkt auf den AgentSEO-Server zu. 25 bis 40 Seed-Keywords pro Pillar werden vollautomatisch "
                           "mit monatlichem Suchvolumen, Keyword Difficulty und CPC angereichert. Die CSV entsteht ohne manuelle Klicks.", body_text))

    # ==================== PAGE BREAK ====================
    story.append(PageBreak())

    # ==================== SEITE 2 ====================
    story.append(Paragraph("3. Die technischen Kern-Hebel im Detail (Teil 2)", h1_section))
    story.append(Paragraph("<b>Hebel 4: Deterministischer 120-Tage-Solver (capacity_matrix_solver.py)</b><br/>"
                           "Ein mathematisches Python-Skript loest die Stundenverteilung (10 bis 15 Stunden pro Woche) fehlerfrei. "
                           "Lokale Pflicht-Landingpages (z.B. Frankfurt Bornheim, Sachsenhausen etc.) werden unabhaengig vom Suchvolumen "
                           "zu 100% in Phase 1 und 2 verplant. Zudem wird eine zweidimensionale Verlinkungs-Map (vertikal + horizontal) erzeugt.", body_text))
    story.append(Paragraph("<b>Hebel 5: Modulare Trennung in 4a (Briefing) und 4b (HTML)</b><br/>"
                           "Schritt 4a fuehrt den Live-SERP-Check durch, generiert Schema.org JSON-LD und liefert ein sauberes Markdown-Briefing "
                           "mit standardisiertem YAML-Frontmatter (Pillar, Keyword, Suchvolumen, Prioritaet, Status) fuer Regina, Katja und Alexander. "
                           "Schritt 4b erzeugt ausschliesslich fuer Landingpages den autarken HTML-Code fuer Entwickler.", body_text))
    story.append(Paragraph("<b>Hebel 6: Strikte Fail-Fast- und Qualitaets-Doktrin</b><br/>"
                           "Im Produktivumfeld gibt es kein Herumraten oder stillschweigende Fallbacks. Fehlt ein API-Key, ein Pflichtfeld oder "
                           "sind Daten unvollstaendig, stoppt das System sofort mit einem praezisen Fehlercode.", body_text))
    story.append(Spacer(1, 4))

    # 4. Notion Roadmap
    story.append(Paragraph("4. Zukuenftige Automations-Roadmap (Notion- & n8n-Pipeline)", h1_section))
    
    n_box = (
        "<b>Stufe 1 (Direkter MCP-Push in Claude Desktop):</b> Sobald euer Notion-Setup live ist, binden wir den Notion-MCP-Server "
        "ein. Roadmaps (Schritt 3) und Briefings (Schritt 4a) werden per Tool-Call direkt als Datenbank-Karten angelegt.<br/>"
        "<b>Stufe 2 (Event-Driven n8n / Make Pipeline):</b> Ein n8n-Workflow ueberwacht den Output-Ordner oder das Git-Repo, "
        "parst das YAML-Frontmatter der Briefings, erstellt die Notion-Karten und weist diese per Auto-Tagging an Regina, Katja "
        "oder Alexander zu inklusive formatierter Slack-Benachrichtigung."
    )
    n_table = Table([[Paragraph(n_box, callout_text)]], colWidths=[499])
    n_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(n_table)
    story.append(Spacer(1, 4))

    # 5. Rollenverteilung
    story.append(Paragraph("5. Rollenverteilung in der operativen Praxis", h1_section))
    story.append(Paragraph("&bull; <b>Fuer Jesse & Raphael (Strategie & Rollout):</b> Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige, mathematisch gepruefte 120-Tage-Roadmap fuer Notion.", bullet_text))
    story.append(Paragraph("&bull; <b>Fuer die Copywriter (Regina, Katja, Alexander):</b> Erhalten aus 4a glasklare Briefings mit Suchintention, Gliederung, FAQs und Verlinkungsvorgaben ohne stoerenden HTML-Code.", bullet_text))
    story.append(Paragraph("&bull; <b>Fuer die Web-Entwicklung / WordPress:</b> Erhaelt aus 1b den Menuebaum (HTML) und aus 4b direkt einsatzbereite Landingpages mit integriertem Schema.org Markup.", bullet_text))
    story.append(Spacer(1, 4))

    # 6. Gespraechspunkte
    story.append(Paragraph("6. Gespraechspunkte fuer unseren Call", h1_section))
    story.append(Paragraph("&bull; <b>Live-Walkthrough:</b> Kurzer Blick auf das GitHub-Repo und die interaktive README-Landkarte.<br/>"
                           "&bull; <b>Notion-Abgleich:</b> Abstimmung der Frontmatter-Properties mit der Datenbankstruktur eurer Agentur.<br/>"
                           "&bull; <b>Pilot-Projekt:</b> Zuweisung des ersten Kunden-Cases (z.B. simCura) fuer den initialen Live-Durchlauf.", body_text))
    story.append(Spacer(1, 6))

    # Signatur
    sig_text = "<b>Raphael Rechberger</b><br/><font color='#64748b'>Technical Operations & AI Integration Architect</font>"
    story.append(Paragraph(sig_text, body_text))

    doc.build(story, canvasmaker=ProfessionalNumberedCanvas)
    print(f"PDF built successfully: {filename}")

build_pdf(pdf_canonical)
build_pdf(pdf_desktop_hw)
build_pdf(pdf_desktop_main)

reader = pypdf.PdfReader(str(pdf_desktop_hw))
print(f"VERIFIED EXACT PAGE COUNT: {len(reader.pages)}")
