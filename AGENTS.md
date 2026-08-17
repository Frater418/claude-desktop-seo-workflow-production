# AGENTS.md: System-Instruktionen fuer KI-Agenten & Ausfuehrungs-Engines

**Projekt:** Heartweb Claude Desktop SEO-Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Stand:** 17. August 2026  
**Zielgruppe:** Claude Desktop, Claude Code, OpenCode, Cursor, Hermes Agent & autonome Systeme  

---

## 1. Fundamentale Architektur: Framework vs. Kunden-Workspace

Dieses Framework trennt strikt zwischen zwei Ebenen:

1. **Das Framework-Repository (Master Blueprint & Tooling Library):**
   - Enthaelt die 9 standardisierten XML-Prompts (`prompts/0-kickoff.xml.md` bis `prompts/4b-landingpage-html.xml.md`).
   - Enthaelt die verbindlichen Daten- und Design-Standards (`standards/manifest.schema.json`, `standards/location-codes.json`, `standards/design-system.css`).
   - Enthaelt die deterministischen Python-Tools (`mcp/tools/capacity_matrix_solver.py`, `validate_schema_jsonld.py`) und MCP-Vertraege (`mcp/tool-contracts/`).

2. **Der individuelle Kunden-Projektordner (Operativer Mandanten-Workspace):**
   - Fuer jeden Kunden wird ein isolierter Ordner auf der Festplatte erstellt (verbindlich `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\<kunde-slug>\`, z.B. `...\Heartweb\Kunden\simcura-pflegedienst\`).
   - Hier liegt kein Git-Repository, sondern ausschliesslich die persistenten Kundendaten:
     - `manifest.json` (Der maschinenlesbare Single Source of Truth Status des Mandanten)
     - `design-system.css` (Die kundenindividuellen CSS-Tokens aus Schritt 1c)
     - `outputs/1-pillar-themen.md` (Themen-Inventar & Pillars)
     - `outputs/2-cluster-themen-agentseo.csv` (Verifizierte Keyword-Metriken)
     - `outputs/3-plan.md` (120-Tage-Roadmap & Verlinkungs-Maps)
     - `outputs/briefings/` (Fertige Briefings mit Notion-Frontmatter fuer Texter)
     - `outputs/html/` (Fertige HTML-Templates fuer Entwickler)

---

## 2. Wie Claude Desktop den Zustand ueber Sessions hinweg behaelt

In Claude Desktop gehen Anweisungen zwischen verschiedenen Chats niemals verloren, weil der Workflow **dateibasiert ueber den Filesystem-MCP-Server** arbeitet:

```text
[Chat Session 1] -> Fuehrt Prompt 0 & 1 aus -> Schreibt manifest.json & 1-pillar-themen.md auf die Festplatte
                         |
                         v (Festplatte: C:\...\Projekte\Heartweb\Kunden\simcura\)
                         |
[Chat Session 2] -> Startet Tage spaeter mit Prompt 3 -> Liest manifest.json & 2-cluster.csv von der Festplatte
                         |
                         v
                    Erzeugt 3-plan.md ohne jeden Kontextverlust!
```

---

## 3. Verbindliche Arbeitsregeln fuer alle Agenten & Prompts

1. **Autorenschaft:** Alle Dokumente, Code-Dateien und Commits sind ausschliesslich auf **Raphael Rechberger** auszustellen.
2. **Formatierungsregel:** Niemals Gedankenstriche (Em-Dashes — oder En-Dashes –) verwenden. Ausschliesslich Bindestriche (-), Doppelpunkte (:) oder saubere Satzstrukturen nutzen.
3. **Strikte Fail-Fast-Doktrin:** Keine stillschweigenden Fallbacks oder Schaetzungen. Fehlt ein API-Key, ein Pflichtfeld oder sind Daten unvollstaendig, stoppt der Prozess mit einem expliziten Fehlercode.
4. **Schrittfolge:** Der Workflow folgt strikt der Sequenz `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> (3b) -> 4a -> 4b`.
5. **Notion-Kompatibilitaet:** Alle Briefings aus Schritt 4a muessen das standardisierte YAML-Frontmatter fuer die direkte Uebernahme in Notion-Datenbanken enthalten.
6. **Zielmarkt:** Jeder AgentSEO-Aufruf uebergibt `location`, `location_code` und `language` gemeinsam. Quelle sind `country` und `location_code` aus der `manifest.json`, aufgeloest ueber `standards/location-codes.json`. Ein Ortsname allein fuehrt zu Provider-Fehlern oder zu Daten des falschen Markts.
7. **Asynchrone Tool-Calls:** Jeder AgentSEO-Aufruf laeuft mit `sync: false`, das Ergebnis wird ueber `agentseo_job_status` abgeholt. Synchrone Aufrufe brechen nach 60 Sekunden ab.
8. **Maschinenpruefbare Mengenregeln:** Zaehlwerte werden am Ende jedes Schritts in die `manifest.json` geschrieben und vom Schema geprueft (`clusters_per_pillar` 8 bis 15, `validated_rows_per_pillar` mindestens 25). Ein Schritt darf nicht als `completed` eingetragen werden, wenn eine Zahl nicht erreicht ist.

---

## 4. Lokale Tool-Ausfuehrung

- **Deterministischer 120-Tage-Solver (v1.2.0):**
  `python mcp/tools/capacity_matrix_solver.py --input <datei.csv|json> --output <plan.md>`
- **Google Rich Results Schema-Validator:**
  `python mcp/tools/validate_schema_jsonld.py`
  Offener Punkt: das Skript hat noch keine Kommandozeilen-Schnittstelle. Der Aufruf gibt nur eine
  Bereitschaftsmeldung aus und prueft nichts. Bis zum Nachbau der CLI ist die Pruefung ueber den
  Google Rich Results Test zu machen.

- **AgentSEO-Aufrufe:** immer `sync: false`, Ergebnis ueber `agentseo_job_status` abholen,
  `location`, `location_code` und `language` gemeinsam uebergeben.
