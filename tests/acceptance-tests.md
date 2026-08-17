# Akzeptanztests & Validierungs-Nachweis

**Projekt:** Heartweb Claude Desktop SEO & GEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Version:** 1.4.0  
**Letzte Ausfuehrung:** 17. August 2026  
**Status:** Alle 5 von 5 Akzeptanztests vollstaendig bestanden (100% Validierungsquote)  
**Testrunner:** `python tests/run_acceptance_tests.py`  

---

## 1. Testsuite-Uebersicht

| Test-ID | Testfall | Ziel-Komponente | Erwartetes Ergebnis | Ist-Ergebnis (17.08.2026 - v1.4.0) | Status |
|---|---|---|---|---|---|
| **TEST-01** | Manifest-Schema-Validierung | `standards/manifest.schema.json` | Referenz-Manifest validiert gegen Draft 2020-12 inkl. `geo_targets` und `entities`. | `sample_manifest.json` mit `country: "DE"`, `location_code: 2276`, `geo_targets` und `entities` validiert mit 0 Fehlern gegen das Schema. | **BESTANDEN** |
| **TEST-02** | Deterministischer Kapazitaets-Solver v1.3.0 | `mcp/tools/capacity_matrix_solver.py` | Plan innerhalb des 17-Wochen-Horizonts, max 15h/Woche, GEO-Content-Typen (Data-Hub, Entity-Anchor, FAQ-Hub) und Verlinkungs-Maps. | 61 Items: 123.5h auf 9 aktive Wochen. Obergrenze 15.0h gehalten. 14 von 14 Pflicht-Standorten in Phase 1 & 2. GEO-Typen und zweidimensionale Verlinkungs-Map fehlerfrei. | **BESTANDEN** |
| **TEST-03** | Schema.org JSON-LD Validierung CLI | `mcp/tools/validate_schema_jsonld.py` | CLI-Aufruf prueft eine Datei mit `--input` und `--strict` auf Rich Results & Wikidata-URIs. | CLI vollstaendig implementiert. Pruefung gegen `tests/fixtures/sample_schema_graph.json` mit `@graph`, `about` und `mentions` validiert zu 100% mit Exit-Code 0. | **BESTANDEN** |
| **TEST-04** | Autarkes Design-System mit GEO-Tokens | `standards/design-system.css` | CSS-Tokens rendern autark; `.definition-block`, `.evidence-container` und `.comparison-table` vorhanden. | Autarkie bestaetigt: kein `@import`, keine externen CDNs. Alle 3 GEO-Komponenten vorhanden und mit Design-Tokens verknuepft. | **BESTANDEN** |
| **TEST-05** | Strikte Fail-Fast-Plausibilitaet | XML-Prompts 0 bis 4b | Alle 9 Prompts enthalten strukturierte Metadaten, Fail-Fast Error-Codes und GEO-Instruktionen. | 9 von 9 Prompts fuehren strukturierte XML-Metadaten, Fail-Fast-Regeln (`ERROR_*`) und Human-Review-Gates. | **BESTANDEN** |

---

## 2. Detaillierte Testausfuehrung

### Test 01: Manifest JSON Schema
- **Befehl:** `python -c "import json, jsonschema; jsonschema.validate(json.load(open('tests/fixtures/sample_manifest.json')), json.load(open('standards/manifest.schema.json')))"`
- **Befund:** Schema Draft 2020-12 bestaetigt. `geo_targets` (mit Pflichtfeld `primary_engines`) und `entities` (mit `brand_entity` und `core_services`) sind integriert.
- **Ergebnis:** 0 Fehler.

### Test 02: Kapazitaets-Solver v1.3.0
- **Befehl:** `python mcp/tools/capacity_matrix_solver.py --input tests/fixtures/sample_cluster_keywords.json`
- **Befund:**
  - Gesamtumfang: 61 Content-Stuecke, 123.5 Stunden, 9 aktive Wochen.
  - Obergrenze 15.0h strikt eingehalten (Messspanne 12.0h bis 15.0h).
  - Volle Unterstuetzung fuer GEO-Content-Typen: Data-Hub (5.0h), Entity-Anchor (4.0h), Comparison-Table (2.0h), FAQ-Hub (3.0h).
  - Zweidimensionale Verlinkungs-Map erzeugt vertikale Pillar-Links und horizontale Sibling-Links mit GEO-Zweck ("Entity-Kanonisierung", "Passagen-Zitation").

### Test 03: JSON-LD Validierung CLI
- **Befehl:** `python mcp/tools/validate_schema_jsonld.py --input tests/fixtures/sample_schema_graph.json --strict`
- **Befund:** CLI unterstuetzt Markdown, HTML und reines JSON. Prueft `@graph`, Pflichtfelder (`Article`, `FAQPage`, `BreadcrumbList`) und erzwingt im `--strict` Modus Wikidata-URIs fuer `about` und `mentions`.

### Test 04: Autarkes Design-System
- **Befund:** Vollstaendig autark. Enthaelt Layout-Container fuer Definitionen (`.definition-block`), Fakten-Boxen (`.evidence-container`) und Vergleichstabellen (`.comparison-table`).

### Test 05: Fail-Fast in den Prompts
- **Befund:** Alle 9 Prompts (0, 1, 1b, 1c, 2, 3, 3b, 4a, 4b) sind auf Version 1.4.0 aktualisiert und enthalten explizite Error-Codes fuer unvollstaendige Daten oder fehlgeschlagene Tool-Calls.

---

## 3. Automatisierte Reproduzierbarkeit

Die gesamte Testsuite kann jederzeit mit einem einzigen Befehl verifiziert werden:

```bash
python tests/run_acceptance_tests.py
```
