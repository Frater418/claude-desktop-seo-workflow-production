# 01. Review-Abgleich und Entscheidungslog

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Datum:** 16. August 2026  
**Status:** Baseline-Abgleich ueberarbeitet (Strikte Fail-Fast- und Qualitaets-Doktrin)  
**Autor:** Raphael Rechberger  
**Referenzierte Quelldokumente:**
- Original-Workflow Prompts: `0-Kickoff-Prompt.md` bis `4-Landingpage-Blog-Struktur.md`
- Onboarding & Meeting Transkript: `Meeting - 08-16-2026-Onboarding-Raphael.pdf`
- Workflow-Review: `SEO_Prompt_Workflow_Analyse_Claude_Desktop-1.pdf`

---

## 1. Einleitung und Qualitaets-Doktrin

Ziel dieses Abgleichs ist die systematische Pruefung der in der Review (`SEO_Prompt_Workflow_Analyse_Claude_Desktop-1.pdf`) formulierten Hypothesen gegenueber den urspruenglichen Prompt-Dateien und den Vereinbarungen aus dem Onboarding-Call mit Jesse Jensen.

**Verbindliche Qualitaets-Doktrin fuer das Produktivumfeld:**
Es gibt in diesem Workflow **keine stillschweigenden Fallbacks**, kein Erraten von Daten und keine Notloesungen mit minderwertigen Ersatzdaten. Wenn an einer Schnittstelle, bei einem API-Aufruf, bei der Schema-Validierung oder bei der Kontingent-Pruefung ein Fehler auftritt, greift ein **strikter Fail-Fast-Mechanismus**:
1. Der Prozess stoppt sofort an der betroffenen Stelle.
2. Es wird eine strukturierte, maschinen- und menschenlesbare Fehlermeldung mit Fehlercode, Ursache und exakter Handlungsanweisung ausgegeben.
3. Erst nach Behebung der Ursache und Verifikation laeuft der Workflow exakt gemaess Standard weiter.

---

## 2. Abgleich der Reibungspunkte und Architektur-Entscheidungen

