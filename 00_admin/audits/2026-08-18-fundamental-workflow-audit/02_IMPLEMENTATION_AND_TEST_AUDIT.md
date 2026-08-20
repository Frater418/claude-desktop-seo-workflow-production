# Lane 2: Implementation and Test Audit

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Auditmodus: Bestehende Source-Dateien read-only untersucht
- Scope: Deterministische Tools, Gateway, JSON-Schemas, Tool-Vertraege, Tests, Fixtures, Changelog und Candidate-Diff

## 1. Executive Verdict

**Verdict: No-Go fuer einen automatisierten Produktionsbetrieb.**

Die Candidate-Implementierung hat brauchbare Bausteine: ein nachvollziehbarer Solver, eine verwendbare CLI-Oberflaeche fuer JSON-LD und einen fail-fast-orientierten AgentSEO-Kern. Die Produktionseigenschaften aus README und AGENTS werden jedoch nicht durchgesetzt. Insbesondere umgeht die konfigurierte Runtime den Gateway, die State-Machine laesst fachlich unzulaessige `completed`-Zustaende zu, der JSON-LD-Validator bestaetigt semantisch ungueltige Daten und die Acceptance-Suite ist weder in dieser Ausfuehrungsumgebung reproduzierbar noch ausreichend aussagekraeftig.

## 2. Scope und gelesene Evidenz

Gelesen wurden:

