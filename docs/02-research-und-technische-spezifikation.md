# 02. Research und Technische Spezifikation

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Datum:** 16. August 2026  
**Status:** Spezifikation fertiggestellt (Strikte Error-Handling & Quality-Gate-Architektur)  
**Autor:** Raphael Rechberger  

---

## 1. Verifizierte Recherchequellen

Alle nachfolgenden Quellen wurden fuer diese Spezifikation direkt abgerufen und geprueft:

| Quelle | Titel | URL | Abrufdatum | Relevanz fuer das Produktionsprojekt |
|---|---|---|---|---|
| 1 | **AgentSEO OpenAPI 3.1.0 Spezifikation** | `https://www.agentseo.dev/openapi.yaml` | 16.08.2026 | Verbindlicher REST- und Tool-Vertrag: 45 Endpunkte, Request-/Response-Schemas, Authentifizierung (`x-api-key`), Credit-Kosten. |
| 2 | **AgentSEO Hosted MCP Server Card** | `https://www.agentseo.dev/.well-known/mcp/server-card.json` | 16.08.2026 | Offizielles MCP-Manifest fuer Streamable-HTTP (`https://www.agentseo.dev/mcp`) und Tool-Definitionen. |
| 3 | **AgentSEO llms.txt & Docs Index** | `https://www.agentseo.dev/llms.txt` | 16.08.2026 | Uebersicht ueber SDKs, Error Codes, Asynchrone Jobs (202 Queued / Polling) und Workflow Bundles. |
| 4 | **Anthropic Claude Desktop MCP Guide** | `https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers` | 16.08.2026 | Offizielle Anleitung zur Anbindung lokaler MCP-Server (z.B. Filesystem Server) an Claude Desktop. |
| 5 | **MCP Transport Architecture Analysis** | `https://startdebugging.net/2026/05/fix-http-mcp-server-url-wont-connect-in-claude-desktop/` | 16.08.2026 | Technischer Nachweis: `claude_desktop_config.json` unterstuetzt ausschliesslich `stdio`. Remote HTTP-Server erfordern `mcp-remote` als Stdio-Bridge oder die Registrierung als Custom Connector. |
| 6 | **Anthropic Prompt Engineering Guidelines** | `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` | 16.08.2026 | Best Practices fuer XML-Kapselung (`<system_role>`, `<context_files>`, `<instructions>`, `<output_format>`), Intent Grounding und strukturierte Ein-/Ausgabe-Vertraege. |

---

## 2. Technische Rahmenbedingungen & Architektur-Entscheidung

### 2.1 Claude Desktop Transport-Restriktion
`claude_desktop_config.json` unter Windows (`%APPDATA%\Claude\claude_desktop_config.json`) und macOS (`~/Library/Application Support/Claude/claude_desktop_config.json`) akzeptiert standardmaessig nur Subprozesse ueber `stdio`. Direkte HTTP-URLs in der JSON-Datei fuehren zum Abbruch oder stillschweigenden Loeschen der Konfiguration.

**Loesungsarchitektur fuer AgentSEO MCP:**
1. **Option A (Empfohlen fuer Claude Desktop):** Einbindung ueber den Stdio-Bridge-Wrapper `mcp-remote` via `npx`:
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
           "x-api-key:${AGENTSEO_API_KEY}"
         ]
       },
       "filesystem": {
         "command": "npx",
         "args": [
           "-y",
           "@modelcontextprotocol/server-filesystem",
           "C:\\Users\\offic\\Documents\\Projekte\\Kunden"
         ]
       }
     }
   }
   ```
2. **Option B (GUI Connector):** Direkte Registrierung des Remote-Endpoints `https://www.agentseo.dev/mcp` unter *Claude Desktop > Settings > Connectors > Add custom connector* mit API-Key Header.
3. **Option C (Lokale Deterministische Tools):** Der Kapazitaets-Solver laeuft als lokales Python-Script (`capacity_matrix_solver.py`), um Token-Kosten und Rundungsfehler gaenzlich zu vermeiden.

