# 04 Traceability and Output Red-Team Audit

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Auditmodus: Read-only fuer bestehende Source-Dateien
- Gegenstand: Durchgaengige Rueckverfolgbarkeit der Schritte 0, 1, 1b, 1c, 2, 3, 3b, 4a und 4b sowie Qualitaet und Deployability ihrer Endoutputs
- Baseline: Ausschliesslich `00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md`

## 1. Executive Verdict

**Verdict: No-Go fuer produktive, automatisierte Kundenauslieferung und Deployment.**

Der Kandidatenstand besitzt eine nachvollziehbare Dateikette, klare Sollpfade, mehrere sinnvolle Fail-Fast-Ideen, einen deterministischen Planer und ein brauchbares Grundmuster fuer Human Review. Die Kette ist aber keine belastbare Traceability Chain. Zwischen Briefing, Research, Providerantwort, Entscheidung, Artefakt, Freigabe, Notion-Task, CMS-Implementierung und Messwert fehlen stabile IDs, Provenienz, Revisionen, Statusregeln und maschinelle Gates. Ein formal vorhandenes oder syntaktisch valides Artefakt kann deshalb fachlich falsch, unbelegt, nicht freigegeben, nicht deploybar oder nicht messbar sein und trotzdem als `completed`, `Bereit fuer Copywriting` oder bestanden erscheinen.

Die schwersten Risiken sind:

1. Single-Market- und Single-Language-State kann reale Cross-Border-, Multi-Brand-, Multi-Domain- und Programmatic-Local-Faelle falsch klassifizieren.
2. YMYL-, Legal-, Local-Presence- und Claim-Evidenz ist kein verpflichtender Outputvertrag.
3. Human Gates sind in Prompts beschrieben, aber mit Ausnahme von Gate 0 nicht als persistente, erzwingbare Transition modelliert.
4. Schritt 4a kann aus einem geo-bekannt fehlerhaften SERP-Pfad und unzureichend belegten Daten unmittelbar ein als Notion-ready bezeichnetes Briefing erzeugen.
5. Schritt 4b liefert Standalone-HTML, aber keinen WordPress- oder Elementor-Implementierungsvertrag, keinen Content-vs-Template-Diff und keinen Nachweis fuer Theme-, Plugin-, Consent-, Accessibility- oder Tracking-Kompatibilitaet.
6. Die Acceptance-Suite prueft ueberwiegend Containerform, Marker und positive synthetische Fixtures. Sie prueft keinen realen Neun-Schritt-Lauf und kann daher false green sein.

**Deployment-Grenze:** Die Artefakte duerfen als Entwicklungsprototyp und manuell gepruefte Spezifikation verwendet werden. Sie duerfen nicht automatisch nach Notion als freigegebene Produktion, in WordPress/Elementor oder auf Kundendomains publiziert werden, bevor die P0- und P1-Acceptance-Criteria dieses Reports nachweislich bestanden sind.

## 2. Scope und gelesene Evidenz

### 2.1 Baseline und Auditregeln

- `AGENTS.md:10-28`, `AGENTS.md:49-58`, `AGENTS.md:62-73`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md:9-37`, `AUDIT_BRIEF.md:40-147`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md:7-39`
- `README.md`, insbesondere Produktionsstatus, Workflow-Landkarte, Vertragsnavigation und Testdarstellung
- `00_admin/PROJECT_STATE.md:1-10`, `00_admin/PROJECT_STATE.md:26-59`, `00_admin/PROJECT_STATE.md:78-100`
- `CHANGELOG.md:8-35`, `CHANGELOG.md:39-83`

Die Host-Baseline weist sieben bereits geaenderte tracked Dateien, den untracked Gateway-, Test- und Fixture-Kandidatenstand sowie den Auditordner aus (`HOST_GIT_BASELINE.md:11-33`). Daraus folgt: Dieser Report bewertet Dateiinhalt. Er behauptet weder, dass Candidate-Dateien Bestandteil des Baseline-Commits sind, noch verwendet er Container-Git-Metadaten. Der Gateway unter `services/` und die Tests `test_agentseo_location_guard.py` sowie `test_prompt0_contract.py` werden getrennt als Kandidatenstand beurteilt.

### 2.2 Workflow-, Output- und Designvertraege

- Alle neun Produktionsprompts: `prompts/0-kickoff.xml.md`, `1-pillar-identifikation.xml.md`, `1b-seitenarchitektur.xml.md`, `1c-pillar-template.xml.md`, `2-cluster-recherche.xml.md`, `3-120-tage-plan.xml.md`, `3b-performance-check.xml.md`, `4a-content-briefing-und-schema.xml.md`, `4b-landingpage-html.xml.md`
- `standards/manifest.schema.json:1-722`
- `standards/location-codes.json:1-21`
- `standards/dateinamen-und-output-vertrag.md:10-68`
- `standards/design-system.css:1-402`
- `mcp/tool-contracts/agentseo_keyword_enricher.json:1-58`
- `mcp/tool-contracts/serp_gap_analyzer.json:1-38`
- `mcp/tool-contracts/schema_jsonld_generator.json:1-41`

### 2.3 Implementierung, Tests und Fixtures

- `mcp/tools/capacity_matrix_solver.py:21-181`, `capacity_matrix_solver.py:183-326`
- `mcp/tools/validate_schema_jsonld.py:19-143`, `validate_schema_jsonld.py:145-176`
- Kandidat `services/agentseo_gateway/core.py:24-96`, `core.py:114-270`, `core.py:273-446`
- `tests/run_acceptance_tests.py:14-130`
- `tests/test_prompt0_contract.py:17-82`
- `tests/test_agentseo_location_guard.py:24-160`
- `tests/acceptance-tests.md:1-57`
- `tests/fixtures/sample_manifest.json:1-174`
- `tests/fixtures/sample_cluster_keywords.json:1-160` sowie Generator `scripts/generate_sample_keywords.py:4-112`
- `tests/fixtures/sample_serp_briefing.json:1-27`
- `tests/fixtures/sample_briefing.md:1-102`
- `tests/fixtures/sample_landingpage.html:1-117`
- `tests/fixtures/sample_schema_graph.json`

### 2.4 Governance, Handoffs, Migration und Realfaelle

- `docs/04-entscheidungslog.md:26-123` mit ADR-001 bis ADR-011
- `docs/05-human-in-the-loop.md:22-120`
- `docs/06-pilot-abnahme-checkliste.md:10-86`
- `docs/copywriter-handoff-guidelines.md:10-68`
- `docs/07-geo-architecture-specification.md`
- `docs/08-geo-sprint-plan-and-multi-agent-orchestration.md`
- `.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:20-242`, `:244-370`, `:371-556`, `:614-740`, `:820-875`
- Reale Matrix `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:1-49`

### 2.5 Scope-Grenzen

Keine Provider-, Test-, Build-, Browser-, Git-, Deployment- oder Netzwerkoperation wurde ausgefuehrt. Es wurden keine Credentials gelesen. Aussagen ueber Verhalten beruhen auf statischer Datei- und Vertragsevidenz, nicht auf einem in diesem Audit erzeugten Green Run.

## 3. Was wirklich stark ist

### 3.1 Fakten

