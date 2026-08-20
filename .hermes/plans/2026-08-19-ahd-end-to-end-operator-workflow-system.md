# AHD End-to-End Operator Workflow System Implementation Plan

> **Fuer Hermes:** Diesen Plan mit `subagent-driven-development` task-by-task ausfuehren. Pro Schreibbereich arbeitet immer nur ein Implementer. Nach jedem Paket folgen Spec-Review und Quality-Review. Keine Commits, Pushes oder Deployments ohne ausdrueckliche Freigabe von Raphael Rechberger.

**Autor:** Raphael Rechberger
**Datum:** 19. August 2026
**Status:** Zur Ausfuehrungsfreigabe vorbereitet
**Golden-Path-Projekt:** AHD Hausbesuch
**Kanonischer Framework-Pfad:** `C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow`
**Kanonischer AHD-Workspace:** `C:\Users\offic\Documents\Projekte\Heartweb\Workflow-Lab\ahd-hausbesuch\STAGING-20260818-001`

## Ziel

Ein lokal vollstaendig lauffaehiges, Notion-zentriert entworfenes SEO- und GEO-Workflow-System erstellen, das AHD durch den kompletten Initialpfad fuehrt, jeden Schritt fuer einen menschlichen Operator sichtbar macht, reale Quality Gates und Fehlerpfade ausfuehrt, ein priorisiertes Content-Item bis zum fertigen 4b-Staging-Artefakt produziert und Jesse den qualitativen Unterschied zu den Basis-Prompts in einer professionellen Praesentationsmatrix zeigt.

## Architektur

Notion bleibt die spaetere zentrale operative Firmenoberflaeche. Die lokale Operator Console bildet heute die funktionsfaehige Referenz fuer Workflow-Timeline, Aufgaben, Reviews, Artefakte, Revisionen und Approval-Aktionen. Eine Python Workflow API stellt den bestehenden Domain-, Gate- und Transition-Services eine stabile Schnittstelle bereit. Lokale Notion- und n8n-Adapter simulieren nur den Transport, waehrend die Workflowlogik, Artefakte, Gates, Tickets und Statuswechsel real ausgefuehrt werden.

## Tech Stack

- Python 3.11 fuer Domain Services, Workflow API, Simulatoren und Tests
- JSON Schema Draft 2020-12 fuer geschlossene Vertraege
- React, TypeScript und Vite fuer die Operator Console
- Vitest und React Testing Library fuer Frontend-Tests
- Browser-QA fuer responsive und visuelle Verifikation
- Screaming Frog CLI fuer Crawl-Evidence
- bestehende deterministische Python-Tools fuer Solver und JSON-LD
- OMO Sisyphus als einzige externe Agentenschnittstelle
- Terra fuer Implementierung, Luna fuer mechanische Arbeit, Sol fuer Architektur und finale Reviews

---

# 1. Verbindliche Definition of Done

Das System ist nur praesentationsbereit, wenn alle folgenden Kriterien erfuellt sind:

1. AHD ist in der Operator Console als reales Projekt sichtbar.
2. Der Initialpfad `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b` ist vollstaendig dargestellt.
3. Schritt 3b ist sichtbar geplant, aber mangels realer 30-, 60- und 90-Tage-Daten als `not_due` markiert.
4. Jeder Schritt zeigt Ziel, Inputs, Outputs, Tool-Calls, Maschinen-Gates, Findings, Aufgaben, Human-Checkliste und naechste Aktion.
5. Jeder Schritt besitzt einen geschlossenen maschinenlesbaren Outputvertrag.
6. Jeder Schritt besitzt mindestens ein blockierendes Maschinen-Gate und genau ein Human Gate.
7. Kein Schritt wird ohne freigegebenen Vorgaenger, aktuelles Artefakt, passende Quality-Gate-Runs und revisionsgebundene Approval freigegeben.
8. Ablehnung erzeugt einen strukturierten Revision Request und eine neue Artefaktrevision.
9. Fehlender Input erzeugt eine Operator Task und pausiert den Run.
10. Ein technischer Workflowdefekt erzeugt ein Workflow Defect Ticket und veraendert keine Artefakte.
11. Scope-, Budget-, Compliance- oder Strategiefragen erzeugen eine Escalation fuer Jesse.
12. Der reale AHD-Ressourcen-404 wird sichtbar behandelt und nicht still gruen gesetzt.
13. Notion und n8n sind als `simulated` gekennzeichnet und besitzen versionierte Eventvertraege.
14. Keine simulierte Integration darf als live oder produktiv dargestellt werden.
15. AHD besitzt reale, gepruefte Outputs fuer 0, 1, 1b, 1c, 2, 3, 4a und 4b.
16. Schritt 4a und 4b werden fuer mindestens ein anhand echter Research-Daten priorisiertes Item vollstaendig ausgefuehrt.
17. Keine Keyword-, Provider-, Local-Presence-, Claim- oder Performance-Daten werden erfunden.
18. Der Step-2-Providerzugang wird vor Kosten oder API-Calls fail-fast geprueft.
19. Das medizinische AHD-Projekt besitzt eine YMYL- und Claim-Evidence-Pruefung.
20. Die Operator Console verbirgt Raw JSON standardmaessig und bietet technische Details nur auf Anforderung.
21. Eine Praesentationsmatrix vergleicht reale Basis-Artefakte mit den Enhanced-Artefakten.
22. Host- und OMO-Suites sind gruen.
23. UI-Build, UI-Tests und Browser-QA sind gruen.
24. Es bestehen keine offenen P0- oder P1-Befunde.
25. AHD Step 0 bleibt byte-identisch zur gesicherten Baseline.
26. Kein Commit, Push oder Deployment wurde ohne Freigabe ausgefuehrt.

# 2. Nichtziele dieser Ausfuehrungswelle

- keine echte Notion-Schreibintegration
- keine produktive n8n-Instanz
- kein Live-Deployment einer AHD-Seite
- keine fingierte 3b-Performance-Auswertung
- keine Produktion aller Inhalte aus dem 120-Tage-Plan
- kein vollstaendiges Enterprise-Helpdesk
- keine unkontrollierten freien Operator-Prompts an eine LLM
- keine neue Datenbanktechnologie als zusaetzliche Source of Truth

# 3. Operator- und Rollenmodell

## Primaere Rollen