### 2.2 AgentSEO Authentifizierung und Credit-Modell
- **Auth-Header:** `x-api-key: <DEIN_API_KEY>`
- **Optionale Tracking-Header:** `x-project-id: <PROJEKT_NAME>`, `x-workflow-id: <WORKFLOW_ID>`
- **Typische Credit-Kosten pro Aufruf:**
  - `agentseo_keyword_metrics_overview`: 5 Credits pro 25 Keywords
  - `agentseo_keyword_ideas_suggest`: 4 Credits
  - `agentseo_content_serp_outline`: 4 Credits
  - `agentseo_content_brief`: 6 Credits
  - `agentseo_content_schema_plan`: 3 Credits
  - `agentseo_domain_competitors`: 5 Credits pro 100 Competitors

### 2.3 Verbindliches Error-Handling & Quality-Gate-Prinzip
In dieser Produktionsarchitektur gibt es **keine stillschweigende Degradation** (kein Fallback auf unvalidierte Schaetzungen oder unvollstaendige Daten). Wenn ein Fehler auftritt, erfolgt ein strukturierter Abbruch:

```json
{
  "status": "ERROR",
  "error_code": "API_QUOTA_EXCEEDED | MISSING_API_KEY | INVALID_SCHEMA | TIMEOUT",
  "step": "step_2_cluster_research",
  "message": "Prazise Fehlerbeschreibung",
  "blocking_reason": "Verifizierte Metriken fuer 32 Keywords fehlen.",
  "remediation_action": "Kontingent aufladen oder API-Key in der Konfiguration hinterlegen."
}
```

---

## 3. Detaillierte Spezifikation der Tool-Bausteine

### Tool 1: `agentseo_keyword_enricher`
- **Zweck:** Vollautomatische Anreicherung von Seed-Keywords aus Schritt 2 mit realen Metriken (Suchvolumen, Keyword Difficulty, CPC, Prioritaet). Ersetzt das manuelle Abtippen in Ahrefs.
- **Workflow-Schritt:** Schritt 2 (`2-cluster-recherche.xml.md`)
- **Ausfuehrungsumgebung:** AgentSEO Remote MCP (`agentseo_keyword_metrics_overview`)
- **Input-Schema:**
  ```json
  {
    "keywords": ["ambulante pflege kosten", "pflegedienst frankfurt preise"],
    "location": "Germany",
    "language": "de",
    "min_search_volume": 0,
    "sort_by": "priority"
  }
  ```
- **Output-Schema:**
  ```json
  {
    "location": {"name": "Germany", "code": 2276},
    "keyword_metrics": {
      "ambulante pflege kosten": {
        "search_volume": 1800,
        "difficulty": 24,
        "cpc": 2.45,
        "intent": "commercial",
        "priority_score": 85
      }
    },
    "markdown_summary": "Tabelle mit Kennzahlen..."
  }
  ```
- **Validierung:** Pruefung auf 100%ige Vollstaendigkeit aller uebergebenen Keywords.
- **Error-Handling:** Bei fehlendem Key, ungueltigem Token, Timeout oder erschoepftem Credit-Kontingent: Sofortiger STOPP mit strukturierter Fehlermeldung. Kein unsauberes Uebergehen oder Erraten von Suchvolumina.

---

### Tool 2: `capacity_matrix_solver`
- **Zweck:** Exakte, mathematisch fehlerfreie Erstellung des 120-Tage-Plans (17 Wochen a 10-15 Std) unter Beruecksichtigung der Score-Priorisierungsformel und der Pflichtabdeckungs-Regel fuer lokale Landingpages.
- **Workflow-Schritt:** Schritt 3 (`3-120-tage-plan.xml.md`)
- **Ausfuehrungsumgebung:** Lokales Python-Script (`mcp/tools/capacity_matrix_solver.py`).
- **Input-Schema:**
  ```json
  {
    "capacity_hours_per_week_min": 10,
    "capacity_hours_per_week_max": 15,
    "total_days": 120,
    "content_items": [
      {
        "id": "item-001",
        "title": "Pflegedienst Frankfurt Bornheim",
        "content_type": "Landingpage",
        "category": "Lokal",
        "search_volume": 70,
        "keyword_difficulty": 12,
        "effort_hours": 1.25,
        "is_mandatory_location": true
      }
    ],
    "effort_weights": {
      "Pillar-Page": 8.0,
      "Blogartikel": 3.0,
      "Landingpage": 1.25,
      "FAQ": 1.0
    }
  }
  ```
