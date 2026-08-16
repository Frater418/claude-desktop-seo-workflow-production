# CHANGELOG

Alle relevanten Aenderungen an diesem Produktionsprojekt werden in dieser Datei dokumentiert.
Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) und folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [1.0.0] - 2026-08-16

### Initiales Release: Produktionsfundament, Standards und Tool-Architektur

**Autor:** Raphael Rechberger

#### Hinzugefuegt
- **Strategische Dokumentation & Baseline-Abgleich (`docs/`):**
  - `docs/01-review-abgleich.md`: Systematischer Abgleich aller 6 Review-Kernpunkte mit dem Original-Workflow und den Onboarding-Vereinbarungen mit Jesse Jensen.
  - `docs/02-research-und-technische-spezifikation.md`: Technische Spezifikation von AgentSEO OpenAPI 3.1.0, Claude Desktop MCP Transport (`stdio` via `mcp-remote`) und XML-Prompt-Hierarchie.
  - `docs/03-sprint-plan.md`: 4-Sprint Umsetzungsplan mit klaren Phasen, Artefakten und Akzeptanzkriterien.
  - `docs/04-entscheidungslog.md`: 7 verbindliche Architecture Decision Records (ADR-001 bis ADR-007).
  - `docs/05-human-in-the-loop.md`: Leitfaden fuer die 7 verbindlichen Quality Gates und Freigabepunkte.

- **Verbindliche Standards & Datenvertraege (`standards/`):**
  - `standards/manifest.schema.json`: JSON Schema (Draft 2020-12) fuer das zentrale `manifest.json` zur persistenten Verwaltung von Projektmetadaten und Phasenfortschritt.
  - `standards/design-system.css`: Autarkes CSS-Design-System mit Token-Definitionen fuer Farben, Typografie, Buttons, Cards, Badges und Utility-Klassen.
  - `standards/dateinamen-und-output-vertrag.md`: Verbindlicher Ein- und Ausgabevertrag fuer saemtliche 9 Workflow-Schritte.

- **MCP-Konfiguration (`mcp/`):**
  - `mcp/claude_desktop_config.template.json`: Stdio-konforme Konfigurationsvorlage fuer Claude Desktop unter Windows und macOS zur Anbindung von AgentSEO und Filesystem.

- **Master-Dokumentation (`README.md`):**
  - Lueckenloser Navigations-Hub mit interaktiver Workflow-Map, Deep-Links zu allen Artefakten und Schnellstartanleitung fuer Meetings mit Jesse.

#### Geaendert
- **Qualitaets-Doktrin:** Vollstaendige Abkehr von stillschweigenden Fallbacks oder Schaetzdaten. Etablierung eines strikten Fail-Fast-Prinzips bei API-, Quota- oder Schema-Fehlern.
- **Workflow-Entlastung:** Vorbereitung der Zweiteilung von Schritt 4 in strategisches Redaktions-Briefing (4a) und HTML-Code-Generierung (4b).
