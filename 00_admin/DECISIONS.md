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

- Status: active
- Date: 2026-08-19
- Owner/source: Raphael Rechberger
- Context: Der gesamte Heartweb-Workflow soll spaeter ueber n8n orchestriert werden. Gleichzeitig muss der fachliche Core zuerst vollstaendig lokal laufen koennen. Jesse nutzt Notion als zentrale Projektoberflaeche fuer Kundendaten, Projekttracking, Aufgabenverteilung und Performance-Zyklen.
- Decision: Der lokale Core bleibt unabhaengig ausfuehrbar und enthaelt die verbindlichen Vertraege, Gates, Transitionen, Artefakte, Evidence und Fehlerregeln. n8n bildet spaeter den vollstaendigen Ablauf als Orchestrierungs- und Transportebene ab, ruft den Core ueber versionierte Commands auf, startet Jobs, wartet auf Events und Gates und verarbeitet Retry, Resume und DLQ. Notion bildet Kunden, Projekte, Steps, Tasks, Verantwortliche, Termine, Blocker, Reviews, Approvals, Performance-Checkpoints, Metriken und Anpassungsvorschlaege als zentrale operative Daten- und Managementoberflaeche ab. Aufgaben fuer Copywriter, Designer, Entwickler und Reviewer werden aus typisierten Workflow-Events nach Notion projiziert. Kritische Workflowstatus, Hashes, Revisionen und Gateentscheidungen bleiben durch den lokalen Core beziehungsweise Transition Service geschuetzt.
- Rationale: Die lokale Ausfuehrbarkeit verhindert eine harte Abhaengigkeit von noch nicht abgestimmten Fremdsystemen. Die gleichen Commands, Events und Projektionen koennen spaeter durch echte n8n-Workflows und Notion-Datenbanken transportiert werden, ohne die fachliche Logik neu zu implementieren.
- Confirmed cadence: Der Performance-Zyklus laeuft an Tag 30, 60 und 90. Notion-Tracking, n8n-Trigger und Step-3b-Anpassungen muessen diese bestaetigte Taktung gemeinsam abbilden.
- Supersedes: none
- Superseded by: none
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
- Orchestration rule: Der lokale Core baut und validiert Context Packages und LLM Run Requests. n8n transportiert und orchestriert diese spaeter. Notion und Operator Console zeigen logische Projektsession, Run-Historie, Context-Zusammenfassung, Revisionen und Rerun-Aktionen, schreiben aber keinen kanonischen Status direkt.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerklaerung und Architekturabgleich vom 19. August 2026
- Impacted files/areas: Sprint 4 Context Builder, Runtime Contracts, Operator API, Event Store, n8n Simulator, Notion Simulator, Sprint 5 Operator Console, Revision Center, Run History