1. Die Sollkette und die Artefaktpfade sind fuer alle neun Schritte zentral dokumentiert (`standards/dateinamen-und-output-vertrag.md:44-56`). Das ist eine gute Basis fuer spaetere Contract-Tests.
2. Schritt 0 ist der einzige Schritt mit einem expliziten, zweistufigen Zustand vor und nach Human Approval. Der Prompt setzt zuerst `in_progress` und erlaubt `completed` erst nach Gate 0 (`prompts/0-kickoff.xml.md:86-101`, `:130-140`). Das ist das richtige Grundmuster.
3. Schritt 2 beschreibt asynchrones Queueing, Polling, Zielmarktpruefung, fehlende Keywords und harte Providerfehler konkret (`prompts/2-cluster-recherche.xml.md:43-66`). Der Candidate-Gateway bewahrt Provider-Rohdaten und Standortkorrektur getrennt auf (`services/agentseo_gateway/core.py:197-270`, `:400-446`).
4. Der Solver trennt Allokation und Rendering, fuehrt unverplante Items als Backlog und weist die gemessene Kapazitaet aus (`mcp/tools/capacity_matrix_solver.py:146-181`, `:219-290`). Das ist deutlich belastbarer als LLM-Arithmetik.
5. Das 4a/4b-Splitting trennt redaktionelle Spezifikation von HTML-Generierung (`docs/04-entscheidungslog.md:60-66`). Diese Grenze ist fachlich sinnvoll und reduziert Outputabbrueche.
6. Design-Tokens und GEO-Komponenten sind zentral vorhanden, ohne externe CSS-Imports (`standards/design-system.css:9-95`, `:342-402`).
7. Der Migrationsplan erkennt viele benoetigte Runtime-Eigenschaften bereits korrekt: Run-ID, Human-Gate-Pause, Wiederaufnahme, Fehlerobjekte, Artefaktspeicher und reale End-to-End-Abnahme (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:114-125`, `:178-189`, `:217-242`, `:820-863`).
8. Die reale Use-Case-Matrix formuliert die entscheidenden Trennungen klar: Leistungsort, Zielmarkt, Suchregion, Sprache, Marktphase, Marken, Domains, GBPs und Workstreams (`2026-08-18-real-customer-use-case-matrix.md:23-45`). Sie ist eine belastbare Quelle fuer kommende negative und positive Fixtures.

### 3.2 Interpretation

Das Repository hat gute fachliche Bausteine, aber die Staerke liegt derzeit in Spezifikation und Prototyping, nicht in beweisbarer Produktionssteuerung. Besonders Schritt 0, Solver-Backlog und Gateway-Rohdatenerhalt zeigen, wie die gesamte Kette aufgebaut werden sollte: jede Entscheidung mit strukturiertem Input, maschinellem Resultat, explizitem Gate und unveraenderter Evidenz.

### 3.3 Empfehlung

Nicht neu beginnen. Die vorhandenen Pfade, Promptgrenzen, Error-Codes und Tools als Domainwissen behalten, aber Status, Provenienz, Outputschemas und CMS-Handoff als versionierte, transportneutrale Vertraege vor die Promptgenerierung ziehen.

## 4. Befunde nach P0 bis P3

### P0-1: Falscher Markt oder falsche Local-Presence kann bis zum Kundenoutput propagieren

**Fakt:** Das Manifest erlaubt genau ein `country`, einen `location_code`, eine `language`, eine `primary_region` und eine Domain (`standards/manifest.schema.json:124-145`, `:617-630`). Die reale Matrix verlangt beliebig viele Zielmaerkte und Sprachen und trennt Leistungsort, Suchmarkt und Suchregion (`2026-08-18-real-customer-use-case-matrix.md:23-30`). Shunyata Sri Lanka, Epargne Plurielle, Daniela Landgraf, MobilePhysiotherapie24 und Shunyata Bali benoetigen genau diese nicht modellierten Beziehungen (`:12-21`).

**Interpretation:** Ein schema-valides Projekt kann Frankreich, Luxemburg, Sri Lanka, DACH, Bali oder Wien nicht ohne Sonderlogik korrekt ausdruecken. Schritt 2 und 4a koennen dadurch Daten des falschen Markts verarbeiten. Schritt 4b kann NAP oder lokale Kundenstimmen fuer Orte erzeugen, an denen kein verifizierter physischer Standort besteht.

**Empfehlung:** Ein versioniertes Array `market_deployments[]` mit stabiler Deployment-ID einfuehren. Pflichtrelationen: Suchmarkt, Sprache, Locale, Leistungsgebiet, physische Standorte, Service-Area-Policy, Legal Jurisdiction, Domain, Brand, GBP, Marktphase und Provider-Codes. Local-Output nur bei passender, gepruefter Location-Policy erlauben.

### P0-2: YMYL- und Claims-Outputs besitzen keine beweispflichtige Evidenzkette

**Fakt:** Schritt 4a fordert pro Abschnitt einen harten Datenpunkt, definitive Sprache und Autorenexpertise (`prompts/4a-content-briefing-und-schema.xml.md:50-58`), definiert aber weder Quellen-ID, Abrufdatum, Rechtsraum, Gueltigkeitsdatum noch Reviewer-Qualifikation. Die Beispiel-Fixture behauptet unter anderem 24 bis 48 Stunden, gesetzliche Hoechstsaetze und konkrete Pflegebetraege (`tests/fixtures/sample_briefing.md:27-28`, `:44-52`) ohne Quellenbeleg. Schritt 4b uebernimmt diese Aussagen und ergaenzt Disclaimer nur als sichtbares Element (`prompts/4b-landingpage-html.xml.md:39-59`).

**Interpretation:** Medizinische, pflegerische, finanzielle oder Sustainability-Claims koennen plausibel aussehen, syntaktisch valide sein und dennoch veraltet, juristisch falsch oder fuer den Kunden unzulaessig sein. Die reale Matrix enthaelt mehrere YMYL- und regulierte Archetypen (`2026-08-18-real-customer-use-case-matrix.md:12-21`).

**Empfehlung:** Pro Claim eine immutable Evidence-ID, Quelle, Herausgeber, URL oder Dokumentreferenz, Abrufdatum, Gueltigkeitszeitraum, Jurisdiction, Claim-Typ und Freigabestatus erzwingen. YMYL-Outputs duerfen vor Fach- oder Legal-Freigabe hoechstens `awaiting_compliance_review` erreichen. Nicht belegte definitive Claims blockieren 4a und 4b.

### P0-3: Human Gates verhindern keine unfreigegebene Completion und Auslieferung

**Fakt:** Schritte 1, 1b, 1c, 2 und 3 setzen ihren Phasenstatus innerhalb der Ausfuehrung direkt auf `completed` (`prompts/1-pillar-identifikation.xml.md:49-51`, `prompts/1b-seitenarchitektur.xml.md:50-52`, `prompts/1c-pillar-template.xml.md:56-58`, `prompts/2-cluster-recherche.xml.md:75-78`, `prompts/3-120-tage-plan.xml.md:68-71`). Die Human Gates stehen danach als Text. Das Schema besitzt nur `pending`, `in_progress`, `completed`, `error` und keine Approval-Objekte fuer diese Schritte (`standards/manifest.schema.json:362-581`). Nur Gate 0 ist strukturiert (`:238-279`).

**Interpretation:** Ein Agent, UI-Worker oder n8n-Flow kann fachlich unfreigegebene Outputs als abgeschlossen behandeln und downstream starten. Damit sind Copywriter-, Entwicklungs- und Deployment-Handoffs nicht kontrollierbar.

**Empfehlung:** Einheitliche Transitionen fuer jeden Schritt: `pending -> running -> validation_failed|awaiting_review -> approved|rejected -> published|superseded`. Jede Transition benoetigt `run_id`, Inputrevision, Outputhash, Actor, Timestamp und optionalen Reason-Code. Nur ein Transition-Service darf den Zustand aendern.

### P0-4: 4a und 4b koennen falsche lokale und redaktionelle Fakten als produktionsbereit ausgeben

**Fakt:** Der SERP-Outline-Pfad ist laut Standorttabelle fuer Deutschland geo-fehlerhaft und seine Gliederung nicht verwertbar (`standards/location-codes.json:18-20`). Schritt 4a nennt genau diesen Pfad als erlaubte Quelle, ohne einen zwingenden Fehlercode oder Evidence-Envelope (`prompts/4a-content-briefing-und-schema.xml.md:43-49`). Die Sample-Fixtures enthalten eine konkrete Strasse, Telefonnummer, Kapazitaets- und Leistungsclaims (`tests/fixtures/sample_briefing.md:60-70`, `sample_landingpage.html:29-57`) ohne Bezug zum Sample-Manifest, das keine Adresse oder Telefonnummer modelliert (`tests/fixtures/sample_manifest.json:1-119`).

**Interpretation:** Die positive Fixture demonstriert genau den gefaehrlichen Pfad: plausible, aber nicht aus einem autoritativen Input rueckverfolgbare NAP- und YMYL-Daten koennen Validator und Acceptance-Test passieren.

**Empfehlung:** 4a muss bei fehlender oder geo-inkonsistenter SERP-Evidenz mit strukturiertem Fehler stoppen. 4b darf NAP, Claims, Testimonials, Map-Referenzen und Canonical nur aus freigegebenen strukturierten Feldern uebernehmen. Jede sichtbare Aussage muss auf eine Briefing- oder Evidence-ID zeigen.

### P1-1: Keine durchgaengige Artefakt-Provenienz, Versionierung oder Idempotenz

**Fakt:** Das Manifest speichert ueberwiegend Pfadstrings (`standards/manifest.schema.json:584-615`), aber keine Artefakt-ID, Inputhashes, Producer-Version, Promptversion, Toolversion, Parent-IDs, Revision oder Reviewstatus. 3b ueberschreibt `outputs/3-plan.md` (`standards/dateinamen-und-output-vertrag.md:54-54`). 4a und 4b verwenden aus dem Titel abgeleitete Pfade ohne Kollisions- oder Revisionierungsregel (`prompts/4a-content-briefing-und-schema.xml.md:67-70`, `prompts/4b-landingpage-html.xml.md:60-63`).

**Interpretation:** Resume, Retry und Replay koennen nicht entscheiden, ob ein Output wiederverwendbar, veraltet oder doppelt ist. 3b zerstoert die vorangegangene Planrevision. Ein gleichlautender Titel in mehreren Maerkten kann kollidieren.

**Empfehlung:** Content-addressed Artefakt-Envelope mit `artifact_id`, `project_id`, `deployment_id`, `step`, `run_id`, `revision`, `parent_artifact_ids`, `input_hash`, `content_hash`, `contract_version`, `producer_version`, `created_at`, `validation_records`, `review_state` und immutable Storage-Key. 3b erzeugt eine neue Planrevision statt Overwrite.

### P1-2: Outputvertraege sind Prosa, nicht maschinell validierbare Schemas

**Fakt:** Der Outputvertrag beschreibt Markdowntabellen, CSV-Spalten und HTMLanforderungen nur textuell (`standards/dateinamen-und-output-vertrag.md:44-56`). `manifest.schema.json` validiert keine Artefaktinhalte. `additionalProperties: false` fehlt auf den zentralen Objekten (`standards/manifest.schema.json:1-722`). Schritt 1b verlangt 100 Prozent Synchronitaet zwischen Markdown und HTML, nennt aber keinen Comparator (`prompts/1b-seitenarchitektur.xml.md:55-60`).

**Interpretation:** Ein Artefakt kann fehlen, falsche Spalten besitzen, teilweise sein oder vom Schwesterartefakt abweichen, waehrend der Manifeststatus `completed` bleibt.

**Empfehlung:** JSON Schemas oder deterministische Parser fuer jeden Output. Markdown nur als Rendering eines kanonischen strukturierten Artefakts. HTML, CSV und Notion-Payload werden daraus erzeugt und gegen Schema, Referential Integrity und Cross-Output-Hashes geprueft.

### P1-3: WordPress- und Elementor-Handoff ist nicht deploybar spezifiziert

**Fakt:** Der einzige explizite Handoff lautet, 4b an Web-Entwickler fuer WordPress/Elementor zu geben (`docs/05-human-in-the-loop.md:102-109`; Rollenbezug `00_admin/PROJECT_STATE.md:18-22`). 4b erzeugt eine vollstaendige autarke HTML-Datei mit eingebettetem CSS und JSON-LD (`prompts/4b-landingpage-html.xml.md:39-63`). Es fehlen Ziel-Theme, Elementor-Version, Template-Kit, globale Styles, Widget-Mapping, Header/Footer Ownership, Shortcodes, Form-Provider, Consent, Cache, Security-Sanitization, Accessibility, responsive Breakpoints, Redirects, Canonical Ownership, Schema-Plugin-Deduplizierung und Rollback.

**Interpretation:** Das Ergebnis ist ein Design-Mock oder Referenz-HTML, kein sicher importierbares Elementor-Artefakt. Beim Einbau drohen doppelte JSON-LD-Graphen, CSS-Konflikte, nicht funktionierende Formulare, verlorene Trackingevents, Consent-Verstoesse und manuelle Abweichung vom freigegebenen Briefing.

**Empfehlung:** Getrennte Handoff-Vertraege fuer Gutenberg, Elementor und Custom Theme. Fuer Elementor mindestens: versioniertes Template-JSON oder eindeutige Widget-Spezifikation, Global-Style-Mapping, Dynamic-Tag-Mapping, Form- und Consent-Contract, Schema-Ownership, Assetmanifest, URL/Redirect-Plan, Accessibility- und Responsive-Gates, Staging-Screenshot-Diff, Contenthash-Vergleich und Deployment-Rollback.

### P1-4: Notion-Frontmatter ist kein Notion-Import- oder Workflowvertrag

**Fakt:** Die Copywriter-Guideline behauptet, YAML-Eigenschaften wuerden automatisch als Notion-Properties erkannt (`docs/copywriter-handoff-guidelines.md:19-38`). Schritt 4a nennt Frontmatter nahtlos synchronisierbar (`prompts/4a-content-briefing-und-schema.xml.md:13-20`, `:67-70`). Es fehlen Data-Source-ID, Property-IDs und Typen, Relations, User-Mapping, Status-Mapping, Revision, Page-ID, Idempotency-Key und Konfliktregel. Der Migrationsplan fuehrt diese Datenbanken nur als proposed Plan (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:244-370`).

