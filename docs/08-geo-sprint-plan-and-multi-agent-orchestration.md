# 08. GEO-Sprint-Plan & Multi-Agent Coding-Team Orchestrierung

> **Lifecycle: superseded.** Aktuelle Ausfuehrungsfolge: `00_admin/PROJECT_STATE.md`, DEC-0024 und `.hermes/plans/INDEX.md`. OMO bleibt Entwicklungswerkzeug und ist keine Produktkomponente.

**Projekt:** Heartweb Claude Desktop SEO-Workflow Framework  
**Dokument-ID:** PLAN-GEO-SPRINTS-v1.4  
**Autor & Architektur:** Raphael Rechberger  
**Datum:** 17. August 2026  
**Status at capture:** Genehmigter Durchfuehrungsplan fuer den GEO-Upgrade-Zyklus v1.4.0
**Architektur-Basis:** OpenCode OMO (Oh-My-OpenCode) Multi-Agent Ensemble & Hermes Task Delegation  

---

## 1. Das Multi-Agent Coding-Team (Rollen & Zustaendigkeiten)

Fuer eine fehlerfreie, deterministische Umsetzung ohne manuelle Reibungsverluste wird das Entwicklungs-Team in 6 spezialisierte KI-Agenten-Rollen gemaess dem bewaehrten OpenCode OMO Standard unterteilt:

```text
+----------------------------------------------------------------------------------------------------+
|                                DAS HEARTWEB MULTI-AGENT ENSEMBLE                                   |
+----------------------------------------------------------------------------------------------------+
| [SISYPHUS] (Master Orchestrator / Raphael Rechberger Proxy)                                        |
| -> Gesamtkoordination, Sprint-Gating, Task-Delegation, Merge-Reconciliation & Git-Hygiene.         |
+--------------------------------------------------+-------------------------------------------------+
                                                   |
         +-----------------------------------------+-----------------------------------------+
         |                                         |                                         |
         v                                         v                                         v
+-----------------------+                 +-----------------------+                 +-----------------------+
| [ORACLE]              |                 | [PROMETHEUS]          |                 | [HEPHAESTUS]          |
| AI Retrieval & GEO    |                 | Schema & Prompts      |                 | Core Tools & Solver   |
| - 2026 GEO-Audits     |                 | - manifest.schema     |                 | - Solver v1.3.0       |
| - Triple-Validierung  |                 | - Prompts 0, 1, 2, 4a |                 | - Validator CLI       |
| - Information Gain    |                 | - Notion-Handoff      |                 | - Tool-Contracts      |
+-----------------------+                 +-----------------------+                 +-----------------------+
         |                                         |                                         |
         +-----------------------------------------+-----------------------------------------+
                                                   |
         +-----------------------------------------+-----------------------------------------+
         |                                                                                   |
         v                                                                                   v
+-------------------------------------------------+                 +-------------------------------------------------+
| [DAEDALUS] (Frontend & Design System)           |                 | [METIS] (QA & Acceptance Test Auditor)          |
| - `standards/design-system.css` Token-Ausbau   |                 | - Strikte Fail-Fast-Pruefungen                  |
| - Prompts 1c & 4b HTML-Templates                |                 | - Schema-Validierung gegen Test-Fixtures        |
| - Semantische IDs & Microdata                   |                 | - Akzeptanztest-Protokolle                      |
+-------------------------------------------------+                 +-------------------------------------------------+
```

### Detaillierte Rollen-Profile

1. **Sisyphus (Lead Orchestrator):**
   - **Aufgabe:** Haelt den globalen Zustand (`00_admin/PROJECT_STATE.md`), ueberwacht die Sprint-Reihenfolge und stellt sicher, dass kein Schritt ohne erfolgreiches QA-Gate abgeschlossen wird.
   - **Modell-Konfiguration:** Claude 3.5 Sonnet / GPT-4o mit maximaler Kontext- und Planungsdisziplin.

2. **Oracle (Senior GEO & Retrieval Architect):**
   - **Aufgabe:** Validiert alle Entitaets-Definitionen, Wikidata-Mappings, Information-Gain-Metriken und RAG-Extraktionsregeln gegen die Spezifikation `docs/07-geo-architecture-specification.md`.

3. **Prometheus (Schema & Prompt Architect):**
   - **Aufgabe:** Refaktoriert `standards/manifest.schema.json` und die XML-Prompts (`0-kickoff.xml.md`, `1-pillar-identifikation.xml.md`, `1b-seitenarchitektur.xml.md`, `2-cluster-recherche.xml.md`, `4a-content-briefing-und-schema.xml.md`).

4. **Hephaestus (Python & Tool Engineer):**
   - **Aufgabe:** Implementiert die neuen GEO-Content-Typen und Bewertungsfaktoren in `mcp/tools/capacity_matrix_solver.py` sowie die CLI-Erweiterung fuer `mcp/tools/validate_schema_jsonld.py`.

5. **Daedalus (Frontend & CSS Architect):**
   - **Aufgabe:** Erweitert `standards/design-system.css` um `.definition-block`, `.evidence-container` und `.comparison-table` und aktualisiert `prompts/1c-pillar-template.xml.md` und `prompts/4b-landingpage-html.xml.md`.

6. **Metis (QA Auditor & Gating Guardian):**
   - **Aufgabe:** Fuehrt automatisierte Tests gegen Test-Fixtures aus, prueft die Rueckwaertskompatibilitaet und dokumentiert die Ergebnisse in `tests/acceptance-tests.md`.

---

