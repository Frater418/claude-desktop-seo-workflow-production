# AGENTS.md & CLAUDE.md: System-Instruktionen fuer KI-Agenten

**Projekt:** Modernisierter Claude Desktop SEO-Workflow  
**Autor:** Raphael Rechberger  
**Stand:** 16. August 2026  
**Zielgruppe:** Claude Code, OpenCode, Cursor, Hermes Agent & autonome Coding-Agenten  

---

## 1. Projekt-Identitaet & Architektur

Dieses Repository enthaelt das modulare Produktions-Framework fuer den SEO-Content-Rollout in Heartweb-Kundenprojekten.
Es verbindet dateibasierte Zustandsspeicherung (`manifest.json`), standardisierte Design-Tokens (`design-system.css`), AgentSEO MCP-Tools und einen deterministischen Python-Kapazitaets-Solver mit 9 strukturierten XML-Workflow-Schritten.

---

## 2. Verzeichnis-Landkarte & Artefakt-Rollen

| Verzeichnis | Rolle im System | Wichtigste Dateien |
|---|---|---|
| `prompts/` | Operative Ausfuehrungs-Prompts (Schritte 0 bis 4b) | `0-kickoff.xml.md` bis `4b-landingpage-html.xml.md` |
| `standards/` | Verbindliche Daten- und Designvertraege | `manifest.schema.json`, `design-system.css`, `dateinamen-und-output-vertrag.md` |
| `mcp/` | MCP-Konfiguration, Python-Tools & Schnittstellen-Vertraege | `claude_desktop_config.template.json`, `capacity_matrix_solver.py`, `validate_schema_jsonld.py`, `tool-contracts/` |
| `docs/` | Strategische Dokumentation, Handbuecher & Memos | `betriebshandbuch-claude-desktop.md`, `copywriter-handoff-guidelines.md`, `jesse-walkthrough-memo.md` |
| `tests/` | Akzeptanztests & Referenz-Fixtures fuer Kundenlaeufe | `acceptance-tests.md`, `fixtures/sample_manifest.json`, `fixtures/sample_cluster_keywords.json` |

---

## 3. Verbindliche Arbeitsregeln fuer Agenten

1. **Autorenschaft:** Bei jeder Aenderung oder Dokumentation ist ausschliesslich **Raphael Rechberger** als Autor zu fuehren.
2. **Formatierungsregel:** Niemals Gedankenstriche (Em-Dashes oder En-Dashes) verwenden. Immer Bindestriche (-), Doppelpunkte (:) oder saubere Satzstrukturen nutzen.
3. **Strikte Fail-Fast-Doktrin:** Niemals fehlende Daten oder Suchvolumina schaetzen oder erraten. Schlaegt ein API-Call fehl oder fehlen Pflichtfelder im Manifest, stoppt der Prozess mit einem strukturierten Fehlercode.
4. **Schrittfolge:** Der Workflow folgt strikt der Sequenz `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> (3b) -> 4a -> 4b`. Kein Vorwegnehmen spaeterer Phasen.
5. **Notion-Kompatibilitaet:** Alle Briefings aus Schritt 4a muessen das standardisierte YAML-Frontmatter fuer die direkte Uebernahme in Notion-Datenbanken enthalten.

---

## 4. MCP-Tools Ausfuehrung

- **Deterministischer Solver:**
  `python mcp/tools/capacity_matrix_solver.py --input <datei.csv|json> --output <plan.md>`
- **Schema JSON-LD Validator:**
  `python mcp/tools/validate_schema_jsonld.py`
