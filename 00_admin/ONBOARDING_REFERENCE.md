# Heartweb onboarding reference

**Author:** Raphael Rechberger
**Lifecycle:** generated onboarding view
**Source commit:** `597eb0a7c68cecceaff26249cec5f3e233f16a65`
**Generator version:** `1.1.0`
**Registry version:** `1.1.0`
**Inventory records:** 333

> This file is a deterministic generated onboarding view. It never overrides `00_admin/PROJECT_STATE.md`, active records in `00_admin/DECISIONS.md`, registered standards, contracts or Evidence. Every embedded source block identifies its canonical path, lifecycle, authority and raw SHA-256. Any drift makes `python scripts/build_repository_index.py --check` fail.

## 1. Snapshot identity and authority order

Authority is resolved before semantic similarity. Latest explicit Raphael instruction wins, followed by Project State, active Decisions and the ordered repository authorities below.

1. `00_admin/PROJECT_STATE.md`
2. `00_admin/DECISIONS.md`
3. `active plans`
4. `standards and contracts`
5. `current runtime and tests`
6. `current integration documents`
7. `supporting research`
8. `historical and audit evidence`

Conflict rule: a lower authority never silently overwrites a higher authority. Historical, superseded and Evidence records are opt-in only.

## 2. Product purpose and hard boundaries

Heartweb is a client-neutral local SEO and GEO production system for one internal operator. It turns verified client inputs into strategy, architecture, keyword Evidence, roadmaps, professional Copywriter briefings, Developer specifications and deterministic handoff packages.

- The system does not write final editorial copy. Human Heartweb Copywriters do.
- The German Single-Admin Console is for the operator only.
- Heartweb Core alone owns canonical workflow state, revisions, gates, approvals and releases.
- External providers are reached only through versioned Provider Gateway operations. Missing data stops fail-closed.
- Customer facts, claims, regions, Evidence and design stay in isolated customer workspaces, not shared framework logic.
- Delivery is derived, deterministic and read-only. It cannot mutate workflow authority.
- Repository consolidation into `master` is not Production Acceptance.

## 3. Truthful current status and next gate

The following excerpt is copied from the canonical Project State in this snapshot:

````text
**Status:** Production-first Completion in Ausfuehrung. Der DEC-0029-Produktionspfad und die DEC-0030-Multi-Location-Bindung sind implementiert. Im realen CL-Projekt ist Step 0 mit Manifest V2 Revision 3, Project V2 1.3.0, Deployment `dep-cl-performance-de`, Provider Target `agentseo-de-country`, `DE / 2276 / de`, Region Deutschland und 10 operatorbestaetigten Wochenstunden freigegeben, abgeschlossen und released. Step 1 Run `run-next-7f7e2b778f4521b9` steht auf `in_progress`; fuer ihn existieren noch keine Production Execution, keine Agent Evidence und kein LLM Run. M10, PT-03 und PT-11 bleiben bis zur echten Step-1-Produktion, dem kompletten weiteren Workflow, Human Review und kontrollierten Kundenoutput offen. DEC-0031 autorisiert parallel die vollstaendige Repository-Konsolidierung nach `master`, ohne daraus Production Acceptance abzuleiten.
### Aktueller Konsolidierungs- und Produktionscheckpoint vom 26. August 2026

- DEC-0031 autorisiert den vollstaendigen aktuellen Repository-Stand als neuen `master`-Basisstand. DEC-0032 autorisiert die deterministische `00_admin/ONBOARDING_REFERENCE.md`. Beides ist Repositorykonsolidierung und kein Production-Acceptance-Nachweis.
- Vor der Git-Konsolidierung wurde ein externer Recovery-Snapshot mit 1.185 relevanten Dateien, vollstaendigem Git-Bundle aller Refs, bytegeprueftem Working Tree und redigierter Sensitive-File-Pruefung erstellt. Nachweis: `C:\Users\offic\Documents\Projekte\Hermes\90_archive\project-snapshots\Heartweb-Claude-Desktop-SEO-Workflow\2026-08-26_06-46-51_-0400-pre-master-consolidation\SNAPSHOT_OK.txt`.
- Der M08-Snapshot-Commit `568bb497e57af4f7ec6dc8a13438681bbf423a55` wurde ueber alle 635 geaenderten Pfade abgeglichen: 424 bytegleich, 140 in spaeterer Commit-Historie vorhanden, 71 im aktuellen post-M08-Worktree weiterentwickelt, 0 fehlend, 0 ungeklaert. Authority: `00_admin/audits/2026-08-26-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`.
- Reales CL-Projekt: Step 0 Revision 3 ist freigegeben, abgeschlossen und released. Step 1 Run `run-next-7f7e2b778f4521b9` ist `in_progress`. Es existieren noch keine Step-1-Production-Execution, keine Agent Evidence und kein LLM Run. Der Produktionsworkflow bleibt waehrend der Repositorykonsolidierung bewusst eingefroren.
- Gateway und Operator Console sind fuer den Freeze gestoppt. Der entfernte stale PID-Record war ausschliesslich lokale Runtime-Metadatei. Er enthielt keinen Repository- oder Kundenquellstand.
- Die letzte Git-Connectivity-Pruefung bestand fuer HEAD und Objektgraph. Die abschliessende affected-closure Verifikation, der Build, Secret Scan, Repository-Index-Check und `hermes verify --json` werden nach Abschluss aller Source-Reconciliations frisch ausgefuehrt.
- Exakte Live-Branches, Remote-SHAs und Worktrees werden nicht in diesem Dokument gecacht. Sie muessen vor jeder Git-Mutation direkt aus Git gelesen und nach jeder Mutation erneut verifiziert werden.
````

The next Product gate remains M10: produce, review, approve and deliver the remaining real route without estimating missing provider data or implying unverified quality.

## 4. Workflow and Step 3B boundary

Initial production route:

`0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery`

Step 3B is not an initial-route Step agent. It runs only after publication at day 30, day 60 and day 90 when verified real performance data exists. It produces a versioned adjustment proposal and never mutates the released original plan.

## 5. Architecture map

| Component | Binding responsibility | Forbidden responsibility |
|---|---|---|
| Core | Canonical state, artifacts, revisions, Evidence, gates, approvals and releases | Provider calls and post-handoff staff management |
| Operator Console | Typed commands and canonical German read models | Duplicating workflow rules or bypassing gates |
| Provider Gateway | Versioned, geo-bound provider operations and persisted Evidence | Guessing missing values or exposing credentials |
| Hermes Gateway | Isolated specialized Step-agent execution and controlled Heartweb tools | Canonical state mutation or credential ownership in prompts |
| Delivery | Deterministic checkpoint and final packages, ZIP and manual Notion import | Approval, artifact mutation or workflow transition |
| Notion | Human implementation tasks after approved Delivery | Calling back into Core for ordinary staff task changes |
| n8n | Future orchestration, transport, Notion creation and scheduled Step 3B trigger | State authority or daily staff-task monitoring |

## 6. Capability evidence levels

| State | Capabilities |
|---|---|
| Implemented | V2 Core and Transition Service; revision, gate, approval and release services; Provider Gateway; specialized Hermes Step agents; German Console; deterministic Delivery and diagnostics |
| Verified locally | Registry and hash bindings; focused Runtime and tool-scope closure; Step 0 release for the active controlled project; local Delivery and diagnostic contract evidence |
| Unverified | Real Step 1 through Step 4B provider-backed output quality; complete active-project ZIP and Notion handoff; Production acceptance |
| Planned before M10 closes | Produce, review, gate and deliver the remaining controlled route with no open P0/P1 |
| Deferred after M10 | Live Notion adapter, n8n orchestration, Step 3B operations, public deployment, broad mobile polish and wider archetypes |
| Absent | Production deployment, live Step-3B performance dataset and an approved complete real Golden Path |

Evidence labels remain separate: unit or contract test, local service integration, deterministic fixture E2E, live-provider smoke, real-project Golden Path, external Notion or n8n E2E and Production acceptance.

## 7. Git, authorship, safety, separation and testing rules

- Raphael Rechberger is the sole author of project documents, deliverables and commits.
- DEC-0031 authorizes this bounded repository consolidation, normal push, reachability-proven branch cleanup and fresh-clone continuation. No force-push is the default.
- Released artifacts and accepted prompt meanings remain immutable. Edits create new versions or revisions.
- Never commit customer workspaces, credentials, raw authorization headers, local `.env` files or sensitive recovery exports.
- Never estimate missing provider metrics or fabricate claims, locations, approvals, Evidence, identities or completion state.
- Run only the affected dependency closure required by `standards/testing/PROTOTYPE_TEST_POLICY.md`; do not restart broad matrices after a bounded failure.
- Never use Em Dash or En Dash characters.

## 8. Complete onboarding-critical source blocks

Each block below contains the complete canonical source text with LF line endings and trailing line whitespace normalized for Git safety. The heading SHA-256 is calculated from these canonical text bytes; binary document bytes remain unchanged.

### Source: [`00_admin/PROJECT_STATE.md`](../00_admin/PROJECT_STATE.md)

- Lifecycle: `current_authority`
- Authority: 100
- SHA-256: `695e27bb02b43bd2f1479f471671389b4a6975b634ba11edd4d56e485fae032b`

````text
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
````

### Source: [`00_admin/DECISIONS.md`](../00_admin/DECISIONS.md)

- Lifecycle: `current_authority`
- Authority: 98
- SHA-256: `a307cfada0297bffa92bc5f9c689912138c08798c6506000317ebd6e0de26e07`

````text
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

- Status: superseded
- Date: 2026-08-21
- Owner/source: Raphael Rechberger
- Context: `master`, `feature/e2e-operator-workflow-system` und der WIP-Checkpoint bilden eine lineare Historie ohne Divergenz. Browser-QA, Sprint 5E und Final-Audit sind noch offen.
- Decision: Vor dem vollstaendigen Final-Gate wird nichts nach `master` gemergt. Nach bestandenem Final-Gate wird der finale Arbeitsstand als Nachfolger des WIP-Checkpoints committed, der Feature-Branch auf diesen finalen Commit gebracht und verifiziert. Anschliessend wird `master` per Fast-Forward auf den finalen Feature-Stand gesetzt. WIP- und Feature-Hilfsbranches werden erst nach verifiziertem Remote-SHA und ausdruecklicher Abschlusskontrolle geloescht.
- Rationale: Die lineare Historie erlaubt eine konfliktfreie Konsolidierung, ohne einen unfertigen Zwischenstand als offiziellen Hauptbranch zu veroeffentlichen oder Sisyphus waehrend der aktiven Arbeit zu stoeren.
- Supersedes: none
- Superseded by: DEC-0031
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

- Status: partially superseded by DEC-0029; Credential-, Core-Authority-, Modellpolicy- und Fail-Fast-Grenzen bleiben active
- Date: 2026-08-23
- Owner/source: Raphael Rechberger
- Context: Die bestehende Heartweb Runtime bindet Context Package, Prompt, Worker Profile, Provider, Modell, Toolpolicy, Outputvertrag und Resultat, fuehrt aber vor M10 noch keinen echten Modellcall aus. Raphael moechte den vorhandenen OpenAI-Codex-OAuth-Zugang ueber Hermes nutzen, ohne OAuth-Tokens in Heartweb einzubauen oder Heartweb von Hermes als einziger Produktionsroute abhaengig zu machen.
- Decision: M08L wird nach dem stabilen M08-Snapshot und vor M09 ausgefuehrt. Root Sisyphus implementiert die Heartweb-Core-Seite mit providerneutralem Execution Backend, Hermes-Adapter, Persistenz, Replay, Recovery und fokussierten Tests. Hermes verantwortet die Hermes-seitige Capability-Probe, das isolierte Profil `heartweb-runtime`, die Hermes-verwaltete Shared-OAuth-Pool-Grenze, die versionierten Modell- und Reasoning-Profile, den neutralen realen Gateway-Nachweis und die unabhaengige Abnahme. Der bestehende OpenAI-Codex-OAuth-Pool bleibt in Hermes und wird vom Profil nur ueber den read-only Provider-Fallback aufgeloest. OAuth-Tokens werden nicht kopiert und nicht an Heartweb, Sisyphus oder Worker uebermittelt. Das Profil verwendet ein eigenes eingebautes `MEMORY.md`, kein `USER.md` und keinen externen Memory-Provider. Heartweb kennt nur einen lokal injizierten API-Server-Key und nicht geheime Provider-/Modellmetadaten. Hermes liefert nur einen Artefaktkandidaten und darf keinen Workflowstatus, kein Gate und keine Revision verbindlich setzen.
- Production-first amendment: Vor M09 wird nur ein duennes Hermes-Runs-Backend gebaut, das die bestehenden Context-, Request-, Result-, Validierungs-, Artefakt-, Idempotency-, Persistenz- und Diagnosegrenzen wiederverwendet. Allgemeine Backend-Registry, separater Execution-Record-Store, direkte Multi-Provider-Adapter, Delegation Contracts, Subagent-Orchestrierung und breite Benchmark-Infrastruktur sind Post-M10. Ein neues Schema oder eine neue Persistenzfamilie ist vor M09 nur zulaessig, wenn ein konkret nachgewiesenes Pflichtfeld durch keine bestehende Authority abbildbar ist.
- Model policy: `gpt-5.6-sol` mit `high` ist fuer 1B, 4A und kritische Schlussreviews vorgesehen, nicht fuer jeden Step. Strukturierte oder deterministisch gestuetzte Steps verwenden ein validiertes schnelleres oder ausgeglichenes Profil mit `low` oder `medium`. Fehlende Modelle oder OAuth-Verfuegbarkeit stoppen fail-fast; kein stiller Provider-, Modell- oder Reasoning-Fallback.
- Rationale: Der erste reale lokale Output kann den vorhandenen OAuth-Zugang sicher und reproduzierbar nutzen, ohne vorab eine allgemeine LLM-Plattform zu bauen. Die Heartweb-Authority-Grenze bleibt erhalten; spaetere direkte offizielle API-Adapter und allgemeine Routinginfrastruktur werden erst aus realer Nutzung begruendet.
- Supersedes: none
- Superseded by: DEC-0029 fuer die Aussage, Heartweb solle Hermes nicht als regulaere Produktionsroute verwenden, sowie fuer die Post-M10-Verschiebung von Delegation und Subagent-Orchestrierung
- Evidence: Raphael-Entscheidung vom 23. August 2026; `.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md`; verifizierter M08-WIP-Snapshot `568bb497e57af4f7ec6dc8a13438681bbf423a55`
- Acceptance: Realer neutraler Step-0-Lauf PASS mit schema-validem Manifest, persistiertem Context Package und LLM Result, Provider Run ID, Modell- und Tokenmetadaten sowie null Toolcalls. `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.
- Impacted files/areas: Runtime Contracts, Worker Profiles, LLM Gateway, Operator API, Runtime Persistence, Recovery, Hermes Profile, OAuth-Grenze, Modellrouting, M09, M10

## DEC-0029: Hermes Gateway ist die agentische Produktionsschicht fuer jeden Workflow-Schritt

- Status: active
- Date: 2026-08-24
- Owner/source: Raphael Rechberger
- Context: Der duenne M08L-Nachweis bewies nur den Transport eines realen Step-0-Modellcalls mit null Toolcalls. Die manuelle CL-Performance-Abnahme zeigte, dass ein Modellcall ohne vollstaendige agentische Tool-, Provider-, Artefakt- und Fortsetzungsbedienung nicht dem beabsichtigten Produktionssystem entspricht. Raphael bestaetigt, dass Hermes Gateway gewaehlt wurde, damit spezialisierte AI-Worker die fachliche Arbeit jedes Schritts ausfuehren, Providerdaten verarbeiten und kontrollierte Provideroperationen selbst anfordern koennen.
- Decision: Die regulaere Produktion der Schritte `0`, `1`, `1b`, `1c`, `2`, `3`, `4a` und `4b` laeuft ueber das isolierte Hermes-Profil `heartweb-runtime`. Jeder Schritt besitzt einen versionierten spezialisierten Agentenvertrag aus Context Package, registriertem Prompt, Worker Profile, Modell- und Reasoning-Policy, erlaubten Toolsets, Kosten- und Bestaetigungspolitik, erwartetem Outputvertrag und maximalen Agent- beziehungsweise Toolrunden. Ein Step-Run darf innerhalb dieser Grenzen spezialisierte Hermes-Subagents fuer Recherche, Verarbeitung, Synthese oder fachliche Gegenpruefung delegieren. Dies sind logische Workerrollen in einer Runtime und keine acht separaten Gateway-Dienste.
- Provider rule: Ein Step-Agent darf Providerdaten als validierten Context erhalten oder eine erlaubte Provideroperation ueber ein typisiertes Heartweb-Tool anfordern. Das Tool routet serverseitig durch den Provider Gateway, bindet Markt, Location Code, Sprache, Kostenfreigabe und Request-Identitaet und persistiert rohe Antwort, Hash und Provenienz als Evidence. Der Agent erhaelt keine Provider-Credentials und ruft keine externe Provider-API an der Heartweb-Grenze vorbei auf.
- Provider usage amendment: Fuer den DEC-0029-Produktionspfad ist AgentSEO der explizit gebundene Provider-Gateway-Adapter fuer die kontrollierten Operationen in Step 1B, Step 2 und Step 4A. Dies ersetzt fuer diesen Pfad die aeltere DataForSEO-Primaerannahme; DataForSEO bleibt eine spaetere alternative Capability und ist kein stiller Fallback. AgentSEO rechnet ueber Provider-Credits und meldet im realen Jobstatus weder per-Call-Credits noch USD-Istkosten. Heartweb erfindet deshalb keinen USD-Wert. Die Operatorfreigabe bindet exakte Operation, Parameter, Requesthash, Calllimit und Itemlimit. Die Tool Policy kennzeichnet dies als `provider_credits_unreported`. Request und Response speichern `billing_unit=credits` und `provider_reported=false`; rohe Providerjobs und normalisierte Exchanges bleiben gehasht erhalten.
- Retry and revision amendment: Ein technischer Retry ist nur vor jeder Toolinteraction, Evidence- oder Artefaktpersistenz erlaubt. Er erzeugt eine neue Production Execution mit byte-identischem Context Package und unveraendertem Agentvertrag. Ein fachlicher Rerun ist davon getrennt: Er bindet das abgelehnte Artefakt, Findings, unveraenderliche Grenzen und Operator-Steering in versionierten Records, laesst die Transition Service Authority `awaiting_gate -> in_progress` ausfuehren und erzeugt danach eine neue Artefaktrevision. Alte Approvals bleiben hashgebunden und koennen fuer die neue Revision nicht gelten.
- AI boundary: AI ist in jedem fachlich generativen oder interpretativen Produktionsschritt aktiv. Deterministische Funktionen wie Hashing, Schema- und Identity-Validierung, Evidence-Normalisierung, Zustandsuebergang, Freigabe, Replay und ZIP-Erzeugung bleiben bewusst nicht-agentisch. Deterministische Provideradapter oder Assembler sind Werkzeuge des Step-Agenten und kein Ersatz fuer ihn.
- Authority: Heartweb Core bleibt alleinige Authority fuer kanonischen Workflowstatus, Artefakte, Revisionen, Evidence, Gates, Freigaben und Releases. Hermes erzeugt und prueft Kandidaten, fuehrt erlaubte Toolschleifen aus und liefert strukturierte Run-Evidence. Hermes darf keinen kanonischen Zustand, kein Human Gate und keine Releasefreigabe selbst setzen.
- Runtime ownership: Die Console startet das Gateway nicht automatisch. Eine vom Operator bestaetigte Produktionsaktion setzt eine erreichbare, bewusst betriebene `heartweb-runtime` voraus. Eine nicht erreichbare Runtime, fehlende Capability, Authentifizierungsfehler, Providerfehler, nicht gebundene Providernutzung oder Interaktionsbedarf stoppen fail-fast mit strukturiertem Fehler und konkreter Behebung. Providerseitig nicht berichtete Einzelcredits werden explizit als nicht berichtet gespeichert. Es gibt keinen stillen Modell-, Provider-, Tool- oder Fixture-Fallback.
- Consequence: Ein einfacher Step-0-Modellcall mit null Toolcalls ist nur Transport-Evidence und kein Nachweis der Zielarchitektur. Der Produktionspfad gilt erst dann als vollstaendig, wenn die spezialisierte Hermes-Ausfuehrung, benoetigten Provider- beziehungsweise Tooloperationen, Outputpersistenz, Validierung, Human Review und Folgeschrittaktivierung fuer alle acht Schritte bedienbar sind.
- Supersedes: DEC-0028 Production-first amendment zur Post-M10-Verschiebung von Delegation und Subagent-Orchestrierung sowie die Aussage, Heartweb solle Hermes nicht als regulaere Produktionsroute verwenden. Die isolierte Profil-, OAuth-, Core-Authority-, Modellpolicy- und Fail-Fast-Grenze aus DEC-0028 bleibt bestehen.
- Superseded by: none
- Evidence: Raphael-Instruktion vom 24. August 2026; Hermes API Server und Subagent Delegation laut `https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server` und `https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation`
- Impacted files/areas: Current Production Architecture, Operator API, Hermes Runs Adapter, Worker Profiles, Prompt Registry, Provider Gateway, Tool Contracts, Context Packages, Runtime Persistence, Diagnostic Trace, Operator Console, M09 und M10

## DEC-0030: Provider-Standorte werden vor Step 0 pro Search Deployment gebunden

- Status: active
- Date: 2026-08-25
- Owner/source: Raphael Rechberger
- Context: Der reale CL-Performance-Test zeigte einen unzulaessigen Widerspruch: Project V2 enthielt fuer das aktive Deployment keinen verifizierten Provider-Location-Code, waehrend Step 0 den Wert `DE / 2276 / de` spaeter aus einer Laendertabelle einsetzte. Eine CL-spezifische Korrektur oder ein globaler Deutschland-Default waere nicht mandantenneutral und nicht multi-location-faehig.
- Decision: Das angenommene Briefing erzeugt vor Step 0 alle Search Deployments mit Markt, Land, Sprache, Locale, SEO Operating Model, Zielregionen, physischen Standort- und Leistungsgebietsreferenzen sowie einer exakten Provider-Target-ID. Die Provider Location Registry ist eine eigene versionierte Authority und nicht Teil der Market Registry. Jedes aktive Deployment muss einen verifizierten und zum Land, zur Sprache und zum Operating Model passenden Provider Target Record besitzen. Mehrere physische Orte oder Service Areas duerfen ein Deployment teilen, wenn sie denselben Provider Research Target verwenden. Unterschiedliche Provider Targets erfordern getrennte Deployments. Der initiale Produktionslauf bindet genau das aktive Primary Deployment. Fehlende, mehrdeutige oder unverifizierte Targets stoppen vor Step 0.
- Manifest rule: Step 0 verwendet keinen Country Lookup. Manifest V2 kopiert das vollstaendige rungebundene Deployment, Source Binding, Provider Target und alle Zielregionen exakt aus Project V2 und dem Preflight. Cross-Binding prueft Deployment-Hash, Target-ID, Provider-Code, Land, Sprache, Locale und Regionen. GATE-0 bleibt eine separate menschliche, artefakt- und hashgebundene Entscheidung.
- Runtime rule: Jeder Run traegt `deployment_id`. Alle Heartweb Provider Tools lehnen ein anderes Deployment ab. Eine Aenderung an akzeptiertem Intake oder Project V2 erzeugt eine neue gehashte Logical Project Session, archiviert den Vorgaenger und verhindert stale Context Packages. Beim fachlichen Rerun ist das Gate des abgelehnten aktuellen Artefakts eine aktive Finding-Quelle, nicht eine historische Quelle.
- Capacity rule: Project V2 bindet vor Step 0 eine ausdruecklich bestaetigte Wochenkapazitaet mit Minimum, Maximum, Quelle, Operator und Zeitpunkt. Fehlt sie im Eingabeportfolio, erzeugt Intake einen typisierten Missing Input. Bei bereits angenommenen Projekten kann der Operator denselben Wert ueber Preview und Confirm in der Console nachtragen. Die Aenderung erzeugt eine neue Project-V2- und Logical-Session-Revision. Step 0 und Step 3 verwenden denselben Record. Defaults und provisional Schaetzwerte sind verboten.
- Legacy rule: `standards/location-codes.json` und `standards/manifest.schema.json` bleiben fuer reproduzierbare Legacy Records erhalten, sind aber nicht der aktive Produktionsvertrag. Der aktive Pfad verwendet `standards/domain/provider-location-registry.json` und `standards/manifest-v2.schema.json`.
- Rationale: Providergeografie ist deploymentbezogen. Markt, physischer Standort, Service Area und Provider Research Target haben unterschiedliche Bedeutungen und duerfen weder aus einem Land noch aus einem Kundenbeispiel geraten werden.
- Supersedes: ADR-008 und alle aktiven Laufzeitannahmen, die einen Provider-Code erst in Step 0 aus `country` ableiten. Historische Records bleiben unveraendert.
- Superseded by: none
- Evidence: Raphael-Korrektur vom 25. August 2026; realer CL-Performance-Workflowtest; `standards/domain/provider-location-registry.json`; `standards/manifest-v2.schema.json`; `services/domain_contract/provider_locations.py`; `services/agent_gateway/kickoff_preflight.py`
- Impacted files/areas: Intake Project Generator, Project V2, Search Deployment Contract, Provider Location Registry, Logical Project Session, Run Envelope, Step-0-Prompt und Manifest, Provider Gateway Tools, Runtime Revision Sources, Operator Console, CL-Performance-Testprojekt

## DEC-0031: Der vollstaendige aktuelle Repository-Stand wird jetzt in master konsolidiert

- Status: active
- Date: 2026-08-26
- Owner/source: Raphael Rechberger
- Context: Der aktuelle produktive Entwicklungsstand liegt als umfangreicher verifizierter Working-Tree-Delta auf `feature/e2e-operator-workflow-system`. Mehrere alte Hilfs- und WIP-Branches erschweren die Orientierung. Raphael verlangt einen eigenstaendigen, vollstaendigen und referenzierten `master` als einzigen konsolidierten Repository-Basisstand und danach genau einen neuen Fortsetzungsbranch.
- Decision: Der aktuelle Code-, Contract-, Prompt-, Test-, Evidence- und Dokumentationsstand wird vollstaendig klassifiziert, authority-konform reconciliiert, fokussiert verifiziert und in nachvollziehbaren Commits auf dem Feature-Branch gesichert. Der einzigartige M08-Snapshot wird nach pfadweisem Nullverlustnachweis als no-tree-change Graph-Merge erreichbar gemacht. Danach wird `master` ausschliesslich per Fast-Forward auf den finalen verifizierten Feature-Stand gesetzt und remote readback-verifiziert. Alte Nebenbranches und Worktrees werden nur nach einzeln bestandenem Ancestor-Nachweis normal geloescht. Anschliessend ersetzt ein verifizierter Fresh Clone das Repository am unveraenderten kanonischen Pfad und `feature/production-workflow-continuation` wird vom exakten konsolidierten `master` erstellt.
- Truth boundary: Die Repository-Konsolidierung ist kein Production-Acceptance-Gate. Step 0 des realen CL-Projekts ist freigegeben, abgeschlossen und released. Step 1 bleibt bis zur echten Hermes-Produktion, Evidence, Human Review und Freigabe `in_progress`. PT-03, PT-11 und M10 bleiben offen, solange ihre reale Evidence fehlt.
- Preservation rule: Historische, superseded und Evidence-Quellen bleiben erhalten und lifecycle-gekennzeichnet. Environment-Dateien, rohe Session-Recovery-Dateien und Kundenworkspaces bleiben ausserhalb von Git. Kein Force Push, kein History Rewrite und keine Branchloeschung ohne Reachability-Nachweis.
- Rationale: Ein einziger konsolidierter Hauptbranch reduziert Drift und Onboardingfehler, ohne unfertige Produktionsarbeit als abgeschlossen darzustellen oder historische Nachweise zu verlieren.
- Supersedes: DEC-0022 ausschliesslich hinsichtlich des Zeitpunkts der Master-Konsolidierung
- Superseded by: none
- Evidence: Raphael-Freigaben vom 26. August 2026; `.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md`; `00_admin/audits/2026-08-26-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`
- Impacted files/areas: gesamtes Repository, Dokumentautoritaet, Prompt- und Agentregistries, GitHub-Branches, Worktrees, Fresh Clone, Session-Onboarding

## DEC-0032: Eine deterministische Onboarding-Referenz buendelt den Repository-Einstieg

- Status: active
- Date: 2026-08-26
- Owner/source: Raphael Rechberger
- Context: Project State, Decisions, Standards, Plaene, Prompts, Agentvertraege, Indizes und Evidence besitzen bewusst getrennte Autoritaeten. Neue Sessions benoetigen trotzdem einen vollstaendigen Single-Entry-Point, ohne dass eine manuell gepflegte Kopie erneut driftet.
- Decision: `00_admin/ONBOARDING_REFERENCE.md` wird deterministisch aus der kanonischen Dokumentregistry und den aktuellen Default-Retrieval-Quellen erzeugt. Die Datei enthaelt Authority- und Konfliktregeln, Produkt- und Architekturgrenzen, den wahrheitsgemaessen Status, Workflow und Step-3B-Grenze, Prompt- und Agentkataloge, lokale Betriebs- und Verifikationspfade sowie eine vollstaendige Inventarzeile fuer jeden Registry-Eintrag. Onboarding-kritische Current-Authority-Quellen werden mit Pfad, Lifecycle, Authority Level und SHA-256 als identifizierte Source Blocks eingebettet. Audit- und Evidence-Rohtexte bleiben an ihren kanonischen Pfaden und werden vollstaendig inventarisiert statt dupliziert.
- Source-of-Truth rule: Die generierte Referenz ist eine Navigation und Momentaufnahme. Sie ueberschreibt niemals `PROJECT_STATE.md`, aktive Decisions oder den jeweiligen Quellvertrag. Generator-Drift muss den Repository-Index-Check fehlschlagen lassen.
- Rationale: Eine deterministische Gesamtansicht ermoeglicht vollstaendiges Onboarding und RAG-Routing, ohne Redundanz oder eine konkurrierende manuelle Autoritaet zu erzeugen.
- Supersedes: none
- Superseded by: none
- Evidence: Raphael-Freigabe vom 26. August 2026; `.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md`
- Impacted files/areas: Repository-Index-Generator, Document Registry, Session Bootstrap, README, AGENTS, CLAUDE, docs- und plan-Indizes, neue Sessions und Agenten
````

### Source: [`00_admin/MASTER_TASK_MATRIX.md`](../00_admin/MASTER_TASK_MATRIX.md)

- Lifecycle: `current_authority`
- Authority: 99
- SHA-256: `3daea023ddba88d1a01f03cc5a1452f063fca268d49b5292f8c1c90450ebddb2`

````text
# Heartweb Master Task Matrix

**Author:** Raphael Rechberger
**Status:** Current project task router
**Updated:** 2026-08-26
**Machine source:** `00_admin/MASTER_TASK_MATRIX.json`
**Binding test policy:** `standards/testing/PROTOTYPE_TEST_POLICY.md`

## 1. What this file solves

This is the stable project hierarchy from the current implementation to the first controlled local production output.

The canonical product roadmap remains `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`. It contains Sprint 0 through Sprint 11. The inserted Sprint 5E creates 13 actual execution stages. The M01 through M10 list below is only a Production-first status overlay and does not replace or renumber the canonical Sprint roadmap.

Root-Sisyphus may split one Main Task into more or fewer internal todos. Those internal counts are execution detail and may change. They do not change the fixed project denominator.

The stable pre-release progress is always reported as:

```text
completed Main Tasks / 10 fixed Main Tasks
current Main Task
completed current subtasks / current subtask total
active subtask
next Main Task
```

New defects are added under the affected Main Task. They do not create a new overall denominator.

## 1A. Canonical 13-stage Sprint roadmap

| Stage | Canonical Sprint | Scope | Status |
|---|---|---|---|
| 1 | Sprint 0 | Freeze candidate baseline | completed |
| 2 | Sprint 1 | Stabilize runtime candidates | completed |
| 3 | Sprint 2 | Operator, ticket and event contracts | completed |
| 4 | Sprint 3 | V2 output contracts and prompt migration | completed |
| 5 | Sprint 4 | Local Workflow API and simulators | completed |
| 6 | Sprint 5 | German Operator Console | completed |
| 7 | Sprint 5E | Local Delivery and export foundation | completed |
| 8 | Sprint 6 | AHD Step 0 and Step 1 | pending |
| 9 | Sprint 7 | AHD Step 1B and Step 1C | pending |
| 10 | Sprint 8 | AHD Step 2 and Step 3 | pending |
| 11 | Sprint 9 | AHD Step 4A and Step 4B | pending |
| 12 | Sprint 10 | Presentation matrix and Jesse demo | pending |
| 13 | Sprint 11 | Final integration and maturity gate | pending |

Current canonical position: **7 of 13 execution stages completed**. Sprint 5E Tasks 1 through 8 and the bounded interstage gates M07, M08, M08L and M09 are complete in their documented scopes. M10 is active on the real CL pilot. Step 0 is released and Step 1 is `in_progress`; the complete real Step-0-through-Step-4B route and first customer package are still open.

## 2. Current executive snapshot

**Snapshot:** 2026-08-26 during M10 and the DEC-0031 repository consolidation. This section records the latest material gate. Exact Git refs are read directly from Git and are not cached here.

```text
Release Main Tasks: 9/10 completed
Current Main Task: M10 first controlled local production output
Current real route: CL Step 0 released; Step 1 in_progress without Production Execution or Agent Evidence
Repository: DEC-0031 consolidation authorized; it does not close M10 or Production Acceptance
Next Main Task: no further pre-release Main Task after M10
Runtime: intentionally stopped during repository freeze
```

The prior 563-test green run is retained baseline evidence. Current Task-6 changes use only the affected dependency closure. No automatic full repository rerun or repeated five-lane review is authorized.

## 3. Stable pre-release Main Tasks

| ID | Main Task | Current status | Owner | Estimate remaining | User-visible result |
|---|---|---|---|---|---|
| M01 | Core and workflow foundation | completed | Root Sisyphus | 0h | Project V2, transitions, artifacts, gates, revisions, events and Local API foundation |
| M02 | German Operator Console and browser gate | completed | Root Sisyphus | 0h | German Single-Admin Console with previously verified core actions and responsive Desktop surface |
| M03 | Delivery foundation Tasks 1 through 5 | completed | Root Sisyphus | 0h | contracts, inventory, role packages, manual Notion import pack and secure deterministic ZIP builder |
| M04 | Close Task 6 Local Delivery API | completed | Root Sisyphus | 0h | stable Preview, Create, History, Record, Download, Replay and Recovery API |
| M05 | Activate the existing Uebergabe und Export workspace | completed | Root Sisyphus | 0h | existing verified Console shell now provides typed Delivery preview, create, history, record and ZIP actions |
| M06 | Focused neutral Delivery E2E | completed | Root Sisyphus | 0h | live local UI/API/persistence route produced checkpoint and final ZIP evidence with exact replay |
| M07 | Minimal shared diagnostic trace DIB-005 | completed | Root Sisyphus | 0h | timestamped trace under gitignored `var/operator-diagnostics/v1/`, current pointer, append-only history and real browser evidence |
| M08 | Release-critical output quality restoration | completed | Root Sisyphus | 0h | PQ-0, PQ-1, PQ-2 and PQ-4 locally complete; professional Step 4A/4B output sets and Console review are restored without external execution claims |
| M09 | Route-based Production Release audit | completed in its recorded scope | Root Sisyphus and Hermes | 0h | PT-01 through PT-10 and Desktop Chrome evidence are retained; later real-pilot route defects were corrected separately and require the final affected-closure verification |
| M10 | First controlled local production output | in progress: Step 0 released, Step 1 awaiting production | Raphael, Hermes and Root Sisyphus | 3h to 8h plus external inputs | first approved downloadable customer package and real operator evidence |

Estimates are focused engineering time ranges, not guarantees. They assume no new external blocker, no scope expansion and compliance with the affected-closure test policy.

## 4. Completed M04 detail record

Sections 4 through 9 preserve the completed M04 through M09 task definitions and evidence boundaries. They are historical execution records, not the current queue. M10 in section 10 is the active Main Task.

| ID | Task-6 subtask | Status | Required verification |
|---|---|---|---|
| M04.1 | Delivery API remediation baseline with prior 563-green evidence | completed | retained baseline only |
| M04.2 | Four focused edge regressions | completed | exact red reproducers exist or are being created |
| M04.3 | Canonical role ordering before hashing and persistence | completed | `tests/test_delivery_api_role_order.py` and direct role persistence closure |
| M04.4 | Resolve completed replay and exact recovery before mutable source reads | completed | `tests/test_delivery_api_replay_source_independence.py` and direct replay/recovery closure focused-green |
| M04.5 | Make repeated OpenAPI generation identical | completed | `tests/test_delivery_openapi.py` and direct response-contract closure focused-green |
| M04.6 | Reject symlink/nonregular recovery paths and sort sidecars canonically | completed | `tests/test_delivery_api_recovery_inventory_safety.py` and direct Recovery Inventory closure focused-green |
| M04.7 | Affected-closure gate and Task-6 closeout | completed | direct Delivery admission regressions corrected and rechecked; no 563 rerun and no five-lane review |

### M04 completion result

Task 6 is complete when the five Delivery API operations and their exact replay/recovery paths are focused-green and Root-Sisyphus records the selected tests and excluded baseline areas.

## 5. M05 activate the existing Uebergabe und Export workspace

The German Console, navigation destination, route shell, responsive layout and visual design already existed and had passed the 24-cell visual browser matrix. M05 was not a new Console or route build. At the start of M05, the route intentionally rendered a contract-gate placeholder and issued no Delivery requests. M05 replaced only that placeholder with functional Delivery content wired to the Task-6 API.

### Subtasks

1. Preserve the existing Operator Shell, navigation, responsive layout and route design.
2. Replace the `delivery-contract-gate` placeholder in `OperatorShell.tsx`.
3. Add typed Delivery methods to the existing API client.
4. Show checkpoint and final eligibility.
5. Show included, missing, draft and released items.
6. Show source revision, package size, checksum and unresolved assignees.
7. Add Preview, Create and Download actions for checkpoint and final ZIP.
8. Add Copywriter, Developer and Notion package downloads.
9. Add export history and individual record view.
10. Preserve canonical readback and run only the affected Delivery route cells.

### User-visible gate

Raphael can open and judge the existing Console design and information architecture now. After M05, he can additionally operate the real Delivery Preview, Create, History, Record and Download flow on that existing surface. This should not wait for DIB-005 or full output-quality restoration.

## 6. M06 focused neutral Delivery E2E

### Subtasks

1. Create one neutral project fixture.
2. Preview checkpoint without writes.
3. Create checkpoint package with open blockers clearly reported.
4. Reject premature final export.
5. Create eligible final export.
6. Read history and exact record.
7. Download and extract ZIP.
8. Revalidate checksums.
9. Replay identical export without duplication.
10. Verify Copywriter, Developer and Notion package boundaries.
11. Verify no credentials or absolute host paths.
12. Exercise the exact Delivery Center browser route.

### User-visible gate

After M06, Raphael can perform a controlled local test flow and inspect a real generated package. This is the recommended minimum cutline for the first hands-on session tomorrow.

## 7. M07 diagnostic trace

### Subtasks

1. One timestamped trace ID per run or retry.
2. Append-only historical run index.
3. Stable `current` pointer.
4. Last successful and first failing operation.
5. Project, run, step, gate, route, action, API result and error code.
6. Transition, event and canonical readback references.
7. Same format for automated smoke and Raphael manual walkthrough.
8. No dashboard, new database, external telemetry or hidden model reasoning.

M07 is required before the formal release audit, but it does not need to block Raphael from first seeing and clicking the Console after M05/M06.

## 8. M08 release-critical output quality

### Subtasks

1. PQ-0: map every first-route output requirement to current authority.
2. PQ-1: restore professional Step 1B architecture presentation.
3. PQ-1: restore Step 1C Pillar-template depth and usable design specification.
4. PQ-2: restore Step-2 metrics and research breadth needed for planning.
5. PQ-2: prove the real Step-2 to Step-3 deterministic solver bridge.
6. PQ-4 plus DIB-001: restore Step-4A Copywriter and GEO briefing quality.
7. PQ-4 plus DIB-001: restore Step-4B Developer, HTML, JSON-LD and GEO quality.
8. Verify only the affected step, direct consumer and output cells.

Step 3B semantics, broad real-output parity and multi-archetype expansion remain post-release.

### M08 completion result

PQ-4 closes with 12 locally verified requirement rows and 2 separated external rows. Local fixtures prove contract shape, deterministic rendering, immutable identity, provenance handling, and Console review behavior. Google Rich Results, Screaming Frog, Lighthouse, axe, visual comparison, staging, production, provider, and customer execution remain unsatisfied by local evidence. The requested GitHub WIP snapshot is verified at `wip/m08-output-quality-2026-08-23`, commit `568bb497e57af4f7ec6dc8a13438681bbf423a55`.

## 8A. M08L Hermes Gateway LLM execution adapter

M08L is a release prerequisite on the existing M08 to M09 edge. It does not add an eleventh Main Task or a fourteenth Sprint stage.

Approved Option A ownership:

1. Root Sisyphus implements only the thin Heartweb Hermes-Runs adapter, the smallest fixture-versus-Hermes injection seam, reuse of existing validation and persistence, stable failure translation and focused repository tests.
2. Hermes performs the installed Gateway capability probe, isolated `heartweb-runtime` profile setup, Hermes-managed shared OAuth-pool verification, model and reasoning policy verification, live neutral Gateway proof and independent acceptance review.
3. Heartweb remains the only workflow, artifact, revision and gate authority.
4. OAuth tokens never enter Heartweb, agent prompts, traces, artifacts or Git.
5. M09 begins only after one neutral real LLM call reaches a valid Heartweb artifact candidate and invalid calls fail before canonical persistence.

Production-first cutline: General backend registry, separate execution-record persistence, direct Multi-Provider adapters, delegation contracts, subagent routing and broad benchmark infrastructure are Post-M10. Existing Heartweb runtime authorities are reused before M09.

### M08L completion result

M08L passed a real neutral Step-0 Heartweb runtime call through the isolated Hermes Gateway. The schema-valid Manifest candidate, Context Package and LLM records were atomically persisted in an ephemeral workspace. Provider Run ID, model and token usage were present, no tools were used, and Detailed Health returned zero active runs and agents. Evidence: `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.

