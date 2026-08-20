# Fundamental Heartweb Workflow Master Audit

- Autor: Raphael Rechberger
- Datum: 19. August 2026
- Repository: `Heartweb-Claude-Desktop-SEO-Workflow`
- Auditmodus: Vier OMO-Lanes plus unabhaengige Hermes-Sol-Verifikation
- Ziel: Professionelle, internationale, reproduzierbare SEO/GEO-Domainlogik fuer eigene UI, n8n und Notion
- Ergebnis: No-Go fuer Produktion, Conditional Go fuer kontrollierte Weiterentwicklung nach Foundation Gate

## 1. Executive Verdict

Der aktuelle Repository-Stand ist **kein produktionsreifer End-to-End-Workflow** fuer die zehn realen Heartweb-Kunden, keine deploybare n8n-Runtime und keine belastbare Notion-Control-Plane.

Er ist ein wertvoller, bereits weit entwickelter fachlicher Prototyp mit:

- einer nachvollziehbaren neunstufigen Artefaktkette,
- gutem Fail-fast-Zielbild,
- einem stark verbesserten Schritt 0,
- sinnvollen Human-Gate-Ideen,
- brauchbaren deterministischen Werkzeugen,
- einer fundierten Providerstrategie,
- einem guten Migrationsplan,
- und einer soliden Grundlage fuer die naechste Vertragsarchitektur.

Die groesste Luecke ist nicht fehlender Prompttext. Die groesste Luecke ist, dass zentrale Qualitaetsregeln nur als Prosa existieren und nicht als erzwingbare Domain-, State-, Gate-, Artefakt-, Evidence- und Providervertraege.

### Verbindliches Gesamturteil

| Ziel | Urteil |
|---|---|
| Automatisierte Kundenproduktion | No-Go |
| Internationale und mehrsprachige Kunden | No-Go |
| n8n-Produktionsruntime | No-Go |
| Notion als sichere operative Control Plane | No-Go im aktuellen Implementierungsstand |
| Automatisches Copywriter-Handoff | No-Go |
| WordPress-/Elementor-Deployment | No-Go |
| YMYL-Medizin, Pflege und Finanzen | No-Go ohne neue Evidence- und Compliance-Gates |
| Weiterentwicklung des Frameworks | Go |
| AHD Schritt 0 | Bestanden im lokalen Kandidatenstand |
| AHD Schritt 1 | Conditional Go erst nach Foundation Gate A |
| Interner Lernpilot | Moeglich mit manueller Kontrolle und ohne Produktionsfreigabe |

## 2. Was der Audit real bewiesen hat

### 2.1 Reale Kundenabdeckung

Die zehn realen Briefings umfassen mindestens folgende Archetypen:

- lokaler medizinischer Service,
- regionaler Pflegedienst,
- nationale B2B-Dienstleistung,
- persoenliche Speaker-Marke mit internationaler Expansion,
- Cross-Border-Finanzprodukt,
- sensibles Ausbildungs- und Retreat-Angebot,
- regionale Ein-Personen-Expertenmarke,
- aggressives Programmatic-Local-Netzwerk mit Satellitendomains,
- Ayurveda-Resort in Sri Lanka mit DACH- und spaeter internationalem Zielmarkt,
- internationales englischsprachiges Resort mit OTA- und Social-Workstreams.

Das aktuelle Manifest kann dagegen genau einen Zielmarkt, einen `location_code`, eine Sprache, eine Domain und eine primaere Region fuehren. Es kann Leistungsort, Suchmarkt, Suchregion, Sprache, Locale, Legal Jurisdiction, Marktphase, Marke, Domain, Satellit, GBP und Service Area nicht sauber voneinander trennen.

### 2.2 Reale Ausfuehrungsevidenz

Der einzige echte kanonische Kundenlauf ist:

`C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\ahd-hausbesuch\STAGING-20260818-001`

Verifiziert:

- Schritt 0 abgeschlossen
- Gate 0 approved with warnings
- Manifest schema-valid
- Marke, Leistungen, Regionen und Workstreams semantisch getrennt
- alle weiteren Phasen pending
- kein Pillar-, Cluster-, Architektur-, Plan-, Briefing-, HTML- oder Performance-Output vorhanden

