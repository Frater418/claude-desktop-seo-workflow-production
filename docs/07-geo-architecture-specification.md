# 07. GEO-Architektur-Spezifikation: Generative Engine Optimization 2026

> **Lifecycle: current strategy under real-output verification.** Diese Datei bleibt fachliche GEO-Quelle. Die lokale V2-Uebertragung ueber DIB-001 und PQ-4 in Schemas, Prompts, Validatoren, Renderer und Gates ist umgesetzt. Professionelle reale Outputqualitaet bleibt bis M10 in Verifikation.

**Projekt:** Heartweb Claude Desktop SEO-Workflow Framework  
**Dokument-ID:** SPEC-GEO-2026-v1.4  
**Autor & Architektur:** Raphael Rechberger  
**Datum:** 17. August 2026  
**Status:** Freigegebene Architektur-Spezifikation fuer den GEO-Upgrade-Zyklus  
**Referenz-Forschung:** Perplexity Deep Research & Exa.ai Multi-Angle Verification (`03_research/exa_geo_research_raw.json`)  

---

## 1. Executive Summary & Zielsetzung

Dieses Dokument definiert die verbindliche technische Spezifikation fuer die Erweiterung des Heartweb Claude Desktop SEO Workflows um **Generative Engine Optimization (GEO)**.

Waehrend klassisches SEO primaer auf klickorientierte Rankings in den "Ten Blue Links" optimiert, erfordert die Suchlandschaft 2026 die direkte Optimierung fuer synthetische KI-Antworten und Zitations-Engines:
- **Google AI Overviews (Gemini 3 Global Rollout)**
- **Perplexity AI (Sonar / Multi-Stage RAG Pipeline)**
- **ChatGPT Search / SearchGPT (OAI-SearchBot & Bing Index)**
- **Claude Web Search (ClaudeBot / Brave Search Backend)**

Das Upgrade erfolgt als **additive, nicht-brechende Erweiterung**. Die bestehende Datei-Persistenz, die 9 XML-Prompts, das Kunden-Workspace-Prinzip und der Notion-Handoff bleiben zu 100% erhalten.

---

## 2. Empirische Evidenz & Ranking-Mechaniken 2026

Die Spezifikation basiert auf verifizierten Datenpunkten aus Patenten, Peer-Reviewed Papers und empirischen Studien aus dem 1. Halbjahr 2026:

### 2.1 Entkopplung von Top-10 Ranking und AI-Zitation
- **Befund (Ahrefs Studie Maerz 2026, 863k Keywords, 4M URLs):** Nur noch **38% der in AI Overviews zitierten URLs** ranken organisch in den Top 10 (Rueckgang von 76% im Vorjahr). 31,2% stammen aus Positionen 11 bis 100, 31,0% von ausserhalb der Top 100.
- **Konsequenz:** Hohe Domain Authority und klassische Backlinks reichen nicht mehr aus. Entscheidend ist die **Passagen-Relevanz und Extraktionsfaehigkeit** des spezifischen Textblocks.

### 2.2 Das 2-Stufen-RAG-Modell: Selection vs. Absorption
- **Befund (Zhang et al., arXiv:2604.25707):**
  1. **Stufe 1 (Selection):** Die Suchmaschine waehlt 10 bis 30 Kandidaten-Dokumente basierend auf Entitaets-Match, Snippet-Klarheit und Index-Trust.
  2. **Stufe 2 (Absorption):** Das LLM absorbiert nur Passagen, die als strukturierte **Evidence Containers** formatiert sind (Definitionen, numerische Daten, Vergleiche, Schrittfolgen). Reine Floskel-Texte oder unstrukturierte Q&A-Listen werden verworfen.
- **Konsequenz:** Jeder H2-Abschnitt muss als modularer Evidence Container mit 130 bis 160 Woertern aufgebaut sein.

### 2.3 Google Query Fan-Out Mechanik
- **Befund (SearchScore / Ahrefs 2026):** Google Gemini zerlegt komplexe Nutzerfragen im Hintergrund in 3 bis 6 parallele Sub-Queries.
- **Konsequenz:** Content muss die typischen Sub-Queries (Scope, Kosten, Voraussetzungen, Prozess, Alternativen) in geschlossenen Einheiten abbilden.

### 2.4 Schema.org Lift & Entity Graph Density
- **Befund (DigitalApplied / The Stacc 2026):** Valide Schema.org-Auszeichnungen fuehren zu einem **2,3-fachen Zitations-Lift** (HowTo und FAQPage bis zu 2,8-fach).
- **Befund (ZipTie.dev / AppearMore 2026):** Eine Dichte von **mindestens 15 erkannten Entitaeten pro 1.000 Woerter** (mit Wikidata-Verknuepfung via `sameAs`) steigert die Auswahl-Wahrscheinlichkeit um den **Faktor 4,8**.
- **Strikte Trennung:** `about` (nur fuer 1 bis 2 Haupt-Entitaeten) vs. `mentions` (fuer alle sekundaeren Kontext-Entitaeten).