| Rolle | Person in der Pilotphase | Rechte |
|---|---|---|
| Operator | Raphael Rechberger | Runs starten, Outputs pruefen, Revisionen anfordern, Tasks bearbeiten, zulässige Waiver beantragen, Human Gates freigeben |
| Business Owner | Jesse Jensen | Scope-, Budget-, Prioritaets- und Managemententscheidungen |
| Workflow Maintainer | Raphael Rechberger und Hermes Entwicklerteam | Workflowdefekte, Contracts, Integrationen und technische Policies reparieren |
| SEO Reviewer | Raphael Rechberger | fachliche SEO- und GEO-Freigaben |
| Compliance Reviewer | explizit zu benennen, falls erforderlich | medizinische und rechtliche Claims freigeben |

## Operator-Aktionen

Die UI darf nur folgende strukturierte Aktionen anbieten:

- `start_step`
- `request_revision`
- `request_input`
- `create_workflow_defect`
- `escalate_decision`
- `request_waiver`
- `approve_gate`
- `reject_gate`
- `resolve_task`
- `resume_run`
- `supersede_run`

Jede Aktion erzeugt einen versionierten Command oder Record. Freie Kommentare sind zusaetzlicher Kontext, aber nie die alleinige maschinenwirksame Anweisung.

# 4. Fehler-, Ticket- und Eskalationsrouting

| Klasse | Beispiele | Route | Darf automatisch fortsetzen? |
|---|---|---|---|
| `retryable_technical` | Timeout, 429, temporaerer 5xx | begrenzter Retry mit gleichem Idempotency-Key | nur nach erfolgreichem Retry |
| `missing_input` | Zugang, Screenshot, Kundeantwort, Evidence fehlt | Operator Task, `waiting_for_input` | nein |
| `revision_required` | Output unvollstaendig, am Thema vorbei, Vertrag fachlich nicht erfuellt | strukturierter Revision Request an Producer | erst nach neuer Revision und allen Gates |
| `waiver_candidate` | erlaubter nicht kritischer Befund | revisionsgebundener Waiver Request | nur wenn Policy und Rolle es erlauben |
| `workflow_defect` | falscher Status, Gate-False-Green, fehlerhafte Ausfuehrungslogik | Defect Ticket an Workflow Maintainer | nein |
| `management_decision` | Scope, Budget, Prioritaet, Strategie | Escalation an Jesse | nein |
| `compliance_decision` | YMYL, medizinische oder rechtliche Claims | Escalation an Compliance Reviewer | nein |
| `abort` | Tenant-Mismatch, Datenintegritaet, Security-Invariant | harter Abbruch und Incident | nein |

## Revisionsschleife

1. Revision 1: Producer korrigiert anhand des strukturierten Revision Requests.
2. Maschinen-Gates laufen erneut.
3. Human Review bewertet den Diff.
4. Revision 2: nur bei sinkender Finding-Anzahl.
5. Revision 3: letzte automatische Revision.
6. Keine Verbesserung oder drei fehlgeschlagene Runden: Workflow Defect oder Management Escalation.
7. Alte Artefakte bleiben unveraendert und werden nicht ueberschrieben.

# 5. Cross-Reference-Matrix des gesamten Workflows

| Step | Vorgaenger | Kanonischer Output | Maschinen-Gates | Human Gate | Notion-Austausch | UI-Ansicht |
|---|---|---|---|---|---|---|
| 0 | keiner | Project V2, Run, Artifact | Domain Contract, Briefing Completeness | GATE-0 | Projekt, Scope, offene Inputs, Approval | Kickoff Review |
| 1 | Step-0 Release | Topic Inventory JSON | Domain, Crawl, Evidence, Applicability | GATE-1 | Pillars, Findings, Aufgaben, Review | Topic Matrix |
| 1b | Step-1 Release | Architecture JSON | Topic Coverage, URL Conflict, Link Graph | GATE-1B | Architekturentscheidungen, offene Konflikte | Sitemap und Tree |
| 1c | Step-1B Release | Design System JSON, CSS, Templates | Token, Visual, Accessibility, Schema | GATE-1C | Design Review, Visual Findings | Template Gallery |
| 2 | Step-1C Release | Keyword Evidence Dataset | Provider Geo, Raw Hash, Coverage, Cost | GATE-2 | Providerstatus, fehlende Rows, Datenreview | Keyword Matrix |
| 3 | Step-2 Release | Plan JSON, Link Graph, Backlog | Solver, Capacity, Mandatory Coverage | GATE-3 | Roadmap, Owners, Termine, Prioritaeten | 120-Tage-Plan |
| 4a | Step-3 Release | Briefing JSON/Markdown, Claim Ledger, JSON-LD | SERP Intent, Claims, Schema Levels | GATE-4A | Copywriter Task, Claim Review | Briefing Review |
| 4b | Step-4A Release | Page Spec, HTML, Staging Evidence | HTML, Crawl, Lighthouse, axe, Visual Diff | GATE-4B | Deployment Task, QA Findings | Page Preview |
| 3b | Publication Release | Adjustment Proposal | Measurement Completeness, Baseline, Confidence | GATE-3B | Performance Review, neue Tasks | Performance View |

# 6. Sicherheits- und Checkpoint-Protokoll

## Vor jeder Implementierungswelle

1. `git status --short --branch` erfassen.
2. Alle laufenden Prozesse listen und konkurrierende Writer stoppen.
3. AHD Step-0-Baseline-Hashes verifizieren.
4. Freien Speicher pruefen.
5. Host-Tests ausfuehren.
6. OMO-Container Health und `model_fallback=false` pruefen.
7. Geplante Schreibbereiche dokumentieren.
8. Nur bei gruenem Preflight weiterarbeiten.

## Nach jedem Task

1. betroffene Tests ausfuehren
2. Diff auf Scope Drift pruefen
3. verbotene Gedankenstriche suchen
4. neue Dateien gegen Schema oder Syntax pruefen
5. keine gemeinsamen State-Dateien durch Subagenten aktualisieren lassen
6. Spec-Review ausfuehren
7. Quality-Review ausfuehren
8. erst danach Task abschliessen

## Nach jedem Sprint

1. komplette Sprint-Suite
2. Host-Full-Suite
3. AHD-Baseline-Hashvergleich
4. Artifact- und Cross-Reference-Validierung
5. Checkpoint-Manifest mit Dateipfaden und SHA-256
6. lokale Rollback-Kopie der neuen Sprint-Artefakte
7. Project State durch Hermes aktualisieren
8. offene P0/P1 pruefen
9. Go oder No-Go fuer naechsten Sprint

## Sofortige Stop-Bedingungen

