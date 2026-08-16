# Implementierungs-Memo: Claude Desktop SEO-Workflow & Notion-Bridge

**An:** Jesse Jensen (Heartweb)  
**Von:** Raphael Rechberger  
**Datum:** 16. August 2026  
**Status:** Vollstaendig implementiert & auf GitHub veroeffentlicht  
**Repository:** [https://github.com/Frater418/claude-desktop-seo-workflow-production](https://github.com/Frater418/claude-desktop-seo-workflow-production)  

---

## 1. Was heute gebaut wurde (Aufbauend auf dem Review-PDF)

Aufbauend auf meiner Review-Analyse habe ich den gesamten Workflow heute vollstaendig umgesetzt und in ein modulares, versioniertes Produktionsprojekt ueberfuehrt. Saemtliche in der Review identifizierten Reibungspunkte wurden geloest: Alle 9 Workflow-Prompts sind refactored, die Datenvertraege stehen und das System ist 1:1 fuer die Uebernahme in euer anstehendes Notion-Setup vorbereitet.

---

## 2. Status-Abgleich: Review-Empfehlung vs. Heutige Implementierung

| Review-Empfehlung | Bisheriger Reibungspunkt | Heutiger Produktions-Stand (Im GitHub-Repo) |
|---|---|---|
| **manifest.json** | Kontext musste im Chat gesucht werden; Verlust bei neuen Sessions. | JSON Schema Draft 2020-12 Standard. Speichert Mandantenstatus & Pfade. |
| **design-system.css** | Screenshot aus 1c ging verloren; CSS in Schritt 4 neu erraten. | Persistiert Farb-, Typo- und Button-Tokens zentral ab Schritt 1c. |
| **AgentSEO MCP** | 45-60 Min. pro Pillar: Keywords einzeln in Ahrefs pruefen. | Tool-Call zieht Suchvolumen, KD und CPC vollautomatisch in 2 Min. |
| **Kapazitaets-Solver** | LLMs verrechnen sich bei 17 Wochen mit variierenden Stundensummen. | Python Solver v1.2 berechnet exakt 10-15h/Woche & Verlinkungs-Maps. |
| **Zweiteilung Schritt 4** | Schritt 4 ueberladen (Briefing, Schema und HTML brachen ab). | Getrennt: 4a fuer Texter (Notion-Frontmatter) & 4b fuer Web-Entwicklung. |
| **Qualitaets-Doktrin** | Ungepruefte Schaetzungen fuehrten zu Daten-Drift. | 7 Quality Gates & striktes Fail-Fast ohne stillschweigende Fallbacks. |

---

## 3. Die 6 umgesetzten Kern-Bausteine im Detail

### 1. Persistentes Projekt-Manifest (`manifest.json`)
Initialisiert in Schritt 0. Enthaelt Domain, Zielgruppe, Geschaeftsziele, Phasenstatus und alle Dateipfade. Dient als Single Source of Truth und bildet 1:1 die Struktur eurer kuenftigen Notion-Mandantendatenbank ab.

### 2. Persistentes Design-System (`design-system.css`)
In Schritt 1c werden alle visuellen Tokens einmalig extrahiert. Alle Folgeschritte (Pillar-Templates und Landingpages) binden identische CSS-Klassen ein. Visuelle Konsistenz ist garantiert.

### 3. Automatisierte Keyword-Anreicherung via AgentSEO MCP
Schritt 2 bindet den AgentSEO-Server an. Bis zu 100 Keywords pro Pillar werden per API verifiziert. Lokale Pflicht-Landingpages werden fuer die Gebietsabdeckung gesondert markiert.

### 4. Deterministischer Kapazitaets-Solver (`capacity_matrix_solver.py`)
Mathematisches Python-Skript fuer den 120-Tage-Plan. Jede der 17 Wochen haelt exakt das Budget von 10-15 Stunden ein. Lokale Pflichtseiten landen garantiert in Phase 1 und 2. Generiert zusaetzlich die zweidimensionale Verlinkungs-Map (vertikal + horizontal).

### 5. Modulare Aufteilung in 4a (Briefing) und 4b (HTML)
Schritt 4a fuehrt den Live-SERP-Check durch, generiert Schema.org JSON-LD und liefert saubere Briefings mit standardisiertem YAML-Frontmatter fuer Regina, Katja und Alexander. Schritt 4b erzeugt autarken HTML-Code fuer Web-Entwickler.

### 6. Strikte Fail-Fast- und Qualitaets-Doktrin
Keine stillschweigenden Fallbacks oder Schaetzdaten. Bei fehlendem Key oder unvollstaendigen Daten stoppt der Prozess mit einer expliziten Fehlermeldung.

---

## 4. Zukuenftige Automations-Roadmap (Notion- & n8n-Pipeline)

- **Stufe 1 (Direkter MCP-Push in Claude Desktop):** Sobald euer Notion-Setup live ist, binden wir den Notion-MCP-Server ein. Roadmaps (Schritt 3) und Briefings (Schritt 4a) werden per Tool-Call direkt als Datenbank-Karten angelegt.
- **Stufe 2 (Event-Driven n8n / Make Pipeline):** Ein n8n-Workflow ueberwacht den Output-Ordner oder das Git-Repo, parst das YAML-Frontmatter der Briefings, erstellt die Notion-Karten und weist diese per Auto-Tagging an Regina, Katja oder Alexander zu inklusive formatierter Slack-Benachrichtigung.

---

## 5. Rollenverteilung in der operativen Praxis

- **Fuer Jesse & Raphael (Strategie & Rollout):** Schritte 0 bis 3 laufen in wenigen Minuten durch. Das Ergebnis ist eine fertige 120-Tage-Roadmap fuer Notion.
- **Fuer die Copywriter (Regina, Katja, Alexander):** Erhalten aus 4a glasklare Briefings mit Suchintention, Gliederung, FAQs und Verlinkungsvorgaben ohne stoerenden HTML-Code.
- **Fuer die Web-Entwicklung / WordPress:** Erhaelt aus 1b den Menuebaum (HTML) und aus 4b direkt einsatzbereite Landingpages mit integriertem Schema.org Markup.

---

## 6. Gespraechspunkte fuer unseren Call

1. **Live-Walkthrough:** Kurzer Blick auf das GitHub-Repo und die interaktive README-Landkarte.
2. **Notion-Abgleich:** Abstimmung der Frontmatter-Properties mit der Datenbankstruktur eurer Agentur.
3. **Pilot-Projekt:** Zuweisung des ersten Kunden-Cases (z.B. simCura) fuer den initialen Live-Durchlauf.
