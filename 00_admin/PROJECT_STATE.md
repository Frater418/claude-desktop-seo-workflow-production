# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 17. August 2026  
**Status:** Auditiert, Version 1.3.0 in Arbeit auf Branch `fix/schritt-2-und-doku-1.3.0`. Sieben offene Punkte, siehe CHANGELOG 1.3.0.  
**GitHub Repository:** https://github.com/Frater418/claude-desktop-seo-workflow-production  
**Kanonischer Pfad:** `C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow\`  
**Desktop-Pfad:** `C:\Users\offic\Desktop\Heartweb\claude-desktop-seo-workflow-production\`  

---

## 1. Projekt-Kontext & Rollen

- **Ziel:** Modernisierung und Automatisierung des 120-Tage-SEO-Rollout-Workflows fuer die Claude Desktop App.
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
   - `capacity_matrix_solver.py` (v1.2.0): Verteilt die Deliverables auf einen Horizont von 17 Wochen mit maximal 15 Stunden pro Woche und weist die Anzahl aktiver Wochen aus. 100% Pflichtabdeckung fuer lokale Landingpages und Verlinkungs-Maps. Offen: die Untergrenze von 10 Stunden wird nicht erzwungen, siehe docs/04-entscheidungslog.md.
   - `validate_schema_jsonld.py`: Autarke Validierung fuer Google Rich Results. Offen: keine CLI, siehe tests/acceptance-tests.md.
   - `tool-contracts/`: Formale Schemas fuer AgentSEO API-Calls.

4. **Dokumentation & Handbuecher (`docs/`):**
   - `betriebshandbuch-claude-desktop.md`: Schritt-fuer-Schritt-Anleitung fuer die Desktop App & Projects.
   - `copywriter-handoff-guidelines.md`: Leitfaden fuer die Notion-Uebergabe an Regina, Katja, Alexander.
   - `jesse-walkthrough-memo.pdf`: Exakt ausbalanciertes 2-Seiten-Memo fuer Jesse.
   - `01-review-abgleich.md`, `02-research-und-technische-spezifikation.md`, `03-sprint-plan.md`, `04-entscheidungslog.md`, `05-human-in-the-loop.md`, `06-pilot-abnahme-checkliste.md`.

5. **Akzeptanztests & Fixtures (`tests/`):**
   - Akzeptanztests neu ausgefuehrt am 17.08.2026: 1 bestanden mit offenem Punkt, 2 teilweise bestanden, 1 nicht ausfuehrbar, 1 nicht bestanden (`tests/acceptance-tests.md`).
   - Fixtures fuer simCura Pflegedienst (`sample_manifest.json`, `sample_cluster_keywords.json` mit 61 synthetischen, formelgenerierten Keywords ohne Live-Metriken).

---

## 2b. Stand vom 17. August 2026

- **Konsistenz-Audit durchgefuehrt:** `00_admin/AUDIT-2026-08-17-konsistenz.md`. 58 Findings, davon 4 Blocker.
- **Erster Live-Testlauf gegen AgentSEO:** Schritte 0 bis 4b im Testworkspace ausgefuehrt. Drei Blocker bestaetigt und in 1.3.0 behoben: fehlender `location_code`, synchrone Tool-Calls mit 60-Sekunden-Abbruch, falscher Filesystem-Root. Ein Blocker offen: die SERP-Gliederung in `agentseo_content_serp_outline` loest deutsche Maerkte falsch auf und liefert englische Platzhalter.
- **Wichtigste Lehre:** Prosa-Regeln in Prompts wurden im Testlauf dreimal gebrochen, Schema-Regeln nicht ein Mal. Zaehlregeln liegen deshalb ab 1.3.0 im Manifest-Schema, siehe ADR-010.
- **Akzeptanztests:** neu ausgefuehrt, Ergebnis 1 bestanden mit offenem Punkt, 2 teilweise, 1 nicht ausfuehrbar, 1 nicht bestanden. Details in `tests/acceptance-tests.md`.
- **Pilot-Abnahme:** in `docs/06-pilot-abnahme-checkliste.md` auf Offen zurueckgesetzt. Der Testlauf war ein Framework-Test, keine Abnahme.
- **GitHub-Anbindung:** Der GitHub-MCP-Server ist seit 17.08.2026 in Claude Desktop eingerichtet und mit 26 Werkzeugen verifiziert. Aenderungen aus einer Cowork-Session laufen darueber per GitHub-API in das Repo, nicht per `git push` aus dem Cloud-Container.
- **Offene Punkte fuer die naechste Version:** CLI des JSON-LD-Validators, Backlog und Untergrenze im Solver, Fehlercodes in Schritt 4a, `additionalProperties: false` im Schema, Media Queries und fehlende Komponenten im Design-System, `country` und `location_code` in `sample_manifest.json`, ausfuehrbarer Testrunner.

---

## 3. Naechste operative Schritte

1. **Call mit Jesse:**
   - Walkthrough durch das GitHub-Repo und das 2-Seiten-PDF-Memo.
   - Einladungen abholen: Slack, Notion, Claude-Team-Lizenz, AgentSEO-API-Key, Buchhaltungsadresse.
2. **Pilot-Projekt starten:**
   - Sobald das erste Kunden-Briefing vorliegt (z.B. simCura), wird der Ordner unter `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\<kunde-slug>\` angelegt.
   - Ausfuehrung der Prompts 0 bis 3 in Claude Desktop.

---

## 4. Verbindliche Arbeitsregeln

1. Autorenschaft immer Raphael Rechberger.
2. Keine Gedankenstriche (weder Em-Dash — noch En-Dash –). Nur Bindestriche (-) oder Doppelpunkte (:).
3. Strikte Fail-Fast-Doktrin (keine Schaetzwerte, harter Stopp bei API- oder Datenfehlern).
4. Strikte Trennung zwischen Framework-Library (`Heartweb-Claude-Desktop-SEO-Workflow`) und individuellem Kunden-Workspace (`Heartweb\Kunden\<slug>\`).
5. Zielmarkt immer als `country` plus `location_code` uebergeben, AgentSEO immer mit `sync: false` und `agentseo_job_status`, Mengenregeln immer als Zahl in das Manifest schreiben (ADR-008 bis ADR-010).
