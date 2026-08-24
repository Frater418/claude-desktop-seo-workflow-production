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
- Context: `master`, `feature/e2e-operator-workflow-system` und der WIP-Checkpoint bilden eine lineare Historie ohne Divergenz. Browser-QA, Sprint 5E und Final-Audit sind noch offen.
- Decision: Vor dem vollstaendigen Final-Gate wird nichts nach `master` gemergt. Nach bestandenem Final-Gate wird der finale Arbeitsstand als Nachfolger des WIP-Checkpoints committed, der Feature-Branch auf diesen finalen Commit gebracht und verifiziert. Anschliessend wird `master` per Fast-Forward auf den finalen Feature-Stand gesetzt. WIP- und Feature-Hilfsbranches werden erst nach verifiziertem Remote-SHA und ausdruecklicher Abschlusskontrolle geloescht.
- Rationale: Die lineare Historie erlaubt eine konfliktfreie Konsolidierung, ohne einen unfertigen Zwischenstand als offiziellen Hauptbranch zu veroeffentlichen oder Sisyphus waehrend der aktiven Arbeit zu stoeren.
- Supersedes: none
- Superseded by: none
- Evidence: Nutzerentscheidung vom 21. August 2026; verifizierter Branchgraph mit `master -> feature -> WIP`
- Impacted files/areas: GitHub Branchstrategie, Final-Audit, Release Gate, WIP-Checkpoint, Feature-Branch, master

## DEC-0023: Promptqualitaet wird vor dem bestehenden Final-Audit in V2 restauriert

- Status: superseded
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Der Read-only-Abgleich der originalen Desktop-Prompts, der master-Prompts und der aktuellen V2-Schemas, Preflights und Renderer zeigt, dass die technische V2-Architektur sicherer ist, aber mehrere outputkritische Anforderungen nicht vollstaendig migriert wurden. Betroffen sind 1B-Praesentation, 1C-Template-Tiefe, Step-2-Metriken und Recherchebreite, die reale Step-2-zu-Step-3-Solverkette, Step-3B-Performance-Semantik sowie die bereits in DIB-001 dokumentierte Step-4A/4B-Qualitaet.
- Decision: Die laufende Browser-QA und Sprint 5E werden nicht unterbrochen. Nach einem stabilen Sprint-5E-Checkpoint wird zuerst DIB-005 implementiert, danach DIB-006 mit PQ-0 bis PQ-5. Der bereits vorhandene Sprint-5-Final-Audit-Todo wird bis zum Abschluss dieser Pakete zurueckgestellt. Alte Prompts werden nicht komplett zurueckkopiert. Fehlende Anforderungen werden in die bestehenden V2-Schemas, Validatoren, Renderer, Quality Gates und Admin-Oberflaechen integriert.
- Rationale: Die sichere V2-Architektur bleibt erhalten, waehrend die urspruenglich genehmigte SEO-, GEO-, Conversion-, Copywriter-, Developer- und Praesentationsqualitaet wieder maschinenpruefbar wird. Ein Audit vor dieser Restauration koennte einen technisch validen, aber fachlich zu duennen Workflow faelschlich freigeben.
- Supersedes: none
- Superseded by: DEC-0024
- Evidence: `00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md`; `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`; Desktop Promptworkflow; Git baselines `a10093b`, `c818ffc`, `5e78679`
- Impacted files/areas: Sisyphus Root-Todo-Reihenfolge, DIB-001, DIB-005, DIB-006, Output-Schemas, Prompts, Preflights, Renderer, Quality Gates, Admin Review, Final-Audit, AHD Golden Path, Branchkonsolidierung

## DEC-0024: Production-first Cut-Line priorisiert den ersten echten Output