Damit ist die Aussage `Produktionsstandard aktiv und validiert` im README nicht durch einen realen End-to-End-Kundenlauf gedeckt.

### 2.3 Tests

Host-Umgebung:

- Acceptance Runner: 7 von 7
- Unit Discovery: 17 Tests

OMO-Container:

- Acceptance Runner: 6 von 7, weil `jsonschema` nicht als reproduzierbare Projektabhaengigkeit installiert war
- Unit Discovery: 17 Tests
- Python Compileall: bestanden

Die Differenz beweist eine fehlende reproduzierbare Dependency- und CI-Definition.

Die aktuellen Tests sind Smoke-Tests, keine Produktionsabnahme:

- Prompttests pruefen vor allem Stringmarker.
- Solvertest prueft Textfragmente im Output.
- Validatorpruefung prueft den eigenen Validator mit positiver Fixture.
- Designsystemtest prueft drei Klassennamen.
- Es gibt keinen vollstaendigen realen Neun-Schritt-Trace.
- Es gibt keine negative internationale, YMYL-, State-, Gate-, Notion-, n8n-, CMS- oder Provider-Acceptance.

### 2.4 Unabhaengig reproduzierte False Greens

Der JSON-LD-Validator meldete im Strict Mode ein Article mit:

- `datePublished: "bad"`
- leerem `about: [{}]`

als `valid: true`.

Der Capacity Solver akzeptierte eine leere Eingabeliste und lieferte 17 leere Wochen statt eines Fehlers.

Diese beiden Befunde widerlegen die aktuelle Behauptung einer durchgehend strikten Fail-fast-Pipeline.

## 3. Was wirklich stark ist

Die vorhandene Arbeit wird nicht verworfen.

### 3.1 Artefaktkette

Die Sequenz vom Intake bis zu Briefing, HTML und Performance ist fachlich nachvollziehbar:

`0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`

Schritt 3b ist ein separater zeitversetzter Post-Publication-Loop fuer Tag 30, 60 und 90.

### 3.2 Schritt 0

Prompt 0 v1.5.0 ist das staerkste aktuelle Vertragsmuster:

- Inputvalidierung
- Wettbewerber-Preflight
- semantische Klassifizierung
- Schema-Validierung
- `in_progress` vor Gate
- explizite Freigabe vor `completed`

Dieses Muster muss auf alle Schritte uebertragen werden.

### 3.3 Deterministische Tools

Der Solver trennt Allokation und Rendering, weist Backlog aus und verhindert die LLM-Arithmetik als alleinige Planungsgrundlage.

Der JSON-LD-Validator besitzt eine echte CLI und strukturierte Exit-Codes. Seine Semantik ist noch zu schwach, aber die Werkzeuggrenze ist richtig.

### 3.4 Providerstrategie

Die Research-Evidenz stuetzt:

- DataForSEO als Default fuer skalierbare Keyword-, Labs- und SERP-Rohdaten
- AgentSEO selektiv fuer semantische Mehrwerte
- unveraenderte Raw Payloads
- eigene kanonische Normalisierung
- strikte Geo-Pruefung

Die Formulierung `Hermes-eigene Synthese` muss fuer Production durch `Heartweb Domain Service` beziehungsweise `versionierte Workflow-Synthese` ersetzt werden.

### 3.5 Zielarchitektur

Der Migrationsplan trennt die Rollen grundsaetzlich richtig:

- Notion als zentrale menschliche Control Plane
- eigene UI als spezialisierte Bedienoberflaeche
- n8n als Orchestrator
- Repository als versionierte Domainlogik
- Artefaktspeicher fuer grosse Outputs
- OpenCode OMO nur fuer Entwicklung und QA
- Claude Desktop nicht als spaetere Production Runtime

Diese Grundentscheidung bleibt bestehen.

## 4. Konsolidierte P0-Blocker

## P0-1: Unzureichendes Domain- und Marktmodell

Das aktuelle Schema kann mehrere reale Kunden nicht ohne manuelle Sonderlogik darstellen.

Erforderlich sind getrennte, versionierte Entitaeten fuer:

- Tenant
- Kunde
- Marke
- Domain und Website
- physische Location
- Service Area
- Search Deployment
- Land und Provider-Codes
- Sprache und Locale
- Legal Jurisdiction
- Marktphase
- GBP
- Workstream
- Conversion Model
- Risk und Compliance

Ein einzelnes `country`, `location_code` und `language` muss durch `market_deployments[]` ersetzt werden.

## P0-2: Keine erzwingbare State Machine

Nur Gate 0 ist strukturiert. Schritte 1, 1b, 1c, 2 und 3 setzen sich vor ihrem Human Gate auf `completed`.

Prompts besitzen neun Gate-IDs. Die Human-Gate-Dokumentation beschreibt sieben anders nummerierte Gates. Das Manifest kennt nur `gate_0`.

Erforderlich:

- ein kanonischer Workflowgraph
- stabile Step- und Gate-IDs
- erlaubte Transitionen
- Revision
- Run-ID
- Input- und Outputhash
- Validatorrecords
- Approvalrecord
- Fehlerobjekt
- Retry- und Supersession-Semantik

Nur ein Domain-Transition-Service darf Status aendern. Weder UI, Notion noch n8n duerfen Regeln duplizieren oder freie Statusfelder schreiben.

## P0-3: Keine YMYL-, Claims- und Local-Presence-Policy

Der aktuelle Workflow fordert definitive Aussagen und harte Datenpunkte, ohne Quellen- und Freigabepflicht.

Erforderlich pro Claim:

- Evidence-ID
- Quelle und Herausgeber
- URL oder Dokumentreferenz
- Abrufdatum
- Gueltigkeitszeitraum
- Jurisdiction
- Claim-Typ
- Disclaimer-Policy
- Reviewer-Policy
- Freigabestatus

LocalBusiness-, NAP-, Karten-, Testimonial- und GBP-Ausgaben duerfen nur aus verifizierten strukturierten Location- und Service-Area-Daten entstehen.

## P0-4: Unsicherer Provider- und Geo-Pfad

Der implementierte Candidate-Gateway ist nicht der verbindliche Production-Eingang. Desktop und Prompts koennen AgentSEO weiterhin direkt ansprechen.

Prompt 4a erlaubt einen bekannten geo-fehlerhaften AgentSEO-SERP-Pfad und besitzt keinen expliziten Fehlervertrag.

Erforderlich:

- ein providerneutraler Research-Gateway
- verpflichtende Market-Deployment-ID
- Location Name, Code, Sprache, Locale und Device
- Capability Routing
- Idempotency-Key
- Request-Hash
- Provider-Job-ID
- Kostenbudget
- Raw Response Hash
- Geo-Response-Validierung
- Retry und Dead Letter

## P0-5: Keine revisionssichere Human Approval

Eine Freigabe muss an genau eine Artefaktversion gebunden sein:

- Gate-ID
- Run-ID
- Artifact-ID
- SHA-256
- Policy-Version
- Reviewer-ID
- Entscheidung
- Grund
- Zeitpunkt
- Ablaufzeit

Eine neue Artefaktversion invalidiert die alte Freigabe. Resume-Tokens muessen authentifiziert, einmalig, kurzlebig und revisionsgebunden sein.

## P0-6: Keine Mandanten-, RBAC- und Credential-Isolation

Lokale Kundenordner sind keine ausreichende Production-Isolation.

Jeder Run, Artefakt-Key, Notion-Datensatz, Providerjob und Credential-Alias braucht `tenant_id`.

UI und Worker erhalten nur freigegebene Actions und Secret-Aliase. Secrets duerfen nie in Manifest, Notion, Prompt, Log oder Artefakt landen.

## 5. Wichtige P1-Befunde

### 5.1 Deterministische Tools sind nicht fail-fast genug

Solver:

- akzeptiert leere Eingabe
- ersetzt fehlende Metriken durch 0
- verwendet Default-Aufwand fuer unbekannte Content-Typen
- erzwingt Wochenuntergrenze nicht

Validator:

- prueft nur lokale Pflichtfeldlisten
- akzeptiert unbekannte Typen
- prueft Datums-, URL-, Address- und Graph-Semantik unzureichend
- sagt `100% valide`, obwohl nur eine begrenzte Pruefebene gemeint ist

### 5.2 Outputvertraege sind Prosa

Markdown, CSV und HTML besitzen keine geschlossenen maschinenlesbaren Schemas.

Erforderlich sind strukturierte kanonische Outputs fuer alle Schritte. Markdown, CSV, HTML und Notion-Payloads werden daraus gerendert.

### 5.3 Keine Artefakt-Provenienz

Pfade ersetzen aktuell Identitaet.

Jedes Artefakt braucht:

- Artifact-ID
- Tenant- und Project-ID
- Market Deployment
- Step und Run
- Revision
- Parent-Artefakte
- Inputhash
- Contenthash
- Contractversion
- Producer-Version
- Validationrecords
- Reviewstate

Schritt 3b darf den Plan nicht ueberschreiben. Er erzeugt ein immutable Adjustment Proposal und nach Freigabe eine neue Planrevision.

### 5.4 Notion-Frontmatter ist kein Notion-Vertrag

YAML-Frontmatter erzeugt nicht automatisch eine belastbare Notion Data Source.

Erforderlich:

- Data-Source-ID
- stabile Property-IDs
- Typen und Enums
- Relations
- User-Mapping
- External-ID
- Revision
- idempotenter Upsert
- Conflict-Policy
- Schema-Drift-Blocker

### 5.5 WordPress und Elementor sind nicht deploybar spezifiziert

Standalone HTML ist ein Preview- oder Referenzartefakt, kein Elementor-Deploymentpaket.

Erforderlich sind CMS-spezifische Adapter und Vertrage fuer:

- Template-JSON oder Widget-Spec
- Theme und globale Styles
- Dynamic Tags
- Forms
- Consent
- Tracking
- Schema Ownership
- Assets
- URLs und Redirects
- Accessibility
- responsive Breakpoints
- Staging Screenshot Diff
- Contenthash
- Rollback

### 5.6 Measurement Loop ist fachlich zu schwach

GSC-Klicks, Impressionen und Position reichen nicht fuer alle Kundenmodelle.

Conversion Models umfassen unter anderem:

- Lead
- Telefonanruf
- Buchung
- Beratung
- Upload und Quote
- Bewerbung
- OTA
- GBP-Aktion

Schritt 3b braucht Baseline, Vergleichsfenster, Source IDs, Datenvollstaendigkeit, Konfidenz und Freigabe.

## 6. Korrekte Zielarchitektur

## 6.1 Notion Control Plane

Notion bleibt das zentrale operative Steuerelement fuer Menschen:

- Kunden
- Assessments
- Projekte
- Statusprojektionen
- Gates
- Tasks
- Verantwortliche
- Blocker
- Artefaktlinks

Notion ist nicht der einzige transaktionale Execution-State.

Notion-Webhooks sind Signale. Sie koennen aggregiert, verspaetet und ungeordnet eintreffen. Nach jedem Event muss der aktuelle API-Stand erneut gelesen und per Event-ID sowie Revision reconciled werden.

## 6.2 Operations API

Eine schmale, Hermes-neutrale API:

- authentifiziert UI-Akteure
- erzwingt Tenant und RBAC
- validiert Commands
- prueft `expected_revision`
- erzeugt stabile Fehlercodes
- liefert Projektionen

Die UI schreibt weder direkt in Notion noch ruft sie rohe n8n-Webhooks oder Resume-URLs auf.

## 6.3 n8n Orchestrator

n8n:

- fuehrt den kanonischen Workflowgraphen aus
- verwendet typisierte Subworkflows
- begrenzt Concurrency
- verwaltet technische Execution-Persistenz
- nutzt Wait Gates und Error Workflows
- fuehrt Retry, DLQ und Replay aus
- orchestriert Provider, Tools, Artefakte und Notion

Die n8n-eigene Datenbank ist technische Runtime-Persistenz. Sie wird nicht zur neuen fachlichen PostgreSQL-Source-of-Truth fuer Kunden.

## 6.4 Domain und Transition Service

