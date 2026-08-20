# Dateinamen- und Output-Vertrag

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Version:** 1.1.0  
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
    └── validation_errors.log                  # Pflicht-Log. Jeder Fehlercode und jede WARN-Meldung
                                                #   wird hier mit Zeitstempel, Schritt und Code abgelegt.
```

---

## 2. Verbindlicher Schnittstellen- und Output-Vertrag

| Schritt | Prompt-Datei | Primaere Inputs | Verbindlicher Output (Pfad & Format) | Validierungs-Kriterium & Error-Verhalten |
|---|---|---|---|---|
| **0** | `0-kickoff.xml.md` | Nutzer-Briefing, `standards/location-codes.json` | `manifest.json` (JSON) | Manifest muss gegen `manifest.schema.json` validieren, inklusive `country` und `location_code`. Fehlen Pflichtfelder: `ERROR_BRIEFING_INCOMPLETE`. |
| **1** | `1-pillar-identifikation.xml.md` | `project.v2.json`, Step-0 Release, Evidence Records, Screaming-Frog-Crawl | 1. `v2/outputs/step1/topic-inventory.v1.json` (kanonisches JSON)<br>2. `v2/outputs/step1/1-pillar-themen.md` (abgeleitete Ansicht) | 3 bis 8 Pillars; pro Pillar 8 bis 15 Hypothesen. Gespeicherte Bytes, Artifact Record und SHA-256 muessen uebereinstimmen. Kein `completed` vor externem GATE-1. |
| **1b** | `1b-seitenarchitektur.xml.md` | `outputs/1-pillar-themen.md` | 1. `outputs/1b-seitenarchitektur.md`<br>2. `outputs/1b-menuestruktur.html` | Beide Dateien muessen inhaltlich 100% synchron sein. HTML muss eigenstaendig im Browser renderbar sein. |
| **1c** | `1c-pillar-template.xml.md` | Released Step 1B candidate | `v2/outputs/step1c/design-system.v1.css` and `v2/outputs/step1c/templates/{template_id}.v1.html` | Awaiting-gate candidates only. Controlled paths refuse existing outputs. |
| **2** | `2-cluster-recherche.xml.md` | Released Step 1C candidate | `v2/outputs/step2/keyword-evidence.v1.csv` | Awaiting-gate candidates only. |
| **3** | `3-120-tage-plan.xml.md` | Released Step 2 candidate and canonical solver payloads | `v2/outputs/step3/plan.v1.md` | Solver input is the sorted projection of verified Step 2 rows with pillar_id, evidence_id, keyword, provider and raw_response_sha256. Input and output SHA-256 values bind canonical bytes. |
| **3b** | `3b-performance-check.xml.md` | Released Step 3 candidate | `v2/outputs/step3b/adjustments/{artifact_id}.v1.md` | A new candidate revision is required. |
| **4a** | `4a-content-briefing-und-schema.xml.md` | Released Step 3 candidate | `v2/outputs/step4a/briefings/{artifact_id}.v1.md` | Canonical JSON-LD graph and graph hash are required. |
| **4b** | `4b-landingpage-html.xml.md` | Released Step 4A candidate and Project V2 | `v2/outputs/step4b/pages/{artifact_id}.v1.html` | Deployment language, locale, location references, actual JSON-LD graph and canonical page content hash must validate. |

---

## 3. Standard-Dateinamenskonventionen

1. **Kebab-Case fuer alle generierten Dateien:**
   - Erlaubt: Kleinbuchstaben `a-z`, Ziffern `0-9`, Bindestrich `-`, Unterstrich `_` (nur bei Systemdateien).
   - Verboten: Umlaute (ae, oe, ue verwenden), Leerzeichen, Sonderzeichen.
2. **Standard-Slugs:**
   - Pillar-Dateien: `pillar-[pillar-thema-slug].html` (z.B. `pillar-pflegeleistungen.html`).
   - Landingpage-Dateien: `landingpage-[leistung-slug]-[stadt-slug].html` (z.B. `landingpage-grundpflege-frankfurt-bornheim.html`).
   - Briefing-Dateien: `briefing-[thema-slug].md` (z.B. `briefing-ambulante-pflege-kosten.md`).