Authority: `.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md` and DEC-0028.

## 9. M09 route-based Production Release audit

The final prototype uses `standards/testing/PROTOTYPE_TEST_POLICY.md` cells PT-01 through PT-10.

### Required route cells

1. app startup and project selection
2. intake and provisioning
3. sequential Step 0 through Step 4B route
4. revision and Human-Gate route
5. Delivery Preview and Create
6. history, record, ZIP and replay
7. one-way Notion handoff
8. Recovery and fail-fast
9. shared diagnostic trace
10. release-critical Desktop browser smoke

Each cell runs once. A failed cell and its named direct dependents are rerun after a fix. The matrix is not restarted from PT-01.

## 10. M10 first controlled local production output

### Subtasks

1. Chosen pilot and exact CL Project V2 inputs confirmed.
2. Search Deployment, Provider Target `agentseo-de-country`, `DE / 2276 / de`, region and 10 weekly hours confirmed.
3. Step 0 Manifest V2 Revision 3 produced, reviewed, approved, completed and released.
4. Step 1 Run `run-next-7f7e2b778f4521b9` created and held at `in_progress` without fabricated Evidence.
5. Produce Step 1 through the canonical Hermes and Provider Gateway route after the repository freeze.
6. Continue 1B, 1C, 2, 3, 4A and 4B with required provider execution, fail-fast behavior, revisions and Human Gates.
7. Create final Copywriter, Developer, Project Management and Notion packages.
8. Download, extract and inspect the final ZIP and deterministic checksums.
9. Review the professional output with Raphael and obtain the explicit M10 decision.
10. Record concrete corrections from the first real use as new bounded deltas.

## 11. Historical 2026-08-21 hands-on cutline

This section preserves the original short-term sequencing assumptions. M04 through M09 are now complete in their recorded scopes. Current M10 status is defined in sections 2, 3 and 10.

### Target 0: Raphael sees the current Console design

Available now:

- German Single-Admin Console
- six navigation destinations
- Projects, Workflow, Tasks, Artifacts and Reviews workspaces
- visible `Uebergabe und Export` route shell
- previously passed responsive visual evidence

Historical limitation at that checkpoint: the `Uebergabe und Export` page still showed the intentional contract-gate placeholder before M05 replaced it with functional Delivery actions.

### Target A: Raphael uses functional Delivery on the existing product

Required:

- M04 complete
- M05 complete
- local services started
- X01 guided manual walkthrough

Expected remaining focused time from the current snapshot: approximately 3h to 7h.

### Target B: Raphael produces and inspects a controlled local package

Required:

- Target A
- M06 complete

Expected remaining focused time from the current snapshot: approximately 5h to 11h.

This is feasible by tomorrow if no new P0/P1 blocks the affected route and Sisyphus does not re-enter broad test or review loops.

### Target C: first release-quality real provider-backed customer output

Required:

- M07 through M10
- verified real inputs and provider access

Expected additional focused time after Target B: approximately 13h to 28h plus external input or provider delays.

A first hands-on and controlled local output should not wait for Target C.

## 12. Work outside the current Root-Sisyphus queue

| ID | Work | Owner | Activation | Estimate |
|---|---|---|---|---|
| X01 | Raphael hands-on Operator Console walkthrough | Raphael and Hermes | after M05, ideally after M06 | 1h to 2h |
| X02 | Confirm real pilot inputs, deployment, provider target and capacity | Raphael and Hermes | completed for the active CL pilot; repeat for each future pilot | 1h to 3h |
| X03 | Complete DEC-0031 documentation authority and deterministic onboarding consolidation | Hermes | completed and verified on 2026-08-26 | 2h to 5h |
| X04 | Commit, push, branch reconciliation, master fast-forward and Fresh Clone | Hermes with Raphael approval | in progress under DEC-0031 | 1h to 3h |
| X05 | Jesse walkthrough and delivery presentation | Raphael | after M10 | 1h to 3h |
| X06 | Live one-way Notion and n8n integration | future approved integration sprint | post-release | 16h to 40h |
| X07 | Deployment, CMS adapters, mobile polish and broad expansion | future approved phases | post-release | 24h to 80h |

## 13. Post-release queue that does not block tomorrow

- full Step-3B performance semantics
- full real-output parity after first AHD output
- live Notion project creation
- live n8n orchestration
- additional mobile polish
- repository cleanup
- broad archetype and international expansion
- Jesse presentation expansion
- WordPress, Elementor, CMS and deployment adapters

## 14. Stable status reporting rule

The Telegram status job must show:

```text
Release Main Tasks: N/10
Current: Mxx title
Current subtasks: N/M
Active subtask: exact Root todo
Next Main Task: Mxx title
Since last update: concrete completions and checkpoint delta
Blocker: exact Raphael blocker or none
```

It must not present raw Root-Todo totals as overall project completion.

If Sisyphus replaces or expands its Root todo list, the Main Task denominator remains 10.

## 15. Authority and update rule

- This file is the current stable project task router.
- `00_admin/MASTER_TASK_MATRIX.json` is the machine-readable mapping used by the status script.
- Root-Sisyphus todos are dynamic execution detail beneath these Main Tasks.
- `PROJECT_STATE.md` and active Decisions remain product-state authority.
- New findings attach beneath an existing Main Task or enter the deferred/post-release backlog.
- A new Main Task requires an explicit scope decision from Raphael.

## 16. Automation stop boundary

Root-Sisyphus may continue automatically through M07, M08, M08L, M09 and M10. After M10 first controlled local production output is complete, Root-Sisyphus stops and waits for Raphael.

PR-008 and every post-release item require a new explicit authorization. Live Notion, live n8n, deployment, repository cleanup, mobile polish, broad archetypes, international expansion and presentation expansion do not start automatically.

Root-Sisyphus stops earlier only for:

- a pending Root question
- `BLOCKED_NEEDS_RAPHAEL`
- fatal runtime or container failure
- a P0 or P1 that needs a user decision
````

### Source: [`AGENTS.md`](../AGENTS.md)

- Lifecycle: `current_authority`
- Authority: 96
- SHA-256: `705cb0de4e0204cc0dbab74a205c40beaa4ab9c97b83000002928c489a193e0f`

````text
# AGENTS.md: Heartweb V2 operating instructions

**Project:** Heartweb SEO and GEO Production Workflow
**Author and architecture:** Raphael Rechberger
**Status:** Current V2 agent authority
**Updated:** 2026-08-25
**Audience:** Hermes Agent, Claude Code, OpenCode, Cursor and other execution agents

## 1. Mandatory session bootstrap

Before any implementation, review, planning or production action, read in this order:

1. `00_admin/SESSION_BOOTSTRAP.md`
2. `00_admin/PROJECT_STATE.md`
3. active and superseding entries in `00_admin/DECISIONS.md`
4. `00_admin/REPOSITORY_INDEX.md`
5. the active plan for the requested task from `.hermes/plans/INDEX.md`
6. exact standards, prompts, services and tests linked by `00_admin/repository-index/DOCUMENT_REGISTRY.json`
7. before any test or review decision, `standards/testing/PROTOTYPE_TEST_POLICY.md`

Latest explicit Raphael instruction wins. Project State and active Decisions override old plans, old docs, audit prose and semantic similarity.

Historical, superseded and evidence records are not default instructions. Read them only for origin, rollback, prior decisions or failure reconstruction.

### Binding test execution authority

`standards/testing/PROTOTYPE_TEST_POLICY.md` is the project-local Production-first test authority. It requires baseline-plus-delta evidence and verification only along the proven affected dependency closure.

Without new explicit authorization from Raphael, do not run the complete repository suite, restart a passed matrix after one later cell fails, or launch repeated broad multi-agent reviews after bounded fixes. A failed matrix cell is rerun only with the direct dependents named by the policy. Generic skills, CI habits and older plans do not override this rule.

### Targeted edit discipline

- Do not submit one aggregate patch across several identical or similarly shaped code regions. Patch one uniquely identifiable semantic block per call.
- If every exact occurrence must change, use an explicit replace-all operation only after verifying that all matches have the same intended meaning.
- At the first ambiguous-match or hunk-not-found rejection, stop that patch strategy. Do not retry a similar aggregate patch.
- After one rejected targeted patch, re-read the exact enclosing region. If it still cannot be matched uniquely, read the complete small file or enclosing function and write it once in full.
- A rejected patch changes nothing. Confirm that before continuing, and never report partial application from a failed patch.

## 2. Product definition

Heartweb is a client-neutral local SEO and GEO production system for one internal operator. It automates the technical production chain from verified client inputs through strategy, architecture, keyword evidence, roadmap, professional Copywriter briefings, Developer specifications and deterministic handoff packages.

The system does not write final editorial copy. Heartweb Copywriters create the final human text from the approved briefing.

The visible product is a professional German Single-Admin Console. Copywriters, developers and clients do not use the Console. They receive files, ZIP packages and a Notion implementation project.

## 3. Binding product flow

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B is not part of the initial sequence. It runs at day 30, 60 and 90 after publication when verified performance data exists.

The first production release is local. Live Notion, live n8n, public deployment, exhaustive mobile polish and broad international expansion do not block the first controlled output.

## 4. Architecture and authority

### Heartweb Core

The Core contains binding domain contracts, workflow graph, transitions, artifacts, revisions, Evidence, Quality Gates, approvals, releases and structured errors.

Only the Transition Service changes canonical workflow state.

### Operator Console

The Console sends typed commands, shows canonical read models and supports intake, workflow execution, artifacts, revisions, reviews, tasks, blockers and Delivery. It does not duplicate workflow rules.

### Provider Gateway

All external research and metric providers are accessed through versioned provider boundaries. Prompts must not call providers directly. Location, location code and language are bound together. Missing or failed provider data stops the run.

### Delivery

Delivery is a derived, deterministic and read-only projection of released Core records. It creates checkpoint and final packages, Copywriter and Developer views, a manual Notion import project and secure ZIP archives. Delivery cannot approve gates, mutate artifacts or change workflow state.

### Notion

After the approved Step-4B Delivery, Notion owns human implementation work: tasks, people, priorities, deadlines, comments, review and launch. Post-handoff staff task changes do not call or resume the Core.

### n8n

n8n is future orchestration and transport. It may orchestrate Step 0 through Step 4B, create the Notion project and later trigger Step 3B. It is not state authority and does not monitor daily staff tasks for Core progression.

### Step 3B

At day 30, 60 and 90, n8n combines the released strategy and plan with publication references and verified real metrics. The Core creates a versioned adjustment proposal. The original plan remains immutable.

## 5. Framework and customer separation

The repository is the client-neutral framework. Customer-specific sector, services, claims, regions, branding, keywords, Evidence and design belong in isolated customer workspaces.

AHD is the Golden-Path pilot, not product logic. Do not embed AHD-specific content into shared prompts, contracts, services or UI.

Never commit customer workspaces, credentials, raw authorization headers or secret values.

## 6. Prompt, tool and contract evolution

Prompts are versioned workflow resources. Never silently overwrite the meaning of a prompt used by an accepted run.

A prompt change that affects output meaning requires coordinated review of:

1. prompt version
2. output schema version
3. validator
4. renderer
5. Quality Gate
6. positive and negative fixtures
7. Context Package and tool policy
8. migration or activation rule

Contracts protect structure, identity, lineage, required Evidence and workflow safety. They do not guarantee semantic truth or excellent writing by themselves. Output quality requires complete inputs, strong prompts, real tool data, adequate contracts, validators, human review and behavioral tests.

LLMs retain strategic freedom inside accepted boundaries. They may develop themes, structures, angles, comparisons and recommendations. They may not invent metrics, claims, locations, approvals, identities, revisions or completion state.

See `docs/09-extension-and-evolution-guide.md`.

## 7. Fail-fast rules

1. Never estimate missing provider metrics.
2. Never fabricate customer facts, local presence, claims or Evidence.
3. Never continue after schema, hash, tenant, revision or gate failure.
4. Never present simulated Evidence as live Evidence.
5. Never use a silent fallback that changes product meaning.
6. Return a stable error code, human remediation and technical details.
7. Preserve the last valid canonical state after failure.

## 8. Artifact and revision rules

- Released artifacts are immutable.
- An edit creates a new revision.
- Every revision binds parent revision, content hash, Project, Run, Step and Evidence.
- A rerun uses the released predecessors, current Prompt Registry entry, findings and expected output contract.
- A stale approval does not apply to a new artifact hash.
- Exact replay is allowed only when identities and canonical bytes match.

## 9. Verification claims

Keep these evidence levels separate:

- unit or contract test
- local service integration
- deterministic fixture E2E
- live-provider smoke
- real-project Golden Path
- external Notion or n8n E2E
- production acceptance

A fixture run proves plumbing and lifecycle behavior. It does not prove provider connectivity, prompt quality, semantic usefulness or customer value.

Do not claim production readiness without a real controlled output, deterministic Delivery, no open P0/P1 and explicit Raphael approval.

## 10. Git and parallel work

- Do not commit, push, merge, deploy or rewrite history without explicit Raphael authorization.
- Do not stage or change the active shared index while Sisyphus writes.
- Parallel work uses an isolated Git worktree and branch.
- Before integrating a parallel branch, update it from the stable Feature commit and rerun all affected tests and generated-index checks.
- DEC-0031 authorizes the current documented repository consolidation into `master`; this Git baseline is not Production Acceptance. Any later commit, push, merge, deployment or history change again requires explicit Raphael authorization.

## 11. Agent orchestration boundary

OpenCode OMO is a development tool, not Heartweb production runtime.

When OMO is active, Hermes communicates only with root Sisyphus. Sisyphus owns internal delegation and worker lifecycle. Hermes does not inspect, steer or terminate OMO child sessions. Native Hermes subagents require explicit Raphael authorization.

## 12. Authorship and writing

- Raphael Rechberger is the sole author of project documents, deliverables and commits.
- Never use Em Dash or En Dash characters. Use standard hyphens, colons or full sentences.
- Distinguish implemented, verified, simulated, planned, deferred and absent behavior.
- Link mutable facts to their canonical source instead of copying them across documents.
- Update `PROJECT_STATE.md` and `DECISIONS.md` when strategy or authority changes.

## 13. Current documentation map

- Current architecture: `docs/00-current-production-architecture.md`
- Extension rules: `docs/09-extension-and-evolution-guide.md`
- Notion boundary: `docs/integrations/notion-operating-model.md`
- n8n boundary: `docs/integrations/n8n-orchestration-model.md`
- Delivery plan: `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
- Documentation registry: `00_admin/repository-index/DOCUMENT_REGISTRY.json`
- RAG-ready registry: `00_admin/repository-index/DOCUMENT_REGISTRY.jsonl`
- Lifecycle indexes: `docs/INDEX.md`, `.hermes/plans/INDEX.md`, `00_admin/audits/INDEX.md`, `03_research/INDEX.md`
````

### Source: [`CLAUDE.md`](../CLAUDE.md)

- Lifecycle: `current_authority`
- Authority: 94
- SHA-256: `66e913c9b37809d8e62ecc20d380e20f47f707efa3b0c7c98dce71beaa1b2a0f`

````text
# CLAUDE.md: Heartweb V2 quick operating contract

**Author:** Raphael Rechberger
**Status:** Current V2 agent authority
**Updated:** 2026-08-22

## Read first

1. `00_admin/SESSION_BOOTSTRAP.md`
2. `00_admin/PROJECT_STATE.md`
3. `00_admin/DECISIONS.md`
4. `00_admin/REPOSITORY_INDEX.md`
5. the active task plan from `.hermes/plans/INDEX.md`
6. before any test or review decision, `standards/testing/PROTOTYPE_TEST_POLICY.md`

Current Project State and active Decisions override old docs, old plans and audit prose. Historical, superseded and evidence records are opt-in context only.

`standards/testing/PROTOTYPE_TEST_POLICY.md` is the binding Production-first test authority. It preserves prior green baseline evidence and selects tests only for the proven affected dependency closure. Without new explicit Raphael authorization, do not run the complete repository suite, restart a passed matrix after a later-cell failure, or launch repeated broad multi-agent review rounds.

## Product

Heartweb is a client-neutral local SEO and GEO production Core with a German Single-Admin Console. It turns verified client inputs into strategy, architecture, keyword evidence, a 120-day roadmap, Copywriter briefings, Developer specifications and deterministic Delivery packages.

Human Copywriters write the final editorial copy. External team members work from files and Notion, not from the Admin Console.

## Workflow

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B runs separately at day 30, 60 and 90 using verified post-publication performance data.

## Authority

- Transition Service is the only canonical workflow state writer.
- Prompts create candidates and never approve or complete steps.
- Provider calls go through Provider Gateway with explicit market, code and language.
- Released artifacts are immutable. Changes create new revisions.
- Delivery is deterministic and read-only with respect to Core state.
- Notion owns staff execution after final handoff.
- Post-handoff Notion task changes do not call the Core.
- n8n later orchestrates the concept workflow, Notion handoff and Step-3B checkpoints. It never owns business state.

## Fail-fast

Never guess missing metrics, facts, claims, locations, Evidence, IDs, revisions or approvals. Stop with a stable error code and remediation. Preserve the last valid canonical state.

Never present simulated output as live or production Evidence.

## Extensibility

Prompt and tool changes are allowed through versioned resources. A semantic output change requires coordinated prompt, schema, validator, renderer, gate, fixtures, Context Package and activation review.

Contracts guarantee accepted structure, identity, lineage and persistence. They reduce and expose hallucination risk but cannot guarantee semantic truth or excellent output alone.

See `docs/09-extension-and-evolution-guide.md`.

## Project separation

Shared runtime and prompts remain client-neutral. Customer facts, claims, regions, branding, Evidence and design remain in isolated customer workspaces. AHD is a pilot fixture, not shared product logic.

## Git and agents

Do not commit, push, merge, deploy or rewrite history without explicit Raphael authorization. Parallel work uses an isolated worktree.

When OpenCode OMO is active, Hermes communicates only with root Sisyphus. Do not control child sessions. Native Hermes subagents require explicit Raphael authorization.

## Writing

Raphael Rechberger is the sole author. Never use Em Dash or En Dash characters. Clearly label implemented, verified, simulated, planned, deferred and absent behavior.
````

### Source: [`README.md`](../README.md)

- Lifecycle: `current_authority`
- Authority: 86
- SHA-256: `0c8c1b1c1a7174b788aa158760b623ca4ad400731282876d2dc8b2c07626aabe`

````text
# Heartweb SEO and GEO Production Workflow

**Author and architecture:** Raphael Rechberger
**Organization:** Heartweb
**Status:** Production-first V2 development
**Updated:** 2026-08-26

Heartweb turns a verified customer briefing into a structured, reviewable and deliverable SEO and GEO implementation project.

The system is designed to replace a manual chain of prompts, spreadsheets, file copying and task creation with one controlled workflow. It produces the strategic and technical foundation. Human Copywriters create the final editorial content, and developers implement the approved specifications.

## What Heartweb produces

A completed local workflow can produce:

- validated Project V2 customer context
- Pillar and cluster strategy
- page, menu and URL architecture
- reusable design tokens and Pillar templates
- verified keyword and provider Evidence
- deterministic 120-day roadmap
- internal-linking maps
- professional Copywriter briefings
- Developer page specifications and HTML
- implementation tasks, priorities, assignees and deadlines
- Copywriter, Developer and Project Management packages
- manual Notion import project
- deterministic ZIP archives with manifests and checksums

## Product flow

```text
Customer briefing
-> Heartweb Admin Console
-> Core workflow 0 to 4B
-> review, revision and Human Gates
-> Delivery packages
-> Notion implementation project
-> human execution by the Heartweb team
```

After handoff, Notion owns daily implementation work. Staff task changes do not resume or mutate the Core.

At day 30, 60 and 90, Step 3B compares the released strategy and plan with verified real performance data and proposes adjustments for future work.

## Architecture

```text
German Single-Admin Console
        |
        v
Operator API -> Heartweb Core -> Provider Gateway and deterministic tools
        |              |
        |              v
        |        artifacts, revisions, Evidence, gates and releases
        v
Delivery Service -> role packages, Notion import and secure ZIP

