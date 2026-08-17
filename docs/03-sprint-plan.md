# 03. Sprint-Plan: Modernisierung des Claude Desktop SEO-Workflows

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Datum:** 16. August 2026, Stand aktualisiert 17. August 2026  
**Status:** Freigegeben am 16.08.2026 und in vier Sprints umgesetzt  
**Autor:** Raphael Rechberger  

---

## 1. Uebersicht der Sprints und Phasen

| Sprint | Fokus | Hauptziel | Kern-Artefakte & GitHub-Deliverables |
|---|---|---|---|
| **Sprint 1** | **Produktionsfundament & Repo-Setup** | Etablierung des oeffentlichen GitHub-Repos, Projekt-Manifest-Schema, Design-System, Dateinamen-Vertrag, Master-README mit lueckenlosem Crosslinking und MCP-Konfiguration. | `README.md` (Master-Hub), `CHANGELOG.md`, `standards/manifest.schema.json`, `standards/design-system.css`, `standards/dateinamen-und-output-vertrag.md`, `mcp/claude_desktop_config.template.json` |
| **Sprint 2** | **Prompt-Refactoring** | XML-Kapselung aller 9 Prompts (0 bis 4b), Eliminierung von Inkonsistenzen, Trennung von Schritt 4 in 4a und 4b, Einbettung strikter Fail-Fast-Regeln. | `prompts/0-kickoff.xml.md` bis `prompts/4b-landingpage-html.xml.md` |
| **Sprint 3** | **Tooling, Solver & Validierung** | Bereitstellung des deterministischen Kapazitaets-Solvers, formaler Tool-Vertraege (AgentSEO / Filesystem) und Test-Fixtures. | `mcp/tools/capacity_matrix_solver.py`, Tool-Contracts, Test-Fixtures |
| **Sprint 4** | **Pilot & Betriebsdokumentation** | End-to-End Pilotdurchlauf an Testdaten, Abnahme-Checklisten und Uebergabe-Handbuch fuer Jesse und die Copywriter (Regina, Katja, Alexander). | `06-pilot-abnahme-checkliste.md`, `betriebshandbuch-claude-desktop.md`, Acceptance Tests |

---

## 2. GitHub Repository-Architektur & Dokumentations-Standard

Das Repository wird so aufgebaut, dass Raphael und Jesse in Meetings jede Komponente in Sekunden aufrufen und vollstaendig nachvollziehen koennen:

```text
claude-desktop-seo-workflow-production/
├── README.md                                  # Zentraler Navigations-Hub mit interaktiver Map & Deep-Links
├── CHANGELOG.md                               # Versionierung und Aenderungshistorie
├── AGENTS.md                                  # System-Instruktionen fuer Claude Desktop und Agenten
├── CLAUDE.md                                  # Kurzfassung der Regeln fuer CLI-Agenten
├── 00_admin/
│   ├── PROJECT_STATE.md                       # Aktueller Projektzustand und Handoff
│   └── AUDIT-2026-08-17-konsistenz.md         # Konsistenz-Audit des Frameworks
├── docs/                                      # Strategische und technische Dokumentation
│   ├── 01-review-abgleich.md                  # Baseline-Abgleich mit Jesse's Original-Workflow
│   ├── 02-research-und-technische-spezifikation.md # AgentSEO OpenAPI & Claude Desktop MCP Specs
│   ├── 03-sprint-plan.md                      # Dieser 4-Sprint-Umsetzungsplan
│   ├── 04-entscheidungslog.md                 # ADR-Entscheidungsprotokoll, ADR-001 bis ADR-010
│   ├── 05-human-in-the-loop.md                # Quality Gates und manuelle Freigabepunkte
│   ├── 06-pilot-abnahme-checkliste.md         # Checkliste fuer den ersten Kundenlauf
│   ├── betriebshandbuch-claude-desktop.md     # Nicht-technische Schritt-fuer-Schritt-Anleitung
│   ├── copywriter-handoff-guidelines.md       # Uebergabe-Standard fuer Regina, Katja, Alexander
│   ├── jesse-walkthrough-memo.md              # Executive Memo fuer Jesse Jensen
│   └── jesse-walkthrough-memo.pdf             # Gesetzte 2-Seiten-Fassung des Memos
├── standards/                                 # Verbindliche Daten- und Designvertraege
│   ├── manifest.schema.json                   # JSON Schema fuer manifest.json
│   ├── location-codes.json                    # Zielmarkt-Codes fuer AgentSEO und DataForSEO
│   ├── design-system.css                      # Persistente CSS-Tokens aus Schritt 1c
│   └── dateinamen-und-output-vertrag.md       # Nomenklatur- und Pfad-Standard
├── prompts/                                   # Produktionsfertige XML-Prompts
│   ├── 0-kickoff.xml.md                       # Schritt 0: Initialisierung & Manifest-Setup
│   ├── 1-pillar-identifikation.xml.md         # Schritt 1: Core Pillars & Content Gaps
│   ├── 1b-seitenarchitektur.xml.md            # Schritt 1b: Navigation, URLs & HTML-Diagramm
│   ├── 1c-pillar-template.xml.md              # Schritt 1c: Design-Extraktion & Pillar-HTML
│   ├── 2-cluster-recherche.xml.md             # Schritt 2: AgentSEO Keyword-Anreicherung
│   ├── 3-120-tage-plan.xml.md                 # Schritt 3: 120-Tage Kapazitaets- & Verlinkungs-Plan
│   ├── 3b-performance-check.xml.md            # Schritt 3b: 30/60/90-Tage GSC/Rank-Sync
│   ├── 4a-content-briefing-und-schema.xml.md  # Schritt 4a: SERP-Briefing & Schema JSON-LD
│   └── 4b-landingpage-html.xml.md             # Schritt 4b: HTML Landingpage Generator
├── mcp/                                       # MCP-Konfiguration & Tool-Vertraege
│   ├── claude_desktop_config.template.json    # Vorlage fuer %APPDATA%/Claude/claude_desktop_config.json
│   ├── tool-contracts/                        # Formale Schemas fuer alle Tool-Calls
│   │   ├── agentseo_keyword_enricher.json
│   │   ├── serp_gap_analyzer.json
│   │   └── schema_jsonld_generator.json
│   └── tools/
│       ├── capacity_matrix_solver.py          # Deterministischer Python 120-Tage Solver
│       └── validate_schema_jsonld.py          # JSON-LD Pruefroutinen, CLI noch offen
├── scripts/                                   # Hilfsskripte, nicht Teil der Laufzeit
│   ├── generate_sample_keywords.py            # Generator der synthetischen Keyword-Fixture
│   └── generate_memo_pdf.py                   # Erzeugt das PDF-Memo aus dem Markdown
└── tests/                                     # Validierung & Fixtures
    ├── fixtures/                              # Saubere Beispieldaten
    │   ├── sample_manifest.json
    │   ├── sample_cluster_keywords.json
    │   └── sample_serp_briefing.json
    └── acceptance-tests.md                    # Testprotokolle und Validierungsnachweis
```