Das Repository liefert geschlossene Schemas und deterministische Validatoren fuer:

- Domainobjekte
- Workflowgraph
- Transitionen
- Gates
- Artefakte
- Evidence
- Claims
- Providerjobs
- Audit-Events
- Kostenbudgets
- Policies

## 6.5 Research Gateway

Capability-basierte Adapter:

- DataForSEO als Default fuer Keywords, Labs und SERP-Rohdaten
- AgentSEO selektiv fuer begruendete semantische Mehrwerte
- spaeter GSC, GBP, Analytics, Screaming Frog, Ahrefs und weitere Quellen

Jede Antwort wird raw gespeichert, validiert und in ein kanonisches Evidence-Schema normalisiert.

## 6.6 Artefaktspeicher

Unveraenderliche tenant- und rungebundene Objekte:

`tenants/<tenant_id>/projects/<project_id>/runs/<run_id>/artifacts/<artifact_id>/<filename>`

Notion speichert Metadaten, Status und kontrollierte Links.

## 6.7 Audit und Observability

Append-only Audit-Events liegen ausserhalb des Notion-Write-Pfads. Notion erhaelt eine menschenlesbare Projektion.

Jedes Event fuehrt mindestens:

- tenant_id
- run_id
- execution_id
- step_id
- operation_id
- attempt
- actor
- provider_job_id
- error_code
- retry_class
- Kosten
- Zeitstempel

## 7. Verbindliche Fix-Reihenfolge

Die Reihenfolge ist wichtiger als Einzelprompt-Optimierung.

### Foundation Gate A: Domain und State vor Schritt 1

1. Aktuellen v1.5-Kandidaten als Legacy Pilot Contract einfrieren.
2. Reifegrad-Claims in README und Project State auf Candidate/Pilot korrigieren.
3. Versioniertes Domainmodell erstellen.
4. `market_deployments[]` und Market Registry erstellen.
5. Maschinenlesbaren Workflowgraphen erstellen.
6. Transition-, Gate-, Run- und Error-Envelopes erstellen.
7. Artifact- und Evidence-Envelopes erstellen.
8. Zehn reale positive Fixtures plus negative Fixtures erstellen.

**AHD Schritt 1 darf erst beginnen, wenn Foundation Gate A gruen ist.**

### Foundation Gate B: Research und Tools vor Schritt 2

1. Providerneutralen Research-Gateway definieren.
2. DataForSEO- und AgentSEO-Adapter gegen Stubs bauen.
3. Geo-, Idempotency-, Retry-, Budget- und Resume-Tests erstellen.
4. Solver auf harten Inputvertrag umstellen.
5. JSON-LD-Validator in ehrliche Pruefebenen aufteilen.
6. Reproduzierbare Dependencies und CI definieren.

### Foundation Gate C: Outputs vor 4a

1. Outputschemas fuer 1, 1b, 1c, 2 und 3.
2. YMYL-, Claim-, Evidence- und Compliance-Policy.
3. 4a-Briefingvertrag.
4. Notion Property Mapping und idempotenter Upsert.
5. SERP Evidence und Claim Evidence Pflicht.

### Foundation Gate D: CMS vor 4b

1. CMS-neutrale Page Spec.
2. Elementor- und WordPress-Adaptervertrag.
3. Schema Ownership und Deduplizierung.
4. Forms-, Consent- und Trackingvertrag.
5. Staging-, Accessibility-, Responsive- und Visual-Regression-Gates.
6. Deployment- und Rollbackrecord.

### Foundation Gate E: n8n Vertical Slice

1. Ein kostenfreier Stub-Vertical-Slice.
2. UI Command mit Revision.
3. n8n Transition.
4. immutable Artefakt.
5. Notion Projektion.
6. Human Wait Gate.
7. Error Workflow und DLQ.
8. Worker-Restart und Resume.

Erst danach werden alle Schritte migriert.

## 8. Kontrollierter Weg zum ersten vollstaendigen AHD-Lauf

Der Audit blockiert nicht das Lernen. Er blockiert falsche Produktionsbehauptungen.

### Jetzt erlaubt