- Baseline-Hash veraendert
- falscher Tenant, Project, Deployment oder Markt
- fehlende Pflichtdependency
- unkontrollierter Providerfallback
- kostenpflichtiger Call ohne Freigabe
- Test entdeckt False Green
- Subagent schreibt ausserhalb des zugewiesenen Bereichs
- zwei konkurrierende Writer auf derselben Datei
- P0- oder P1-Befund ohne klare Reparatur
- Disk Space unter dem festgelegten Sicherheitslimit
- OMO wechselt Modell oder Provider still

# 7. OMO-Ausfuehrungsprotokoll

## Orchestrierung

1. Hermes ist Hauptorchestrator und Besitzer des Masterplans.
2. Extern wird nur mit Sisyphus gesprochen.
3. Sisyphus delegiert intern nach Kategorie.
4. Pro Implementierungstask wird genau ein Schreibworker eingesetzt.
5. Spec- und Quality-Reviewer sind read-only.
6. Shared Files wie Registry, Workflow Graph, Project State und AHD Run State werden nur durch Hermes nach Verifikation aktualisiert.
7. Parallele Worker duerfen nur disjunkte Verzeichnisse bearbeiten.
8. Die interaktive Attach-Session bleibt bis zum Abschluss interner Tasks offen.
9. OMO-Selbstberichte gelten nicht als Nachweis.
10. Hermes prueft Dateien, Tests und Hashes selbst.

## Task-Zyklus

```text
Preflight
-> Implementer schreibt failing test
-> RED bestaetigen
-> minimale Implementierung
-> GREEN bestaetigen
-> Spec-Review
-> Fix falls erforderlich
-> erneutes Spec-Review
-> Quality-Review
-> Fix falls erforderlich
-> erneutes Quality-Review
-> Integrationssuite
-> Checkpoint
```

Maximal drei Review-Fix-Runden pro Task. Wenn Findings nicht sinken, wird der Task gestoppt und neu geschnitten oder an Raphael eskaliert.

# 8. Sprint 0: Kandidatenstand einfrieren und Plan aktivieren

## Task 0.1: Alle Prozesse und Writer bereinigen

**Objective:** Sicherstellen, dass keine alte OMO-, Crawl- oder Dev-Session Dateien veraendert.

**Files:** keine

**Steps:**

1. Hintergrundprozesse auflisten.
2. abgeschlossene Attach-Clients beenden.
3. Server nur stoppen, wenn ein Writer aktiv ist.
4. OMO-Sessionliste auf laufende Tasks pruefen.
5. Ergebnis dokumentieren.

**Validation:** Kein unbekannter Writer, kein aktiver Crawl.

## Task 0.2: Framework-Checkpoint erstellen

**Objective:** Dirty Working Tree vor neuen Wellen reproduzierbar sichern.

**Files:**

- Create: `00_admin/checkpoints/2026-08-19-pre-e2e/FILE_MANIFEST.json`
- Create: `00_admin/checkpoints/2026-08-19-pre-e2e/GIT_STATUS.txt`
- Create: `00_admin/checkpoints/2026-08-19-pre-e2e/TEST_BASELINE.json`

**Steps:**

1. geaenderte und neue Dateien erfassen.
2. SHA-256 aller planrelevanten Dateien berechnen.
3. AHD Step-0-Baseline separat verifizieren.
4. aktuelle Host-Suite ausfuehren.
5. aktuelle OMO-Suite ausfuehren.
6. rot markierte Kandidaten nicht als Baseline-Pass ausgeben.

**Validation:** Checkpoint manifestiert exakten Istzustand. Kein Commit.

## Task 0.3: Aktuellen Kandidatenstand klassifizieren

**Objective:** Bestehende Dateien in `verified`, `candidate`, `superseded` oder `blocked` einordnen.

**Files:**

- Create: `00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md`

**Pflichtklassifikation:**

- Transition Service
- Quality Gate Registry 1.1
- Registry Evaluator
- Crawl Policy 1.0
- Step-1 Preflight CLI
- AHD Crawl 005
- AHD Step-1 Artifact v1
- OMO Reviews 04 und 05

**Validation:** Kein Kandidat wird ungeprueft als fertig behandelt.

## Task 0.4: Project State und Entscheidungen aktualisieren

**Objective:** Veraltete operative Projektbeschreibung ersetzen.

**Files:**

- Modify: `00_admin/PROJECT_STATE.md`
- Create: `00_admin/DECISIONS.md`

**Active Decisions:**

- Notion bleibt zentrale operative Firmenoberflaeche.
- Raphael ist primaerer Pilotoperator.
- eigene UI ist spezialisierte, aus Notion erreichbare Workflowansicht.
- n8n ist spaetere Orchestrierung, heute Simulator.
- AHD ist Golden Path.
- initiale E2E-Route endet bei 4b.
- 3b ist `not_due`.
- ein priorisiertes Item durchlaeuft 4a und 4b.

**Validation:** Keine widerspruechlichen aktiven Entscheidungen.

**Sprint-0-Gate:** Checkpoint vorhanden, State aktuell, Baseline unveraendert.

# 9. Sprint 1: Runtime-Kandidaten stabilisieren

## Task 1.1: Transition Service Contract Review

**Objective:** Zentralen Statuswriter gegen alle Runtime-Schemas und Reviewbefunde pruefen.

**Files:**

- Modify if needed: `services/transition_service/service.py`
- Modify if needed: `standards/runtime/transition-command.schema.json`
- Modify if needed: `standards/runtime/release-record.schema.json`
- Test: `tests/test_transition_service.py`

**Negative Tests:**

- falscher Tenant
- stale Revision
- stale Artifact Hash
- fehlender Vorgängerrelease
- fehlendes Maschinen-Gate
- fehlende oder abgelaufene Approval
- direktes Complete ohne Approved
- Idempotency-Konflikt
- Retry-Limit
- ungueltiger Sideflow
- geaendertes Artefakt nach Approval

**Validation:** Jeder Fehler veraendert den Run nicht und erzeugt strukturierte Errors.

## Task 1.2: Registry Evaluator Review

**Objective:** Applicability und Gate-Bindungen fuer alle Steps erzwingen.

**Files:**

- Modify if needed: `services/quality_gate_registry/evaluator.py`
- Modify if needed: `standards/quality/quality-gate-registry.json`
- Test: `tests/test_quality_gate_registry_evaluator.py`
- Test: `tests/contracts/test_quality_gate_registry.py`

**Validation:** Jeder Step besitzt Maschinen- und Human-Gate. `when_configured` verlangt eine explizite Entscheidung.

## Task 1.3: Crawl Disposition Review

**Objective:** Step-1- und Step-4B-Dispositionen vollstaendig pruefen.

**Files:**

