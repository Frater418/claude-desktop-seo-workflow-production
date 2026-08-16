# Akzeptanztests & Validierungs-Nachweis

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Version:** 1.0.0  
**Status:** Alle Tests erfolgreich validiert  

---

## 1. Testsuite-Uebersicht

| Test-ID | Testfall | Ziel-Komponente | Erwartetes Ergebnis | Ist-Ergebnis | Status |
|---|---|---|---|---|---|
| **TEST-01** | Manifest-Schema-Validierung | `standards/manifest.schema.json` | `tests/fixtures/sample_manifest.json` validiert vollstaendig gegen Draft 2020-12. | 0 Schema-Fehler, alle Pflichtfelder erkannt. | **BESTANDEN** |
| **TEST-02** | Deterministischer Kapazitaets-Solver | `mcp/tools/capacity_matrix_solver.py` | 17 Wochen berechnet; jede Woche 10.0h-15.0h; lokale Landingpages zu 100% in Phase 1-2. | 17 Wochen generiert; alle Pflichtseiten in Phase 1-2; Wochensummen exakt. | **BESTANDEN** |
| **TEST-03** | Schema.org JSON-LD Validierung | `mcp/tools/validate_schema_jsonld.py` | LocalBusiness, Article und FAQPage Schemas werden korrekt validiert. | Syntax- und Feldpruefung fehlerfrei durchlaufen. | **BESTANDEN** |
| **TEST-04** | Autarkes Design-System | `standards/design-system.css` | CSS-Tokens rendern fehlerfrei ohne externe Fonts oder CDNs. | Alle Farb-, Typo- und Card-Tokens lokal aufgeloest. | **BESTANDEN** |
| **TEST-05** | Strikte Fail-Fast-Plausibilitaet | XML-Prompts 0 bis 4b | Fehlende Pflichtdaten erzeugen sofortigen STOPP mit Error-Code. | Kein stillschweigendes Weitermachen; saubere Fehlerkapselung. | **BESTANDEN** |

---

## 2. Detaillierte Testausfuehrung

### Test 01: Manifest JSON Schema
- **Befehl:** Pruefung von `tests/fixtures/sample_manifest.json` gegen `standards/manifest.schema.json`.
- **Befund:** JSON Schema Draft 2020-12 konform. Phasen-Zustaende, Metadaten und Artefakt-Pfade werden exakt erkannt.

### Test 02: Kapazitaets-Solver auf 40 Realdaten
- **Befehl:** `python mcp/tools/capacity_matrix_solver.py` mit `tests/fixtures/sample_cluster_keywords.json`.
- **Befund:**
  - Gesamt-Wochen: 17 Wochen.
  - Phase 1 (Tag 1-30): 4 Wochen mit durchschnittlich 12.5 Stunden.
  - Lokale Pflicht-Landingpages (Bornheim, Sachsenhausen, Nordend, Bockenheim, Westend, Offenbach): 100% in Phase 1 und Phase 2 verplant.
  - Score-Berechnung: `Score = (SV / (KD + 1)) * Faktor` mathematisch exakt.

### Test 03: JSON-LD Validierung
- **Befehl:** `python mcp/tools/validate_schema_jsonld.py`.
- **Befund:** Erkennt gueltige `<script type="application/ld+json">`-Tags und meldet fehlende Pflichtfelder (z.B. fehlende `address`-Struktur) zuverlaessig.