### 2.5 Information Gain & Definitive Language
- **Befund (Google Patent US20200349181A1 / Princeton GEO Study):** Das System berechnet Information Gain als Mengendifferenz zum SERP-Konsens. Eigene Statistiken und Tabellen steigern die Sichtbarkeit um bis zu **40%**.
- **Befund (Onbrand Marketer 2026):** Definitive Formulierungen ("Ambulante Pflege umfasst...") werden fast doppelt so haeufig zitiert wie vorsichtige Formulierungen ("Manche Experten meinen...").

---

## 3. Architektur-Aenderungen im Framework

```text
+----------------------------------------------------------------------------------------------------+
|                                    HEARTWEB GEO v1.4 SCHICHTEN                                     |
+----------------------------------------------------------------------------------------------------+
| 1. DATEN-STANDARDS (`standards/`):                                                                 |
|    - `manifest.schema.json`: Erweiterung um `geo_targets` und `entities` (Wikidata URIs).          |
|    - `design-system.css`: Neue Klassen `.definition-block`, `.evidence-container`, `.faq-card`.    |
+----------------------------------------------------------------------------------------------------+
| 2. STRUKTUR- & PROMPT-LAYER (`prompts/`):                                                          |
|    - `0-kickoff`: Initialisiert GEO-Targets und Entitaeten-Mapping.                                |
|    - `1-pillar` & `1b-architektur`: Information Gain Scoring (1-5), semantische Section-IDs.       |
|    - `2-cluster`: AI Overview Trigger Erkennung & Long-Tail Fan-Out Fragenmuster.                  |
|    - `4a-briefing`: Notion YAML-Frontmatter mit Hero-Lead-In & Semantic Triples Tabelle.           |
|    - `4b-html`: Autarkes HTML5-Markup mit semantischen IDs, Microdata & JSON-LD Graph.             |
+----------------------------------------------------------------------------------------------------+
| 3. DETERMINISTISCHE TOOLS (`mcp/tools/`):                                                          |
|    - `capacity_matrix_solver.py`: Upgrade v1.3.0 fuer GEO-Content-Typen (Data-Hub, Entity-Anchor). |
|    - `validate_schema_jsonld.py`: Erweiterte Pruefung auf `about`, `mentions` und Wikidata URIs.  |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Spezifikation der Komponenten

### 4.1 Schema-Erweiterung: `standards/manifest.schema.json`

Ergaenzung der Schema-Eigenschaften unter Wahrung der Rueckwaertskompatibilitaet:

```json
{
  "geo_targets": {
    "type": "object",
    "description": "Ziel-Suchraeume fuer Generative Engine Optimization",
    "properties": {
      "primary_engines": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "google_ai_overviews",
            "google_classic",
            "perplexity",
            "claude_search",
            "chatgpt_search",
            "local_maps",
            "b2b_niche"
          ]
        },
        "minItems": 1
      },
      "geo_focus": {
        "type": "string",
        "enum": [
          "citation_visibility",
          "answer_passage_extraction",
          "entity_graph_authority"
        ],
        "default": "citation_visibility"
      }
    },
    "required": ["primary_engines"]
  },
  "entities": {
    "type": "object",
    "description": "Zentrale Entitaeten mit Wikidata- und SameAs-Verknuepfungen",
    "properties": {
      "brand_entity": { "type": "string" },
      "brand_wikidata_id": { "type": "string", "pattern": "^(Q[0-9]+)?$" },
      "brand_sameas_urls": {
        "type": "array",
        "items": { "type": "string", "format": "uri" }
      },
      "core_services": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "wikidata_id": { "type": "string", "pattern": "^(Q[0-9]+)?$" }
          },
          "required": ["name"]
        }
      }
    },
    "required": ["brand_entity"]
  }
}
```

---

### 4.2 Prompt-Erweiterung: `prompts/4a-content-briefing-und-schema.xml.md`

Das Notion-Handoff fuer die Copywriter (Regina, Katja, Alexander) wird um 3 Pflicht-Elemente praezisiert:

1. **Hero Direct-Answer Vorgabe:**
   - Exakt 50 bis 70 Woerter direkt nach der H1.
   - Beantwortet die Kernfrage ohne Einleitungsfloskeln.
   - Nutzt definitive Aussagesaetze ("X ist...", "Y ermoeglicht...").

2. **Semantic Triples Tabelle:**
   - Mindestens 15 vordefinierte (Subjekt | Praedikat | Objekt) Relationen.
   - Dient dem Texter als Leitplanke, um Entitaeten natuerlich zu verknuepfen.

3. **Evidence Container Vorgabe pro H2-Sektion:**
   - Ziel-Laenge: 130 bis 160 Woerter pro logischer Passage.
   - Pflicht zur Integration von mindestens einem Datenpunkt (Zahl, Dauer, Euro, Paragraf) oder einer strukturierten Tabelle.

4. **Erweitertes Schema.org JSON-LD mit `@graph`:**
   ```json
   {
     "@context": "https://schema.org",
     "@graph": [
       {
         "@type": "Article",
         "@id": "https://example.de/leistungen/ambulante-pflege#article",
         "headline": "Ambulante Pflege Frankfurt: Leistungen, Kosten & Ablauf",
         "about": [
           {
             "@type": "Thing",
             "name": "Ambulante Pflege",
             "sameAs": "https://www.wikidata.org/wiki/Q380012"
           }
         ],
         "mentions": [
           {
             "@type": "Place",
             "name": "Frankfurt am Main",
             "sameAs": "https://www.wikidata.org/wiki/Q1794"
           },
           {
             "@type": "Thing",
             "name": "Pflegegrad",
             "sameAs": "https://www.wikidata.org/wiki/Q20829871"
           }
         ]
       }
     ]
   }
   ```

---

### 4.3 Solver-Erweiterung: `mcp/tools/capacity_matrix_solver.py` (v1.3.0)

Erweiterung der Aufwands- und Relevanz-Matrizen um spezifische GEO-Content-Typen:

```python
EFFORT_HOURS.update({
    "Data-Hub": 5.0,           # Datengestuetzte Hub-Seiten mit Original-Statistiken
    "Entity-Anchor": 4.0,      # Grundsatz-Seiten zur Etablierung einer Kern-Entitaet
    "Comparison-Table": 2.0,   # Dedizierte Vergleichs- und Differenzierungs-Seiten
    "FAQ-Hub": 3.0             # Strukturierte FAQ-Zentren fuer Voice & AI Search
})