- Modify if needed: `services/quality_gate_runner/disposition.py`
- Modify if needed: `services/quality_gate_runner/screaming_frog.py`
- Modify if needed: `standards/quality/crawl-disposition-policy.json`
- Test: `tests/test_crawl_disposition.py`
- Test: `tests/test_screaming_frog_quality_gate.py`

**Required Cases:**

- URL-Limit
- Missing Exports
- 5xx
- HTML-404
- Resource-404
- Broken Links
- H2
- Redirect Chains
- Structured Data
- Hreflang
- Security
- noindex fuer Impressum und Datenschutz
- Waiver nur bei erlaubter Finding-Klasse

## Task 1.4: Step-1 Preflight und Storage Binding Review

**Objective:** Gespeicherte Bytes, Bundle, Registry, Waiver und Run-Lineage direkt pruefen.

**Files:**

- Modify if needed: `services/step1_preflight/validator.py`
- Test: `tests/test_step1_contract_v2.py`

**Validation:** CLI liest das echte gespeicherte Artefakt. Kopierte Bundle-Bytes reichen nicht.

## Task 1.5: Error Envelope und Operator Routing Gap schließen

**Objective:** Runtime-Errors eindeutig in Operator-Routen uebersetzen.

**Files:**

- Create: `standards/operator/error-routing-policy.schema.json`
- Create: `standards/operator/error-routing-policy.json`
- Create: `services/operator_routing/router.py`
- Test: `tests/test_operator_error_routing.py`

**Validation:** Jeder Errorcode besitzt genau eine Default-Route und einen Owner-Typ.

## Task 1.6: Sprint-1-Integrationstest

Run:

```bash
python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 -v
python tests/run_full_suite.py
```

**Sprint-1-Gate:** Keine offenen P0/P1. AHD-Baseline unveraendert.

# 10. Sprint 2: Operator-, Ticket- und Eventvertraege

## Task 2.1: Operator Task Contract

**Files:**

- Create: `standards/operator/operator-task.schema.json`
- Test: `tests/contracts/test_operator_contracts.py`

**Fields:** Task-ID, Tenant, Project, Run, Step, Type, Title, Plain-Language Description, Owner Role, Priority, Blocking, Due, Artifact, Evidence, Acceptance Criteria, Resolution Method, Status.

## Task 2.2: Blocker Contract

- Create: `standards/operator/blocker-record.schema.json`

**Types:** input, technical, quality, compliance, provider, management.

## Task 2.3: Revision Request Contract

- Create: `standards/operator/revision-request.schema.json`

**Fields:** current Artifact, Revision, affected sections, problem, expected result, immutable constraints, Evidence, reviewer feedback, attempt number.

## Task 2.4: Workflow Defect Contract

- Create: `standards/operator/workflow-defect.schema.json`

**Fields:** expected behavior, actual behavior, reproducer, affected run, severity, regression test, owner, status.

## Task 2.5: Escalation Contract

- Create: `standards/operator/escalation-record.schema.json`

**Fields:** decision owner, options, impacts, deadline, evidence, blocking scope, final decision.

## Task 2.6: Resolution Contract

- Create: `standards/operator/resolution-record.schema.json`

**Fields:** resolved record, action, new Evidence, verification gate, resolver, timestamp, resume command.

## Task 2.7: Workflow Event Contract

**Files:**

- Create: `standards/integrations/workflow-event.schema.json`
- Create: `standards/integrations/event-catalog.json`

**Events:** project.created, run.started, step.blocked, artifact.created, gate.ready, gate.approved, gate.rejected, task.created, task.resolved, defect.created, escalation.created, run.resumed, release.created.

## Task 2.8: Notion Projection Contract

**Files:**

- Create: `standards/integrations/notion-projection.schema.json`
- Create: `docs/integrations/notion-operating-model.md`

**Rule:** Notion ist operative Projektion, nicht atomare State Machine.

## Task 2.9: n8n Command Contract

- Create: `standards/integrations/n8n-command.schema.json`
- Create: `docs/integrations/n8n-orchestration-model.md`

**Validation:** Retry, idempotency, wait gates, resume und DLQ sind spezifiziert.

**Sprint-2-Gate:** Alle Operator- und Integrationfixtures validieren. Routingmatrix ist lueckenlos.

# 11. Sprint 3: V2-Outputvertraege und Promptmigration 1b bis 4b

## Allgemeine Regel

Jeder Schritt erhaelt zuerst einen strukturierten JSON-Vertrag. Markdown, CSV, CSS und HTML sind abgeleitete oder auslieferbare Views. Kein Prompt setzt selbststaendig `completed` oder erzeugt eine Human Approval.

## Task 3.1: Step-1B Architecture Contract

**Files:**

- Create: `standards/outputs/step-1b-architecture.schema.json`
- Create: `services/step1b_preflight/validator.py`
- Modify: `prompts/1b-seitenarchitektur.xml.md`
- Test: `tests/test_step1b_contract.py`

**Must Cover:** jede Pillar- und Cluster-ID, bestehende und geplante URL, Navigation, Canonical, Redirect, Vertical Links, Sibling Links, Orphan Detection, Conflict Decisions.

## Task 3.2: Step-1B Renderer

- Create: `services/step1b_preflight/render.py`
- Output: Markdown und interaktiver HTML-Tree aus demselben JSON.

**Validation:** Markdown und HTML werden nicht separat erfunden.

## Task 3.3: Step-1C Design Contract

- Create: `standards/outputs/step-1c-design-system.schema.json`
- Create: `standards/outputs/step-1c-template.schema.json`
- Modify: `prompts/1c-pillar-template.xml.md`
- Test: `tests/test_step1c_contract.py`

**Critical Cross-Check:** keine physische Adresse, GBP oder NAP behaupten, wenn Project V2 nur Service Area belegt.

## Task 3.4: Step-2 Provider-Neutral Evidence Contract

- Create: `standards/outputs/step-2-keyword-evidence.schema.json`
- Create: `standards/providers/research-request.schema.json`
- Create: `standards/providers/research-response.schema.json`
- Modify: `prompts/2-cluster-recherche.xml.md`
- Test: `tests/test_step2_contract.py`

**Provider Strategy:** DataForSEO primaer fuer skalierbare Rohdaten. AgentSEO nur ueber Gateway und nur bei verifizierter Capability. Direkte Prompt-Calls verboten.

## Task 3.5: Provider Gateway Hardening

- Modify: `services/agentseo_gateway/core.py`
- Create: `services/provider_gateway/router.py`
- Test: `tests/test_provider_gateway.py`

**Fail Conditions:** Location mismatch, Metadata mismatch, missing raw response, quota, timeout, unknown cost, missing job ID.

## Task 3.6: Step-3 Plan Contract

