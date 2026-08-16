import os
import pypdf
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas
import pypdfium2 as pdfium

pdf_canonical = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/docs/jesse-walkthrough-memo.pdf")
pdf_desktop_hw = Path("C:/Users/offic/Desktop/Heartweb/jesse-walkthrough-memo.pdf")
pdf_desktop_main = Path("C:/Users/offic/Desktop/jesse-walkthrough-memo.pdf")

class HeartwebCanvas(canvas.Canvas):
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
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(colors.HexColor("#0f172a"))
        self.drawString(48, 804, "HEARTWEB")
        
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(110, 804, "|   SEO-Workflow Modernisierung & Notion-Bridge")
        self.drawRightString(547, 804, "Executive Implementation Memo")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(48, 796, 547, 796)
        
        # Footer
        self.line(48, 44, 547, 44)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(48, 32, "Autor: Raphael Rechberger   |   Vertraulich fuer Jesse Jensen   |   Repo: Frater418/claude-desktop-seo-workflow-production")
        self.drawRightString(547, 32, f"Seite {self._pageNumber} von {page_count}")
        self.restoreState()

styles = getSampleStyleSheet()

doc_title = ParagraphStyle(
    "DocTitle",
    fontName="Helvetica-Bold",
    fontSize=15.5,
    leading=19.5,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=4
)

meta_box_style = ParagraphStyle(
    "MetaBox",
    fontName="Helvetica",
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#334155")
)

h1_section = ParagraphStyle(
    "H1Section",
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=14.5,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=8,
    spaceAfter=4
)

body_text = ParagraphStyle(
    "BodyTextCustom",
    fontName="Helvetica",
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#334155"),
    spaceAfter=5
)

bullet_text = ParagraphStyle(
    "BulletTextCustom",
    parent=body_text,
    leftIndent=10,
    spaceAfter=3
)

callout_text = ParagraphStyle(
    "CalloutText",
    fontName="Helvetica",
    fontSize=8,
    leading=11.5,
    textColor=colors.HexColor("#1e293b")
)

tbl_header = ParagraphStyle(
    "TblHeader",
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=colors.white
)

tbl_cell = ParagraphStyle(
    "TblCell",
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#334155")
)