| # | Review-Empfehlung / Reibungspunkt | Status | Evidenz (Datei, Call, Recherche) | Entscheidung & Begruendung | Auswirkung auf Workflow, Prompts & Tools |
|---|---|---|---|---|---|
| 1 | **Projekt-Manifest (`manifest.json`)**<br>Keine feste Strukturdatei; Claude muss Kontext aus Chat suchen. | **Bestaetigt** | `0-Kickoff-Prompt.md` Z. 19-20 verlangt Dateispeicherung, bietet aber kein zentrales Schema; Call Z. 231-244 (Single Source of Truth fuer Projekte). | **Bestaetigt und uebernommen.** Jedes Kundenprojekt erhaelt ein definiertes `manifest.json` mit Metadaten, Phasenstatus, Zielen, URLs und Artefakt-Pfaden. | Neues Schema `standards/manifest.schema.json`. Prompt 0 initialisiert das Manifest; alle Folgeschritte aktualisieren ihren Status darin. |
| 2 | **Persistentes Design-System (`design-system.css`)**<br>Design aus Schritt 1c geht bis Schritt 4 verloren; CSS wird erraten. | **Bestaetigt** | `1c-Pillar-Page-Templates.md` Z. 12-19 verlangt Screenshot-Scan; `4-Landingpage-Blog-Struktur.md` Z. 88-95 verlangt gleiches Design, hat aber keinen Zugriff mehr auf den Screenshot. | **Bestaetigt und uebernommen.** Die aus dem Screenshot extrahierten CSS-Variablen (Farben, Typo, Spacings, Buttons, Cards) werden in `design-system.css` gespeichert und von 1c und 4b eingebunden. | Neuer Standard `standards/design-system.css`. Prompt 1c extrahiert Tokens und schreibt die CSS-Datei; Prompt 4b liest die CSS-Datei ein. Fehlt die Datei: Hard Error. |
| 3 | **Automatisierte Keyword-Anreicherung via AgentSEO**<br>Manueller Flaschenhals: 25-40 Zeilen pro Pillar manuell in Ahrefs pruefen. | **Bestaetigt** | `2-Cluster-Recherche-je-Pillar.md` Z. 32-41 (einziger manueller Schritt); Call Z. 89, 403-407, 451-458 (Jesse begruesst Automatisierung via AgentSEO). | **Bestaetigt mit striktem Error-Handling.** Schritt 2 nutzt AgentSEO (`agentseo_keyword_metrics_overview`), um Suchvolumen, Difficulty und CPC automatisiert und verifiziert abzurufen. Bei API-/Quota-Fehler: Sofortiger Abbruch mit Fehlermeldung. Kein stillschweigendes Weitermachen mit Schaetzdaten. | Prompt 2 erhaelt MCP-Tool-Anweisungen fuer AgentSEO mit striktem Error Handling. Tool-Vertrag `mcp/tool-contracts/agentseo_keyword_enricher.md` wird spezifiziert. |
| 4 | **Deterministischer Kapazitaets-Solver (`capacity_matrix_solver`)**<br>LLMs verrechnen sich bei 17 Wochen mit Stunden-Summen (10-15h) leicht. | **Bestaetigt** | `3-30-60-90-120-Tage-Plan.md` Z. 19-33 (strikte Summenpruefung); LLM-Arithmetik neigt bei mehrdimensionalen Tabellen zu Rundungs- und Zuordnungsfehlern. | **Bestaetigt und als deterministischer Baustein umgesetzt.** Ein Python-Script berechnet die exakte Stunden-Matrix und Prioritaets-Scores (Score-Formel + Local-Landingpage-Pflichtabdeckung) mathematisch exakt. | Prompt 3 bindet den Solver ein. Bereitstellung als eigenstaendiges Script `mcp/tools/capacity_matrix_solver.py` mit strikter Schema-Validierung. |
| 5 | **Nomenklatur- und Dateiformat-Konsistenz**<br>Inkonsistenz zwischen `.md` und `.csv` (Schritt 4 sucht `2-cluster...md`, Schritt 2 erzeugt `.csv`). | **Bestaetigt** | `2-Cluster-Recherche-je-Pillar.md` Z. 41 (`2-cluster-themen-ahrefs.csv`) vs. `4-Landingpage-Blog-Struktur.md` Z. 8 (`2-cluster-themen-ahrefs.md`). | **Bestaetigt und korrigiert.** Einheitlicher Standard: Strukturtabellen und Keyword-Daten liegen als standardisierte `.csv` oder `.json` vor, textliche Strategien als `.md`. | Dokument `standards/dateinamen-und-output-vertrag.md` legt saemtliche Dateinamen, relative Pfade und Schemas verbindlich fest. |
| 6 | **Zweiteilung von Schritt 4 (4a Briefing/Schema + 4b HTML)**<br>Schritt 4 ist ueberladen; LLM bricht bei simultaner Briefing-, Schema- und HTML-Generierung ab. | **Bestaetigt** | `4-Landingpage-Blog-Struktur.md` Z. 20-105 umfasst 6 Einzelschritte (SERP-Check, Tonalitaet, Struktur, EEAT, JSON-LD, vollstaendige HTML-Datei). | **Bestaetigt und umgesetzt.** Schritt 4 wird aufgeteilt in `4a-content-briefing-und-schema.xml.md` (fuer alle Content-Typen) und `4b-landingpage-html.xml.md` (nur fuer Landingpages zur HTML-Erstellung). | Trennung in zwei modulare Prompts 4a und 4b. Verhindert Token-Limits und trennt Copywriting-Briefing von Frontend-Code. |
| 7 | **Tool-Klassifikation: Echte MCP-Tools vs. Prompt-Instruktionen**<br>Review schlaegt 8 Skills vor; nicht alle muessen eigene MCP-Server sein. | **Angepasst** | Recherche zu AgentSEO OpenAPI (`45 Endpunkte`) und Claude Desktop MCP Architektur (`stdio` Transport). | **Angepasst.** Differenzierung zwischen: (a) AgentSEO Remote-MCP Tools (`agentseo_*`), (b) Lokale Python/Helper Scripts (`capacity_matrix_solver.py`), und (c) Prompt-internen Validierungen. | Reduktion unnoetiger Server-Komplexitaet: 1 AgentSEO-MCP-Server + 1 Filesystem-Server + 1 lokaler deterministischer Solver. |
| 8 | **Human-in-the-Loop & Quality Gates**<br>Vollautomatisierung ohne Review birgt Qualitaets- und Haftungsrisiken. | **Bestaetigt** | Call Z. 15, 96-98, 477-482 (Jesse: SEO-Content bleibt human-edited; Copywriter Regina, Katja, Alexander veredeln). | **Bestaetigt und als zentraler Standard etabliert.** An jedem Meilenstein (Pillar-Freigabe, Keyword-Export, 120-Tage-Plan-Abnahme, Content-Briefing) existiert ein expliziter Review-Stop. | Eigene Dokumentation `docs/05-human-in-the-loop.md` und Review-Gates in jedem XML-Prompt. |
| 9 | **Intent Grounding & SERP-Validierung**<br>Vermutete Suchintentionen duerfen nicht ungeprueft uebernommen werden. | **Bestaetigt** | `1-Pillar-Themen-Identifikation.md` Z. 31 (`Status: zu recherchieren`); `4-Landingpage-Blog-Struktur.md` Z. 32-44 (Pflicht-SERP-Check). | **Bestaetigt.** Schritt 1 und 2 markieren Intentionen explizit als Hypothese; Schritt 4a validiert diese zwingend ueber AgentSEO SERP-Analyse (`agentseo_analyze_serp` oder `agentseo_content_serp_outline`). | XML-Validierungsregeln erzwingen den Abgleich von hypothetischer und realer SERP-Intention. |

