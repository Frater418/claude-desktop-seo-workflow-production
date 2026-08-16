# Claude Desktop SEO Workflow: Produktionsarchitektur

**Autor & Architektur:** Raphael Rechberger  
**Organisation / Kontext:** Heartweb (Zusammenarbeit Raphael Rechberger & Jesse Jensen)  
**Version:** 1.2.0  
**Stand:** 16. August 2026  
**Status:** Produktionsstandard aktiv & validiert  

---

## 1. Uebersicht & Zielsetzung

Dieses Repository enthaelt den modernisierten, produktionsreifen **SEO-Content- & Rollout-Workflow fuer die Claude Desktop App**.

Basiert auf den bewaehrten SEO-Grundlagen von Jesse Jensen wurden saemtliche Reibungspunkte, Kontextbrueche und manuellen Flaschenhaelse systematisch eliminiert. Das System transformiert den urspruenglichen Prompt-Ablauf in eine hochgradig deterministische, datenbank-kompatible Produktionspipeline fuer Heartweb mit:

1. **Persistentem Projekt-Manifest (`manifest.json`):** Maschinenlesbarer Single-Source-of-Truth-Status fuer jedes Kundenprojekt ohne Kontextverlust im Chat (1:1 Notion-kompatibel).
2. **Persistentem Design-System (`design-system.css`):** Screenshot-basierte CSS-Token-Extraktion in Schritt 1c fuer konsistentes Styling bis hin zur Landingpage-Generierung in Schritt 4b.
3. **Automatisierter Keyword-Anreicherung via AgentSEO MCP:** Vollstaendige Beseitigung des manuellen Ahrefs-Abtippens durch direkte API-Abfragen verifizierter Suchmetriken.
4. **Deterministischem 120-Tage-Kapazitaets-Solver v1.2:** Mathematisch exakte Wochenplanung (17 Wochen a 10 bis 15 Stunden) mit prioritativer Gebietsabdeckung fuer lokale Landingpages und automatischer Verlinkungs-Map.
5. **Strikter Fail-Fast- und Qualitaets-Doktrin:** Keine stillschweigenden Fallbacks oder Schaetzdaten. Bei Fehlern stoppt das System sofort mit klaren Handlungsanweisungen.
6. **Zweiteilung von Schritt 4:** Trennung in redaktionelle Briefings inkl. Schema.org JSON-LD (4a) mit YAML-Frontmatter fuer Copywriter (Regina, Katja, Alexander) und Frontend-HTML-Code (4b).

---

## 2. Interaktive Workflow-Landkarte

Klicke auf die einzelnen Schritte, Standards oder Dokumente, um direkt zur jeweiligen Spezifikation zu springen:

```text
+----------------------------------------------------------------------------------------------------+
|                                    PROJEKT-INITIALISIERUNG                                         |
|                                                                                                    |
|  [0-Kickoff-Prompt] --------> Erstellt manifest.json gemaess [standards/manifest.schema.json]      |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                                   v
+--------------------------------------------------+-------------------------------------------------+
|                               STRUKTUR- & ARCHITEKTUR-PHASE                                        |
|                                                                                                    |
|  [1-Pillar-Identifikation] --> Content-Inventar & Pillar-Tabelle (outputs/1-pillar-themen.md)      |
|                                                  |                                                 |
|  [1b-Seitenarchitektur] -----> Menue-Struktur & URL-Schema (1b-seitenarchitektur.md + .html)       |
|                                                  |                                                 |
|  [1c-Pillar-Templates] ------> Design-Token-Extraktion in [standards/design-system.css]           |
|                                + Standalone Pillar-HTML-Templates (outputs/html/pillar-*.html)     |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                                   v
+--------------------------------------------------+-------------------------------------------------+
|                                 KEYWORD- & ROADMAP-PHASE                                           |
|                                                                                                    |
|  [2-Cluster-Recherche] ------> Automatisierte Anreicherung via AgentSEO MCP-Server                 |
|                                (outputs/2-cluster-themen-agentseo.csv)                             |
|                                                  |                                                 |
|  [3-120-Tage-Plan] ----------> Deterministischer Solver (mcp/tools/capacity_matrix_solver.py)     |
|                                17 Wochen a 10-15h + Verlinkungs-Map (outputs/3-plan.md)            |
|                                                  |                                                 |
|  [3b-Performance-Check] -----> Tag 30/60/90 Ranking-Sync & adaptive Phasenanpassung               |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
                                                   v
+--------------------------------------------------+-------------------------------------------------+
|                              TAGESGESCHAEFT & PRODUKTION (SCHRITT 4)                               |
|                                                                                                    |
|  [4a-Content-Briefing] ------> Live-SERP-Check, Intent-Grounding, EEAT, Schema.org JSON-LD         |
|                                -> Uebergabe an Copywriter (Regina, Katja, Alexander) in Notion     |
|                                                  |                                                 |
|  [4b-Landingpage-HTML] ------> Vollstaendige HTML-Datei im einheitlichen Design-System             |
|                                (outputs/html/landingpage-*.html) fuer Web-Entwicklung              |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Direkte Navigation & Cross-Links

### 3.1 Produktions-Prompts (`prompts/`)
- [Schritt 0: Kickoff & Manifest-Initialisierung](prompts/0-kickoff.xml.md)
- [Schritt 1: Pillar-Themen-Identifikation](prompts/1-pillar-identifikation.xml.md)
- [Schritt 1b: Seitenarchitektur & Menuestruktur](prompts/1b-seitenarchitektur.xml.md)
- [Schritt 1c: Pillar-Page-Templates & Design-Extraktion](prompts/1c-pillar-template.xml.md)
- [Schritt 2: Cluster-Recherche & AgentSEO-Anreicherung](prompts/2-cluster-recherche.xml.md)
- [Schritt 3: 120-Tage-Content-Plan & Verlinkungs-Map](prompts/3-120-tage-plan.xml.md)
- [Schritt 3b: Performance-Check & adaptive Anpassung](prompts/3b-performance-check.xml.md)
- [Schritt 4a: Content-Briefing, SERP-Check & Schema JSON-LD](prompts/4a-content-briefing-und-schema.xml.md)
- [Schritt 4b: Landingpage HTML-Generator](prompts/4b-landingpage-html.xml.md)

### 3.2 Standards & Datenvertraege (`standards/`)
- [Manifest Schema (`manifest.schema.json`)](standards/manifest.schema.json)
- [Globales Design-System (`design-system.css`)](standards/design-system.css)
- [Dateinamen- und Output-Vertrag](standards/dateinamen-und-output-vertrag.md)

### 3.3 Dokumentation, Memos & Handbuecher (`docs/`)
- [Jesse Walkthrough Memo (Markdown)](docs/jesse-walkthrough-memo.md)
- [Jesse Walkthrough Memo (2-Seiten PDF)](docs/jesse-walkthrough-memo.pdf)
- [Betriebshandbuch fuer Claude Desktop](docs/betriebshandbuch-claude-desktop.md)
- [Copywriter-Handoff- & Notion-Guidelines](docs/copywriter-handoff-guidelines.md)
- [01. Review-Abgleich (Baseline vs. Optimierung)](docs/01-review-abgleich.md)
- [02. Research & Technische Spezifikation](docs/02-research-und-technische-spezifikation.md)
- [03. 4-Sprint-Umsetzungsplan](docs/03-sprint-plan.md)
- [04. Entscheidungslog (Architecture Decision Records)](docs/04-entscheidungslog.md)
- [05. Human-in-the-Loop & Quality Gates](docs/05-human-in-the-loop.md)
- [06. Pilot-Abnahme-Checkliste](docs/06-pilot-abnahme-checkliste.md)

### 3.4 MCP-Tools, Solver & Validierung (`mcp/`)
- [Claude Desktop Config Template](mcp/claude_desktop_config.template.json)
- [Deterministischer Kapazitaets-Solver v1.2](mcp/tools/capacity_matrix_solver.py)
- [Schema.org JSON-LD Validator](mcp/tools/validate_schema_jsonld.py)
- [Tool-Contract: AgentSEO Keyword Enricher](mcp/tool-contracts/agentseo_keyword_enricher.json)
- [Tool-Contract: SERP Gap Analyzer](mcp/tool-contracts/serp_gap_analyzer.json)
- [Tool-Contract: Schema JSON-LD Generator](mcp/tool-contracts/schema_jsonld_generator.json)

### 3.5 Test-Fixtures & Nachweise (`tests/`)
- [Akzeptanztest-Protokoll (Alle 5 Tests bestanden)](tests/acceptance-tests.md)
- [Test-Fixture: Referenz-Manifest simCura](tests/fixtures/sample_manifest.json)
- [Test-Fixture: 61 verifizierte Cluster-Keywords](tests/fixtures/sample_cluster_keywords.json)
- [Test-Fixture: SERP-Briefing Response](tests/fixtures/sample_serp_briefing.json)

---

## 4. Schnellstart fuer Claude Desktop

### Schritt 1: MCP-Server konfigurieren
Kopiere die Vorlage [mcp/claude_desktop_config.template.json](mcp/claude_desktop_config.template.json) in deine Claude Desktop Konfiguration:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Setze deinen AgentSEO API-Key:
```json
{
  "mcpServers": {
    "agentseo": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://www.agentseo.dev/mcp",
        "--header",
        "x-api-key:DEIN_AGENTSEO_API_KEY"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Pfad\\Zu\\Deinen\\Projekten"
      ]
    }
  }
}
```

### Schritt 2: Projekt starten
1. Erstelle einen neuen Ordner fuer den Kunden (z.B. `kunden/simcura-pflege/`).
2. Oeffne Claude Desktop und starte mit [prompts/0-kickoff.xml.md](prompts/0-kickoff.xml.md).
3. Folge der vorgegebenen Prompt-Reihenfolge (0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a/4b).

---

## 5. Qualitaets- und Governance-Prinzipien

- **Strikter Fail-Fast-Standard:** Keine Generierung von Texten oder Plaenen auf Basis fehlerhafter oder fehlender Daten.
- **Human-in-the-Loop Pflicht:** Jeder Meilenstein besitzt eine explizite Abnahme-Checkliste gemaess [docs/05-human-in-the-loop.md](docs/05-human-in-the-loop.md).
- **Kein ungepruefter KI-Content:** Redaktionelle Inhalte werden von Copywritern finalisiert; Claude Desktop liefert das datengestuetzte, verifizierte Fundament.

---

## 6. Lizenz & Autorenschaft

**Konzeption & Architektur:** Raphael Rechberger  
**Lizenz:** Proprietaer / Fuer den produktiven Einsatz bei Heartweb  