Future n8n:
UI and schedules -> typed Core commands -> Notion handoff -> Step-3B checkpoints
```

Only the Transition Service writes canonical workflow state. The Console, Notion and n8n never duplicate that logic.

Read the full architecture at [`docs/00-current-production-architecture.md`](docs/00-current-production-architecture.md).

## Current state

Implemented in the current repository baseline:

- V2 domain, workflow and Transition Service
- multi-location Project V2, Search Deployment and verified Provider Target bindings
- Provider Gateway, typed Heartweb tools and persisted Evidence boundaries
- immutable artifacts and revisions
- Quality Gates, approvals, releases and recovery
- Context Packages and reproducible LLM run records
- specialized Hermes Step agents, Worker Profiles and Tool Policies for Steps 0 through 4B
- persistent production executions, bounded continuation, retry and re-steering
- Local Operator API and append-only events
- German Single-Admin Console
- real browser-tested core actions
- shared local diagnostic traces
- deterministic Delivery API, Delivery Center, role packages, manual Notion import and secure ZIPs

Current real acceptance boundary:

- the current real pilot has a reviewed, approved and released Step-0 Manifest V2
- Step 1 is `in_progress` without Production Execution, Agent Evidence or LLM output
- the real Step-1-through-Step-4B route, Human Gates, final Delivery package and professional operator review remain open
- M10, PT-03 and PT-11 are not complete

Post-release:

- live Notion adapter
- live n8n orchestration
- complete Step-3B implementation before the first day-30 checkpoint
- public deployment adapters
- broad international and multi-archetype expansion
- additional mobile polish and repository cleanup

Current mutable status is always in [`00_admin/PROJECT_STATE.md`](00_admin/PROJECT_STATE.md).

## Repository navigation

Start every new human or LLM session with:

1. [`00_admin/ONBOARDING_REFERENCE.md`](00_admin/ONBOARDING_REFERENCE.md), the deterministic single-entry snapshot
2. [`00_admin/SESSION_BOOTSTRAP.md`](00_admin/SESSION_BOOTSTRAP.md)
3. [`00_admin/PROJECT_STATE.md`](00_admin/PROJECT_STATE.md)
4. active and superseding entries in [`00_admin/DECISIONS.md`](00_admin/DECISIONS.md)
5. [`00_admin/REPOSITORY_INDEX.md`](00_admin/REPOSITORY_INDEX.md)
6. the active task plan from [`.hermes/plans/INDEX.md`](.hermes/plans/INDEX.md)

The generated Onboarding Reference bundles navigation and identified source blocks. It does not override Project State, active Decisions or the linked contract source.

Machine-readable retrieval sources:

- [`DOCUMENT_REGISTRY.json`](00_admin/repository-index/DOCUMENT_REGISTRY.json)
- [`DOCUMENT_REGISTRY.jsonl`](00_admin/repository-index/DOCUMENT_REGISTRY.jsonl)
- [`document-registry.schema.json`](standards/documentation/document-registry.schema.json)

Area indexes:

- [`docs/INDEX.md`](docs/INDEX.md)
- [`00_admin/audits/INDEX.md`](00_admin/audits/INDEX.md)
- [`03_research/INDEX.md`](03_research/INDEX.md)

## Workflow steps

| Step | Purpose | Main output |
|---|---|---|
| 0 | Intake and Project V2 | validated customer project |
| 1 | Pillar and topic inventory | strategic topic model |
| 1B | page and navigation architecture | architecture and menu view |
| 1C | design system and Pillar templates | reusable page structure |
| 2 | provider-backed keyword research | verified keyword Evidence |
| 3 | deterministic capacity plan | 120-day roadmap and links |
| 4A | Copywriter briefing | editorial implementation package |
| 4B | Developer page specification | HTML, schema and technical handoff |
| Delivery | deterministic handoff | ZIP, role packages and Notion import |
| 3B | later performance adaptation | versioned adjustment proposal |

## Extending the system

Prompts, providers, tools, schemas and workflow steps can be extended through versioned contracts. Old accepted runs remain bound to their original prompt, schema, model, tool policy, Evidence and artifact hashes.

See [`docs/09-extension-and-evolution-guide.md`](docs/09-extension-and-evolution-guide.md).

## Quality model

Contracts protect:

- required structure
- customer and project identity
- revision and hash integrity
- Evidence references
- workflow ordering
- deterministic persistence

Contracts do not guarantee semantic truth or excellent writing by themselves. Heartweb combines strong prompts, verified sources, tool results, validators, behavioral tests and human approval.

## Framework and customer data

This repository contains the client-neutral Core. Customer-specific facts, claims, services, regions, design and Evidence belong in isolated customer workspaces and must never be committed to the framework repository.

The active pilot identity is recorded in Project State. AHD and CL are validation projects, not shared product logic.

## Integrations

- Current first release: local Core, files, ZIP and manual Notion import
- Future Notion: one-way creation of the customer implementation project
- Future n8n: orchestration, provider waits, retries, Notion handoff and Step-3B schedules
- OpenCode OMO: development and QA only, never production runtime

## Development and release rules

- No silent fallback or estimated provider data
- No commit, push, merge or deployment without Raphael approval
- `master` is the consolidated repository baseline under DEC-0031, not a Production Acceptance claim
- Historical audits and checkpoints remain immutable
- Parallel work uses isolated Git worktrees
- Raphael Rechberger is the sole author
- Em Dash and En Dash characters are forbidden

## License

Proprietary. Intended for Heartweb production use.
````

### Source: [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md)

- Lifecycle: `current_authority`
- Authority: 97
- SHA-256: `72b28ebfcbadfd8bef7a31b90cfcb07e8ce081ecb7cc33f78c5db92154bdb2d4`

````text
# Heartweb Prototype Test Policy and Final Test Matrix

**Author:** Raphael Rechberger
**Status:** Binding project-local test authority
**Version:** 1.0.0
**Effective:** 2026-08-22
**Scope:** Heartweb local prototype, implementation fixes, regression verification and Production Release audit

## 1. Binding instruction

Every agent, orchestrator, reviewer and new session MUST read this file before selecting or running tests.

This policy has higher project-local authority than generic skills, generic CI habits, worker defaults or previous plans that prescribe a complete suite after every change.

The latest explicit instruction from Raphael remains the highest authority.

The objective is the fastest safe path to an operable local Heartweb system. Testing protects that objective. Testing must not replace delivery.

## 2. Core rule

A green test result remains valid baseline evidence for the exact code and behavior it previously covered.

After a code change, only the proven affected dependency closure loses direct current-state evidence:

```text
changed symbol
-> changed module
-> shared contract or persisted shape
-> affected route
-> affected flow
-> affected gate
```

Test that closure. Do not restart unrelated test areas.

## 3. Prohibited defaults

Without a new explicit Raphael authorization, agents MUST NOT:

1. Run `python tests/run_full_suite.py`.
2. Run all discovered repository tests.
3. Repeat the complete suite after a small or bounded fix.
4. Restart a previously passed end-to-end flow from its first step when only a later cell failed.
5. Launch multiple broad review lanes after each correction.
6. Re-run unrelated solver, prompt, workflow, UI, browser, archive or integration tests only because files changed elsewhere.
7. Treat a prior green baseline as invalid without naming the exact dependency that the new change can affect.
8. Expand a focused test scope merely because broader testing is convenient.
9. Use test count as a proxy for customer usefulness or production readiness.
10. spend model tokens on repeated review synthesis when deterministic evidence already answers the question.

A complete suite requires separate explicit authorization from Raphael in the current conversation. A prior general instruction to "verify" or "test thoroughly" is not authorization for a full suite.

## 4. Baseline plus delta evidence

Heartweb uses cumulative evidence:

```text
validated baseline H0
+ changed delta D1
+ focused verification V1 for the affected closure
= current evidence H1
```

Unchanged areas retain their baseline evidence. The delta record must name:

- changed files and symbols
- observable defect or requested behavior
- affected route, flow and gate
- selected tests
- reason each test belongs to the closure
- tests deliberately not repeated
- result
- next product action

A new error does not erase unrelated previous evidence.

## 5. Mandatory test selection algorithm

For every defect or bounded change:

1. Assign one defect or change identifier.
2. Reproduce the exact failure at the highest stable public seam.
3. Add or identify the smallest red regression test that proves the failure.
4. List changed symbols and direct callers.
5. Trace only the affected contract, route, flow and gate.
6. Select the matching matrix row below.
7. Run the red reproducer.
8. Apply the smallest safe fix.
9. Run the reproducer again.
10. Run the smallest directly affected integration set.
11. If an unexpected failure appears, expand exactly one dependency ring outward.
12. Do not jump from one unexpected failure to the complete repository suite.
13. Record the commands, counts and results.
14. Continue to the next product task as soon as the affected closure is green.

## 6. Incremental regression matrix

| Change class | Required focused evidence | Conditional evidence | Explicitly excluded by default |
|---|---|---|---|
| Pure normalization, sorting or helper behavior | exact unit regression plus direct caller test | persistence or hash test only when output bytes or identity change | unrelated API, UI, workflow, prompt and solver tests |
| Request or response model | model validation plus exact route success and failure case | OpenAPI and generated client only when public schema changes | unrelated service and browser suites |
| API error translation | exact failing route plus advertised error envelope | neighboring methods on the same route family when they share the handler | all other API routes and repository suite |
| Persistence or immutable record shape | write, readback, idempotency and conflict tests for that record family | replay or recovery only when they consume the changed shape | UI, prompt, solver and unrelated repositories |
| Replay or recovery ordering | exact completed replay, interrupted recovery and changed-source case | authorization and sidecar cleanup when touched | fresh project creation, unrelated steps and browser matrix |
| Filesystem safety | exact traversal, symlink or nonregular-file regression at the changed boundary | one authorized positive case for the same boundary | every other security or archive test |
| OpenAPI override | repeated `app.openapi()` equality plus exact affected response contract | codegen drift check when snapshot bytes change | full API suite and frontend build when generated types do not change |
| Generated API client | exact codegen drift check plus TypeScript compile of affected client | frontend build only when application imports changed generated types | Python full suite |
| UI component behavior | affected component test plus exact operator action | one browser route and affected viewport when rendering changes | all routes, all viewports and backend suite |
| Shared layout or CSS | exact affected surfaces and viewports identified from the shared selector | one neighboring surface to prove the shared rule | automatic 24-cell visual rerun |
| Workflow transition | exact legal transition, exact illegal transition and immediate predecessor or successor | persistence/readback if event or state shape changes | all unrelated workflow steps |
| Prompt, schema, validator or renderer | exact workflow step fixture, validator and rendered output | immediate downstream consumer of that artifact | complete Step 0 to 4B rerun |
| Provider adapter | exact capability, request binding, error and evidence contract | one consuming step with deterministic provider fixture | unrelated providers and workflow steps |
| Diagnostic trace | exact action to trace, persisted trace and readback | one failure reconstruction for the same route | full smoke matrix and unrelated logging |
| Broad shared service | changed public seam plus every proven caller in its dependency closure | expand one caller ring when an unexpected failure proves it necessary | complete repository suite unless Raphael explicitly authorizes it |

## 7. Current Task 6 affected closure

The current four Task 6 defects use this bounded matrix.

| Defect | Primary regression | Directly affected closure | Tests not repeated |
|---|---|---|---|
| Canonical role order | `tests/test_delivery_api_role_order.py` | role requests, request hash, persisted role order, idempotent replay | solver, prompts, workflow transitions, UI and unrelated Delivery files |
| Source-independent replay and recovery | `tests/test_delivery_api_replay_source_independence.py` | completed replay, exact recovery, mutable source independence | fresh workflow runs, browser routes and unrelated artifact revisions |
| Repeatable OpenAPI generation | `tests/test_delivery_openapi.py` | repeated `app.openapi()`, affected Delivery response contract, codegen only if bytes changed | all Delivery persistence, workflow and UI tests when generated types stay unchanged |
| Recovery Inventory safety and ordering | `tests/test_delivery_api_recovery_inventory_safety.py` | sidecar discovery, regular-file enforcement, symlink rejection, canonical order | archive suite, provider suite, prompt suite and unrelated API routes |

After these four regressions and their direct closure are green, Task 6 proceeds to Task 7. Another complete 563-plus run and another five-lane review are prohibited without separate Raphael authorization.

## 8. Review proportionality

### Default for bounded fixes

- implementer focused red and green proof
- one direct code and evidence check by Root-Sisyphus
- no multi-lane review

### Additional review only when justified

One additional independent review may be used only when the change creates or alters:

- an irreversible data migration
- a new external side effect
- a new authorization boundary
- a new public contract with customer-visible consequences

The review scope remains limited to that boundary. Repeated five-lane review rounds are not a default acceptance gate.

## 9. Final prototype route matrix

The final prototype is accepted through the following customer and operator route matrix. This matrix replaces an automatic complete repository suite.

Each cell runs once on the release candidate. If one cell fails, rerun that cell and only its direct downstream dependents after the fix. Do not restart the matrix at PT-01.

| ID | Prototype route or gate | Required observable evidence | Direct downstream cells |
|---|---|---|---|
| PT-01 | Local app startup and project selection | Operator Console loads, correct tenant and project are visible, no hidden fallback | PT-02 |
| PT-02 | Intake, validation and provisioning | accepted Project V2 identity, workspace readback, invalid intake fails before writes | PT-03 |
| PT-03 | Sequential production route 0 -> 1 -> 1B -> 1C -> 2 -> 3 -> 4A -> 4B | each required artifact exists with correct identity, predecessor, revision, validation and visible status | PT-04, PT-05 |
| PT-04 | Human review, revision and gate route | edit, save, canonical readback, revision request, rejection, approval and stale-approval protection | PT-05 |
| PT-05 | Delivery Preview and Create | preview has no writes, create binds approved revisions, warnings and policy are visible | PT-06, PT-07 |
| PT-06 | Delivery history, record, ZIP and replay | history and record read back canonical completion, ZIP downloads, exact replay remains identical | PT-07 |
| PT-07 | One-way Notion handoff | deterministic import package, assignments, priorities and deadlines, no staff-task callback into Core | none |
| PT-08 | Recovery and fail-fast route | interrupted Delivery is recoverable, unauthorized or unsafe recovery is blocked without writes | PT-05, PT-06 |
| PT-09 | Shared diagnostic trace | first failing operation, last successful operation, IDs, timestamps, error code and artifact evidence are directly readable | affected failed cell only |
| PT-10 | Release-critical operator browser smoke | exact Desktop actions for project, workflow, artifact, review and Delivery Center succeed in Chrome | affected UI cell only |
| PT-11 | Controlled real customer output | one approved local customer route produces professional downloadable packages without live integration claims | none |

### Matrix retry rule

Examples:

- PT-06 fails after ZIP download: fix and rerun PT-06. Rerun PT-07 only if package bytes or Notion inputs changed. Do not rerun PT-01 through PT-05.
- PT-04 fails on stale approval: fix and rerun the stale-approval scenario plus PT-05 if approval identity changed. Do not rerun research steps.
- PT-10 fails on Delivery Center layout: rerun the exact Delivery Center action and viewport. Do not rerun backend solvers or the full visual matrix.
- PT-03 fails in Step 2 metrics: rerun Step 2 and the Step 2 -> Step 3 dependency. Do not restart Step 0, Step 1 or unrelated Delivery.

## 10. Release decision

The release decision uses:

- the retained green baseline
- all focused delta evidence since that baseline
- the final prototype route matrix
- open P0 and P1 findings
- actual customer-facing outputs

Production acceptance does not require rerunning every historical test after every delta.

A full repository suite remains available as an optional diagnostic or explicitly authorized release action. It is not the default Heartweb prototype gate.

## 11. Required Root-Sisyphus report after each fix

Root-Sisyphus reports:

```text
Change ID:
Observed failure:
Changed files and symbols:
Affected route, flow and gate:
Focused red test:
Direct closure tests selected:
Why each test is in scope:
Unrelated tests deliberately retained from baseline:
Result:
Remaining blocker:
Next product task:
```

Reports must distinguish:

- previous baseline evidence
- new focused evidence
- not assessed areas

They must not describe a focused regression pass as a complete Full-System test.

## 12. Enforcement for new sessions

`AGENTS.md` and `CLAUDE.md` point to this file. New sessions must read it before:

- creating a test plan
- adding a test todo
- running a test command
- requesting independent review
- declaring a gate complete

If another plan, skill, review template or worker instruction conflicts with this file, this file wins unless Raphael explicitly changes the policy.
````

### Source: [`docs/00-current-production-architecture.md`](../docs/00-current-production-architecture.md)

- Lifecycle: `current_authority`
- Authority: 94
- SHA-256: `2be27ed26bd8893ac8919cbca3c382f62f9d0441139fc28353e44c83243f72a6`

````text
# Current Heartweb production architecture

**Author:** Raphael Rechberger
**Status:** Current architecture authority
**Updated:** 2026-08-26

## 1. Purpose

Heartweb automates the strategic and technical preparation of SEO and GEO customer projects. It accepts verified client input and produces an implementation-ready strategy, architecture, roadmap, Copywriter briefing, Developer specification and Delivery package.

The system is not a final editorial writer, CMS, CRM or employee monitoring platform.

## 2. Product boundary

### Heartweb owns

- verified intake and Project V2
- workflow Steps 0 through 4B
- provider Evidence and deterministic tools
- artifacts, revisions and Quality Gates
- strategy and architecture outputs
- Copywriter and Developer handoffs
- deterministic Delivery packages
- later Step-3B performance comparison

### Notion owns after handoff

- human implementation tasks
- assignees and deadlines
- comments and coordination
- Copywriting, design and development execution
- operational review and launch

Post-handoff Notion tasks do not resume the Core or mutate artifacts.

### Human team owns

- final editorial copy
- brand judgment
- implementation in WordPress, Elementor or another CMS
- customer communication and commercial approval
- publication decisions

## 3. Runtime components

### 3.1 Domain contracts

Project V2 and related contracts separate Customer, Brand, Market, Search Deployment, Entity, Risk, physical location and Service Area. The framework remains client-neutral.

The accepted briefing creates one or more `market_deployments[]` before Step 0. Every active deployment binds its own market, country, language, locale, SEO operating model, target regions, physical-location and service-area references and one exact Provider Location Registry target. The registry target carries provider identity, target type, canonical location name, provider location code and verification Evidence. A market registry entry is not a substitute for this deployment-specific provider target.

Project V2 also binds the confirmed weekly planning capacity with minimum, maximum, source, operator identity and timestamp. If the input portfolio contains no explicit hours, intake returns a typed missing-input question instead of a default. For an already accepted project, the same value can be previewed and explicitly confirmed in the Operator Console. This creates a new Project V2 and Logical Project Session revision before Step 0 continues. Step 0 and Step 3 consume the same confirmed capacity record.

Multiple physical locations or service areas may belong to one deployment when they share the same provider research target. Distinct provider research targets require distinct deployments. The initial production sequence is bound to the one active primary deployment. Missing, ambiguous, unverified or operating-model-incompatible targets stop before Step 0. There is no country, language or provider-code default.

Step 0 produces Manifest V2 as an exact read-only projection of the run-bound deployment. A Project V2 or accepted-intake revision also creates a new hash-bound Logical Project Session and archives its predecessor so a rerun cannot consume stale intake bytes.

### 3.2 Workflow graph

The workflow graph defines legal step order and predecessor releases. Prompts do not control state.

```text
0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery
```

Step 3B is activated separately by a valid day-30, day-60 or day-90 performance checkpoint.

### 3.3 Transition Service

The Transition Service is the only canonical state writer. It validates:

- tenant, project and run identity
- current revision
- workflow predecessor
- artifact and content hash
- machine Quality Gates
- Human Approval
- release state

A failed transition leaves canonical state unchanged.

### 3.4 Context Builder and LLM runtime

Each run receives a versioned Context Package containing exact source paths, revisions and hashes. LLM Run Records bind prompt ID, prompt version, model, provider, tool policy, input hash, output hash and result metadata.

Provider sessions may be reused as a cache but are never Source of Truth.

The isolated Hermes profile `heartweb-runtime` is the agentic production runtime for Steps 0, 1, 1B, 1C, 2, 3, 4A and 4B. Every Step starts a specialized, versioned agent run with its own prompt, Worker Profile, model and reasoning policy, allowed tools, output contract and bounded agent and tool rounds. A Step agent may delegate focused research, processing, synthesis or review work to Hermes subagents when the Step contract permits it.

AI performs the generative and interpretive work. Deterministic code remains responsible for hashes, identity, schema validation, Evidence normalization, state transitions, approval authority, replay and Delivery packaging.

### 3.5 Prompt Registry

Every step uses a registered prompt version and expected output contracts. Old accepted runs remain reproducible because the exact prompt bytes and related versions remain identifiable.

### 3.6 Provider Gateway

The Provider Gateway normalizes external research and metric providers. Every request binds the run deployment, provider target ID, market, country, canonical provider location name, provider location code and language. The tool boundary verifies these values against `standards/domain/provider-location-registry.json` and the persisted Project V2 deployment before any provider call. Raw provider responses and hashes become Evidence.

Step agents may receive already validated provider Evidence or request an allowed provider operation through a typed Heartweb tool. The tool executes server-side through the Provider Gateway. Prompts and agents never receive provider credentials and never bypass this boundary with direct external provider calls.

Paid, externally acting or cost-unknown provider operations require the registered preview and explicit operator confirmation before execution. Missing capabilities, credentials, quota, exact deployment bindings, verified provider targets or confirmation stop the run without a fallback. Country-only lookup through the legacy `standards/location-codes.json` is not part of the production path.

### 3.7 Artifacts and revisions

Artifacts are immutable after release. Editing creates a child revision. A revision binds:

- Project, Run and Step
- parent revision
- content hash
- prompt and context identity
- relevant Evidence
- gate and approval state

### 3.8 Quality Gates

Machine gates enforce structural and measurable requirements. Human Gates approve strategic and customer-facing meaning. Neither can be inferred from prompt prose.

### 3.9 Operator API

The local API exposes typed commands and read models for the Admin Console. It preserves tenant and workspace containment, idempotency, replay and structured error behavior.

### 3.10 German Single-Admin Console

The Console is the production cockpit for one internal operator. It supports:

- project intake and selection
- workflow execution
- task and blocker handling
- artifact editing and revision comparison
- reviews and Human Gates
- release and recovery
- Delivery preview and download

Technical hashes, raw records and logs remain behind detail views.

### 3.11 Delivery Service

Delivery reads released Core records and creates derived packages. It cannot mutate Core state.

Delivery outputs include:

- checkpoint package
- final handoff package
- Copywriter package
- Developer package
- Project Management package
- manual Notion import project
- deterministic secure ZIP
- manifest and checksums

### 3.12 Diagnostic trace

The minimal diagnostic trace records automated and manual runs in one shared local format. It connects visible action, API request, Transition result, event, canonical readback, last success and first failure. It is Evidence only and never state authority.

## 4. Integration architecture

### 4.1 First local release

```text
Operator Console
-> Local Operator API
-> explicit production preview and confirmation
-> isolated Hermes heartweb-runtime
-> specialized Step agent and bounded subagents
-> typed Heartweb tools
-> Provider Gateway and Evidence
-> Core validation, Human Gate and workflow transition
-> Delivery Service
-> files, ZIP and manual Notion import
```

The local Hermes Gateway is a required production dependency but is never started automatically by the Console. Live Notion, n8n and a public server are not required for the first controlled output.

### 4.2 Future n8n orchestration

```text
UI trigger
-> n8n
-> typed Core command
-> provider and tool orchestration
-> Core validation and release
-> Delivery
-> Notion project creation
```

n8n owns transport, waiting, retry, notification and scheduling. It does not own workflow state.

### 4.3 Notion handoff

The approved Delivery creates one complete customer implementation project in Notion. Human execution remains there without Core callbacks.

### 4.4 Performance loop

```text
Day 30, 60 or 90
-> released strategy and plan
-> publication registry
-> verified GSC, Ahrefs and applicable local metrics
-> Step 3B
-> versioned adjustment proposal
-> explicit strategy approval
-> future plan and task update in Notion
```

Missing or stale metrics stop the checkpoint. The original plan is not overwritten.

## 5. Persistence and reproducibility

The system guarantees accepted artifact bytes, content hashes, source identities, revisions, approvals and releases. It does not guarantee that a fresh stochastic LLM rerun produces identical wording.

For exact reproduction, use the accepted stored artifact. A rerun produces a new revision.

## 6. Extensibility

The architecture supports:

- new prompt versions
- stronger output contracts
- new providers and tools
- optional customer archetype modules
- new Quality Gates
- additional workflow steps
- server deployment adapters
- semantic retrieval over the document registry

Every semantic extension must preserve versioning, fail-fast behavior, prior run readability and client neutrality.

## 7. Documentation and retrieval

The repository index is deterministic and contains lifecycle and authority metadata. A future semantic retriever must filter by this metadata before similarity ranking.

Read order:

1. `00_admin/ONBOARDING_REFERENCE.md` for the deterministic single-entry snapshot
2. `00_admin/SESSION_BOOTSTRAP.md`
3. `00_admin/PROJECT_STATE.md`
4. active and superseding entries in `00_admin/DECISIONS.md`
5. `00_admin/REPOSITORY_INDEX.md`
6. active plan and exact linked contracts

The generated Onboarding Reference is a navigational snapshot. Project State, active Decisions and the exact source contract remain authoritative when any embedded block is older than its source.

Historical and superseded files remain available but are excluded from default retrieval.

## 8. Current and planned capability

### Implemented in the current repository baseline

- V2 Core, workflow and transitions
- Context Packages and LLM records
- specialized Hermes Step agents, Worker Profiles and Tool Policies for Steps 0 through 4B
- persistent Production Executions with bounded continuation, retry and re-steering
- multi-location Search Deployment, Provider Target and planning-capacity bindings
- typed Heartweb tools, Provider Gateway operations and persisted Evidence
- artifacts, revisions, gates, approvals and releases
- Operator API and German Console
- browser-tested release-critical actions
- deterministic Delivery API, Delivery Center, role packages, manual Notion import and secure ZIPs
- shared local diagnostic trace
- locally restored PQ-0, PQ-1, PQ-2 and PQ-4 output quality

### Current acceptance evidence and limits

- The real CL pilot has a reviewed, approved, completed and released Step-0 Manifest V2 Revision 3.
- Step 1 Run `run-next-7f7e2b778f4521b9` is `in_progress` without Production Execution, Agent Evidence or LLM output.
- The complete real route through Step 4B, all Human Gates, final Delivery package and professional operator review are not yet proven.
- Repository consolidation under DEC-0031 does not change PT-03, PT-11, M10 or Production Acceptance status.

### Pre-release remaining

- produce Step 1 through the canonical Hermes and Provider Gateway route
- continue 1B, 1C, 2, 3, 4A and 4B with real required Evidence and fail-fast behavior
- perform every required Human Gate and revision decision
- generate, extract and inspect the final Delivery package
- complete the real-project Golden Path and explicit M10 acceptance

### Post-release

- live Notion and n8n
- complete Step 3B before the first day-30 checkpoint
- public deployment adapters
- broad archetype and international expansion
- additional mobile and presentation work

## 9. Non-goals

- no second state engine in Notion or n8n
- no automatic final Copywriter output
- no silent metric or claim estimation
- no AHD-specific shared product logic
- no requirement for a vector database
- no live deployment before explicit approval
````

### Source: [`docs/09-extension-and-evolution-guide.md`](../docs/09-extension-and-evolution-guide.md)

- Lifecycle: `current_authority`
- Authority: 90
- SHA-256: `6b61a24d634273c4ffed52b734641ac4ca8888102285e353e0aee1418e089ede`

````text
# Heartweb extension and evolution guide

**Author:** Raphael Rechberger
**Status:** Current extension authority
**Updated:** 2026-08-26

## 1. Goal

Heartweb is designed to evolve without losing old results, customer separation or workflow integrity. Extensions are versioned and activated deliberately. Existing accepted runs remain bound to the versions that produced them.

## 2. Freedom and constraints

LLMs retain freedom for:

- strategic interpretation
- topic and cluster development
- information-gap analysis
- page structure and comparison concepts
- briefing language and recommendations
- evidence-grounded prioritization

LLMs do not control:

- customer or project identity
- workflow state
- revisions and hashes
- Human Gates
- provider market binding
- missing metrics
- unsupported claims
- releases and publication status

Contracts are guardrails and acceptance filters. They do not replace prompt quality, real data or human judgment.

## 3. Change a prompt

A semantic prompt change follows this sequence:

1. create a new prompt version
2. document the intended output difference
3. compare against the preserved baseline requirement matrix
4. update the expected output schema if meaning or structure changes
5. update validator and renderer
6. update Quality Gate rules
7. add positive and negative fixtures
8. update Context Package and tool policy
9. run behavioral comparison against representative fixtures
10. activate only for new runs or an explicit migration

Never replace accepted prompt bytes silently.

## 4. Change an output contract

Contract changes use a new schema version when they alter required fields, meaning, allowed values or validation behavior.

A contract migration must define:

- old version
- new version
- compatible read behavior
- activation rule
- whether old artifacts remain valid
- whether a rerun is required
- negative cases that must fail

Do not add optional fields that silently become required in downstream code.

## 5. Add or replace a provider

Use a provider adapter behind Provider Gateway.

The adapter must define:

- capability
- request schema
- required market, location and language fields
- asynchronous or synchronous execution behavior
- normalized result schema
- raw-response Evidence and hash
- timeout, quota and error mapping
- retry policy
- unsupported capability behavior

Provider failure must not produce estimated values or an automatic fallback with different semantics.

## 6. Add a tool

Classify the tool as:

- deterministic validator or solver
- external data provider
- renderer
- file transformer
- deployment adapter

Define exact inputs, outputs, errors, side effects and Evidence. Add the tool to a step Tool Policy only after contract and failure tests pass.

## 7. Add a workflow step

A new step requires:

1. stable step ID
2. workflow-graph transition
3. predecessor and successor rules
4. prompt or deterministic executor
5. Context Package rule
6. output contract
7. renderer
8. machine Quality Gate
9. Human Gate decision
10. artifact and revision behavior
11. Operator API command and read model
12. Console action and state
13. Delivery mapping
14. tests and real acceptance evidence

A new step must not duplicate behavior that belongs inside an existing step or Notion implementation work.

## 8. Customer-specific customization

Prefer typed Project V2 configuration over prompt forks.

Customer-specific inputs include:

- sector and services
- target audience
- countries, regions and service areas
- language and tone
- business objectives
- design tokens
- claims and Evidence
- risk and compliance profile
- content types
- provider availability

If a new customer archetype requires reusable behavior, add a client-neutral optional module with an explicit activation condition. Do not embed the first customer's content into shared logic.

## 9. Quality preservation

Every extension is checked against:

- original approved quality requirements
- current schema and validator behavior
- representative positive and negative fixtures
- customer-neutral archetypes
- real output usefulness
- no regression in tenant, revision, Evidence or transition safety

A structurally valid but professionally thin result is not accepted.

## 10. Reruns and migrations

A rerun creates a new artifact revision. It uses:

- exact active prompt version
- released predecessor artifacts
- Project V2
- current permitted Evidence
- rejected artifact and findings when applicable
- immutable field policy
- expected schema version

Do not rewrite an accepted artifact in place.

## 11. Documentation update contract

A semantic change must update:

- `00_admin/PROJECT_STATE.md`
- active or superseded entry in `00_admin/DECISIONS.md`
- relevant active plan
- AGENTS and CLAUDE only when a global agent rule changes
- README when user-visible architecture or capability changes
- current architecture or integration documents
- authority overrides and generated registry
- `00_admin/ONBOARDING_REFERENCE.md` only through the deterministic repository-index generator

Then run:

```text
python scripts/build_repository_index.py
python scripts/build_repository_index.py --check
python -m unittest tests.test_repository_index -v
```

## 12. Retrieval and RAG integration

A future retriever consumes `DOCUMENT_REGISTRY.jsonl`.

Required order:

1. filter by lifecycle
2. filter by workflow step, audience and task area
3. prefer authority level and retrieval priority
4. apply semantic ranking
5. include historical Evidence only for explicit historical or audit requests

Never let embedding similarity override Project State, Decisions, schema versions or supersession metadata.

## 13. Release gate

An extension is ready only when:

- implementation and contracts match
- generated clients show no drift
- affected tests pass
- negative behavior is proven
- documentation and registry are current
- no open P0/P1 remains
- a real or representative output demonstrates the intended value
- Raphael explicitly approves commit, merge or deployment where required
````

### Source: [`00_admin/DEFERRED_INTEGRATION_BACKLOG.md`](../00_admin/DEFERRED_INTEGRATION_BACKLOG.md)

- Lifecycle: `current_strategy`
- Authority: 88
- SHA-256: `79c96f69f158221665b23582e2ef3e1f81dedd2fb6fbb696f1e1b7caea72e13e`

````text
# Deferred Change and Integration Backlog

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Created:** 2026-08-20
**Status:** Active capture log
**Canonical file:** `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`

## Purpose

This file is the canonical intake for findings, problems, UI feedback, SEO and GEO improvements, integration needs, and quality refinements discovered while the current base system is being completed.

Capturing an item here does not authorize immediate implementation. The current base workflow must first be completed, independently verified, and proven stable. Backlog items are then triaged and implemented coherently in a dedicated integration sprint.

## Protected Current Scope

This backlog does not defer or replace requirements that are already part of the active base implementation.

Current binding sources remain:

- `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- `.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md`
- `.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md`
- `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
- `standards/workflow/workflow-graph.json`
- `standards/quality/quality-gate-registry.json`

Examples of active scope that must not be demoted to this backlog:

- real local workflow from Step 0 through Step 4b
- German single-admin Operator Console
- artifact content readback, editing, revisions, comparison, validation, approval, rejection, and rerun
- deterministic delivery packages and exports
- final task-based browser QA and completion audit
- deterministic manual Notion import and complete task matrix for the first local release; live one-way project creation remains PR-003 and does not block M10

## Activation Gate

Backlog implementation starts only when all of the following are true:

1. The current Sprint 5 and Sprint 5E base implementation is complete.
2. The local Step-0-through-Step-4b Golden Path is independently verified.
3. The German single-admin interface passes task-based QA.
4. Delivery and export paths pass deterministic and security verification.
5. There are no open P0 or P1 base defects.
6. Raphael explicitly authorizes the integration sprint.

## Intake Rules

1. Record findings immediately, but do not silently implement them.
2. Preserve Raphael's intent and wording in the source note.
3. Link every item to concrete files, sessions, screenshots, or observed behavior when available.
4. Separate defects from enhancements and strategic changes.
5. Do not create a second workflow state authority or duplicate an existing contract.
6. Prefer extending existing schemas, services, UI workspaces, and gates.
7. Mark conflicts and supersession explicitly.
8. A backlog item is not complete until its acceptance criteria are verified.
9. Current production blockers remain in `PROJECT_STATE.md`; this backlog is not a place to hide active blockers.
10. Secrets, credentials, and raw tokens must never be copied into this file.

## Status Lifecycle

- `captured`: Recorded but not yet analyzed.
- `triaged`: Scope, dependencies, and affected architecture identified.
- `approved_for_integration`: Raphael approved implementation in the integration sprint.
- `in_progress`: Implementation has started.
- `verification`: Implementation exists and is undergoing independent verification.
- `verified`: Acceptance criteria are proven.
- `rejected`: Deliberately not implemented, with rationale.
- `superseded`: Replaced by another backlog item or decision.

## Categories

- `SEO_GEO_QUALITY`
- `UI_UX`
- `WORKFLOW`
- `COPYWRITER_HANDOFF`
- `DEVELOPER_HANDOFF`
- `NOTION`
- `N8N`
- `PROVIDER`
- `DELIVERY_EXPORT`
- `MEASUREMENT_PERFORMANCE`
- `SECURITY_RELIABILITY`
- `DOCUMENTATION`
- `REPOSITORY_HYGIENE`
- `OBSERVABILITY_DIAGNOSTICS`
- `PROMPT_OUTPUT_QUALITY`

## Priority

- `P0`: Active production or data-integrity emergency. Must not wait in this backlog.
- `P1`: Blocks the accepted base product. Promote to current blocker.
- `P2`: Mandatory integration-sprint requirement.
- `P3`: Valuable enhancement.
- `P4`: Optional idea or experiment.

## Backlog Index

| ID | Category | Title | Priority | Status | Activation | Detail |
|---|---|---|---|---|---|---|
| DIB-001 | SEO_GEO_QUALITY | Restore approved GEO requirements to V2 Step 4a and 4b contracts | P1 | verification | Local contract and renderer restoration complete; real output proof remains in M10 | `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` |
| DIB-002 | DOCUMENTATION | Reconcile AGENTS, CLAUDE and README with the V2 runtime and product architecture | P2 | verified | Entry documents align with active V2 and DEC-0031 authority | `AGENTS.md`, `CLAUDE.md`, `README.md` |
| DIB-003 | DOCUMENTATION | Classify and reconcile the complete docs corpus | P2 | verified | All 18 registry entries classified and documentation QA passed | `docs/` |
| DIB-004 | REPOSITORY_HYGIENE | Execute repository hygiene and legacy cleanup from the full tree audit | P2 | triaged | Post-release at a stable checkpoint | `00_admin/audits/2026-08-21-repository-hygiene/` |
| DIB-005 | OBSERVABILITY_DIAGNOSTICS | Add a shared local diagnostic trace and timestamped run history | P2 | verified | Implemented and evidenced under M07 | `00_admin/audits/2026-08-22-m07-diagnostic-trace/` |
| DIB-006 | PROMPT_OUTPUT_QUALITY | Restore only release-critical Promptworkflow quality before first production | P1 | verification | Local PQ-0, PQ-1, PQ-2 and PQ-4 closure complete; real-output proof remains in M10 | `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md` |
| DIB-007 | SECURITY_RELIABILITY | Make local Operator Console process ownership and shutdown unambiguous | P3 | captured | Post-consolidation lifecycle hardening unless it blocks M10 | `scripts/start_operator_console.py`, local PID record and Windows launcher behavior |

## DIB-001: Restore approved GEO requirements to V2 Step 4a and 4b contracts

- **Status:** `verification`
- **Priority:** `P1`
- **Category:** `SEO_GEO_QUALITY`
- **Captured:** 2026-08-20
- **Source:** Session `20260817_151731_bc9488`, ADR-011, repository comparison on 2026-08-20
- **Problem:** The GEO architecture remains present, but concrete approved Copywriter and Developer quality requirements are not fully enforced by the current executable V2 Step-4a and Step-4b schemas, prompts, validators, and renderers.
- **Required outcome:** Restore the Hero Direct Answer, Semantic Triples, Evidence Containers, evidence-bearing data points, definitive-language guidance, enhanced entity bindings, semantic sections, GEO markup, and related admin review functions without replacing the current workflow architecture.
- **Detailed plan:** `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`
- **Dependencies:** Stable base workflow, stable admin interface, stable artifact review and revision surfaces.
- **Current evidence:** Local typed contracts, validators, renderers, gates and Console review were restored under M08 PQ-4. The item remains in `verification` until a real M10 output proves the professional Copywriter and Developer result.
- **Acceptance:** Defined in the detailed plan and requires a real controlled-project quality proof.

## DIB-002: Reconcile AGENTS, CLAUDE and README with the V2 runtime and product architecture

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `DOCUMENTATION`
- **Captured:** 2026-08-21
- **Source:** Raphael observation and repository verification on 2026-08-21
- **Current behavior:** AGENTS, CLAUDE, README, CHANGELOG, current architecture and generated onboarding reflect the V2 runtime and active DEC-0031 authority. The superseded DEC-0022 merge-timing sentence was replaced through the protected-file consent gate.
- **Problem:** Resolved. Entry documents no longer preserve an active pre-V2 or superseded merge-timing claim.
- **Expected outcome:** Update all three documents from verified repository facts, preserve stable global rules, separate current implementation from planned or simulated capability, add accurate navigation, and remove obsolete commands or architectural claims.
- **Affected workflow steps:** Repository onboarding, every agent session, product presentation, final handoff, branch consolidation.
- **Affected files or services:** `AGENTS.md`, `CLAUDE.md`, `README.md`, linked project-state, decision, architecture, integration, UI, and delivery documents.
- **Dependencies:** Promoted into the DEC-0031 master consolidation from the stable M09 and current M10 implementation state.
- **Risks and conflicts:** Updating too early can create repeated churn. Waiting beyond the Final-Gate would publish misleading agent instructions and public documentation.
- **Acceptance criteria:** Current architecture and commands are factually correct; implemented, simulated, planned, and deferred capabilities are distinguished; all primary links resolve; no obsolete v1.2 or no-CLI claims remain; documentation review passes before `master` fast-forward.
- **Resolution Evidence:** Protected AGENTS edit approved by Raphael on 2026-08-26; `00_admin/ONBOARDING_REFERENCE.md`; `python -m unittest tests.test_repository_index`; `hermes verify --json`.
- **Supersedes:** none
- **Superseded by:** none

## DIB-003: Classify and reconcile the complete docs corpus

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `DOCUMENTATION`
- **Captured:** 2026-08-21
- **Source:** Raphael observation and complete `docs/` inventory on 2026-08-21
- **Current behavior:** All 18 registered `docs/` records are explicitly classified. Current authorities were reconciled, historical and superseded Markdown files have visible lifecycle labels, the historical HTML map has a visible banner, and the two Evidence PDFs remain immutable and opt-in.
- **Problem:** Several files still claim direct AgentSEO operation, Solver v1.2, a missing JSON-LD CLI, seven prose gates, manual Claude Desktop prompt execution, manifest status authority, direct Notion MCP writes, or full production readiness. These claims conflict with the current V2 Core, Provider Gateway, Transition Service, machine/human gate registry, single-admin Console, Delivery plan, and open completion gates.
- **Expected outcome:** Classify every file as current authority, current strategy, historical baseline, superseded plan, external handoff, or generated artifact. Update current documents, add explicit supersession headers to historical sources, regenerate or archive stale PDFs, preserve evidence history, and create one accurate cross-linked docs index.
- **Affected workflow steps:** Repository onboarding, external review, Jesse presentation, operator training, Copywriter and Developer handoff, final release.
- **Affected files or services:** All 18 registered `docs/` sources, README navigation, generated lifecycle indexes and canonical state/decision links.
- **Dependencies:** Promoted into the DEC-0031 master consolidation; current runtime, Delivery and integration boundaries are defined by active Decisions and the Production Architecture.
- **Risks and conflicts:** Deleting historical evidence would damage traceability. Leaving old files unlabeled would mislead agents, auditors, Jesse, and future operators.
- **Acceptance criteria:** Every docs file has an explicit lifecycle classification; current operational claims match tested behavior; superseded plans are clearly labeled and excluded from current setup instructions; PDFs match their canonical source or are archived; all links resolve; documentation QA passes before `master` fast-forward.
- **Resolution Evidence:** `00_admin/audits/2026-08-26-repository-consolidation/DOCUMENT_LIFECYCLE_RECONCILIATION.md`; `00_admin/ONBOARDING_REFERENCE.md`; `python -m unittest tests.test_repository_index` with 16 of 16 tests passing.
- **Supersedes:** none
- **Superseded by:** none

## DIB-004: Execute repository hygiene and legacy cleanup from the full tree audit

- **Status:** `triaged`
- **Priority:** `P2`
- **Category:** `REPOSITORY_HYGIENE`
- **Captured:** 2026-08-21
- **Source:** `00_admin/audits/2026-08-21-repository-hygiene/REPOSITORY_HYGIENE_AND_AUTHORITY_AUDIT.md`
- **Current behavior:** The active core coexists with a 21.4 MB stale native binding, a stale preview PID, one exact duplicate 1.17 MB plan image, 16 production-unreachable files from the rejected demo UI, three legacy direct-AgentSEO contracts, historical generators, mixed-lifecycle plans, and unindexed audit evidence.
- **Problem:** These items increase project-tree noise, confuse source authority, and can be accidentally committed or presented as current functionality. Deleting them during active browser or delivery work could still remove useful evidence or a hidden dependency.
- **Expected outcome:** After the active gates, prove each candidate unused, remove or archive it deliberately, preserve immutable audit/checkpoint history, add plan/docs/audit indexes, reconcile CHANGELOG and entry documents, and leave a clean final repository tree.
- **Affected workflow steps:** Browser QA, Sprint 5E Delivery, final audit, documentation QA, final branch consolidation.
- **Affected files or services:** `.gitignore`, `apps/operator-console/src/dev`, `apps/operator-console/src/features`, `.hermes/plans`, `mcp/tool-contracts`, `scripts`, `00_admin/audits`, `CHANGELOG.md`.
- **Dependencies:** Stable browser evidence, Delivery completion, final TypeScript import graph, final Python/runtime reference sweep, DIB-001 through DIB-003 decisions.
- **Risks and conflicts:** Removing audit history, active fixtures, Package 4 code, or OMO continuation state is prohibited. Cleanup must be path-specific and evidence-backed.
- **Acceptance criteria:** No stale dependency/PID artifacts; no unreachable rejected demo code; one canonical architecture image; legacy contracts and generators classified; current plan/docs/audit indexes present; no secret or path leakage; the affected cleanup dependency closure and applicable release-matrix cells are green; final Git tree and links are verified before `master` fast-forward.
- **Supersedes:** none
- **Superseded by:** none

## DIB-005: Add a shared local diagnostic trace and timestamped run history

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `OBSERVABILITY_DIAGNOSTICS`
- **Captured:** 2026-08-21
- **Source:** Raphael clarification on 2026-08-21. The automated final smoke test and Raphael's later manual operator walkthrough must write the same directly readable diagnostic evidence. Raphael must not export, package, collect, or upload logs for Hermes.
- **Goal:** When either the automated smoke test or Raphael's manual flow encounters an error, missing action, wrong blocker, bottleneck, false success, or later inconsistency, Hermes can immediately read the current or historical local trace, reproduce or verify the problem, and prepare a concrete diagnosis and fix proposal. If implementation is required, Hermes gives root Sisyphus the trace ID and evidence path. Root Sisyphus reads the same files and works from the same facts.
- **Required sequence:** Sprint 5E completes first. The minimal diagnostic trace is then implemented before the Sprint-5 final smoke test and audit. The final automated smoke test must already use it. The same mechanism remains active for Raphael's later manual walkthrough and the real AHD pilot.
- **Minimum implementation:** Write one small structured trace per automated smoke-test or operator run to one stable shared local path that both Hermes on the host and root Sisyphus through the mounted workspace can read directly. Keep an append-only timestamped run index plus a simple `current` pointer to the latest run. Closing a run makes its trace immutable; a retry or later test receives a new trace ID. Use existing event, error, API, and browser evidence instead of adding a new database, service, dashboard, or external observability platform.
- **Minimum trace content:** Run start and end timestamps; ordered event timestamps; trace ID; build/version; tenant, project, run, step, gate, revision, artifact and route when available; expected server-authorized actions; actually rendered, disabled, and missing actions; operator or test action; API method and status; stable error code and remediation; Transition Service result; emitted event reference; canonical readback result; browser console and classified network failure; last successful operation; first failing operation; and screenshot path only when useful.
- **Direct diagnostic workflow:** Raphael reports the approximate step, action, or time of the problem. Hermes reads the `current` trace or searches the timestamped run history by time, project, run, step, action, trace ID, or error code. Hermes verifies the mismatch, compares it with earlier runs when useful, explains the causal chain, and proposes the smallest safe fix. Hermes contacts only root Sisyphus when implementation is needed. No OMO child session is inspected or controlled.
- **Affected workflow steps:** Automated Sprint-5 final smoke test, final audit, Raphael's manual operator walkthrough, real AHD pilot, and all Operator Console actions from intake through Delivery and recovery.
- **Affected files or services:** Existing Operator Console action seam, Operator API, Transition Service, event store, stable error catalog, browser smoke-test harness, and one shared local diagnostic path.
- **Non-goals:** No new observability platform, dashboard, distributed tracing stack, log server, second state store, external telemetry, manual export flow, hidden model reasoning, full prompt capture, or broad instrumentation of every internal development action.
- **Dependencies:** Stable Sprint-5 UI and action surface, Sprint 5E Delivery actions, current event catalog, and stable error routing.
- **Risks and conflicts:** Diagnostic files are evidence only and never change canonical state. They must exclude credentials, tokens, authorization headers, unrestricted customer documents, cross-tenant records, and OMO child-session data. History retention and file size must remain bounded without overwriting or silently rewriting retained closed runs.
- **Acceptance criteria:**
  1. The automated final smoke test creates the shared trace automatically and requires no manual log collection.
  2. Raphael's later manual walkthrough writes the same trace format and updates the stable `current` pointer automatically.
  3. Every closed run remains immutable in a timestamped index; `current` points to the latest run without replacing historical evidence.
  4. Hermes can read the latest or a historical trace directly from the shared workspace and identify the last success, first failure, relevant action, API result, transition/event evidence, and canonical readback.
  5. Root Sisyphus can read the same trace and evidence path when Hermes assigns a verified fix, without any child-session inspection.
  6. An expected-versus-rendered action check identifies an allowed action missing from the UI, an unexpected action, and a disabled action with the wrong or missing blocker reason.
  7. One success, one validation failure, one stale-confirmation conflict, one missing-action mismatch, one server error, one QA-harness error, and one regression between two timestamped runs are reconstructable from the retained traces.
  8. No secrets, unrestricted customer documents, cross-tenant data, hidden reasoning, or external telemetry are recorded.
  9. The implementation remains small, uses existing evidence seams, and keeps the affected diagnostic dependency closure plus applicable prototype-matrix cells green under `standards/testing/PROTOTYPE_TEST_POLICY.md`.
- **Verification evidence:** M07 implementation and real browser/persistence evidence under `00_admin/audits/2026-08-22-m07-diagnostic-trace/`; current trace root `var/operator-diagnostics/v1/` remains gitignored and directly readable.
- **Supersedes:** none
- **Superseded by:** none

## DIB-006: Preserve original Promptworkflow output quality in V2 contracts

- **Status:** `verification`
- **Priority:** `P1`
- **Category:** `PROMPT_OUTPUT_QUALITY`
- **Captured:** 2026-08-21
- **Source:** Raphael approval following `00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md`
- **Behavior at capture:** The V2 migration improved Domain, State, Evidence, Provider, Revision, Gate, and Transition integrity, while several output-critical requirements were incomplete compared with the original Desktop Promptworkflow and master prompt baseline.
- **Current evidence:** PQ-0, PQ-1, PQ-2 and PQ-4 were restored and accepted in their local M08 scope. Typed fields, fixtures, validators, renderers, the Step-2-to-Step-3 solver seam and Console review are present. The item remains in `verification` because real provider-backed Step-2 quality, the complete M10 output chain and professional human review are not yet proven.
- **Problem:** The existing final audit could validate a technically safe but output-thin workflow. The final Heartweb product must preserve the original editorial, SEO, GEO, conversion, planning, presentation, and handoff requirements while keeping the current V2 architecture.
- **Required outcome:** Execute only the release-critical scope from `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`: bounded PQ-0, PQ-1, PQ-2, and PQ-4. Map each original requirement needed for the first production route to one current authority, restore missing typed fields and behavior through existing schemas, validators, renderers, Quality Gates and Admin surfaces, prove the real Step-2-to-Step-3 solver path, and complete DIB-001 for Step 4A and Step 4B. PQ-3 and PQ-5 are post-release.
- **Required sequence:** Do not interrupt the current Browser-QA run or Sprint 5E. After a stable controller-verified Sprint-5E checkpoint, implement DIB-005, then bounded PQ-0, PQ-1, PQ-2, and PQ-4. Run a targeted Production Release audit immediately afterward.
- **Affected workflow steps:** Pre-release: Step 1B, Step 1C, Step 2, Step 3, Step 4A, Step 4B, Delivery handoff, and targeted production smoke. Post-release: Step 3B, real-output parity, broad rollout, and final maturity gate.
- **Dependencies:** Browser QA complete, Sprint 5E complete, stable checkpoint, DIB-005, preserved prompt baseline, and explicit package-by-package verification.
- **Risks and conflicts:** Do not copy old prompts wholesale into production, reintroduce prompt-controlled state, call providers directly, duplicate authorities, or weaken lineage and safety. Original prompts remain immutable requirement sources, not executable production authority.
- **Acceptance criteria:**
  1. PQ-0 classifies every output-critical original requirement as preserved, strengthened, restored, deferred with explicit approval, or not applicable.
  2. Step 1B and Step 1C produce professional customer and developer artifacts matching approved original intent.
  3. A real provider-backed Step-2 artifact supplies the actual deterministic solver with all required metrics and classifications without manual side data.
  4. DIB-001 restores complete Step-4A Copywriter and Step-4B Developer and GEO quality needed for the first output chain.
  5. Positive and negative fixtures fail or pass for the intended quality requirement, not only schema presence.
  6. No existing V2 Domain, State, Provider, Evidence, Revision, Approval, Transition or tenant-isolation invariant regresses.
  7. A targeted Desktop and core-action Production Release audit passes with deterministic Delivery and no open P0/P1.
  8. Step 3B semantics and the full real-output parity audit are recorded in `00_admin/POST_RELEASE_BACKLOG.md` and do not block the first controlled production output.
- **Supersedes:** none
- **Superseded by:** none

## DIB-007: Make local Operator Console process ownership and shutdown unambiguous

- **Status:** `captured`
- **Priority:** `P3`
- **Category:** `SECURITY_RELIABILITY`
- **Captured:** 2026-08-26
- **Source:** Repository-freeze operation on Windows. Closing the browser did not itself prove that the locally started Console and Gateway processes had stopped. A stale PID record remained after the process was already absent.
- **Current behavior:** `scripts/start_operator_console.py` starts a persistent local service and records process metadata outside the repository. Browser-window closure is not the service shutdown authority. The existing fail-closed cleanup correctly refused to remove an unproven PID record until PID and listener absence were verified.
- **Problem:** The lifecycle is technically recoverable but not sufficiently obvious to the single operator. A stale record can look like project corruption even though it contains no project state.
- **Expected outcome:** Provide one explicit start, status and stop path that verifies the process tree and bound ports, removes only proven-stale metadata and reports a structured result. The browser should not be presented as the process owner unless the launcher is deliberately changed to make it one.
- **Non-goals:** Do not couple canonical workflow state to local PIDs, autostart the Hermes Gateway, kill unrelated Python processes, or hide shutdown failures.
- **Acceptance criteria:** Start creates one authoritative record; status distinguishes running, stopped and stale; stop terminates only the recorded process tree; stale cleanup requires process and listener absence; repeated stop is idempotent; Windows launcher tests and a real local smoke pass.
- **Activation:** Post-consolidation lifecycle hardening. Promote into M10 only if the launcher prevents the required operator run.
- **Supersedes:** none
- **Superseded by:** none

## UI and UX Findings Intake

Future UI observations from Raphael are added as individual `DIB-UI-NNN` items. Each item must record:

- exact screen or workflow step
- what the admin is trying to accomplish
- observed problem
- expected behavior
- screenshot or session evidence when available
- affected API or domain command, if any
- whether it is a defect, usability issue, or enhancement
- acceptance scenario from the admin's perspective

UI feedback must not be converted directly into isolated visual patches. It is reviewed against the screen-action map, current workflow authority, and overall information architecture during the integration sprint.

## New Item Template

```markdown
## DIB-NNN: Short title