- Create: `standards/outputs/step-3-plan.schema.json`
- Create: `services/step3_preflight/validator.py`
- Modify: `prompts/3-120-tage-plan.xml.md`
- Test: `tests/test_step3_contract.py`

**Must Cover:** 17 Wochen, Capacity, Pflichtitems, Backlog, Linkgraph, Solver-Version, Input- und Output-Hash.

## Task 3.7: Step-4A Briefing Contract

- Create: `standards/outputs/step-4a-briefing.schema.json`
- Create: `standards/outputs/claim-ledger.schema.json`
- Modify: `prompts/4a-content-briefing-und-schema.xml.md`
- Test: `tests/test_step4a_contract.py`

**Critical Cross-Check:** medizinische Claims nur mit Evidence und passender Reviewer-Policy. Kein direkter AgentSEO-Aufruf.

## Task 3.8: Step-4B Page Contract

- Create: `standards/outputs/step-4b-page-spec.schema.json`
- Create: `standards/outputs/staging-evidence.schema.json`
- Modify: `prompts/4b-landingpage-html.xml.md`
- Test: `tests/test_step4b_contract.py`

**Must Cover:** HTML, Meta, Canonical, Schema, Content Hash, Forms, Consent, Tracking Slots, Service Area, Accessibility, Responsive, Sibling Links.

## Task 3.9: Step-3B Adjustment Contract

- Create: `standards/outputs/step-3b-adjustment.schema.json`
- Modify: `prompts/3b-performance-check.xml.md`
- Test: `tests/test_step3b_contract.py`

**Rule:** Ursprungsplan bleibt unveraendert. Neue Revision statt Overwrite.

## Task 3.10: Vollstaendige Prompt-Contract-Suite

**Validation:**

- genau ein offizieller Prompt pro Step
- Inputs stimmen mit Vorgaengerartefakten ueberein
- Outputs stimmen mit Output Registry ueberein
- kein Prompt erzeugt Human Approval
- kein Prompt startet Folgeschritt
- kein direkter Providerpfad
- keine Legacy-Manifest-Completion ohne Transition Service

**Sprint-3-Gate:** Alle V2-Vertraege, Prompttests und negative Fixtures gruen.

# 12. Sprint 4: Local Workflow API und Integrationssimulatoren

## Task 4.1: Reproduzierbare App-Dependencies

**Files:**