- Status: active
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Der lokale Core und die Admin Console sind weit fortgeschritten, waehrend wiederholte Mobile- und Evidence-Schleifen den ersten echten Output unverhaeltnismaessig verzoegern. Raphael muss schnell produktiv arbeiten und reale Kundenartefakte liefern. Live-Notion, Live-n8n, perfekte Mobile-Politur, Step-3B vor realen Tag-30-Daten, Voll-Dokumentation und Repository-Cleanup sind dafuer nicht erforderlich.
- Decision: Der aktuell laufende Browser-Harness darf einmal abschliessen. Danach sind Desktop und Kernaktionen release-blocking; reine Mobile-Komfort- oder Scrollprobleme werden Post-Release behandelt, solange sie keine Daten korrumpieren, keine erforderliche Reviewaktion unzugaenglich machen und keinen falschen Erfolg erzeugen. Vor dem ersten lokalen Production-Run werden nur Sprint 5E, DIB-005, bounded PQ-0, PQ-1, PQ-2 und PQ-4 sowie ein gezielter Production Release Audit abgeschlossen. PQ-3, PQ-5, Live-Notion, Live-n8n, umfassende Mobile-QA, Voll-Dokumentation, Repository-Hygiene, breite Archetypen- und Praesentationsarbeit gehen in `00_admin/POST_RELEASE_BACKLOG.md`.
- Rationale: Die erste Releasegrenze muss korrekte, sichere und professionell nutzbare Outputs beweisen, nicht maximale Produktreife in jedem spaeteren Kanal. Reale Nutzung liefert schneller die wertvollste Evidence fuer weitere Verbesserungen.
- Supersedes: DEC-0023
- Superseded by: none
- Evidence: Nutzerentscheidung vom 21. August 2026; `00_admin/POST_RELEASE_BACKLOG.md`; `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`; aktueller Browser-QA-Verlauf
- Impacted files/areas: Sisyphus Root-Todos, Browser-Gate, Sprint 5E, DIB-005, DIB-006, targeted Production Release audit, AHD Golden Path, Post-Release-Planung, Branch- und Deployment-Gates

## DEC-0025: Notion uebernimmt die Umsetzung nach einmaligem Projekthandoff

- Status: active
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: Heartweb soll einen manuellen SEO-/GEO-Prozess automatisieren, ein vollstaendiges Kundenkonzept erzeugen und dieses als operatives Projekt mit Aufgaben, Verantwortlichen, Prioritaeten, Terminen und Umsetzungsunterlagen in Notion anlegen. Die spaetere Arbeit von Copywritern, Designern und Entwicklern wird dort durch Jesse und das Team gesteuert. Eine permanente Rueckmeldung einzelner Mitarbeiteraufgaben an den Core war nie Produktziel und wuerde unnoetige Softwarekomplexitaet erzeugen.
- Decision: Der Core und die Operator Console fuehren Step 0 bis Step 4B bis zur freigegebenen Delivery aus. Sprint 5E erzeugt ein vollstaendiges Notion-Kundenprojekt und trennt Core-interne Produktionstasks von Notion-eigenen Umsetzungsaufgaben. Nach dem Handoff bleiben Status, Kommentare, Verantwortliche, Prioritaeten, Deadlines, Review und Launch der Umsetzungsaufgaben ausschliesslich in Notion. Sie duerfen keinen Core-Run fortsetzen, kein Gate freigeben, keine Revision erzeugen und kein Artefakt veraendern. Der einzige geplante automatisierte Wiedereinstieg ist Step 3B an Tag 30, 60 und 90: n8n verbindet die freigegebene Kernstrategie und den Plan mit verifizierten realen Performance-Daten, der Core erzeugt einen versionierten Anpassungsvorschlag und nach expliziter Strategiefreigabe werden nur zukuenftige Planung und Aufgaben angepasst.
- Rationale: Heartweb soll Arbeit abnehmen und eine umsetzbare Strategie liefern, nicht die menschliche Projektabwicklung nach dem Handoff als zweites Betriebssystem nachbauen. Notion bleibt Jesses zentrale Steuerungsmatrix. Der Core wird nur dort erneut benoetigt, wo reale Performance die Kernstrategie fachlich neu bewerten soll.
- Supersedes: DEC-0018
- Superseded by: none
- Evidence: Nutzerklaerung vom 21. August 2026; `C:\Users\offic\Desktop\Heartweb\Promptworkflow\0b-Workflow-Uebersicht.md`; `C:\Users\offic\Desktop\Heartweb\Promptworkflow\3b-Performance-Check-Tag30-60-90.md`; `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`; `docs/integrations/notion-operating-model.md`; `docs/integrations/n8n-orchestration-model.md`
- Impacted files/areas: Sprint 5E, Notion Import Pack, Notion Live Adapter, n8n Workflow, Integration Contracts, internal Operator Tasks, Step 3B, Performance Checkpoints, Project State, Post-Release Backlog

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