**Interpretation:** Das Briefing ist menschenlesbar, aber weder importbeweisend noch bidirektional synchronisierbar. Wiederholte Imports koennen Duplikate erzeugen, Statuskonflikte koennen Freigaben ueberschreiben.

**Empfehlung:** Versionierter Notion-Adaptervertrag mit stabiler External-ID, Data-Source-Schema, Property-Mapping, User-/Relation-Mapping, expected revision, idempotent upsert und Konfliktstatus. Markdown bleibt Contentartefakt, nicht Control Plane.

### P1-5: 3b misst keine belastbare Wirkung und kann den Plan destruktiv veraendern

**Fakt:** 3b verlangt nur URL, Keyword, Klicks, Impressionen, Position und Alter (`prompts/3b-performance-check.xml.md:18-27`). Die Klassifikation nutzt unspezifizierte Begriffe wie stark steigend und keine Positionsveraenderung (`:29-41`). Bei Local Pages soll GBP/Map Pack zaehlen, obwohl der Inputvertrag dafuer keine Felder nennt (`:35-37`). Anschliessend wird der bestehende Plan direkt angepasst (`:43-51`).

**Interpretation:** GSC-Export allein misst weder Leads, Umsatz, Calls, Buchungen, Uploads, Bewerbungen, OTA-Konversion noch GBP-Aktionen. Baseline, Zeitraumvergleich, Attribution, Saisonalitaet, Indexierungsstatus und Konfidenz fehlen. Ein schwaches oder unvollstaendiges Signal kann eine freigegebene Roadmap ueberschreiben.

**Empfehlung:** Measurement-Contract je Conversion-Modell, Channel und Markt. 3b erzeugt zuerst einen immutable Adjustment Proposal mit Baseline, Vergleichsfenster, Source IDs, Datenvollstaendigkeit, Schwellenwerten und Konfidenz. Erst Gate 3B erzeugt eine neue Planrevision.

### P1-6: Providerabhaengigkeiten besitzen keinen durchgaengigen Evidence- und Kostenvertrag

**Fakt:** Die alten Toolvertraege verlangen nur minimale Inputs und setzen Germany/de Defaults (`mcp/tool-contracts/agentseo_keyword_enricher.json:8-35`, `serp_gap_analyzer.json:8-17`). Sie enthalten weder `location_code` noch `sync`, Run-ID, Idempotency-Key, Kostenbudget oder Retry-Policy. Der Candidate-Gateway erzwingt Async ueber Queryparameter und bewahrt Rohdaten (`services/agentseo_gateway/core.py:355-398`, `:400-446`), ist laut Host-Baseline aber untracked Kandidatenstand (`HOST_GIT_BASELINE.md:21-29`). DataForSEO ist im Zielbild bevorzugt (`AUDIT_BRIEF.md:15-25`), aber die produktiven Prompt- und Outputvertraege bleiben AgentSEO-spezifisch.

**Interpretation:** Providerwechsel, Kostenkontrolle, deduplizierte Retries und reproduzierbare Evidenz sind nicht durchgaengig moeglich. Prompt und Toolcontract widersprechen einander.

**Empfehlung:** Providerneutraler Research-Request und Evidence-Response. Capability-basierte Adapter fuer DataForSEO, AgentSEO und weitere Quellen. Pflichtfelder: Deployment-ID, Query, Locale, Geo-ID, Device, requested capability, async policy, budget, idempotency key, provider job ID, raw response hash und Normalisierungsversion.

### P2-1: Pillar-, Seiten- und Kannibalisierungsentscheidungen sind nicht beweisbar

**Fakt:** Schritt 1 schaetzt Wortzahlen, analysiert Websites und Wettbewerber und erzeugt Hypothesen (`prompts/1-pillar-identifikation.xml.md:27-50`). Schritt 1b ordnet jedes Thema URLs und Navigation zu (`prompts/1b-seitenarchitektur.xml.md:28-52`). Es fehlen Crawl-Snapshot-ID, URL-Inventar-Schema, Canonical-/Redirect-Entscheidung, Query-Overlap-Metrik, Decision-ID und Reviewerkommentar.

**Interpretation:** Die Strategie kann plausibel wirken, aber niemand kann spaeter rekonstruieren, warum eine bestehende URL behalten, ersetzt, zusammengelegt oder neu angelegt wurde. Kannibalisierung ist nur eine Reviewfrage.

**Empfehlung:** Strukturierte URL- und Topic-Entscheidungsmatrix mit Source Snapshot, Existing URL, Proposed URL, Intent Cluster, Overlap Score, Action, Redirect Target, Owner, Decision Reason und Approval.

### P2-2: Design-Extraktion und HTML-Qualitaet sind nicht reproduzierbar