- Create: `requirements-app.txt`
- Modify only after dependency review: `\\wsl.localhost\Ubuntu\home\frater418\projekte\opencode-omo-integration\Dockerfile`
- Modify only after dependency review: `\\wsl.localhost\Ubuntu\home\frater418\projekte\opencode-omo-integration\docker-compose.yml`
- Add exact Linux wheels if required: `\\wsl.localhost\Ubuntu\home\frater418\projekte\opencode-omo-integration\vendor\python-wheels\`

**Rule:** exakte Pins, Lock oder vendorte Wheels. Keine Live-PyPI-Abhaengigkeit im finalen OMO-Build.

## Task 4.2: Context Builder und LLM Run Contracts

**Files:**

- Create: `standards/runtime/logical-project-session.schema.json`
- Create: `standards/runtime/official-prompt-registry.schema.json`
- Create: `standards/runtime/official-prompt-registry.json`
- Create: `standards/runtime/worker-profile.schema.json`
- Create: `standards/runtime/context-package.schema.json`
- Create: `standards/runtime/llm-run-request.schema.json`
- Create: `standards/runtime/llm-run-result.schema.json`
- Create: `services/context_builder/builder.py`
- Create: `services/context_builder/validator.py`
- Create: `services/context_builder/session_policy.py`
- Test: `tests/test_context_builder.py`
- Test: `tests/contracts/test_llm_runtime_contracts.py`

**Rule:** Das Projekt ist stateful, der technische Worker ist ersetzbar. Schritt 0 bindet das unveraenderliche Project Intake. Ab Schritt 1 bindet jeder Step- und Revisionslauf das freigegebene Project V2. Jeder Lauf bindet einen offiziellen Prompt, alle zugehoerigen Outputvertraege, freigegebene Vorgaenger, Evidence, Decisions, Findings und Operator-Anweisungen ueber exakte Revisionen und SHA-256-Hashes. Eine technische Provider-Session ist nur ein optionaler Cache. Ein verlorener Session-Handle darf keinen Kontextverlust erzeugen.

**Revision:** Ein Rerun erhaelt das abgelehnte Artefakt, maschinelle und menschliche Findings, Operator-Anweisung, unveraenderliche Felder, verbotene Aenderungen und den erwarteten Outputvertrag. Er erzeugt immer eine neue Artefaktrevision.

**Fail-Fast:** Fehlende, stale, superseded, hash-falsche, untrusted-nicht-markierte oder cross-tenant Inputs stoppen vor jedem LLM-Aufruf.

## Task 4.3: Read-Only Project API

**Files:**

- Create: `services/operator_api/app.py`
- Create: `services/operator_api/repository.py`
- Create: `services/operator_api/models.py`
- Test: `tests/test_operator_api.py`

**Endpoints:** projects, logical project session, workflow, steps, artifacts, gates, tasks, tickets, assignments, context packages, LLM runs, performance checkpoints, metrics, adjustment proposals, integration status.

## Task 4.4: Command API

**Endpoints:** start, request-revision, request-input, create-defect, escalate, request-waiver, approve, reject, resolve, resume.

**Rule:** Kein Endpoint schreibt Status direkt. Jeder Command geht durch Transition oder Routing Service. Ein LLM Dispatch ist nur mit validiertem Context Package und LLM Run Request erlaubt.

## Task 4.5: Local Event Store

**Files:**

- Create: `services/operator_api/event_store.py`
- Customer data: ausschliesslich im jeweiligen Kunden-Workspace unter `v2/operator/events/`. Fuer den Golden Path ist dies der AHD-Workspace.

**Rule:** append-only, Event-ID, Idempotency-Key, Timestamp, Correlation-ID.

## Task 4.6: Notion Simulator

**Files:**

- Create: `services/integrations/notion_simulator.py`
- Create: `tests/fixtures/integrations/notion/`
- Test: `tests/test_notion_simulator.py`

**Output:** Notion-projected Customer, Project, Step, Task, Assignment, Review, Approval, Performance Checkpoint, Metric und Adjustment Proposal Views als lokale JSON-Fixtures.

**Behavior:** Der Simulator bildet relationale Notion-Datenbanken, Verantwortliche, Rollen, Termine, Status, Blocker, Artefaktlinks, Reviewfenster, logische Projektsession, LLM Run-Historie und Performance-Checkpoints nach. Aufgaben werden rollenbasiert an Copywriter, Designer, Entwickler und Reviewer projiziert. Ein Notion-Feldedit erzeugt hoechstens einen typisierten Command und keine direkte kanonische Statusmutation.

## Task 4.7: n8n Simulator

- Create: `services/integrations/n8n_simulator.py`
- Test: `tests/test_n8n_simulator.py`

**Behavior:** Den vollstaendigen Workflowgraph lokal orchestrieren: Command empfangen, validiertes Context Package und LLM Run Request transportieren, frischen Step-Worker oder policy-kontrollierten Session-Cache ausloesen, Event erzeugen, Evidence persistieren, Wait Gate simulieren, Aufgaben und Notion-Projektionen erzeugen, Fehler routen, Retry und DLQ ausfuehren, Performance-Checkpoint verarbeiten, Step-3b-Anpassung anfordern und Resume ueber den Transition Service beantragen.

**Rule:** Die lokale Simulation nutzt dieselben versionierten Commands und Events wie die spaetere n8n-Integration. Sie dupliziert keine Gate-, Hash-, Revisions- oder Transitionregeln aus dem Core.

## Task 4.8: OpenAPI und Type Generation

- Generate: `apps/operator-console/src/generated/api-types.ts`

**Rule:** UI erfindet keine separaten Contracttypen.

## Task 4.9: API Integration Suite

**Tests:** Golden Path, Reject Path, Missing Input, Workflow Defect, Escalation, Waiver, Idempotent Replay, rollenbasierte Aufgabenverteilung, Notion-Projekttracking, reproduzierbares Context Package, verlorene technische Session, Revision-Rerun, stale und cross-tenant Context, Performance-Checkpoints an Tag 30, 60 und 90, Metrikimport, Step-3b-Adjustment-Proposal, Wait/Resume und DLQ.

**Sprint-4-Gate:** Der komplette Workflow ist lokal ueber API, Events und Simulatoren ausfuehrbar. Notion zeigt Projekt-, Aufgaben-, Run- und Trackingdaten. n8n simuliert die spaetere Gesamtorchestrierung. Jeder Step oder Rerun ist ueber ein deterministisches Context Package reproduzierbar und uebersteht den Verlust einer technischen Provider-Session. Kein Adapter kann eine Gate-, Hash-, Revisions- oder Statusregel umgehen. Der bestaetigte Performance-Zyklus an Tag 30, 60 und 90 ist in Notion-Tracking, n8n-Orchestrierung und Step 3b konsistent abgebildet.

# 13. Sprint 5: Operator Console

## Task 5.1: Frontend-Grundgeruest

**Files:**

- Create: `apps/operator-console/package.json`
- Create: `apps/operator-console/package-lock.json`
- Create: `apps/operator-console/vite.config.ts`
- Create: `apps/operator-console/tsconfig.json`
- Create: `apps/operator-console/src/main.tsx`
- Create: `apps/operator-console/src/App.tsx`
- Create: `apps/operator-console/src/styles.css`

**Validation:** `npm ci`, Test, Build.

## Task 5.2: API Client und Contracttypen

- Create: `apps/operator-console/src/api/client.ts`
- Use only generated types.

## Task 5.3: Project Dashboard

- Create: `apps/operator-console/src/features/projects/ProjectDashboard.tsx`

**Shows:** aktueller Step, Fortschritt, Blocker, Tasks, Review Requests, naechste Aktion.

## Task 5.4: Workflow Timeline

- Create: `apps/operator-console/src/features/workflow/WorkflowTimeline.tsx`

**Shows:** 0, 1, 1b, 1c, 2, 3, 4a, 4b sowie 3b Sideflow.

## Task 5.5: Step Detail und Presentation Card

- Create: `apps/operator-console/src/features/workflow/StepDetail.tsx`

**Shows:** Ziel, Inputs, Tools, Output Summary, Gates, Findings, Context Package, Workerprofil, Promptversion, LLM Run-Status, Operator Checklist, Actions.

## Task 5.6: Artifact Preview und Diff

- Create: `apps/operator-console/src/features/artifacts/ArtifactPreview.tsx`
- Create: `apps/operator-console/src/features/artifacts/RevisionDiff.tsx`

**Rule:** Raw JSON nur unter technische Details.

## Task 5.7: LLM Run-Historie und Revision Dispatch

- Create: `apps/operator-console/src/features/runs/RunHistory.tsx`
- Create: `apps/operator-console/src/features/runs/ContextPackageSummary.tsx`
- Create: `apps/operator-console/src/features/runs/RevisionRunPreview.tsx`

**Shows:** logische Projektsession, technische Session nur als Cache-Status, Provider, Modell, Promptversion, Workerprofil, Toolpolicy, Context-Quellen, Tokenverbrauch, Run-Ergebnis und Artefaktrevision.

**Action:** `request revision` zeigt vor Dispatch das strukturierte Rerun-Paket mit Findings, Operator-Anweisung, unveraenderlichen Feldern, verbotenen Aenderungen und erwarteter neuer Revision.

## Task 5.8: Task- und Ticketqueue

- Create: `apps/operator-console/src/features/tasks/TaskQueue.tsx`
- Create: `apps/operator-console/src/features/tasks/TicketDetail.tsx`

## Task 5.9: Review Center

- Create: `apps/operator-console/src/features/reviews/ReviewCenter.tsx`

**Actions:** approve, reject, request revision, request input, escalate, request waiver.

## Task 5.10: Integration Status

- Create: `apps/operator-console/src/features/integrations/IntegrationStatus.tsx`

**Labels:** Notion simulated, n8n simulated, Production disabled.

## Task 5.11: Presentation Matrix

- Create: `apps/operator-console/src/features/presentation/WorkflowMatrix.tsx`
- Create: `apps/operator-console/src/features/presentation/BaselineComparison.tsx`

## Task 5.12: Frontend Tests

**Tests:** Timeline, status locks, task routing, action forms, Context-Package-Zusammenfassung, verlorene technische Session, Revision-Preview, raw-detail toggle, integration badges, artifact diff.

## Task 5.13: Browser-QA

**Viewports:** Desktop, Tablet, Mobile.
**Checks:** console errors, keyboard navigation, contrast, responsive layout, empty states, blocked states, long text.

**Sprint-5-Gate:** Ein geschulter SEO-Mitarbeiter kann den naechsten Schritt ohne technische Dokumentation erkennen.

# 14. Sprint 6: AHD Step 0 und Step 1 kanonisch versoehnen

## Task 6.1: AHD Step-0-Baseline erneut verifizieren

Keine Mutation erlaubt.

## Task 6.2: Crawl 005 als Raw Evidence registrieren

**Files in AHD:**

- Create new Evidence Record
- Create new Artifact Record
- Create raw blocked qgr

**Rule:** Crawl 004 bleibt historisch. Crawl 005 wird nicht nachtraeglich veraendert.

## Task 6.3: Resource-404 Operator Task erzeugen

Task zeigt:

- kein HTML-404
- Step-1-Waiver moeglich
- harter Blocker vor 4b Production
- verantwortliche Rolle Technik

## Task 6.4: Waiver-Entscheidung nur durch Raphael

Ohne explizite Approval bleibt Step 1 blocked. Kein Agent erstellt einen Waiver in Raphaels Namen.

## Task 6.5: Step-1-Artifact-Revision erstellen

Neue Run- und Artifact-Revision. Alte Revision unveraendert archivieren. Crawl-005-Evidence und Gate Context einbinden.

## Task 6.6: Step-1-Preflight CLI ausfuehren

Expected: valid nur bei vollstaendiger Policy-Disposition und explizitem Independent-Source-N/A oder realer Evidence.

## Task 6.7: GATE-1 in Operator Console

Raphael prueft Pillars und Cluster. Approval wird durch Transition Service verarbeitet.

## Task 6.8: AHD Step-1 Release

Erst danach 1b entsperren.

**Sprint-6-Gate:** Step 1 released, 1b ready, alte Artefakte unveraendert.

# 15. Sprint 7: AHD Step 1b und 1c

## Task 7.1: Aktuelle Website- und Navigations-Evidence erfassen

Sitemap, Navigation, URLs, Canonicals, interne Links und bestehende Seiten.

## Task 7.2: Architecture JSON erzeugen

Jeder Pillar und Cluster besitzt genau eine Entscheidung: existing, update, merge, redirect, new oder backlog.

## Task 7.3: Architecture Gates

Orphans, URL-Konflikte, Kannibalisierung, Redirect-Loops, fehlende Sibling Links.

## Task 7.4: GATE-1B Operator Review

UI zeigt Tree, Diffs und offene Entscheidungen.

## Task 7.5: Full-Page-Screenshot und Brand Evidence

Kein Designraten. Screenshot und extrahierte Tokens als Evidence.

## Task 7.6: Design System und Pillar Templates

Alle primaeren Pillar-Templates oder eine vertraglich explizit definierte Templatefamilie erzeugen. Keine ungeprueften Claims.

## Task 7.7: Browser-, Accessibility- und JSON-LD-QA

## Task 7.8: GATE-1C Operator Review

**Sprint-7-Gate:** Architektur und Design released, Step 2 ready.

# 16. Sprint 8: AHD Step 2 und Step 3

## Task 8.1: Provider Readiness Gate

Pruefen:

- Credentials vorhanden
- Provider erreichbar
- Deployment und Geo-Code verifiziert
- Sprache korrekt
- Cost Budget bekannt
- Raw Response Speicherung vorbereitet

Bei Fehler: ein konsolidierter Operator Blocker. Keine Ersatzwerte.

## Task 8.2: Seed-Dataset erzeugen

Mindestens 25 bis 40 Kandidaten pro freigegebenem Pillar. Noch keine erfundenen Metriken.

## Task 8.3: Provider-Batches ausfuehren

Idempotent, asynchron, Raw Payload und Job IDs speichern.

## Task 8.4: Geo- und Completeness-Gates

Mindestens 25 verifizierte Rows pro Pillar oder harter Blocker.

## Task 8.5: GATE-2 Operator Review

UI zeigt Providerstatus, Top Keywords, Coverage, fehlende Daten und Costs.

## Task 8.6: Capacity Solver Input erstellen

Nur aus freigegebenem Step-2-Dataset.

## Task 8.7: 120-Tage-Plan und Linkgraph erzeugen

17 Wochen, 4 Phasen, Pflichtitems, Backlog, vertikale und horizontale Links.

## Task 8.8: Solver- und Plan-Gates

Keine Woche ueber 15 Stunden. Untergrenze wird sichtbar zur Human Review gestellt.

## Task 8.9: GATE-3 Operator Review

**Sprint-8-Gate:** Plan released, priorisiertes 4a-Item eindeutig bestimmt.

# 17. Sprint 9: AHD Step 4a und 4b Vertical Slice

## Task 9.1: Prioritaetsitem aus freigegebenem Plan waehlen

Default nur wenn Evidence es bestaetigt: `Privataerztlicher Hausbesuch Muenchen`.

## Task 9.2: SERP- und Source-Evidence erfassen

Nur ueber kontrollierte Research-Gateways und persistierte Raw Evidence.

## Task 9.3: Claim Ledger aufbauen

Jede medizinische, preisliche, zeitliche oder leistungsbezogene Aussage klassifizieren und belegen.

## Task 9.4: Briefing erzeugen

Section-by-Section, Query Fan-Out, Meta, Internal Links, Semantic Relations, JSON-LD.

## Task 9.5: Step-4A Gates

Claim Evidence, JSON-LD-Level, Intent, Linkmap, Notion Frontmatter.

## Task 9.6: GATE-4A Operator Review

## Task 9.7: Page Spec und HTML erzeugen

Responsive, autark, keine unbestaetigte NAP-Adresse, Service-Area korrekt, keine externen CDNs.

## Task 9.8: Staging QA

Crawl, HTML, Canonical, Schema, axe, responsive Visual QA, Forms, Links, Content Hash.

Der bestehende AHD Resource-404 bleibt sichtbar. Er blockiert nur dann das neue 4b-Artefakt, wenn das Artefakt oder der geplante Deployment-Scope davon betroffen ist. Kein stiller Pass.

## Task 9.9: GATE-4B Operator Review

Kein Live-Deployment. Release bedeutet `staging_ready` fuer die Praesentation.

**Sprint-9-Gate:** Ein reales priorisiertes Item hat 4a und 4b vollstaendig durchlaufen.

# 18. Sprint 10: Praesentationsmatrix und Jesse-Demo

## Task 10.1: Reale Baseline-Artefakte sammeln

Nur bestehende Basis-Prompt-Artefakte. Keine erfundenen Vorher-Ergebnisse.

## Task 10.2: Enhanced-Artefakte sammeln

Alle released AHD-Artefakte und QA-Evidence.

## Task 10.3: Vergleichsmatrix erzeugen

**Dimensionen:** Tiefe, Vollstaendigkeit, Evidence, SEO, GEO, Fehlererkennung, Reproduzierbarkeit, Operator-Nutzen, Notion-Readiness.

## Task 10.4: Workflow Presentation Matrix erzeugen

Alle Steps, Outputs, Gates, Tasks, Status und Vorschaulinks.

## Task 10.5: Demo-Szenario vorbereiten

1. AHD Dashboard
2. Timeline
3. Step-1-Output
4. realer 404-Blocker
5. Task oder Waiver Route
6. Architecture Tree
7. Keyword Evidence
8. Plan
9. Briefing
10. fertige Page Preview
11. Notion- und n8n-Zielintegration

## Task 10.6: Operator-Handbuch in der UI

Plain-Language Hilfe fuer jede Aktion. Keine technischen JSON-Anweisungen.

## Task 10.7: Jesse-Walkthrough

Kurzes Script: Problem, alte Arbeitsweise, neue Arbeitsweise, reale Outputs, Kontrollmechanismen, naechste Integrationsphase.

## Task 10.8: Finaler visueller QA

Screenshots und Browser-Checks fuer die Praesentationsreihenfolge.

# 19. Sprint 11: Finaler Integrations- und Reifegrad-Gate

## Task 11.1: Gesamte Host-Suite

```bash
python tests/run_full_suite.py
```

## Task 11.2: Gesamte OMO-Suite

```bash
docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python tests/run_full_suite.py'
```

## Task 11.3: Frontend-Suite

```bash
cd apps/operator-console
npm ci
npm run test
npm run lint
npm run build
```

## Task 11.4: End-to-End Golden Path

Ein frischer lokaler API-Run muss den AHD-Pfad reproduzierbar darstellen. Keine direkte Mutation des kanonischen Kundenlaufs waehrend dieses Tests.

## Task 11.5: Negative End-to-End-Suite

- missing input
- output revision
- workflow defect
- management escalation
- waiver candidate
- expired approval
- provider unavailable
- wrong geo
- stale artifact
- duplicate command

## Task 11.6: Spec-Review

Read-only Terra Review gegen diesen Plan. Null P0/P1.

## Task 11.7: Quality-Review

Read-only Terra Review fuer Code, Daten, UX, Security, False Greens und Outputqualitaet. Null P0/P1.

## Task 11.8: Sol Final Architecture Review

Pruefen:

- Notion bleibt zentral
- n8n bleibt Middleware
- UI konkurriert nicht mit Notion
- AHD ist real durchlaufen
- simulierte Integrationen korrekt gekennzeichnet
- keine versteckten Fallbacks
- kein Scope Drift

## Task 11.9: Go oder No-Go Report

- Create: `00_admin/audits/2026-08-19-e2e-demo/FINAL_GO_NO_GO.md`

**GO nur wenn:** alle Definition-of-Done-Kriterien erfuellt und keine P0/P1 offen.

# 20. Abhaengigkeitsgraph

```text
Sprint 0
  -> Sprint 1 Runtime stabil
      -> Sprint 2 Operator Contracts
          -> Sprint 3 alle Output Contracts
              -> Sprint 4 API und Simulatoren
                  -> Sprint 5 Operator Console
                  -> Sprint 6 AHD Step 1 Release
                      -> Sprint 7 AHD 1b und 1c
                          -> Sprint 8 AHD 2 und 3
                              -> Sprint 9 AHD 4a und 4b
                                  -> Sprint 10 Praesentation
                                      -> Sprint 11 Final Gate
