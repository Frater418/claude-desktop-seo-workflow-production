# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 26. August 2026
**Status:** Production-first Completion in Ausfuehrung. Der DEC-0029-Produktionspfad und die DEC-0030-Multi-Location-Bindung sind implementiert. Im realen CL-Projekt ist Step 0 mit Manifest V2 Revision 3, Project V2 1.3.0, Deployment `dep-cl-performance-de`, Provider Target `agentseo-de-country`, `DE / 2276 / de`, Region Deutschland und 10 operatorbestaetigten Wochenstunden freigegeben, abgeschlossen und released. Step 1 Run `run-next-7f7e2b778f4521b9` steht auf `in_progress`; fuer ihn existieren noch keine Production Execution, keine Agent Evidence und kein LLM Run. M10, PT-03 und PT-11 bleiben bis zur echten Step-1-Produktion, dem kompletten weiteren Workflow, Human Review und kontrollierten Kundenoutput offen. DEC-0031 autorisiert parallel die vollstaendige Repository-Konsolidierung nach `master`, ohne daraus Production Acceptance abzuleiten.
**GitHub Repository:** https://github.com/Frater418/claude-desktop-seo-workflow-production  
**Kanonischer Pfad:** `C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow\`  
**Desktop-Pfad:** `C:\Users\offic\Desktop\Heartweb\claude-desktop-seo-workflow-production\`  

---

## 1. Projekt-Kontext & Rollen

- **Ziel:** Kundenneutraler lokaler SEO-/GEO-Produktionscore mit gefuehrtem Step-0-bis-4b-Workflow, deutscher Single-Admin-Console, professionellen Copywriter-/Developer-Paketen, Delivery, Notion-Projektion und spaeterer n8n-Orchestrierung.
- **Stakeholder & Team:**
  - **Raphael Rechberger:** Technical Operations & AI Integration Architect (fuehrt die Rollouts durch, steuert die Pipeline, baut die Schnittstellen).
  - **Jesse Jensen:** Lead & Strategie Heartweb (steuert Kundenbeziehungen, Onboarding, Freigaben).
  - **Copywriting-Team:** Regina, Katja, Alexander (erhalten saubere 4a-Briefings fuer redaktionelle Veredelung in Notion).
  - **Entwicklung / Design:** Thure, Rahul, Wayan (erhalten 1b-Menuebaeume und 4b-HTML-Templates fuer WordPress/Elementor).
  - **Automation / Tech:** Manuel (Social/YouTube-Automation & technische Audits).

---

## 2. Abgeschlossener Arbeitsstand (Was fertig gebaut ist)

1. **Standards & Vertraege (`standards/`):**
   - `manifest-v2.schema.json`: Aktiver JSON-Schema-Draft-2020-12-Vertrag fuer das deploymentgebundene Step-0-Manifest. `manifest.schema.json` bleibt Legacy-Vertrag.
   - `design-system.css`: Autarke CSS-Token-Schablone (Farben, Typo, Cards, Buttons) fuer Landingpages.
   - `dateinamen-und-output-vertrag.md`: Verbindliche Pfade und Dateinamen fuer alle Schritte.
   - `domain/provider-location-registry.json`: Aktive, versionierte Provider-Target-Authority pro Search Deployment. `location-codes.json` bleibt Legacy-Tabelle und ist kein Produktionslookup.

2. **9 Produktions-Prompts (`prompts/`):**
   - `0-kickoff-v1.10.0.xml.md`: Erzeugt das Manifest V2 aus exakter Deployment-, Provider- und Kapazitaetsbindung.
   - `1-pillar-identifikation.xml.md`: Core Pillars & Content Gaps.
   - `1b-seitenarchitektur.xml.md`: Menue-Tree & `1b-menuestruktur.html`.
   - `1c-pillar-template.xml.md`: Screenshot-Analyse, CSS-Extraktion & Pillar-HTML.
   - `2-cluster-recherche.xml.md`: Automatisierte AgentSEO Keyword-Anreicherung.
   - `3-120-tage-plan.xml.md`: 120-Tage-Roadmap & zweidimensionale Verlinkungs-Map.
   - `3b-performance-check.xml.md`: Tag 30/60/90 Ranking-Sync & Phasenanpassung.
   - `4a-content-briefing-und-schema.xml.md`: SERP-Check, Notion-Frontmatter fuer Texter & Schema JSON-LD.
   - `4b-landingpage-html.xml.md`: Autarker HTML-Generator fuer lokale Landingpages.

3. **Deterministische Python-Tools (`mcp/tools/`):**
   - `capacity_matrix_solver.py` (v1.3.0): Verteilt validierte Deliverables deterministisch auf einen 17-Wochen-Horizont, erzwingt die Obergrenze, weist aktive Wochen aus und unterstuetzt GEO-Content-Typen.
   - `validate_schema_jsonld.py`: Autarke CLI-Validierung fuer JSON-LD, Google Rich Results und strikte GEO-Entity-Bindungen.
   - Aktuelle DEC-0029-Produktionsroute: Typisierte Heartweb-Tools routen Step 1B, Step 2 und Step 4A serverseitig ueber Provider Gateway zum explizit gebundenen AgentSEO-Adapter. DataForSEO bleibt eine spaetere alternative Capability und ist kein stiller Fallback. Alte `mcp/tool-contracts/` sind Legacy-Kandidaten.

4. **Dokumentation & Handbuecher (`docs/`):**
   - `betriebshandbuch-claude-desktop.md`: Schritt-fuer-Schritt-Anleitung fuer die Desktop App & Projects.
   - `copywriter-handoff-guidelines.md`: Leitfaden fuer die Notion-Uebergabe an Regina, Katja, Alexander.
   - `jesse-walkthrough-memo.pdf`: Exakt ausbalanciertes 2-Seiten-Memo fuer Jesse.
   - `01-review-abgleich.md`, `02-research-und-technische-spezifikation.md`, `03-sprint-plan.md`, `04-entscheidungslog.md`, `05-human-in-the-loop.md`, `06-pilot-abnahme-checkliste.md`.

5. **Akzeptanztests & Fixtures (`tests/`):**
   - Akzeptanztests dokumentiert in `tests/acceptance-tests.md`.
   - Fixtures fuer simCura Pflegedienst (`sample_manifest.json`, `sample_cluster_keywords.json`).

---

## 2b. Stand vom 17. August 2026

- **Konsistenz-Audit & Live-Testlauf:** Schritte 0 bis 4b im Testworkspace auditiert und refaktoriert (ADR-008 bis ADR-010).
- **Call mit Jesse erfolgreich abgeschlossen:**
  - Architektur v1.2.0 / v1.3.0 vollstaendig besprochen und bestaetigt.
  - Dokumentiert in `00_admin/meetings/2026-08-17-meeting-raphael-jesse.md`.
  - Rechnungsabwicklung fuer August besprochen (Details per WhatsApp / Andreas).
- **Neuer strategischer Schwerpunkt: GEO (Generative Engine Optimization):**
  - Forschungsauftrag durch Jesse erteilt.
  - Perplexity Deep Research und Exa.ai Multi-Angle API-Verifikation erfolgreich durchgefuehrt.
  - Rohdaten unter `03_research/exa_geo_research_raw.json` persistiert.
- **Infrastruktur:**
  - Claude Desktop App aktiv, AgentSEO MCP-Server und GitHub MCP-Server erfolgreich angebunden.

---

## 3. Aktueller Status & Naechste operative Schritte

### Aktueller Konsolidierungs- und Produktionscheckpoint vom 26. August 2026

- DEC-0031 autorisiert den vollstaendigen aktuellen Repository-Stand als neuen `master`-Basisstand. DEC-0032 autorisiert die deterministische `00_admin/ONBOARDING_REFERENCE.md`. Beides ist Repositorykonsolidierung und kein Production-Acceptance-Nachweis.
- Vor der Git-Konsolidierung wurde ein externer Recovery-Snapshot mit 1.185 relevanten Dateien, vollstaendigem Git-Bundle aller Refs, bytegeprueftem Working Tree und redigierter Sensitive-File-Pruefung erstellt. Nachweis: `C:\Users\offic\Documents\Projekte\Hermes\90_archive\project-snapshots\Heartweb-Claude-Desktop-SEO-Workflow\2026-08-26_06-46-51_-0400-pre-master-consolidation\SNAPSHOT_OK.txt`.
- Der M08-Snapshot-Commit `568bb497e57af4f7ec6dc8a13438681bbf423a55` wurde ueber alle 635 geaenderten Pfade abgeglichen: 424 bytegleich, 140 in spaeterer Commit-Historie vorhanden, 71 im aktuellen post-M08-Worktree weiterentwickelt, 0 fehlend, 0 ungeklaert. Authority: `00_admin/audits/2026-08-26-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`.
- Reales CL-Projekt: Step 0 Revision 3 ist freigegeben, abgeschlossen und released. Step 1 Run `run-next-7f7e2b778f4521b9` ist `in_progress`. Es existieren noch keine Step-1-Production-Execution, keine Agent Evidence und kein LLM Run. Der Produktionsworkflow bleibt waehrend der Repositorykonsolidierung bewusst eingefroren.
- Gateway und Operator Console sind fuer den Freeze gestoppt. Der entfernte stale PID-Record war ausschliesslich lokale Runtime-Metadatei. Er enthielt keinen Repository- oder Kundenquellstand.
- Die letzte Git-Connectivity-Pruefung bestand fuer HEAD und Objektgraph. Die abschliessende affected-closure Verifikation, der Build, Secret Scan, Repository-Index-Check und `hermes verify --json` werden nach Abschluss aller Source-Reconciliations frisch ausgefuehrt.
- Exakte Live-Branches, Remote-SHAs und Worktrees werden nicht in diesem Dokument gecacht. Sie muessen vor jeder Git-Mutation direkt aus Git gelesen und nach jeder Mutation erneut verifiziert werden.

### Historische Planungs- und Ausfuehrungscheckpoints vom 22. bis 25. August 2026

- Kanonischer Masterplan: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- Primaerer Admin-Operator: Raphael Rechberger. Keine Rollenumschaltung oder separaten Copywriter-/Developer-Portale.
- Notion bleibt die zentrale operative Heartweb-Oberflaeche nach dem Handoff. Die erste lokale Release verwendet das deterministische manuelle Importpaket. Live One-way-Projekterstellung ist Post-Release und blockiert den ersten Output nicht.
- n8n bleibt spaetere Orchestrierungs- und Transportschicht. Der lokale Core funktioniert unabhaengig.
- Golden Path: AHD Hausbesuch. Der reale AHD-Lauf ist noch nicht vollstaendig ausgefuehrt.
- Ein neutraler lokaler Fixture-E2E erzeugt den kanonischen Backend-Lifecycle von Step 0 bis Step 4b. Das beweist den Core, nicht reale Kunden- oder Providerqualitaet.
- Package 4 Backend, Actions, Artefaktinhalt, Revisionen, Diff und kanonisches Readback sind implementiert.
- Die deutsche Single-Admin-Console ist implementiert. Alle sechs sichtbaren Arbeitsbereiche, einschliesslich der vorhandenen `Uebergabe und Export`-Route, bestanden die 24-Zellen-Browsermatrix an vier Viewports. Die funktionalen Kernaktionen besitzen separate Browser-Evidence.
- Sprint 5E Tasks 1 bis 5 sind abgeschlossen: Delivery-Vertraege, Inventar und Policy, Rollenpakete, manuelles One-way-Notion-Importpaket und sicherer deterministischer ZIP-Builder.
- M04 Task 6 Delivery API ist unter der bindenden Testpolicy fokussiert abgeschlossen. Preview, Create, History, Record, Download, Replay und Recovery sind implementiert; die fruehere 563er-Suite bleibt Baseline und die aktuelle Delta-Closure ist gruen.
- M05 ist abgeschlossen. Die bestehende `Uebergabe und Export`-Seite bietet typed Delivery Preview, Create, History, Record und ZIP-Download, ohne die verifizierte Console-Shell neu zu bauen.
- M06 ist abgeschlossen. Ein fokussierter neutraler Live-Flow ueber UI, lokale API, Persistenz, Checkpoint-ZIP, Final-ZIP und exakten Replay besitzt gespeicherte Section-11-Evidence.
- M07 ist abgeschlossen. Der gemeinsame gitignorierte Trace-Root ist `var/operator-diagnostics/v1/`; abgeschlossene Runs bleiben append-only, `current` zeigt auf den neuesten Run und Secrets oder Rohdokumente sind ausgeschlossen. Reale Browser- und Persistenz-Evidence liegt unter `00_admin/audits/2026-08-22-m07-diagnostic-trace/`.
- M08 ist abgeschlossen. PQ-0 dokumentiert 46 Anforderungen. PQ-1, PQ-2 und PQ-4 sind fokussiert akzeptiert. Step 4A und Step 4B besitzen wieder professionelle typed Outputsets, deterministische Renderer, ehrliche Evidence-Grenzen und eine exakte Console-Reviewdarstellung.
- Der stabile M08-GitHub-Snapshot ist `wip/m08-output-quality-2026-08-23`, Commit `568bb497e57af4f7ec6dc8a13438681bbf423a55`; aktiver Feature-Branch, HEAD und Git-Index blieben unveraendert.
- M08L ist als Transportnachweis abgeschlossen. Der duenne Hermes-Runs-Adapter bestand einen echten neutralen Step-0-Lauf mit schema-validem Manifest, persistiertem Context Package und LLM Result, Provider Run ID, `gpt-5.6-sol`, Token Usage und null Toolcalls. DEC-0029 superseded die damalige Post-M10-Verschiebung der Delegation und Subagent-Orchestrierung: Die spezialisierte Hermes-Agent-, Tool- und Providerproduktion fuer alle Schritte ist releasekritisch. Evidence des Transportnachweises: `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.
- Die automatisierte M09-Matrix PT-01 bis PT-10 und der 1280x900-Chrome-Smoke waren in ihrem geprueften Umfang gruen. Die daraus abgeleitete Aussage `offene P0/P1 sind null` ist durch die manuelle CL-Performance-Abnahme vom 24. August 2026 superseded. Der reale Run stand auf `in_progress`, hatte kein Artefakt und bot keine Produktionsaktion. Auch Einreichung, Abschluss und Folgeschrittanlage fehlten in der sichtbaren Schrittsteuerung. Evidence des frueheren Umfangs: `00_admin/audits/2026-08-24-m09-route-matrix/SECTION_11_REPORT.md`.
- Der Korrekturstand vom 24. August 2026 zeigt statusgebundene Aktionen fuer Start, reale Produktion, Gate-Einreichung, Review, Abschluss und Folgeschrittanlage. Schritt 0 ist an den realen Hermes-Runs-Adapter, Vertragsvalidierung und Artefaktpersistenz gebunden. Dieser direkte Lauf ist noch kein Nachweis der durch DEC-0029 verlangten spezialisierten Agent-, Subagent-, Tool- und Providerarchitektur fuer alle Schritte. Frontend-Produktionsbuild: 55 Module, Exitcode 0. Python-Produktionsmodule: `py_compile` Exitcode 0. Testsuite und Browserautomation wurden auf Raphaels ausdrueckliche Vorgabe nicht ausgefuehrt; der Stand bleibt bis zu seiner manuellen Abnahme `unverified`.
- Konsolidierungsstand vom 25. August 2026: Alle acht Production-Prompts laden mit ihren aktuellen SHA-256-Bindungen, Worker Profiles und Tool Policies. Die direkte Acht-Step-Contractclosure erreichte 182 von 183 sofort gruene Tests. Der einzige Fehler, eine duplizierte Step-3-Solver-Exceptionklasse, wurde auf den kanonischen MCP-Solverpfad vereinheitlicht; die fehlgeschlagene Zelle und ihre direkten Renderer-Dependents bestanden danach 4 von 4. Repository-Index und Frontend-Produktionsbuild sind gruen. Eine breite Gesamtsuite wurde gemaess `standards/testing/PROTOTYPE_TEST_POLICY.md` nicht neu gestartet.
- Historischer CL-Performance-Checkpoint vom 25. August 2026 vor der GATE-0-Freigabe: Tenant `tenant-heartweb`, Projekt `project-cl-performance-bundesweite-sichtbarkeit-fur-b2b-3d-druck`, Run `run-neutral-0001`, Step 0 Revision 3, damaliger Runstatus `awaiting_gate`, Artefakt `artifact-5e21d144e75b15b2`, Content SHA-256 `c0e41d905bfdec1fa33ba7395d1c7eae62b914163a12900ff5360942eee109a3`, Parent `artifact-e9ed0fbaf1842ffa`. Der aktive Vertrag war `manifest-v2.schema.json` 2.0.0. Project V2 1.3.0, Manifest und Preflight banden exakt `dep-cl-performance-de`, `agentseo-de-country`, `DE / 2276 / de`, Region Deutschland und `10 / 10` operatorbestaetigte Wochenstunden. Dieser Zwischenstand ist durch den aktuellen 26.-August-Checkpoint mit freigegebenem und released Step 0 superseded.
- Generische Korrektur: Neue Intakes erzeugen alle Market Deployments und verifizierten Provider Targets vor Step 0. Fehlende Wochenkapazitaet wird als Missing Input markiert. Neue Projekte verwenden den vorhandenen Intake-Ergaenzungsdialog; bereits angenommene Projekte besitzen in der Console einen Preview-/Confirm-Dialog. Jede bestaetigte Aenderung versioniert Project V2, Intake und Logical Project Session gemeinsam. Der Country Lookup des Legacy-Manifestpfads ist aus der aktiven Produktion entfernt.
- Schritt 3b bleibt bis zu realen Post-Publication-Daten auf `not_due`.
- Die damalige Sperre gegen einen `master`-Merge vor dem Final-Gate ist durch DEC-0031 fuer die dokumentierte Repository-Konsolidierung superseded. Production Acceptance und Deployment bleiben davon unberuehrt und weiterhin gesondert gesperrt.
### Ausfuehrungsstand und Checkpoints bis 21. August 2026

