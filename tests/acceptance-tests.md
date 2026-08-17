# Akzeptanztests & Validierungs-Nachweis

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows
**Autor:** Raphael Rechberger
**Version:** 1.3.0
**Letzte Ausfuehrung:** 17. August 2026
**Status:** 1 bestanden mit offenem Punkt, 2 teilweise bestanden, 1 nicht ausfuehrbar, 1 nicht bestanden

---

## 1. Testsuite-Uebersicht

| Test-ID | Testfall | Ziel-Komponente | Erwartetes Ergebnis | Ist-Ergebnis (17.08.2026) | Status |
|---|---|---|---|---|---|
| **TEST-01** | Manifest-Schema-Validierung | `standards/manifest.schema.json` | Referenz-Manifest validiert gegen Draft 2020-12. | Schema ist valides Draft 2020-12. Ein Manifest mit `country` und `location_code` validiert mit 0 Fehlern. `tests/fixtures/sample_manifest.json` faellt seit 1.3.0 durch, weil beide Pflichtfelder fehlen. Fixture ist nachzuziehen. | **BESTANDEN mit offenem Punkt** |
| **TEST-02** | Deterministischer Kapazitaets-Solver | `mcp/tools/capacity_matrix_solver.py` | Plan innerhalb des 17-Wochen-Horizonts, keine aktive Woche ueber 15.0h, lokale Pflichtseiten zu 100% in Phase 1 und 2, gemessene Spanne im Plankopf. | 48 Live-Items: 139.0h auf 10 aktive Wochen, Wochen 11 bis 17 leer. Obergrenze gehalten (max 14.75h). Untergrenze verletzt: W10 hat 9.0h. 14 von 14 Pflicht-Standorten verplant. | **TEILWEISE BESTANDEN** |
| **TEST-03** | Schema.org JSON-LD Validierung | `mcp/tools/validate_schema_jsonld.py` | Aufruf prueft eine Datei und endet bei Fehlern mit Exit-Code ungleich 0. | Nicht ausfuehrbar. Das Skript hat kein argparse und keine Eingabe. Der Aufruf gibt "Schema JSON-LD Validator v1.0.0 bereit." aus und endet mit Exit 0. Die Pruefroutinen selbst sind korrekt, aber nur per Import erreichbar. Ein JSON-LD-Array im Script-Tag loest `AttributeError` aus. | **NICHT AUSFUEHRBAR** |
| **TEST-04** | Autarkes Design-System | `standards/design-system.css` | CSS-Tokens rendern ohne externe Fonts oder CDNs, Komponenten decken die Anforderungen aus 1c und 4b ab. | Autarkie bestaetigt: kein `@import`, kein `url()`, keine externen Fonts, 64 Tokens ohne Dubletten und ohne undefinierte `var()`. Komponenten unvollstaendig: keine Media Query, keine NAP-Box, keine Breadcrumb, keine Sticky-CTA, keine Vergleichstabelle, kein Akkordeon. | **TEILWEISE BESTANDEN** |
| **TEST-05** | Strikte Fail-Fast-Plausibilitaet | XML-Prompts 0 bis 4b | Fehlende Pflichtdaten erzeugen sofortigen Stopp mit Error-Code. | 9 von 9 Prompts fuehren jetzt benannte Codes. `0-kickoff` erhielt `ERROR_BRIEFING_INCOMPLETE` und `ERROR_LOCATION_UNKNOWN` in 1.3.0. Offen: `4a-content-briefing-und-schema.xml.md` hat weiterhin keine Abbruchbedingung, obwohl es Live-Metriken in das Notion-Frontmatter schreibt. | **NICHT BESTANDEN fuer 4a** |

---

## 2. Detaillierte Testausfuehrung

### Test 01: Manifest JSON Schema

- **Befehl:** Validierung gegen `standards/manifest.schema.json` mit `jsonschema` und `Draft202012Validator`.
- **Befund:** `check_schema` bestaetigt das Schema selbst. Seit 1.3.0 sind `country` und `location_code` Pflicht und `status` ist in jeder Phase Pflicht. Neu geprueft werden `validated_rows_per_pillar` (Minimum 25 pro Pillar) und `clusters_per_pillar` (8 bis 15).
- **Nachweis der Wirksamkeit:** Ein Versuch, `step_1c_pillar_templates.status` auf den nicht definierten Wert `blocked` zu setzen, wurde vom Schema abgelehnt.
- **Offen:** `additionalProperties` ist weiterhin nirgends gesetzt, Tippfehler in Feldnamen validieren also fehlerfrei durch.

### Test 02: Kapazitaets-Solver auf 48 Live-Datensaetzen

- **Befehl:** `python mcp/tools/capacity_matrix_solver.py --input outputs/2-cluster-themen-agentseo.csv --output outputs/3-plan.md`
- **Datenbasis:** 48 Zeilen mit echten AgentSEO-Metriken, Markt Deutschland, abgefragt am 17.08.2026.
- **Befund:**
  - Gesamt: 48 Content-Stuecke, 139.0 Stunden, 10 aktive Wochen.
  - Wochenverteilung gemessen: W1 14.75, W2 14.75, W3 bis W7 je 14.5, W8 14.0, W9 14.0, W10 9.0. W11 bis W17 leer.
  - Obergrenze 15.0h eingehalten. Untergrenze 10.0h in W10 verletzt (9.0h). Die neue Zeile `Kapazitaets-Messung` im Plankopf weist das jetzt selbst aus.
  - Phasen-Zwischensummen und Wochensummen stimmen exakt, keine Rundungsfehler.
  - Pflicht-Standorte: 14 von 14 verplant, alle in Phase 1 und 2.
  - Score-Formel `Score = (SV / (KD + 1)) * Faktor` mathematisch exakt.