---

## 3. Detaillierte Entscheidungsbegruendungen

### 3.1 Projekt-Manifest (`manifest.json`)
Im urspruenglichen Workflow musste Claude in jedem Prompt angewiesen werden, vorherige Chat-Verlaeufe oder einzelne Textdateien manuell zu durchsuchen. Dies fuehrt bei laengeren Projekten zu Kontextverlust. Das `manifest.json` fungiert als maschinenlesbarer Index ueber den Projektfortschritt, definierte Pillars, Cluster-Pfade, Design-Token-Pfade und die Ziel-Zielgruppe.

### 3.2 Design-Persistenz (`design-system.css`)
Schritt 1c forderte einen Screenshot zur visuellen Analyse. In Schritt 4 (Landingpage-Bau) stand dieser Screenshot in der Regel nicht mehr im aktiven Kontextfenster zur Verfuegung, sodass Farben und Typografie neu halluziniert wurden. Durch die Extraktion in eine standardisierte CSS-Datei (`design-system.css`) in Schritt 1c koennen alle spaeteren HTML-Templates (Pillar-Pages und Cluster-Landingpages) identische CSS-Klassen und Farbvariablen referenzieren.

### 3.3 AgentSEO MCP-Integration & Strikte Datenqualitaet
AgentSEO stellt ueber 45 spezialisierte Endpunkte zur Verfuegung. Insbesondere `/keyword-metrics/overview` (Volumen, KD, CPC fuer bis zu 100 Keywords) und `/content/serp-outline` bzw. `/content/brief` ersetzen die zeitaufwaendige manuelle Recherche in Ahrefs durch einen 1-Klick Tool-Call in Claude Desktop.
Treten Fehler auf (z.B. API-Key ungueltig, Quota erschoepft, Netzwerk-Timeout), bricht der Schritt mit einem klaren Fehlerbericht ab. Es gibt kein automatisches Weitermachen mit Schaetzungen oder unvollstaendigen Daten.

### 3.4 Kapazitaets-Solver
Die Berechnung von 17 Wochen mit je exakt 10 bis 15 Arbeitsstunden bei variierenden Deliverable-Aufwaenden (Pillar: 8h, Blog: 3h, Landingpage: 1.25h, FAQ: 1h) unter Beruecksichtigung der Pflichtabdeckung fuer lokale Landingpages ist ein klassisches kombinatorisches Optimierungsproblem (Knapsack / Bin-Packing). Ein deterministisches Python-Script loest dies in Millisekunden fehlerfrei, waehrend LLMs dazu neigen, Wochen mit 8 oder 18 Stunden zu befuellen.

### 3.5 Trennung von Schritt 4 in 4a und 4b
Schritt 4 war der groesste Engpass im Workflow. Die gleichzeitige Anforderung, eine SERP-Wettbewerbsanalyse durchzufuehren, eine EEAT-Checkliste abzuarbeiten, ein vollstaendiges Schema.org JSON-LD zu generieren und 300 bis 500 Zeilen sauberen HTML-Code zu schreiben, fuehrte haeufig zu Abbruechen oder oberflaechlichem Output. Die Trennung in:
- **4a:** Strategisches Content-Briefing, Search Intent, Gliederung, EEAT und Schema JSON-LD (fuer alle Content-Typen, optimiert fuer Copywriter)
- **4b:** Produktionsfertiges HTML-Layout (nur fuer Landingpages auf Basis von `design-system.css` und dem 4a-Briefing)
stellt maximale Qualitaet und Stabilitaet sicher.

---

## 4. Fazit und Freigabestatus

Alle Kern-Punkte wurden verifiziert und mit einer strikten Qualitaets- und Error-Handling-Doktrin versehen. Die Tool-Architektur kombiniert den offiziellen AgentSEO MCP-Server nahtlos mit lokalen Standards (`manifest.json`, `design-system.css`, Python Solver) und klaren Human-in-the-Loop Gates.
