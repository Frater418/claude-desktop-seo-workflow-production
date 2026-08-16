# 05. Human-in-the-Loop und Quality Gates

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Version:** 1.0.0  
**Zweck:** Verbindlicher Leitfaden fuer manuelle Review- und Freigabepunkte im Workflow.  

---

## 1. Philosophie: Warum Human-in-the-Loop unverzichtbar ist

Im Onboarding-Call mit Jesse Jensen wurde unmissverstaendlich vereinbart:
**SEO-Content bleibt „human-edited“; reiner ungepruefter KI-Content wird fuer Kundenprojekte ausgeschlossen.**

Claude Desktop und die angebundenen Tools dienen als Hochleistungs-Beschleuniger fuer Analyse, Strukturierung, Recherche und Schema-Generierung. An strategischen Knotenpunkten sichert die menschliche Pruefung durch Raphael Rechberger und Jesse Jensen ab:
1. Keine Halluzinationen oder unpassende Nischen-Begriffe.
2. 100%ige Uebereinstimmung mit den Geschaeftszielen des Kunden.
3. Perfekte Briefing-Qualitaet fuer die Copywriter (Regina, Katja, Alexander).

---

## 2. Die 7 verbindlichen Quality Gates

```text
[Schritt 0 & 1] ---> GATE 1: Pillar- & Architektur-Freigabe (Jesse/Raphael)
                          |
[Schritt 1b & 1c] -> GATE 2: Menue- & Design-System-Freigabe (Raphael)
                          |
[Schritt 2] -------> GATE 3: Keyword- & Cluster-Validierung (Raphael)
                          |
[Schritt 3] -------> GATE 4: 120-Tage-Roadmap-Abnahme (Jesse/Raphael)
                          |
[Schritt 4a] ------> GATE 5: Redaktions-Briefing-Freigabe (Copywriter-Handoff)
                          |
[Schritt 4b] ------> GATE 6: HTML-Landingpage-QA (Frontend/Design)
                          |
[Schritt 3b] ------> GATE 7: 30/60/90-Tage Performance-Review (Jesse/Raphael)
```

---

### Gate 1: Pillar-Themen- & Themenarchitektur-Freigabe
- **Position:** Nach Ausfuehrung von `1-pillar-identifikation.xml.md`.
- **Reviewer:** Raphael Rechberger & Jesse Jensen.
- **Pruefkriterien:**
  - Deckt die Pillar-Liste die tatsaechlichen Geschaeftsbereiche des Kunden ab?
  - Wurden die wichtigsten Wettbewerber-Content-Gaps identifiziert?
  - Sind die Cluster-Subthemen inhaltlich trennscharf (keine Kannibalisierungsrisiken)?
- **Freigabe-Aktion:** Bestaetigung des Markdown-Outputs `outputs/1-pillar-themen.md` und Freigabe fuer Schritt 1b.

---

### Gate 2: Menuestruktur- & Design-Token-Freigabe
- **Position:** Nach Ausfuehrung von `1b-seitenarchitektur.xml.md` und `1c-pillar-template.xml.md`.
- **Reviewer:** Raphael Rechberger.
- **Pruefkriterien:**
  - Ist das visuelle Menuediagramm `outputs/1b-menuestruktur.html` im Browser fehlerfrei darstellbar und kundenpraesentabel?
  - Sind die extrahierten CSS-Tokens in `standards/design-system.css` visuell deckungsgleich mit dem Screenshot der Kunden-Website?
  - Stimmt die Zuordnung: Primare Pillar-Page vs. unterstuetzender Themen-Hub?
- **Freigabe-Aktion:** Speicherung des Design-Systems und Freigabe fuer Schritt 2.

---

### Gate 3: Keyword- & Cluster-Validierung
- **Position:** Nach Ausfuehrung von `2-cluster-recherche.xml.md`.
- **Reviewer:** Raphael Rechberger.
- **Pruefkriterien:**
  - Wurden alle Seed-Keywords via AgentSEO mit echten Metriken angereichert?
  - Sind lokale Pflicht-Landingpages (auch bei Suchvolumen 0) fuer die Gebietsabdeckung korrekt markiert?
  - Liegt die CSV-Datei `outputs/2-cluster-themen-agentseo.csv` vollstaendig vor?
- **Freigabe-Aktion:** Freigabe der CSV-Daten fuer den Kapazitaets-Solver in Schritt 3.

---

### Gate 4: 120-Tage-Roadmap-Abnahme
- **Position:** Nach Ausfuehrung von `3-120-tage-plan.xml.md` und `capacity_matrix_solver.py`.
- **Reviewer:** Jesse Jensen & Raphael Rechberger.
- **Pruefkriterien:**
  - Entspricht jede der 17 Wochen exakt dem Budget von 10 bis 15 Stunden?
  - Sind lokale Money-Pages prioritativ in Phase 1 und 2 platziert?
  - Ist die interne Verlinkungs-Map (vertikal zu Pillar und horizontal zu Siblings) logisch und abwechslungsreich?
- **Freigabe-Aktion:** Finale Abnahme der Roadmap `outputs/3-plan.md` und Uebernahme in Notion.

---

### Gate 5: Redaktions-Briefing & Copywriter-Handoff
- **Position:** Nach Ausfuehrung von `4a-content-briefing-und-schema.xml.md` fuer ein spezifisches Thema.
- **Reviewer:** Copywriter (Regina, Katja, Alexander) / Raphael.
- **Pruefkriterien:**
  - Passt die Gliederung zur realen SERP-Wettbewerbstiefe?
  - Ist die Tonalitaet der Nische (YMYL, B2B, direkt) in den Formulierungsbeispielen getroffen?
  - Ist das Schema.org JSON-LD Markup fehlerfrei und vollstaendig?
- **Freigabe-Aktion:** Handoff an den Texter in Notion zur Ausformulierung.

---

### Gate 6: HTML-Landingpage-Abnahme
- **Position:** Nach Ausfuehrung von `4b-landingpage-html.xml.md` (nur fuer Landingpages).
- **Reviewer:** Raphael Rechberger / Frontend-Designer.
- **Pruefkriterien:**
  - Ist die Datei `landingpage-[slug]-[ort].html` lokal im Browser vollstaendig und responsiv renderbar?
  - Sind Local-SEO-Signale (NAP, Karte, Stadtteil-Nennung, Breadcrumbs) sichtbar eingebunden?
  - Bindet die Seite das globale `design-system.css` ein?
- **Freigabe-Aktion:** Uebergabe an den Web-Entwickler zur Integration in WordPress/Elementor.

---

### Gate 7: 30/60/90-Tage Performance-Review
- **Position:** Nach 30, 60 und 90 Tagen Laufzeit (`3b-performance-check.xml.md`).
- **Reviewer:** Jesse Jensen & Raphael Rechberger.
- **Pruefkriterien:**
  - Welche Seiten performen in den Top 20?
  - Wurden Stagnierer identifiziert und fehlende Sibling-Links nachgebessert?
  - Wird die naechste Phase auf Basis harter Daten angepasst, statt den Plan stur weiterlaufen zu lassen?
- **Freigabe-Aktion:** Update der Phasen-Tabelle in `outputs/3-plan.md` und Notion.