- **Status:** `captured`
- **Priority:** `P2 | P3 | P4`
- **Category:** `<category>`
- **Captured:** `<YYYY-MM-DD>`
- **Source:** `<session, screenshot, file, user quote, test, or observed behavior>`
- **Current behavior:**
- **Problem or opportunity:**
- **Expected outcome:**
- **Affected workflow steps:**
- **Affected files or services:**
- **Dependencies:**
- **Risks and conflicts:**
- **Acceptance criteria:**
- **Supersedes:** `none | DIB-NNN`
- **Superseded by:** `none | DIB-NNN`
```

## Integration Sprint Procedure

When the activation gate is reached:

1. Review every `captured` and `triaged` item.
2. Remove duplicates by linking and superseding, never by deleting history.
3. Separate mandatory corrections from optional experiments.
4. Map each approved item to existing architecture seams.
5. Define package boundaries and regression tests.
6. Approve the integration-sprint scope with Raphael.
7. Implement one coherent package at a time.
8. Run specification, quality, security, and task-based UI reviews.
9. Update this log with exact evidence and final status.

## Change Log

| Date | Change | Source |
|---|---|---|
| 2026-08-26 | DIB-002 and DIB-003 promoted into DEC-0031 master consolidation; DIB-005 verified; DIB-001 and DIB-006 moved to real-output verification | DEC-0031 and current Project State |
| 2026-08-26 | DIB-007 captured for unambiguous Windows Console process ownership and shutdown | Repository-freeze runtime observation |
| 2026-08-21 | Production-first Cut-Line: DIB-001 and release-critical DIB-006 stay pre-release; Step 3B, real-output parity, integrations, mobile polish, docs and cleanup moved post-release | Raphael decision, DEC-0024 |
| 2026-08-21 | DIB-006 approved for full Promptworkflow quality preservation before the existing final audit | Raphael approval and read-only parity audit |
| 2026-08-21 | DIB-005 approved for a shared directly readable diagnostic trace and timestamped history in automated and manual smoke tests | Raphael request and clarifications |
| 2026-08-21 | DIB-004 registered from complete repository hygiene and authority audit | Raphael request and repository verification |
| 2026-08-21 | DIB-003 registered after complete docs-corpus freshness and authority audit | Raphael observation and repository verification |
| 2026-08-21 | DIB-002 registered for mandatory entry-document reconciliation before final master merge | Raphael observation and repository verification |
| 2026-08-20 | Canonical deferred backlog created and DIB-001 registered | Raphael Rechberger and repository audit |
````

### Source: [`00_admin/POST_RELEASE_BACKLOG.md`](../00_admin/POST_RELEASE_BACKLOG.md)

- Lifecycle: `current_strategy`
- Authority: 87
- SHA-256: `7c745f8009195ff825f2ba7356ed5c34aed7ac1e5dc8a5ccdbf4b7db3cdf56f4`

````text
# Post-Release Backlog

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Created:** 2026-08-21
**Status:** Active non-blocking post-release queue
**Purpose:** Keep valuable work without delaying the first locally production-capable workflow and real customer output.

## Authority Boundary

This file is a scheduling projection, not a second Source of Truth. Detailed requirements remain in the linked Decision, DIB, plan, schema, or audit. If this file conflicts with those sources, the higher-authority source wins.

## First Production Release Definition

The first local Production Release exists when:

1. Desktop and core Operator actions pass targeted browser and functional QA.
2. No open P0 or P1 data-integrity, workflow, security, output-quality, or Delivery defect remains.
3. Sprint 5E produces deterministic checkpoint and handoff packages.
4. DIB-005 provides the minimal shared timestamped diagnostic trace.
5. The output-critical pre-release part of DIB-006 is verified for Step 1B/1C, Step 2/3, and Step 4A/4B.
6. One targeted production smoke test passes with the local Core and manual file handoff.
7. Live Notion, live n8n, public deployment, and perfect mobile polish are not required.

## Post-Release Queue

| ID | Work | Source authority | Activation | Why it does not block first Production Release |
|---|---|---|---|---|
| PR-001 | Full Step-3B performance semantics | DIB-006 PQ-3, original Step-3B prompt | Before the first real day-30 checkpoint | Initial production route marks Step 3B `not_due`; no real performance data exists yet. |
| PR-002 | Full real-output parity and PQ-5 acceptance | DIB-006 PQ-5 | Immediately after the first real AHD output chain | Requires real outputs and therefore cannot logically precede the first production run. |
| PR-003 | Live one-way Notion project creation for customer concept, tasks, people, priorities and deadlines | DEC-0025, current Notion operating model | After local production output is stable and target databases are confirmed | Manual Delivery and Notion import pack provide the first release handoff. Daily task callbacks to the Core are out of scope. |
| PR-004 | Live n8n orchestration for concept production, Notion handoff and scheduled Step-3B performance re-entry | DEC-0025, current n8n operating model | After local production and command/event contracts are stable | The local Core already executes without n8n. n8n does not monitor staff-task completion for Core progression. |
| PR-005 | Additional mobile polish and exhaustive mobile-only regression rounds | Operator Experience spec and QA evidence | After first release unless a mobile issue corrupts state or blocks a required review action | Desktop is the production surface. Mobile is review/status convenience only. |
| PR-006 | Full docs-corpus classification and historical PDF regeneration | DIB-002, DIB-003 and DEC-0031 | Docs classification and generated onboarding completed on 2026-08-26; historical PDF regeneration remains post-release where source parity is unproven | Current onboarding is verified; historical presentation PDFs do not block M10. |
| PR-007 | Repository hygiene, dead demo code removal, image deduplication and readability cleanup | DIB-004 | After first release at a stable checkpoint | Important maintenance, but not required to generate correct customer outputs. |
| PR-008 | Broad multi-archetype, international and portability expansion | Master plan Sprint 11 and domain fixture matrix | After the first real local Golden Path | The first release needs one proven real Golden Path, not every future archetype. |
| PR-009 | Jesse presentation expansion and complete presentation matrix | Master plan Sprint 10 | After real outputs exist | Presentation must use real production evidence rather than delaying that evidence. |
| PR-010 | CMS, WordPress, Elementor and public deployment adapters | Fundamental audit section 5.5 | Separate explicitly approved deployment phase | First release produces professional Developer files and staging-ready outputs, not a live deployment. |
| PR-011 | General LLM backend platform, direct Multi-Provider adapters, separate execution-record store, delegation contracts and model benchmark framework | DEC-0028 and Hermes Gateway LLM adapter plan | After M10 and only if real runs prove a concrete need | The first release needs one thin validated Hermes Runs adapter, not a speculative provider platform. |

## Blocking Rule

A post-release item returns to the release-blocking queue only if it causes one of the following:

- data corruption or false canonical success;
- illegal workflow transition or stale approval;
- tenant, secret, path or security breach;
- missing or materially weak customer output;
- unusable Desktop operator action;
- nondeterministic or unsafe Delivery package;
- a deadline-specific dependency such as Step 3B before day 30.

Cosmetic mobile behavior, documentation polish, repository tidiness, live integrations, broad archetype coverage, and presentation enhancements remain post-release by default.

## Review Rule

Raphael may promote any item before implementation. Otherwise the queue is reviewed after the first real AHD output package and again before the first day-30 performance checkpoint.

Live-integration implementation must preserve the DEC-0025 boundary: one complete project handoff to Notion, Notion-owned human execution, and Core re-entry only for the scheduled Step-3B performance cycle.
````

### Source: [`.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md`](../.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md)

- Lifecycle: `active_plan`
- Authority: 95
- SHA-256: `a6d29f7892f4518a1b1ac0018ead783dc68754ea0230cb48420070b60660b629`

````text
---
title: "Heartweb Repository Authority, Master Consolidation and Fresh Clone"
summary: "Architecture and execution plan for repository-wide documentation, prompt, agent and information reconciliation, safe master integration, verified branch retirement, a deterministic one-file onboarding reference and a fresh continuation clone."
created_at: "2026-08-25T22:56:54-04:00"
status: "proposed"
author: "Raphael Rechberger"
---

# Heartweb Repository Authority, Master Consolidation and Fresh Clone Implementation Plan

> **For implementation:** Use only the execution path authorized by Raphael and the project rules. If OpenCode OMO is used, Hermes briefs only root Sisyphus and independently verifies results. Native `delegate_task` is not authorized. Git integration, push, branch deletion and clone replacement remain explicit controller gates.

**Goal:** Reconcile the complete Heartweb repository without deleting historical context, publish the truthful integrated state to `master`, retire every proven-reconciled non-master branch, replace the current workspace with a verified fresh clone and continue the paused real workflow from a new feature branch.

**Architecture:** Canonical sources remain separate and authoritative. A deterministic generated onboarding compendium provides one complete entry surface without replacing those sources. Documentation and runtime status are reconciled append-only through Project State, Decisions, lifecycle metadata and versioned prompt and agent contracts. Git branches are retired only after their tips are provably reachable from the final `master` graph.

**Tech Stack:** Git and GitHub CLI, Python 3.11, deterministic repository-index generator, JSON Schema, Markdown, FastAPI contracts, React and TypeScript Operator Console, Hermes `heartweb-runtime` Gateway.

---

## 1. Binding outcome

The operation ends with all of the following true:

1. Every current repository authority reflects the actually implemented state as of the consolidation.
2. Historical, superseded, audit and evidence files remain present or are explicitly preserved outside Git when they are local-only. Nothing is silently deleted because it appears stale.
3. Prompt changes obey semantic versioning. Previously accepted prompt versions remain immutable.
4. Every active Step Agent, Worker Profile and Tool Policy is mapped to its exact prompt, model policy, output contract and hash.
5. `00_admin/ONBOARDING_REFERENCE.md` provides one generated onboarding surface with complete source traceability.
6. The final `master` includes all accepted implementation and documentation changes.
7. Every retired branch tip is reachable from final `master` before deletion.
8. A clean clone at the canonical path matches the remote `master` SHA byte-for-byte at the Git tree boundary.
9. A new branch named `feature/production-workflow-continuation` starts from that exact `master` SHA.
10. The existing external CL project and its canonical workflow state survive the repository replacement.
11. Merging to `master` is not described as Production acceptance. The real Step-1 result and later Golden Path cells remain honestly open until executed and reviewed.

## 2. Measured baseline

Read-only inventory captured on 2026-08-25 at 22:56 AST:

| Area | Current fact |
|---|---|
| Repository | `Frater418/claude-desktop-seo-workflow-production` |
| GitHub default branch | `master` |
| Current `master` | `3f980520f049725e8c5a531c6925512ca79c023d` |
| Active local branch | `feature/e2e-operator-workflow-system` at the same commit as `master` |
| Working tree | 112 tracked change entries and 84 untracked files |
| Registry | 327 entries, no missing path and no duplicate path |
| Registry lifecycle | 127 current authority, 8 current strategy, 6 active plans, 173 evidence, 7 historical, 6 superseded |
| Default retrieval | 23 documents |
| Prompt files | 14 |
| Official workflow prompts | 9, including post-publication Step 3B |
| Active initial-route Step Agents | 8 for `0`, `1`, `1b`, `1c`, `2`, `3`, `4a`, `4b` |
| Worker Profiles | 8 |
| Tool Policies | 8 |
| GitHub branch protection | `master` is currently not protected |
| Open PRs | none |
| Merged PRs | PR 1 and PR 2 |
| Real workflow | Step 0 approved and released; Step 1 Run `run-next-7f7e2b778f4521b9` is paused in `in_progress`; no Step-1 provider execution was submitted |

## 3. Authority and supersession architecture

### 3.1 Authority order

The existing order remains binding:

1. latest explicit Raphael instruction
2. `00_admin/PROJECT_STATE.md`
3. active and superseding records in `00_admin/DECISIONS.md`
4. active plans
5. standards and contracts
6. current runtime and tests
7. current integration documents
8. supporting research
9. historical and audit evidence

### 3.2 New decisions required

Append, do not rewrite history:

- `DEC-0031`: Consolidate the truthful current repository state into `master` now. This supersedes only the timing restriction in DEC-0022. It does not declare M10, PT-03, PT-11 or Production acceptance complete.
- `DEC-0032`: Provide a deterministic one-file onboarding compendium while preserving all canonical source files and lifecycle history.

Patch DEC-0022 to `superseded` with `Superseded by: DEC-0031`. Preserve its original context, rationale and evidence.

### 3.3 No false release claim

The consolidated `master` is the integrated development and operational baseline. Documentation must state explicitly:

- implemented behavior
- verified behavior and exact evidence boundary
- currently running or paused behavior
- unverified behavior
- deferred behavior
- absent behavior

The merge must not convert a real Step-1 run without a result into a completed Golden Path claim.

## 4. Known inconsistencies to resolve

| ID | Current source | Conflict | Planned resolution |
|---|---|---|---|
| C-01 | `00_admin/PROJECT_STATE.md` | Says GATE-0 is closed and no Approval or Release exists | Update to the verified Step-0 release and Step-1 `in_progress` state |
| C-02 | DEC-0022 | Prohibits master integration before Final-Gate | Supersede timing through DEC-0031, while preserving open Production gates |
| C-03 | `README.md` | Still lists Delivery, diagnostics and output restoration as incomplete | Reconcile against current implementation and latest verified boundaries |
| C-04 | generated `SESSION_BOOTSTRAP.md` | Describes a parallel WIP index and stable Feature integration that has already occurred | Replace branch-specific prose with neutral source-snapshot and onboarding rules |
| C-05 | Prompt inventory | 14 files, 9 official workflow entries and 8 initial-route agents are easy to misread as inconsistent counts | Classify aliases, historical versions, active intake, active workflow prompts and deferred Step 3B explicitly |
| C-06 | `INTEGRATION_CHECKLIST.md` | Refers to the now-merged documentation branch and old WIP base | Mark superseded and point to this plan and DEC-0031 without deletion |
| C-07 | Repository index snapshot | Generated outputs use current `HEAD`, while source edits may still be uncommitted | Use a two-stage commit: authored sources first, generated views second |
| C-08 | Local-only untracked files | `apps/operator-console/.env.production` and `00_admin/session-recovery/` are not safely classified for Git | Preserve in the external snapshot, exclude from staging and add explicit ignore rules without reading secret values |
| C-09 | Central project registries | Still describe Delivery and the real run as open at an older checkpoint | Refresh status pointers after the new clone is verified |
| C-10 | GitHub master | Default branch is unprotected | Decide after consolidation whether to enable protection; do not change it silently |

Any newly discovered conflict with two plausible current meanings becomes a blocking question for Raphael. Historical material is never silently rewritten into the new meaning.

## 5. One-file onboarding architecture

### 5.1 Generated target

Create:

- `00_admin/ONBOARDING_REFERENCE.md`

Generate it through:

- `scripts/build_repository_index.py`

Add it to `GENERATED_PATHS`, so it is not recursively indexed as its own source.

### 5.2 Content contract

The file contains, in this order:

1. snapshot identity and generator version
2. authority order and conflict rule
3. product purpose and hard boundaries
4. truthful current status and next gate
5. workflow `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b -> Delivery`
6. separate Step-3B day-30, day-60 and day-90 boundary
7. Core, Console, Provider Gateway, Hermes Gateway, Delivery, Notion and n8n architecture
8. implemented, verified, unverified, planned, deferred and absent capability tables
9. Git, authorship, safety, customer-separation and testing rules
10. verbatim source sections for all current onboarding-critical Default-Retrieval authorities, each headed by source path, lifecycle, authority level and SHA-256
11. complete prompt catalog for all 14 prompt files, with active, alias, historical or deferred classification
12. full active workflow prompt registry map for all 9 registered steps
13. full active Step-Agent map for all 8 initial-route agents
14. Worker Profile and Tool Policy versions, paths and hashes
15. schema, validator, renderer, gate and fixture evolution rules
16. exact local startup, health, verification and recovery entry points without credentials
17. complete inventory row for every registry entry, including path, lifecycle, authority, type, summary and hash
18. branch and fresh-clone continuation point

Every registry entry appears in the final inventory. Raw bodies of the 173 audit and evidence records remain at their canonical paths instead of being duplicated into the onboarding file. This keeps the file usable while omitting no source from discovery.

### 5.3 Source-of-truth warning

The generated file begins with:

- it is a generated onboarding view
- it never overrides Project State, active Decisions or source contracts
- source blocks are identified and hashed
- any drift makes `build_repository_index.py --check` fail

### 5.4 Generator and test files

Modify:

- `scripts/build_repository_index.py`
- `tests/test_repository_index.py`
- `00_admin/repository-index/source-policy.json`
- `00_admin/repository-index/authority-overrides.json`
- `standards/documentation/document-registry.schema.json` only if an additive field is genuinely required

Regenerate:

- `00_admin/ONBOARDING_REFERENCE.md`
- `00_admin/REPOSITORY_INDEX.md`
- `00_admin/SESSION_BOOTSTRAP.md`
- `00_admin/repository-index/DOCUMENT_REGISTRY.json`
- `00_admin/repository-index/DOCUMENT_REGISTRY.jsonl`
- `docs/INDEX.md`
- `.hermes/plans/INDEX.md`
- `00_admin/audits/INDEX.md`
- `03_research/INDEX.md`

## 6. Complete repository reconciliation scope

### 6.1 Governance and entry documents

Update from verified facts:

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `CHANGELOG.md`
- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `00_admin/MASTER_TASK_MATRIX.md`
- `00_admin/MASTER_TASK_MATRIX.json`
- `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
- `00_admin/POST_RELEASE_BACKLOG.md`
- `00_admin/repository-index/INTEGRATION_CHECKLIST.md`

