# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 20. August 2026
**Status:** End-to-End Operator Workflow System in Ausfuehrung. Sprint 4 ist vollstaendig implementiert und verifiziert. Sprint 5 Operator Console ist aktiv, Packages 1 und 2 sind abgeschlossen.
**GitHub Repository:** https://github.com/Frater418/claude-desktop-seo-workflow-production  
**Kanonischer Pfad:** `C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow\`  
**Desktop-Pfad:** `C:\Users\offic\Desktop\Heartweb\claude-desktop-seo-workflow-production\`  

---

## 1. Projekt-Kontext & Rollen

- **Ziel:** Modernisierung und Automatisierung des 120-Tage-SEO-Rollout-Workflows fuer die Claude Desktop App inklusive Generative Engine Optimization (GEO).
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
   - `capacity_matrix_solver.py` (v1.2.0): Verteilt die Deliverables auf einen Horizont von 17 Wochen mit maximal 15 Stunden pro Woche und weist die Anzahl aktiver Wochen aus. 100% Pflichtabdeckung fuer lokale Landingpages und Verlinkungs-Maps.
   - `validate_schema_jsonld.py`: Autarke Validierung fuer Google Rich Results.
   - `tool-contracts/`: Formale Schemas fuer AgentSEO API-Calls.

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

### Aktueller Planungsstand vom 19. August 2026

- Kanonischer Masterplan: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- Primaerer Pilotoperator: Raphael Rechberger.
- Zentrale spaetere Firmenoberflaeche: Notion.
- Eigene UI: spezialisierte, aus Notion erreichbare Workflow-, Review- und Praesentationsansicht.
- n8n: spaetere Orchestrierung und Middleware. Fuer die lokale Pilotwelle nur versionierter Simulator.
- Golden Path: AHD Hausbesuch.
- AHD Step 0 und GATE-0: abgeschlossen und als unveraenderliche Baseline geschuetzt.
- AHD Step 1: Staging-Kandidat vorhanden, aber noch nicht released.
- AHD Step 1b und alle Folgeschritte: nicht gestartet.
- Ziel der naechsten Ausfuehrungswelle: ein vollstaendiger lokaler Durchlauf von 0 bis 4b mit Operator Console, Tickets, Gates, Praesentationsmatrix und einem priorisierten 4a/4b-Vertical-Slice.
- Schritt 3b bleibt sichtbar, aber bis zu realen Post-Publication-Daten auf `not_due`.
- Reale Notion- und n8n-Verbindungen, Live-Deployment und 120-Tage-Performance sind nicht Bestandteil der lokalen Demonstrationswelle.
### Ausfuehrungsstand vom 19. August 2026

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
- Sichtbare Demo: `http://127.0.0.1:4173/?mode=demo`, solange der lokale Vite-Server laeuft.
- Kompressionssicherer Fortsetzungspunkt: `00_admin/audits/2026-08-19-e2e-demo/sprint-4/CURRENT_POINT_OF_WORK.md`.
- Naechster Gate: Sprint 5 Package 3 mit Taskqueue, Review Center, Integrationsstatus und Praesentationsmatrix implementieren.

### Aktive Risiken und externe Voraussetzungen

1. Step 2 des spaeteren AHD-Livelaufs benoetigt realen, geo-korrekten Providerzugang. Keine Ersatzwerte.
2. Der reale AHD Crawl 005 besitzt eine Resource-404, die sichtbar geroutet und vor Production aufgeloest werden muss.
3. Reale Notion- und n8n-Verbindungen sind noch nicht konfiguriert. Sprint 4 baut versionierte lokale Simulatoren mit denselben Commands, Events und Projektionen.
4. Der UI-Stack beginnt jetzt in Sprint 5 und nutzt ausschliesslich die in Stage D generierten API-Typen.
5. Der bestaetigte Performance-Zyklus fuer Notion, n8n und Step 3b ist Tag 30, 60 und 90.

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
2. Keine Em-Dashes oder En-Dashes. Nur Bindestriche (-), Doppelpunkte oder klare Satzstrukturen.
3. Strikte Fail-Fast-Doktrin (keine Schaetzwerte, harter Stopp bei API- oder Datenfehlern).
4. Strikte Trennung zwischen Framework-Library (`Heartweb-Claude-Desktop-SEO-Workflow`) und individuellem Kunden-Workspace (`Heartweb\Kunden\<slug>\`).
5. Zielmarkt immer als `country` plus `location_code` uebergeben, AgentSEO immer mit `sync: false` und `agentseo_job_status`, Mengenregeln immer als Zahl in das Manifest schreiben (ADR-008 bis ADR-010).