- **Output-Schema:**
  ```json
  {
    "total_weeks": 17,
    "allocated_items_count": 48,
    "backlog_items_count": 12,
    "weekly_schedule": [
      {
        "week": 1,
        "phase": 1,
        "total_hours": 13.75,
        "items": [
          {
            "id": "item-001",
            "title": "Pflegedienst Frankfurt Bornheim",
            "content_type": "Landingpage",
            "score": 21.5,
            "priority": "Hoch",
            "effort_hours": 1.25
          }
        ]
      }
    ]
  }
  ```
- **Validierung:** Jede Woche muss strikt zwischen 10.0 und 15.0 Stunden liegen. Lokale Pflicht-Landingpages muessen prioritativ in Phase 1 und 2 platziert sein.
- **Error-Handling:** Kann die Matrix nicht mathematisch geloest werden (z.B. zu wenige Items fuer Wochenkapazitaet oder ungueltige Stundenformate), wirft das Script einen Validierungsfehler mit exaktem Delta aus.

---

### Tool 3: `serp_gap_analyzer`
- **Zweck:** Live-Abfrage der Top-SERP-Ergebnisse, Suchintentionen, W-Fragen ("People Also Ask") und Content-Gaps der Wettbewerber fuer ein spezifisches Keyword.
- **Workflow-Schritt:** Schritt 4a (`4a-content-briefing-und-schema.xml.md`)
- **Ausfuehrungsumgebung:** AgentSEO Remote MCP (`agentseo_analyze_serp` / `agentseo_content_gap` / `agentseo_content_serp_outline`)
- **Input-Schema:**
  ```json
  {
    "keyword": "ambulanter pflegedienst leistungen",
    "location": "Germany",
    "language": "de",
    "outline_depth": "detailed"
  }
  ```
- **Output-Schema:**
  ```json
  {
    "primary_intent": "informational_commercial",
    "top_serp_formats": ["Ratgeber", "Leistungsuebersicht mit Preisen"],
    "people_also_ask": [
      "Welche Leistungen zahlt die Pflegekasse?",
      "Was gehoert zur Grundpflege?"
    ],
    "competitor_h2_structure": [
      "Grundpflege vs. Behandlungspflege",
      "Kosten und Kostenuebernahme",
      "Ablauf der Beauftragung"
    ],
    "missing_topics": ["Verhinderungspflege", "Pflegegrad-Voraussetzungen"]
  }
  ```
- **Validierung:** Gleicht die urspruenglich angenommene Intention mit den Live-Ergebnissen ab.
- **Error-Handling:** Bei Fehlschlag der SERP-Analyse stoppt der Schritt mit `ERROR_SERP_FETCH_FAILED`. Keine Generierung von Briefings auf Basis unbestaetigter Annahmen.

---

### Tool 4: `schema_jsonld_generator`
- **Zweck:** Erzeugung von syntaktisch und semantisch valide Schema.org JSON-LD Bloecken (`LocalBusiness`, `MedicalBusiness`, `Service`, `Article`, `FAQPage`, `BreadcrumbList`).
- **Workflow-Schritt:** Schritt 4a (`4a-content-briefing-und-schema.xml.md`)
- **Ausfuehrungsumgebung:** AgentSEO Remote MCP (`agentseo_content_schema_plan`) und Prompt-Validierung.
- **Input-Schema:**
  ```json
  {
    "page_type": "local_business",
    "page_title": "Pflegedienst Frankfurt Bornheim",
    "business_name": "simCura Pflegedienst",
    "address": {
      "street": "Berger Str. 120",
      "city": "Frankfurt am Main",
      "postal_code": "60385",
      "country": "DE"
    },
    "faqs": [
      {"question": "Was kostet der Dienst?", "answer": "Die Kosten richten sich nach..."}
    ]
  }
  ```