## DEC-0028: Testweise reale LLM-Ausfuehrung nutzt Option A ueber ein isoliertes Hermes-Gateway-Profil

- Status: active
- Date: 2026-08-23
- Owner/source: Raphael Rechberger
- Context: Die bestehende Heartweb Runtime bindet Context Package, Prompt, Worker Profile, Provider, Modell, Toolpolicy, Outputvertrag und Resultat, fuehrt aber vor M10 noch keinen echten Modellcall aus. Raphael moechte den vorhandenen OpenAI-Codex-OAuth-Zugang ueber Hermes nutzen, ohne OAuth-Tokens in Heartweb einzubauen oder Heartweb von Hermes als einziger Produktionsroute abhaengig zu machen.
- Decision: M08L wird nach dem stabilen M08-Snapshot und vor M09 ausgefuehrt. Root Sisyphus implementiert die Heartweb-Core-Seite mit providerneutralem Execution Backend, Hermes-Adapter, Persistenz, Replay, Recovery und fokussierten Tests. Hermes verantwortet die Hermes-seitige Capability-Probe, das isolierte Profil `heartweb-runtime`, die Hermes-verwaltete Shared-OAuth-Pool-Grenze, die versionierten Modell- und Reasoning-Profile, den neutralen realen Gateway-Nachweis und die unabhaengige Abnahme. Der bestehende OpenAI-Codex-OAuth-Pool bleibt in Hermes und wird vom Profil nur ueber den read-only Provider-Fallback aufgeloest. OAuth-Tokens werden nicht kopiert und nicht an Heartweb, Sisyphus oder Worker uebermittelt. Das Profil verwendet ein eigenes eingebautes `MEMORY.md`, kein `USER.md` und keinen externen Memory-Provider. Heartweb kennt nur einen lokal injizierten API-Server-Key und nicht geheime Provider-/Modellmetadaten. Hermes liefert nur einen Artefaktkandidaten und darf keinen Workflowstatus, kein Gate und keine Revision verbindlich setzen.
- Production-first amendment: Vor M09 wird nur ein duennes Hermes-Runs-Backend gebaut, das die bestehenden Context-, Request-, Result-, Validierungs-, Artefakt-, Idempotency-, Persistenz- und Diagnosegrenzen wiederverwendet. Allgemeine Backend-Registry, separater Execution-Record-Store, direkte Multi-Provider-Adapter, Delegation Contracts, Subagent-Orchestrierung und breite Benchmark-Infrastruktur sind Post-M10. Ein neues Schema oder eine neue Persistenzfamilie ist vor M09 nur zulaessig, wenn ein konkret nachgewiesenes Pflichtfeld durch keine bestehende Authority abbildbar ist.
- Model policy: `gpt-5.6-sol` mit `high` ist fuer 1B, 4A und kritische Schlussreviews vorgesehen, nicht fuer jeden Step. Strukturierte oder deterministisch gestuetzte Steps verwenden ein validiertes schnelleres oder ausgeglichenes Profil mit `low` oder `medium`. Fehlende Modelle oder OAuth-Verfuegbarkeit stoppen fail-fast; kein stiller Provider-, Modell- oder Reasoning-Fallback.
- Rationale: Der erste reale lokale Output kann den vorhandenen OAuth-Zugang sicher und reproduzierbar nutzen, ohne vorab eine allgemeine LLM-Plattform zu bauen. Die Heartweb-Authority-Grenze bleibt erhalten; spaetere direkte offizielle API-Adapter und allgemeine Routinginfrastruktur werden erst aus realer Nutzung begruendet.
- Supersedes: none
- Superseded by: none
- Evidence: Raphael-Entscheidung vom 23. August 2026; `.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md`; verifizierter M08-WIP-Snapshot `568bb497e57af4f7ec6dc8a13438681bbf423a55`
- Acceptance: Realer neutraler Step-0-Lauf PASS mit schema-validem Manifest, persistiertem Context Package und LLM Result, Provider Run ID, Modell- und Tokenmetadaten sowie null Toolcalls. `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.
- Impacted files/areas: Runtime Contracts, Worker Profiles, LLM Gateway, Operator API, Runtime Persistence, Recovery, Hermes Profile, OAuth-Grenze, Modellrouting, M09, M10
