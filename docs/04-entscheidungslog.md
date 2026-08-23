# 04. Entscheidungslog (Architecture Decision Records)

> **Lifecycle: superseded.** Aktuelle Entscheidungsautoritaet: `00_admin/DECISIONS.md`. Alte ADRs bleiben als fachliche Quelle erhalten, gelten aber nicht automatisch als aktive Entscheidung.

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Status:** Aktiv  
**Letzte Aktualisierung:** 17. August 2026  

---

## Inhaltsverzeichnis

- [ADR-001: Persistentes Projekt-Manifest](#adr-001-persistentes-projekt-manifest-manifestjson)
- [ADR-002: Persistentes Design-System](#adr-002-persistentes-design-system-design-systemcss)
- [ADR-003: AgentSEO MCP-Integration fuer automatisierte Keyword-Anreicherung](#adr-003-agentseo-mcp-integration-fuer-automatisierte-keyword-anreicherung)
- [ADR-004: Deterministischer Kapazitaets-Solver fuer die 120-Tage-Planung](#adr-004-deterministischer-kapazitaets-solver-fuer-die-120-tage-planung)
- [ADR-005: Zweiteilung von Schritt 4 in Content-Briefing und HTML-Generierung](#adr-005-zweiteilung-von-schritt-4-in-content-briefing-und-html-generierung)
- [ADR-006: Strikte Fail-Fast- und Quality-Gate-Doktrin](#adr-006-strikte-fail-fast--und-quality-gate-doktrin-ohne-stillschweigende-fallbacks)
- [ADR-007: Stdio-Transport-Architektur via mcp-remote fuer Claude Desktop](#adr-007-stdio-transport-architektur-via-mcp-remote-fuer-claude-desktop)
- [ADR-008: Zielmarkt ueber country und location_code statt ueber einen Ortsnamen](#adr-008-zielmarkt-ueber-country-und-location_code-statt-ueber-einen-ortsnamen)
- [ADR-009: Asynchrone AgentSEO-Aufrufe als verbindliches Muster](#adr-009-asynchrone-agentseo-aufrufe-als-verbindliches-muster)
- [ADR-010: Mengenregeln maschinenpruefbar im Manifest-Schema statt als Prosa im Prompt](#adr-010-mengenregeln-maschinenpruefbar-im-manifest-schema-statt-als-prosa-im-prompt)
- [ADR-011: Generative Engine Optimization (GEO) & RAG Evidence Containers](#adr-011-generative-engine-optimization-geo--rag-evidence-containers)

---

### ADR-001: Persistentes Projekt-Manifest (`manifest.json`)

- **Kontext:** Im urspruenglichen Workflow musste Claude in jedem Prompt angewiesen werden, den Kontext aus vorherigen Chat-Nachrichten oder verstreuten Textdateien zu rekonstruieren. Dies fuehrte bei langen Chats zu Kontextverlust und Inkonsistenzen.
- **Entscheidung:** Jedes Kundenprojekt fuehrt ab Schritt 0 eine zentrale Datei `manifest.json`, die saemtliche Metadaten, URLs, Zielgruppen, Phasenstatus und Dateipfade enthaelt und gegen `standards/manifest.schema.json` validiert.
- **Konsequenzen:** Jeder Folgeschritt liest ausschliesslich die im Manifest referenzierten Artefakte. Der Kontext ist dateibasiert, reproduzierbar und unabhaengig vom Chat-Verlauf.

---

### ADR-002: Persistentes Design-System (`design-system.css`)

- **Kontext:** Schritt 1c forderte einen Screenshot der Kunden-Website zur visuellen Analyse. In Schritt 4 (Landingpage-Bau) stand dieser Screenshot nicht mehr im aktiven Kontextfenster zur Verfuegung. Claude musste das CSS bei jeder Landingpage neu erraten, was zu visuellem Drift fuehrte.
- **Entscheidung:** In Schritt 1c werden die visuellen Tokens (Farben, Typografie, Abstaende, Buttons, Card-Stile) einmalig extrahiert und verbindlich in `standards/design-system.css` persistiert.
- **Konsequenzen:** Alle spaeter erzeugten HTML-Dateien (Pillar-Templates und Cluster-Landingpages) binden identische CSS-Tokens und Utility-Klassen ein. Visuelle Konsistenz ist garantiert.

---

### ADR-003: AgentSEO MCP-Integration fuer automatisierte Keyword-Anreicherung

- **Kontext:** Schritt 2 erforderte das manuelle Pruefen von 25 bis 40 Seed-Keywords pro Pillar in Ahrefs, das Kopieren in Excel und den CSV-Re-Export. Dieser manuelle Zwischenschritt kostete 45 bis 60 Minuten pro Pillar.
- **Entscheidung:** Anbindung des offiziellen AgentSEO Hosted MCP-Servers ueber den Endpunkt `/keyword-metrics/overview` (`agentseo_keyword_metrics_overview`), um Suchvolumen, Difficulty und CPC automatisiert und verifiziert in Sekunden abzurufen.
- **Konsequenzen:** Massive Zeitersparnis bei gleichzeitiger Erhoehung der Datenpraezision.
- **Nachtrag 17.08.2026:** Der Aufruf ist nur mit `location`, `location_code`, `language` und `sync: false` betriebssicher, siehe ADR-008 und ADR-009.

---

### ADR-004: Deterministischer Kapazitaets-Solver fuer die 120-Tage-Planung

- **Kontext:** Die Erstellung des 120-Tage-Plans (17 Wochen a exakt 10 bis 15 Stunden) mit variierenden Deliverable-Aufwaenden und der Pflichtabdeckung lokaler Landingpages ueberfordert die probabilistische Arithmetik von LLMs.
- **Entscheidung:** Die Stunden- und Phasen-Berechnung wird durch ein deterministisches Python-Script (`mcp/tools/capacity_matrix_solver.py`) durchgefuehrt.
- **Konsequenzen:** Mathematisch exakte Wochensummen und garantierte Platzierung aller lokalen Pflicht-Seiten in Phase 1 und 2.
- **Nachtrag 17.08.2026:** Die Formulierung "lueckenlose Einhaltung der Kapazitaetsgrenzen" war zu weit gefasst. Der Solver erzwingt nur die Obergrenze von 15.0 Stunden. Die Untergrenze von 10.0 Stunden ist ein Planungsziel und wird an Gate 3 geprueft. Der Horizont von 17 Wochen ist ein Rahmen, nicht eine Zusage: belegt werden nur so viele Wochen, wie das Datenvolumen hergibt. Der Plankopf weist die gemessene Spanne seit 1.3.0 selbst aus.

---

### ADR-005: Zweiteilung von Schritt 4 in Content-Briefing und HTML-Generierung

- **Kontext:** Schritt 4 umfasste gleichzeitig SERP-Intent-Pruefung, Wettbewerbsanalyse, EEAT-Checkliste, Schema.org JSON-LD Generierung und vollstaendigen HTML-Code. Dies fuehrte regelmaessig zu Output-Abbruechen oder fluechtigen Briefings.
- **Entscheidung:** Schritt 4 wird modular aufgeteilt:
  - **4a:** `4a-content-briefing-und-schema.xml.md` fuer redaktionelle Briefings und Schema-Markup (fuer alle Content-Typen).
  - **4b:** `4b-landingpage-html.xml.md` ausschliesslich fuer den Bau produktionsfertiger HTML-Landingpages.
- **Konsequenzen:** Die Copywriter (Regina, Katja, Alexander) erhalten saubere, unueberladene Briefings. Frontend-Code wird kontrolliert und separat validiert.

---

### ADR-006: Strikte Fail-Fast- und Quality-Gate-Doktrin ohne stillschweigende Fallbacks

- **Kontext:** In einem professionellen Kunden-Produktionsumfeld koennen unvollstaendige Daten oder ungepruefte Annahmen zu fehlerhaften Kunden-Websites fuehren.
- **Entscheidung:** Es gibt keine stillschweigenden Fallbacks auf unvalidierte Schaetzwerte. Fehlt ein API-Key, ist das Kontingent erschoepft oder schlaegt eine Validierung fehl, stoppt der Prozess mit einer expliziten, strukturierten Fehlermeldung.
- **Konsequenzen:** Hoechste Datenqualitaet und Nachvollziehbarkeit. Keine stillen Fehler.
- **Nachtrag 17.08.2026:** Die Doktrin gilt, ist aber im Code noch nicht vollstaendig umgesetzt. Offene Stellen sind in CHANGELOG 1.3.0 benannt: der Solver verwirft nicht platzierbare Items still und ersetzt fehlende Metriken durch 0, der JSON-LD-Validator meldet ungepruefte Typen als gueltig.

---

### ADR-007: Stdio-Transport-Architektur via `mcp-remote` fuer Claude Desktop

- **Kontext:** `claude_desktop_config.json` unter Windows und macOS validiert ausschliesslich `stdio`-Server. Direkte HTTP-URLs in der Konfigurationsdatei fuehren zu Abstuerzen oder dem Loeschen des Config-Blocks.
- **Entscheidung:** Einbindung von Remote-MCP-Servern (AgentSEO) ueber den Stdio-Bridge-Wrapper `mcp-remote` via `npx` in `claude_desktop_config.template.json`.
- **Konsequenzen:** Maximale Kompatibilitaet mit Claude Desktop ohne manuelle Node-Server-Basteleien.
- **Nachtrag 17.08.2026:** Geheimnisse gehoeren in den `env`-Block, nicht als `${VARIABLE}` in `args`. Werte unter `env` erreichen den Serverprozess als echte Umgebungsvariablen, eine Interpolation in `args` findet nicht statt und landet wortwoertlich im HTTP-Header. Der GitHub-Server nutzt deshalb `env` mit `GITHUB_PERSONAL_ACCESS_TOKEN`, AgentSEO uebergibt den Key direkt im Header-Argument.

---

### ADR-008: Zielmarkt ueber `country` und `location_code` statt ueber einen Ortsnamen

- **Kontext:** Schritt 2 uebergab an AgentSEO nur `keywords`, `location` und `language`. Im Live-Test am 17.08.2026 antwortete der Datenlieferant mit `VALIDATION_ERROR: DataForSEO keyword_overview live failed with status 40501 "Invalid Field: 'location_code'."`. Wurde nur `location_code: 2276` gesetzt, kamen Daten zurueck, die als `location_name: "United States"` beschriftet waren. Erst beide Felder zusammen ergaben `location_name: "Germany"`.
- **Entscheidung:** Der Zielmarkt wird im Manifest als `country` (ISO-3166-Alpha-2) und `location_code` (Google Geo Target Criteria ID) gefuehrt. Die Zuordnung liegt verbindlich in `standards/location-codes.json`. Prompt 0 erhebt das Land, Prompt 2 uebergibt `location`, `location_code` und `language` gemeinsam und prueft `location_name` in der Antwort gegen den Zielmarkt.
- **Begruendung fuer eine Tabelle statt Laufzeit-Ableitung:** Fuer Laender gilt die Regel 2000 plus ISO-3166-numerisch (DE 276 ergibt 2276). Fuer Staedte und Regionen gilt sie nicht, dort sind die IDs frei vergeben. AgentSEO stellt keinen Endpunkt zum Nachschlagen bereit, geprueft wurden alle 48 Tools. Eine Ableitung zur Laufzeit waere damit ein Raten und verstiesse gegen ADR-006.
- **Konsequenzen:** Neue Fehlercodes `ERROR_LOCATION_UNKNOWN` und `ERROR_LOCATION_MISMATCH`. Ein Kunde in einem nicht hinterlegten Markt bricht den Lauf ab, statt Daten des falschen Markts in die Roadmap zu schreiben. Die Tabelle muss bei neuen Maerkten erweitert werden.
- **Bekannte Ausnahme:** `agentseo_content_serp_outline` akzeptiert keinen `location_code`. Mit `location: "Germany"` loeste das Tool am 17.08.2026 auf `location_code: 1018023`, `location_name: "Many,Louisiana,United States"` auf und lieferte eine englische Platzhalter-Gliederung. Verwertbar sind dort nur die SERP-Signale, nicht die Geo-Angabe und nicht die Gliederung.

---

### ADR-009: Asynchrone AgentSEO-Aufrufe als verbindliches Muster

- **Kontext:** Alle datenliefernden AgentSEO-Tools haben den Parameter `sync` mit Default `true`. Zwei synchrone Aufrufe von `agentseo_keyword_metrics_overview` liefen am 17.08.2026 in einen Abbruch nach 60 Sekunden. Dasselbe Tool mit `sync: false` antwortete in unter 5 Sekunden mit einer `jobId`.
- **Entscheidung:** Alle Tool-Aufrufe in den Prompts laufen mit `sync: false`. Das Ergebnis wird ueber `agentseo_job_status` abgeholt, mit `retry_after_seconds` aus der Antwort als Wartezeit. `status: failed` fuehrt zu `ERROR_AGENTSEO_FETCH_FAILED` samt unveraendertem `error.code` und `error.message` im Log.
- **Konsequenzen:** Kein Zeitlimit-Abbruch mehr bei groesseren Batches. Der Ablauf braucht dafuer eine Warteschleife, die in den Prompts explizit beschrieben ist.

---

### ADR-010: Mengenregeln maschinenpruefbar im Manifest-Schema statt als Prosa im Prompt

- **Kontext:** Beim Framework-Testlauf am 17.08.2026 wurden drei Prosa-Regeln der Prompts verletzt, ohne dass etwas den Lauf gestoppt haette: Schritt 1c wurde ohne Screenshot uebersprungen statt mit `ERROR_SCREENSHOT_MISSING` abzubrechen, Prompt 1 Regel 2 (mindestens 8 Cluster pro Pillar) wurde mit 5 Clustern in einer Pillar unterschritten und Prompt 2 Regel 2 (mindestens 25 validierte Zeilen pro Pillar) wurde mit 5 bis 12 Zeilen deutlich unterschritten. Im gleichen Lauf wurde ein ungueltiger Phasen-Status vom JSON Schema sofort abgelehnt.
- **Beobachtung:** Prosa-Regeln in Prompts werden von einem Modell unter Ergebnisdruck gebogen, Schema-Regeln nicht.
- **Entscheidung:** Jede Mengenregel wird am Ende ihres Schritts als Zahl in die `manifest.json` geschrieben und dort vom Schema geprueft. `phases.step_1_pillar_identification.clusters_per_pillar` erlaubt 8 bis 15 pro Pillar, `phases.step_2_cluster_research.validated_rows_per_pillar` verlangt mindestens 25 pro Pillar. `status` ist in jeder Phase Pflichtfeld.
- **Konsequenzen:** Ein Schritt kann sich nicht mehr als `completed` eintragen, wenn die Zahlen nicht stimmen. Die Pruefung ist ohne Vertrauen in den ausfuehrenden Agenten nachvollziehbar. Weitere Zaehlregeln sind nach demselben Muster nachzuruesten, insbesondere fuer 1c und 4a.
 
---
 
### ADR-011: Generative Engine Optimization (GEO) & RAG Evidence Containers
 
- **Kontext:** Empirische Studien aus 2026 (Ahrefs Maerz 2026 mit 863k Keywords, Zhang et al. arXiv:2604.25707) zeigen, dass nur noch 38% der Zitationen in Google AI Overviews aus den organischen Top-10 stammen. LLM-Reranker (Gemini 3, Perplexity, ClaudeBot) bewerten Text nach Information Gain (Google Patent US20200349181A1) und absorbieren bevorzugt geschlossene Passagen (130-160 Woerter) mit harten Datenpunkten und Tabellen.
- **Entscheidung:**
  1. Das Manifest-Schema fuehrt `geo_targets` (mit Pflichtfeld `primary_engines`) und `entities` (mit Wikidata-URIs via `sameAs`).
  2. Der Kapazitaets-Solver (v1.3.0) unterstuetzt 4 neue GEO-Content-Typen (`Data-Hub`, `Entity-Anchor`, `Comparison-Table`, `FAQ-Hub`) und berechnet zweidimensionale Verlinkungs-Maps mit Zitations-Zweck.
  3. Schritt 4a erzeugt ein Notion-kompatibles Frontmatter mit 50 bis 70 Woertern Hero-Direct-Answer, Evidence Containers (130-160 Woerter) und 15 bis 20 Semantic Triples.
  4. Schema.org JSON-LD wird zwingend als `@graph` mit sauberer Trennung von `about` (Hauptkonzept mit Wikidata-URI) und `mentions` (sekundaere Entitaeten) modelliert und ueber `mcp/tools/validate_schema_jsonld.py --strict` CLI geprueft.
- **Konsequenzen:** Der Workflow ist zu 100% zukunftssicher fuer AI Overviews, Perplexity und Claude Web Search aufgestellt, ohne die bestehende Dateipersistenz oder den Notion-Handoff zu brechen.