- Ausfuehrungsfreigabe erteilt.
- Sprint 0: abgeschlossen. Pre-E2E-Checkpoint mit 121 Datei-Hashes, Host- und OMO-Baseline sowie AHD-Step-0-Hashpruefung vorhanden.
- Sprint 1: abgeschlossen und unabhaengig freigegeben.
- Sprint 2: abgeschlossen und unabhaengig freigegeben. Operator-, Ticket-, Eskalations-, Workflow-Event-, Notion-Projektions- und n8n-Command-Vertraege sind vorhanden.
- Sprint 3: abgeschlossen und unabhaengig freigegeben. Alle Outputs 1b bis 4b besitzen geschlossene V2-Vertraege, mandatory lineage, kontrollierte Rendererpfade, Provider-Evidence-Bindung und negative Sicherheitsregressionen.
- Windows Host, Sprint-4-Abschluss: Acceptance 7, Root Tests 247, Contract Tests 59, gesamt 313 bestanden.
- OMO, Sprint-4-Abschluss: Acceptance 7, Root Tests 247, Contract Tests 59, gesamt 313 bestanden.
- `hermes verify --json`: `ok: true`, Acceptance 7 von 7.
- Finaler Sprint-3-Spec-Review: `APPROVED`.
- Finaler Sprint-3-Quality-Review: `APPROVED`.
- Offene Sprint-3-Findings: P0 0, P1 0, P2 0, P3 0.
- Sprint-3-Checkpoint: `00_admin/checkpoints/2026-08-19-sprint-3/` mit 226 Datei-Hashes.
- AHD Step 0 bleibt 4 von 4 Dateien byte-identisch.
- Damaliger Entwicklungsbranch: `feature/e2e-operator-workflow-system`. Die damalige Sperre gegen Commit oder Push auf `master` wurde fuer die dokumentierte Repository-Konsolidierung durch Raphaels Freigabe und DEC-0031 superseded.
- Externer verifizierter Live-Snapshot: `C:\Users\offic\Documents\Projekte\Hermes\90_archive\project-snapshots\Heartweb-Claude-Desktop-SEO-Workflow\2026-08-19_20-26-39_-0400`.
- Sprint 4 Stage A: Integrationsvertraege und deterministische Notion-Graph-Validierung implementiert. Terminaler Spec Review `APPROVED`. Terminaler Quality Review `APPROVED`. Offene Findings: P0 0, P1 0, P2 0, P3 0.
- Sprint-4-Stage-A-Checkpoint: `00_admin/checkpoints/2026-08-19-sprint-4-stage-a/` mit 597 Datei-Hashes, 236 Tests je Runtime und 4 von 4 byte-identischen AHD-Step-0-Dateien.
- Feature-Branch-Checkpoint auf GitHub: `feature/e2e-operator-workflow-system`, Commit `a3b8ea1`. Lokaler und remote `master` bleiben unveraendert auf `5e78679`.
- Sprint 4 Stage A2 ist abgeschlossen. Logische Projektsessions, Context Packages, Workerprofile, LLM Run Request/Result, Session-Cache-Policy, Revision-Reruns und Fail-Fast Context Validation sind implementiert und freigegeben.
- Sprint 4 Stage B ist abgeschlossen. Local Workflow API, serverseitige Workspace Registry, Repository und append-only Event Store sind implementiert und freigegeben.
- Sprint 4 Stage C ist abgeschlossen. Notion- und n8n-Simulator, Multi-Tenant-Isolation, Replay, Konflikte, Recovery, Retry, DLQ und Tag-30/60/90-Pfade sind implementiert und freigegeben.
- Sprint 4 Stage D ist abgeschlossen. Der deterministische FastAPI-OpenAPI-Snapshot, generierte TypeScript-Typen und die lokale API-/Simulator-Integration sind implementiert und verifiziert.
- Stage-D-Fokus: 6 von 6 Tests auf Host und OMO. Full Suite: 313 von 313 Tests auf Host und OMO. TypeScript strict in OMO: Exit 0. `hermes verify --json`: `ok: true`.
- Sprint-4-Checkpoint: `00_admin/checkpoints/2026-08-20-sprint-4/` mit 983 Datei-Hashes, Testevidence, Reviewstatus und Branchzustand.
- Sprint 5 Package 1 ist abgeschlossen. Frontend-Grundgeruest, generierter API-Client, Project Dashboard, Workflow Timeline und Step Detail sind als explizite lokale Simulation vorhanden.
- Package-1-Evidence: finaler Lockfile-`npm ci` erfolgreich, npm Audit 0 Vulnerabilities, 11 von 11 UI-Tests, TypeScript und Vite-8-Production-Build gruen, OpenAPI-Codegen unveraendert, Browser-QA auf Desktop, Tablet und echter 390-Pixel-Mobile-Emulation bestanden.
- Sprint 5 Package 2 ist abgeschlossen. Artefaktvorschau, immutable Revision Diff, LLM Run-Historie, Context-Package-Zusammenfassung und disabled Revision-Run-Preview sind integriert.
- Package-2-Evidence: 16 von 16 UI-Tests, TypeScript und Vite-8-Production-Build gruen, npm Audit 0 Vulnerabilities, OpenAPI-Codegen unveraendert, Browser-QA auf Desktop und echter 390-Pixel-Mobile-Emulation bestanden.
- Sprint 5 Package 3 ist abgeschlossen. Taskqueue, Ticket Detail, Review Center, Integrationsstatus, Workflow Matrix und Baseline Comparison sind integriert.
- Package-3-Evidence: 23 von 23 UI-Tests, TypeScript und Vite-8-Production-Build gruen, npm Audit 0 Vulnerabilities, OpenAPI-Codegen unveraendert, Operations- und Presentation-Browser-QA auf Desktop und echter 390-Pixel-Mobile-Emulation bestanden.
- Sprint 5 Package 4 Backend ist implementiert: Intake, Provisioning, Context/LLM Runtime, immutable Artefakte, Revisionen, Gate/Approval/Release-Lifecycle, Recovery, Actions und neutraler Step-0-bis-4b-Flow. Backend-Verifikation meldete 347 Tests und aktuelle OpenAPI-/TypeScript-Typen vor dem Frontendumbau.
- Die abgelehnte englische `?mode=demo`-Kartenoberflaeche ist nicht mehr das Produkt. Die neue deutsche Arbeitsoberflaeche liegt unter `apps/operator-console/src/app/`.
- Sprint-5-Operational-Wiring-Report: `00_admin/audits/2026-08-19-e2e-demo/sprint-5/04_SPRINT5_OPERATIONAL_WIRING.md`.
- Aktueller Repository-Audit: `00_admin/audits/2026-08-21-repository-hygiene/REPOSITORY_HYGIENE_AND_AUTHORITY_AUDIT.md`.
- WIP-Sicherungsbranch: `wip/sprint5-operator-console-2026-08-21-0809`, Commit `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`. Lokaler Feature-HEAD bleibt fuer Sisyphus unveraendert.
- Feste Releasefolge ab dem Nacht-Checkpoint: M08 PQ-4 mit DIB-001 abschliessen, M09 route-basierter Production Release Audit und M10 erster kontrollierter lokaler Output. Die feste Hierarchie steht in `00_admin/MASTER_TASK_MATRIX.md`; dynamische Root-Todos sind nur Subtasks.
- DEC-0029-Produktionspfad ist als aktueller WIP fuer alle acht Steps implementiert: persistente Production Executions, exakte MCP-Toolfreigabe und Fortsetzung desselben Hermes-Runs, revisiongebundene Agent Evidence, kanonische Single- und Multi-Output-Transaktionen, Step-1-Crawl-Supporting-Artifact, realer AgentSEO-Dispatcher fuer 1B/2/4A, Step-3-Solver, technischer side-effect-freier Retry sowie versionierter fachlicher Steering-Rerun. OpenAPI-Codegen, Repository-Index-Check, Python-Syntaxpruefung, Console-Produktionsbuild und statischer Abschlussabgleich sind gruen. Der Funktions- und E2E-Stand bleibt bis zu Raphaels manuellem Operatorlauf `unverified`. Console, Gateway, Runtime und neue Provideroperationen wurden waehrend der Implementierung nicht gestartet.