---

## 3. Detaillierte Sprint-Spezifikationen

### Sprint 1: Produktionsfundament & Repo-Setup
- **Ziel:** Schaffung einer stabilen, fehlertoleranten Basis und Bereitstellung des lueckenlos dokumentierten GitHub-Repositories.
- **Scope & konkrete Dateien:**
  - `README.md`: Master-Dokumentation mit Workflow-Diagramm, Schnellstart, Crosslinks zu allen Prompts, Standards und Tools.
  - `CHANGELOG.md`: Versionierungs-Historie.
  - `standards/manifest.schema.json`: JSON Schema fuer `manifest.json`.
  - `standards/design-system.css`: Standardisierte CSS-Variablen und UI-Komponenten.
  - `standards/dateinamen-und-output-vertrag.md`: Verbindliche Festlegung aller Pfade und Dateinamen.
  - `mcp/claude_desktop_config.template.json`: Stdio-konforme Konfigurationsvorlage.
  - `docs/04-entscheidungslog.md`: Zentrales Protokoll aller getroffenen Entscheidungen.
  - `docs/05-human-in-the-loop.md`: Leitfaden fuer Qualitaets-Gates.
- **Akzeptanzkriterien:**
  1. `manifest.schema.json` validiert vollstaendig gemaess JSON Schema Draft 2020-12.
  2. `README.md` enthaelt eine lueckenlose Crosslink-Tabelle fuer alle 9 Prompts, Standards und Schemas.
  3. Konfigurationsvorlage enthaelt sprechende Platzhalter fuer Secrets. Der AgentSEO-Key steht direkt im Header-Argument, weil `${AGENTSEO_API_KEY}` in `args` nicht aufgeloest wird. Echte Keys bleiben ausschliesslich in der lokalen `claude_desktop_config.json` und werden nie committet.
  4. Git Repository ist initialisiert und enthaelt eine saubere Commit-Historie.
- **Human-Review-Punkt:** Raphael prueft das Manifest-Schema, die Master-README und das Design-System vor Sprint 2.

---

### Sprint 2: Prompt-Refactoring (XML-Architektur & Vertraege)
- **Ziel:** Ueberfuehrung der 9 Workflow-Prompts in standardisierte XML-Prompts mit striktem Intent Grounding, Fail-Fast-Validierung und Entlastung von Schritt 4.
- **Scope & konkrete Dateien:** `prompts/0-kickoff.xml.md` bis `prompts/4b-landingpage-html.xml.md`.
- **Akzeptanzkriterien:**
  1. Alle Prompts besitzen standardisierte XML-Tags (`<system_role>`, `<context_files>`, `<instructions>`, `<validation_rules>`, `<output_format>`, `<human_review_gate>`).
  2. Schritt 4 ist sauber in 4a (Briefing/Schema) und 4b (HTML) getrennt.
  3. Bei unvollstaendigen Daten, fehlenden Dateien oder API-Fehlern greift ein striktes Fail-Fast Error-Handling (kein automatisches Weitermachen mit Schaetzungen).
