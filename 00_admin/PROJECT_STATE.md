# PROJECT STATE & OPERATIONAL BRIEFING

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework  
**Autor & Architektur:** Raphael Rechberger  
**Organisation:** Heartweb / Zusammenarbeit Raphael Rechberger & Jesse Jensen  
**Datum:** 16. August 2026  
**Status:** Produktionsbereit, vollstaendig auditiert & auf GitHub veroeffentlicht  
**GitHub Repository:** https://github.com/Frater418/claude-desktop-seo-workflow-production  
**Kanonischer Pfad:** `C:\Users\offic\Documents\Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow\`  
**Desktop-Pfad:** `C:\Users\offic\Desktop\Heartweb\claude-desktop-seo-workflow-production\`  

---

## 1. Projekt-Kontext & Rollen

- **Ziel:** Modernisierung und Automatisierung des 120-Tage-SEO-Rollout-Workflows fuer die Claude Desktop App.
- **Stakeholder & Team:**
  - **Raphael Rechberger:** Technical Operations & AI Integration Architect (fuehrt die Rollouts durch, steuert die Pipeline, baut die Schnittstellen).
  - **Jesse Jensen:** Co-Founder & Lead Heartweb (steuert Kundenbeziehungen, Onboarding, Strategie).
  - **Copywriting-Team:** Regina, Katja, Alexander (erhalten saubere 4a-Briefings fuer redaktionelle Veredelung in Notion).
  - **Entwicklung / Design:** Thure, Rahul, Wayan (erhalten 1b-Menuebaeume und 4b-HTML-Templates fuer WordPress/Elementor).
  - **Automation / Tech:** Manuel (Social/YouTube-Automation & technische Audits).

---

## 2. Abgeschlossener Arbeitsstand (Was fertig gebaut ist)

1. **Standards & Vertraege (`standards/`):**
   - `manifest.schema.json`: JSON Schema Draft 2020-12 fuer den Mandanten-Steckbrief `manifest.json`.
   - `design-system.css`: Autarke CSS-Token-Schablone (Farben, Typo, Cards, Buttons) fuer Landingpages.
   - `dateinamen-und-output-vertrag.md`: Verbindliche Pfade und Dateinamen fuer alle Schritte.

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
   - `capacity_matrix_solver.py` (v1.2.0): Berechnet 17 Wochen a 10-15h, 100% Pflichtabdeckung fuer lokale Landingpages und Verlinkungs-Maps.
   - `validate_schema_jsonld.py`: Autarke Validierung fuer Google Rich Results.
   - `tool-contracts/`: Formale Schemas fuer AgentSEO API-Calls.

4. **Dokumentation & Handbuecher (`docs/`):**
   - `betriebshandbuch-claude-desktop.md`: Schritt-fuer-Schritt-Anleitung fuer die Desktop App & Projects.
   - `copywriter-handoff-guidelines.md`: Leitfaden fuer die Notion-Uebergabe an Regina, Katja, Alexander.
   - `jesse-walkthrough-memo.pdf`: Exakt ausbalanciertes 2-Seiten-Memo fuer Jesse.
   - `01-review-abgleich.md`, `02-research-und-technische-spezifikation.md`, `03-sprint-plan.md`, `04-entscheidungslog.md`, `05-human-in-the-loop.md`, `06-pilot-abnahme-checkliste.md`.

5. **Akzeptanztests & Fixtures (`tests/`):**
   - 5 von 5 Akzeptanztests bestanden (`tests/acceptance-tests.md`).
   - Fixtures fuer simCura Pflegedienst (`sample_manifest.json`, `sample_cluster_keywords.json` mit 61 Keywords).

---

## 3. Naechste operative Schritte

1. **Call mit Jesse:**
   - Walkthrough durch das GitHub-Repo und das 2-Seiten-PDF-Memo.
   - Einladungen abholen: Slack, Notion, Claude-Team-Lizenz, AgentSEO-API-Key, Buchhaltungsadresse.
2. **Pilot-Projekt starten:**
   - Sobald das erste Kunden-Briefing vorliegt (z.B. simCura), wird der Ordner unter `C:\Users\offic\Documents\Projekte\Kunden\<kunde-slug>\` angelegt.
   - Ausfuehrung der Prompts 0 bis 3 in Claude Desktop.

---

## 4. Verbindliche Arbeitsregeln

1. Autorenschaft immer Raphael Rechberger.
2. Keine Gedankenstriche (weder Em-Dash — noch En-Dash –). Nur Bindestriche (-) oder Doppelpunkte (:).
3. Strikte Fail-Fast-Doktrin (keine Schaetzwerte, harter Stopp bei API- oder Datenfehlern).
4. Strikte Trennung zwischen Framework-Library (`Heartweb-Claude-Desktop-SEO-Workflow`) und individuellem Kunden-Workspace (`Kunden/<slug>/`).
