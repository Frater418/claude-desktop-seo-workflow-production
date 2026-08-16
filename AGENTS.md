# AGENTS.md: System-Instruktionen fuer KI-Agenten & Ausfuehrungs-Engines

**Projekt:** Heartweb Claude Desktop SEO-Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Stand:** 16. August 2026  
**Zielgruppe:** Claude Desktop, Claude Code, OpenCode, Cursor, Hermes Agent & autonome Systeme  

---

## 1. Fundamentale Architektur: Framework vs. Kunden-Workspace

Dieses Framework trennt strikt zwischen zwei Ebenen:

1. **Das Framework-Repository (Master Blueprint & Tooling Library):**
   - Enthält die 9 standardisierten XML-Prompts (`prompts/0-kickoff.xml.md` bis `prompts/4b-landingpage-html.xml.md`).
   - Enthält die verbindlichen Daten- und Design-Standards (`standards/manifest.schema.json`, `standards/design-system.css`).
   - Enthält die deterministischen Python-Tools (`mcp/tools/capacity_matrix_solver.py`, `validate_schema_jsonld.py`) und MCP-Verträge (`mcp/tool-contracts/`).

2. **Der individuelle Kunden-Projektordner (Operativer Mandanten-Workspace):**
   - Für jeden Kunden wird ein isolierter Ordner auf der Festplatte erstellt (z.B. `C:\Users\offic\Documents\Projekte\Kunden\simcura-pflegedienst\`).
   - Hier liegt kein Git-Repository, sondern ausschließlich die persistenten Kundendaten:
     - `manifest.json` (Der maschinenlesbare Single Source of Truth Status des Mandanten)
     - `design-system.css` (Die kundenindividuellen CSS-Tokens aus Schritt 1c)
     - `outputs/1-pillar-themen.md` (Themen-Inventar & Pillars)
     - `outputs/2-cluster-themen-agentseo.csv` (Verifizierte Keyword-Metriken)
     - `outputs/3-plan.md` (120-Tage-Roadmap & Verlinkungs-Maps)
     - `outputs/briefings/` (Fertige Briefings mit Notion-Frontmatter für Texter)
     - `outputs/html/` (Fertige HTML-Templates für Entwickler)

---

## 2. Wie Claude Desktop den Zustand ueber Sessions hinweg behaelt

In Claude Desktop gehen Anweisungen zwischen verschiedenen Chats niemals verloren, weil der Workflow **dateibasiert über den Filesystem-MCP-Server** arbeitet:

```text
[Chat Session 1] -> Führt Prompt 0 & 1 aus -> Schreibt manifest.json & 1-pillar-themen.md auf die Festplatte
                         |
                         v (Festplatte: C:\Projekte\Kunden\simcura\)
                         |
[Chat Session 2] -> Startet Tage später mit Prompt 3 -> Liest manifest.json & 2-cluster.csv von der Festplatte
                         |
                         v
                    Erzeugt 3-plan.md ohne jeden Kontextverlust!
```

---

## 3. Verbindliche Arbeitsregeln fuer alle Agenten & Prompts

1. **Autorenschaft:** Alle Dokumente, Code-Dateien und Commits sind ausschließlich auf **Raphael Rechberger** auszustellen.
2. **Formatierungsregel:** Niemals Gedankenstriche (Em-Dashes — oder En-Dashes –) verwenden. Ausschließlich Bindestriche (-), Doppelpunkte (:) oder saubere Satzstrukturen nutzen.
3. **Strikte Fail-Fast-Doktrin:** Keine stillschweigenden Fallbacks oder Schätzungen. Fehlt ein API-Key, ein Pflichtfeld oder sind Daten unvollständig, stoppt der Prozess mit einem expliziten Fehlercode.
4. **Schrittfolge:** Der Workflow folgt strikt der Sequenz `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> (3b) -> 4a -> 4b`.
5. **Notion-Kompatibilitaet:** Alle Briefings aus Schritt 4a müssen das standardisierte YAML-Frontmatter für die direkte Übernahme in Notion-Datenbanken enthalten.

---

## 4. Lokale Tool-Ausfuehrung

- **Deterministischer 120-Tage-Solver (v1.2.0):**
  `python mcp/tools/capacity_matrix_solver.py --input <datei.csv|json> --output <plan.md>`
- **Google Rich Results Schema-Validator:**
  `python mcp/tools/validate_schema_jsonld.py`
