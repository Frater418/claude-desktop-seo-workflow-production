# Foundation Gates and Step 1 Readiness Implementation Brief

> **Lifecycle: superseded and completed evidence.** Aktuelle Projekt- und Gate-Autoritaet: `00_admin/PROJECT_STATE.md`, `00_admin/DECISIONS.md`, `standards/quality/` und die aktiven Plaene.

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Status: In Umsetzung
- Ausgangspunkt: `00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md`

## Ziel

Den lokalen Kandidatenstand so erweitern, dass AHD Schritt 1 kontrolliert beginnen kann, ohne den bestandenen Schritt-0-Lauf zu veraendern. Gleichzeitig werden die fuer spaetere Workflowphasen erforderlichen Quality-Gate-Vertraege und Toolgrenzen vorbereitet.

## Nicht verhandelbare Regeln

1. Keine Commits, Pushes, Deployments oder produktiven Notion-Schreibvorgaenge.
2. Keine stillen Defaults fuer Markt, Sprache, Provider, Claims oder Status.
3. Bestehende AHD-Dateien aus `AHD_STEP0_IMMUTABLE_BASELINE.json` bleiben byte-identisch.
4. Neue Migrationen werden als Sidecar-Artefakte geschrieben.
5. Alle Objektschemas sind JSON Schema Draft 2020-12 und standardmaessig geschlossen.
6. Human Approval bindet eine konkrete Artefaktversion und einen SHA-256.
7. Schritt 3b bleibt ein separater Post-Publication-Sideflow.
8. Raphael Rechberger ist alleiniger Autor.
9. Keine Em-Dashes oder En-Dashes.
10. OMO wird extern nur ueber Sisyphus angesprochen.

## Wave 1: Foundation Gate A

### Paket A: Domain und Markt

Neue Vertrage unter `standards/domain/`:

- `project.schema.json`
- `search-deployment.schema.json`
- `entity-domain-gbp.schema.json`
- `risk-compliance.schema.json`
- `market-registry.schema.json`
- `market-registry.json`

Das Modell trennt Tenant, Kunde, Marke, Domain, physische Location, Service Area, Search Deployment, Suchmarkt, Sprache, Locale, Legal Jurisdiction, Marktphase, GBP, Workstream, Conversion Model und Compliance.

### Paket B: Workflow und Traceability

Neue Vertrage unter `standards/workflow/` und `standards/runtime/`:

- `workflow-graph.json`
- `workflow-graph.schema.json`
- `run-envelope.schema.json`
- `transition-command.schema.json`
- `approval-record.schema.json`
- `error-envelope.schema.json`
- `artifact-record.schema.json`
- `evidence-record.schema.json`
- `claim-record.schema.json`
- `quality-gate-run.schema.json`

Kanonischer Initialpfad:

`0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`

3b ist ein wiederholbarer Sideflow nach Publikation fuer Tag 30, 60 und 90.

### Paket C: Fixtures und Tests

- Zehn reale, datenarme Kundenfixtures unter `tests/fixtures/domain/real-customer-matrix/`
- Negative Fixtures fuer Geo-Mismatch, fehlende Locale, falsche State-Transition, stale Approval, unverified Local Presence und fehlende YMYL-Evidence
- Contracttests unter `tests/contracts/`

## Wave 2: Schritt 1

- `standards/outputs/step-1-topic-inventory.schema.json`
- Prompt 1 auf v2-Vertraege umstellen
- Kein `completed` vor Gate 1
- maschinenlesbarer Output plus Markdown-View
- Crawl Snapshot, Source URLs, Competitor Evidence, Hypothesen und Decision Records
- Step-1-Preflight CLI
- AHD v2 Sidecar-Projekt und Run Envelope

## Wave 3: Quality Gates und Tools

### Screaming Frog

Installierter CLI-Pfad:

`C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe`

Neue Vertrage und Adapter:

- `standards/quality/quality-gate-registry.json`
- `standards/quality/quality-gate-registry.schema.json`
- `standards/quality/screaming-frog-crawl.schema.json`
- `services/quality_gate_runner/screaming_frog.py`
- konservativer CLI-Preflight
- Export- und Hash-Manifest
- harte Fehlercodes bei fehlendem Binary, Crawlfehlern, fehlenden Exports oder URL-Limit

Schritt-1-Gates pruefen mindestens:

- Crawl erfolgreich
- Start-URL und Final-URL
- Statuscodes
- Indexability
- Canonicals
- Titles und Meta Descriptions
- H1/H2
- interne Links
- hreflang bei mehrsprachigen Deployments
- strukturierte Daten
- Redirects und Broken Links
- Crawl- und Exporthashes

Weitere registrierte Quality Gates:

- JSON Schema Contract
- HTML und Link QA
- JSON-LD pruefgestufte Validierung
- Google Rich Results manuelles externes Gate
- Lighthouse und Accessibility fuer spaetere 4b-Staging-Gates
- Ahrefs und GSC als unabhaengige Evidence-Quellen, nicht als stiller Pflichtfallback

## Wave 4: Deterministische Toolfixes

### Solver

- leere Eingabe ist Fehler
- fehlende Pflichtmetriken sind Fehler
- unbekannter Content-Typ ist Fehler
- `hours_min <= hours_max`
- positive Wochenanzahl
- keine stillen 0-Werte
- strukturierte Fehlercodes und negative Tests

### JSON-LD Validator

Getrennte Ebenen:

- parse-valid
- contract-valid
- format-valid
- geo-valid
- evidence-ready

Keine pauschale Aussage `100% valide`.

Mindestens pruefen:

- bekannte Typen
- Datumsformat
- URL-Format
- Address-Struktur
- leere about/mentions-Eintraege
- FAQ-Struktur
- Breadcrumb-Struktur
- Wikidata URI im Strict Mode

## Wave 5: Reproduzierbarkeit

- `requirements-dev.txt`
- einheitlicher Test Runner
- Host und OMO gleiche Dependencies
- vollständige Contract-, Unit- und Acceptance-Suite
- keine Tests, die nur Marker als Verhalten akzeptieren

## Abschlusskriterien fuer Schritt-1-Go

1. Alte AHD-Dateien sind byte-identisch.
2. AHD v2 Sidecar validiert.
3. Alle zehn realen Domainfixtures validieren.
4. Alle negativen Fixtures schlagen mit erwarteten Fehlercodes fehl.
5. Workflowgraph und Transitiontests bestehen.
6. Gate 1 kann nicht ohne Artifact-ID, Hash und Reviewer approval erreichen.
7. Screaming-Frog-Preflight und AHD Crawl-Snapshot sind vorhanden oder liefern einen expliziten Blocker.
8. Schritt-1-Outputvertrag und Promptvertrag bestehen.
9. Vollständige Test-Suite ist auf Host und OMO gruen.
10. OMO Spec- und Quality-Review besitzen keine offenen P0- oder P1-Befunde.
