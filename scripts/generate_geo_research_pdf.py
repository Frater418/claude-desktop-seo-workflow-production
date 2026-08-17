"""
Executive GEO 2026 Research & Copywriter Guidelines PDF Generator
Autor: Raphael Rechberger
Projekt: Heartweb Claude Desktop SEO Workflow
"""

import os
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas
import pypdf

pdf_canonical = Path("C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow/docs/07-geo-research-und-copywriter-guidelines.pdf")
pdf_desktop_hw = Path("C:/Users/offic/Desktop/Heartweb/GEO_2026_Research_und_Copywriter_Guidelines.pdf")

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
        self.drawString(108, 804, "|   Generative Engine Optimization (GEO) 2026 & Copywriter Guidelines")
        self.drawRightString(547, 804, "Executive Research Memo")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(48, 796, 547, 796)
        
        # Footer
        self.line(48, 44, 547, 44)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(48, 32, "Autor: Raphael Rechberger   |   Vertraulich fuer Jesse Jensen   |   Heartweb AI Operations")
        self.drawRightString(547, 32, f"Seite {self._pageNumber} von {page_count}")
        self.restoreState()

styles = getSampleStyleSheet()

doc_title = ParagraphStyle(
    "DocTitle",
    fontName="Helvetica-Bold",
    fontSize=14.0,
    leading=17.5,
    textColor=colors.HexColor("#0f172a"),
    spaceAfter=4
)

meta_box_style = ParagraphStyle(
    "MetaBox",
    fontName="Helvetica",
    fontSize=8.0,
    leading=11.5,
    textColor=colors.HexColor("#334155")
)

h1_section = ParagraphStyle(
    "H1Section",
    fontName="Helvetica-Bold",
    fontSize=10.0,
    leading=13.5,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=7,
    spaceAfter=3
)

body_text = ParagraphStyle(
    "BodyTextCustom",
    fontName="Helvetica",
    fontSize=8.0,
    leading=11.2,
    textColor=colors.HexColor("#334155"),
    spaceAfter=3.5
)

bullet_text = ParagraphStyle(
    "BulletTextCustom",
    parent=body_text,
    leftIndent=10,
    spaceAfter=3
)

callout_text = ParagraphStyle(
    "CalloutText",
    fontName="Helvetica-Oblique",
    fontSize=8.0,
    leading=11.5,
    textColor=colors.HexColor("#1e293b")
)

tbl_cell_bold = ParagraphStyle(
    "TblCellBold",
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9.5,
    textColor=colors.HexColor("#0f172a")
)

tbl_cell = ParagraphStyle(
    "TblCell",
    fontName="Helvetica",
    fontSize=7.5,
    leading=9.5,
    textColor=colors.HexColor("#334155")
)