- **Human-Review-Punkt:** Jesse und Raphael pruefen die XML-Prompts gegenueber den Original-Markdowns auf Vollstaendigkeit.
- **Nachtrag 17.08.2026:** Kriterium 3 ist fuer 8 von 9 Prompts erfuellt. `4a-content-briefing-und-schema.xml.md` hat weiterhin keinen Fehlercode, siehe CHANGELOG 1.3.0.

---

### Sprint 3: Tooling, Solver & Validierung
- **Ziel:** Bereitstellung deterministischer Hilfstools (Kapazitaets-Solver), formaler Tool-Vertraege und Test-Fixtures.
- **Scope & konkrete Dateien:**
  - `mcp/tools/capacity_matrix_solver.py`: Deterministisches Python-Script zur fehlerfreien Stunden- und Phasenberechnung (Zielband 10 bis 15h pro Woche, Horizont 17 Wochen, Pflichtabdeckung fuer lokale Landingpages).
  - Formale Tool-Vertraege unter `mcp/tool-contracts/`.
  - Test-Fixtures unter `tests/fixtures/`.
- **Akzeptanzkriterien:**
  1. `capacity_matrix_solver.py` erzeugt aus Test-Keywords einen Plan innerhalb des 17-Wochen-Horizonts, haelt die Obergrenze von 15.0 Stunden pro aktiver Woche ein und rechnet ohne Rundungsfehler. Die Untergrenze von 10.0 Stunden wird derzeit nicht erzwungen.
  2. Lokale Landingpages werden zu 100% in Phase 1 und 2 verplant.
  3. Script laeuft vollstaendig mit Python-Standardbibliotheken (kein pip-Zwang).
- **Human-Review-Punkt:** Mathematische Pruefung der generierten 120-Tage-Matrix.
- **Nachtrag 17.08.2026:** Kriterien 1 bis 3 sind erfuellt und mit 48 Live-Datensaetzen nachgemessen. Offen bleibt, dass nicht platzierbare Items still verworfen werden und `validate_schema_jsonld.py` keine CLI hat.

---

### Sprint 4: Pilotierung, Abnahme & Betriebsdokumentation
- **Ziel:** Vollstaendige Validierung des Systems an Testdaten und Erstellung der Uebergabedokumentation fuer das Team (Jesse, Copywriter Regina, Katja, Alexander).
- **Scope & konkrete Dateien:**
  - `docs/06-pilot-abnahme-checkliste.md`: Schritt-fuer-Schritt Checkliste fuer die Projekt-Abnahme.
  - `tests/acceptance-tests.md`: Testprotokoll des Pilotdurchlaufs.
  - `docs/betriebshandbuch-claude-desktop.md`: Kompakte Anleitung zur Nutzung in Claude Desktop fuer Nicht-Techniker.
  - `docs/copywriter-handoff-guidelines.md`: Richtlinien fuer die Weitergabe der 4a-Briefings an die Redaktion.
- **Akzeptanzkriterien:**
  1. Erfolgreicher Durchlauf aller 9 Schritte an einem Referenz-Case (z.B. Multi-Location Pflegedienst).
  2. Saubere Uebergabe der Briefings an Copywriter ohne ueberfluessigen Code-Ballast.
- **Human-Review-Punkt:** Finale Freigabe des Gesamtsystems durch Jesse und Raphael.
- **Nachtrag 17.08.2026:** Ein Framework-Testlauf ueber die Schritte 0, 1, 1b, 2, 3, 4a und 4b ist erfolgt und protokolliert. Schritt 1c wurde ohne Screenshot nicht korrekt abgebrochen, das war ein Verfahrensfehler im Testlauf und kein Framework-Fehler. Kriterium 1 gilt deshalb erst mit dem ersten echten Kunden-Rollout als erfuellt. Die Abnahme in `docs/06` steht bis dahin auf Offen.

---

## 4. Governance und Freigabestatus

Dieses Produktionsprojekt erzeugt ausschliesslich modulare, wiederverwendbare Standards und Konfigurationen.
**Historischer Hinweis:** Dieser Sprint-Plan wurde am 16.08.2026 freigegeben und in vier Sprints umgesetzt. Der urspruengliche Freigabevorbehalt gilt damit als erfuellt. Fuer alle weiteren Aenderungen gilt: keine Live-Aenderungen an Kundenprojekten und keine externen API-Aufrufe ohne Freigabe durch Raphael Rechberger.
