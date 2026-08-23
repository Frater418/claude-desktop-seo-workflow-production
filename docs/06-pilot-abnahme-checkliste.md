# 06. Pilot-Abnahme-Checkliste

> **Lifecycle: historical.** Diese Checkliste beschreibt einen frueheren Pilotstand. Aktuelle Releasefolge und Abnahmekriterien stehen in `00_admin/PROJECT_STATE.md`, DEC-0024 und den aktiven Plaenen.

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Version:** 1.1.0  
**Zweck:** Verbindliche Abnahme-Checkliste fuer den ersten Kunden-Pilotdurchlauf in Claude Desktop.  

---

## 1. Vorbereitung & Umgebung

- [ ] **Claude Desktop Konfiguration:** `claude_desktop_config.json` enthaelt die Eintraege fuer `agentseo` (via `mcp-remote`), `filesystem` und optional `github` gemaess Template.
- [ ] **API-Key verifiziert:** `AGENTSEO_API_KEY` ist aktiv und verfuegt ueber ausreichendes Credit-Kontingent. Live bestaetigt am 17.08.2026.
- [ ] **Kunden-Ordner angelegt:** Neuer Ordner unter `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\[projekt-slug]\` erstellt.
- [ ] **Zielmarkt gesetzt:** `country` und `location_code` stehen in der `manifest.json` und sind in `standards/location-codes.json` hinterlegt.
- [ ] **Website-Screenshot bereitgestellt:** `inputs/website_screenshot.png` liegt vor.

---

## 2. Phasen-Abnahme Schritt fuer Schritt

### Phase A: Initialisierung & Architektur (Schritte 0 bis 1c)
- [ ] **Schritt 0 (Kickoff):**
  - `manifest.json` wurde erzeugt und validiert gegen `standards/manifest.schema.json`.
  - Keine Pflichtfelder fehlen, inklusive `country` und `location_code`.
- [ ] **Schritt 1 (Pillar-Identifikation):**
  - `outputs/1-pillar-themen.md` enthaelt 3 bis 8 fundierte Core Pillars.
  - Pro Pillar liegen 8 bis 15 Cluster vor. Gegenprobe: `phases.step_1_pillar_identification.clusters_per_pillar` im Manifest.
  - Content-Gaps der Wettbewerber wurden identifiziert.
  - Quality Gate 1 von Raphael und Jesse freigegeben.
- [ ] **Schritt 1b (Seitenarchitektur):**
  - `outputs/1b-seitenarchitektur.md` und `outputs/1b-menuestruktur.html` liegen vor.
  - Die HTML-Menueuebersicht oeffnet sich fehlerfrei im Browser und zeigt farbige Badges.
- [ ] **Schritt 1c (Pillar-Templates):**
  - `standards/design-system.css` enthaelt alle extrahierten Farb- und Schrift-Tokens.
  - Pro Pillar existiert ein responsives HTML-Template unter `outputs/html/pillar-[slug].html`.
  - Quality Gate 2 freigegeben.

---

### Phase B: Keyword-Recherche & 120-Tage-Plan (Schritte 2 bis 3b)
- [ ] **Schritt 2 (Cluster-Recherche via AgentSEO):**
  - Tool-Call `agentseo_keyword_metrics_overview` lieferte verifizierte Suchvolumina und KD-Werte, uebergeben mit `location`, `location_code`, `language` und `sync: false`.
  - `location_verified` im Manifest nennt den erwarteten Zielmarkt.
  - `outputs/2-cluster-themen-agentseo.csv` enthaelt mindestens 25 Zeilen pro Pillar. Gegenprobe: `phases.step_2_cluster_research.validated_rows_per_pillar` im Manifest, jeder Wert mindestens 25.
  - Nicht zurueckgegebene Keywords sind in `logs/validation_errors.log` protokolliert und nicht geschaetzt.
  - Lokale Pflicht-Landingpages sind als solche markiert.
  - Quality Gate 3 freigegeben.
- [ ] **Schritt 3 (120-Tage-Plan & Solver):**
  - `capacity_matrix_solver.py` ist gelaufen, die Zeile `Kapazitaets-Messung` im Plankopf ist geprueft.
  - Jede aktive Woche liegt zwischen 10.0 und 15.0 Stunden. Die Untergrenze ist manuell zu pruefen, der Solver erzwingt sie nicht.
  - Alle lokalen Pflicht-Landingpages sind in Phase 1 und 2 verplant.
  - Interne Verlinkungs-Map (vertikal + horizontal) liegt vor.
  - Quality Gate 4 freigegeben.
- [ ] **Schritt 3b (Performance Check nach Tag 30/60/90):**
  - Performance-Daten aus GSC wurden eingelesen.
  - Performer und Unterperformer wurden klassifiziert.
  - Folgephase wurde adaptiv angepasst.

---

### Phase C: Tagesgeschaeft & Produktion (Schritte 4a und 4b)
- [ ] **Schritt 4a (Content-Briefing & Schema JSON-LD):**
  - Live-SERP-Check via `agentseo_content_serp_outline` durchgefuehrt. Achtung: das Tool loest deutsche Maerkte falsch auf, verwertbar sind nur die SERP-Signale.
  - Redaktionelles Briefing liegt unter `outputs/briefings/briefing-[slug].md` vor.
  - YAML Frontmatter fuer Notion-Import ist vollstaendig.
  - Schema.org JSON-LD ist geprueft. Solange `validate_schema_jsonld.py` keine CLI hat, erfolgt die Pruefung ueber den Google Rich Results Test.
  - Quality Gate 5 fuer Texter (Regina, Katja, Alexander) freigegeben.
- [ ] **Schritt 4b (Landingpage-HTML):**
  - HTML-Datei liegt unter `outputs/html/landingpage-[slug]-[ort].html` vor.
  - Bindet globales `design-system.css` ein.
  - Lokale SEO-Elemente (NAP, Karte, Stadtteil-Liste, Breadcrumb) sind sichtbar.
  - Schema JSON-LD ist im `<head>` integriert.
  - Quality Gate 6 fuer Web-Entwickler freigegeben.

---

## 3. Abschluss-Freigabe

| Pruefbereich | Status | Abgenommen durch | Datum |
|---|---|---|---|
| Architektur & Design-System | Offen | Raphael Rechberger | - |
| Keyword-Daten & 120-Tage-Plan | Offen | Jesse Jensen / Raphael Rechberger | - |
| Briefing- & HTML-Qualitaet | Offen | Copywriting-Team (Regina, Katja, Alexander) / Raphael Rechberger | - |

Hinweis: Die Freigaben stehen bis zum ersten vollstaendigen Kunden-Rollout auf Offen. Der Testlauf vom 17.08.2026 war ein Framework-Test, keine Pilot-Abnahme.
