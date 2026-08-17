# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 17. August 2026  
**Status:** Auditiert, Version 1.3.0 in Arbeit. Vorbereitung der GEO-Erweiterung (Generative Engine Optimization v1.4.0 / GEO-Branch).  
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
2. Keine Gedankenstriche (weder Em-Dash — noch En-Dash –). Nur Bindestriche (-) oder Doppelpunkte (:).
3. Strikte Fail-Fast-Doktrin (keine Schaetzwerte, harter Stopp bei API- oder Datenfehlern).
4. Strikte Trennung zwischen Framework-Library (`Heartweb-Claude-Desktop-SEO-Workflow`) und individuellem Kunden-Workspace (`Heartweb\Kunden\<slug>\`).
5. Zielmarkt immer als `country` plus `location_code` uebergeben, AgentSEO immer mit `sync: false` und `agentseo_job_status`, Mengenregeln immer als Zahl in das Manifest schreiben (ADR-008 bis ADR-010).