**Fakt:** Schritt 1c extrahiert Tokens visuell aus einem Screenshot (`prompts/1c-pillar-template.xml.md:20-39`) und markiert danach Templates completed (`:40-58`). Das globale CSS ist eine generische dunkle Palette (`standards/design-system.css:9-95`) und besitzt nur wenige responsive Verhaltensweisen ueber `auto-fit`, aber keinen kundenbezogenen Token-Provenienznachweis. Die Sample-Landingpage inlined nur einen kleinen Teilsatz (`tests/fixtures/sample_landingpage.html:9-28`).

**Interpretation:** Screenshot vorhanden ist nicht gleich Brand Fidelity. Es fehlen Screenshotquelle, Viewport, Extraktionskonfidenz, Kontrastpruefung, Fontlizenz, Breakpointmatrix und visuelle Regression.

**Empfehlung:** Design-token JSON als kanonische Quelle, Screenshot- und Viewport-IDs, Brand-Approval, WCAG-Checks, Komponentenmatrix und Screenshot-Diffs gegen Staging. CSS und CMS-Mapping daraus generieren.

### P2-3: JSON-LD- und GEO-Validierung belegt weder Wahrheit noch Rich-Result-Eignung

**Fakt:** Der Validator prueft eine kleine lokale Pflichtfeldliste (`mcp/tools/validate_schema_jsonld.py:19-31`, `:66-124`) und meldet bei fehlenden Fehlern 100 Prozent valide (`:145-176`). Unbekannte Typen werden nicht gegen Schema.org validiert. In Strict Mode ist `about` fuer LocalBusiness und MedicalBusiness nicht verpflichtend, weil die Fehlermeldung nur fuer Article-Typen gesetzt wird (`:105-115`). Die Sample-Fixtures enthalten nur eine FAQ-Frage, obwohl Prompt 4a drei bis fuenf fordert (`tests/fixtures/sample_briefing.md:86-99`; `prompts/4a-content-briefing-und-schema.xml.md:59-65`).

**Interpretation:** Syntax und wenige Felder sind nicht semantische Korrektheit, Google Eligibility oder GEO-Evidenz. Ein gruen markierter Validator kann falsche NAP-, Preis- oder Fachclaims nicht erkennen.

**Empfehlung:** Validatorausgabe in klar getrennte Ebenen aufteilen: parse-valid, contract-valid, schema.org-valid, Google-feature-eligible, entity-evidence-valid und claim-approved. Kein Label `100% valide` ohne definierte Pruefebene.

### P2-4: Observability besteht ueberwiegend aus einer Logdatei, nicht aus korrelierbaren Runs

