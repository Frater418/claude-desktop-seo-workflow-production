# Technisches Briefing & Architektur-Bridge: Claude Desktop zu Notion

**An:** Jesse Jensen (Heartweb / Hardware Design)  
**Von:** Raphael Rechberger  
**Datum:** 16. August 2026  
**Status:** Produktionsbereit & auf GitHub veroeffentlicht  
**Repository:** [https://github.com/Frater418/claude-desktop-seo-workflow-production](https://github.com/Frater418/claude-desktop-seo-workflow-production)  

---

## 1. Ausgangslage & Zielsetzung

Wie in unserem Onboarding-Gesetz besprochen, steht Heartweb vor dem Skalierungsschritt von manueller ad-hoc Steuerung hin zu einer zentralen, automatisierten Operations-Plattform in Notion.

Bisherige Herausforderung:
Die operative Logik deiner SEO-Rollouts (Pillars, Cluster, 120-Tage-Priorisierung, lokale Pflichtseiten) existierte als Prompt-Sequenz. Wenn mehrere Projekte parallel laufen, fuehren manuelle Zwischenschritte (wie das Abtippen in Ahrefs), fehlende Zustandsspeicher und unstrukturierte Chat-Outputs zu Reibung und Kontextverlust.

Was wir umgesetzt haben:
Wir haben deinen Workflow nicht neu erfunden, sondern ein **deterministisches, datenbank-kompatibles Fundament** geschaffen. Das System laeuft lokal in Claude Desktop, erzeugt aber von Haus aus standardisierte Datenstrukturen (JSON/YAML-Frontmatter), die nahtlos in dein neues Notion-Setup einfliessen und spaeter per API/Webhook vollautomatisiert werden koennen.

---

## 2. Die 6 technischen Bausteine im Ueberblick

```text
Lokale Claude Desktop Pipeline                Zukuenftige Notion- & Automations-Bridge
------------------------------------------    ---------------------------------------------------------
1. manifest.json                              -> Bildet 1:1 die Notion Mandanten-/Projekt-Datenbank ab
2. standards/design-system.css                -> Sichert visuelle CI-Konsistenz bis zur Landingpage
3. AgentSEO MCP-Integration                   -> Zieht Keyword-Metriken automatisiert per API-Call
4. capacity_matrix_solver.py                  -> Berechnet 17 Wochen mathematisch exakt (10-15h Budget)
5. 4a Content-Briefings                       -> Liefert Notion-Frontmatter fuer Regina, Katja, Alexander
6. 4b HTML-Generator                          -> Erzeugt autarke Landingpages fuer Web-Entwickler
```

---

### Die Bausteine im Detail:

### 1. Datenmodell & Projekt-Manifest (`manifest.json`)
- **Architektur:** Jedes Kundenprojekt erhaelt eine zentrale `manifest.json`, validiert gegen `standards/manifest.schema.json`.
- **Notion-Bridge:** Die Felder (`project_id`, `domain`, `competitors`, `target_audience`, `brand_tone`, `phases.status`) entsprechen exakt den Properties, die ihr in Notion fuer Mandanten-Dashboards benoetigt.

### 2. Persistentes Design-System (`design-system.css`)
- **Architektur:** In Schritt 1c werden die visuellen Design-Tokens (Farben, Typo, Abstaende, Card- und Button-Stile) aus dem Website-Screenshot extrahiert und in `design-system.css` festgeschrieben.
- **Nutzen:** Schritt 4b erzeugt Landingpages im exakten Kundendesign, ohne Stile im Chat neu zu erraten.

### 3. Automatisierte Keyword-Anreicherung via AgentSEO MCP
- **Architektur:** Schritt 2 bindet den AgentSEO MCP-Server (`agentseo_keyword_metrics_overview`) ein.
- **Nutzen:** Bis zu 100 Keywords pro Pillar werden in Sekunden mit verifiziertem Suchvolumen, KD und CPC angereichert. Der bisherige manuelle Ahrefs-Zwischenschritt entfaellt vollstaendig.

### 4. Deterministischer Kapazitaets-Solver (`capacity_matrix_solver.py`)
- **Architektur:** Ein Python-Script uebernimmt die kombinatorische Stundenverteilung fuer die 17 Wochen (10 bis 15 Stunden pro Woche).
- **Nutzen:** Mathematische Garantie: Keine Woche wird ueber- oder unterbelegt. Lokale Pflicht-Landingpages werden zu 100% in Phase 1 und 2 verplant.

### 5. Modulares Tagesgeschaeft: 4a Briefings & 4b HTML
- **Architektur:** Trennung des frueher ueberladenen Schritt 4 in zwei kontrollierte Schritte:
  - **4a (Copywriting-Briefing):** Fuehrt den Live-SERP-Check durch, generiert Schema.org JSON-LD und erzeugt ein reines Markdown-Briefing mit Notion-Frontmatter (Properties: `Pillar`, `Target_Keyword`, `Search_Volume`, `Priority`, `Status`).
  - **4b (Landingpage-HTML):** Erzeugt autarken Frontend-Code ausschliesslich fuer Landingpages.
- **Nutzen:** Eure Copywriter (Regina, Katja, Alexander) erhalten saubere, lesbare Briefings in Notion; Entwickler erhalten fertigen HTML-Code.

### 6. Strikte Fail-Fast- und Qualitaets-Doktrin
- **Architektur:** Keine stillschweigenden Fallbacks auf Schaetzdaten. Bei fehlendem Key oder unvollstaendigen Daten stoppt der Prozess mit einer expliziten Fehlermeldung.

---

## 3. Zukuenftige Automations-Roadmap (Notion Integration)

Sobald eure Agentur das Notion-Setup live geschaltet hat, kann die Pipeline in zwei Schritten weiter automatisiert werden:

1. **Stufe 1 (Direkter MCP-Push):**
   - Einbindung des offiziellen Notion-MCP-Servers in Claude Desktop. Die generierten Roadmaps (Schritt 3) und Briefings (Schritt 4a) werden per Tool-Call direkt als Datenbank-Eintraege in Notion angelegt.
2. **Stufe 2 (Event-Driven Pipeline via n8n / Make):**
   - Ein n8n-Workflow ueberwacht den Output-Ordner oder das Git-Repo, liest die Markdown-Briefings aus, erstellt die Notion-Karten und weist diese per Auto-Tagging an Regina, Katja oder Alexander zu inklusive Slack-Notification.

---

## 4. GitHub Repository Uebersicht

Das vollstaendige Produktionspaket ist oeffentlich auf GitHub verfuegbar:
**Repository:** [https://github.com/Frater418/claude-desktop-seo-workflow-production](https://github.com/Frater418/claude-desktop-seo-workflow-production)

- **`README.md`:** Interaktiver Navigations-Hub mit vollstaendiger Workflow-Landkarte.
- **`prompts/`:** Alle 9 produktionsfertigen XML-Prompts (`0-kickoff.xml.md` bis `4b-landingpage-html.xml.md`).
- **`standards/`:** `manifest.schema.json`, `design-system.css`, Dateinamen-Vertrag.
- **`mcp/`:** Claude Desktop Konfigurations-Template und `capacity_matrix_solver.py`.
- **`docs/`:** Betriebshandbuch, Quality Gates, ADR-Entscheidungslog, Copywriter-Leitfaden.

---

## 5. Gespraechspunkte fuer unseren Call

1. Kurzer Walkthrough durch die Repository-Struktur und das Menuediagramm.
2. Abgleich der Frontmatter-Felder mit der Datenbankstruktur eurer Notion-Agentur.
3. Konfiguration der Claude Desktop App fuer den ersten gemeinsamen Kundenlauf.
