# CHANGELOG

Alle relevanten Aenderungen an diesem Produktionsprojekt werden in dieser Datei dokumentiert.
Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) und folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [1.4.0] - 2026-08-17

### Generative Engine Optimization (GEO), RAG Evidence Containers, Schema.org Graph & Validator CLI

**Autor:** Raphael Rechberger  
**Anlass:** Strategischer Ausbau des Heartweb-Workflows fuer Zitations-Sichtbarkeit in Google AI Overviews (Gemini 3), Perplexity, Claude Web Search und ChatGPT Search basierend auf 2026er Studien (Princeton GEO, Zhang et al. 2026, Ahrefs Maerz 2026).

#### Hinzugefuegt
- `docs/07-geo-architecture-specification.md`: Vollstaendige empirische und technische Spezifikation der GEO-Erweiterung (Selection vs. Absorption, Query Fan-Out, Schema.org `about`/`mentions`, Definitive Language, Evidence Containers).
- `docs/08-geo-sprint-plan-and-multi-agent-orchestration.md`: Detaillierter 4-Sprint-Umsetzungsplan und Rollen-Definition des 6-Agenten OpenCode OMO Ensembles (Sisyphus, Oracle, Prometheus, Hephaestus, Daedalus, Metis).
- `03_research/`: Persistierte Rohdaten der Exa.ai Multi-Angle Deep Research (`03_research/exa_geo_research_raw.json`) und automatisierter Recherche-Runner `run_exa_geo_verification.py`.
- `tests/run_acceptance_tests.py`: Automatisierter Testrunner fuer CI/CD und lokale Validierung aller 5 Akzeptanztests.
- `tests/fixtures/sample_schema_graph.json`: Validierte Schema.org JSON-LD `@graph` Referenz-Fixture mit Wikidata-Verknuepfungen.
- `standards/manifest.schema.json`: Erweiterung um `geo_targets` (mit Pflichtfeld `primary_engines`) und `entities` (mit `brand_entity`, `brand_wikidata_id`, `core_services` und Wikidata-URIs).
- `mcp/tools/validate_schema_jsonld.py` (v1.1.0): Vollstaendige CLI (`--input`, `--strict`, `--json-out`), Unterstuetzung fuer `@graph`, Markdown/HTML-Extraktion und strikte Wikidata-URI-Pruefung.
- `standards/design-system.css`: Neue RAG- und GEO-Komponenten (`.definition-block`, `.evidence-container`, `.comparison-table`, `.speakable-section`, `.badge-datahub`).

#### Geaendert
- `mcp/tools/capacity_matrix_solver.py` (v1.3.0): Native Unterstuetzung fuer 4 neue GEO-Content-Typen (`Data-Hub` mit 5.0h / Faktor 3.5, `Entity-Anchor` mit 4.0h / Faktor 3.0, `Comparison-Table` mit 2.0h / Faktor 2.5, `FAQ-Hub` mit 3.0h / Faktor 2.5) sowie zweidimensionale Verlinkungs-Maps mit GEO-Zweck-Ausweisung.
- `prompts/0-kickoff.xml.md` (v1.4.0): Erhebung von GEO-Targets und Entitaeten im Kickoff.
- `prompts/1-pillar-identifikation.xml.md` (v1.4.0): Ergaenzung von `Information_Gain_Potential` und `Conversational_Query_Patterns`.
- `prompts/1b-seitenarchitektur.xml.md` (v1.4.0): Semantische Section-IDs und Kebab-Case Anchor-Konvention.
- `prompts/1c-pillar-template.xml.md` (v1.4.0): Hero-Definitionsblock (`.definition-block`) und Schema-Graph im Template.
- `prompts/2-cluster-recherche.xml.md` (v1.4.0): GEO-Typisierung, Information-Gain-Scoring und AI-Overview-Pruefung.
- `prompts/4a-content-briefing-und-schema.xml.md` (v1.4.0): 50-70 Woerter Hero-Direct-Answer, 15-20 Semantic Triples, Evidence Containers (130-160 Woerter) und `@graph` Schema.org JSON-LD fuer Notion.
- `prompts/4b-landingpage-html.xml.md` (v1.4.0): Semantische Section-IDs, Microdata und GEO-Attribute.
- `tests/fixtures/sample_manifest.json`: Aktualisiert mit `country: "DE"`, `location_code: 2276`, `geo_targets` und `entities`.
- `tests/acceptance-tests.md`: Alle 5/5 Akzeptanztests verifiziert und als 100% bestanden protokolliert.

---

## [1.3.0] - 2026-08-17

### Zielmarkt-Parameter, asynchrone Tool-Calls, maschinenpruefbare Mengenregeln und Doku-Bereinigung