- Framework-Vertraege bauen
- negative Tests erstellen
- AHD als anonymisierte reale Fixture verwenden
- jeden Schritt in Staging manuell pruefen
- Provider-Stubs verwenden
- Outputs gemeinsam mit Raphael fachlich reviewen

### Noch nicht erlaubt

- automatisches Notion-Handoff als freigegeben
- automatische Copywriter-Tasks
- automatische Provider-Retries ohne Idempotenz und Budget
- automatisches WordPress-/Elementor-Deployment
- ungepruefte YMYL-Claims
- Produktionslabel

### Reihenfolge fuer AHD

1. Foundation Gate A implementieren.
2. AHD Manifest auf Domainmodell v2 migrieren.
3. Schritt 1 gegen strukturiertes Topic-Inventory ausfuehren.
4. Gate 1 revisionssicher freigeben.
5. Schritt 1b und 1c mit Outputschemas und Gate Records.
6. Foundation Gate B abschliessen.
7. Schritt 2 und 3 mit Provider-Stubs oder spaeter freigegebenen echten Daten.
8. Foundation Gate C abschliessen.
9. Schritt 4a mit Claim Evidence und Compliance Gate.
10. Foundation Gate D abschliessen.
11. Schritt 4b als Page Spec plus Preview, nicht sofort als Elementor-Deployment.
12. Publication- und Measurement-Baseline definieren.
13. 3b erst nach Publikation und realem Zeitfenster starten.

## 9. Maschinenpruefbare Master-Acceptance

Der Audit gilt erst als umgesetzt, wenn mindestens folgende Nachweise existieren:

1. Alle zehn realen Kundenfixtures validieren ohne freie Zusatzfelder und Sonderlogik.
2. Falsche Markt-, Sprach-, Locale-, Jurisdiction- und Location-Kombinationen werden abgelehnt.
3. Kein Schritt kann ohne freigegebenen Vorgaenger, Pflichtartefakte und Gate Record approved oder completed werden.
4. Human Approval ist an Artefakt-ID, SHA-256, Policy-Version und Revision gebunden.
5. Retry mit identischem Idempotency-Key erzeugt genau einen fachlichen Seiteneffekt.
6. Worker-Restart setzt denselben Providerjob und Run fort.
7. Solver lehnt leere oder unvollstaendige Inputs und unbekannte Content-Typen ab.
8. JSON-LD-Pruefung trennt Syntax, Contract, Schema.org, Google Eligibility, Entity Evidence und Claim Approval.
9. Aktuelle False-Green-Fixtures werden in den neuen Tests rot.
10. Notion-Webhooks werden dedupliziert und durch erneuten API-Read reconciled.
11. Stale Revisionen werden mit stabilem Conflict-Code abgelehnt.
12. Cross-Tenant-Zugriffe werden ohne Metadatenleck blockiert.
13. Providerdispatch stoppt vor Kostenueberschreitung.
14. Notion-Ausfall verhindert Audit Log und DLQ nicht.
15. 3b erzeugt eine neue Planrevision und veraendert nie den freigegebenen Ursprungsplan in-place.
16. Elementor-Staging importiert das freigegebene Paket ohne manuelles Nachbauen.
17. Forms, Consent, Tracking, Accessibility, Responsive und Schema-Deduplizierung bestehen.
18. Ein echter AHD-Lauf durchlaeuft alle Initialschritte mit vollständigem Auditgraph.
19. Ein zweiter internationaler oder mehrsprachiger Archetyp besteht.
20. Ein Programmatic-Local-Archetyp besteht, bevor diese Skalierung produktiv freigegeben wird.

## 10. OMO-Agenten-Audit und Betriebsfix

Der Audit deckte einen eigenen OMO-Orchestrierungsfehler auf.

### Fehlerursache

Hermes adressierte Spezialagenten direkt ueber `--agent`:

- Prometheus blieb im Plan-Approval-Modus.
- Atlas erzeugte keine Reports.
- Hephaestus lieferte direkt, aber ausserhalb der OMO-Orchestratorhierarchie.
- Sisyphus in `opencode run` startete interne Background Tasks, aber der One-shot-Client beendete sich vor den Completion-Events.

### Erfolgreiches Muster

