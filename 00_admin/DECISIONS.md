# Decisions

## DEC-0012: Notion bleibt zentrale operative Firmenoberflaeche

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Jesse Jensen soll Kunden, Projekte, Aufgaben, Freigaben und Firmenablaeufe zentral ueber Notion steuern koennen.
- Decision: Notion bleibt die zentrale operative Firmenoberflaeche. Die eigene Operator Console ist eine spezialisierte, aus Notion erreichbare Workflow-, Review- und Praesentationsansicht. Sie ersetzt Notion nicht.
- Rationale: Notion entspricht Jesses bestaetigtem Arbeitsmodell. Die eigene UI loest nur komplexe Visualisierung, Artefaktvergleich und sichere Approval-Aktionen.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 19. August 2026; `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- Impacted files/areas: Operator Console, Notion Adapter, n8n Adapter, Workflow API, Presentation Matrix

## DEC-0013: Raphael ist primaerer Pilotoperator

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Jesse erledigte bisher die operative Arbeit und holte Raphael, um diese Arbeit direkt zu uebernehmen.
- Decision: Die erste Operator Experience wird fuer Raphael gebaut. Spaetere Rollen und Masken muessen auch fuer geschulte SEO-Mitarbeiter ohne Hermes-Zugang funktionieren.
- Rationale: Der Pilot muss Raphaels reale Arbeitsweise abbilden und zugleich strukturierte Aktionen statt freie technische Prompts anbieten.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 19. August 2026
- Impacted files/areas: Rollenmodell, Operator Tasks, Tickets, Review Center, Escalation Routing

## DEC-0014: AHD ist der Golden Path fuer die lokale End-to-End-Demonstration

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Fuer Jesse soll ein reales Projekt den gesamten verbesserten Workflow sichtbar durchlaufen.
- Decision: AHD wird von Schritt 0 bis Schritt 4b als Golden Path verwendet. Schritt 3b bleibt bis zu realen Post-Publication-Daten auf `not_due`.
- Rationale: Ein realer Vertical Slice demonstriert Outputqualitaet, Quality Gates, Aufgaben, Freigaben und Operator-Nutzen besser als isolierte technische Tests.
- Supersedes: none
- Superseded by: none
- Evidence: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- Impacted files/areas: AHD Workspace, Operator Console, Presentation Matrix, Golden-Path-Tests

## DEC-0015: Notion und n8n werden lokal nur simuliert

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Reale Notion- und n8n-Verbindungen muessen spaeter mit den jeweiligen Entwicklern und produktiven Systemen abgestimmt werden.
- Decision: Die lokale Welle implementiert versionierte Schnittstellen und klar gekennzeichnete Simulatoren. Sie behauptet keine Liveintegration.
- Rationale: Der komplette Workflow kann lokal geprueft werden, ohne spaetere Integrationsentscheidungen vorwegzunehmen oder technische Fallbacks zu verstecken.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 19. August 2026
- Impacted files/areas: Integration Contracts, Notion Simulator, n8n Simulator, UI Integration Status

## DEC-0016: Tickets und Eskalationen sind Teil des Workflowprodukts

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Ein spaeterer Operator ohne direkten Hermes-Zugang muss Fehler und fachliche Ablehnungen sicher bearbeiten koennen.
- Decision: Missing Input, Revision Request, Workflow Defect, Waiver Candidate, Management Decision, Compliance Decision und Abort erhalten strukturierte Routingregeln. Kein unkontrollierter freier Operator-Prompt steuert den Workflow.
- Rationale: Das System muss bei Fehlern sicher pausieren, klare Aufgaben erzeugen und den richtigen Entscheider einbeziehen.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 19. August 2026
- Impacted files/areas: Operator Contracts, Routing Service, Task Queue, Review Center, Transition Service

## DEC-0017: Heutiger Erfolgsmaßstab ist ein lokaler E2E-Vertical-Slice

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Jesse soll den qualitativen Unterschied zu den Basis-Prompts anhand eines vollstaendigen Projektdurchlaufs sehen.
- Decision: Die lokale Demonstration produziert die komplette Strategie bis Schritt 3 und fuehrt mindestens ein anhand realer Research-Daten priorisiertes Item vollstaendig durch 4a und 4b. Nicht alle Inhalte des 120-Tage-Plans werden produziert.
- Rationale: Jeder Workflow-Schritt wird real ausgefuehrt, ohne einen bereits produzierten 120-Tage-Zyklus vorzutäuschen.
- Supersedes: none
- Superseded by: none
- Evidence: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- Impacted files/areas: AHD Deliverables, Demo Scope, Final QA, Jesse Presentation

## DEC-0018: Lokaler Core, n8n-Gesamtorchestrierung und Notion-Projektbetrieb

- Status: superseded
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Der gesamte Heartweb-Workflow soll spaeter ueber n8n orchestriert werden. Gleichzeitig muss der fachliche Core zuerst vollstaendig lokal laufen koennen. Jesse nutzt Notion als zentrale Projektoberflaeche fuer Kundendaten, Projekttracking, Aufgabenverteilung und Performance-Zyklen.
- Decision: Der lokale Core bleibt unabhaengig ausfuehrbar und enthaelt die verbindlichen Vertraege, Gates, Transitionen, Artefakte, Evidence und Fehlerregeln. n8n bildet spaeter den vollstaendigen Ablauf als Orchestrierungs- und Transportebene ab, ruft den Core ueber versionierte Commands auf, startet Jobs, wartet auf Events und Gates und verarbeitet Retry, Resume und DLQ. Notion bildet Kunden, Projekte, Steps, Tasks, Verantwortliche, Termine, Blocker, Reviews, Approvals, Performance-Checkpoints, Metriken und Anpassungsvorschlaege als zentrale operative Daten- und Managementoberflaeche ab. Aufgaben fuer Copywriter, Designer, Entwickler und Reviewer werden aus typisierten Workflow-Events nach Notion projiziert. Kritische Workflowstatus, Hashes, Revisionen und Gateentscheidungen bleiben durch den lokalen Core beziehungsweise Transition Service geschuetzt.
- Rationale: Die lokale Ausfuehrbarkeit verhindert eine harte Abhaengigkeit von noch nicht abgestimmten Fremdsystemen. Die gleichen Commands, Events und Projektionen koennen spaeter durch echte n8n-Workflows und Notion-Datenbanken transportiert werden, ohne die fachliche Logik neu zu implementieren.
- Confirmed cadence: Der Performance-Zyklus laeuft an Tag 30, 60 und 90. Notion-Tracking, n8n-Trigger und Step-3b-Anpassungen muessen diese bestaetigte Taktung gemeinsam abbilden.
- Supersedes: none
- Superseded by: DEC-0025
- Evidence: Nutzerpraezisierung vom 19. August 2026; Meetingnotiz vom 17. August 2026
- Impacted files/areas: Local Workflow API, Event Store, n8n Simulator, Notion Simulator, Aufgabenverteilung, Performance Tracking, Step 3b, Operator Console, Integrationsmeeting

## DEC-0019: Kontinuierliche Projektsession und reproduzierbare LLM Runs

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Jeder Kundenworkflow soll fuer den Operator als kontinuierliches Projekt mit vollstaendiger Geschichte erscheinen. Technische Provider- oder Chat-Sessions koennen jedoch ablaufen, verloren gehen, komprimiert werden oder bei Modellwechseln unbrauchbar werden. Ein grosses Context Window ist kein dauerhafter Projektspeicher.
- Decision: Heartweb verwendet das Prinzip `stateful project, replaceable worker`. Der dauerhafte dateibasierte Projektzustand, append-only Events, freigegebene Artefakte, Evidence, Decisions, Gates und Revisionen sind die Autoritaet. Jeder Step- oder Revisionslauf erhaelt ein versioniertes Context Package mit exakten Quellen, Revisionen, SHA-256-Hashes, Prompt-ID und Promptversion. Ein LLM Run bindet Workerprofil, Provider, Modell, Toolpolicy, Context Package, Trigger, Input- und Output-Hashes sowie Ergebnis- und Tokenmetadaten. Eine technische Provider-Session darf als optionaler Cache wiederverwendet werden, ist aber niemals Voraussetzung oder Source of Truth. Der Standard ist ein frischer Run pro Step oder groesserer Revision. Ein verlorener Session-Handle muss aus dem Context Package reproduzierbar wiederherstellbar sein.
- Revision rule: Ein Rerun verwendet den offiziellen Step-Prompt, Project V2, freigegebene Vorgaenger, das abgelehnte Artefakt, maschinelle und menschliche Findings, die Operator-Anweisung, erlaubte Evidence, unveraenderliche Felder und den erwarteten Outputvertrag. Das alte Artefakt bleibt erhalten. Der Rerun erzeugt eine neue Revision.
- Context rule: Superseded, rejected oder historische Quellen werden nicht still als aktuell eingespeist. Untrusted Crawl-, SERP- und Wettbewerberinhalte werden als Daten markiert. Fehlende, stale, hash-falsche oder cross-tenant Inputs stoppen mit strukturiertem Fehler vor jedem LLM-Aufruf.
- Step-0 rule: Schritt 0 bindet ein unveraenderliches gehashtes Project-Intake, weil Project V2 erst als Ergebnis dieses Schritts entsteht. Ab Schritt 1 ist das freigegebene Project V2 Pflichtkontext. Die offizielle Prompt Registry bindet jeden Step an exakte Promptbytes und alle zugehoerigen Outputvertraege.
- Orchestration rule: Der lokale Core baut und validiert Context Packages und LLM Run Requests. n8n transportiert und orchestriert diese spaeter. Notion und Operator Console zeigen logische Projektsession, Run-Historie, Context-Zusammenfassung, Revisionen und Rerun-Aktionen, schreiben aber keinen kanonischen Status direkt.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerklaerung und Architekturabgleich vom 19. August 2026
- Impacted files/areas: Sprint 4 Context Builder, Runtime Contracts, Operator API, Event Store, n8n Simulator, Notion Simulator, Sprint 5 Operator Console, Revision Center, Run History

## DEC-0020: GEO-V2-Vertragsrestauration wird nach stabilem Sprint 5 verpflichtend ausgefuehrt

- Status: active
- Date: 2026-08-20
- Owner/source: Raphael Rechberger
- Context: Der Abgleich mit Session `20260817_151731_bc9488` und ADR-011 zeigt, dass die GEO-Grundarchitektur erhalten ist, konkrete Step-4a- und Step-4b-Qualitaetsregeln aber nicht vollstaendig in die aktuellen V2-Schemas, Prompts, Validatoren und Renderer uebernommen wurden.
- Decision: Die aktuelle Sprint-5-/5E-Ausfuehrung wird nicht unterbrochen. Nach ihrem stabilen und unabhaengig verifizierten Abschluss wird der verbindliche Plan `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` ausgefuehrt. Die Erweiterung nutzt die bestehenden Workflow-, Transition-, Artifact-, Revision-, Approval-, Release- und Provider-Gateway-Grenzen und baut keine parallele Architektur.
- Rationale: Der technische Golden Path soll zuerst stabil funktionieren. Die genehmigten GEO-Qualitaetsanforderungen fuer professionelle Copywriter- und Developer-Outputs duerfen zugleich nicht verloren gehen oder nur als Dokumentation bestehen bleiben.
- Supersedes: none
- Superseded by: none
- Evidence: Session `20260817_151731_bc9488`; `docs/07-geo-architecture-specification.md`; `docs/04-entscheidungslog.md`, ADR-011; Repository-Abgleich vom 20. August 2026
- Impacted files/areas: Step-4a- und Step-4b-Schemas, Prompts, Validatoren, Renderer, Quality Gates, Fixtures, Operator Console, AHD Golden Path

## DEC-0021: Neue Findings werden gesammelt und erst im freigegebenen Integrations-Sprint umgesetzt

- Status: active
- Date: 2026-08-20
- Owner/source: Raphael Rechberger
- Context: Waehrend der laufenden Basisimplementierung entstehen weitere SEO-, GEO-, UI-, Integrations- und Qualitaetsbeobachtungen. Sofortige Einzelkorrekturen wuerden den aktiven Scope wiederholt erweitern und koennten Inkonsistenzen erzeugen.
- Decision: `00_admin/DEFERRED_INTEGRATION_BACKLOG.md` ist der kanonische Sammelpunkt fuer alle neuen, nicht akut blockierenden Findings und Wuensche. Das Erfassen eines Items autorisiert keine Implementierung. Nach stabiler und unabhaengig verifizierter Basis priorisiert Raphael die Items fuer einen eigenen Integrations-Sprint. Aktive P0-/P1-Defects und bereits verbindliche Basisanforderungen duerfen nicht in den Backlog verschoben werden.
- Rationale: Die Basis wird zuerst fertig und beweisbar funktionsfaehig. Zusaetzliche Anforderungen gehen nicht verloren und werden spaeter als konsistente Pakete statt als isolierte Patches integriert.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 20. August 2026
- Impacted files/areas: Projektsteuerung, UI/UX, SEO/GEO Contracts, Integrationen, Quality Gates, spaeterer Integrations-Sprint

## DEC-0022: Branchkonsolidierung erfolgt erst nach dem Final-Gate

- Status: active
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Master, Feature und WIP bilden eine lineare Historie. Browser, Delivery, Outputqualitaet und erster realer Lauf sind noch nicht vollstaendig abgeschlossen.
- Decision: Vor dem Production Release Gate wird nichts nach master uebernommen. Hilfsbranches werden erst nach verifiziertem finalen SHA und ausdruecklicher Raphael-Freigabe konsolidiert oder geloescht.
- Rationale: Unfertige Zwischenstaende duerfen nicht als offizieller Hauptbranch erscheinen.
- Supersedes: none
- Superseded by: none
- Evidence: Branchgraph und Nutzerentscheidung vom 21. August 2026
- Impacted files/areas: Git, Release Gate, Feature, WIP, master

## DEC-0023: Vollstaendige Promptqualitaet vor dem damaligen Final-Audit

- Status: superseded
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Der Prompt-Paritaetsaudit zeigte reale V2-Qualitaetsluecken.
- Decision: Der damalige breite Plan sah PQ-0 bis PQ-5 vor dem Final-Audit vor.
- Rationale: Fachlich duenne, aber formal valide Outputs durften nicht freigegeben werden.
- Supersedes: none
- Superseded by: DEC-0024
- Evidence: Prompt-Paritaetsaudit und Restaurationsplan
- Impacted files/areas: Promptqualitaet, Final-Audit, Golden Path

## DEC-0024: Production-first Cut-Line priorisiert den ersten echten Output

- Status: active
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Wiederholte Mobile-, Evidence- und Vollreife-Schleifen verzoegerten den ersten realen Kundenoutput unverhaeltnismaessig.
- Decision: Vor dem ersten lokalen Production-Run werden nur releasekritische Desktop-Aktionen, Sprint 5E, DIB-005, bounded PQ-0, PQ-1, PQ-2 und PQ-4 sowie ein gezielter lokaler Audit abgeschlossen. Mobile-Politur, Live-Notion, Live-n8n, Deployment, Step 3B vor Tag 30 und breite Expansion bleiben Post-Release.
- Rationale: Heartweb muss zuerst reale professionelle Outputs liefern und danach anhand realer Nutzung verbessert werden.
- Supersedes: DEC-0023
- Superseded by: none
- Evidence: Nutzerentscheidung vom 21. August 2026; `00_admin/POST_RELEASE_BACKLOG.md`
- Impacted files/areas: Releasefolge, Sprint 5E, DIB-005, DIB-006, Golden Path, Post-Release

## DEC-0025: Notion uebernimmt die Umsetzung nach einmaligem Projekthandoff

- Status: active
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Heartweb soll den manuellen Strategie- und Planungsprozess automatisieren und ein vollstaendiges Kundenprojekt in Notion anlegen. Die spaetere Umsetzung durch Copywriter und Entwickler soll nicht als zweites Core-Workflow-System nachgebaut werden.
- Decision: Core und Console produzieren Step 0 bis Step 4B bis zur freigegebenen Delivery. Danach bleiben Umsetzungsaufgaben, Status, Kommentare, Verantwortliche, Prioritaeten, Termine, Review und Launch in Notion. Sie duerfen keinen Core-Run fortsetzen, kein Gate freigeben und kein Artefakt veraendern. Der einzige geplante Post-Handoff-Wiedereinstieg ist Step 3B an Tag 30, 60 und 90 mit verifizierten Performance-Daten.
- Rationale: Notion bleibt Jesses operative Steuerungsmatrix. Der Core wird nur erneut benoetigt, wenn reale Performance die Kernstrategie fachlich neu bewertet.
- Supersedes: DEC-0018
- Superseded by: none
- Evidence: Originalworkflow; `docs/integrations/notion-operating-model.md`; `docs/integrations/n8n-orchestration-model.md`
- Impacted files/areas: Sprint 5E, Notion, n8n, Tasks, Step 3B, Performance

## DEC-0026: Deterministische Repository-Authority-Registry steuert Sessionkontext und RAG

- Status: active
- Date: 2026-08-22
- Owner/source: Raphael Rechberger
- Context: Entry-Dokumente, aktuelle Architektur, historische Plaene, Audits und Evidence waren ohne einheitliche Lifecycle-Klassifikation gemischt. Neue LLM-Sessions konnten relevante, aber veraltete Quellen als aktuelle Anweisung behandeln.
- Decision: Heartweb verwendet eine deterministisch erzeugte Dokument-Registry mit Lifecycle, Authority-Level, Retrieval-Prioritaet, Default-Retrieval, Workflow-Step, Zielgruppe, Supersession und Content-Hash. Neue Sessions starten ueber `00_admin/SESSION_BOOTSTRAP.md`. Semantische RAG-Suche darf spaeter nur nach Lifecycle- und Authority-Filterung ranken. Historische und superseded Quellen bleiben erhalten, sind aber opt-in.
- Rationale: Vollstaendiger Kontext muss auffindbar bleiben, ohne dass historische Naehe aktuelle Autoritaet ueberschreibt. Eine Registry ist leichter wartbar und portabler als ein neuer Vector- oder Logserver.
- Supersedes: none
- Superseded by: none
- Evidence: `.hermes/plans/2026-08-22-repository-authority-rag-index.md`; `00_admin/repository-index/DOCUMENT_REGISTRY.json`; `tests/test_repository_index.py`
- Impacted files/areas: AGENTS, CLAUDE, README, Project State, Decisions, docs, plans, audits, research, future RAG ingestion

## DEC-0027: Heartweb testet Baseline plus betroffene Delta-Closure und berichtet ueber feste Main Tasks

- Status: active
- Date: 2026-08-22
- Owner/source: Raphael Rechberger
- Context: Wiederholte komplette Suites und breite Multi-Agent-Reviews nach kleinen Fixes verbrauchten Zeit und Modellbudget, waehrend wechselnde Root-Todo-Zaehler keinen stabilen Gesamtfortschritt zeigten.
- Decision: `standards/testing/PROTOTYPE_TEST_POLICY.md` ist die bindende projektlokale Testautoritaet. Eine gruene Baseline bleibt fuer unveraenderte Bereiche gueltig. Nach einer Aenderung werden nur geaendertes Modul, betroffener Vertrag, Route, Flow, Gate und benannte direkte Abhaengigkeiten geprueft. Eine komplette Repository-Suite braucht neue ausdrueckliche Raphael-Freigabe. Der Gesamtfortschritt zeigt gleichzeitig die kanonische 13-Stufen-Sprint-Roadmap und die 10 festen Production-first-Main-Tasks aus `00_admin/MASTER_TASK_MATRIX.md`; dynamische Root-Todos sind Subtasks.
- Rationale: Heartweb muss schnell operativ nutzbar werden, ohne Datenintegritaet und nachvollziehbare Evidence aufzugeben. Risikobasierte Delta-Pruefung erhaelt bestehende Evidence und verhindert endlose Test- und Review-Loops.
- Supersedes: alte generische Full-Suite-, Vollmatrix- und wechselnde Root-Todo-Gesamtzaehler fuer dieses Projekt
- Superseded by: none
- Evidence: Raphael-Instruktionen vom 22. August 2026; `standards/testing/PROTOTYPE_TEST_POLICY.md`; `00_admin/MASTER_TASK_MATRIX.md`
- Impacted files/areas: AGENTS, CLAUDE, Sprint-5- und Sprint-5E-Plaene, Root-Sisyphus-Todos, Cronstatus, Release Audit und Prototype-Matrix