## 2. Der 4-Sprint-Umsetzungsplan (GEO Upgrade v1.4.0)

| Sprint | Fokus | Beteiligte Agenten | Kern-Deliverables & Dateien |
|---|---|---|---|
| **Sprint G1** | **Daten-Standards & Manifest-Schema** | Prometheus, Oracle, Metis | `standards/manifest.schema.json`, `tests/fixtures/sample_manifest.json` |
| **Sprint G2** | **Solver v1.3 & Deterministische Tools** | Hephaestus, Metis | `mcp/tools/capacity_matrix_solver.py`, `validate_schema_jsonld.py` |
| **Sprint G3** | **Prompt-Engineering & Notion-Handoff** | Prometheus, Oracle, Sisyphus | `prompts/0`, `prompts/1`, `prompts/1b`, `prompts/2`, `prompts/4a` |
| **Sprint G4** | **HTML5, Design-System & End-to-End QA** | Daedalus, Hephaestus, Metis | `standards/design-system.css`, `prompts/1c`, `prompts/4b`, Acceptance Tests |

---

## 3. Detaillierte Sprint-Spezifikationen

### Sprint G1: Daten-Standards & Manifest-Schema
- **Lead-Agent:** Prometheus | **Reviewer:** Oracle & Metis
- **Scope:**
  1. `standards/manifest.schema.json` um `geo_targets` (mit Pflichtfeld `primary_engines`) und `entities` (mit `brand_entity`, `brand_wikidata_id`, `core_services`) erweitern.
  2. Rueckwaertskompatibilitaet sicherstellen: Vorhandene `manifest.json` Dateien ohne GEO-Felder duerfen nicht invalidieren (optionale Eigenschaften mit soliden Defaults).
  3. Aktualisierung der Referenz-Fixture `tests/fixtures/sample_manifest.json` um reale Wikidata-IDs (z.B. simCura Pflegedienst).
- **Akzeptanzkriterium (Gate G1):** `jsonschema` Validierung von `sample_manifest.json` laeuft fehlerfrei durch (0 Fehler).

---

### Sprint G2: Solver v1.3 & Deterministische Tools
- **Lead-Agent:** Hephaestus | **Reviewer:** Metis
- **Scope:**
  1. `mcp/tools/capacity_matrix_solver.py` auf Version 1.3.0 aufruesten:
     - Integration von 4 neuen GEO-Content-Typen: `Data-Hub` (5.0h), `Entity-Anchor` (4.0h), `Comparison-Table` (2.0h), `FAQ-Hub` (3.0h).
     - Priorisierungs-Bonus fuer Zeilen mit `Information_Gain_Score > 3`.
  2. `mcp/tools/validate_schema_jsonld.py` um eine vollwertige CLI erweitern (`--input <datei.json|html>` / `--strict`).
- **Akzeptanzkriterium (Gate G2):** Der Solver verteilt 61 Keywords inkl. GEO-Typen deterministisch auf max. 15h/Woche und erzeugt eine valide Verlinkungs-Map.

---

### Sprint G3: Prompt-Engineering & Notion-Handoff
- **Lead-Agent:** Prometheus | **Reviewer:** Oracle & Sisyphus
- **Scope:**
  1. `prompts/0-kickoff.xml.md`: Aufnahme der `<geo_briefing>` Abfrage im Kickoff.
  2. `prompts/1-pillar-identifikation.xml.md`: Ergaenzung der Spalten `Information_Gain_Potential` und `Conversational_Query_Patterns`.
  3. `prompts/2-cluster-recherche.xml.md`: Integration der AI-Overview-Pruefung via AgentSEO.
  4. `prompts/4a-content-briefing-und-schema.xml.md`:
     - Definition des 50 bis 70 Woerter Hero-Definitions-Blocks.
     - Generierung der 15 bis 20 Semantic Triples.
     - Vollstaendiges Schema.org JSON-LD mit Wikidata `about` und `mentions`.
- **Akzeptanzkriterium (Gate G3):** Generiertes Briefing enthaelt valides Notion-Frontmatter, das direkt von Textern ohne technisches Nachfragen verstanden wird.

---

### Sprint G4: HTML5, Design-System & End-to-End QA
- **Lead-Agent:** Daedalus & Metis | **Reviewer:** Sisyphus
- **Scope:**
  1. `standards/design-system.css`: Hinzufuegen der Klassen `.definition-block`, `.evidence-container`, `.comparison-table`.
  2. `prompts/1c-pillar-template.xml.md` & `prompts/4b-landingpage-html.xml.md`: Einbau semantischer Section-IDs und Microdata.
  3. End-to-End Testlauf aller 9 Prompts gegen die Test-Fixtures.
  4. Dokumentation in `tests/acceptance-tests.md` und Update von `README.md` auf Version 1.4.0.
- **Akzeptanzkriterium (Gate G4):** Alle 5 Akzeptanztests bestanden, HTML-Dateien validieren W3C- und Schema.org-konform.

---

## 4. Git- & Branch-Governance

1. **Branch-Name:** `feature/geo-enhancement-v1.4`
2. **Master-Schutz:** Der `master`-Branch bleibt waehrend der Sprint-Ausfuehrung unangetastet.
3. **Commit-Konvention:** Ausschließlich auf **Raphael Rechberger** ausgestellte, strukturierte Commits nach Conventional Commits (`feat(geo): ...`, `test(solver): ...`, `docs(spec): ...`).
4. **Abschluss:** Nach erfolgreichem Gate G4 erfolgt der Merge via Pull Request in `master` und das Tagging von `v1.4.0`.