DIB-002 and DIB-003 move to completed only after their acceptance criteria are verified. DIB-004 remains partially open unless every cleanup candidate is separately proven safe. No broad cleanup is inferred from this consolidation.

### 6.2 Documentation corpus

Reconcile all 18 indexed `docs` records:

- update current authorities and current strategy documents
- add visible lifecycle banners to historical and superseded Markdown
- preserve old facts as historical facts
- keep PDFs as evidence unless their source and intended current status are proven
- never regenerate or replace a PDF merely because its prose is old
- verify all relative links and source relationships

Primary current documents include:

- `docs/00-current-production-architecture.md`
- `docs/09-extension-and-evolution-guide.md`
- `docs/07-geo-architecture-specification.md`
- `docs/copywriter-handoff-guidelines.md`
- `docs/integrations/notion-operating-model.md`
- `docs/integrations/n8n-orchestration-model.md`

### 6.3 Prompts

Audit all 14 files under `prompts/`.

Rules:

1. Never silently overwrite a prompt whose meaning was used by an accepted run.
2. Alias files may point to the current active version only when their role is explicit.
3. Historical versions such as Step-0 v1.9.0 and Intake v1.2.0 remain present and inactive.
4. Active Step-0 v1.10.0 and Intake v1.3.0 retain exact version identity.
5. A semantic change requires a new prompt version plus coordinated schema, validator, renderer, Quality Gate, fixtures, Context Package and activation review.
6. Documentation-only corrections inside executable prompts still require hash and registry review.
7. Step 3B remains a registered post-publication prompt but is not presented as an active initial-route Step Agent.

Likely synchronized files:

- `standards/runtime/official-prompt-registry.json`
- `tests/contracts/test_llm_runtime_contracts.py`
- `tests/contracts/test_output_contracts_v2.py`
- direct step contract and renderer tests named by the affected prompt

### 6.4 Agents

Audit every entry and referenced file:

- `standards/runtime/step-agent-registry.json`
- `standards/runtime/step-agent-registry.schema.json`
- `standards/runtime/worker-profiles/step-0-agent.json` through `step-4b-agent.json`
- `standards/runtime/tool-policies/step-0-agent.json` through `step-4b-agent.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/agent-tool-policy.schema.json`
- `standards/runtime/step-agent-output-envelope.schema.json`

For each of the eight agents, verify:

- unique Step ID
- active prompt ID, path, version and hash
- Worker Profile ID, version and hash
- Tool Policy ID, version and hash
- model and reasoning policy
- allowed tool and provider operations
- confirmation and cost boundary
- output contract set
- max interaction rounds
- fail-fast behavior
- Evidence and revision binding

Any semantic agent change creates a new version. Do not rewrite accepted contract meaning in place.

### 6.5 Information, standards and tests

Use the 327-entry registry as the exhaustive inventory. Reclassify every new or changed item. Do not use filesystem similarity as authority. Update standards only when implementation and tests prove the new meaning.

The consolidation must also classify all 112 tracked changes and 84 untracked files into:

- accepted implementation
- accepted authored documentation
- deterministic generated output
- immutable evidence
- local-only runtime or session material
- sensitive or environment-specific material
- unresolved item requiring Raphael

No `git add -A` or blind whole-tree staging is permitted.

## 7. Branch reconciliation design

### 7.1 Current branch table

| Branch or ref | Tip | Unique relative to current master | Required disposition |
|---|---|---:|---|
| `master` | `3f98052` | target | Advance to final consolidation commit |
| `feature/e2e-operator-workflow-system` | `3f98052` plus dirty worktree | 0 committed | Commit accepted current work, then fast-forward master |
| `docs/repository-authority-index-2026-08-22` | `47ffdf9` | 0 | Remove clean worktree and delete local branch after final verification |
| `feature/geo-enhancement-v1.4` | `18cdd66` | 0 | Already merged through PR 2, delete local branch |
| `origin/fix/schritt-2-und-doku-1.3.0` | `aa11097` | 0 | Already merged through PR 1, delete remote branch |
| `origin/wip/sprint5-operator-console-2026-08-21-0809` | `7c844ba` | 0 | Already reachable, delete remote branch |
| `wip/m08-output-quality-2026-08-23` | `568bb49` | 1 | Semantic reconciliation required before graph merge and deletion |

### 7.2 M08 unique-commit rule

Create evidence:

- `00_admin/audits/2026-08-25-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`

For commit `568bb497e57af4f7ec6dc8a13438681bbf423a55`, classify every changed path as:

- present identically
- present in a newer implementation
- intentionally superseded with authority link
- still uniquely valuable and must be integrated
- unresolved

If any uniquely valuable current behavior is missing, integrate it explicitly and verify its affected closure. If all value is present or superseded, record that proof and use a documented no-tree-change merge such as `git merge --no-ff -s ours wip/m08-output-quality-2026-08-23`. This makes the branch tip reachable without reintroducing its older tree. If meaning remains ambiguous, stop and ask Raphael before the merge.

### 7.3 Deletion rule

Before every deletion:

```bash
git merge-base --is-ancestor <branch-tip> master
```

Expected: exit code 0.

Use normal deletion, not force deletion:

```bash
git branch -d <local-branch>
git push origin --delete <remote-branch>
```

If `git branch -d` refuses, stop. Do not substitute `-D` without a new exact proof and explicit Raphael decision.

## 8. Execution plan

### Task 1: Freeze mutable runtime and capture a recovery snapshot

**Objective:** Prevent repository writes during consolidation and preserve a rollback source.

**Actions:**

1. Read canonical CL run, artifact, approval and release state.
2. Stop Operator Console and `heartweb-runtime` gracefully after readback.
3. Verify no repository-writing process remains.
4. Create a dated external snapshot under `C:/Users/offic/Documents/Projekte/Hermes/90_archive/project-snapshots/Heartweb-Claude-Desktop-SEO-Workflow/`.
5. Preserve the full dirty repository, local-only files and Git metadata without publishing secrets.
6. Verify snapshot file count and a manifest of safe hashes.

**Hard stop:** Snapshot verification failure.

### Task 2: Classify the complete dirty tree

**Objective:** Decide explicitly what enters Git.

**Actions:**

1. Export exact tracked and untracked path lists.
2. Review each top-level package against implementation, tests and registry authority.
3. Exclude `apps/operator-console/.env.production` without reading or printing values.
4. Exclude raw `00_admin/session-recovery/` exports from Git while preserving them in the external snapshot.
5. Add precise `.gitignore` rules for environment and raw recovery material.
6. Create an explicit staging allowlist.
7. Ask Raphael about any path whose intent remains ambiguous.

### Task 3: Reconcile the M08 unique commit

**Objective:** Preserve every unique branch contribution without restoring stale tree state.

**Actions:**

1. Compare the M08 commit against final current sources path by path.
2. Write the branch reconciliation report.
3. Integrate any missing current value with focused verification.
4. Record supersession evidence for older alternatives.
5. Stop for unresolved meaning.
6. Only then create the graph merge that makes the M08 tip reachable.

### Task 4: Reconcile Project State, Decisions and release truth

**Objective:** Establish one truthful current authority before editing lower-level docs.

**Files:**

- `00_admin/PROJECT_STATE.md`
- `00_admin/DECISIONS.md`
- `00_admin/MASTER_TASK_MATRIX.md`
- `00_admin/MASTER_TASK_MATRIX.json`
- `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`
- `00_admin/POST_RELEASE_BACKLOG.md`

**Actions:**

1. Append DEC-0031 and DEC-0032.
2. Supersede DEC-0022 timing without deleting it.
3. Record Step-0 release and paused Step-1 state.
4. Separate repository integration from Production acceptance.
5. Reconcile DIB-002 and DIB-003 only when their acceptance criteria are met.
6. Preserve DIB-004 cleanup candidates unless individually proven.

### Task 5: Reconcile every entry document and docs record

**Objective:** Make public, operator and agent documentation agree with current authority.

**Actions:**

1. Update `AGENTS.md`, `CLAUDE.md`, `README.md` and `CHANGELOG.md`.
2. Update all current docs authorities and strategies.
3. Add or correct visible lifecycle banners on historical and superseded docs.
4. Preserve old details as historical, not current.
5. Verify every docs file has a registry classification.
6. Preserve PDFs unless a separate source-linked regeneration is proven necessary.

### Task 6: Reconcile all prompts

**Objective:** Align executable instructions and prompt metadata without breaking reproducibility.

**Actions:**

1. Build a 14-file prompt lifecycle matrix.
2. Verify all 9 official registry entries and hashes.
3. Verify Intake v1.3.0 and its historical v1.2.0 predecessor.
4. Verify Step-0 v1.10.0 and historical v1.9.0.
5. Make aliases explicit.
6. For every semantic mismatch, create a new version instead of overwriting.
7. Update immediate contracts, validators, renderers, gates and fixtures only when semantics change.
8. Run the directly affected prompt dependency closure.

### Task 7: Reconcile all Step Agents

**Objective:** Make each active agent contract reproducible and documented.

**Actions:**

1. Validate registry, Worker Profiles and Tool Policies against schemas.
2. Recompute and verify record hashes.
3. Verify prompt and output-contract cross-bindings.
4. Verify Tool Policy operations against MCP and Provider Gateway implementations.
5. Verify Step 3B is clearly post-publication and outside the initial eight-agent route.
6. Version any semantic correction.
7. Run agent registry, tool identity, scope, failure envelope, Evidence and deterministic hash tests.

### Task 8: Implement the deterministic onboarding compendium

**Objective:** Provide one reliable new-session file without creating a competing authority.

**Actions:**

1. Add `00_admin/ONBOARDING_REFERENCE.md` to generated outputs.
2. Add a deterministic onboarding renderer to `scripts/build_repository_index.py`.
3. Update bootstrap and repository index navigation.
4. Add tests for source order, source hashes, complete inventory, no recursion, no forbidden dashes, no sensitive paths and link resolution.
5. Generate twice and require byte-identical output.

### Task 9: Refresh external project pointers

**Objective:** Keep the central Hermes and Agency Workbench routers accurate without duplicating repo content.

**Files outside this Git repository:**

- `C:/Users/offic/Documents/Projekte/Hermes/04_projects/PROJECT_REGISTRY.md`
- `C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Agency-Workbench/00_admin/PROJECT_REGISTRY.md`

Only update status and canonical pointer. Do not copy repository history into the Workbench.

### Task 10: Focused verification under the binding test policy

**Objective:** Verify the changed dependency closures and release metadata without an unauthorized complete-suite restart.

**Required commands or equivalents:**

```bash
python -m unittest -v tests.test_repository_index
python scripts/build_repository_index.py --check
python -m unittest -v tests.contracts.test_llm_runtime_contracts
python -m unittest -v tests.test_mcp_tool_identity tests.test_agent_tool_call_scope
python -m unittest -v tests.test_step_agent_deterministic_hashes tests.test_step_agent_failure_envelope tests.test_step1_agent_evidence_bundle
npm run build
hermes verify --json
git diff --check
```

Run prompt-specific validator and renderer tests only for prompt semantics that changed. Run the exact affected Operator Console component tests for UI changes already present. Retain earlier green baselines for unrelated areas. Do not run `python tests/run_full_suite.py` without separate explicit authorization.

Additional release checks:

- staged secret and credential scan
- no customer workspace path in Git
- no `.env` file staged
- no raw session export staged
- no Em Dash or En Dash
- generated index drift zero
- all Default-Retrieval links resolve
- all prompt, agent and contract hashes match bytes
- open P0 and P1 list explicit

### Task 11: Commit authored sources, then generated views

**Objective:** Keep the index source commit exact and auditable.

**Sequence:**

1. Verify Git author is Raphael Rechberger.
2. Stage only explicit accepted paths.
3. Commit implementation and authored source changes in focused, reviewable commits.
4. Include the branch reconciliation report and this plan.
5. Run the repository index generator from the final authored-source commit.
6. Commit only generated registry, index, bootstrap and onboarding views in the final metadata commit.
7. Verify generated `source_commit` equals the authored-source parent commit and all source hashes match.

Do not use `git add -A`.

### Task 12: Integrate and push master

**Objective:** Publish the verified truthful baseline.

**Sequence:**

```bash
git switch master
git merge --ff-only feature/e2e-operator-workflow-system
git push origin master
```

If fast-forward fails, stop and inspect. Do not force push or rewrite history.

Verify externally:

```bash
git ls-remote origin refs/heads/master
gh repo view --json defaultBranchRef,url
gh api repos/Frater418/claude-desktop-seo-workflow-production/commits/master
```

The local and remote SHA must match exactly.

### Task 13: Retire all reconciled non-master branches

**Objective:** Leave only verified master before creating the new continuation branch.

**Sequence:**

1. Re-run ancestor proof for every local and remote branch tip.
2. Remove the clean documentation worktree.
3. Delete merged local branches with `git branch -d`.
4. Delete remote branches:
   - `fix/schritt-2-und-doku-1.3.0`
   - `wip/m08-output-quality-2026-08-23`
   - `wip/sprint5-operator-console-2026-08-21-0809`
5. Verify `git ls-remote --heads origin` lists only `refs/heads/master`.
6. Verify no second worktree remains.

### Task 14: Create and verify the fresh clone

**Objective:** Continue from a clean repository while preserving the old dirty source as a rollback artifact.

**Recommended path strategy:**

1. Clone remote master into a temporary sibling folder.
2. Verify clone HEAD equals the remote master SHA.
3. Run `git fsck --full`, `git status --short` and repository-index check.
4. Move the old repository to the dated external snapshot location.
5. Move the verified fresh clone into the unchanged canonical path:
   - `C:/Users/offic/Documents/Projekte/Hermes/04_projects/active/Heartweb-Claude-Desktop-SEO-Workflow`
6. Restore only required local runtime configuration without staging it.
7. Create and push:

```bash
git switch -c feature/production-workflow-continuation
git push -u origin feature/production-workflow-continuation
```

8. Verify the new branch starts exactly at consolidated master.
9. Verify remote now contains exactly `master` and the new continuation branch.

### Task 15: Reattach runtime and resume the real workflow

**Objective:** Continue the existing CL workflow from the fresh codebase without creating a new project or losing canonical state.

**Actions:**

1. Start Operator Console and `heartweb-runtime` from the new clone.
2. Verify health endpoints from current profile configuration rather than hardcoded ports.
3. Read back the external CL project state.
4. Verify Step-0 release still exists.
5. Verify Step-1 Run `run-next-7f7e2b778f4521b9` remains `in_progress` unless canonical state proves otherwise.
6. Verify no provider call was created during consolidation.
7. Resume Step-1 production only after the normal production and tool approval gate.

## 9. Verification and acceptance matrix

The consolidation is accepted only when:

- [ ] Every tracked and untracked path has a disposition.
- [ ] No secret, `.env`, raw session export or customer workspace is staged.
- [ ] DEC-0031 and DEC-0032 exist and old decisions remain traceable.
- [ ] Current Project State reflects released Step 0 and paused Step 1.
- [ ] All 18 docs records have correct lifecycle and current claims.
- [ ] All 14 prompt files are classified.
- [ ] All 9 workflow prompt registry entries validate and hash-match.
- [ ] All 8 Step Agents, Worker Profiles and Tool Policies validate and hash-match.
- [ ] Step 3B is clearly post-publication and not falsely presented as an initial-route agent.
- [ ] `ONBOARDING_REFERENCE.md` is deterministic and complete by its content contract.
- [ ] Every registry entry appears in the onboarding inventory.
- [ ] No historical or evidence record enters Default Retrieval.
- [ ] Repository index generation and check both pass.
- [ ] Focused tests, Console build and `hermes verify --json` pass or a concrete blocker is reported.
- [ ] M08 unique commit is integrated or explicitly blocked for Raphael.
- [ ] Final master contains every retired branch tip.
- [ ] Remote master SHA equals local master SHA.
- [ ] All old non-master branches are gone locally and remotely.
- [ ] The old workspace exists in a verified external snapshot.
- [ ] The fresh clone is clean and at the canonical path.
- [ ] The new continuation branch starts at exact consolidated master.
- [ ] The external CL project and Step-1 state remain readable.
- [ ] No statement claims Production acceptance before the real route proves it.

## 10. Rollback

Before push:

- reset only by switching back to the preserved pre-consolidation branch or external snapshot
- never rewrite shared remote history

After master push but before branch deletion:

- all prior tips remain available as branches and through the master graph

After branch deletion:

- all deleted tips must already be reachable from master
- the external full workspace snapshot remains the filesystem rollback source
- GitHub master remains the remote source of truth

After fresh clone replacement:

- restore the archived old workspace only if clone verification or runtime reattachment fails
- do not delete the archive during this operation

## 11. Explicitly out of scope

- completing the real Step-1 production result before repository consolidation
- claiming PT-03 or PT-11 complete
- live Notion or live n8n implementation
- deployment
- broad code cleanup unrelated to safe consolidation
- deleting historical docs, audits, plans, PDFs or recovery sources
- force-pushing or rewriting Git history
- running the complete repository suite without separate authorization
- changing customer facts or customer workspace records during documentation reconciliation

## 12. Execution gate

No implementation, commit, merge, push, branch deletion, clone swap or runtime resume begins until Raphael accepts:

1. the generated onboarding scope
2. the canonical-path fresh-clone strategy
3. the semantic M08 reconciliation rule
4. the truthful-master rule that does not claim Production acceptance
````

## 9. Complete prompt catalog

| Classification | Prompt | Version | Lifecycle | SHA-256 |
|---|---|---|---|---|
| `active_registry` | [`prompts/0-kickoff-v1.10.0.xml.md`](../prompts/0-kickoff-v1.10.0.xml.md) | `1.10.0` | `current_authority` | `eac03e7bc82437bb6a5a567ad8765c6cad4066a6816200ae91a29d7a5edf9e30` |
| `historical_version` | [`prompts/0-kickoff-v1.9.0.xml.md`](../prompts/0-kickoff-v1.9.0.xml.md) | `1.9.0` | `superseded` | `f90a0cb583f095b671ff06e215b238127d75b98c21469dc279edcf4d701958ed` |
| `superseded_alias` | [`prompts/0-kickoff.xml.md`](../prompts/0-kickoff.xml.md) | `1.8.0` | `superseded` | `4fe594f3ec13ceccb6c7f930585762a38b0420e735bcb87754d5d53de1391d00` |
| `historical_version` | [`prompts/1-pillar-identifikation-v2.1.0.xml.md`](../prompts/1-pillar-identifikation-v2.1.0.xml.md) | `2.1.0` | `superseded` | `f6ef3f57a45a2f78ce35413e87075ade44d65be61387333f318f0b32d3ded7a6` |
| `active_registry` | [`prompts/1-pillar-identifikation.xml.md`](../prompts/1-pillar-identifikation.xml.md) | `2.2.0` | `current_authority` | `4b0e3a25b150c4342ef6cc0a13bdee69246d10c6563da5ff42f75522bd5c1ef2` |
| `active_registry` | [`prompts/1b-seitenarchitektur.xml.md`](../prompts/1b-seitenarchitektur.xml.md) | `2.1.0` | `current_authority` | `71d5bbbea3839aa447b60866de75cb3b31a764659572b704c33f9eb801667fac` |
| `active_registry` | [`prompts/1c-pillar-template.xml.md`](../prompts/1c-pillar-template.xml.md) | `2.1.0` | `current_authority` | `7b12fac9cec125aa1932242a9a0d0b1fdf580cccd7faefa855a5c4c3bc1eefdb` |
| `active_registry` | [`prompts/2-cluster-recherche.xml.md`](../prompts/2-cluster-recherche.xml.md) | `2.2.0` | `current_authority` | `a3c498d84b4d7187a2a0335a5fc6607226870ad415c8e6ebcf7c664ca75aec23` |
| `active_registry` | [`prompts/3-120-tage-plan.xml.md`](../prompts/3-120-tage-plan.xml.md) | `2.1.0` | `current_authority` | `adc175eb01d0cb92b4d9165a7e1ab8def889a5a9c3ea649789095e623a5e49e5` |
| `active_registry` | [`prompts/3b-performance-check.xml.md`](../prompts/3b-performance-check.xml.md) | `2.0.0` | `current_authority` | `ff5d5aff300823ab859e72f150a331fadab6b426b4de71d77350363872215369` |
| `active_registry` | [`prompts/4a-content-briefing-und-schema.xml.md`](../prompts/4a-content-briefing-und-schema.xml.md) | `2.2.0` | `current_authority` | `f97bcd37990e8207916ff88c6ce4b0980aeefeecbfb77eeae1200a4bd5dec3f9` |
| `active_registry` | [`prompts/4b-landingpage-html.xml.md`](../prompts/4b-landingpage-html.xml.md) | `2.1.0` | `current_authority` | `35520d1069c45b6346c3ed971489dfa21e46749b838418acfe941961201352bc` |
| `historical_version` | [`prompts/intake-project-v2-v1.2.0.xml.md`](../prompts/intake-project-v2-v1.2.0.xml.md) | `1.2.0` | `superseded` | `7dd0522b3f353d2e840988ad1448e187eaa0d2d374c2bc6ec726901f06ebbfab` |
| `active_intake` | [`prompts/intake-project-v2-v1.3.0.xml.md`](../prompts/intake-project-v2-v1.3.0.xml.md) | `1.3.0` | `current_authority` | `1599f8b0c61151612601280c807270a25ebb813b62e246868f7b0a1ae1b28f6a` |
| `superseded_alias` | [`prompts/intake-project-v2.xml.md`](../prompts/intake-project-v2.xml.md) | `1.1.3` | `superseded` | `16907a5db60c82353bd1bf902db4e587cc1b00f6f2765a1331707da5af42293c` |

## 10. Active workflow prompt registry

| Step | Prompt contract | Prompt path and hash | Output contracts |
|---|---|---|---|
| `0` | `heartweb.step.0@1.10.0` | [`prompts/0-kickoff-v1.10.0.xml.md`](../prompts/0-kickoff-v1.10.0.xml.md) `eac03e7bc82437bb6a5a567ad8765c6cad4066a6816200ae91a29d7a5edf9e30` | `https://heartweb.example/schema/manifest-v2.schema.json@2.0.0`: `standards/manifest-v2.schema.json` `a8ea8b91513c00dec56a65293f33231732a6178f40e7aae9df7c83de73333c82` |
| `1` | `heartweb.step.1@2.2.0` | [`prompts/1-pillar-identifikation.xml.md`](../prompts/1-pillar-identifikation.xml.md) `4b0e3a25b150c4342ef6cc0a13bdee69246d10c6563da5ff42f75522bd5c1ef2` | `https://heartweb.example/schema/outputs/step-1-topic-inventory.schema.json@2.0.0`: `standards/outputs/step-1-topic-inventory.schema.json` `3efe1839ecdb511db63410480c58a78daae655206464efbac39bc9d9dbd35ec1` |
| `1b` | `heartweb.step.1b@2.1.0` | [`prompts/1b-seitenarchitektur.xml.md`](../prompts/1b-seitenarchitektur.xml.md) `71d5bbbea3839aa447b60866de75cb3b31a764659572b704c33f9eb801667fac` | `https://heartweb.example/schema/outputs/step-1b-architecture.schema.json@2.0.0`: `standards/outputs/step-1b-architecture.schema.json` `cd187aa294670c53cab379086e5efc00ef3400fa30e39c176655453710353ba7` |
| `1c` | `heartweb.step.1c@2.1.0` | [`prompts/1c-pillar-template.xml.md`](../prompts/1c-pillar-template.xml.md) `7b12fac9cec125aa1932242a9a0d0b1fdf580cccd7faefa855a5c4c3bc1eefdb` | `https://heartweb.example/schema/outputs/step-1c-design-system.schema.json@2.0.0`: `standards/outputs/step-1c-design-system.schema.json` `51a6c601505000e346d79c258910ca705876ec756fefb1cc26d6e5ea507cc7d4`<br>`https://heartweb.example/schema/outputs/step-1c-template.schema.json@2.0.0`: `standards/outputs/step-1c-template.schema.json` `705e3bd944f62256ddbad4450ec857dc01607359f6493c2604fa748877ce4056` |
| `2` | `heartweb.step.2@2.2.0` | [`prompts/2-cluster-recherche.xml.md`](../prompts/2-cluster-recherche.xml.md) `a3c498d84b4d7187a2a0335a5fc6607226870ad415c8e6ebcf7c664ca75aec23` | `https://heartweb.example/schema/outputs/step-2-keyword-evidence.schema.json@2.0.0`: `standards/outputs/step-2-keyword-evidence.schema.json` `7bbdb5d62d0e6cda64713e9525adc984b904668ecea241f05c7dd7a0d2a2948b` |
| `3` | `heartweb.step.3@2.1.0` | [`prompts/3-120-tage-plan.xml.md`](../prompts/3-120-tage-plan.xml.md) `adc175eb01d0cb92b4d9165a7e1ab8def889a5a9c3ea649789095e623a5e49e5` | `https://heartweb.example/schema/outputs/step-3-plan.schema.json@2.0.0`: `standards/outputs/step-3-plan.schema.json` `91322528c18d5f28da8f1371c93cbfca34e2917ab8b3f54dabd68769ba10976f` |
| `3b` | `heartweb.step.3b@2.0.0` | [`prompts/3b-performance-check.xml.md`](../prompts/3b-performance-check.xml.md) `ff5d5aff300823ab859e72f150a331fadab6b426b4de71d77350363872215369` | `https://heartweb.example/schema/outputs/step-3b-adjustment.schema.json@2.0.0`: `standards/outputs/step-3b-adjustment.schema.json` `42be410fab80415a8afb8eca3675d4760e64800c69106a56261ced73fd8b0f9b` |
| `4a` | `heartweb.step.4a@2.2.0` | [`prompts/4a-content-briefing-und-schema.xml.md`](../prompts/4a-content-briefing-und-schema.xml.md) `f97bcd37990e8207916ff88c6ce4b0980aeefeecbfb77eeae1200a4bd5dec3f9` | `https://heartweb.example/schema/outputs/step-4a-briefing.schema.json@2.0.0`: `standards/outputs/step-4a-briefing.schema.json` `dc9d7731d70f5bee4f0e4b99ce292c2dc1991767f2f413e043e80552b3d14093`<br>`https://heartweb.example/schema/outputs/claim-ledger.schema.json@2.0.0`: `standards/outputs/claim-ledger.schema.json` `945f23deec09ec8d371365eae4d8a4fef37f320f45e161c0c048d758f26ff990` |
| `4b` | `heartweb.step.4b@2.1.0` | [`prompts/4b-landingpage-html.xml.md`](../prompts/4b-landingpage-html.xml.md) `35520d1069c45b6346c3ed971489dfa21e46749b838418acfe941961201352bc` | `https://heartweb.example/schema/outputs/step-4b-page-spec.schema.json@2.0.0`: `standards/outputs/step-4b-page-spec.schema.json` `fd8d3179e18eaad26a5be788a8d97aaa5c84dca8bb27fd3c40d86dfb0d2f8aae`<br>`https://heartweb.example/schema/outputs/staging-evidence.schema.json@2.0.0`: `standards/outputs/staging-evidence.schema.json` `7a288946ba24f407dbd613e568ceb0cf1830d2cdf678002d7edac32034ce7d01` |