### Aktive Risiken und externe Voraussetzungen

1. Step 2 des spaeteren AHD-Livelaufs benoetigt realen, geo-korrekten Providerzugang. Keine Ersatzwerte.
2. Der reale AHD Crawl 005 besitzt eine Resource-404, die sichtbar geroutet und vor Production aufgeloest werden muss.
3. Reale Notion- und n8n-Verbindungen sind noch nicht konfiguriert. Sprint 4 baut versionierte lokale Simulatoren mit denselben Commands, Events und Projektionen.
4. Der DEC-0029-Pfad ist implementiert, build-gruen und fuer Step 0 real ueber die isolierte `heartweb-runtime` ausgefuehrt. Funktional endverifiziert ist er erst nach der sichtbaren Human-Freigabe, der realen Step-1-Produktion und dem lesbaren revisionsfaehigen Ergebnis. Crawl-, Provider- und Bundleadapter bleiben Werkzeuge der Step-Agenten und nicht deren Ersatz.
5. Der bestaetigte Performance-Zyklus fuer Notion, n8n und Step 3b ist Tag 30, 60 und 90.
6. Die releasekritische ADR-011-Restauration fuer Step 4a und Step 4b ist in Prompts, ausfuehrbaren Schemas, Validatoren, Renderern, Tool Policies und Gates umgesetzt und direkt verifiziert. Vollstaendige reale GEO-Produktionsqualitaet fuer Copywriter- und Developer-Pakete bleibt bis zu einem kontrollierten Real-Output und Human Review unbewiesen.
7. Kanonischer Sammelpunkt fuer neue Probleme, Verbesserungen, UI-Feedback und spaetere Integrationsarbeit ist `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`. Das Erfassen eines Punkts autorisiert keine sofortige Umsetzung. Der Backlog wird erst nach stabiler Basis und ausdruecklicher Freigabe in einem Integrations-Sprint abgearbeitet.
8. Der Repository-Hygiene-Audit identifiziert stale Dependency-/PID-Artefakte, einen exakten Planbild-Duplikat, produktiv unerreichbaren Demo-UI-Code, Legacy-Providervertraege und veraltete Dokumentation. Nichts davon wird waehrend des aktiven Browser-/Delivery-Gates destruktiv bereinigt.
9. Die releasekritischen Prompt-Paritaetsluecken in 1B, 1C, Step 2/3 und 4A/4B sind auf der DEC-0029-Architektur restauriert und direkt verifiziert. Step 3B und die vollstaendige Real-Output-Paritaet bleiben Post-Release; fuer den initialen Pfad ersetzt der Contractnachweis nicht die ausstehende reale Ergebnisabnahme.
10. DEC-0024 setzt eine verbindliche Production-first Cut-Line. Reine Mobile-Komfortprobleme, Live-Notion, Live-n8n, Voll-Dokumentation, Repository-Cleanup, breite Archetypen- und Praesentationsarbeit blockieren den ersten lokalen Production-Run nicht.
11. DEC-0025 begrenzt die Integrationslogik: Core-interne Tasks existieren nur waehrend Step 0 bis Step 4B. Das freigegebene Delivery-Paket erzeugt danach Notion-eigene Umsetzungsaufgaben ohne Task-Callbacks, Resume, Gate- oder Revisionswirkung. Der einzige geplante Post-Handoff-Loop ist der Performance-Abgleich an Tag 30, 60 und 90.