- `AGENTS.md`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md`
- `mcp/tools/capacity_matrix_solver.py`
- `mcp/tools/validate_schema_jsonld.py`
- `services/agentseo_gateway/core.py`
- alle drei Dateien in `mcp/tool-contracts/`
- `standards/manifest.schema.json`, `standards/location-codes.json`
- `mcp/claude_desktop_config.template.json`
- `tests/run_acceptance_tests.py`, `tests/test_agentseo_location_guard.py`, `tests/test_prompt0_contract.py` und die referenzierten Fixtures
- `tests/acceptance-tests.md`, `CHANGELOG.md`, `00_admin/PROJECT_STATE.md`
- `scripts/generate_sample_keywords.py`
- Git-Status und Candidate-Diff-Pruefung

Ausgefuehrte sichere Checks:

| Check | Beobachtung | Aussagegrenze |
|---|---|---|
| `python3 tests/run_acceptance_tests.py` | 6 von 7 Checks bestanden. TEST-01 scheitert mit `No module named 'jsonschema'`. | Der beworbene Ein-Befehl-Nachweis ist ohne dokumentierte Abhaengigkeit nicht reproduzierbar. |
| `python3 -m unittest discover -s tests -v` | 17 Tests bestanden, davon 8 Gateway- und 9 Prompt-0-Stringtests. | Belegt nur diese Candidate-Unit-Tests, keine Provider- oder Workflow-Integration. |
| `python3 -m compileall -q mcp/tools services tests scripts` | Erfolgreich ohne Ausgabe. | Belegt nur Syntax-Kompilierbarkeit. |
| Direkter Aufruf `validate_text(..., strict_geo=True)` mit Article, `about: [{}]` und ungueltigem Datum | Rueckgabe: `{'valid': True, 'blocks_found': 1, 'errors': []}`. | Reproduzierter semantischer False-Green des Validators. |
| Direkter Aufruf `solve_capacity_plan([])` | Liefert 17 leere Wochen statt eines Fehlercodes. | Reproduzierter Fail-Fast-Verstoss fuer leere Eingabe. |

Git-Baseline und Candidate sind getrennt zu beurteilen: `git status --short` zeigt umfassende uncommitted Aenderungen, inklusive neuer `services/`, neuer Tests und des gesamten Audit-Ordners. Die Gateway- und Unit-Test-Befunde betreffen daher Candidate-Code, nicht nachgewiesenen Git-Baseline-Produktionsstand.

## 3. Was wirklich stark ist

### Fakten

- `services/agentseo_gateway/core.py:46` bis `96` validiert die Standorttabelle fail-fast. Die Unit-Tests pruefen unbekannte Laender und fehlende Pflichtwerte in `tests/test_agentseo_location_guard.py:141` bis `156`.
- `services/agentseo_gateway/core.py:220` bis `258` lehnt abweichende Provider-Standortcodes und -namen ab und bewahrt die bekannte ISO-Korrektur als Warnung. Das wird in `tests/test_agentseo_location_guard.py:33` bis `114` abgedeckt.
- `services/agentseo_gateway/core.py:360` bis `398` erzwingt beim eigenen REST-Pfad `sync=false`, pollt asynchron und behandelt fehlende Job-ID, Fehlstatus und Timeout explizit.
- `mcp/tools/capacity_matrix_solver.py:164` bis `181` gibt nicht platzierbare Items als `unplaced` aus, statt sie wie im alten Changelog beschrieben zu verwerfen.
- `mcp/tools/validate_schema_jsonld.py:145` bis `176` besitzt im Candidate eine echte CLI mit Exit-Code 0 oder 1.

### Interpretation

Diese Bausteine sind eine gute Grundlage fuer einen transportneutralen Gateway. Sie werden aber nicht als verbindliche Produktionsgrenze eingesetzt und die vorhandenen Tests pruefen mehrheitlich nur einen einzelnen positiven Fixture-Pfad.

## 4. Befunde nach Prioritaet

### P0

#### P0-1: Die produktive Desktop-Konfiguration umgeht den einzigen implementierten Geo- und Async-Gateway

**Fakten:**

- Der Gateway erzwingt die Zielmarktfelder nur beim Payload-Aufbau in `services/agentseo_gateway/core.py:134` bis `141` und `164` bis `170`.
- Die konfigurierte Desktop-Runtime ruft dagegen AgentSEO direkt ueber `mcp-remote` auf: `mcp/claude_desktop_config.template.json:3` bis `12`.
- Es gibt keine MCP-Server- oder HTTP-Entrypoint-Datei fuer `AgentSEOClient`; `core.py` endet mit Methoden auf `AgentSEOClient` bei `services/agentseo_gateway/core.py:400` bis `446`.
- Die Tool-Vertraege selbst verlangen fuer Keyword und SERP nur `keywords` beziehungsweise `keyword`: `mcp/tool-contracts/agentseo_keyword_enricher.json:10` und `mcp/tool-contracts/serp_gap_analyzer.json:10`. Sie machen `location_code`, `language` und `sync=false` nicht verbindlich.

**Interpretation:**

Der operative Pfad kann die in AGENTS geforderten Marktparameter und die asynchrone Ausfuehrung ohne Gateway-Validierung an den Provider senden. Damit kann ein falscher Suchmarkt erfolgreich durch den Workflow laufen. Die Unit-Tests beweisen nur den nicht eingebundenen Candidate-Kern.

**Empfehlung:**

Expose den Gateway als alleinigen transportneutralen Service und lasse n8n, UI und MCP ausschliesslich diesen Service aufrufen. Entferne den direkten Provider-MCP-Pfad aus dem Produktions-Template oder markiere ihn als lokale Diagnosekonfiguration.

#### P0-2: Das Manifest-Schema erzwingt weder Schrittfolge noch Abschluss-Gates

**Fakten:**

- Die Phasen erlauben jeweils `completed`, verlangen aber nur `status`, zum Beispiel `step_1_pillar_identification` in `standards/manifest.schema.json:362` bis `396`, Schritt 2 in `450` bis `495` und Schritt 3 in `497` bis `526`.
- Die als maschinenpruefbar bezeichneten Mengenfelder sind optional: `clusters_per_pillar` in `384` bis `392`, `validated_rows_per_pillar` in `484` bis `491`.
- Es gibt keine JSON-Schema-Conditional, die bei `status: completed` Abschlusszeit, Artefakt, Gate-Freigabe, Mengenwerte oder den vorherigen Schritt verlangt.
- `country` ist zwar auf drei Werte begrenzt und `location_code` ist eine positive Zahl (`617` bis `630`), aber keine Regel bindet den Code an das Land aus `location-codes.json`.

**Interpretation:**

Ein Manifest kann schema-valide sein, obwohl Schritt 2 mit null oder fehlender Coverage abgeschlossen wird, ein falscher Geo-Code gesetzt ist oder Schritt 4 vor seinen Vorbedingungen abgeschlossen wird. Dies widerspricht direkt dem Abschlussverbot in `AGENTS.md:58` und kann falsche Kundenoutputs als freigegeben markieren.

**Empfehlung:**

Implementiere eine versionierte State-Transition-Validierung ausserhalb des JSON Schema, inklusive atomischer Transition, erwarteter vorheriger Revision, Gate-Evidenz, Artefakt-Hash und Mengenregeln. Das JSON Schema soll anschliessend die stabile Dokumentform mit `additionalProperties: false` an jeder Vertragsgrenze absichern.

### P1

#### P1-1: `--strict` bestaetigt semantisch ungueltiges JSON-LD als valide

**Fakten:**

- Die strikte GEO-Pruefung meldet nur dann einen Fehler, wenn `sameAs` vorhanden, aber falsch ist: `mcp/tools/validate_schema_jsonld.py:105` bis `122`. Ein `about`-Objekt ohne `sameAs` wird akzeptiert.
- `datePublished`, URLs, Adressen, `@context`, verlinkte Graph-Referenzen und bekannte Rich-Result-spezifische Mindestfelder werden nicht typisiert oder semantisch geprueft. Die Pflichtfeldtabelle beschraenkt sich auf Existenz und Truthiness in `19` bis `31` sowie `85` bis `103`.
- Unbekannte `@type`-Werte werden ohne Fehler durchgelassen, weil die Schleife in `85` bis `90` nur bekannte Typen bearbeitet.
- Der reproduzierte direkte Aufruf mit `datePublished: "bad"` und `about: [{}]` lieferte mit `strict_geo=True` `valid: True`.

**Interpretation:**

Die Behauptung eines Google-Rich-Result-Validators in `mcp/tools/validate_schema_jsonld.py:7` bis `10`, README und `tests/acceptance-tests.md:18` wird durch die Implementierung nicht gedeckt. Besonders bei YMYL-Briefings kann ein bestandenes Gate den Betrieb irrefuehren.

**Empfehlung:**

Trenne syntaktische Extraktion, Schema.org-Strukturvalidierung und typenbezogene Rich-Result-Profile. `--strict` muss fehlende Wikidata-URIs, ungueltige Datums- und URL-Formate, leere Entitaetsobjekte sowie unbekannte Produktivtypen mit nicht-null Exit-Code ablehnen. Google Rich Results muss als externe Integrationspruefung ausgewiesen werden, solange kein offizieller Validator eingebunden ist.

#### P1-2: Solver verletzt Fail-Fast und die Mindestkapazitaet, ohne den Prozess zu stoppen

**Fakten:**

- Bei leerer Eingabe gibt `solve_capacity_plan` in `mcp/tools/capacity_matrix_solver.py:108` bis `110` eine Liste leerer Wochen zurueck, statt einen expliziten Fehler zu werfen.
- Fehlende Metriken werden durch `or 0` ersetzt: Suchvolumen und Difficulty in `114` bis `115`, Information Gain und Entity Density in `119` bis `120`.
- Unbekannte Content-Typen erhalten mit `EFFORT_WEIGHTS.get(c_type, 2.5)` in `128` einen stillen Aufwand-Fallback.
- Der Mindestwert wird lediglich gemessen und als Textwarnung ausgegeben: `generate_markdown_plan` setzt `ok` in `238` und schreibt bei Verfehlung nur `ACHTUNG` in `240` bis `242`.

**Interpretation:**

Der Solver kann einen erfolgreich geschriebenen Plan aus unvollstaendigen oder semantisch unbekannten Datensaetzen produzieren. Das ist mit der Fail-Fast-Doktrin unvereinbar und entwertet die Aussage eines deterministischen Produktionsplans.

**Empfehlung:**

Definiere ein versioniertes Input-Schema. Leere Listen, fehlende oder negative Metriken, unbekannte Content-Typen und nicht einhaltbare Zielband-Anforderungen muessen einen strukturierten Fehler und Exit-Code ungleich 0 erzeugen. Wenn Untergrenzen nur Kapazitaetsziele sind, muessen sie aus Vertrag und Dokumentation entfernt werden statt als Gate formuliert zu sein.

#### P1-3: Tool-Vertraege und Gateway-Code beschreiben verschiedene APIs

**Fakten:**

- Der SERP-Vertrag nennt Tool `agentseo_content_serp_outline` und Endpoint `/content/serp-outline` in `mcp/tool-contracts/serp_gap_analyzer.json:5` bis `7`.
- Der Gateway sendet stattdessen an `/analyze/serp` in `services/agentseo_gateway/core.py:437`.
- Der Keyword-Vertrag hat nur `keywords` als required und bietet harte DE-defaults an (`agentseo_keyword_enricher.json:10` bis `24`), waehrend der Gateway ein voraufgeloestes `target` erwartet und keinen Default erzeugt (`core.py:114` bis `141`).
- Kein Test validiert Request oder Response gegen einen Tool-Vertrag. `tests/test_agentseo_location_guard.py` prueft nur Python-Dictionaries.

**Interpretation:**

Ein Consumer kann laut Vertrag einen Request erzeugen, den der Gateway nicht als sichere Produktionsoperation behandelt. Endpoint- und Payload-Drift wird erst bei kostenpflichtigem Providerkontakt sichtbar.

**Empfehlung:**

Generiere Gateway-Request- und Response-Modelle aus einer kanonischen, providerneutralen Contract-Version. Fuege Contract-Tests gegen jedes Gateway-Operationsergebnis und einen Provider-Stub hinzu. Der Contract muss `location`, `location_code`, `language`, Async-Verhalten, Fehlerform, Run-ID und Idempotency-Key verpflichtend machen.

### P2

#### P2-1: Asynchrone Provider-Jobs besitzen keine Idempotenz, Persistenz, Retry-Strategie oder Kostenkontrolle

**Fakten:**

- `_queue_and_poll` erzeugt bei jedem Aufruf ein neues POST: `services/agentseo_gateway/core.py:360` bis `365`.
- Es wird weder ein Idempotency-Key noch Run-ID, Request-Hash, Budget oder persistierter Jobstatus uebergeben beziehungsweise gespeichert. Der Rueckgabewert bleibt fluechtig in `keyword_metrics` und `serp_analysis` bei `400` bis `446`.
- Transiente HTTP- und Netzwerkfehler werden direkt abgebrochen (`324` bis `339`), ohne begrenzte Retry-Policy oder Remediation-Daten.

**Interpretation:**

UI- und n8n-Retries koennen kostenpflichtige Duplicate-Jobs erzeugen und Resume nach Prozessabbruch kann nicht sicher an einen vorhandenen Provider-Job anknuepfen.

**Empfehlung:**

Fuege eine speicherbare Job-Envelope mit `run_id`, Idempotency-Key, Request-Hash, Provider-Job-ID, Status, Kostenbudget und Retry-Zaehler ein. Ein identischer Auftrag muss denselben laufenden oder abgeschlossenen Job zurueckgeben.

#### P2-2: Die Acceptance-Suite prueft fast nur positive synthetische Fixtures und deckt den Gateway nicht ab

**Fakten:**

- Der Solver-Test prueft nur drei String-Fragmente im stdout: `tests/run_acceptance_tests.py:34` bis `44`.
- Der Validator-Test prueft nur eine positive Graph-Fixture und das Wort `[BESTANDEN]`: `46` bis `54`.
- Prompt-Fail-Fast wird nur durch XML-Substring-Pruefungen bewertet: `64` bis `71`.
- Die Gateway-Testdatei wird nicht durch die Acceptance-Liste in `108` bis `116` aufgerufen, obwohl `unittest discover` sie separat ausfuehrt.
- Die Fixtures behaupten keine reale Provider-Antwort oder Kundenbriefing-Trace. Der Changelog bezeichnet die Keyword-Fixture selbst als synthetisch in `CHANGELOG.md:68`.

**Interpretation:**

Gruene Acceptance-Tests beweisen nicht die reale Workflow-Sequenz, Provider-Contract-Kompatibilitaet, Resume-Verhalten, Multi-Markt-Unterstuetzung oder semantische Gueltigkeit. Sie sind Smoke-Tests und duerfen nicht als Produktionsabnahme verwendet werden.

**Empfehlung:**

Etabliere getrennte Unit-, Contract-, Integration- und Acceptance-Suites. Acceptance muss alle neun Schritte auf einem anonymisierten realen Kundenfall mit Provider-Stubs, negativen Fixtures, Artefakt-Validierung und zustandsbehaftetem Resume durchlaufen.

#### P2-3: Schema-Validierung und Manifest-Vertrag lassen unbekannte Felder und ungueltige URI-Formate passieren

**Fakten:**

- `standards/manifest.schema.json` setzt an keiner Objektgrenze `additionalProperties: false`, zum Beispiel Root `5` bis `33`, `phases` `326` bis `583` und `entities` `667` bis `720`.
- Das Acceptance-Programm ruft `jsonschema.validate` ohne `FormatChecker` auf: `tests/run_acceptance_tests.py:24` bis `32`. URI- und date-time-Formate im Schema, etwa `domain` bei `48` bis `52` und `created_at` bei `280` bis `286`, werden damit nicht geprueft.

**Interpretation:**

Tippfehler in Status- oder Artefaktfeldern und ungueltige URLs beziehungsweise Zeitstempel koennen unbemerkt in die Single Source of Truth gelangen.

**Empfehlung:**

Lehne unbekannte Vertragsfelder an Boundaries ab und fuehre FormatChecker-basierte Negativtests aus. Erweiterungen brauchen eine explizite `schema_version` und eine Migration.

### P3

#### P3-1: Test- und Release-Dokumentation ist widerspruechlich und nicht reproduzierbar

**Fakten:**

- `tests/acceptance-tests.md:7` behauptet 5 von 5 Tests, der Runner definiert sieben Tests in `tests/run_acceptance_tests.py:108` bis `116`.
- Der dokumentierte Befehl benutzt `python` in `tests/acceptance-tests.md:55` bis `57`, obwohl diese Ausfuehrungsumgebung nur `python3` hat. Ausserdem ist `jsonschema` nicht als installierbare Projektabhaengigkeit dokumentiert, wodurch der direkte Runner bei TEST-01 scheiterte.
- `CHANGELOG.md:76` sagt, der JSON-LD-Validator habe keine CLI, waehrend die CLI in `mcp/tools/validate_schema_jsonld.py:145` bis `176` implementiert ist.
- `CHANGELOG.md:77` beschreibt stille Solver-Verwerfung, die Candidate-Funktion inzwischen als `unplaced` ausgibt (`capacity_matrix_solver.py:164` bis `181`).
- `00_admin/PROJECT_STATE.md:7` nennt Version 1.3.0 in Arbeit, README und Runner nennen 1.4.0.

**Interpretation:**

Ein Operator kann weder den korrekten Produktstand noch den korrekten Nachweis bestimmen. Dies ist ein False-Green-Risiko fuer jede formale Abnahme.

**Empfehlung:**

Verwalte Version, Abhaengigkeiten, Testanzahl, reale Ausfuehrung und offene Punkte aus einer Release-Quelle. Ein CI-Job muss dokumentierte Befehle in einer frischen Umgebung ausfuehren und das Testprotokoll erzeugen.

#### P3-2: Der Fixture-Generator schreibt auf obsolete, nicht kanonische Pfade

**Fakten:**

- `scripts/generate_sample_keywords.py:107` bis `111` schreibt gleichzeitig in zwei absolute Windows-Pfade, darunter `Documents\\Projekte\\Hermes\\04_projects\\active`, statt in den im AGENTS geforderten Kundenpfad.
- `AGENTS.md:20` nennt den verbindlichen Kundenpfad `Documents\\Projekte\\Heartweb\\Kunden\\<kunde-slug>`.

**Interpretation:**

Der Generator ist nicht portabel und kann Fixtures am falschen Ort erzeugen. Er ist kein reproduzierbarer Bestandteil der aktuellen Repository-Tests.

**Empfehlung:**

Akzeptiere einen expliziten Ausgabepfad, verwende repository-relative Default-Pfade nur fuer Testfixtures und teste den Generator in einem temporären Verzeichnis ausserhalb des Kunden-Workspace.

## 5. Widersprueche und False-Green-Risiken

| Claim | Konkrete Gegen-Evidenz | Risiko |
|---|---|---|
| "Produktionsstandard aktiv & validiert" in `README.md:7` | P0-1 bis P2-3 zeigen fehlende Runtime-Anbindung, State-Gates und reale Integrationsbeweise. | Unberechtigte Produktionsfreigabe. |
| Striktes Fail-Fast in `AGENTS.md:53` | Solver setzt fehlende Werte auf 0 und akzeptiert leere Eingabe: `capacity_matrix_solver.py:108` bis `120`. | Priorisierung und Plan aus unvollstaendigen Daten. |
| Mengenregeln werden maschinell geprueft in `AGENTS.md:58` | Felder sind optional und nicht an `completed` gebunden: `manifest.schema.json:384` bis `392`, `484` bis `491`. | Unvollstaendige Research-Phasen gelten als abgeschlossen. |
| Jeder AgentSEO-Aufruf mit drei Zielmarktfeldern und async in `AGENTS.md:56` bis `57` | Direkter MCP-Providerpfad in `mcp/claude_desktop_config.template.json:3` bis `12`; Contracts machen die Felder nicht required. | Falscher Markt, Timeout oder nicht nachvollziehbare Calls. |
| "Google Rich Results & GEO" Validator in `validate_schema_jsonld.py:146` | Direkter strict-Aufruf akzeptierte leeres `about` und ungueltiges Datum. | Falsche Schema-Freigaben. |
| "Alle 5 von 5" in `tests/acceptance-tests.md:7` | Runner enthaelt 7 Tests und lief lokal nur mit 6 von 7. | Dokumentierter Testnachweis ist veraltet. |

## 6. Sollarchitektur und Korrekturreihenfolge

1. Definiere zuerst den kanonischen, providerneutralen Workflow-Contract: Run-ID, Mandanten-ID, State-Revision, Input-Hash, Idempotency-Key, Zielmarkt-Tripel, Fehlerform, Kostenbudget und Artefakt-Evidenz.
2. Implementiere den Gateway als einzigen Netzwerkrand mit Provideradapter. UI, n8n und MCP muessen gegen denselben Contract arbeiten. Provider-Endpoints, Tool-Namen und Payloads duerfen nur im Adapter liegen.
3. Implementiere eine persistierbare State-Machine mit compare-and-swap-Transition und Gate-Validator. Das Manifest ist Snapshot und Audit-Artefakt, nicht alleinige Ausfuehrungslogik.
4. Verhaerte die beiden deterministischen Tools gegen unvollstaendige oder unbekannte Eingaben. Jeder fachliche Gate-Verstoss braucht einen stabilen Fehlercode und Exit-Code ungleich 0.
5. Ersetze positive Fixture-Smoke-Tests durch Contract- und negative Tests, danach einen vollstaendigen Acceptance-Trace mit Provider-Stubs und mindestens einem anonymisierten realen Kundenfall.
6. Generiere Changelog, Testnachweis und Release-Status aus der tatsaechlich ausgefuehrten CI-Pipeline.

## 7. Maschinenpruefbare Acceptance Criteria

| ID | Kriterium | Nachweis |
|---|---|---|
| AC-01 | Kein Produktionsaufruf an AgentSEO kann ohne `location`, `location_code`, `language`, `run_id` und Idempotency-Key ausgefuehrt werden. | Contract-Test fuer Keyword und SERP mit je fehlendem Feld erwartet strukturierten Fehler. Positivtest prueft den serialisierten Request. |
| AC-02 | Ein identischer Gateway-Auftrag erzeugt hoechstens einen Provider-POST und Resume pollt dieselbe Job-ID. | Stub-Integrationstest mit zweimaliger Einreichung und simuliertem Prozessneustart. |
| AC-03 | Falscher Provider-Standort, fehlende Standortmetadaten, ungueltiger Jobstatus, Timeout und HTTP-429 beziehungsweise 5xx erzeugen definierte Fehler- oder Retry-Ergebnisse ohne Duplicate-Job. | Parametrisierter Gateway-Integrationstest gegen lokalen Stub. |
| AC-04 | Ein Manifest mit `completed` in Schritt 1 oder 2 ohne Mengenwerte, Gate oder Vorphase wird abgelehnt. Ein abweichender Country-Code wird abgelehnt. | Negative State-Transition-Tests mit erwarteten Fehlercodes. |
| AC-05 | Solver lehnt leere Liste, fehlende oder negative Metriken, unbekannten Content-Typ und nicht einhaltbares Zielband mit Exit-Code ungleich 0 ab. | CLI-Tests mit negativen JSON- und CSV-Fixtures. |
| AC-06 | `validate_schema_jsonld.py --strict` lehnt fehlendes Wikidata-`sameAs`, leeres `about`, ungueltige Datums- und URL-Formate, unbekannte Produktivtypen und fehlerhafte Rich-Result-Unterstrukturen ab. | Negative CLI-Fixtures mit Exit-Code 1 und maschinenlesbaren Fehlercodes. |
| AC-07 | Der Contract ist die einzige Quelle fuer Toolname, Endpoint und Payload. | Consumer-Driven-Contract-Test, der Gateway-Requests und -Responses gegen die kanonische Schema-Version validiert. |
| AC-08 | Eine frische Umgebung installiert alle dokumentierten Abhaengigkeiten und fuehrt die komplette Suite mit `python3` aus. | CI-Job mit Lockfile oder requirements-Datei, der den dokumentierten Testreport erzeugt. |
| AC-09 | Ein Acceptance-Trace durchlaeuft den Initiallauf 0, 1, 1b, 1c, 2, 3, 4a und 4b. Schritt 3b wird separat als wiederholbarer Post-Publication-Loop fuer Tag 30, 60 und 90 mit Artefakt-, Gate- und Resume-Pruefung getestet. | Ein versionierter, anonymisierter End-to-End-Fixture-Run mit Provider-Stubs und manifestierter Evidence sowie ein separater zeitversetzter 3b-Test. |

## 8. Go Verdict

**No-Go.** Ein Conditional Go ist erst zulaessig, wenn AC-01 bis AC-06 gruen in CI laufen und ein kontrollierter Acceptance-Trace AC-09 die Runtime-Anbindung belegt. Ein produktiver Provider-Live-Test darf erst nach Budget-, Idempotenz- und Observability-Absicherung erfolgen.

## 9. Exakte naechste Fix-Reihenfolge

1. `services/agentseo_gateway/core.py` und ein neuer Runtime-Entrypoint: Gateway verbindlich anbinden, Contract und Idempotenz einbauen.
2. `mcp/tool-contracts/*.json`: Einen kanonischen Contract mit verpflichtendem Zielmarkt, Async, Fehlern und Run-Metadaten erstellen.
3. `standards/manifest.schema.json` plus State-Transition-Validator: Abschluss-Gates, Geo-Bindung, Schema-Version und strikte Objektgrenzen ergaenzen.
4. `mcp/tools/capacity_matrix_solver.py`: Input-Contract und harte Fehler fuer fehlende Daten, leere Eingabe und unmet Capacity-Gates einbauen.
5. `mcp/tools/validate_schema_jsonld.py`: Strikte semantische Profile und negative CLI-Tests implementieren.
6. `tests/`: Contract-, Stub-Integration-, negative Fixture- und vollstaendige Acceptance-Tests ergaenzen. `tests/run_acceptance_tests.py` muss diese umfassen.
7. `tests/acceptance-tests.md`, `CHANGELOG.md`, `00_admin/PROJECT_STATE.md`, `README.md` und `scripts/generate_sample_keywords.py`: erst nach gruenem CI auf den realen Stand bringen.