```

## Erlaubte Parallelisierung

- Read-only Reviews duerfen parallel laufen.
- Nach Freeze der Operator Contracts duerfen API-Grundgeruest und UI-Grundgeruest parallel in disjunkten Verzeichnissen entstehen.
- AHD Content-Research darf parallel zu UI-Polish laufen, wenn keine gemeinsamen State-Dateien beschrieben werden.
- Shared Registry, Workflow Graph, Project State, AHD Run State und Presentation Matrix werden nur durch Hermes geschrieben.

## Verbotene Parallelisierung

- zwei Worker an derselben Schemafamilie
- Promptmigration und Output-Schema fuer denselben Step durch verschiedene Writer
- mehrere Worker an AHD `runtime/`
- parallele Updates an `PROJECT_STATE.md`
- UI-Type-Edits waehrend OpenAPI-Type-Generation

# 21. Provider- und externe Blocker

## Potenzieller harter Blocker fuer den heutigen E2E-Run

Reale Step-2-Metriken benoetigen funktionierenden, geo-korrekten Providerzugang. Vor dem Research-Lauf ist deshalb ein explizites Readiness-Gate erforderlich.

Erlaubte Ergebnisse:

- `ready`: reale Calls duerfen nach Kostenfreigabe starten
- `blocked_credentials`: Zugang fehlt
- `blocked_geo`: Marktmetadaten sind inkonsistent
- `blocked_quota`: Budget oder Quota fehlt
- `blocked_provider`: Provider nicht erreichbar

Nicht erlaubt:

- geschaetzte Metriken
- manuell erfundene Nullwerte
- stiller Wechsel auf einen anderen Markt
- stiller Wechsel auf einen anderen Provider

# 22. Abschlussartefakte

## Framework

- vollstaendige Output- und Operator-Schemas
- stabile Runtime Services
- Operator API
- Integrationssimulatoren
- React Operator Console
- Tests und QA-Reports
- Notion- und n8n-Schnittstellendokumentation

## AHD

- Project V2
- released Step-1 Topic Inventory
- released Step-1B Architecture
- released Step-1C Design System und Templates
- released Step-2 Keyword Evidence
- released Step-3 Plan und Linkgraph
- released Step-4A Briefing fuer Priority Item
- released Step-4B Staging-Artefakt fuer Priority Item
- Tasks, Tickets, Gates, Approvals und Releases
- Workflow Presentation Matrix
- Baseline Comparison

## Praesentation

- lokale Operator Console
- Jesse-Demo-Script
- Matrix aller Outputs
- Vorher-gegen-Nachher-Vergleich
- klarer Status real gegen simulated
- naechste Phase fuer Notion- und n8n-Entwickler

# 23. Ausfuehrungsfreigabe

Dieser Plan autorisiert noch keine Implementierung. Vor Task 0.1 ist eine ausdrueckliche Ausfuehrungsfreigabe von Raphael Rechberger erforderlich.

Nach Freigabe arbeitet Hermes diesen Plan in der angegebenen Reihenfolge ab. Jeder Sprint endet mit einem dokumentierten Go oder No-Go. Bei einem Blocker stoppt nur der betroffene Pfad. Bereits verifizierte Artefakte bleiben unveraendert und der letzte gruene Checkpoint bleibt wiederherstellbar.