- **Bekannte Grenzen:** Der Greedy-Algorithmus fuellt von vorne. Bei kleinem Datenvolumen bleiben hintere Wochen leer. Nicht platzierbare Items werden ohne Meldung verworfen (`if not placed: pass`), es gibt keine Backlog-Sektion. Fehlende Metriken werden zu 0, ein unbekannter Content-Typ erhaelt pauschal 2.5 Stunden.

### Test 03: JSON-LD Validierung

- **Befehl:** `python mcp/tools/validate_schema_jsonld.py`
- **Beobachtet:** `Schema JSON-LD Validator v1.0.0 bereit.`, Exit-Code 0. Keine Datei- oder stdin-Uebergabe moeglich.
- **Funktionaler Kern geprueft per Import:** Pflichtfeldpruefung fuer Article, LocalBusiness und FAQPage arbeitet korrekt, `@graph`-Rekursion ist richtig implementiert.
- **Fehler:** JSON-LD als Array (`[{...}]`) fuehrt zu `AttributeError: 'list' object has no attribute 'get'`. Ein unbekannter `@type` wird als `valid: True` gemeldet, ohne geprueft zu werden. Ein `JSONDecodeError` wird verschluckt und als "kein Block gefunden" gemeldet.
- **Konsequenz:** Der Quality Gate fuer Schema in Schritt 4a und 4b ist bis zum Nachbau der CLI manuell ueber den Google Rich Results Test zu fahren.

### Test 04: Autarkes Design-System

- **Befehl:** Auswertung aller `:root`-Definitionen und aller `var()`-Referenzen sowie Suche nach externen Abhaengigkeiten.
- **Befund:** 64 Tokens, keine Dubletten, keine undefinierte Referenz, keine externe Abhaengigkeit.
- **Luecken:** keine `@media`-Query, damit ist der Checkpoint "teste die Responsivitaet" aus Prompt 4b nicht bestehbar. Es fehlen NAP-Box, Breadcrumb, Sticky-CTA, Vergleichstabelle, FAQ-Akkordeon und Testimonial-Baustein, die 1c und 4b voraussetzen. Drei Farben sind ausserhalb `:root` hartkodiert.

### Test 05: Fail-Fast in den Prompts

- **Befehl:** Suche nach `ERROR_[A-Z_]+` ueber alle 9 Prompts plus Live-Test von Schritt 2.
- **Befund vor 1.3.0:** `0-kickoff` und `4a` ohne jeden Code.
- **Befund nach 1.3.0:** `0-kickoff` hat `ERROR_BRIEFING_INCOMPLETE` und `ERROR_LOCATION_UNKNOWN`. Schritt 2 hat zusaetzlich `ERROR_LOCATION_UNKNOWN`, `ERROR_LOCATION_MISMATCH` und `ERROR_INSUFFICIENT_CLUSTER_COVERAGE`.
- **Live-Nachweis der Wirksamkeit:** Von 64 abgefragten Keywords gab der Datenlieferant 48 zurueck. Die 16 fehlenden wurden verworfen und protokolliert, nicht geschaetzt. Darunter `pflegedienst frankfurt westend`, ein Stadtteil aus dem Manifest ohne belegbare Nachfrage.
- **Offen:** `4a` hat weiterhin keine Abbruchbedingung.

---

## 3. Offene Punkte aus dieser Ausfuehrung

| Nr | Punkt | Betroffene Datei |
|---|---|---|
| 1 | CLI fuer den JSON-LD-Validator nachbauen, Array-Support, Exit-Code ungleich 0 | `mcp/tools/validate_schema_jsonld.py` |
| 2 | Backlog-Ausweis statt stilles Verwerfen, Untergrenze durchsetzen oder Restlast umverteilen (W10 liegt bei 9.0h), `ERROR_DATA_INCOMPLETE` bei fehlenden Metriken | `mcp/tools/capacity_matrix_solver.py` |
| 3 | Fehlercodes in Schritt 4a | `prompts/4a-content-briefing-und-schema.xml.md` |
| 4 | `additionalProperties: false` im Schema | `standards/manifest.schema.json` |
| 5 | Media Queries und fehlende Komponenten | `standards/design-system.css` |
| 6 | `country` und `location_code` in die Fixture nachziehen | `tests/fixtures/sample_manifest.json` |
| 7 | Ausfuehrbaren Testrunner anlegen, damit diese Tabelle nicht von Hand gepflegt werden muss | `tests/` |

---

## 4. Reproduzierbarkeit

Es existiert kein Testrunner. Alle Ergebnisse oben wurden am 17.08.2026 manuell ausgefuehrt und
protokolliert. Bis Punkt 7 erledigt ist, gilt dieses Dokument als Momentaufnahme und muss bei jeder
Aenderung an Solver, Validator, Schema oder Prompts erneut ausgefuehrt werden.