- Externer Einstieg nur ueber Sisyphus.
- Persistente `opencode attach` TUI-Session.
- Interne Delegation durch Sisyphus.
- Session bleibt bis zu den Completion-Events offen.
- Erfolg wird an Artefakten und Tests gemessen.
- Hermes verifiziert unabhaengig.

### Dauerhafte Fixes

- Orchestrator-only-Regel im Hermes-Skill.
- Fester Launcher `/scripts/attach-orchestrator.sh`.
- `Sisyphus-Junior` von Luna auf Terra umgestellt.
- OMO-Kategorie `deep` auf Terra mit hoher Reasoning-Stufe gesetzt.
- Oracle bleibt Sol.
- Explore und Librarian bleiben Luna.
- CURRENT_STATE.md aktualisiert.
- Ctrl+C-Pitfall dokumentiert. Nach Artefaktpruefung wird nur der lokale Attach-Client mit `process.kill` beendet.

### Transparenz zu diesem Audit

- Lane 1 und Lane 2 wurden vor dem Betriebsfix direkt durch Hephaestus/Terra erstellt.
- Lane 3 und Lane 4 wurden ueber die persistente Sisyphus-Orchestratorsession intern erstellt.
- Vor der Routingkorrektur liefen interne `Sisyphus-Junior`-Worker noch auf Luna.
- Alle vier Reports wurden von Hermes Sol unabhaengig gegen Repository, Tests und offizielle Quellen verifiziert.
- Fuer kuenftige OMO-Arbeit ist `Sisyphus-Junior` nun Terra.

## 11. Finaler Go-Entscheid

### No-Go

- Production
- automatische n8n-Kundenlaeufe
- Notion-Schreibautomation mit echten Kunden
- internationale Produktion
- YMYL-Publikation
- Programmatic Local
- WordPress-/Elementor-Deployment
- Claims `produktionsreif`, `vollstaendig validiert`, `Notion-ready` oder `100% valide`

### Conditional Go

Ein interner, manueller Staging-Lernpilot ist erlaubt, wenn:

- kein automatisches Deployment erfolgt,
- jeder Gate-Entscheid durch Raphael dokumentiert wird,
- Claims extern belegt und reviewed werden,
- HTML nur Preview ist,
- Providerkosten kontrolliert sind,
- Ursprungsartefakte unveraendert bleiben.

### Naechste Entscheidung

Nicht Prompt 1 sofort ausfuehren.

Zuerst Foundation Gate A implementieren. Danach AHD Schritt 1 mit dem neuen strukturierten Vertrag testen.

## 12. Evidence Map

### OMO Reports

1. `01_DOMAIN_AND_PROMPT_AUDIT.md`
2. `02_IMPLEMENTATION_AND_TEST_AUDIT.md`
3. `03_N8N_NOTION_UI_ARCHITECTURE_AUDIT.md`
4. `04_TRACEABILITY_OUTPUT_REDTEAM_AUDIT.md`

### Audit Inputs

5. `AUDIT_BRIEF.md`
6. `HOST_GIT_BASELINE.md`
7. `OFFICIAL_PLATFORM_EVIDENCE.md`
8. `C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\_audit_inputs\2026-08-18-real-customer-use-case-matrix.md`

### Reale Staging-Evidenz

9. `C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\ahd-hausbesuch\STAGING-20260818-001\manifest.json`
10. `C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\ahd-hausbesuch\STAGING-20260818-001\logs\step-0-report.json`
11. `C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\ahd-hausbesuch\STAGING-20260818-001\run.json`

## 13. Schlussfolgerung

Das Repository ist nicht wertlos und muss nicht neu gebaut werden. Die fachliche Arbeit ist umfangreich und bietet eine starke Grundlage.

Der entscheidende Architekturwechsel lautet:

> Von neun grossen Prompts mit Dateipfaden und Human-Gate-Prosa zu einer versionierten Domain- und State-Machine, in der Prompts nur noch klar begrenzte Transformationsschritte ausfuehren.

Erst diese Verschiebung macht die vorhandene Arbeit international, n8n-faehig, Notion-steuerbar, mandantensicher, revisionsfaehig und konsistent reproduzierbar.
