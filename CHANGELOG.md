# CHANGELOG

Alle relevanten Aenderungen an diesem Produktionsprojekt werden in dieser Datei dokumentiert.
Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) und folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [1.1.0] - 2026-08-16

### Vollstaendiger Rollout aller Sprints: Prompts, Tooling, Solver & Betriebsdokumentation

**Autor:** Raphael Rechberger

#### Hinzugefuegt
- **XML-Produktions-Prompts (`prompts/`):**
  - `prompts/0-kickoff.xml.md`: Projekt-Initialisierung & Manifest-Setup.
  - `prompts/1-pillar-identifikation.xml.md`: Pillar-Themen-Identifikation & Gap-Analyse.
  - `prompts/1b-seitenarchitektur.xml.md`: Finale Informationsarchitektur & interaktives Menuediagramm.
  - `prompts/1c-pillar-template.xml.md`: Screenshot-Analyse, CSS-Token-Persistierung & Pillar-HTML-Templates.
  - `prompts/2-cluster-recherche.xml.md`: Cluster-Recherche & automatisierte AgentSEO-Keyword-Anreicherung.
  - `prompts/3-120-tage-plan.xml.md`: 120-Tage-Roadmap & interne Verlinkungs-Map.
  - `prompts/3b-performance-check.xml.md`: Tag 30/60/90 Ranking-Sync & adaptive Phasenanpassung.
  - `prompts/4a-content-briefing-und-schema.xml.md`: SERP-Intent Check, Notion-Frontmatter & Schema.org JSON-LD.
  - `prompts/4b-landingpage-html.xml.md`: Produktionsfertiger Landingpage-HTML-Generator.

- **Deterministische Tools & Validierung (`mcp/tools/`):**
  - `mcp/tools/capacity_matrix_solver.py`: Mathematisch exakter 120-Tage-Solver (17 Wochen a 10-15h, 100% Pflichtabdeckung fuer lokale Landingpages).
  - `mcp/tools/validate_schema_jsonld.py`: Autarker JSON-LD Schema.org Validator gegen Google Rich Results Standards.
  - Formale Tool-Vertraege unter `mcp/tool-contracts/` (`agentseo_keyword_enricher.json`, `serp_gap_analyzer.json`, `schema_jsonld_generator.json`).

- **Test-Fixtures & Nachweise (`tests/`):**
  - `tests/fixtures/sample_manifest.json`: Referenz-Manifest fuer simCura Pflegedienst.
  - `tests/fixtures/sample_cluster_keywords.json`: 40 verifizierte Keywords fuer Solver-Tests.
  - `tests/fixtures/sample_serp_briefing.json`: Beispielhafter SERP-Briefing-Datensatz.
  - `tests/acceptance-tests.md`: Vollstaendig dokumentiertes Testprotokoll (alle 5 Akzeptanztests bestanden).

- **Betriebs- & Uebergabedokumentation (`docs/`):**
  - `docs/06-pilot-abnahme-checkliste.md`: Schritt-fuer-Schritt Checkliste fuer Kunden-Rollouts.
  - `docs/betriebshandbuch-claude-desktop.md`: Nicht-technische Anleitung fuer den Alltag.
  - `docs/copywriter-handoff-guidelines.md`: Leitfaden fuer die Notion-Uebergabe an Regina, Katja, Alexander.
  - `docs/jesse-walkthrough-memo.md`: Praegnantes Walkthrough-Memo fuer Jesse Jensen mit Vergleichstabelle und Kern-Hebeln.

---

## [1.0.0] - 2026-08-16

### Initiales Release: Produktionsfundament, Standards und Tool-Architektur

**Autor:** Raphael Rechberger

#### Hinzugefuegt
- `standards/manifest.schema.json`
- `standards/design-system.css`
- `standards/dateinamen-und-output-vertrag.md`
- `mcp/claude_desktop_config.template.json`
- `docs/01-review-abgleich.md`
- `docs/02-research-und-technische-spezifikation.md`
- `docs/03-sprint-plan.md`
- `docs/04-entscheidungslog.md`
- `docs/05-human-in-the-loop.md`
- `README.md`
