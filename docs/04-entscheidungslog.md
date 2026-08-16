# 04. Entscheidungslog (Architecture Decision Records)

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Status:** Aktiv  
**Letzte Aktualisierung:** 16. August 2026  

---

## Inhaltsverzeichnis

- [ADR-001: Persistentes Projekt-Manifest](#adr-001-persistentes-projekt-manifest-manifestjson)
- [ADR-002: Persistentes Design-System](#adr-002-persistentes-design-system-design-systemcss)
- [ADR-003: AgentSEO MCP-Integration fuer automatisierte Keyword-Anreicherung](#adr-003-agentseo-mcp-integration-fuer-automatisierte-keyword-anreicherung)
- [ADR-004: Deterministischer Kapazitaets-Solver fuer die 120-Tage-Planung](#adr-004-deterministischer-kapazitaets-solver-fuer-die-120-tage-planung)
- [ADR-005: Zweiteilung von Schritt 4 in Content-Briefing und HTML-Generierung](#adr-005-zweiteilung-von-schritt-4-in-content-briefing-und-html-generierung)
- [ADR-006: Strikte Fail-Fast- und Quality-Gate-Doktrin](#adr-006-strikte-fail-fast--und-quality-gate-doktrin-ohne-stillschweigende-fallbacks)
- [ADR-007: Stdio-Transport-Architektur via mcp-remote fuer Claude Desktop](#adr-007-stdio-transport-architektur-via-mcp-remote-fuer-claude-desktop)

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

---

### ADR-004: Deterministischer Kapazitaets-Solver fuer die 120-Tage-Planung

- **Kontext:** Die Erstellung des 120-Tage-Plans (17 Wochen a exakt 10 bis 15 Stunden) mit variierenden Deliverable-Aufwaenden und der Pflichtabdeckung lokaler Landingpages ueberfordert die probabilistische Arithmetik von LLMs.
- **Entscheidung:** Die Stunden- und Phasen-Berechnung wird durch ein deterministisches Python-Script (`mcp/tools/capacity_matrix_solver.py`) durchgefuehrt.
- **Konsequenzen:** Mathematisch exakte Wochensummen, lueckenlose Einhaltung der Kapazitaetsgrenzen und garantierte Platzierung aller lokalen Pflicht-Seiten in Phase 1 und 2.

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

---

### ADR-007: Stdio-Transport-Architektur via `mcp-remote` fuer Claude Desktop

- **Kontext:** `claude_desktop_config.json` unter Windows und macOS validiert ausschliesslich `stdio`-Server. Direkte HTTP-URLs in der Konfigurationsdatei fuehren zu Abstuerzen oder dem Loeschen des Config-Blocks.
- **Entscheidung:** Einbindung von Remote-MCP-Servern (AgentSEO) ueber den Stdio-Bridge-Wrapper `mcp-remote` via `npx` in `claude_desktop_config.template.json`.
- **Konsequenzen:** Maximale Kompatibilitaet mit Claude Desktop ohne manuelle Node-Server-Basteleien.