**Autor:** Raphael Rechberger
**Anlass:** Erster Live-Testlauf des Workflows gegen den echten AgentSEO-Server und ein Konsistenz-Audit des Repos. Beides am 17.08.2026, protokolliert in `00_admin/AUDIT-2026-08-17-konsistenz.md` und `tests/acceptance-tests.md`.

#### Hinzugefuegt
- `standards/location-codes.json`: verbindliche Zuordnung Land zu Google Geo Target Criteria ID. DE 2276 live bestaetigt, AT 2040 und CH 2756 aus der Regel 2000 plus ISO-3166-numerisch abgeleitet. Enthaelt ausserdem die dokumentierten Tool-Grenzen von AgentSEO.
- `standards/manifest.schema.json`: Pflichtfelder `country` und `location_code`. Neue Zaehlfelder `phases.step_1_pillar_identification.clusters_per_pillar` (8 bis 15 pro Pillar) und `phases.step_2_cluster_research.validated_rows_per_pillar` (mindestens 25 pro Pillar), zusaetzlich `keywords_not_returned` und `location_verified`. `status` ist in jeder Phase Pflichtfeld.
- Neue Fehlercodes: `ERROR_BRIEFING_INCOMPLETE` und `ERROR_LOCATION_UNKNOWN` in Schritt 0, `ERROR_LOCATION_UNKNOWN`, `ERROR_LOCATION_MISMATCH` und `ERROR_INSUFFICIENT_CLUSTER_COVERAGE` in Schritt 2.
- `docs/04-entscheidungslog.md`: ADR-008 (Zielmarkt ueber country und location_code), ADR-009 (asynchrone AgentSEO-Aufrufe), ADR-010 (Mengenregeln im Schema statt als Prosa im Prompt).
- `docs/betriebshandbuch-claude-desktop.md`: eigene Phase 2b fuer Schritt 3b, der bisher im gesamten Ablauf fehlte, sowie Abschnitt 2.2b zur Einrichtung des GitHub-Servers inklusive Token-Scope, der Erklaerung warum `env` funktioniert und `${VARIABLE}` in `args` nicht, und der Grenze zwischen Desktop-MCP und Cloud-Session.
- `README.md`: Abschnitt 3.6 fuer CHANGELOG, AGENTS.md, CLAUDE.md, PROJECT_STATE und `scripts/`, die bisher in keiner Navigationsliste standen.
- `AGENTS.md` und `CLAUDE.md`: Regeln 6 bis 8 zu Zielmarkt, asynchronen Aufrufen und maschinenpruefbaren Zaehlwerten.

#### Geaendert
- `prompts/2-cluster-recherche.xml.md` (Version 1.1.0): uebergibt `location`, `location_code`, `language` und `sync: false`, holt Ergebnisse ueber `agentseo_job_status` ab, prueft `location_name` der Antwort gegen den Zielmarkt und verwirft nicht zurueckgegebene Keywords statt sie mit 0 zu fuellen. Regel 2 erzwingt jetzt eine zweite Recherche-Runde und danach einen Abbruch.
- `prompts/0-kickoff.xml.md` (Version 1.1.0): erhebt das Land, schreibt `country` und `location_code`, setzt die vom Schema verlangten Felder `author`, `created_at`, `artifacts` und alle acht Phasen-Objekte.
- `prompts/3-120-tage-plan.xml.md`: 17 Wochen sind als Horizont formuliert, nicht als Zusage. Regel 1 unterscheidet die vom Solver erzwungene Obergrenze von der manuell zu pruefenden Untergrenze.
- `mcp/tools/capacity_matrix_solver.py`: der statische Satz "Kapazitaets-Garantie" ist durch eine gemessene Zeile "Kapazitaets-Messung" ersetzt, die Anzahl aktiver Wochen sowie die tatsaechliche Spanne ausgibt und beim Verlassen des Zielbands warnt.
- `mcp/claude_desktop_config.template.json`: Filesystem-Roots auf `Documents\Projekte` und `Desktop\Heartweb` erweitert, damit Framework und Kunden-Workspaces abgedeckt sind. Der Block `github` aus Commit `bf428dbe` bleibt unveraendert erhalten, er ist am 17.08.2026 mit 26 Werkzeugen live verifiziert. Der AgentSEO-Key steht direkt im Header, weil `${AGENTSEO_API_KEY}` in `args` nicht aufgeloest wird.
- `tests/acceptance-tests.md`: vollstaendig neu ausgefuehrt und mit gemessenen Werten dokumentiert.
- `docs/03-sprint-plan.md`: Repo-Baum auf den Ist-Stand gebracht, Freigabestatus geklaert.
- `docs/06-pilot-abnahme-checkliste.md`: Abschluss-Freigaben auf Offen zurueckgesetzt.