**Fakt:** Der Outputvertrag nennt `logs/validation_errors.log` als einziges Pflichtlog (`standards/dateinamen-und-output-vertrag.md:37-39`). Schritt 2 schreibt einige Providerfehler hinein (`prompts/2-cluster-recherche.xml.md:52-66`). Andere Schritte definieren keine einheitliche Eventstruktur, Run-ID, Span, Metrik, Dead Letter oder Recovery Pointer. Der Migrationsplan beschreibt diese Eigenschaften erst als Ziel (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:488-556`).

**Interpretation:** Operatoren koennen nicht sicher beantworten, welcher Input, Prompt, Providerjob, Output und Reviewer zu einem Kundenartefakt gehoert oder wo Resume ansetzen soll.

**Empfehlung:** Append-only Audit Events und Run Envelope pro Schritt mit Correlation-ID, Attempt, Actor, Transition, Input-/Outputhash, Providerjob, Cost, Duration, Error, Remediation und Resume Token.

### P3-1: Dokumentation widerspricht dem Kandidatenstand

**Fakt:** `AGENTS.md:66-70`, `docs/06-pilot-abnahme-checkliste.md:63-68`, `docs/03-sprint-plan.md` und `CHANGELOG.md:75-82` beschreiben die JSON-LD-CLI als offen oder fehlend. Die CLI ist implementiert (`mcp/tools/validate_schema_jsonld.py:145-176`) und README bezeichnet sie als vollstaendig. `PROJECT_STATE.md:7` nennt v1.3.0 in Arbeit, README und mehrere Prompts v1.4.0, Prompt 0 v1.5.0 (`prompts/0-kickoff.xml.md:4-10`). `tests/acceptance-tests.md:7` behauptet 5 von 5, waehrend der Runner sieben Tests listet (`tests/run_acceptance_tests.py:108-116`).

**Interpretation:** Operatoren koennen aus Statusseiten keinen verlaesslichen Release- oder Teststand ableiten. Das erhoeht False-Green- und Fehlbedienungsrisiko.

**Empfehlung:** Eine generierte Release-Matrix aus Contractversionen, Tests und Kandidatenstatus. Manuelle Statusbehauptungen entfernen oder automatisiert gegen die kanonische Matrix pruefen.

## 5. Widersprueche und False-Green-Risiken

### 5.1 Schritt-fuer-Schritt Trace

#### Schritt 0: Kickoff und Manifest

- **Input und Preconditions, Fakt:** Briefing, Location-Tabelle, Outputvertrag, optional Gate-0-Bestaetigungen und Preflight (`prompts/0-kickoff.xml.md:17-23`). Pflichtfelder und bekannte Laender werden geprueft (`:51-62`).
- **Execution, Fakt:** Domain-/Wettbewerber-Preflight, semantische Trennung von Marke, Leistungen, Regionen und Workstreams, danach Manifestgenerierung (`:63-101`).
- **Output, Fakt:** `manifest.json`, Ordnerstruktur und eine konsolidierte Operatornachricht (`:97-127`).
- **State und Gate, Fakt:** `initialization`, Schritt 0 `in_progress`, nach Gate 0 `completed` (`:86-95`, `:130-140`).
- **Failure, Fakt:** `ERROR_BRIEFING_INCOMPLETE`, `ERROR_LOCATION_UNKNOWN`; Schema- oder Preflightfehler setzen `error` (`:55-61`, `:97-102`).
- **Resume/Retry/Idempotenz, Fakt:** Nicht spezifiziert. Eine erneute Initialisierung besitzt keinen Requesthash, keine Manifestrevision und keine Merge-/Overwrite-Regel.
- **Downstream und Observability, Fakt:** Schritt 1 liest Manifest. Warnungen sollen konsolidiert werden, aber nur `gate_0.operator_message` und globale Errorfelder sind modelliert (`standards/manifest.schema.json:238-324`).
- **Red-Team-Interpretation:** Bester Gate-Entwurf der Kette, aber ungeeignet fuer mehrere Deployments. Competitor-Reachability ist kein fachlicher Wettbewerbernachweis.

#### Schritt 1: Pillar-Identifikation

- **Input und Preconditions, Fakt:** Nur `manifest.json` ist required (`prompts/1-pillar-identifikation.xml.md:22-30`). Eine explizite Preconditions-Pruefung auf Gate-0-Approval fehlt.
- **Execution, Fakt:** Websiteinventar, Wettbewerbsanalyse, drei bis acht Pillars, acht bis 15 Cluster je Pillar und GEO-Hypothesen (`:31-48`).
- **Output, Fakt:** `outputs/1-pillar-themen.md` mit Gaps und Themenarchitektur (`:61-75`).
- **State und Gate, Fakt:** Prompt setzt `completed`, danach Gate 1 als Text (`:49-51`, `:78-82`). Das Schema verlangt `clusters_per_pillar` nicht, auch wenn dessen Werte begrenzt sind (`standards/manifest.schema.json:362-397`).
- **Failure, Fakt:** Nur fehlendes oder ungueltiges Manifest hat `ERROR_MANIFEST_MISSING`; Mengenverletzungen haben keinen expliziten Error-Code (`prompts/1-pillar-identifikation.xml.md:27-29`, `:54-59`).
- **Resume/Retry/Idempotenz, Fakt:** Nicht spezifiziert. Crawlstand, organische Wettbewerberantwort und Entscheidungen werden nicht versioniert.
- **Downstream und Observability, Fakt:** 1b liest die Markdown-Datei. Keine Source-URL-, Snapshot- oder Evidence-ID im Outputvertrag.
- **Red-Team-Interpretation:** Hypothesen sind als solche markiert, aber strategische Entscheidungen sind nicht von Research-Evidenz getrennt und nicht reproduzierbar.

#### Schritt 1b: Seitenarchitektur

- **Input und Preconditions, Fakt:** Manifest und Pillar-Markdown (`prompts/1b-seitenarchitektur.xml.md:23-31`). Kein maschineller Gate-1-Nachweis.
- **Execution, Fakt:** Live-/Staging-Scan, Nav-, URL-, Seitentyp- und Anchor-Zuordnung (`:32-49`).
- **Output, Fakt:** Markdown und Standalone-HTML (`:41-49`, `:62-70`).
- **State und Gate, Fakt:** Status wird vor GATE-1B `completed` gesetzt (`:50-52`, `:73-77`).
- **Failure, Fakt:** `ERROR_INPUT_MISSING` nur fuer Pillar-Datei. Kein Fehler fuer Crawl, Staging, URL-Konflikt oder fehlende 100-Prozent-Synchronitaet.
- **Resume/Retry/Idempotenz, Fakt:** Nicht spezifiziert. Zwei Outputs koennen bei Retry auseinanderlaufen.
- **Downstream und Observability, Fakt:** 1c liest nur das Markdown, nicht das HTML. Damit wird die behauptete Synchronitaet downstream nicht abgesichert.
- **Red-Team-Interpretation:** Kundenpraesentables Diagramm ist kein implementierbarer Redirect-, Canonical-, Navigation- oder CMS-Migrationsplan.

#### Schritt 1c: Designsystem und Pillar-Templates

- **Input und Preconditions, Fakt:** Manifest, Seitenarchitektur und Screenshot (`prompts/1c-pillar-template.xml.md:20-29`).
- **Execution, Fakt:** Visuelle Tokenextraktion, mehrere autonome HTML-Templates, Schema und Links (`:31-55`).
- **Output, Fakt:** Kunden-CSS und ein HTML pro Pillar (`:68-76`).
- **State und Gate, Fakt:** Status plus Templatepfade werden vor Browsergate `completed` gesetzt (`:56-58`, `:79-83`).
- **Failure, Fakt:** Nur fehlender Screenshot hat `ERROR_SCREENSHOT_MISSING`; keine maschinelle Design-, Responsive-, Accessibility- oder Schema-Fidelity-Fehlerklasse.
- **Resume/Retry/Idempotenz, Fakt:** Keine Screenshot-ID, Tokenrevision oder kontrollierte Aktualisierung. `speichere bzw. aktualisiere` kann bestehende Tokens ueberschreiben.
- **Downstream und Observability, Fakt:** 4b liest CSS, aber keine Designfreigabe oder Komponentenversion. Templatepfade sind Strings ohne Hash.
- **Red-Team-Interpretation:** Ein Screenshot reicht nicht als Corporate-Design-Vertrag. Standalone HTML ist noch kein WordPress-/Elementor-Baustein.

#### Schritt 2: Cluster- und Keyword-Recherche

- **Input und Preconditions, Fakt:** Manifest, Pillar-Datei, Location-Tabelle (`prompts/2-cluster-recherche.xml.md:18-31`). Gate 1C wird nicht geprueft.
- **Execution, Fakt:** 25 bis 40 Ideen je Pillar, asynchrone AgentSEO-Batches, Polling, Location-Check, Filter und GEO-Scoring (`:32-74`).
- **Output, Fakt:** CSV und Manifestmetriken (`:75-98`).
- **State und Gate, Fakt:** Status wird vor GATE-2 `completed` gesetzt (`:75-78`, `:101-105`). Das Schema macht `validated_rows_per_pillar` optional (`standards/manifest.schema.json:450-495`).
- **Failure, Fakt:** Provider-, Location- und fehlende Inputfehler sind beschrieben. Der Outputvertrag nennt zusaetzlich `ERROR_INSUFFICIENT_CLUSTER_COVERAGE`, der Prompt verwendet ihn nicht explizit (`standards/dateinamen-und-output-vertrag.md:52`; `prompts/2-cluster-recherche.xml.md:81-87`).
- **Resume/Retry/Idempotenz, Fakt:** Polling ist beschrieben, aber Job-ID, Batch-ID, Attempt, Kosten und Resume State werden nicht im Manifest verlangt. Candidate-Gateway pollt synchron und ohne persistenten Resume Token (`services/agentseo_gateway/core.py:355-398`).
- **Downstream und Observability, Fakt:** CSV speist Solver. Nicht zurueckgegebene Keywords gehen in eine Textlogdatei, nicht in einen strukturierten Evidence-Record.
- **Red-Team-Interpretation:** Metrik-Provenienz und Keyword-to-provider-response Nachweis fehlen. Information-Gain- und Entity-Density-Scores bleiben Modellbewertungen, obwohl sie neben Providerdaten in derselben CSV stehen.

#### Schritt 3: 120-Tage-Plan

- **Input und Preconditions, Fakt:** Manifest und Keyword-CSV (`prompts/3-120-tage-plan.xml.md:20-23`). Gate-2-Approval und Provider-Evidenz werden nicht geprueft.
- **Execution, Fakt:** Score, 17-Wochen-Horizont, vier Phasen, vertikale und horizontale Links (`:49-71`). Solver ersetzt fehlende numerische Werte durch 0 (`mcp/tools/capacity_matrix_solver.py:112-128`) und nimmt fuer unbekannte Content-Typen 2.5 Stunden (`:127-143`).
- **Output, Fakt:** `outputs/3-plan.md` und Manifestzaehler (`prompts/3-120-tage-plan.xml.md:68-95`).
- **State und Gate, Fakt:** `completed` vor Gate 3 (`:68-71`, `:98-102`). Die 10-Stunden-Untergrenze ist nur manuell (`:74-78`).
- **Failure, Fakt:** `ERROR_DATA_INCOMPLETE` steht im Prompt, aber der Solver selbst failt bei fehlenden Metriken nicht. Unbekannte Typen erhalten einen Default statt Fail-Fast.
- **Resume/Retry/Idempotenz, Fakt:** Deterministisch fuer identische Eingabereihenfolge und Implementierung, aber ohne Inputhash, Seed-, Solver- oder Outputrevision im Artefaktvertrag.
- **Downstream und Observability, Fakt:** 4a sucht Titel in Markdown statt ueber stabile Item-ID. 3b ueberschreibt den Plan.
- **Red-Team-Interpretation:** Mathematische Obergrenze ist stark, aber fachliche Prioritaet, Aufwand und Linkziele sind nicht referentiell abgesichert.

#### Schritt 3b: Performance und adaptive Anpassung

- **Input und Preconditions, Fakt:** Manifest, Plan und Performance-CSV; Seiten muessen 21 Tage alt sein (`prompts/3b-performance-check.xml.md:18-34`).
- **Execution, Fakt:** Performer-/Stagnierer-/Unterperformer-Klassifikation, Local-Ausnahme, Ursachenempfehlung und Planaenderung (`:29-51`).
- **Output, Fakt:** Performancebericht plus ueberschriebener Plan (`:48-68`).
- **State und Gate, Fakt:** Checkpoint wird ins Manifest geschrieben, danach GATE-3B (`:48-51`, `:71-75`). Das Schema erlaubt beliebige Strings in `checkpoints_completed` (`standards/manifest.schema.json:528-555`).
- **Failure, Fakt:** Nur fehlende Datei hat `ERROR_PERFORMANCE_DATA_MISSING`. Keine Fehler fuer falsches Datum, lueckenhafte Quellen, Duplikate, Property-/URL-Mismatch oder fehlende GBP-Daten.
- **Resume/Retry/Idempotenz, Fakt:** Nicht spezifiziert. Retry kann den bereits veraenderten Plan erneut veraendern. Rollback auf Vorrevision ist nicht definiert.
- **Downstream und Observability, Fakt:** 4a liest den mutierten Plan. Keine Lineage vom Messdatensatz zum ersetzten Item.
- **Red-Team-Interpretation:** Das Measurement Loop ist konzeptionell wertvoll, aber derzeit weder messmethodisch belastbar noch revisionssicher.

#### Schritt 4a: Briefing, SERP und JSON-LD

- **Input und Preconditions, Fakt:** Manifest, Plan und ein Freitexttitel (`prompts/4a-content-briefing-und-schema.xml.md:22-30`). Kein Approvalnachweis fuer Plan oder 3b-Aenderung.
- **Execution, Fakt:** Markdown-Lookup, Live-SERP, redaktionelle Struktur, Semantic Triples, JSON-LD (`:32-70`).
- **Output, Fakt:** Briefing-Markdown mit YAML-Frontmatter (`:81-114`).
- **State und Gate, Fakt:** Kein atomarer Briefing-Record im Manifest, nur ein globaler Zaehler fuer `step_4_execution` (`standards/manifest.schema.json:557-580`). GATE-4A folgt als Prosa (`prompts/4a-content-briefing-und-schema.xml.md:117-121`).
- **Failure, Fakt:** Der Prompt besitzt keinen expliziten Error-Pfad fuer Thema nicht gefunden, SERP-Fehler, Location-Mismatch, fehlende Wikidata-ID, nicht belegte Claims oder Validatorfehler.
- **Resume/Retry/Idempotenz, Fakt:** Slugpfad ohne Deployment- oder Revision-ID. Wiederholung kann ueberschreiben oder abweichende SERPs unsichtbar ersetzen.
- **Downstream und Observability, Fakt:** Copywriter und 4b erhalten das Markdown. Roh-SERP, Query, Zeitpunkt, Top-URLs und Responsehash sind nicht verpflichtend persistiert.
- **Red-Team-Interpretation:** Das Briefingformat ist redaktionell hilfreich, aber die Bezeichnung Notion-ready und validated ist nicht belegt. Die Sample-Fixture hat nur acht statt mindestens 15 Triples (`tests/fixtures/sample_briefing.md:30-41`) und nur eine statt drei bis fuenf FAQs (`:86-99`), kann aber den aktuellen JSON-LD-Test passieren.

#### Schritt 4b: Landingpage HTML

- **Input und Preconditions, Fakt:** Manifest, CSS und 4a-Briefing (`prompts/4b-landingpage-html.xml.md:23-37`). GATE-4A-Approval wird nicht geprueft.
- **Execution, Fakt:** Standalone HTML mit Meta, CSS, JSON-LD, Local-SEO, FAQ, CTA und Footer (`:39-59`).
- **Output, Fakt:** `outputs/html/landingpage-[thema]-[ort].html` und Zaehler (`:60-81`).
- **State und Gate, Fakt:** Der Zaehler steigt vor GATE-4B. Ein globaler Zaehler beweist weder welche Seite noch deren Reviewstate (`standards/manifest.schema.json:557-580`; `prompts/4b-landingpage-html.xml.md:84-88`).
- **Failure, Fakt:** Nur fehlendes Briefing oder CSS hat `ERROR_INPUT_MISSING`. Keine Fehlerklasse fuer fehlendes NAP, unfreigegebenen Claim, fehlerhaften Canonical, CSS-Konflikt, CMS-Inkompatibilitaet oder fehlendes Tracking.
- **Resume/Retry/Idempotenz, Fakt:** Nicht spezifiziert. Keine Contenthash-Pruefung gegen freigegebenes Briefing und keine Diffgrenze fuer Copywriter-Aenderungen.
- **Downstream und Observability, Fakt:** Handoff an Frontend, aber kein Deployment-Artefakt, Importresultat, Staging-URL, Release-ID oder Messplan.
- **Red-Team-Interpretation:** Die Sample-Seite fehlt unter anderem NAP-Box, Karte, Sibling-Links, Sticky Mobile CTA, Footer und Breadcrumb-Schema (`tests/fixtures/sample_landingpage.html:78-117`), obwohl 4b diese fordert. Der aktuelle Acceptance-Test prueft nur JSON-LD.

### 5.2 Konkrete False-Green-Mechanismen

1. **Marker statt Verhalten:** TEST-05 prueft nur, dass neun Dateien Metadaten, Validation-Text und irgendein `ERROR_` oder `Regel` enthalten (`tests/run_acceptance_tests.py:64-71`). Ein Schritt ohne wirksame Failure-Transition kann bestehen.
2. **Positive Fixture gegen permissives Schema:** TEST-01 validiert genau ein lokales DE-Manifest (`tests/run_acceptance_tests.py:24-32`). Es gibt keine negativen Multi-Market-, falscher Country-Code-, unerlaubter State- oder YMYL-Faelle.
3. **Solver-Substring statt Vertrag:** TEST-02 sucht drei Texte im stdout (`tests/run_acceptance_tests.py:34-44`). Er prueft weder fehlende Metriken, unbekannte Typen, Inputreihenfolge, alle Pflichtseiten, Backlogintegritaet noch Wochenuntergrenze.
4. **JSON-LD lokale Teilvalidierung:** TEST-03 und TEST-06 akzeptieren `[BESTANDEN]` vom eigenen Validator (`tests/run_acceptance_tests.py:46-54`, `:73-86`). Das ist kein unabhaengiger Google-, Schema.org-, Truth- oder Claim-Nachweis.
5. **CSS Token Presence:** TEST-04 prueft drei Klassennamen und fehlendes `@import` (`tests/run_acceptance_tests.py:56-62`), nicht Rendering, Responsivitaet, Kontrast oder Brand Fidelity.
6. **Synthetische Metriken:** `sample_cluster_keywords.json` wird per Formel erzeugt (`scripts/generate_sample_keywords.py:13-24`, `:55-67`, `:92-105`). Dennoch dokumentiert `tests/acceptance-tests.md:17` genaue Planergebnisse, die keine reale Researchqualitaet beweisen.
7. **Selbstinkonsistente E2E-Fixtures:** Das Sample-Briefing verletzt 4a-Mindestmengen, die Sample-Landingpage verletzt 4b-Sektionen, und beide enthalten nicht manifestbelegte NAP-/Claim-Daten. TEST-06 prueft nur ihren JSON-LD-Block.
8. **Testzahl-Drift:** Dokumentation sagt 5 von 5 (`tests/acceptance-tests.md:7`), Runner listet sieben (`tests/run_acceptance_tests.py:108-116`). Ein gruen kommunizierter Status ist damit nicht einmal revisionsklar.
9. **Fixture-State umgeht Mengenregeln:** Das Sample-Manifest markiert Schritt 1 und 2 `completed`, enthaelt aber weder `clusters_per_pillar` noch `validated_rows_per_pillar` (`tests/fixtures/sample_manifest.json:125-147`). Weil diese Properties nicht required sind, validiert der unerwuenschte Zustand.
10. **Kein Neun-Schritt-E2E:** Kein Test erzeugt aus einem realen Intake ueber alle Schritte einen freigegebenen, importierten, gestagten und messbaren Output. Die Pilotcheckliste bestaetigt selbst, dass der erste Framework-Test keine Pilot-Abnahme war (`docs/06-pilot-abnahme-checkliste.md:78-86`).

### 5.3 Dokumentationswidersprueche

- CLI vorhanden versus CLI offen: `mcp/tools/validate_schema_jsonld.py:145-176` widerspricht `AGENTS.md:66-70`, `docs/06-pilot-abnahme-checkliste.md:63-68` und `CHANGELOG.md:75-82`.
- Produktionsstandard versus Pilot offen: README nennt den Status produktionsaktiv, waehrend `docs/06-pilot-abnahme-checkliste.md:78-86` alle Abschlussfreigaben offen laesst.
- Neun-Schritt-Sequenz: README beschreibt 3b als zeitversetzten Zyklus, der Migrationsplan fuehrt ihn teils linear zwischen 3 und 4a (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:106-112`, `:467-487`).
- CSS-Handoff: 4b verlangt eingebettetes CSS (`prompts/4b-landingpage-html.xml.md:39-42`), Gate 6 fragt nach Bindung des globalen CSS (`docs/05-human-in-the-loop.md:102-109`). Das sind verschiedene Integrationsmodelle.
- Notion: Frontmatter wird als automatisch erkannte Properties beschrieben (`docs/copywriter-handoff-guidelines.md:23-38`), waehrend die reale Notion-Datenstruktur und Mappings laut Migrationsplan noch offen sind (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:642-678`, `:744-759`).

## 6. Sollarchitektur beziehungsweise Korrekturempfehlung

### 6.1 Kanonische Traceability Chain

```text
Intake Source
  -> Assessment Revision
  -> Project + Market Deployment
  -> Step Run Envelope
  -> Research Request
  -> Provider Raw Evidence
  -> Normalized Evidence
  -> Decision Record
  -> Structured Output Artifact
  -> Rendered Markdown/CSV/HTML
  -> Validation Records
  -> Human Approval
  -> Notion Upsert + Task IDs
  -> CMS Implementation Revision
  -> Staging QA
  -> Deployment Record
  -> Measurement Plan
  -> Performance Evidence
  -> Adjustment Proposal
  -> Approved New Plan Revision
```

Jeder Pfeil benoetigt Parent-ID, Contenthash, Contractversion, Run-ID, Actor und Timestamp. Kein Pfadstring ersetzt eine Identitaet.

### 6.2 State Machine

Einheitlich fuer jeden Schritt und jedes einzelne 4a-/4b-Item:

```text
pending
  -> running
  -> validation_failed | awaiting_review
  -> rejected | approved
  -> handed_off
  -> implemented
  -> staging_verified
  -> deployed
  -> superseded
```

- Nur `approved` darf den fachlichen Folgeschritt starten.
- Retry verwendet denselben Idempotency-Key und eine neue Attempt-ID.
- Veraenderter Input erzeugt einen neuen Run und superseded den alten Output.
- 3b erstellt einen Vorschlag und nie einen In-place-Overwrite.
- Fehler besitzen Code, Klasse, Retryability, Remediation, Owner und Resume Token.

### 6.3 Outputvertraege pro Stufe

1. **0:** Strukturierter Intake plus `market_deployments[]`, Brands, Domains, Sites, Locations, Service Areas, GBPs, Personas, Workstreams, Risk/Compliance und Conversion Models.
2. **1:** Kanonisches Topic-Inventory JSON mit Crawl-Snapshot, Source URLs, Competitor Evidence, Hypothesen und Decision Records. Markdown ist View.
3. **1b:** URL Architecture JSON mit Existing/Proposed URL, Action, Redirect, Canonical, Navigation, Template Type, Market Deployment und Approval.
4. **1c:** Design Token JSON, Component Contract, Screenshot Evidence, Viewports, Accessibility Results und CMS Mapping.
5. **2:** Providerneutrales Keyword Dataset mit Query-ID, Market Deployment, Source, Retrieved At, Raw Hash, Normalizer Version und getrennten modellbasierten Scores.
6. **3:** Plan JSON mit stabiler Item-ID, Source Keyword IDs, Effort Policy Version, Capacity, Dependency Graph, Link Target IDs und Backlog.
7. **3b:** Performance Evidence plus immutable Adjustment Proposal und Approval.
8. **4a:** Briefing JSON/Markdown mit Source Item-ID, SERP Evidence IDs, Claim Evidence IDs, editorial status, compliance status, Notion external ID und JSON-LD Validation Records.
9. **4b:** CMS-neutraler Page Spec plus renderer-spezifische Pakete. HTML ist Preview, nicht automatisch Deploymentpaket.

### 6.4 WordPress- und Elementor-Grenze

- Heartweb-Domainlogik entscheidet Content, Struktur, Claims, Meta, Links und Schema Ownership.
- Ein CMS-Adapter entscheidet Widgets, Dynamic Tags, Formulare, Theme Styles, Consent, Assets und Importformat.
- Elementor-Paket enthaelt Templateversion, benoetigte Plugins, globale Style-IDs, Widgetbaum, Dynamic-Tag-Quellen und verbotene Raw-HTML-Bereiche.
- Vor Deployment: Staging Import, URL/Canonical/Redirect Check, Schema-Deduplizierung, Form- und Consent-Test, WCAG-Test, Responsive Screenshot-Diff, Event-Test und Contenthash-Abgleich.
- Nach Deployment: Release-ID, Live-URL, Rollback-Revision, GSC Inspection Task und Measurement Baseline.

### 6.5 Notion-, n8n- und Providergrenze

- Notion speichert operative Projektion, Approval und Tasks, nicht unversionierte Rohartefakte.
- Der Artefaktspeicher ist immutable; Notion speichert IDs, Hashes und Links.
- n8n orchestriert, darf aber Domaintransitionen nicht selbst erfinden. Es ruft Transition-, Validation- und Provideradapter auf.
- Webhook oder UI-Start wird ueber Idempotency-Key dedupliziert.
- Provideradapter liefern Rohantwort, normalisierte Evidenz, Marktvalidierung, Kosten und Fehler separat.
- Dead Letter, Retry-Budget, Rate Limit und Kostenbudget sind pro Run sichtbar.

## 7. Maschinenpruefbare Acceptance Criteria

| ID | Kriterium | Maschinenpruefung | Erwartetes Ergebnis |
|---|---|---|---|
| AC-01 | Jeder reale Archetyp ist ohne Sonderfelder modellierbar. | Zehn Fixtures aus der realen Matrix gegen Domain Schema validieren. | 10/10 positiv; jede Deployment-, Brand-, Domain-, GBP-, Sprache- und Marktphase eindeutig referenziert. |
| AC-02 | Leistungsort, Suchmarkt, Suchregion und Legal Jurisdiction sind getrennt. | Negative Fixtures mit vertauschten Relationen. | Validierung scheitert mit stabilem Error-Code. |
| AC-03 | Country, Provider-Code und Sprache koennen nicht falsch gepaart werden. | Parametrisierte Registry- und Adaptertests fuer jeden Markt. | Dispatch vor Providercall blockiert; keine Defaults. |
| AC-04 | Kein Schritt kann vor Approval abgeschlossen werden. | Transition-Contract-Test fuer jede erlaubte und verbotene Kante. | Alle verbotenen Transitionen liefern `ERROR_TRANSITION_NOT_ALLOWED`. |
| AC-05 | Completion setzt Pflichtmetriken voraus. | Negative Manifest-/Step-Record-Fixtures ohne Cluster-, Row-, Template-, Briefing- oder Landingpage-Nachweise. | `approved` und `completed` unmoeglich. |
| AC-06 | Retry ist idempotent. | Gleichen Request zehnmal mit demselben Idempotency-Key senden. | Genau ein fachlicher Run, ein Providerjob, ein Outputartefakt und ein Notion-Task. |
| AC-07 | Resume ueberlebt Prozessabbruch. | Run nach Providerqueue, Outputwrite und Human Gate jeweils abbrechen und fortsetzen. | Fortsetzung am letzten durable State ohne Duplicate oder Datenverlust. |
| AC-08 | Artefaktlineage ist vollstaendig. | Graphwalk von Live Page bis Intake Source. | Jede Kante besitzt Parent-ID, Hash, Run-ID, Contractversion und Validation Record. |
| AC-09 | 3b ist revisionssicher. | Performance-Run zweimal ausfuehren und Gate ablehnen. | Ursprungsplan unveraendert; Proposal immutable; kein zweiter Effekt. |
| AC-10 | Providerdaten und Modellscores bleiben getrennt. | Dataset-Schema und Provenienztest. | Jede Metrik hat Provider Evidence ID; jeder Score hat Scorer und Version. |
| AC-11 | Kosten und Quota sind begrenzt. | Stub fuer 429, 5xx, Timeout und Quota exhaustion. | Begrenzter Retry mit Jitter, kein Duplicate, sichtbarer Cost/Retry State, danach Dead Letter. |
| AC-12 | Briefingmengen werden erzwungen. | 4a-Contract-Tests fuer Hero, mindestens 15 Triples, 3 bis 5 FAQ, alle Pflichtsektionen und Links. | Untererfuellung scheitert vor Notion-Handoff. |
| AC-13 | Claims sind belegt. | YMYL-, Finance-, Travel- und Sustainability-Fixtures mit fehlender, veralteter und falscher Jurisdiction-Evidenz. | Output bleibt blockiert, bis Evidence und Required Reviewer approved sind. |
| AC-14 | Local Presence wird nicht erfunden. | Service-Area-Fall Sauerlach/Muenchen, nationaler B2B-Fall und physischer Standortfall. | Nur erlaubter Seitentyp und korrektes Schema; kein unberechtigtes GBP-/LocalBusiness-Markup. |
| AC-15 | JSON-LD-Pruefebenen sind ehrlich. | Negative Schemas fuer falsche NAP, unbekannten Typ, fehlendes about, FAQ-Mismatch und doppelte CMS-Graphen. | Separate parse-, contract-, schema-, eligibility- und evidence-Ergebnisse; kein pauschales 100 Prozent valide. |
| AC-16 | Notion-Upsert ist konfliktfest. | Create, Replay, stale revision und paralleler Approval-Write gegen Stub. | Eine Page pro External-ID; stale write wird abgelehnt; Approval bleibt erhalten. |
| AC-17 | WordPress-/Elementor-Handoff ist reproduzierbar. | Frische Staging-Site importiert freigegebenes Paket. | Inhaltshash stimmt, keine doppelten Schemas, keine fehlenden Widgets/Assets, kein manuelles Nachbauen. |
| AC-18 | Frontend-QA ist vollstaendig. | Automatisierte HTML-, Accessibility-, Responsive-, Link-, Form-, Consent- und Event-Checks auf Staging. | Null kritische Fehler und alle definierten Viewports bestanden. |
| AC-19 | Measurement Loop passt zum Conversion Model. | Tests fuer Lead, Booking, Upload/Quote, Bewerbung, OTA und GBP. | Jede Seite hat messbare Events, Source IDs, Baseline und Datenvollstaendigkeitsstatus. |
| AC-20 | Ein echter Neun-Schritt-Lauf besteht. | Realer Pilot von freigegebenem Intake bis Staging, Notion-Tasks und Messbaseline. | Alle neun Schritte, Gates, Artefakte und Handoffs mit Auditgraph; keine manuelle Sonderlogik. |
| AC-21 | False-Green-Fixtures werden rot. | Aktuelle `sample_briefing.md`, `sample_landingpage.html` und unvollstaendiges completed Manifest gegen neue Vertraege pruefen. | Alle drei scheitern mit konkreten Codes. |
| AC-22 | Dokumentationsstatus ist reproduzierbar. | Release-Matrix gegen Prompt-, Schema-, Tool- und Testrunner-Versionen. | Null Versions-, Testzahl- oder CLI-Widersprueche. |

## 8. Go, Conditional Go oder No-Go

### Entscheidung

**No-Go.**

### Gilt fuer

- Automatisierte Produktion ueber UI, n8n und Notion
- Automatisches Erstellen oder Freigeben von Copywriter-Tasks
- WordPress- oder Elementor-Deployment
- Internationale, mehrsprachige und Multi-Market-Kunden
- Programmatic Local, Satellitendomains, mehrere Marken oder GBPs
- YMYL Medizin, Pflege, Finanzen und andere regulierte oder sensible Claims
- Aussage `produktionsreif`, `vollstaendig validiert`, `Notion-ready` oder `100% valide`

### Eng begrenzte Conditional-Go-Ausnahme

Ein manueller interner Lernpilot ist vertretbar, wenn alle folgenden Bedingungen gleichzeitig gelten:

1. Ein Markt DE, AT oder CH, eine Sprache, eine Domain und eine verifizierte Brand-/Service-Area-Konstellation.
2. Keine automatisierte Publikation und keine automatische Notion-Freigabe.
3. Jede Gate-Entscheidung wird extern dokumentiert und von Raphael Rechberger bestaetigt.
4. Jede fachliche, lokale, rechtliche und YMYL-Aussage wird ausserhalb des aktuellen Systems belegt und reviewed.
5. HTML wird nur als Referenz an Entwicklung gegeben, nicht als importfertiges Elementor-Paket bezeichnet.
6. Performanceaenderungen werden als Vorschlag gespeichert, der Ursprungsplan bleibt unveraendert.

Diese Ausnahme ist kein Deployment-Go und kein Nachweis fuer die zehn realen Use Cases.

## 9. Exakte Dateien, Tests und naechste Fix-Reihenfolge

### Fix 1: Kanonisches Domain- und Traceability-Modell

**Dateien neu oder zu ersetzen:**

- `standards/project.schema.json`
- `standards/market-deployment.schema.json`
- `standards/entity-location-domain-gbp.schema.json`
- `standards/risk-compliance.schema.json`
- `standards/step-run.schema.json`
- `standards/artifact-envelope.schema.json`
- `standards/transition.schema.json`
- Migration von `standards/manifest.schema.json`

**Tests zuerst:**

- `tests/contracts/test_real_customer_matrix.py`
- `tests/contracts/test_market_relationships.py`
- `tests/contracts/test_transition_state_machine.py`
- `tests/contracts/test_artifact_lineage.py`
- Negative Fixtures fuer alle zehn Realfaelle und verbotene Zustandskombinationen

### Fix 2: Outputschemas fuer alle neun Schritte

**Dateien:**

- `standards/outputs/step-0-manifest.schema.json`
- `standards/outputs/step-1-topic-inventory.schema.json`
- `standards/outputs/step-1b-site-architecture.schema.json`
- `standards/outputs/step-1c-design-system.schema.json`
- `standards/outputs/step-2-keyword-dataset.schema.json`
- `standards/outputs/step-3-plan.schema.json`
- `standards/outputs/step-3b-adjustment-proposal.schema.json`
- `standards/outputs/step-4a-briefing.schema.json`
- `standards/outputs/step-4b-page-spec.schema.json`
- Aktualisierung `standards/dateinamen-und-output-vertrag.md`

**Tests:**

- `tests/contracts/test_all_step_outputs.py`
- `tests/contracts/test_cross_output_references.py`
- `tests/contracts/test_retry_and_revision_semantics.py`

### Fix 3: YMYL, Claims und Local-Presence Policy

**Dateien:**

- `standards/evidence-record.schema.json`
- `standards/claim.schema.json`
- `standards/location-page-policy.schema.json`
- `standards/compliance-review.schema.json`
- Policy-Implementierung in einer runtime-neutralen Domainbibliothek
- Aktualisierung von `prompts/0-kickoff.xml.md`, `prompts/1-pillar-identifikation.xml.md`, `prompts/4a-content-briefing-und-schema.xml.md`, `prompts/4b-landingpage-html.xml.md`

**Tests:**

- `tests/policy/test_ymyl_claim_evidence.py`
- `tests/policy/test_local_presence_and_gbp.py`
- `tests/policy/test_market_jurisdiction.py`
- Fixtures fuer AHD, Epargne Plurielle, Pflegedienst Sauerlach, MobilePhysiotherapie24 und beide Shunyata-Faelle

### Fix 4: Providerneutraler Gateway und Evidence Store

**Dateien:**

- Ersatz fuer `mcp/tool-contracts/agentseo_keyword_enricher.json`
- Ersatz fuer `mcp/tool-contracts/serp_gap_analyzer.json`
- `services/research_gateway/contracts.py`
- Adapter fuer DataForSEO und AgentSEO
- Durable Job Store, Idempotency, Retry, Budget und Dead Letter
- Candidate `services/agentseo_gateway/core.py` nur nach Einordnung in die Host-Baseline integrieren

**Tests:**

- `tests/integration/test_provider_gateway_contract.py`
- `tests/integration/test_provider_geo_mismatch.py`
- `tests/integration/test_provider_idempotency.py`
- `tests/integration/test_provider_retry_budget.py`
- Lokale Stubs, keine kostenpflichtigen Livecalls in Acceptance

### Fix 5: 4a-Briefing, JSON-LD und Notion-Handoff

**Dateien:**

- `prompts/4a-content-briefing-und-schema.xml.md`
- `mcp/tools/validate_schema_jsonld.py`
- `mcp/tool-contracts/schema_jsonld_generator.json`
- `standards/notion/briefing-property-map.json`
- `standards/notion/workflow-status-map.json`
- Notion-Adapter mit External-ID und expected revision

**Tests:**

- `tests/contracts/test_briefing_contract.py`
- `tests/contracts/test_claim_to_schema_consistency.py`
- `tests/integration/test_notion_idempotent_upsert.py`
- `tests/integration/test_notion_stale_revision.py`
- Negative Tests gegen aktuelle `sample_briefing.md`

### Fix 6: 4b und WordPress-/Elementor-Deploymentvertrag

**Dateien:**

- `standards/cms/page-spec.schema.json`
- `standards/cms/elementor-package.schema.json`
- `standards/cms/wordpress-deployment.schema.json`
- `prompts/4b-landingpage-html.xml.md`
- CMS-Adapter und Staging-Validator
- Design Token JSON als Quelle fuer `standards/design-system.css`

**Tests:**

- `tests/cms/test_elementor_package_import.py`
- `tests/cms/test_schema_ownership_no_duplicates.py`
- `tests/cms/test_content_hash_matches_approved_briefing.py`
- `tests/cms/test_forms_consent_tracking.py`
- `tests/cms/test_accessibility_and_responsive_contract.py`
- Negative Tests gegen aktuelle `sample_landingpage.html`

### Fix 7: Planrevision und Measurement Loop

**Dateien:**

- `prompts/3-120-tage-plan.xml.md`
- `prompts/3b-performance-check.xml.md`
- `mcp/tools/capacity_matrix_solver.py`
- `standards/measurement-plan.schema.json`
- `standards/performance-evidence.schema.json`

**Tests:**

- `tests/tools/test_solver_missing_metrics_fail_fast.py`
- `tests/tools/test_solver_unknown_content_type.py`
- `tests/tools/test_solver_mandatory_and_backlog_integrity.py`
- `tests/workflow/test_3b_creates_revisioned_proposal.py`
- `tests/workflow/test_conversion_models.py`

### Fix 8: Vollstaendige Neun-Schritt-Acceptance und Dokumentationsbereinigung

**Dateien:**

- Ersatz fuer `tests/run_acceptance_tests.py`
- Ersatz fuer `tests/acceptance-tests.md` durch generierten Report
- Aktualisierung `README.md`, `AGENTS.md`, `00_admin/PROJECT_STATE.md`, `CHANGELOG.md`, `docs/03-sprint-plan.md`, `docs/05-human-in-the-loop.md`, `docs/06-pilot-abnahme-checkliste.md`, `docs/copywriter-handoff-guidelines.md`
- Aktualisierung des Migrationsplans erst nach bestaetigtem Notion-Control-Model

**Tests und Abnahme:**

- Ein echter Single-Market-Pilot
- Ein echter Multi-Market-/Multi-Language-Pilot
- Ein YMYL-Pilot mit Claim Evidence und Legal Gate
- Ein nationaler B2B-Pilot ohne Local-SEO-Fehlklassifikation
- Ein Programmatic-Local-Pilot mit Scale-, Uniqueness- und GBP-Policy
- End-to-End von Intake ueber Notion und n8n bis Elementor-Staging, Deployment Record und Measurement Baseline

### Verbindliche Reihenfolge

`Fix 1 -> Fix 2 -> Fix 3 -> Fix 4 -> Fix 5 -> Fix 6 -> Fix 7 -> Fix 8`

Kein Fix ab 4 darf die alten Single-Market-, unversionierten Artefakt- oder freien Statusfelder als langfristigen Vertrag konservieren. Erst nach bestandenem Fix 8 darf der Deployment-Status neu bewertet werden.