## 11. Initial-route Step agents, Worker Profiles and Tool Policies

| Step | Agent contract | Worker Profile | Tool Policy | Required operations |
|---|---|---|---|---|
| `0` | `heartweb-step-0-agent@1.3.0` | [`standards/runtime/worker-profiles/step-0-agent.json`](../standards/runtime/worker-profiles/step-0-agent.json) `1.3.0` `8edaa3ffeb219b9d7772710edc6a03d449ac84e10afc5204af0aebe978835150` | [`standards/runtime/tool-policies/step-0-agent.json`](../standards/runtime/tool-policies/step-0-agent.json) `1.2.0` `9056c3acdcdde6e0e85c75d159d8fd8a1cac4d5f0cde1835f6efb5198ee882e3` | `prepare_kickoff_preflight` |
| `1` | `heartweb-step-1-agent@1.2.0` | [`standards/runtime/worker-profiles/step-1-agent.json`](../standards/runtime/worker-profiles/step-1-agent.json) `1.3.0` `9e8b1211a0e6ebd08f80087cf07c4aa845b35aef50fb7ace8a1322288fb699e8` | [`standards/runtime/tool-policies/step-1-agent.json`](../standards/runtime/tool-policies/step-1-agent.json) `1.2.0` `9703f054fd023895a71b7d43b3dc57c92b077d4bbc5b72d10ca9c3ab56d45f9e` | `run_screaming_frog_crawl`, `request_serp_intent_evidence` |
| `1b` | `heartweb-step-1b-agent@1.3.0` | [`standards/runtime/worker-profiles/step-1b-agent.json`](../standards/runtime/worker-profiles/step-1b-agent.json) `1.4.0` `4378797468c0fa732efa353676cf089e82127d2df3d85241ebd950de817705ac` | [`standards/runtime/tool-policies/step-1b-agent.json`](../standards/runtime/tool-policies/step-1b-agent.json) `1.4.0` `2b2b09f58870305d54755191e7b7cd316f34b661f9897ac973c1ecabed8c5421` | `request_serp_intent_evidence` |
| `1c` | `heartweb-step-1c-agent@1.1.0` | [`standards/runtime/worker-profiles/step-1c-agent.json`](../standards/runtime/worker-profiles/step-1c-agent.json) `1.2.0` `951a616d27ed5cf1bd6b19ff72b989f08b54d7e8617c47bb29ec8e29d72d1180` | [`standards/runtime/tool-policies/step-1c-agent.json`](../standards/runtime/tool-policies/step-1c-agent.json) `1.1.0` `37099f2e19ea33ab911381d5dba2b8dc1d916b51283fde7ff5c38345d4eeaa8f` | `read_design_evidence` |
| `2` | `heartweb-step-2-agent@1.3.0` | [`standards/runtime/worker-profiles/step-2-agent.json`](../standards/runtime/worker-profiles/step-2-agent.json) `1.4.0` `32429475babe4624988d299f0281058b595e2ce24a1c08d6ec917f7fc3afe560` | [`standards/runtime/tool-policies/step-2-agent.json`](../standards/runtime/tool-policies/step-2-agent.json) `1.4.0` `e3ed624b217ebe78d8bedc7923bbc873b6962a32c11a3b5ec373fe876f911c17` | `request_keyword_metrics` |
| `3` | `heartweb-step-3-agent@1.1.0` | [`standards/runtime/worker-profiles/step-3-agent.json`](../standards/runtime/worker-profiles/step-3-agent.json) `1.2.0` `5fbbc0dc37ad166b61c3162f49ac4e07559711a0af3f58ddb425e37808a67ada` | [`standards/runtime/tool-policies/step-3-agent.json`](../standards/runtime/tool-policies/step-3-agent.json) `1.1.0` `8304b3f7cba413b2ee0fd79a80cd10c1a422a752c8ac475bf44a4cee970f35b0` | `solve_capacity_matrix` |
| `4a` | `heartweb-step-4a-agent@1.3.0` | [`standards/runtime/worker-profiles/step-4a-agent.json`](../standards/runtime/worker-profiles/step-4a-agent.json) `1.4.0` `9a0a46b223f0df53033c91b0f4cfcfed324bebcf18ffbcb5587111fb36d50367` | [`standards/runtime/tool-policies/step-4a-agent.json`](../standards/runtime/tool-policies/step-4a-agent.json) `1.4.0` `bccc68ca85ba4ab3d73a6a99813ae99fadb0562c2cabfabedf01a7f3d1acb29a` | `request_serp_briefing_evidence`, `validate_jsonld` |
| `4b` | `heartweb-step-4b-agent@1.2.0` | [`standards/runtime/worker-profiles/step-4b-agent.json`](../standards/runtime/worker-profiles/step-4b-agent.json) `1.3.0` `43900968fbed5d25b58742b1db2c8b36726d7bc8c04aacbeb0dfd706b92ab9cd` | [`standards/runtime/tool-policies/step-4b-agent.json`](../standards/runtime/tool-policies/step-4b-agent.json) `1.2.0` `351b305c9e62a9f7f225b6731e5cc4e289ccc55aee0e967d0bd1294f5df9fd00` | `validate_jsonld`, `run_staging_validation` |

## 12. Evolution rules

A semantic prompt change requires coordinated review of prompt version, output schema version, validator, renderer, Quality Gate, positive and negative fixtures, Context Package, tool policy and migration or activation rule. Contracts stay strict on identity, lineage, Evidence and state while preserving strategic freedom inside accepted boundaries.

New providers enter through the Provider Gateway. New agent tools require versioned operations and policies. New workflow Steps require Core graph, transitions, artifacts, gates, prompts, contracts, validators, renderers, tests and operator projection updates. The full authority is embedded above from `docs/09-extension-and-evolution-guide.md`.

## 13. Local entry points

```text
python scripts/start_operator_console.py
hermes -p heartweb-runtime gateway status
curl http://127.0.0.1:8650/health
curl http://127.0.0.1:8765/api/v2/readiness
python scripts/smoke_operator_console.py
python scripts/build_repository_index.py
python scripts/build_repository_index.py --check
python -m unittest tests.test_repository_index
npm run build --prefix apps/operator-console
hermes verify --json
```

Do not place credentials on a command line or in this repository. Use the isolated runtime profile and environment configuration. Shared diagnostics are under the local `var/operator-diagnostics/` contract and are not repository authority.

## 14. Lifecycle counts

- `active_plan`: 5
- `current_authority`: 123
- `current_strategy`: 8
- `evidence`: 177
- `historical`: 8
- `superseded`: 12

## 15. Complete registry inventory

Every registry source appears exactly once below. Evidence and audit bodies remain at their canonical paths and are not duplicated here.