1. **GEO-Architektur-Spezifikation (`docs/07-geo-architecture-specification.md`):**
   - Vollstaendige Dokumentation des GEO-Erweiterungskonzepts (Selection vs. Absorption, Query Fan-Out, Evidence Containers, Schema.org about/mentions, Solver GEO-Gewichte).

2. **Multi-Agent Coding Team Setup (OpenCode Container Konfiguration):**
   - Persistente Modell- und Agenten-Rollen fuer die Sprint-Umsetzung definieren.

3. **Vorbereitung auf Meeting mit Max (Automatisierungsagentur):**
   - Abstimmung der Schnittstellen fuer Notion-Datenbanken und Task-Delegation.

4. **Pilot-Projekt nach Erhalt der Kundenbriefings von Jesse:**
   - Testlauf der Prompts 0 bis 4b unter realen Bedingungen.

---

## 4. Verbindliche Arbeitsregeln

1. Autorenschaft immer Raphael Rechberger.
2. Keine Gedankenstriche verwenden. Nur Bindestriche (-), Doppelpunkte oder klare Satzstrukturen.
3. Strikte Fail-Fast-Doktrin (keine Schaetzwerte, harter Stopp bei API- oder Datenfehlern).
4. Strikte Trennung zwischen Framework-Library (`Heartweb-Claude-Desktop-SEO-Workflow`) und individuellem Kunden-Workspace (`Heartweb\Kunden\<slug>\`).
5. Jedes Search Deployment bindet vor Step 0 Markt, Land, Provider Target, Provider-Location-Code, Sprache, Locale, Regionen und bestaetigte Wochenkapazitaet. Providerdaten laufen ausschliesslich ueber Provider Gateway. Im aktuellen DEC-0029-Produktionspfad ist AgentSEO fuer Step 1B, Step 2 und Step 4A explizit gebunden; DataForSEO ist kein stiller Fallback. Keine stillen Defaults oder Ersatzwerte.