def build_pdf():
    story = []

    # --- PAGE 1: RESEARCH DIGEST & EVOLUTION ---
    story.append(Paragraph("GEO 2026: Generative Engine Optimization & LLM-Zitations-Architektur", doc_title))

    meta_html = "<b>Status:</b> Produktionsstandard v1.4.0 &nbsp;|&nbsp; <b>Autor:</b> Raphael Rechberger &nbsp;|&nbsp; <b>Kontext:</b> Heartweb / Jesse Jensen &nbsp;|&nbsp; <b>Datum:</b> 17. August 2026<br/><b>Forschungs-Evidenz:</b> Ahrefs (863k Keywords, 4M URLs), Zhang et al. (arXiv:2604.25707), Google Information Gain Patent, Princeton GEO Study"
    meta_table = Table([[Paragraph(meta_html, meta_box_style)]], colWidths=[499])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Der Paradigmenwechsel: Klassisches SEO vs. GEO 2026", h1_section))
    story.append(Paragraph("Waehrend klassisches SEO primaer auf Klick-Rankings in den 10 blauen Links optimiert, ermitteln Google AI Overviews (Gemini 3), Perplexity, Claude und ChatGPT Search ihre Antworten durch Retrieval-Augmented Generation (RAG). Wer in KI-Antworten zitiert werden will, muss Text nicht laenger fuer Keyword-Dichte schreiben, sondern als <b>maschinenlesbare, extrahierbare Fakten-Container</b> aufbauen.", body_text))

    # Evidenz-Tabelle
    tbl_data = [
        [Paragraph("GEO-Faktor 2026", tbl_cell_bold), Paragraph("Empirische Evidenz (Q1/Q2 2026)", tbl_cell_bold), Paragraph("Architektonische Konsequenz fuer Heartweb", tbl_cell_bold)],
        [Paragraph("<b>Top-10 Entkopplung</b>", tbl_cell), Paragraph("Ahrefs (Maerz 2026): Nur noch <b>38% der AIO-Zitationen</b> stammen aus den Top-10. 62% kommen aus Position 11-100+.", tbl_cell), Paragraph("Reines Keyword-Ranking garantiert keine KI-Sichtbarkeit. Passagen-Struktur entscheidet.", tbl_cell)],
        [Paragraph("<b>2-Stufen-RAG</b><br/>(Selection vs. Absorption)", tbl_cell), Paragraph("Zhang et al. (2026): Stufe 1 filtert nach Relevanz; Stufe 2 (LLM) absorbiert nur Passagen mit harten Fakten & Tabellen.", tbl_cell), Paragraph("Jeder H2-Block wird als modularer <b>Evidence Container (130-160 Woerter)</b> formatiert.", tbl_cell)],
        [Paragraph("<b>Google Query Fan-Out</b>", tbl_cell), Paragraph("Gemini 3 zerlegt Nutzeranfragen in 3 bis 6 parallele Sub-Queries (Kosten, Dauer, Prozess, Kriterien).", tbl_cell), Paragraph("Content-Briefings muessen die 4 wahrscheinlichsten Sub-Queries in geschlossenen Absaetzen abdecken.", tbl_cell)],
        [Paragraph("<b>Schema.org & Entity-Graph</b>", tbl_cell), Paragraph("DigitalApplied (2026): Schema-Markup liefert <b>2,3x Zitations-Lift</b>; 15+ Entitaeten steigern Chance um <b>4,8x</b>.", tbl_cell), Paragraph("Vollstaendiger Schema.org `@graph` mit Wikidata-URIs (`about` vs. `mentions`) in Schritt 4a/4b.", tbl_cell)],
        [Paragraph("<b>Information Gain</b>", tbl_cell), Paragraph("Google Patent US20200349181A1: Mengendifferenz zum SERP-Konsens. Rewriting erhaelt Score 0.", tbl_cell), Paragraph("Eigene Daten, Preisspannen, Checklisten und Vergleichstabellen sind Pflichtbestandteil.", tbl_cell)]
    ]
    t_evidence = Table(tbl_data, colWidths=[95, 210, 194])
    t_evidence.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_evidence)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Die 3 Saeulen der Zitations-Optimierung fuer KI-Suchmaschinen", h1_section))
    story.append(Paragraph("<b>1. Direktheit (Instant Passage Lift):</b> Sofortige, unmissverstaendliche Beantwortung der Kernfrage in den ersten 50 bis 70 Woertern der Hero Section und unter jeder H2.<br/>"
                           "<b>2. Information Gain (Beweis-Dichte):</b> Integration echter Zahlen, Fristen, Paragrafen und Vergleichstabellen statt generischem Marketing-Sprech.<br/>"
                           "<b>3. Semantische Maschinenlesbarkeit:</b> Eindeutige Verknuepfung von Konzepten mit Wikidata-URIs, damit Gemini und Claudebot Entitaeten exakt zuordnen.", body_text))

    story.append(PageBreak())

    # --- PAGE 2: OPERATIONAL GUIDELINES FOR TEAM & COPYWRITERS ---
    story.append(Paragraph("Operative Umsetzung & Copywriter-Richtlinien (Regina, Katja, Alexander)", doc_title))

    callout_html = "<b>Die goldene Redaktionsregel fuer KI-Sichtbarkeit:</b> Schreibe Absaetze nicht mehr als fliessende Erzaehlung, sondern als in sich geschlossene, zitierfaehige Fakten-Container. Wenn eine KI nur einen einzigen Absatz deiner Seite liest, muss dieser Absatz fuer sich alleine vollstaendig Sinn ergeben und einen konkreten Mehrwert liefern."
    callout_table = Table([[Paragraph(callout_html, callout_text)]], colWidths=[499])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#3b82f6")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Das neue Briefing-Format in Notion (Schritt 4a)", h1_section))
    story.append(Paragraph("Texter muessen keine technische SEO verstehen. Sie erhalten ueber Schritt 4a in Notion ein glasklares, modulares Raster mit 4 Pflichtbausteinen:", body_text))

    story.append(Paragraph("• <b>Hero Direct-Answer Block (50 bis 70 Woerter):</b> Direkt unter der H1 folgt eine praezise Definition ohne Einleitungsfloskeln. Satz 1 nennt das Thema und den Hauptnutzen. Satz 2 liefert die wichtigste Zahl/Voraussetzung.", bullet_text))
    story.append(Paragraph("• <b>Evidence Containers pro H2 (130 bis 160 Woerter):</b> Jeder H2-Abschnitt enthaelt mindestens einen harten Datenpunkt (Euro-Betrag, Pflegegrad, Bearbeitungszeitraum, Gesetzestext) oder schliesst mit einer Mini-Tabelle / Aufzaehlung ab.", bullet_text))
    story.append(Paragraph("• <b>Semantic Triples Checkliste (15 bis 20 Relationen):</b> Vorgegebene Subjekt-Praedikat-Objekt Kombinationen (z.B. <i>[Ambulante Pflege] -> [entlastet] -> [pflegende Angehoerige]</i>), die natuerlich in den Text eingewoben werden.", bullet_text))
    story.append(Paragraph("• <b>Definitive Sprache:</b> Verwendung klarer Behauptungssaetze ('Pflegegrad 2 gewaehrt 332 Euro Pflegegeld') statt vorsichtiger Floskeln ('Manche Quellen berichten, dass es eventuell Zuschuesse gibt').", bullet_text))

    story.append(Paragraph("2. Technische Workflow-Erweiterungen (Vollautomatisch im Hintergrund)", h1_section))

    tbl_tech = [
        [Paragraph("Komponente", tbl_cell_bold), Paragraph("Erweiterung v1.4.0", tbl_cell_bold), Paragraph("Nutzen & Ziel-Engine", tbl_cell_bold)],
        [Paragraph("<b>Manifest Schema</b>", tbl_cell), Paragraph("`geo_targets` (AIO, Perplexity, Claude) & `entities` (Wikidata URIs).", tbl_cell), Paragraph("Verhindert Halluzinationen und verankert die Marke im Google Knowledge Graph.", tbl_cell)],
        [Paragraph("<b>Solver v1.3.0</b>", tbl_cell), Paragraph("Neue Content-Typen: Data-Hub (5h), Entity-Anchor (4h), Comparison-Table (2h), FAQ-Hub (3h).", tbl_cell), Paragraph("Plant gezielt zitierfaehige Daten-Hubs in den 120-Tage-Roadmaps ein.", tbl_cell)],
        [Paragraph("<b>Schema Validator</b>", tbl_cell), Paragraph("CLI mit `--strict` Pruefung fuer `@graph` JSON-LD mit `about` (Wikidata) & `mentions`.", tbl_cell), Paragraph("Sichert 100% Google Rich Results & RAG-Kompatibilitaet vor Veröffentlichung.", tbl_cell)],
        [Paragraph("<b>Design-System</b>", tbl_cell), Paragraph("`.definition-block`, `.evidence-container`, `.comparison-table`, `data-speakable`.", tbl_cell), Paragraph("Saubere visuelle und semantische Struktur fuer Web-Entwickler & CSS-Autarkie.", tbl_cell)]
    ]
    t_tech = Table(tbl_tech, colWidths=[90, 205, 204])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 6))

    story.append(Paragraph("3. Naechste Schritte fuer die Heartweb-Produktion", h1_section))
    story.append(Paragraph("1. <b>Pilot-Lauf mit Kundenbriefings:</b> Durchlauf der Schritte 0 bis 3 fuer die 2 neuen Kundenprojekte von Jesse.<br/>"
                           "2. <b>Agency-Abstimmung (Meeting mit Max):</b> Vorstellung der Notion-Datenbank-Felder fuer die automatisierte Task-Zuweisung.<br/>"
                           "3. <b>Team-Onboarding:</b> Uebergabe dieser 2-Seiten-Guidelines an Regina, Katja und Alexander als verbindlicher Qualitaetsstandard.", body_text))

    pdf_canonical.parent.mkdir(parents=True, exist_ok=True)
    pdf_desktop_hw.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(pdf_canonical),
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=48,
        bottomMargin=48
    )

    doc.build(story, canvasmaker=HeartwebCanvas)

    # Copy to desktop
    shutil.copyfile(pdf_canonical, pdf_desktop_hw)

    reader = pypdf.PdfReader(str(pdf_canonical))
    print(f"SUCCESS: Generated {len(reader.pages)}-page PDF at:")
    print(f"  - Canonical: {pdf_canonical}")
    print(f"  - Desktop:   {pdf_desktop_hw}")

if __name__ == "__main__":
    build_pdf()