tbl_cell_bold = ParagraphStyle(
    "TblCellBold",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=10,
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
    story.append(Paragraph("Implementierungs-Memo: Claude Desktop SEO-Workflow & Notion-Bridge", doc_title))
    
    meta_html = (
        "<b>Empfaenger:</b> Jesse Jensen &nbsp;|&nbsp; "
        "<b>Architektur & Autor:</b> Raphael Rechberger &nbsp;|&nbsp; "
        "<b>Datum:</b> 16. August 2026<br/>"
        "<b>Status:</b> Vollstaendig implementiert & auf GitHub veroeffentlicht &nbsp;|&nbsp; "
        "<b>GitHub Repo:</b> https://github.com/Frater418/claude-desktop-seo-workflow-production"
    )
    meta_table = Table([[Paragraph(meta_html, meta_box_style)]], colWidths=[499])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))

    # 1. Was heute gebaut wurde
    story.append(Paragraph("1. Was heute gebaut wurde (Aufbauend auf dem Review-PDF)", h1_section))
    p1_text = (
        "Aufbauend auf meiner Review-Analyse habe ich den gesamten Workflow heute vollstaendig umgesetzt und in ein "
        "modulares, versioniertes Produktionsprojekt ueberfuehrt. Saemtliche in der Review identifizierten Reibungspunkte "
        "wurden geloest: Alle 9 Workflow-Prompts sind refactored, die Datenvertraege stehen und das System ist 1:1 fuer die "
        "Uebernahme in euer anstehendes Notion-Setup vorbereitet."
    )
    story.append(Paragraph(p1_text, body_text))
    story.append(Spacer(1, 3))

    # 2. Vergleichstabelle
    story.append(Paragraph("2. Status-Abgleich: Review-Empfehlung vs. Heutige Implementierung", h1_section))
    
    t_data = [
        [
            Paragraph("Review-Empfehlung", tbl_header),
            Paragraph("Bisheriger Reibungspunkt", tbl_header),
            Paragraph("Heutiger Produktions-Stand (Im GitHub-Repo)", tbl_header)
        ],
        [
            Paragraph("<b>manifest.json</b>", tbl_cell_bold),
            Paragraph("Kontext musste im Chat gesucht werden; Verlust bei neuen Sessions.", tbl_cell),
            Paragraph("JSON Schema Draft 2020-12 Standard. Speichert Mandantenstatus & Pfade.", tbl_cell)
        ],
        [
            Paragraph("<b>design-system.css</b>", tbl_cell_bold),
            Paragraph("Screenshot aus 1c ging verloren; CSS in Schritt 4 neu erraten.", tbl_cell),
            Paragraph("Persistiert Farb-, Typo- und Button-Tokens zentral ab Schritt 1c.", tbl_cell)
        ],
        [
            Paragraph("<b>AgentSEO MCP</b>", tbl_cell_bold),
            Paragraph("45-60 Min. pro Pillar: Keywords einzeln in Ahrefs pruefen.", tbl_cell),
            Paragraph("Tool-Call zieht Suchvolumen, KD und CPC vollautomatisch in 2 Min.", tbl_cell)
        ],
        [
            Paragraph("<b>Kapazitaets-Solver</b>", tbl_cell_bold),
            Paragraph("LLMs verrechnen sich bei 17 Wochen mit variierenden Stundensummen.", tbl_cell),
            Paragraph("Python Solver v1.2 berechnet exakt 10-15h/Woche & Verlinkungs-Maps.", tbl_cell)
        ],
        [
            Paragraph("<b>Zweiteilung Schritt 4</b>", tbl_cell_bold),
            Paragraph("Schritt 4 ueberladen (Briefing, Schema und HTML brachen ab).", tbl_cell),
            Paragraph("Getrennt: 4a fuer Texter (Notion-Frontmatter) & 4b fuer Web-Entwicklung.", tbl_cell)
        ],
        [
            Paragraph("<b>Qualitaets-Doktrin</b>", tbl_cell_bold),
            Paragraph("Ungepruefte Schaetzungen fuehrten zu Daten-Drift.", tbl_cell),
            Paragraph("7 Quality Gates & striktes Fail-Fast ohne stillschweigende Fallbacks.", tbl_cell)
        ]
    ]

    t = Table(t_data, colWidths=[90, 200, 209])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
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

    # 3. Kern-Bausteine Teil 1
    story.append(Paragraph("3. Die 6 umgesetzten Kern-Bausteine im Detail (Teil 1)", h1_section))
    story.append(Paragraph("<b>1. Persistentes Projekt-Manifest (manifest.json):</b> Initialisiert in Schritt 0. Enthaelt Domain, Zielgruppe, Geschaeftsziele, Phasenstatus und alle Dateipfade. Dient als Single Source of Truth und bildet 1:1 die Struktur eurer kuenftigen Notion-Mandantendatenbank ab.", body_text))
    story.append(Paragraph("<b>2. Persistentes Design-System (design-system.css):</b> In Schritt 1c werden alle visuellen Tokens einmalig extrahiert. Alle Folgeschritte (Pillar-Templates und Landingpages) binden identische CSS-Klassen ein. Visuelle Konsistenz ist garantiert.", body_text))
    story.append(Paragraph("<b>3. Automatisierte Keyword-Anreicherung via AgentSEO MCP:</b> Schritt 2 bindet den AgentSEO-Server an. Bis zu 100 Keywords pro Pillar werden per API verifiziert. Lokale Pflicht-Landingpages werden fuer die Gebietsabdeckung gesondert markiert.", body_text))

    # ==================== PAGE BREAK ====================
    story.append(PageBreak())

    # ==================== SEITE 2 ====================
    story.append(Paragraph("3. Die 6 umgesetzten Kern-Bausteine im Detail (Teil 2)", h1_section))
    story.append(Paragraph("<b>4. Deterministischer Kapazitaets-Solver (capacity_matrix_solver.py):</b> Mathematisches Python-Skript fuer den 120-Tage-Plan. Jede der 17 Wochen haelt exakt das Budget von 10-15 Stunden ein. Lokale Pflichtseiten landen garantiert in Phase 1 und 2. Generiert zusaetzlich die zweidimensionale Verlinkungs-Map (vertikal + horizontal).", body_text))
    story.append(Paragraph("<b>5. Modulare Aufteilung in 4a (Briefing) und 4b (HTML):</b> Schritt 4a fuehrt den Live-SERP-Check durch, generiert Schema.org JSON-LD und liefert saubere Briefings mit standardisiertem YAML-Frontmatter fuer Regina, Katja und Alexander. Schritt 4b erzeugt autarken HTML-Code fuer Web-Entwickler.", body_text))
    story.append(Paragraph("<b>6. Strikte Fail-Fast- und Qualitaets-Doktrin:</b> Keine stillschweigenden Fallbacks oder Schaetzdaten. Bei fehlendem Key oder unvollstaendigen Daten stoppt der Prozess mit einer expliziten Fehlermeldung.", body_text))
    story.append(Spacer(1, 4))

    # 4. Notion Pipeline
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
        ("PADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(n_table)
    story.append(Spacer(1, 4))

    # 5. Rollenverteilung
    story.append(Paragraph("5. Rollenverteilung in der operativen Praxis", h1_section))
    story.append(Paragraph("&bull; <b>Fuer Jesse & Raphael (Strategie & Rollout):</b> Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige 120-Tage-Roadmap fuer Notion.", bullet_text))
    story.append(Paragraph("&bull; <b>Fuer die Copywriter (Regina, Katja, Alexander):</b> Erhalten aus 4a glasklare Briefings mit Suchintention, Gliederung, FAQs und Verlinkungsvorgaben ohne stoerenden HTML-Code.", bullet_text))
    story.append(Paragraph("&bull; <b>Fuer die Web-Entwicklung / WordPress:</b> Erhaelt aus 1b den Menuebaum (HTML) und aus 4b direkt einsatzbereite Landingpages mit integriertem Schema.org Markup.", bullet_text))
    story.append(Spacer(1, 4))

    # 6. Gespraechspunkte
    story.append(Paragraph("6. Gespraechspunkte fuer unseren Call", h1_section))
    story.append(Paragraph("&bull; <b>Live-Walkthrough:</b> Kurzer Blick auf das GitHub-Repo und die interaktive README-Landkarte.<br/>"
                           "&bull; <b>Notion-Abgleich:</b> Abstimmung der Frontmatter-Properties mit der Datenbankstruktur eurer Agentur.<br/>"
                           "&bull; <b>Pilot-Projekt:</b> Zuweisung des ersten Kunden-Cases (z.B. simCura) fuer den initialen Live-Durchlauf.", body_text))
    story.append(Spacer(1, 4))

    # Signatur
    sig_text = "<b>Raphael Rechberger</b><br/><font color='#64748b'>Technical Operations & AI Integration Architect</font>"
    story.append(Paragraph(sig_text, body_text))

    doc.build(story, canvasmaker=HeartwebCanvas)
    print(f"PDF built successfully: {filename}")

build_pdf(pdf_canonical)
build_pdf(pdf_desktop_hw)
build_pdf(pdf_desktop_main)

reader = pypdf.PdfReader(str(pdf_desktop_hw))
print(f"VERIFIED EXACT PAGE COUNT: {len(reader.pages)}")