- **Output-Schema:** Valides `<script type="application/ld+json">` Array mit verknuepften `@graph`-Knoten.
- **Error-Handling:** Bei unvollstaendigen Unternehmensdaten (z.B. fehlende Adresse bei LocalBusiness) wird der Block nicht unvollstaendig erzeugt, sondern als fehlendes Pflichtfeld gemeldet.

---

### Tool 5: `gsc_rank_tracker_sync`
- **Zweck:** Abgleich veröffentlichter Inhalte mit echten Ranking-Daten aus Google Search Console oder AgentSEO Rank Tracker nach 30, 60 und 90 Tagen.
- **Workflow-Schritt:** Schritt 3b (`3b-performance-check.xml.md`)
- **Ausfuehrungsumgebung:** AgentSEO Remote MCP (`agentseo_rank_track` / `agentseo_local_visibility_track`) oder GSC-Export-Parsing.
- **Input-Schema:**
  ```json
  {
    "plan_phase": 1,
    "performance_data": [
      {
        "url": "https://example.de/leistungen/grundpflege/",
        "keyword": "grundpflege leistungen",
        "clicks": 140,
        "impressions": 3200,
        "average_position": 8.4,
        "days_live": 35
      }
    ]
  }
  ```
- **Output-Schema:** Klassifizierung in Performer, Stagnierend und Unterperformer mit konkreten Massnahmen.
- **Error-Handling:** Bei fehlenden Performance-Daten wird keine Phasenanpassung "ins Blaue hinein" vorgenommen.

---

### Tool 6: `seo_entity_discovery`
- **Zweck:** Identifikation von Hauptentitaeten, Nischen-Pillars und Content-Gaps gegenueber Wettbewerbern beim Projekt-Kickoff.
- **Workflow-Schritt:** Schritt 1 (`1-pillar-identifikation.xml.md`)
- **Ausfuehrungsumgebung:** AgentSEO Remote MCP (`agentseo_domain_competitors`, `agentseo_domain_intersection`, `agentseo_content_competitor_gap_matrix`).

---

### Tool 7: `design_token_extractor` & `visual_tree_builder`
- **Zweck:**
  - `design_token_extractor`: Analysiert den hochgeladenen Full-Page-Screenshot in Schritt 1c und persistiert Farb-, Font- und Card-Tokens in `design-system.css`.
  - `visual_tree_builder`: Generiert die interaktive, eigenstaendige Menue-Hierarchie `1b-menuestruktur.html`.
- **Workflow-Schritt:** Schritt 1b und Schritt 1c.
- **Error-Handling:** Fehlt der Screenshot in 1c, stoppt Claude und fordert diesen zwingend ein (kein Erraten des Designs).

---

## 4. Standardisierte XML-Prompt-Architektur

Alle Produktions-Prompts (0 bis 4b) folgen einheitlich dieser XML-Hierarchie:

```xml
<system_role>
  Definition der Expertenrolle, Tonalitaet und Arbeitsprinzipien.
</system_role>

<context_files>
  <required_file path="manifest.json" purpose="Projektstatus und Metadaten" />
  <required_file path="standards/design-system.css" purpose="Visuelle Konsistenz" />
</context_files>

<instructions>
  <step number="1" name="Input-Validierung">...</step>
  <step number="2" name="Analyse und Tool-Aufruf">...</step>
  <step number="3" name="Synthese und Strukturierung">...</step>
</instructions>

<validation_rules>
  - Regel 1: Keine Halluzination von Suchvolumen (Strikter Stopp bei fehlenden Daten)
  - Regel 2: Strikte Einhaltung der Wochenstunden (10-15h)
  - Regel 3: Lokale Pflichtabdeckung vorrangig in Phase 1-2
  - Regel 4: Fail-Fast bei allen API- und Validierungsfehlern
</validation_rules>

<output_format>
  <file_target path="outputs/1-pillar-themen.md" format="markdown" />
  <manifest_update field="phases.step_1.status" value="completed" />
</output_format>

<human_review_gate>
  Explizite Checkliste fuer Raphael und Jesse zur Freigabe des Meilensteins.
</human_review_gate>
```
