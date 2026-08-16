# Executive Memo: Modernisierung des SEO-Workflows fuer Claude Desktop

**An:** Jesse Jensen (Heartweb / Hardware Design)  
**Von:** Raphael Rechberger  
**Datum:** 16. August 2026  
**Status:** Produktionsbereit & auf GitHub veroeffentlicht  
**Repository:** [https://github.com/Frater418/claude-desktop-seo-workflow-production](https://github.com/Frater418/claude-desktop-seo-workflow-production)  

---

## 1. Executive Summary

Hi Jesse,

wie in unserem Onboarding-Call besprochen, habe ich deinen bestehenden SEO-Prompt-Workflow (Schritte 0 bis 4) im Detail analysiert, alle manuellen Flaschenhaelse beseitigt und das gesamte Setup in eine **skalierbare, hochgradig praezise Produktionsarchitektur fuer Claude Desktop** ueberfuehrt.

Die strategische Substanz deines Workflows (Pillars, Themencluster, 120-Tage-Logik, lokale Pflicht-Landingpages) war bereits extrem stark. Wir haben das Rad nicht neu erfunden, sondern ein **stabiles technisches Fundament** darum gebaut, damit du bei mehreren parallelen Kunden-Rollouts maximale Zeitersparnis hast und Claude niemals den Kontext verliert.

Das gesamte System ist ab sofort in einem oeffentlichen, lueckenlos dokumentierten GitHub-Repository strukturiert, sodass du und das Team jede Datei, jeden Prompt und jeden Standard in Sekunden aufrufen koennt.

---

## 2. Was wir ZUSAETZLICH gebaut und optimiert haben

Hier ist die Uebersicht der 6 zentralen Hebel, die ueber deinen urspruenglichen Prompt-Workflow hinausgehen:

```text
Bisheriger Workflow (Manuelle Reibung)          Modernisierter Produktions-Standard
--------------------------------------------    --------------------------------------------------
1. Kontext aus Chat-Verlauf suchen              -> 1. Zentrales manifest.json pro Kundenprojekt
2. Design in Schritt 4 neu erraten              -> 2. Persistentes design-system.css ab Schritt 1c
3. 45-60 Min. Keywords in Ahrefs tippen         -> 3. Vollautomatische AgentSEO-MCP-Anreicherung (2 Min.)
4. LLM verrechnet sich bei 17 Wochen            -> 4. Deterministischer Python-Kapazitaets-Solver
5. Schritt 4 ueberladen (bricht ab)             -> 5. Trennung in 4a (Briefing fuer Texter) & 4b (HTML)
6. Keine einheitlichen Quality Gates            -> 6. 7 verbindliche Human-in-the-Loop Freigabepunkte
```

---

### Die 6 Kern-Hebel im Detail:

### 1. Persistentes Projekt-Manifest (`manifest.json`)
- **Problem bisher:** Bei laengeren Sessions oder Neustarts musste Claude den Kontext aus verstreuten Textdateien oder dem Chatverlauf zusammensuchen.
- **Loesung:** Jedes Kundenprojekt fuehrt ab Schritt 0 eine maschinenlesbare `manifest.json`. Sie enthaelt Domain, Wettbewerber, Zielgruppe, Phasenstatus und alle Dateipfade. Claude greift in jedem Schritt deterministisch darauf zu.

### 2. Persistentes Design-System (`design-system.css`)
- **Problem bisher:** Der Screenshot aus Schritt 1c stand Claude in Schritt 4 nicht mehr zur Verfuegung; CSS-Stile und Farben wurden bei jeder Landingpage neu erraten.
- **Loesung:** In Schritt 1c werden die visuellen Tokens (Farben, Typo, Buttons, Cards, Badges) einmalig extrahiert und in `standards/design-system.css` gespeichert. Alle HTML-Templates (1c & 4b) greifen auf identische Klassen zu.

### 3. Automatisierte Keyword-Anreicherung via AgentSEO MCP
- **Problem bisher:** Pro Pillar mussten 25 bis 40 Seed-Keywords einzeln in Ahrefs geprueft, manuell in Excel uebertragen und als CSV exportiert werden (~45-60 Min. pro Pillar).
- **Loesung:** In Schritt 2 ruft Claude Desktop ueber den MCP-Server direkt die verifizierten Metriken (Suchvolumen, KD, CPC) von AgentSEO ab. Die CSV entsteht in Sekunden vollautomatisch.

### 4. Deterministischer Kapazitaets-Solver (`capacity_matrix_solver.py`)
- **Problem bisher:** Bei 17 Wochen a 10 bis 15 Stunden und 40+ Keywords neigen LLMs bei der Stundenberechnung zu Rechenfehlern oder unvollstaendigen Wochen.
- **Loesung:** Ein mathematisch exaktes Python-Script loest die 120-Tage-Matrix fehlerfrei. Alle lokalen Pflicht-Landingpages werden garantiert in Phase 1 und 2 verplant; keine Woche weicht vom Stundenbudget ab.

### 5. Zweiteilung von Schritt 4 (4a Redaktions-Briefing & 4b HTML)
- **Problem bisher:** Schritt 4 war ueberladen (SERP-Check + EEAT + Schema JSON-LD + 400 Zeilen HTML auf einmal fuehrten oft zu Abbruechen).
- **Loesung:**
  - **4a:** Erzeugt das strategische Content-Briefing inkl. Notion-Frontmatter und Schema.org JSON-LD fuer eure Copywriter (Regina, Katja, Alexander).
  - **4b:** Erzeugt ausschliesslich fuer Landingpages den fertigen, sauberen HTML-Code fuer die Web-Entwickler.

### 6. Strikte Fail-Fast- und Qualitaets-Doktrin
- **Prinzip:** Im Produktivumfeld gibt es keine stillschweigenden Fallbacks auf unvalidierte Schaetzdaten. Wenn ein API-Call fehlschlaegt oder Pflichtdaten fehlen, stoppt Claude sofort mit einer klaren Fehlermeldung und Handlungsanweisung.

---

## 3. Wie ihr im Team damit arbeitet

1. **Fuer Jesse / Raphael (Strategie & Setup):**
   - Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige 120-Tage-Roadmap, die direkt in euer neues Notion-System uebernommen werden kann.
2. **Fuer die Copywriter (Regina, Katja, Alexander):**
   - Erhalten aus Schritt 4a glasklare, strukturierte Briefings mit Suchintention, Gliederung, FAQ-Antworten und Verlinkungsvorgaben ohne stoerenden HTML-Code-Ballast.
3. **Fuer die Web-Entwicklung / WordPress:**
   - Erhaelt aus Schritt 1b das visuelle Menuebaums-Diagramm (`1b-menuestruktur.html`) und aus 4b direkt einsatzbereite HTML-Landingpages mit integriertem Schema.org Markup.

---

## 4. GitHub Repository Schnelluebersicht

Im GitHub-Repository findest du alle Bausteine sauber sortiert:

- **[Master README.md](https://github.com/Frater418/claude-desktop-seo-workflow-production#readme):** Zentraler Einstieg mit interaktiver Workflow-Landkarte.
- **[prompts/](https://github.com/Frater418/claude-desktop-seo-workflow-production/tree/master/prompts):** Alle 9 ueberarbeiteten XML-Prompts (0 bis 4b).
- **[standards/](https://github.com/Frater418/claude-desktop-seo-workflow-production/tree/master/standards):** `manifest.schema.json`, `design-system.css` und der Dateinamen-Vertrag.
- **[mcp/](https://github.com/Frater418/claude-desktop-seo-workflow-production/tree/master/mcp):** Konfigurations-Template fuer Claude Desktop und der Kapazitaets-Solver.
- **[docs/](https://github.com/Frater418/claude-desktop-seo-workflow-production/tree/master/docs):** Betriebshandbuch, Human-in-the-Loop Gates, ADR-Entscheidungslog und Copywriter-Leitfaden.

---

## 5. Vorbereitung auf unseren Call

Fuer unseren anstehenden Call koennen wir direkt anhand des Repos durchgehen:
1. Kurzer Live-Walkthrough durch die `README.md` und das Menuediagramm.
2. Einrichten deiner `claude_desktop_config.json` mit dem AgentSEO-Server.
3. Auswahl des ersten Pilot-Projekts (z.B. simCura oder ein anderes anstehendes Kundenprojekt).

Beste Gruesse,  
Raphael Rechberger