| # | Document | Lifecycle | Authority | Type | Summary | SHA-256 |
|---:|---|---|---:|---|---|---|
| 1 | [`.hermes/plans/2026-08-18_082138-heartweb-operations-platform-plan.md`](../.hermes/plans/2026-08-18_082138-heartweb-operations-platform-plan.md) | `superseded` | 15 | `plan` | Superseded broad platform plan retained for original intent reconstruction. | `0ec7b92137c2b3c5d872ff04d691cde0724101e7abf79a590be689adf89920cf` |
| 2 | [`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md`](../.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md) | `superseded` | 15 | `plan` | Superseded migration plan retained for original integration intent reconstruction. | `8918a0e82b881593a329598f4841c6228be1df4d76f1a17f7bd48e0c1e8819d3` |
| 3 | [`.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`](../.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md) | `active_plan` | 92 | `plan` | Primary end-to-end implementation plan for the local Core and Operator workflow. | `b774c9a80f689e37e5837d29feea46d7c7e7b4ff585afe54a84bede2abb18d20` |
| 4 | [`.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md`](../.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md) | `superseded` | 20 | `plan` | Completed foundation planning evidence retained for historical reconstruction. | `a9f80ee0f35f48f01f8a2f744c57bf1f799f84d45ead6570441b9a83ff5a0569` |
| 5 | [`.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`](../.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md) | `historical` | 30 | `plan` | Completed PQ-4 restoration plan retained as historical implementation evidence; real-output semantic verification remains open in M10. | `9955f6356198b6249fa9ae710b7a01a923b967229d6675a6c83fbcb8ac15e9c3` |
| 6 | [`.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md`](../.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md) | `active_plan` | 90 | `plan` | Binding completion and evidence contract for Sprint 5 operational behavior. | `be2396f6a93f62f3e704c930a1928cb5d8aa799d2f5ca0b8765413ef54ee5c46` |
| 7 | [`.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md`](../.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md) | `active_plan` | 88 | `plan` | Binding German single-admin product and interaction specification. | `d8c69e515d0443c4bf16242850f5fc59d7f7ab12b0bc114e5e3c7de17df6ec2b` |
| 8 | [`.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`](../.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md) | `active_plan` | 92 | `plan` | Binding Sprint 5E plan for deterministic packages, ZIP delivery and manual Notion handoff. | `f3bde01f6914a4ce41f08554a7612bb2ea2480a23db09c1c02946fde77bff46d` |
| 9 | [`.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`](../.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md) | `current_strategy` | 88 | `plan` | Current quality-restoration source for preserving approved prompt requirements in V2 contracts and gates. | `6c9a659f1dadd1c53cefe1363dff347435fd68f54ecfbf65ca28c5fc2a5debb9` |
| 10 | [`.hermes/plans/2026-08-22-repository-authority-rag-index.md`](../.hermes/plans/2026-08-22-repository-authority-rag-index.md) | `superseded` | 25 | `plan` | Completed isolated authority-index plan retained as the origin of the generator and superseded by the master-consolidation plan. | `02c9caf72e882517492cd01d55c4b6f1ac05c4abbc0aee2f44bf2ff6186f31b8` |
| 11 | [`.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md`](../.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md) | `current_strategy` | 84 | `plan` | Current bounded execution policy for the thin Hermes Runs adapter and its OAuth ownership boundary. | `d0692bfb67c27adfaccbba0262b2ffc2d05db1ac5fad9a1acbf0821c154e1463` |
| 12 | [`.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md`](../.hermes/plans/2026-08-25_225654-repository-master-consolidation-and-onboarding.md) | `active_plan` | 95 | `plan` | Current authorized execution plan for complete master consolidation, deterministic onboarding, branch cleanup and fresh-clone continuation. | `a6d29f7892f4518a1b1ac0018ead783dc68754ea0230cb48420070b60660b629` |
| 13 | [`.hermes/plans/heartweb-notion-n8n-ui-migration.png`](../.hermes/plans/heartweb-notion-n8n-ui-migration.png) | `evidence` | 10 | `plan` | Historical planning image retained as visual Evidence and excluded from default retrieval. | `e821aa1b0400f4571568a364e86cadb36f7286216e637ab4f22058604c469ad2` |
| 14 | [`.hermes/plans/heartweb-operations-platform-architecture.png`](../.hermes/plans/heartweb-operations-platform-architecture.png) | `evidence` | 10 | `plan` | Historical planning image retained as visual Evidence and excluded from default retrieval. | `e821aa1b0400f4571568a364e86cadb36f7286216e637ab4f22058604c469ad2` |
| 15 | [`00_admin/AUDIT-2026-08-17-konsistenz.md`](../00_admin/AUDIT-2026-08-17-konsistenz.md) | `evidence` | 15 | `audit_evidence` | Historical consistency audit retained as source evidence. | `4501cf72c5858eb93ff33beda9a95f6ec0e329ed446c2dd58205a44a2a5f7c3d` |
| 16 | [`00_admin/DECISIONS.md`](../00_admin/DECISIONS.md) | `current_authority` | 98 | `decision_log` | Append-only active and superseded project decisions with rationale and evidence. | `a307cfada0297bffa92bc5f9c689912138c08798c6506000317ebd6e0de26e07` |
| 17 | [`00_admin/DEFERRED_INTEGRATION_BACKLOG.md`](../00_admin/DEFERRED_INTEGRATION_BACKLOG.md) | `current_strategy` | 88 | `backlog` | Canonical queue for approved or deferred integration work and acceptance criteria. | `79c96f69f158221665b23582e2ef3e1f81dedd2fb6fbb696f1e1b7caea72e13e` |
| 18 | [`00_admin/MASTER_TASK_MATRIX.md`](../00_admin/MASTER_TASK_MATRIX.md) | `current_authority` | 99 | `project_state` | Current fixed M01 to M10 release hierarchy and 13-stage roadmap status overlay. | `3daea023ddba88d1a01f03cc5a1452f063fca268d49b5292f8c1c90450ebddb2` |
| 19 | [`00_admin/POST_RELEASE_BACKLOG.md`](../00_admin/POST_RELEASE_BACKLOG.md) | `current_strategy` | 87 | `backlog` | Current non-blocking queue for live integrations, Step 3B, deployment, expansion and cleanup after the first local Production output. | `7c745f8009195ff825f2ba7356ed5c34aed7ac1e5dc8a5ccdbf4b7db3cdf56f4` |
| 20 | [`00_admin/PROJECT_STATE.md`](../00_admin/PROJECT_STATE.md) | `current_authority` | 100 | `project_state` | Primary mutable authority for current project goal, status, risks and next action. | `695e27bb02b43bd2f1479f471671389b4a6975b634ba11edd4d56e485fae032b` |
| 21 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/00_MASTER_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Der aktuelle Repository-Stand ist kein produktionsreifer End-to-End-Workflow fuer die zehn realen Heartweb-Kunden, keine deploybare n8n-Runtime und keine belastbare Notion-Control-Plane. | `3c9d8ec12f5cb14ce4bce1d1995cb8ec571e2d9d871151769d4ce45d34da3e05` |
| 22 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/01_DOMAIN_AND_PROMPT_AUDIT.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/01_DOMAIN_AND_PROMPT_AUDIT.md) | `evidence` | 10 | `audit_evidence` | No-Go fuer die Zielarchitektur UI, n8n und Notion sowie fuer die zehn realen Kundenfaelle. Der Workflow ist ein gut dokumentierter, sinnvoll gegateter Einzelmarkt-SEO-Workflow fuer einen vorwiegend deutschsprachigen lokalen Pilotfall. Er ist noch kein ausfuehrbarer, international | `25a2765a0f98de10c4369077b4dd5c34330d4e681702e35aa1e4a1aed384d285` |
| 23 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/02_IMPLEMENTATION_AND_TEST_AUDIT.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/02_IMPLEMENTATION_AND_TEST_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Verdict: No-Go fuer einen automatisierten Produktionsbetrieb. | `fae47b4238dc34e4eeede90897bcaa29641b38fea2438a01afb45085c3c64199` |
| 24 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/03_N8N_NOTION_UI_ARCHITECTURE_AUDIT.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/03_N8N_NOTION_UI_ARCHITECTURE_AUDIT.md) | `evidence` | 10 | `audit_evidence` | No-Go fuer Deployment und produktive Kundenlaeufe. Das Zielbild ist fachlich sinnvoll: Die eigene UI soll Bedienoberflaeche sein, n8n soll orchestrieren, Notion soll das zentrale operative Steuerelement bilden und das Repository soll die versionierte Domainlogik liefern. Diese Ro | `e370acc6bc47edf3ba28b448e0165c7f804541127cd08b547caf93fb25e22f51` |
| 25 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/04_TRACEABILITY_OUTPUT_REDTEAM_AUDIT.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/04_TRACEABILITY_OUTPUT_REDTEAM_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Verdict: No-Go fuer produktive, automatisierte Kundenauslieferung und Deployment. | `5a7fa0a6271140622c1c8ad4cdcf5eeb973f8328631d501d196522386f196807` |
| 26 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md) | `evidence` | 10 | `audit_evidence` | Auditiere das gesamte Repository und den Workflow fundamental gegen den realen Heartweb-Einsatz. Beurteile nicht nur, ob Dateien vorhanden sind oder Tests gruen werden. Beurteile, ob die Architektur alle realen Kundentypen professionell, reproduzierbar, internationalisierbar, aut | `ca3a70d41a6bb54775b1034983d9930824eb72197005cbcb0e181a2d36c4158d` |
| 27 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md) | `evidence` | 10 | `audit_evidence` | master entspricht origin/master bei Commit 5e78679. | `6334b09c1b77eaacaa85161b1d624b3d126e37e769ba77b03c32cd08d0bd92d7` |
| 28 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/OFFICIAL_PLATFORM_EVIDENCE.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/OFFICIAL_PLATFORM_EVIDENCE.md) | `evidence` | 10 | `audit_evidence` | Quelle: https://docs.n8n.io/deploy/host-n8n/configure-n8n/scaling/control-concurrency | `4d8ccdf9350b8df9bd737665275127d008abcaa500587064bdf61f2a832388b4` |
| 29 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/SCREAMING_FROG_OFFICIAL_EVIDENCE.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/SCREAMING_FROG_OFFICIAL_EVIDENCE.md) | `evidence` | 10 | `audit_evidence` | Pfad: | `e85d4b6a70ed49848d0809844bfe25c7c74c437ef3080ea6d77060481a84438c` |
| 30 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/01_FOUNDATION_DOMAIN_IMPLEMENTATION.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/01_FOUNDATION_DOMAIN_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Ausgefuehrt: | `7e3613c22def3e72b03955ddfac3a938e54574b446809f1649b1f02a06ce8c57` |
| 31 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/02_FOUNDATION_WORKFLOW_IMPLEMENTATION.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/02_FOUNDATION_WORKFLOW_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Ausgefuehrt: | `a6a4283bd6941d086e8f5e00ead151216f6d5bc09192975c57475201d142d489` |
| 32 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/03_STEP1_CONTRACT_IMPLEMENTATION.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/03_STEP1_CONTRACT_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Autor: Raphael Rechberger | `88e0b5e7e042fde8911f1da6e755869c4b78654d5055bad33368137d0d4793cb` |
| 33 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/04_STEP1_SPEC_REVIEW.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/04_STEP1_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | The implementation must preserve the immutable AHD baseline, provide a validating V2 sidecar, prevent Step 1 completion before the external Gate 1, provide the required crawl or an explicit blocker, enforce the Step 1 output and prompt contracts, and have green Host and OMO verif | `b08686865e20a556fdf0d249e762d1bf21824f70f4cc9f3ba1b7fbfca18e0dd2` |
| 34 | [`00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/05_STEP1_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-18-fundamental-workflow-audit/implementation/05_STEP1_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | This was a read-only audit of the Step 1 Foundation contracts, registries, Prompt 1 v2, preflight implementation, Screaming Frog adapter, relevant tests, and AHD staging lineage. The implementation declares a closed canonical inventory, an awaiting-gate submission, and revision-b | `14a695351ec47928db30512745f524eafd6c806bcf40526e51662db11df76430` |
| 35 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/01_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/01_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Sprint 1 requires a transition-service review, registry applicability enforcement, crawl disposition coverage, persisted-artifact Step 1 preflight, error-envelope operator routing, and the listed integration suite. The gate also requires no open P0 or P1 findings: .hermes/plans/2 | `42723ebc89b46496cdce3ba6a371efb3ea1a91fe4daaa29521b268c7bd110d12` |
| 36 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/02_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/02_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | REQUESTCHANGES | `2618c245ee4abcf9b79d691799de27d412cf056293dff42d0308e809c9e133c9` |
| 37 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/03_FIX_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/03_FIX_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Indexed repository document: Sprint 1 Fix Implementation. | `da8be70ac46f6ec8f85dba5e6a8e64a4d48de73566153674aca5779499715bce` |
| 38 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/04_HOST_PORTABILITY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/04_HOST_PORTABILITY_FIX.md) | `evidence` | 10 | `audit_evidence` | Autor: Raphael Rechberger | `7c9ae1ae85f934bbfcd8f0987efd9ed1720bf2e010cfd14e00fe4e53c1340cd1` |
| 39 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/05_SPEC_REREVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/05_SPEC_REREVIEW.md) | `evidence` | 10 | `audit_evidence` | No P0 finding verified. | `f0f32f40e9ba499b7cb103f5a09ffa87666f47dabb789a8a82fabc68a23d6983` |
| 40 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/06_QUALITY_REREVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/06_QUALITY_REREVIEW.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `a168ff58e11b02306b5b5f5ff166dc236859f66a8ae935dd6677816a6801aa24` |
| 41 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/07_REREVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/07_REREVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `5b7d3d7e35d5b25cce1808beac8b62133c6987541545d1a1b5679246cee68557` |
| 42 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/08_WINDOWS_REPARSE_TEST_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/08_WINDOWS_REPARSE_TEST_FIX.md) | `evidence` | 10 | `audit_evidence` | Changed only these test files: | `579a3d22237e3418967eb82524cac0528af51eb0cf8f5ba71cac55fff316c1d0` |
| 43 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/09_FINAL_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/09_FINAL_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `dda1f76017cd8b892c2f24cfd9061f3742f9fb0cd396842218fbd423477dd848` |
| 44 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/10_FINAL_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/10_FINAL_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `e03f6004409727be002c99487ca1fdae63574352934f5bc4e252e8eed6cdc9a8` |
| 45 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/11_ROUTING_COMPLETENESS_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/11_ROUTING_COMPLETENESS_FIX.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `1c40d880f1aad86f853f0bfc20866841c698ba0ab0c50425d75db438326a4c76` |
| 46 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/12_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/12_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `c7ccf2c45dce4a4d067b6e573ae40ab1295d39f9237ab495d7d12b0634406a74` |
| 47 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-1/13_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-1/13_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `84c22002e3746f6b6286e6610c680979be4e18ae3b4d1943511675d04abf455f` |
| 48 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-2/01_OPERATOR_CONTRACT_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-2/01_OPERATOR_CONTRACT_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `08181b6c2d818c824f7ca2f00a24afadbc759301595babd269c08f059ea9713d` |
| 49 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-2/02_INTEGRATION_CONTRACT_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-2/02_INTEGRATION_CONTRACT_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Implemented Sprint 2 Tasks 2.7 through 2.9 only. The contracts define append-only workflow events, a Notion operative projection, and n8n orchestration commands. Notion remains the central operative interface and is not an atomic state writer. All current positive fixtures use si | `1490b47f7913968fab40a8eb16485e879052aa1531bf31a3cddcc6f496776089` |
| 50 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-2/03_FULL_SUITE_DISCOVERY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-2/03_FULL_SUITE_DISCOVERY_FIX.md) | `evidence` | 10 | `audit_evidence` | Corrected the local full-suite runner so it runs exactly three fail-fast phases: the acceptance runner, root tests unittest discovery excluding tests/contracts, and tests/contracts unittest discovery. Each unittest phase reports its actual test count and fails if it discovers zer | `e8c385f28f74c1ad01e5404cead06b1c653c69302575e34c3ebebff619fcb603` |
| 51 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-2/04_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-2/04_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Reviewer: Raphael Rechberger | `50698f55e82cb50f6fa05264ca9baaf865d912c917b8c32d1d63f4646f0ca6f0` |
| 52 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-2/05_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-2/05_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `66b579c6ce43af1980dc86416adf63aaf1f33fe95c622b454de3bfaa4dfe1f93` |
| 53 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/01_ARCHITECTURE_DESIGN_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/01_ARCHITECTURE_DESIGN_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Implemented Tasks 3.1 through 3.3 within the assigned allowlist only. | `92ebc046cc2afcffebe135076395f33af4c3d7df8f27d3203ccc881db22691d7` |
| 54 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/02_RESEARCH_PLAN_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/02_RESEARCH_PLAN_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Implemented Tasks 3.4 through 3.6 within the Lane B allowlist only. | `e36a7bd5a3c2d3db3a5299157538d0abfc482f12c7c6e15ab8dda10194024c01` |
| 55 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/03_CONTENT_STAGING_PERFORMANCE_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/03_CONTENT_STAGING_PERFORMANCE_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `7602349c7e8bbb439564d14fcc118bf2a932d2538253b9df4f99183278219ad6` |
| 56 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/04_INTEGRATION_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/04_INTEGRATION_FIX.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `91e74a2158ddcf725ffa181940b169e96698b5c525c762f4edf6275591b3c7f4` |
| 57 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/05_OUTPUT_CONTRACT_INTEGRATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/05_OUTPUT_CONTRACT_INTEGRATION.md) | `evidence` | 10 | `audit_evidence` | This change harmonizes the authorized canonical output and support-output schemas for Steps 1, 1b, 1c, 2, 3, 3b, 4a, and 4b. Step 0, renderer work, runtime services, quality registry, operator routing, provider gateway, project state, and plans were not changed. | `beddafcdf3f520da1c4e13d93dca14d9efaa0ece7538bbe00570dacc33b9fc5d` |
| 58 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/06_DERIVED_VIEW_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/06_DERIVED_VIEW_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Implemented deterministic, validator-backed derived-view renderers only for Steps 1c, 2, 3, 3b, 4a, and 4b. | `4e8b7534573771a7ba681eb2abae60ef41ea25dc4bd1e07b1609937e80e2af49` |
| 59 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/07_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/07_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `043c68a95f75429ec627e7e6752e740574b22ecfce44c86b4f1d9d278267a05b` |
| 60 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/08_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/08_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Review date: 2026-08-19 | `eee2f69ce356b37dbd558ac8982f99d9e33583cae16a6cdd937c5403315f2d08` |
| 61 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/09_CROSS_STEP_SAFETY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/09_CROSS_STEP_SAFETY_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `1678558c896f57ef00bd5c59a2bd24b53d77878fb5fccb6a97cb3ed25ee5944b` |
| 62 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/10_PREDECESSOR_LINEAGE_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/10_PREDECESSOR_LINEAGE_FIX.md) | `evidence` | 10 | `audit_evidence` | Added services/preflightcommon as the reusable runtime artifact and release lineage boundary. The boundary rejects non-awaiting-gate candidates, missing predecessor records, runtime-schema-invalid records, release status or gate mismatches, identity mismatches, and omitted predec | `0f836b9410c40d03872b0f1e89dbf880c9181e9ee55eeccb6633159176f8b4a5` |
| 63 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/11_RENDERER_EVIDENCE_PATH_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/11_RENDERER_EVIDENCE_PATH_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `ea69bfe61f5a0af1f198171a738b63bf58c380d14b2111589cf33deef2f35a79` |
| 64 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/12_RENDERER_EVIDENCE_PATH_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/12_RENDERER_EVIDENCE_PATH_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `944c259852819fd959ae447ebd382d9cb5fe101761e08d226130f9855455803e` |
| 65 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/13_MANDATORY_LINEAGE_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/13_MANDATORY_LINEAGE_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `e2f41fca05e0891db745fb598e6419aa1fa47110aac0d95b27fd94e0d8bca9ae` |
| 66 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/14_WINDOWS_JSONLD_IMPORT_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/14_WINDOWS_JSONLD_IMPORT_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `eeaac2e283764749978682d42bd346ef572bcfefac566e02099d77ed585e04ce` |
| 67 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/15_FINAL_SPEC_REREVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/15_FINAL_SPEC_REREVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `761687bbd7bcab57b79cb343b2a9efe36c93a2fece7fee18d8744e5cc2c01223` |
| 68 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/16_FINAL_QUALITY_REREVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/16_FINAL_QUALITY_REREVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `daba5e46580103356ed809625a6b9ae35f1f3991c224c6c169c0076eb7b48d38` |
| 69 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/17_FINAL_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/17_FINAL_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `3c162d411cb76d8ee7a010962bfad51cd7f6fd9aa656adc44ecb50840b244fe5` |
| 70 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/18_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/18_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `800d7feeb9cfec1d2b705757cf064470ec965b8b74398385e2f1a1fa757aaa28` |
| 71 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/19_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/19_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `30821b115bb551d46a9bacfda26a309de0943bfdbf4f70ae76d1174c7447e43c` |
| 72 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/20_PROVIDER_HASH_RENDERER_GATE_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/20_PROVIDER_HASH_RENDERER_GATE_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `e770c86ca0e9d2028f73a49568b5a73e160ac00b8862f62f8c4a2421693cb132` |
| 73 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/21_ULTIMATE_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/21_ULTIMATE_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `42ecfd2922564850eeeca6ff8a1e5de2adf7675a53ddd1884c9a27ecd19c7f32` |
| 74 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-3/22_ULTIMATE_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-3/22_ULTIMATE_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `190246a13f14a96cf680007cf5af13ec94e5fd3d47b7150d3e570e2656d0be8d` |
| 75 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/01_API_ARCHITECTURE_RESEARCH.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/01_API_ARCHITECTURE_RESEARCH.md) | `evidence` | 10 | `audit_evidence` | This is a read-only architecture recommendation for Sprint 4. It distinguishes current repository contracts from required implementation work. Statements prefixed Design decision are not implemented contracts and require implementation review before they become binding. | `29612f1eae409bccc7ce527872921da5a0c6128b4e2ae8b582659c548a4a7111` |
| 76 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/02_INTEGRATION_SIMULATION_RESEARCH.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/02_INTEGRATION_SIMULATION_RESEARCH.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `fd6b2cc59e77d5679a81f78dcd316f8bcfddc78e5bfe5cef3271724ea6b21821` |
| 77 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `042cb909d2b14571779206aaa8aaca84a6215437dc4ca4461acde90afc8e41d7` |
| 78 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/04_INTEGRATION_V2_CONTRACT_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/04_INTEGRATION_V2_CONTRACT_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `70dca123b803e1e5fbe91dcbc74caef85770d04b2797a4303037c258fa37a8e6` |
| 79 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/05_INTEGRATION_V2_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/05_INTEGRATION_V2_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `d9419035e21b36c5f79041c310211beca61862b58a33eb33ce875a8f64c5a892` |
| 80 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/06_INTEGRATION_V2_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/06_INTEGRATION_V2_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `6b394382ef91685f488245583d5b858556548eb96e313d209ae6fdb487956e7d` |
| 81 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/07_INTEGRATION_V2_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/07_INTEGRATION_V2_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `009b1d4a31493bfa93892c9e895293c2bc732918362c251635d5a62bba12b8e5` |
| 82 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/08_INTEGRATION_V2_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/08_INTEGRATION_V2_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `0853c20c4cc34385faf6bc551dad6450e017e5e590fbb628cb19de3224477c58` |
| 83 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/09_INTEGRATION_V2_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/09_INTEGRATION_V2_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `e159a45216a7522f4b34d39906bddd45e4a599cb6caed760e4589110526bc753` |
| 84 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/10_NOTION_GRAPH_INTEGRITY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/10_NOTION_GRAPH_INTEGRITY_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `6edce59263de87bd333b0eba73961e209166485887261aa4bfffe7acd4ef5783` |
| 85 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/11_STAGE_A_TERMINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/11_STAGE_A_TERMINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `aecf58ab1ffa42a1045e92bc8324fb5e07b6cca647f2f2eebe280a248b05b619` |
| 86 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/12_STAGE_A_TERMINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/12_STAGE_A_TERMINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `03c35830377140deaeb56998083f32c4f32ff03211d833b3c841cb9da98b3560` |
| 87 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/13_STAGE_A_SCHEMA_ID_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/13_STAGE_A_SCHEMA_ID_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `abbdbac419ab00ab21a064028f652970c2665107da4b1e4095403ab48a361569` |
| 88 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/14_STAGE_A_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/14_STAGE_A_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `00f77172788cf82b983ab60678ebbc768b8e33c6cd7728003c41458f3f1e9095` |
| 89 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/15_STAGE_A2_RUNTIME_CONTRACT_RESEARCH.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/15_STAGE_A2_RUNTIME_CONTRACT_RESEARCH.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `cf24ead81b83a96de0d61a24874665a3e9309979e7e0f33e70da03f7a2378253` |
| 90 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/16_STAGE_A2_CONTEXT_BUILDER_RESEARCH.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/16_STAGE_A2_CONTEXT_BUILDER_RESEARCH.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `b2b1cbef303edc6600352a0d8b7bd711b1e93e752a9e7ddf3d6a84ec04b6c088` |
| 91 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/17_STAGE_A2_IMPLEMENTATION_PLAN.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/17_STAGE_A2_IMPLEMENTATION_PLAN.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `5fcdd200455f29983e12152117136616ccf16688f9e03bb7de2408660252f9d3` |
| 92 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/18_STAGE_A2_RUNTIME_CONTRACT_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/18_STAGE_A2_RUNTIME_CONTRACT_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `7520a1ea7c3725961aab322f5394545fd033923d6e33a0084b2e7bcfe48774a9` |
| 93 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/19_STAGE_A2_RUNTIME_CONTRACT_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/19_STAGE_A2_RUNTIME_CONTRACT_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `6ed69654ccf4ef212d353c3d3f54f59e2628eec643689a3ae977c3ec3d157700` |
| 94 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/20_STAGE_A2_RUNTIME_CONTRACT_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/20_STAGE_A2_RUNTIME_CONTRACT_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `4becce791da26073cf433b26179268cd2c0605c217058d953e96687b5747e4e3` |
| 95 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/21_STAGE_A2_RUNTIME_CONTRACT_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/21_STAGE_A2_RUNTIME_CONTRACT_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `744a4d483d5e133c52d4451f2417b5cea89577704a5c666cc1856b566cc3d5cd` |
| 96 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/22_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/22_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `0e5c39c6316cc6907a215115e310bf86117ff916500fc1fcfe3909be53360287` |
| 97 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/23_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/23_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `f91bee3cb6568cb557bdbcba2beb51d2f6307db2aba8f289926c924f211f13c0` |
| 98 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/24_STAGE_A2_PROJECT_CONTEXT_KIND_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/24_STAGE_A2_PROJECT_CONTEXT_KIND_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `e809934fa308cc787521370e3fbbcae7f0035cf21acbc3420f8a2ff946bce0fa` |
| 99 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/25_STAGE_A2_RUNTIME_CONTRACT_TERMINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/25_STAGE_A2_RUNTIME_CONTRACT_TERMINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `c0602c3e67f5d8aecf84dcfc085792ace70b30d8899e369de453557631c0d083` |
| 100 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/26_STAGE_A2_RUNTIME_CONTRACT_TERMINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/26_STAGE_A2_RUNTIME_CONTRACT_TERMINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `effdd4adfd1fa080d719194fae2b19229096d4169dbdeef3f80202274128d467` |
| 101 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/27_STAGE_A2_PROJECT_SOURCE_POLICY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/27_STAGE_A2_PROJECT_SOURCE_POLICY_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `66226f2d292bc3f37af00289a538edb18f6c04fd17d33b9e7c1c3d186016dc0a` |
| 102 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/28_STAGE_A2_RUNTIME_CONTRACT_ULTIMATE_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/28_STAGE_A2_RUNTIME_CONTRACT_ULTIMATE_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `724269d807ef6868867aae9ce350783facc0e7eaf8ab305f6cfb8c85f0ef1914` |
| 103 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/29_STAGE_A2_RUNTIME_CONTRACT_ULTIMATE_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/29_STAGE_A2_RUNTIME_CONTRACT_ULTIMATE_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `318faae332b44493f84230b2de61c3b4a8735c2d20d4a95a345b19f1312e76da` |
| 104 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/30_STAGE_A2_CONTEXT_META_SCHEMA_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/30_STAGE_A2_CONTEXT_META_SCHEMA_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `ab1b72db2b95d98d1598b820052bddda1f4da605be98052e7619c4dcda2ff4c5` |
| 105 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/31_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/31_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `088419f7bc20a70a29d36da0d23e236298a270ceea1fd1d3ea28fdd73e792f65` |
| 106 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/32_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/32_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `454f034763ff754ef84d34e8b2d44fc5023f6d46ea13f5fb9fa79fc39cf1b83a` |
| 107 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/33_STAGE_A2_META_VALIDATION_PRECONDITION_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/33_STAGE_A2_META_VALIDATION_PRECONDITION_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-19 | `32ed94f240214487ee1e773ae395a20abf7bdf7859a0217096dbecb9f2d67fda` |
| 108 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/34_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/34_STAGE_A2_RUNTIME_CONTRACT_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `4b4e89f3d990dd54ada6f023e73e822c32b1858507f345e8e0466483774a2744` |
| 109 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/35_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/35_STAGE_A2_RUNTIME_CONTRACT_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `522e353f56397d1f3dd0aa2c9c35fe418636ad04f6af34a6eecfda0d55e3c909` |
| 110 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/36_STAGE_A2_CONTEXT_BUILDER_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/36_STAGE_A2_CONTEXT_BUILDER_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `73ec221933a2e55986ac4edf33858a8970179a83a7bd0eeb7ccf840bc28977ba` |
| 111 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/37_STAGE_A2_CONTEXT_BUILDER_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/37_STAGE_A2_CONTEXT_BUILDER_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `3d44912153f8ea3a76d69cdb4e2b33924522b1d3138535155add3c0e941ea4b6` |
| 112 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/38_STAGE_A2_CONTEXT_BUILDER_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/38_STAGE_A2_CONTEXT_BUILDER_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `774e7a89f5e8608a3a373fac24946ae320c03257448bb4dc939ad9968210a5dd` |
| 113 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/39_STAGE_A2_CONTEXT_BUILDER_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/39_STAGE_A2_CONTEXT_BUILDER_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `0991901241dc5bce3e7d4a2c33aa669796d8d5b8dcc3f4af5b972879fda445e4` |
| 114 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/40_STAGE_A2_CONTEXT_BUILDER_FINAL_SPEC_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/40_STAGE_A2_CONTEXT_BUILDER_FINAL_SPEC_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `bb90147cc3fa8891c0347ffd95bca9058e2a998c0c84cdb2887a2657f7c0aba0` |
| 115 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/41_STAGE_A2_CONTEXT_BUILDER_FINAL_QUALITY_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/41_STAGE_A2_CONTEXT_BUILDER_FINAL_QUALITY_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `9a82cb311f47486d2f2a32a7a1f3c95dccab0b2ba3bca9fa9b741070e0f14468` |
| 116 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/42_STAGE_B_OPERATOR_API_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/42_STAGE_B_OPERATOR_API_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `04787fe015752f67365a7bb126716c8c897c75ac619cd1ccb28959dee95d68b2` |
| 117 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/43_STAGE_B_OPERATOR_API_SPEC_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/43_STAGE_B_OPERATOR_API_SPEC_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `03d20e4ac9719f3a0d5ab81268763e1d40e86e6bd0b26eb4d4089041d46c1c86` |
| 118 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/44_STAGE_B_OPERATOR_API_QUALITY_REVIEW.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/44_STAGE_B_OPERATOR_API_QUALITY_REVIEW.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `37e5fa2e5fac5c4c3b15f6399730b9931a0d62a02f2ac21868861a233e187965` |
| 119 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/45_STAGE_B_OPERATOR_API_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/45_STAGE_B_OPERATOR_API_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `74146d5d172d170f7b1368586043d87a77e720dd7d18498cde7d07d1c0e18b7f` |
| 120 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/46_STAGE_B_WINDOWS_RECOVERY_TEST_PORTABILITY_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/46_STAGE_B_WINDOWS_RECOVERY_TEST_PORTABILITY_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `1f7eb9fed8f138c41c096f50878a03f1c9492359569e20e5f5d94703bcf9473a` |
| 121 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/47_STAGE_B_OPERATOR_API_FINAL_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/47_STAGE_B_OPERATOR_API_FINAL_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `f4f9682f077e0f68af8b735c3716029a3bedd80fd9f78b90ac7088f8c41e3948` |
| 122 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/48_STAGE_B_OPERATOR_API_TERMINAL_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/48_STAGE_B_OPERATOR_API_TERMINAL_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `32916a514c607a21abaf1cc10a9cd7db6268fcb44a85f5230a6571ee57a7cfb2` |
| 123 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/49_STAGE_C_INTEGRATION_SIMULATORS_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/49_STAGE_C_INTEGRATION_SIMULATORS_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `b984488bdb279e46ee3371aa8497620d0d7b9bbd11cb41d67dfff832e24903dc` |
| 124 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/50_STAGE_C_INTEGRATION_SIMULATORS_FINAL_AUDIT.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/50_STAGE_C_INTEGRATION_SIMULATORS_FINAL_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `e14a63004bbea343d5de5223f63a917924ae582caa2254d75fee1802b89c0d4c` |
| 125 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/51_STAGE_C_INTEGRATION_SIMULATORS_REVIEW_FIX.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/51_STAGE_C_INTEGRATION_SIMULATORS_REVIEW_FIX.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `3bfb1a9a1f3c7d3bfe03427f4f9f752690c7a7be565715df2947aa64fff41047` |
| 126 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/52_STAGE_C_INTEGRATION_SIMULATORS_TERMINAL_APPROVAL.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/52_STAGE_C_INTEGRATION_SIMULATORS_TERMINAL_APPROVAL.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `ca01be1405df6b05898cfd60c949782caefe35f83469fda1b2b6c6edad76eeee` |
| 127 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/53_STAGE_D_OPENAPI_INTEGRATION_IMPLEMENTATION.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/53_STAGE_D_OPENAPI_INTEGRATION_IMPLEMENTATION.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `b2ec915291a6b3cf38dbc216584e8fe69c28425c1e6bcbbe70c5a16de7d5b344` |
| 128 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-4/CURRENT_POINT_OF_WORK.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-4/CURRENT_POINT_OF_WORK.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `1d62e78f102169014b76ce3f3f0f88a137fe06f3958d5554da060c885ddad42b` |
| 129 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/01_OPERATOR_CONSOLE_VERTICAL_SLICE.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/01_OPERATOR_CONSOLE_VERTICAL_SLICE.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `17cc4e8442702d322427f5a7272438780a2d71af037ba0ed46ea29a1ba86a779` |
| 130 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/02_ARTIFACT_AND_RUN_WORKSPACE.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/02_ARTIFACT_AND_RUN_WORKSPACE.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `951dc16be2a9ce812296f3ad2334ddfddce0c231ab7d599377f2a24493ed2d2e` |
| 131 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/03_OPERATIONS_REVIEW_PRESENTATION_WORKSPACE.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/03_OPERATIONS_REVIEW_PRESENTATION_WORKSPACE.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-20 | `59fc99aa5a8150cc65d3d42e335b5bc05e380f88017e288d97d66ff3eacd90b8` |
| 132 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/04_SPRINT5_OPERATIONAL_WIRING.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/04_SPRINT5_OPERATIONAL_WIRING.md) | `evidence` | 10 | `audit_evidence` | Date: 2026-08-21 | `53672991a91cc626873632bac7f30f8d95c63c5514332ad7e0eb30a2cd458476` |
| 133 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/README.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/README.md) | `evidence` | 10 | `audit_evidence` | PASS: the current approved round is approval/footer-pass/. | `c750ef66d5eeb0519393c9d85f1dcfe53386501bbefcca0aa470e011fae697fd` |
| 134 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/api-readback.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/api-readback.md) | `evidence` | 10 | `audit_evidence` | The temporary server mounted the production apps/operator-console/dist and the real services.operatorapi.app.createapp at http://127.0.0.1:43179. | `46b7d2608741175bb5ffb717c3a94421f2e665ee48c1b6d0a52d2618e27b793f` |
| 135 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-cleanup.md) | `evidence` | 10 | `audit_evidence` | Cleanup timestamp: 2026-08-21 after the final Chrome evidence run. | `70eea7e460abe28ff73c214ebcbf814bd2d2aa68f02fddd2137176d9973f389d` |
| 136 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-findings.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-findings.md) | `evidence` | 10 | `audit_evidence` | Verdict: BLOCKED | `cc01e6115e35e073e70447d85cf527ddaa75c76552e0f9eca644a03e71d9dd78` |
| 137 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-reproduction.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-reproduction.md) | `evidence` | 10 | `audit_evidence` | Build command: | `c101b9092e3c58c28653d2058b24602de68bb80a1f9efaacf8fde06601dd2666` |
| 138 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-visual-inspection.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/approval-visual-inspection.md) | `evidence` | 10 | `audit_evidence` | Inspection timestamp: 2026-08-21T15:18:23Z to 2026-08-21T15:18:30Z | `b11b003bd21fbeda58d841ac3c8e6a3c7e15a4f0177deff76dfbaf39fef09a37` |
| 139 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/README.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/README.md) | `evidence` | 10 | `audit_evidence` | Verdict: PASS | `33bcf2aa31d45ea94f9f0f57ae2e2209c4c4448859615518e66f4234614200fa` |
| 140 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/approval-pass-cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/approval-pass-cleanup.md) | `evidence` | 10 | `audit_evidence` | Result: cleanup verified. | `65041a8eb7cd47dbb3a537a11ce8ae4a1a1801d189e4028140a624ecafb28459` |
| 141 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/approval-pass-visual-inspection.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final-pass/approval-pass-visual-inspection.md) | `evidence` | 10 | `audit_evidence` | All 24 captures in this directory were opened with lookat after the completed Chrome run. Content continuing below a viewport is normal document scrolling, not clipping. | `c8647733b7baab4b300801488b9a3e78ea7a26a109953aa4a86d4a2312d29606` |
| 142 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-cleanup.md) | `evidence` | 10 | `audit_evidence` | Result: cleanup verified. | `dd4f2e1356b76dd684d277190910ee48be6504e9070e071884f52a1d7f9de619` |
| 143 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-findings.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-findings.md) | `evidence` | 10 | `audit_evidence` | Verdict: BLOCKED | `9b707e8dde1ca6f094d67590c1417e15070527167afada0694b93ef29bed51cf` |
| 144 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-visual-inspection.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/final/approval-final-visual-inspection.md) | `evidence` | 10 | `audit_evidence` | All 24 images in this directory were opened with lookat after the final Chrome run. | `c678e238e33e1fecbb2086d9a506efd57482100c2e65f10086f7eac5ef0c407b` |
| 145 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/FOOTER-PASS-2026-08-21-CURRENT-BLOCKER.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/FOOTER-PASS-2026-08-21-CURRENT-BLOCKER.md) | `evidence` | 10 | `audit_evidence` | Verdict: BLOCKED | `aa4c16de32f4e33cb5ab88213312a791f258d5a44fbdcee0fae21e4a6d879513` |
| 146 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/README.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/README.md) | `evidence` | 10 | `audit_evidence` | Verdict: PASS | `25bdd4016d8f8a02611751d78cc630d28672fc6e48b5eafef3631c0298e2c4c4` |
| 147 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/footer-pass-cleanup-current.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/footer-pass-cleanup-current.md) | `evidence` | 10 | `audit_evidence` | The isolated synthetic server on 127.0.0.1:43185 was stopped after the current PASS run. The temporary Chrome profile, HOME, XDG cache, npm cache, and server log below /tmp/opencode were removed. | `e4fecf38adb416dc80fbb4b9c9eb6f5772bc581cf091ea9fc688b3fd8ab13f64` |
| 148 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/footer-pass-visual-inspection.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/footer-pass-visual-inspection.md) | `evidence` | 10 | `audit_evidence` | Verdict: PASS | `77068e5d81ee80f75782d121c094912027f3d95ac8f73408ef96ef81e953a7ae` |
| 149 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/harness/README.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/footer-pass/harness/README.md) | `evidence` | 10 | `audit_evidence` | The harness uses synthetic tenant, project, artifact, task, and intake values only. It must bind localhost only, serve the current production build, reject unknown paths, and retain only these source files after cleanup. | `de7cf8bdcaf90f01799cd8d30b16b3bc061359f6bb52a34e3d67db394fe273da` |
| 150 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/release-critical-targeted/BLOCKER.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/release-critical-targeted/BLOCKER.md) | `evidence` | 10 | `audit_evidence` | Verdict: BLOCKED | `ccdf8e8829e20d1fe32bd21979a46cb7aafbb96afb54b0f582b1519ad1441529` |
| 151 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/release-critical-targeted/cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/approval/release-critical-targeted/cleanup.md) | `evidence` | 10 | `audit_evidence` | The strict localhost server was stopped. Temporary Chrome profile, HOME, XDG cache, npm cache, and server log below /tmp/opencode were removed. | `66bd512f5a1016488cbe3e5e527f4b6301aab670d4c3902dd05e753ff9d37504` |
| 152 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-direct-cli-failure.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-direct-cli-failure.md) | `evidence` | 10 | `audit_evidence` | The requested direct Playwright Node or CLI fallback is not installed locally. | `0416f384c6113feb290016fc0f4c98536b941f3b62cbc3424160ce1a234024c7` |
| 153 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-launch-failure.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-launch-failure.md) | `evidence` | 10 | `audit_evidence` | Command surface attempted: playwright.browsertabs followed by playwright.browsernavigate for http://127.0.0.1:43179/. | `f93cad1c00f90d4550f863b1ebfb50352972584b9d3b3366ce843bbd5ff41697` |
| 154 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-resume-failure.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/browser-resume-failure.md) | `evidence` | 10 | `audit_evidence` | The missing Chrome error recorded in browser-launch-failure.md is superseded. Chrome Stable is now available at /opt/google/chrome/chrome. | `baeea9ffa73b27f672fd54fbc32ece30a23295523d68ca62b3b363d21c274114` |
| 155 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/cleanup.md) | `evidence` | 10 | `audit_evidence` | The direct fallback created /tmp/opencode/operator-console-browser-home only while verifying local package availability. It was removed with: | `ad03feb7eeff81a7bd9489403302a518285bec47a63f584f378afe87b68aa327` |
| 156 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/last-attempt-cleanup.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/last-attempt-cleanup.md) | `evidence` | 10 | `audit_evidence` | Indexed repository document: Last Attempt Cleanup. | `9543133f3e9c9ede8a28896a90758cb2ce64e50bd906eabb0e807fc7cf93e6e2` |
| 157 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/rerun-findings.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/rerun-findings.md) | `evidence` | 10 | `audit_evidence` | All 24 current route captures pass visual review. | `94738fb5d340a2b5c9ecad92feccedb51717b20806534282f3299a7a39068a8a` |
| 158 | [`00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/visual-findings.md`](../00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/visual-findings.md) | `evidence` | 10 | `audit_evidence` | PRODUCT-001: the required responsive layout fails at 768x1024, 390x844, and 375x812 for every destination. The evidence panel overlays the main workspace and the shell clips horizontally. This violates the DESIGN.md requirement that the panel move below work or become a disclosur | `8369a8684649fec5b1e6491994c6bef5c6fb7ab5d10980f15e108483b3508a27` |
| 159 | [`00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md`](../00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Project: Heartweb Claude Desktop SEO Workflow | `a7468754bb5c5fa21cdd9328bbe78db14cc44482ac6e567e25b97e17827f9323` |
| 160 | [`00_admin/audits/2026-08-21-repository-hygiene/REPOSITORY_HYGIENE_AND_AUTHORITY_AUDIT.md`](../00_admin/audits/2026-08-21-repository-hygiene/REPOSITORY_HYGIENE_AND_AUTHORITY_AUDIT.md) | `evidence` | 10 | `audit_evidence` | Project: Heartweb Claude Desktop SEO Workflow | `1f8bf54dbf3afc7df8bca5c19e1e703cf490340c87000ac5e3fce2aa25b46c60` |
| 161 | [`00_admin/audits/2026-08-22-m06-delivery-e2e/SECTION_11_REPORT.md`](../00_admin/audits/2026-08-22-m06-delivery-e2e/SECTION_11_REPORT.md) | `evidence` | 10 | `audit_evidence` | Change ID: M06-DELIVERY-E2E-001 | `d79917fa3e6f1c391336de07fa03163f51954ff8d9229750233a3babefbf799b` |
| 162 | [`00_admin/audits/2026-08-22-m07-diagnostic-trace/SECTION_11_REPORT.md`](../00_admin/audits/2026-08-22-m07-diagnostic-trace/SECTION_11_REPORT.md) | `evidence` | 10 | `audit_evidence` | Change ID: M07-DIAGNOSTIC-TRACE-001 | `c48f58402455c22ad3928e580530d7785f5dcd7dbd7329c0e2779520a2d8eb24` |
| 163 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/PQ-0_REQUIREMENT_MATRIX.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/PQ-0_REQUIREMENT_MATRIX.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `a61576478504231b6eee02837a41ad1760fbd8ed18ebafddabe6ced7367c3773` |
| 164 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/BASELINE_PLUS_DELTA.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/BASELINE_PLUS_DELTA.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `3f1dc5466767c4846dce284f28929fe74a622c2bf12eb16cf3ab850b300f8535` |
| 165 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-001.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-001.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `136ee49d462065b05c65de57e425329bcd9d6cb859a2e3ac727297f8b7f707d7` |
| 166 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-002.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-002.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `9717adb67c5461fa7699c66808e0aa43b9219b3f34da6d0d1de4e1c6d318357d` |
| 167 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-003.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-003.md) | `evidence` | 10 | `audit_evidence` | Status: deferredexternal | `adcdb350a17fd0e99badbb4842cbbf7fb6d38f4da4dcc8a6310bd5ae61140d3f` |
| 168 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-004.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-004.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `986a3c2dbcabe9d84575752aca172b497433a0aab95519750e310b801e191a24` |
| 169 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-005.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-005.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `f8a7d3cb71502610af667b205e5c445f5d67b2d52d377968b717f66cf9fe70fe` |
| 170 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-006.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-006.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `931c086ad9eddfce58e39ee8759b4e48adc7a9d65357bbbee128e5f1a1a8014d` |
| 171 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-007.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-007.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `65697864dcdaac9c9cd27d9df10aa5901749f380dbb4617dcffa7fd521b5e564` |
| 172 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-008.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4A-008.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `e8aa7be00e718bc932654486bce5ecf9919e5b64bd935069ce6a7e9c5e99f3a8` |
| 173 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-001.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-001.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `930736545e5a781e7c8556d1c009ebdbea5c91483fb82fff7be5c3a122423330` |
| 174 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-002.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-002.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `eebeefc2726e4323095af54d7a7d435595b64908506b436a34f5d07137a4c426` |
| 175 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-003.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-003.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `ae856f55101575b4c925c94b2854f53e3195ba50a3cc7a485612214248d9308e` |
| 176 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-004.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-004.md) | `evidence` | 10 | `audit_evidence` | Status: deferredexternal | `a8fad9eebfb8fd6d6ccf57c7c41a35b51229ed8c4634ad9417b9c221b282b10a` |
| 177 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-005.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-005.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `4439d8440d651bbaceb98a53537612923e76c4bd09c2ea4dbbbe7901bab93089` |
| 178 | [`00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-006.md`](../00_admin/audits/2026-08-23-m08-output-quality-restoration/evidence/PQ-4/PQ0-4B-006.md) | `evidence` | 10 | `audit_evidence` | Status: verified local contract | `df083045a4cccc47a835d3719eeecb90bc44fccc669e33d7dc061ea8e4b7569e` |
| 179 | [`00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`](../00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md) | `evidence` | 10 | `audit_evidence` | Autor: Raphael Rechberger | `22c1e0a5a8a8e15235151119184eb5494ac9a355ed0d986738028a526b55f590` |
| 180 | [`00_admin/audits/2026-08-24-m09-route-matrix/SECTION_11_REPORT.md`](../00_admin/audits/2026-08-24-m09-route-matrix/SECTION_11_REPORT.md) | `evidence` | 10 | `audit_evidence` | Autor: Raphael Rechberger | `ce16707e4dfffdf08e05be29d20ec56e746dccfea088d0c7cb314b64a2c8a18b` |
| 181 | [`00_admin/audits/2026-08-24-m10-readiness/M10_READINESS_REPORT.md`](../00_admin/audits/2026-08-24-m10-readiness/M10_READINESS_REPORT.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `ddf2f64a8e607e08b75cb1fae3bf5ae1d91a81f26e5b16e78ce43d935cc0d9e4` |
| 182 | [`00_admin/audits/2026-08-26-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md`](../00_admin/audits/2026-08-26-repository-consolidation/BRANCH_RECONCILIATION_REPORT.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `f99819d73deda87139d8b184ddc1b0520a25ec6443593c0abd500006fdf3b64a` |
| 183 | [`00_admin/audits/2026-08-26-repository-consolidation/DOCUMENT_LIFECYCLE_RECONCILIATION.md`](../00_admin/audits/2026-08-26-repository-consolidation/DOCUMENT_LIFECYCLE_RECONCILIATION.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `3e57c07a76f8fa209a0a7cfcfb7fff741ba203b692d8da64c7a39b228bfaba77` |
| 184 | [`00_admin/audits/2026-08-26-repository-consolidation/PROMPT_VERSION_RECONCILIATION.md`](../00_admin/audits/2026-08-26-repository-consolidation/PROMPT_VERSION_RECONCILIATION.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `816ab7a48fc7b768a1bb1b1493b3f0e957d8aa15185862f186ea3dc61c9fca3b` |
| 185 | [`00_admin/audits/2026-08-26-repository-consolidation/STEP_AGENT_CONTRACT_RECONCILIATION.md`](../00_admin/audits/2026-08-26-repository-consolidation/STEP_AGENT_CONTRACT_RECONCILIATION.md) | `evidence` | 10 | `audit_evidence` | Author: Raphael Rechberger | `0568bca4ef89186d64a6a986cdd3fbebd7d5250258f17bed6707d2f8f84bd4a1` |
| 186 | [`00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md`](../00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md) | `evidence` | 10 | `checkpoint_evidence` | Nur Hermes aktualisiert nach unabhaengiger Verifikation: | `06d150e4e48365e8cf8e72d223dadccb377df12760dd1c3fe11d8f468b85ea6f` |
| 187 | [`00_admin/meetings/2026-08-17-meeting-raphael-jesse.md`](../00_admin/meetings/2026-08-17-meeting-raphael-jesse.md) | `evidence` | 20 | `meeting_source` | Datum: 17. August 2026 | `98b34f1ac6fdcba3a39fac9eab2b95e8a5e6d2945c4f9df3a24c0abb2080ef83` |
| 188 | [`00_admin/repository-index/INTEGRATION_CHECKLIST.md`](../00_admin/repository-index/INTEGRATION_CHECKLIST.md) | `current_strategy` | 84 | `integration_checklist` | Binding DEC-0031 loss-protection, verification, master, branch-cleanup and fresh-clone integration gate. | `5fba8681c981c37b0842a709615c6c66f97332dbb3d406c43421016fcb7b9f45` |
| 189 | [`03_research/exa_geo_research_raw.json`](../03_research/exa_geo_research_raw.json) | `evidence` | 20 | `research_source` | "Google AI Overviews 2026 Ranking & Passage Factors": [ | `f9d4f26a9e1be8e0c807047637d415dd44b8e045b7a90d4ebd0a4b7f3fc85827` |
| 190 | [`03_research/provider-strategy-2026-08-18/exa_raw.json`](../03_research/provider-strategy-2026-08-18/exa_raw.json) | `evidence` | 20 | `research_source` | "provider": "exa", | `2e287774ac4fb91713aaf57c56a9c37a68be02ab961c13b2ea1f3a5ef0035cd9` |
| 191 | [`03_research/provider-strategy-2026-08-18/firecrawl_raw.json`](../03_research/provider-strategy-2026-08-18/firecrawl_raw.json) | `evidence` | 20 | `research_source` | "retrievedatutc": "2026-08-18T21:24:13.379543+00:00", | `fae590132112c824dc57dc9e122917b1a02edaeea7ee4b5b06a330b82620b766` |
| 192 | [`03_research/provider-strategy-2026-08-18/worker_synthesis.md`](../03_research/provider-strategy-2026-08-18/worker_synthesis.md) | `evidence` | 20 | `research_source` | Stand: 18.08.2026 | `2a7a5a5a4424511ce1b9f0dadc771cc0616221ae5c86a2f01b99faf820bcee21` |
| 193 | [`AGENTS.md`](../AGENTS.md) | `current_authority` | 96 | `governance` | Current complete V2 operating instructions and mandatory authority order for execution agents. | `705cb0de4e0204cc0dbab74a205c40beaa4ab9c97b83000002928c489a193e0f` |
| 194 | [`CHANGELOG.md`](../CHANGELOG.md) | `current_strategy` | 62 | `governance` | Current version history with V2 Production-first implementation, repository consolidation and honest M10 boundaries. | `c15544806bbbba94d1eeb5bd6d1d29822fc643595ca23af0d6c629715563e43d` |
| 195 | [`CLAUDE.md`](../CLAUDE.md) | `current_authority` | 94 | `governance` | Current concise V2 operating contract for Claude and compatible coding agents. | `66e913c9b37809d8e62ecc20d380e20f47f707efa3b0c7c98dce71beaa1b2a0f` |
| 196 | [`README.md`](../README.md) | `current_authority` | 86 | `governance` | Current public overview of the V2 Core, Console, Delivery, Notion boundary and Production-first sequence. | `0c8c1b1c1a7174b788aa158760b623ca4ad400731282876d2dc8b2c07626aabe` |
| 197 | [`docs/00-current-production-architecture.md`](../docs/00-current-production-architecture.md) | `current_authority` | 94 | `architecture` | Canonical V2 architecture for Core, Console, Delivery, Notion, n8n, Step 3B, persistence and Production-first scope. | `2be27ed26bd8893ac8919cbca3c382f62f9d0441139fc28353e44c83243f72a6` |
| 198 | [`docs/01-review-abgleich.md`](../docs/01-review-abgleich.md) | `historical` | 18 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `c0f0c6145b62bb0ed90c516659f0e0045764cd3772658ecffde34eeac842302d` |
| 199 | [`docs/02-research-und-technische-spezifikation.md`](../docs/02-research-und-technische-spezifikation.md) | `historical` | 18 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `f6db485b5f37554e38c6d121286d28e0ae2e827acfe8cdfd9d9ea7815b550552` |
| 200 | [`docs/03-sprint-plan.md`](../docs/03-sprint-plan.md) | `superseded` | 15 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `77434e05f778d891930f54f4be51aa6755765900fd6925b5f1e6ca657f83500e` |
| 201 | [`docs/04-entscheidungslog.md`](../docs/04-entscheidungslog.md) | `superseded` | 15 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `b67c3870050235a548c114434134dfeec20b9712a9a1c823231d6fdb966633b6` |
| 202 | [`docs/05-human-in-the-loop.md`](../docs/05-human-in-the-loop.md) | `historical` | 18 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `49da5144643724dcd76e9c8a2d7e89d64bb72a506a99564a06cb19cdda93a697` |
| 203 | [`docs/06-pilot-abnahme-checkliste.md`](../docs/06-pilot-abnahme-checkliste.md) | `historical` | 18 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `da527fccab5792a84f7d170431aed07f9c23ff57cf68417be27d4e7f01555a40` |
| 204 | [`docs/07-geo-architecture-specification.md`](../docs/07-geo-architecture-specification.md) | `current_strategy` | 76 | `documentation` | Current GEO strategy source after local V2 contract restoration; real-output semantic verification remains open in M10. | `32a0883ba87f635f86832b8dcda94fc2524650e25826fae6653af21d30cc35b5` |
| 205 | [`docs/07-geo-research-und-copywriter-guidelines.pdf`](../docs/07-geo-research-und-copywriter-guidelines.pdf) | `evidence` | 25 | `documentation` | Supporting GEO research PDF retained as evidence beside the current Markdown strategy. | `21a86065c92a4ce2618b8f1bd2dc1d5c5b8d52a0e259b59cd495250d82e09f45` |
| 206 | [`docs/08-geo-sprint-plan-and-multi-agent-orchestration.md`](../docs/08-geo-sprint-plan-and-multi-agent-orchestration.md) | `superseded` | 15 | `documentation` | Projekt: Heartweb Claude Desktop SEO-Workflow Framework | `aa520104d44ef38b0cc3fa7a4839607094b0d4cf1a4d41551433d0194122839d` |
| 207 | [`docs/09-extension-and-evolution-guide.md`](../docs/09-extension-and-evolution-guide.md) | `current_authority` | 90 | `extension_guide` | Current authority for versioned prompt, contract, provider, tool, workflow and documentation evolution. | `6b61a24d634273c4ffed52b734641ac4ca8888102285e353e0aee1418e089ede` |
| 208 | [`docs/betriebshandbuch-claude-desktop.md`](../docs/betriebshandbuch-claude-desktop.md) | `historical` | 18 | `documentation` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `ba393555534d6b0ea2165ccb50eb407bbe7685adcd64e7fe4d07d03417276c70` |
| 209 | [`docs/copywriter-handoff-guidelines.md`](../docs/copywriter-handoff-guidelines.md) | `current_strategy` | 76 | `documentation` | Current boundary and quality guidance for human Copywriter work after the approved Heartweb handoff. | `3701f30b25eabfb42130215b1b6971517f9e5df4e966b8cc47eef5165fa8d21e` |
| 210 | [`docs/integrations/n8n-orchestration-model.md`](../docs/integrations/n8n-orchestration-model.md) | `current_authority` | 82 | `documentation` | Current DEC-0025 authority for concept orchestration, Notion handoff and scheduled Step-3B performance re-entry. | `288663a845e8216b466bf5509e0df75584a50b95c90f30e44f587f6f1108fc45` |
| 211 | [`docs/integrations/notion-operating-model.md`](../docs/integrations/notion-operating-model.md) | `current_authority` | 82 | `documentation` | Current DEC-0025 authority for one-way Notion project handoff, Notion-owned execution and Step-3B re-entry. | `ce4d890f3fd1dc89856d4d7fad49f174bee12de7a07f80f52082bede0ac600aa` |
| 212 | [`docs/jesse-walkthrough-memo.md`](../docs/jesse-walkthrough-memo.md) | `historical` | 12 | `documentation` | An: Jesse Jensen (Heartweb) | `101be189e29fb22f29914b861040008a363537ed068c190d2971c345461d76b1` |
| 213 | [`docs/jesse-walkthrough-memo.pdf`](../docs/jesse-walkthrough-memo.pdf) | `evidence` | 10 | `documentation` | Indexed PDF document: jesse walkthrough memo. | `91c4bd6aaf41ea49c2cfb693e91437b765192d7ab8c36f271e65a59fd5c4e7bc` |
| 214 | [`docs/operator-workflow-function-map.html`](../docs/operator-workflow-function-map.html) | `historical` | 15 | `documentation` | Historical generated Sprint-5 workflow map retained as visual Evidence until a final Product snapshot is available. | `1725d42109ea8e501813e5e59b1f79d8395136116bb60d20a20d530c19796e4f` |
| 215 | [`prompts/0-kickoff-v1.10.0.xml.md`](../prompts/0-kickoff-v1.10.0.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-0 prompt with deployment, provider-location and confirmed-capacity binding. | `eac03e7bc82437bb6a5a567ad8765c6cad4066a6816200ae91a29d7a5edf9e30` |
| 216 | [`prompts/0-kickoff-v1.9.0.xml.md`](../prompts/0-kickoff-v1.9.0.xml.md) | `superseded` | 22 | `prompt_contract` | Superseded deployment-bound Step-0 prompt retained for exact historical replay. | `f90a0cb583f095b671ff06e215b238127d75b98c21469dc279edcf4d701958ed` |
| 217 | [`prompts/0-kickoff.xml.md`](../prompts/0-kickoff.xml.md) | `superseded` | 20 | `prompt_contract` | Superseded unversioned Step-0 compatibility source retained for exact historical replay. | `4fe594f3ec13ceccb6c7f930585762a38b0420e735bcb87754d5d53de1391d00` |
| 218 | [`prompts/1-pillar-identifikation-v2.1.0.xml.md`](../prompts/1-pillar-identifikation-v2.1.0.xml.md) | `superseded` | 22 | `prompt_contract` | Immutable Step-1 predecessor retained before the logical Step-0 lineage correction. | `f6ef3f57a45a2f78ce35413e87075ade44d65be61387333f318f0b32d3ded7a6` |
| 219 | [`prompts/1-pillar-identifikation.xml.md`](../prompts/1-pillar-identifikation.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-1 prompt with released Step-0 lineage, crawl and SERP Evidence operations. | `4b0e3a25b150c4342ef6cc0a13bdee69246d10c6563da5ff42f75522bd5c1ef2` |
| 220 | [`prompts/1b-seitenarchitektur.xml.md`](../prompts/1b-seitenarchitektur.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-1B architecture and intent Evidence prompt. | `71d5bbbea3839aa447b60866de75cb3b31a764659572b704c33f9eb801667fac` |
| 221 | [`prompts/1c-pillar-template.xml.md`](../prompts/1c-pillar-template.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-1C design Evidence and reusable template prompt. | `7b12fac9cec125aa1932242a9a0d0b1fdf580cccd7faefa855a5c4c3bc1eefdb` |
| 222 | [`prompts/2-cluster-recherche.xml.md`](../prompts/2-cluster-recherche.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-2 prompt for provider keyword metrics without estimation. | `a3c498d84b4d7187a2a0335a5fc6607226870ad415c8e6ebcf7c664ca75aec23` |
| 223 | [`prompts/3-120-tage-plan.xml.md`](../prompts/3-120-tage-plan.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Step-3 strategy and deterministic capacity-solver prompt. | `adc175eb01d0cb92b4d9165a7e1ab8def889a5a9c3ea649789095e623a5e49e5` |
| 224 | [`prompts/3b-performance-check.xml.md`](../prompts/3b-performance-check.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound day-30, day-60 and day-90 adjustment-proposal prompt outside the initial route. | `ff5d5aff300823ab859e72f150a331fadab6b426b4de71d77350363872215369` |
| 225 | [`prompts/4a-content-briefing-und-schema.xml.md`](../prompts/4a-content-briefing-und-schema.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound Copywriter briefing, claim-ledger and JSON-LD validation prompt. | `f97bcd37990e8207916ff88c6ce4b0980aeefeecbfb77eeae1200a4bd5dec3f9` |
| 226 | [`prompts/4b-landingpage-html.xml.md`](../prompts/4b-landingpage-html.xml.md) | `current_authority` | 82 | `prompt_contract` | Active registry-bound typed Page Spec and staging-validation prompt. | `35520d1069c45b6346c3ed971489dfa21e46749b838418acfe941961201352bc` |
| 227 | [`prompts/intake-project-v2-v1.2.0.xml.md`](../prompts/intake-project-v2-v1.2.0.xml.md) | `superseded` | 22 | `prompt_contract` | Superseded multi-location intake prompt retained for exact historical replay. | `7dd0522b3f353d2e840988ad1448e187eaa0d2d374c2bc6ec726901f06ebbfab` |
| 228 | [`prompts/intake-project-v2-v1.3.0.xml.md`](../prompts/intake-project-v2-v1.3.0.xml.md) | `current_authority` | 82 | `prompt_contract` | Active intake-generation prompt with deployment and confirmed weekly-capacity binding. | `1599f8b0c61151612601280c807270a25ebb813b62e246868f7b0a1ae1b28f6a` |
| 229 | [`prompts/intake-project-v2.xml.md`](../prompts/intake-project-v2.xml.md) | `superseded` | 20 | `prompt_contract` | Superseded unversioned intake compatibility source retained for exact historical replay. | `16907a5db60c82353bd1bf902db4e587cc1b00f6f2765a1331707da5af42293c` |
| 230 | [`standards/api/operator-api.openapi.json`](../standards/api/operator-api.openapi.json) | `current_authority` | 85 | `standard_or_contract` | "components": { | `e1f7d8fdfc1bfa10de00bd5ac334af1c0c0e2b356663616b549422df4f175250` |
| 231 | [`standards/dateinamen-und-output-vertrag.md`](../standards/dateinamen-und-output-vertrag.md) | `current_authority` | 85 | `standard_or_contract` | Projekt: Modernisierung des Claude Desktop SEO-Workflows | `54a247282923e796c4bc6aff6ea4bd838775d63a58e7c61f44d85d64de1658a2` |
| 232 | [`standards/delivery/delivery-export-request.schema.json`](../standards/delivery/delivery-export-request.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `40115eefd76cb7c5c63c05c1923a7b04a8424f3c7afeb00b5a4c951fd534f3b4` |
| 233 | [`standards/delivery/delivery-export-result.schema.json`](../standards/delivery/delivery-export-result.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `024fe181e751c274379234e63cf4e7a705c062a89f0311c6d336c75296de1849` |
| 234 | [`standards/delivery/delivery-package-record.schema.json`](../standards/delivery/delivery-package-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fa9bd73faa07771622dd5e80752e6a76598b25c2271c79a17965fdc3274914d6` |
| 235 | [`standards/delivery/notion-import-manifest.schema.json`](../standards/delivery/notion-import-manifest.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `1f3febcd3ffeadc17fa61749268811af8c1a822ce2ee7950872258edfeb42bfe` |
| 236 | [`standards/delivery/role-handoff-manifest.schema.json`](../standards/delivery/role-handoff-manifest.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `56a018b53a46012a08c15c8f6b917366dac59a198d02330c8407ddddc1bfe196` |
| 237 | [`standards/design-system.css`](../standards/design-system.css) | `current_authority` | 85 | `standard_or_contract` | / | `f17b6c4fd007e82b54d647197500607e5a49eaabeb025f5dfcb84f0303511fc3` |
| 238 | [`standards/documentation/document-registry.schema.json`](../standards/documentation/document-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `5072e637631e669e3b2e2d8e25a8eaf203ee607ee7d7d6f34072c459525f70d3` |
| 239 | [`standards/domain/entity-domain-gbp.schema.json`](../standards/domain/entity-domain-gbp.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `8a16fa362f2935f0f4481af540adf420d689e13b764442b662da20cc210c6cef` |
| 240 | [`standards/domain/market-registry.json`](../standards/domain/market-registry.json) | `current_authority` | 85 | `standard_or_contract` | "registryversion": "v1.1.0", | `38da18d76f67f7c8c0ce599f044c8debb331d4a22dda2a5a790d4f0cd7e2b7dd` |
| 241 | [`standards/domain/market-registry.schema.json`](../standards/domain/market-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `d4d99c7420445132ac93a4ad40c14336897edfb0f6d576860249ce884d03b8ac` |
| 242 | [`standards/domain/project.schema.json`](../standards/domain/project.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `ff4e377a2b40e2c3ebdbc7d708544f629bca30ba6c8a8e7e23de00c29e152087` |
| 243 | [`standards/domain/provider-location-registry.json`](../standards/domain/provider-location-registry.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://heartweb.example/schema/provider-location-registry.schema.json", | `88cb7b7abf52f805fde7bd33960f704829bcb191ba181fd894f7b1a6b734cde2` |
| 244 | [`standards/domain/provider-location-registry.schema.json`](../standards/domain/provider-location-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `aa0130908955ded6dd58d362b25fa1547fa972e6803d78ac1d5734138dc34b42` |
| 245 | [`standards/domain/risk-compliance.schema.json`](../standards/domain/risk-compliance.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `c3e73199aa7a0025b595cea9a520ed18f4b28c1c2c8a0c8e3f9ff3d1e8e624fd` |
| 246 | [`standards/domain/search-deployment.schema.json`](../standards/domain/search-deployment.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `89fb22144270b34595203c5fa6326c6638846da1ce8b09e5c462ad97eed526d9` |
| 247 | [`standards/integrations/event-catalog-v2.json`](../standards/integrations/event-catalog-v2.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `2e0e7e2986d05fac7aa0f09fbae8e3e86bf05e8faae74309f256b7d569fbd020` |
| 248 | [`standards/integrations/event-catalog.json`](../standards/integrations/event-catalog.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `2117bf672a975c7343a55349211339ae84b3428ac53abc15a56c3b798a96bdba` |
| 249 | [`standards/integrations/n8n-command.schema.json`](../standards/integrations/n8n-command.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `92537292d562bd5574806dc39e74884ddf09a97ea968ed4723afa5751369fa21` |
| 250 | [`standards/integrations/n8n-dlq-entry.schema.json`](../standards/integrations/n8n-dlq-entry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `9b0a86a4dbeffeb92a2c8d2f1fc8a9b592ac565e059a12eee57e0fa45a7bfbce` |
| 251 | [`standards/integrations/n8n-retry-entry.schema.json`](../standards/integrations/n8n-retry-entry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `37e3151016cc23ad4d772902407847d05ca0b6ba57f2bdc2e5dc4f93386d6082` |
| 252 | [`standards/integrations/n8n-simulation-state.schema.json`](../standards/integrations/n8n-simulation-state.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `2bf06f7cf6aa9b79cc7505e6595aa93451d4be9377dd1bd51d60fd17577c76fd` |
| 253 | [`standards/integrations/n8n-wait-subscription.schema.json`](../standards/integrations/n8n-wait-subscription.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `8bade1792d8e43c53eb5771bee70e4b988b291039bc04b4ecf725cc200d46ec7` |
| 254 | [`standards/integrations/notion-projection-v2.schema.json`](../standards/integrations/notion-projection-v2.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `b6dacffeba86987a33422091ef0e3281b78baae69e246a1c4302a2a4e4258b47` |
| 255 | [`standards/integrations/notion-projection.schema.json`](../standards/integrations/notion-projection.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `afbec5cd1c5bf1d4a6fec97eb258eb9248103c102e5fcb8dc21cac972eee325a` |
| 256 | [`standards/integrations/notion-proposal.schema.json`](../standards/integrations/notion-proposal.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `159874f5e86fd0501186afd4a3a49864cc54f901700ecd483aa6be99ef38a685` |
| 257 | [`standards/integrations/notion-record-v2.schema.json`](../standards/integrations/notion-record-v2.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fac5a00000c2988b1780555b5166b1890718d20a7da69e390dadd946350a2966` |
| 258 | [`standards/integrations/notion-snapshot.schema.json`](../standards/integrations/notion-snapshot.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `2fcc0f92f90b3920638aaf5bb9d15b7283386a48e7401ce8a4268ac5615ce193` |
| 259 | [`standards/integrations/workflow-event-v2.schema.json`](../standards/integrations/workflow-event-v2.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `8872e58d1dff3d341377c4ebbdbe031946bcd2614e95726573e1cac890fdc967` |
| 260 | [`standards/integrations/workflow-event.schema.json`](../standards/integrations/workflow-event.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `cf49b1790c7350061a0ce0c21a9c69a5b5e6708748daf493aee1231a6f76f29b` |
| 261 | [`standards/location-codes.json`](../standards/location-codes.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `1b7ddd7116f6a2127f1a223b5594f25423e931b540ca4ee173cc5685b0bf16e2` |
| 262 | [`standards/manifest-v2.schema.json`](../standards/manifest-v2.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `a8ea8b91513c00dec56a65293f33231732a6178f40e7aae9df7c83de73333c82` |
| 263 | [`standards/manifest.schema.json`](../standards/manifest.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `11a12dbc27ab4a1d236ea7ade81177011411a5e4d235eb00685b2747ccd8d760` |
| 264 | [`standards/operator/blocker-record.schema.json`](../standards/operator/blocker-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fe362b075aa13373ee4864c6ae50d5a55dd89e1b4cb8e554261adf32c5eaccbb` |
| 265 | [`standards/operator/error-routing-policy.json`](../standards/operator/error-routing-policy.json) | `current_authority` | 85 | `standard_or_contract` | "schemaversion": "1.0.0", | `efb012a04292cd975d0ab144be15dd434658f660f54a03cded649c1c6e22eef5` |
| 266 | [`standards/operator/error-routing-policy.schema.json`](../standards/operator/error-routing-policy.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `0a898b3f33ff40fb0b53099568e39133d3140eedf826720af9b36f9d3dd94516` |
| 267 | [`standards/operator/escalation-record.schema.json`](../standards/operator/escalation-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `b968135d1310731a593450c317eabc8dc43f714699e2aa595e2e89b87e37c33a` |
| 268 | [`standards/operator/intake-project-draft.schema.json`](../standards/operator/intake-project-draft.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `ab74a89e851773110903f5afb7d580c07ad256099b71b6436ca6c11715b75adc` |
| 269 | [`standards/operator/operator-task.schema.json`](../standards/operator/operator-task.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `139880d1df4011712d3960644f71b53ed85ef0675ce925341bf42c68b307d2f8` |
| 270 | [`standards/operator/production-steering.schema.json`](../standards/operator/production-steering.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `587c93fa196917e759ed56a698b1ecf05a2da158617168cbfa83c5db9b4d65db` |
| 271 | [`standards/operator/resolution-record.schema.json`](../standards/operator/resolution-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `ac67497c85fd8490dcecf4b08d0e97aa4266fff16f8b7371f9c77f6edea3b22b` |
| 272 | [`standards/operator/revision-request.schema.json`](../standards/operator/revision-request.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `34ccb7cdc58da395d8b22977d35e6fb63a713bc94a5b1113515e715ba4479e2a` |
| 273 | [`standards/operator/workflow-defect.schema.json`](../standards/operator/workflow-defect.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `f3660967176f46b8ae4b5681074c01933231ec23aea5589aa59e6fe8affbdf89` |
| 274 | [`standards/outputs/claim-ledger.schema.json`](../standards/outputs/claim-ledger.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `945f23deec09ec8d371365eae4d8a4fef37f320f45e161c0c048d758f26ff990` |
| 275 | [`standards/outputs/staging-evidence.schema.json`](../standards/outputs/staging-evidence.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://heartweb.example/schema/outputs/staging-evidence.schema.json", "title": "Heartweb Staging Evidence", "type": "object", "additionalProperties": false, | `7a288946ba24f407dbd613e568ceb0cf1830d2cdf678002d7edac32034ce7d01` |
| 276 | [`standards/outputs/step-1-topic-inventory.schema.json`](../standards/outputs/step-1-topic-inventory.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `3efe1839ecdb511db63410480c58a78daae655206464efbac39bc9d9dbd35ec1` |
| 277 | [`standards/outputs/step-1b-architecture.schema.json`](../standards/outputs/step-1b-architecture.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `cd187aa294670c53cab379086e5efc00ef3400fa30e39c176655453710353ba7` |
| 278 | [`standards/outputs/step-1c-design-system.schema.json`](../standards/outputs/step-1c-design-system.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `51a6c601505000e346d79c258910ca705876ec756fefb1cc26d6e5ea507cc7d4` |
| 279 | [`standards/outputs/step-1c-template.schema.json`](../standards/outputs/step-1c-template.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `705e3bd944f62256ddbad4450ec857dc01607359f6493c2604fa748877ce4056` |
| 280 | [`standards/outputs/step-2-keyword-evidence.schema.json`](../standards/outputs/step-2-keyword-evidence.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `7bbdb5d62d0e6cda64713e9525adc984b904668ecea241f05c7dd7a0d2a2948b` |
| 281 | [`standards/outputs/step-3-plan.schema.json`](../standards/outputs/step-3-plan.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://heartweb.example/schema/outputs/step-3-plan.schema.json", "title": "Heartweb Step 3 Deterministic Plan V2", "type": "object", "additionalProperties": false, | `91322528c18d5f28da8f1371c93cbfca34e2917ab8b3f54dabd68769ba10976f` |
| 282 | [`standards/outputs/step-3b-adjustment.schema.json`](../standards/outputs/step-3b-adjustment.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://heartweb.example/schema/outputs/step-3b-adjustment.schema.json", "title": "Heartweb Step 3B Immutable Adjustment Candidate", "type": "object", "additionalProperties": false, | `42be410fab80415a8afb8eca3675d4760e64800c69106a56261ced73fd8b0f9b` |
| 283 | [`standards/outputs/step-4a-briefing.schema.json`](../standards/outputs/step-4a-briefing.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `dc9d7731d70f5bee4f0e4b99ce292c2dc1991767f2f413e043e80552b3d14093` |
| 284 | [`standards/outputs/step-4b-page-spec.schema.json`](../standards/outputs/step-4b-page-spec.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fd8d3179e18eaad26a5be788a8d97aaa5c84dca8bb27fd3c40d86dfb0d2f8aae` |
| 285 | [`standards/providers/research-request.schema.json`](../standards/providers/research-request.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `f7bd94dbbe36f766157088220557fe6f1289cd4c59791a02dde6884340033906` |
| 286 | [`standards/providers/research-response.schema.json`](../standards/providers/research-response.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fad51f6fa6d5094801a8cf7567f2128511af83d4f44d85cfe08cac6f25bac950` |
| 287 | [`standards/quality/crawl-disposition-policy.json`](../standards/quality/crawl-disposition-policy.json) | `current_authority` | 85 | `standard_or_contract` | "policyid": "heartweb-crawl-disposition", | `f9e0e16519153be393a00e42d7a04d9d13295358e536548af242d668d92c03c8` |
| 288 | [`standards/quality/crawl-disposition-policy.schema.json`](../standards/quality/crawl-disposition-policy.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `b12ec394f965f63776b45ed4766dbe9385cc3f91d4d04b51df845ec6bea0e87b` |
| 289 | [`standards/quality/quality-gate-registry.json`](../standards/quality/quality-gate-registry.json) | `current_authority` | 85 | `standard_or_contract` | "schemaversion": "1.1.0", | `949fb6764a3d80727da4f13398ea5b367185f54835a13e299f2e1d61d1758cb0` |
| 290 | [`standards/quality/quality-gate-registry.schema.json`](../standards/quality/quality-gate-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `6ee05688d747ff1fa580a8b5f542fba645be5e9da452fc0f722e37c17a616067` |
| 291 | [`standards/quality/screaming-frog-crawl.schema.json`](../standards/quality/screaming-frog-crawl.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `fb4e77416ff8b4bee6969e07b72fbeb83a1c3a5fa1da42cf57e0399a2bab6d31` |
| 292 | [`standards/runtime/agent-tool-policy.schema.json`](../standards/runtime/agent-tool-policy.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `906b83652aef28cd05f26bf510e27e2d9c4f130c2b07ec639cd0728f78292ad4` |
| 293 | [`standards/runtime/approval-record.schema.json`](../standards/runtime/approval-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `afc066da03cf0b05d39b78e1c85863cf44d9301d86f448047ec265cc6c3cb118` |
| 294 | [`standards/runtime/artifact-record.schema.json`](../standards/runtime/artifact-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `bc9812312ee9339072f97f25ce5af7f0f50823feef812c1d5766271b87a1bf4b` |
| 295 | [`standards/runtime/claim-record.schema.json`](../standards/runtime/claim-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `67953b85cc0fdc27502d20d912bfd7ff0ae581a4b92755128b8f0e1b6ba5d804` |
| 296 | [`standards/runtime/context-package.schema.json`](../standards/runtime/context-package.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `add24025db8dd4329c542eeabf1ae574c83ebf743c54c114ff72a4fb2f1de9bd` |
| 297 | [`standards/runtime/error-envelope.schema.json`](../standards/runtime/error-envelope.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `99cdf2f5cca1f6cf133b66c7f3fd36e9e8d5f641c7188047902e9df6959ca38e` |
| 298 | [`standards/runtime/evidence-record.schema.json`](../standards/runtime/evidence-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `d623897bd6b3a8e8cf8a53620c1106883709c4aaeaba6e625aa674139f2dba71` |
| 299 | [`standards/runtime/llm-run-request.schema.json`](../standards/runtime/llm-run-request.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `9ee8caa691e75737131e384e64f0e7740ed5eadda65bf10200bb244b5c880c98` |
| 300 | [`standards/runtime/llm-run-result.schema.json`](../standards/runtime/llm-run-result.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `64ba136d92c7ea9cfabf9d5d6955e20554e2c77726733519d3afe040bbc0290b` |
| 301 | [`standards/runtime/logical-project-session.schema.json`](../standards/runtime/logical-project-session.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `7ef55bcb9df90ca68e6cae6f1f75b01f58883d7a19e0477f291c20e5e2f69a8e` |
| 302 | [`standards/runtime/official-prompt-registry.json`](../standards/runtime/official-prompt-registry.json) | `current_authority` | 85 | `standard_or_contract` | "entries": [ | `7824aa57348fb36fe0a7a439d07233f1d228de69ea93aec23cfbd37dad178cc9` |
| 303 | [`standards/runtime/official-prompt-registry.schema.json`](../standards/runtime/official-prompt-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `503c99ba73824d5aaf503e5da6e655fd73febc7641958504ab27e3699ff0c912` |
| 304 | [`standards/runtime/operator-worker-profile.json`](../standards/runtime/operator-worker-profile.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-heartweb-operator", | `21e4d90bc4006f39cb6dd5fe46934f54de1c0515f34243d46107f4a2ef42878d` |
| 305 | [`standards/runtime/quality-gate-run.schema.json`](../standards/runtime/quality-gate-run.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `c5fff5eee4e5791aa97a1e5c97cbbe9f7c674ea8d6fbc494651d695b01d8fdc4` |
| 306 | [`standards/runtime/release-record.schema.json`](../standards/runtime/release-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `a85e597e2f22b2a2de787b7602f9ae80168baa0ea719fab7c5b5a42c27b5e0cb` |
| 307 | [`standards/runtime/run-envelope.schema.json`](../standards/runtime/run-envelope.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `4b964f21561466490806b8060e1d6b3cf96594b2db570da73ac380b171e2f7bc` |
| 308 | [`standards/runtime/step-agent-output-envelope.schema.json`](../standards/runtime/step-agent-output-envelope.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `95a42b9c9e883d74267ede72fdfdc0469ecd9c0dc203ecf7915f7fcaddfae9af` |
| 309 | [`standards/runtime/step-agent-registry.json`](../standards/runtime/step-agent-registry.json) | `current_authority` | 85 | `standard_or_contract` | "registryid": "heartweb-step-agent-registry", | `f891a53384ed0f5f1e36782d1022297c712cd99b9bc43c3147ad007282eabea9` |
| 310 | [`standards/runtime/step-agent-registry.schema.json`](../standards/runtime/step-agent-registry.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `a9cc7625cdfe27570062c929fabf2563a2fdd7cbc68430a50245db1a690ae69f` |
| 311 | [`standards/runtime/tool-policies/step-0-agent.json`](../standards/runtime/tool-policies/step-0-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-0-agent", | `c18fde0968caddd9f33c32eebbcc06a0d604ddb5130bae311aa9d1f1128ff7de` |
| 312 | [`standards/runtime/tool-policies/step-1-agent.json`](../standards/runtime/tool-policies/step-1-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-1-agent", | `185dd362fbadaad93f7934ef99acbd9691c9457a6354737c4eb9fb895aa6c7d3` |
| 313 | [`standards/runtime/tool-policies/step-1b-agent.json`](../standards/runtime/tool-policies/step-1b-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-1b-agent", | `d35932483259861da83194e678a9c54c9c8c1324057586720d854d85b29d6e60` |
| 314 | [`standards/runtime/tool-policies/step-1c-agent.json`](../standards/runtime/tool-policies/step-1c-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-1c-agent", | `c38512d523863eda8908aa684fd717203d82ad4fa63bc2e12b21e0da5def73d6` |
| 315 | [`standards/runtime/tool-policies/step-2-agent.json`](../standards/runtime/tool-policies/step-2-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-2-agent", | `b8b30795d92acee799e0a843abee1bc21855050fea8c22d28be0dcf41909a724` |
| 316 | [`standards/runtime/tool-policies/step-3-agent.json`](../standards/runtime/tool-policies/step-3-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-3-agent", | `c79e3b43e2c5337822bd77357aae68297a7dc55d94827cf0381c37069e42eca4` |
| 317 | [`standards/runtime/tool-policies/step-4a-agent.json`](../standards/runtime/tool-policies/step-4a-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-4a-agent", | `01a8d1b70a44e59d63d4a2e0236621ca292acc72b5b9d280c665a72fb59a786f` |
| 318 | [`standards/runtime/tool-policies/step-4b-agent.json`](../standards/runtime/tool-policies/step-4b-agent.json) | `current_authority` | 85 | `standard_or_contract` | "toolpolicyid": "tool-policy-step-4b-agent", | `8979e17c7c49226058f0f360d5f832950127a48a41b9f0da14ec7c30b9a1c3a0` |
| 319 | [`standards/runtime/transition-command.schema.json`](../standards/runtime/transition-command.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `8eb3a3be944324c2d70e4f5e8b8c4bfd8900ad6dc1dfda27e139b7b8f42a4cf1` |
| 320 | [`standards/runtime/waiver-record.schema.json`](../standards/runtime/waiver-record.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `54a3deaf55e9e7b351b0ad9cd72a851e46b14e366dc41476003feb34c163b5e4` |
| 321 | [`standards/runtime/worker-profile.schema.json`](../standards/runtime/worker-profile.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `3384f9687452946908339699e8ce684cd0ef83a321e74d2f40c74fa13d6ef47c` |
| 322 | [`standards/runtime/worker-profiles/step-0-agent.json`](../standards/runtime/worker-profiles/step-0-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-0-agent", | `9bb16a0f24bc916817efc5eb9c08446d119bca1c31f0870bbffecb67d6f42107` |
| 323 | [`standards/runtime/worker-profiles/step-1-agent.json`](../standards/runtime/worker-profiles/step-1-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-1-agent", | `ca9c3c2905fcb1947d98167497cbc0fc07e38bd78ee2cc8debe46d5114c5fa4a` |
| 324 | [`standards/runtime/worker-profiles/step-1b-agent.json`](../standards/runtime/worker-profiles/step-1b-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-1b-agent", | `c862e7c1fd3c16c235c6c751026841e7049f00f841ee98d3ae68dc7ff0d74245` |
| 325 | [`standards/runtime/worker-profiles/step-1c-agent.json`](../standards/runtime/worker-profiles/step-1c-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-1c-agent", | `07c53c7bf68921bfd71297e46714066dfed2fd6bda8f664428500a31db7664e9` |
| 326 | [`standards/runtime/worker-profiles/step-2-agent.json`](../standards/runtime/worker-profiles/step-2-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-2-agent", | `1476af6b171c18b01e90c69d67508c1baab37312ff39ef402621d99f201a8eae` |
| 327 | [`standards/runtime/worker-profiles/step-3-agent.json`](../standards/runtime/worker-profiles/step-3-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-3-agent", | `822d263765fd9d6cc72fbe947183e60b098d703fbb3d2142bdcafc8e1025eae2` |
| 328 | [`standards/runtime/worker-profiles/step-4a-agent.json`](../standards/runtime/worker-profiles/step-4a-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-4a-agent", | `20e5ca8bf85d394257be6a9a4725da2b053de2ca085d830ec9885c2b4c9f995d` |
| 329 | [`standards/runtime/worker-profiles/step-4b-agent.json`](../standards/runtime/worker-profiles/step-4b-agent.json) | `current_authority` | 85 | `standard_or_contract` | "workerprofileid": "worker-profile-step-4b-agent", | `36df6454068fa2b72565097e703de343bfe405707b93526d7ee1db371ddb2a47` |
| 330 | [`standards/testing/PROTOTYPE_TEST_POLICY.md`](../standards/testing/PROTOTYPE_TEST_POLICY.md) | `current_authority` | 97 | `test_policy` | Binding Production-first authority for baseline-plus-delta evidence, affected dependency closure selection and the final route-based prototype matrix. | `72b28ebfcbadfd8bef7a31b90cfcb07e8ce081ecb7cc33f78c5db92154bdb2d4` |
| 331 | [`standards/workflow/workflow-graph.json`](../standards/workflow/workflow-graph.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://heartweb.example/schema/workflow/workflow-graph.schema.json", | `ced2d85e366c284aca3578efaee0eb6ca523b1437cc87b46260df4d61b61b8ff` |
| 332 | [`standards/workflow/workflow-graph.schema.json`](../standards/workflow/workflow-graph.schema.json) | `current_authority` | 85 | `standard_or_contract` | "$schema": "https://json-schema.org/draft/2020-12/schema", | `73ebdf8851e9a30c7084a7fb0920e5157e7e024d7743803cf9b09966d17e6ae4` |
| 333 | [`tests/acceptance-tests.md`](../tests/acceptance-tests.md) | `evidence` | 30 | `test_evidence` | Projekt: Heartweb Claude Desktop SEO & GEO Workflow Framework | `25550bdb5918fe7df3f288a0bad760a19dbbdad74150d3e79adb6a5bddc32e70` |

## 16. Branch and fresh-clone continuation

- Canonical integration target: `master`.
- Required continuation branch after remote and fresh-clone SHA verification: `feature/production-workflow-continuation`.
- Exact live commit identity must be read from `git rev-parse master`, `git rev-parse origin/master` and the fresh clone. Do not infer it from prose.
- Delete an old branch only after `git merge-base --is-ancestor <tip> master` succeeds or an explicit semantic-reconciliation record proves its content is represented and its tip is preserved in the final graph.
- The external customer workspace is not inside the repository replacement and must remain unchanged.