#### Korrigiert
- **Kunden-Pfad vereinheitlicht** auf `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\<slug>\`. Vorher standen vier Varianten in `CLAUDE.md`, `AGENTS.md` (zwei Stellen), `00_admin/PROJECT_STATE.md`, `docs/02`, `docs/06`, `README.md`, `docs/betriebshandbuch-claude-desktop.md` und im Config-Template. Der Filesystem-Server konnte den echten Workspace damit nicht sehen.
- **17-Wochen-Behauptung korrigiert.** Version 1.1.0 fuehrte "17 Wochen a 10-15h" als Eigenschaft des Solvers. Nachgemessen belegt der Solver nur so viele Wochen, wie das Datenvolumen hergibt: mit der Repo-Fixture 9 aktive Wochen, mit 48 Live-Datensaetzen 10 aktive Wochen. Betroffene Stellen in `README.md`, `00_admin/PROJECT_STATE.md`, `docs/02`, `docs/03`, `docs/05`, `docs/06`, `docs/jesse-walkthrough-memo.md` und `prompts/3-120-tage-plan.xml.md` sind angepasst.
- **Fixture-Beschreibung korrigiert.** `tests/fixtures/sample_cluster_keywords.json` enthaelt 61 synthetische, per Formel erzeugte Keywords, keine verifizierten Live-Metriken. Der Eintrag in 1.1.0 nannte faelschlich 40 Keywords und die Bezeichnung "verifiziert".
- **Sequenz ergaenzt.** `CLAUDE.md` und `README.md` liessen Schritt 3b in der Ausfuehrungsfolge aus.
- **Tote Referenz behoben.** `docs/01-review-abgleich.md` verwies auf `mcp/tool-contracts/agentseo_keyword_enricher.md`, die Datei ist eine `.json`.
- **Mengenangabe im Memo korrigiert.** 100 Keywords sind das Limit pro API-Call, nicht die Menge pro Pillar.
- **Rollenbezeichnung korrigiert.** "Copywriting Lead" existiert nicht, das Texter-Team sind Regina, Katja und Alexander.
- **Akzeptanztest-Status korrigiert.** 1.1.0 behauptete "alle 5 Akzeptanztests bestanden". Nachgeprueft: TEST-03 ist nicht ausfuehrbar, TEST-02 und TEST-04 sind teilweise bestanden, TEST-05 ist fuer Schritt 4a nicht bestanden.

#### Offene Punkte (bewusst nicht in dieser Version behoben)
- `mcp/tools/validate_schema_jsonld.py` hat keine CLI, verarbeitet keine JSON-LD-Arrays und meldet unbekannte Typen als gueltig.
- `mcp/tools/capacity_matrix_solver.py` verwirft nicht platzierbare Items still (`if not placed: pass`), erzwingt die Untergrenze von 10 Stunden nicht (W10 des Referenzlaufs liegt bei 9.0h) und ersetzt fehlende Metriken durch 0.
- `prompts/4a-content-briefing-und-schema.xml.md` hat keinen Fehlercode, obwohl es Live-Metriken in das Notion-Frontmatter schreibt.
- `standards/manifest.schema.json` setzt nirgends `additionalProperties: false`.
- `standards/design-system.css` hat keine Media Queries und keine der von 1c und 4b geforderten Komponenten NAP-Box, Breadcrumb, Sticky-CTA, Vergleichstabelle, Akkordeon.
- `tests/fixtures/sample_manifest.json` validiert seit dieser Version nicht mehr, weil `country` und `location_code` fehlen.
- Es existiert kein ausfuehrbarer Testrunner.

---

## [1.2.0] - 2026-08-16

### Nachtraeglich dokumentiert: Solver v1.2, Agenten-Instruktionen, Betriebsdokumentation

**Autor:** Raphael Rechberger
**Hinweis:** Diese Version wurde bei Auslieferung nicht im Changelog erfasst und ist hier nachgetragen, damit die Historie lueckenlos ist.

#### Hinzugefuegt
- `AGENTS.md`: System-Instruktionen fuer Claude Desktop, Claude Code, OpenCode, Cursor und Hermes.
- `CLAUDE.md`: Kurzfassung derselben Regeln fuer CLI-Agenten.
- `00_admin/PROJECT_STATE.md`: Projektzustand und Handoff-Protokoll.
- `docs/betriebshandbuch-claude-desktop.md`: Schritt-fuer-Schritt-Anleitung fuer Desktop App, MCP-Setup und Projects.
- `docs/jesse-walkthrough-memo.pdf`: gesetzte 2-Seiten-Fassung des Memos.
- `scripts/generate_memo_pdf.py` und `scripts/generate_sample_keywords.py`: Hilfsskripte fuer PDF-Satz und Fixture-Erzeugung.

#### Geaendert
- `mcp/tools/capacity_matrix_solver.py` auf v1.2.0: Verlinkungs-Maps, Phasenlogik und CSV-Import.
- `tests/fixtures/sample_cluster_keywords.json` von 40 auf 61 Datensaetze erweitert.
- `README.md`: Navigations-Hub mit Deep-Links auf alle Artefakte.

#### Entfernt
- Temporaere Cockpit-UI (`ui/`) inklusive Prompt-Generator, zurueckgenommen mit Commit `d03f7de`.

---

## [1.1.0] - 2026-08-16

### Vollstaendiger Rollout aller Sprints: Prompts, Tooling, Solver & Betriebsdokumentation

**Autor:** Raphael Rechberger

#### Hinzugefuegt
- **XML-Produktions-Prompts (`prompts/`):**
  - `prompts/0-kickoff.xml.md`: Projekt-Initialisierung & Manifest-Setup.
  - `prompts/1-pillar-identifikation.xml.md`: Pillar-Themen-Identifikation & Gap-Analyse.
  - `prompts/1b-seitenarchitektur.xml.md`: Finale Informationsarchitektur & interaktives Menuediagramm.
  - `prompts/1c-pillar-template.xml.md`: Screenshot-Analyse, CSS-Token-Persistierung & Pillar-HTML-Templates.
  - `prompts/2-cluster-recherche.xml.md`: Cluster-Recherche & automatisierte AgentSEO-Keyword-Anreicherung.
  - `prompts/3-120-tage-plan.xml.md`: 120-Tage-Roadmap & interne Verlinkungs-Map.
  - `prompts/3b-performance-check.xml.md`: Tag 30/60/90 Ranking-Sync & adaptive Phasenanpassung.
  - `prompts/4a-content-briefing-und-schema.xml.md`: SERP-Intent Check, Notion-Frontmatter & Schema.org JSON-LD.
  - `prompts/4b-landingpage-html.xml.md`: Produktionsfertiger Landingpage-HTML-Generator.

- **Deterministische Tools & Validierung (`mcp/tools/`):**
  - `mcp/tools/capacity_matrix_solver.py`: Mathematisch exakter 120-Tage-Solver (17 Wochen a 10-15h, 100% Pflichtabdeckung fuer lokale Landingpages). *Korrigiert in 1.3.0: der Solver belegt nur so viele Wochen, wie das Datenvolumen hergibt, und erzwingt die Untergrenze nicht.*
  - `mcp/tools/validate_schema_jsonld.py`: Autarker JSON-LD Schema.org Validator gegen Google Rich Results Standards.
  - Formale Tool-Vertraege unter `mcp/tool-contracts/` (`agentseo_keyword_enricher.json`, `serp_gap_analyzer.json`, `schema_jsonld_generator.json`).

- **Test-Fixtures & Nachweise (`tests/`):**
  - `tests/fixtures/sample_manifest.json`: Referenz-Manifest fuer simCura Pflegedienst.
  - `tests/fixtures/sample_cluster_keywords.json`: 40 verifizierte Keywords fuer Solver-Tests. *Korrigiert in 1.3.0: die Datei enthaelt 61 synthetische, formelgenerierte Keywords ohne Live-Metriken.*
  - `tests/fixtures/sample_serp_briefing.json`: Beispielhafter SERP-Briefing-Datensatz.
  - `tests/acceptance-tests.md`: Vollstaendig dokumentiertes Testprotokoll (alle 5 Akzeptanztests bestanden). *Korrigiert in 1.3.0: nachgeprueft sind 1 bestanden mit offenem Punkt, 2 teilweise, 1 nicht ausfuehrbar, 1 nicht bestanden.*

- **Betriebs- & Uebergabedokumentation (`docs/`):**
  - `docs/06-pilot-abnahme-checkliste.md`: Schritt-fuer-Schritt Checkliste fuer Kunden-Rollouts.
  - `docs/betriebshandbuch-claude-desktop.md`: Nicht-technische Anleitung fuer den Alltag.
  - `docs/copywriter-handoff-guidelines.md`: Leitfaden fuer die Notion-Uebergabe an Regina, Katja, Alexander.
  - `docs/jesse-walkthrough-memo.md`: Praegnantes Walkthrough-Memo fuer Jesse Jensen mit Vergleichstabelle und Kern-Hebeln.

---

## [1.0.0] - 2026-08-16

### Initiales Release: Produktionsfundament, Standards und Tool-Architektur

**Autor:** Raphael Rechberger

#### Hinzugefuegt
- `standards/manifest.schema.json`
- `standards/design-system.css`
- `standards/dateinamen-und-output-vertrag.md`
- `mcp/claude_desktop_config.template.json`
- `docs/01-review-abgleich.md`
- `docs/02-research-und-technische-spezifikation.md`
- `docs/03-sprint-plan.md`
- `docs/04-entscheidungslog.md`
- `docs/05-human-in-the-loop.md`
- `README.md`
