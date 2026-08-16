# Dateinamen- und Output-Vertrag

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Version:** 1.0.0  
**Geltungsbereich:** Alle Kundenprojekte in Claude Desktop  

---

## 1. Uebersicht der Verzeichnisstruktur pro Kundenprojekt

Jedes Kundenprojekt besitzt im Workspace einen dedizierten Projektordner mit folgender Ordnerstruktur:

```text
kunden-projekt-name/
├── manifest.json                              # Zentraler maschinenlesbarer Projektstatus
├── standards/
│   └── design-system.css                      # Extrahierte CSS-Tokens aus Schritt 1c
├── inputs/                                    # Vom Kunden oder Nutzer bereitgestellte Rohdaten
│   ├── briefing.md                            # Kunden-Briefing aus Schritt 0 / 1
│   ├── website_screenshot.png                 # Full-Page Screenshot fuer Schritt 1c
│   └── performance_export.csv                 # GSC / Rank-Tracker Daten fuer Schritt 3b
├── outputs/                                   # Strukturierte Markdown- & Datendateien
│   ├── 1-pillar-themen.md                     # Pillar- und Themenarchitektur-Tabelle
│   ├── 1b-seitenarchitektur.md                # Informationsarchitektur & Navigationszuordnung
│   ├── 1b-menuestruktur.html                  # Visuelle, interaktive Menuebaum-Uebersicht
│   ├── 2-cluster-themen-agentseo.csv          # Vollstaendig verifizierte Keyword-Daten
│   ├── 3-plan.md                              # 120-Tage Content-Roadmap & Verlinkungs-Map
│   ├── 3b-performance-check.md                # Phasenanpassungs- und Performance-Report
│   ├── briefings/                             # Redaktionsfertige Content-Briefings (4a)
│   │   ├── briefing-[thema-slug].md
│   │   └── ...
│   └── html/                                  # Fertige HTML-Templates & Landingpages (1c & 4b)
│       ├── pillar-[pillar-slug].html
│       ├── landingpage-[thema-slug]-[ort-slug].html
│       └── ...
└── logs/
    └── validation_errors.log                  # Error-Logs bei Schema- oder Tool-Fehlern
```

---

## 2. Verbindlicher Schnittstellen- und Output-Vertrag

| Schritt | Prompt-Datei | Primaere Inputs | Verbindlicher Output (Pfad & Format) | Validierungs-Kriterium & Error-Verhalten |
|---|---|---|---|---|
| **0** | `0-kickoff.xml.md` | Nutzer-Briefing | `manifest.json` (JSON) | Manifest muss gegen `manifest.schema.json` validieren. Fehlen Pflichtfelder: Hard Error. |
| **1** | `1-pillar-identifikation.xml.md` | `manifest.json`, Web-Crawl | `outputs/1-pillar-themen.md` (Markdown) | Mindestens 3 bis 8 Pillar-Themen; pro Pillar 8 bis 15 Subthemen mit Status `zu recherchieren`. |
| **1b** | `1b-seitenarchitektur.xml.md` | `outputs/1-pillar-themen.md` | 1. `outputs/1b-seitenarchitektur.md`<br>2. `outputs/1b-menuestruktur.html` | Beide Dateien muessen inhaltlich 100% synchron sein. HTML muss eigenstaendig im Browser renderbar sein. |
| **1c** | `1c-pillar-template.xml.md` | `outputs/1b-seitenarchitektur.md`, `inputs/website_screenshot.png` | 1. `standards/design-system.css`<br>2. `outputs/html/pillar-[slug].html` | Fehlt der Screenshot: Sofortiger Abbruch mit `ERROR_SCREENSHOT_MISSING`. CSS-Tokens muessen vollstaendig sein. |
| **2** | `2-cluster-recherche.xml.md` | `outputs/1-pillar-themen.md`, AgentSEO Tool-Call | `outputs/2-cluster-themen-agentseo.csv` (CSV) | 25 bis 40 Keywords pro Pillar. Suchvolumen und KD muessen verifiziert sein. Bei API-Quota-Fehler: Stopp mit Error-Code. |
| **3** | `3-120-tage-plan.xml.md` | `outputs/2-cluster-themen-agentseo.csv`, `capacity_matrix_solver.py` | `outputs/3-plan.md` (Markdown) | Exakt 17 Wochen a 10.0 bis 15.0 Stunden. Lokale Pflicht-Landingpages zu 100% in Phase 1 und 2. |
| **3b** | `3b-performance-check.xml.md` | `outputs/3-plan.md`, `inputs/performance_export.csv` | `outputs/3b-performance-check.md` | Nur Inhalte aelter als 21 Tage werden bewertet. Kapazitaet der Folgephase bleibt exakt bei 10 bis 15h. |
| **4a** | `4a-content-briefing-und-schema.xml.md` | `outputs/3-plan.md`, AgentSEO SERP-Check | `outputs/briefings/briefing-[slug].md` | SERP-Intent muss abgeglichen sein. Schema.org JSON-LD Codeblock muss syntaktisch valide sein. |
| **4b** | `4b-landingpage-html.xml.md` | `outputs/briefings/briefing-[slug].md`, `standards/design-system.css` | `outputs/html/landingpage-[slug]-[ort].html` | Standalone HTML ohne externe CDNs; Schema JSON-LD im `<head>` integriert; Local SEO Checklist abgearbeitet. |

---

## 3. Standard-Dateinamenskonventionen

1. **Kebab-Case fuer alle generierten Dateien:**
   - Erlaubt: Kleinbuchstaben `a-z`, Ziffern `0-9`, Bindestrich `-`, Unterstrich `_` (nur bei Systemdateien).
   - Verboten: Umlaute (ae, oe, ue verwenden), Leerzeichen, Sonderzeichen.
2. **Standard-Slugs:**
   - Pillar-Dateien: `pillar-[pillar-thema-slug].html` (z.B. `pillar-pflegeleistungen.html`).
   - Landingpage-Dateien: `landingpage-[leistung-slug]-[stadt-slug].html` (z.B. `landingpage-grundpflege-frankfurt-bornheim.html`).
   - Briefing-Dateien: `briefing-[thema-slug].md` (z.B. `briefing-ambulante-pflege-kosten.md`).