CATEGORY_FACTORS.update({
    "Data-Hub": 3.5,
    "Entity-Anchor": 3.0,
    "Comparison-Table": 2.5,
    "FAQ-Hub": 2.5
})
```

---

### 4.4 Design-System-Erweiterung: `standards/design-system.css`

Zusaetzliche Utility-Klassen fuer RAG-optimierte Layout-Komponenten:

```css
/* ==========================================================================
   GEO & RAG Extraction Components
   ========================================================================== */

.definition-block {
  font-size: var(--font-size-lg, 1.125rem);
  line-height: var(--line-height-relaxed, 1.6);
  font-weight: var(--font-weight-medium, 500);
  color: var(--color-text-primary, #111827);
  background-color: var(--color-surface-subtle, #f9fafb);
  border-left: 4px solid var(--color-primary, #2563eb);
  padding: var(--spacing-4, 1rem) var(--spacing-5, 1.25rem);
  margin-bottom: var(--spacing-6, 1.5rem);
  border-radius: 0 var(--radius-md, 0.375rem) var(--radius-md, 0.375rem) 0;
}

.evidence-container {
  border: 1px solid var(--color-border-subtle, #e5e7eb);
  border-radius: var(--radius-lg, 0.5rem);
  padding: var(--spacing-5, 1.25rem);
  margin: var(--spacing-6, 1.5rem) 0;
  background: var(--color-surface-card, #ffffff);
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  margin: var(--spacing-4, 1rem) 0;
}

.comparison-table th,
.comparison-table td {
  border: 1px solid var(--color-border-subtle, #e5e7eb);
  padding: var(--spacing-3, 0.75rem) var(--spacing-4, 1rem);
  text-align: left;
}

.comparison-table th {
  background-color: var(--color-surface-muted, #f3f4f6);
  font-weight: var(--font-weight-semibold, 600);
}
```

---

## 5. Qualitaets- und Governance-Gates (Fail-Fast)

1. **Gate 0 (Manifest):** `manifest.json` ist ungueltig, wenn `geo_targets.primary_engines` fehlt oder leer ist.
2. **Gate 2 (Cluster):** Jedes Cluster-Keyword muss auf AI-Overview-Präsenz geprueft sein.
3. **Gate 4a (Briefing):** Ein Briefing wird abgelehnt, wenn:
   - Der Hero Direct-Answer Block fehlt oder mehr als 80 Woerter umfasst.
   - Weniger als 15 Semantic Triples definiert sind.
   - Das JSON-LD Schema kein valides `about` mit Wikidata-URI aufweist.
4. **Gate 4b (HTML):** Jede Landingpage muss semantische Section-IDs aufweisen, die 1:1 mit dem Schema.org Graph harmonieren.
