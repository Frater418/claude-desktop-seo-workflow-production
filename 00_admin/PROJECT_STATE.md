# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 23. August 2026
**Status:** Production-first Completion in Ausfuehrung. Sieben von 13 Ausfuehrungsstufen einschliesslich Sprint 5E und neun von zehn Release-Haupttasks sind abgeschlossen. M08 Outputqualitaet, M08L realer LLM-Ausfuehrungspfad und M09 Production Release Audit sind abgeschlossen. M10 erster kontrollierter lokaler Production-Output steht am Input- und Provider-Preflight gemaess `00_admin/MASTER_TASK_MATRIX.md`.
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
   - `manifest.schema.json`: JSON Schema Draft 2020-12 fuer den Mandanten-Steckbrief `manifest.json`.
   - `design-system.css`: Autarke CSS-Token-Schablone (Farben, Typo, Cards, Buttons) fuer Landingpages.
   - `dateinamen-und-output-vertrag.md`: Verbindliche Pfade und Dateinamen fuer alle Schritte.
   - `location-codes.json`: Verbindliche Zielmarkt-Codes fuer AgentSEO (DE 2276, AT 2040, CH 2756).

2. **9 Produktions-Prompts (`prompts/`):**
   - `0-kickoff.xml.md`: Initialisiert `manifest.json`.
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
   - Aktuelle Providergrenze: Provider Gateway mit DataForSEO primaer und AgentSEO nur bedingt. Alte `mcp/tool-contracts/` sind Legacy-Kandidaten.

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

### Aktueller Planungs- und Ausfuehrungsstand vom 22. August 2026

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
- M08L ist abgeschlossen. Der duenne Hermes-Runs-Adapter bestand einen echten neutralen Step-0-Lauf mit schema-validem Manifest, persistiertem Context Package und LLM Result, Provider Run ID, `gpt-5.6-sol`, Token Usage und null Toolcalls. Allgemeine Backend-Plattform, separate Execution-Record-Persistenz, Multi-Provider-Adapter und Subagent-Orchestrierung bleiben Post-M10. Evidence: `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.
- M09 ist abgeschlossen und vom Hermes Controller akzeptiert. PT-01 bis PT-10 sind gruen, offene P0/P1 sind null, der aktuelle 1280x900-Chrome-Smoke besitzt 23 Checks und null Console-, Request- oder HTTP-Fehler. Evidence: `00_admin/audits/2026-08-24-m09-route-matrix/SECTION_11_REPORT.md`.
- Schritt 3b bleibt bis zu realen Post-Publication-Daten auf `not_due`.
- Kein Deployment und kein Merge nach `master` vor Final-Gate und DEC-0022-Konsolidierung.
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
- Aktiver Entwicklungsbranch: `feature/e2e-operator-workflow-system`. Kein Commit oder Push auf `master` vor vollstaendigem Workflow, tiefer Dokumentation, unabhaengiger Finalauditierung und expliziter Freigabe durch Raphael.
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

### Aktive Risiken und externe Voraussetzungen

1. Step 2 des spaeteren AHD-Livelaufs benoetigt realen, geo-korrekten Providerzugang. Keine Ersatzwerte.
2. Der reale AHD Crawl 005 besitzt eine Resource-404, die sichtbar geroutet und vor Production aufgeloest werden muss.
3. Reale Notion- und n8n-Verbindungen sind noch nicht konfiguriert. Sprint 4 baut versionierte lokale Simulatoren mit denselben Commands, Events und Projektionen.
4. Der UI-Stack, das visuelle Browser-Gate, Delivery, Diagnose, M08 Outputqualitaet und M08L realer LLM-Testadapter sind fokussiert abgeschlossen. Offen sind M09 Release-Matrix und M10 erster kontrollierter Output.
5. Der bestaetigte Performance-Zyklus fuer Notion, n8n und Step 3b ist Tag 30, 60 und 90.
6. Verbindliche spaetere Nacharbeit: Beim V2-Umbau wurden konkrete ADR-011-Anforderungen fuer Step 4a und Step 4b nicht vollstaendig in die ausfuehrbaren Schemas, Prompts und Validatoren uebernommen. Nach stabilem Sprint-5-/5E-Abschluss ist `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` auszufuehren. Vorher darf keine vollstaendige GEO-Produktionsqualitaet fuer Copywriter- und Developer-Pakete behauptet werden.
7. Kanonischer Sammelpunkt fuer neue Probleme, Verbesserungen, UI-Feedback und spaetere Integrationsarbeit ist `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`. Das Erfassen eines Punkts autorisiert keine sofortige Umsetzung. Der Backlog wird erst nach stabiler Basis und ausdruecklicher Freigabe in einem Integrations-Sprint abgearbeitet.
8. Der Repository-Hygiene-Audit identifiziert stale Dependency-/PID-Artefakte, einen exakten Planbild-Duplikat, produktiv unerreichbaren Demo-UI-Code, Legacy-Providervertraege und veraltete Dokumentation. Nichts davon wird waehrend des aktiven Browser-/Delivery-Gates destruktiv bereinigt.
9. Der Prompt-Paritaets-Audit zeigt zusaetzliche outputkritische V2-Luecken in 1B, 1C, Step 2/3 und 3B sowie die bereits bekannte 4A/4B-Nacharbeit. Die Architektur wird nicht zurueckgerollt. Vor dem ersten Output werden nur 1B/1C, Step 2/3 und 4A/4B releasekritisch restauriert. Step 3B und die vollstaendige Real-Output-Paritaet folgen Post-Release.
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
5. Zielmarkt immer als Land, Provider-Location-Code und Sprache binden. Providerdaten laufen ausschliesslich ueber Provider Gateway, DataForSEO primaer und AgentSEO nur bei passender Capability. Keine stillen Defaults oder Ersatzwerte.
