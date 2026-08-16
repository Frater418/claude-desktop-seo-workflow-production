# Betriebshandbuch: Claude Desktop SEO Workflow

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor:** Raphael Rechberger  
**Zielgruppe:** Jesse Jensen, Raphael Rechberger & Heartweb Projekt-Teams  
**Version:** 1.0.0  

---

## 1. Einleitung & taegliche Nutzung

Dieses Handbuch erklaert Schritt fuer Schritt, wie neue Kundenprojekte in der Claude Desktop App aufgesetzt und durchgefuehrt werden.

---

## 2. Einmalige Einrichtung der Claude Desktop App

1. **Konfigurationsdatei oeffnen:**
   - **Windows:** Oeffne `%APPDATA%\Claude\claude_desktop_config.json` mit einem Texteditor.
   - **macOS:** Oeffne `~/Library/Application Support/Claude/claude_desktop_config.json`.
2. **Server eintragen:** Kopiere den Inhalt aus `mcp/claude_desktop_config.template.json` in deine Konfigurationsdatei.
3. **API-Key hinterlegen:** Ersetze `HIER_AGENTSEO_API_KEY_EINTRAGEN` mit deinem gueltigen AgentSEO API-Key.
4. **Claude Desktop neu starten:** Beende Claude Desktop vollstaendig und starte die App neu. In der unteren rechten Ecke der Chat-Eingabe siehst du nun das Hammer-Symbol fuer aktive Tools (`agentseo` und `filesystem`).

---

## 3. Ablauf eines Kunden-Rollouts

### Phase 1: Projekt anlegen & Kickoff (10 Minuten)
1. Erstelle einen lokalen Ordner fuer den Kunden (z.B. `C:\Kunden\simcura-pflegedienst\`).
2. Oeffne eine frische Session in Claude Desktop.
3. Kopiere den Inhalt von `prompts/0-kickoff.xml.md`, fuelle die Platzhalter im `<input_briefing>` aus und sende den Prompt.
4. Claude generiert automatisch die `manifest.json`.

### Phase 2: Pillar- & Seitenarchitektur (20 Minuten)
1. Sende `prompts/1-pillar-identifikation.xml.md`. Claude analysiert die Website und Wettbewerber und erzeugt `outputs/1-pillar-themen.md`.
2. Sende `prompts/1b-seitenarchitektur.xml.md`. Claude erzeugt das Navigationsdokument und die interaktive HTML-Menueuebersicht `outputs/1b-menuestruktur.html`.
3. Lade einen Screenshot der Kunden-Website hoch und sende `prompts/1c-pillar-template.xml.md`. Claude extrahiert die CSS-Tokens in `standards/design-system.css` und baut die Pillar-HTML-Templates.

### Phase 3: Keyword-Recherche & 120-Tage-Plan (5 Minuten)
1. Sende `prompts/2-cluster-recherche.xml.md`. Claude ruft AgentSEO auf und erzeugt vollautomatisch `outputs/2-cluster-themen-agentseo.csv` mit echten Suchvolumina.
2. Sende `prompts/3-120-tage-plan.xml.md`. Claude nutzt den deterministischen Solver und generiert den 17-Wochen-Plan in `outputs/3-plan.md`.

### Phase 4: Tagesgeschaeft (Taeglich 2 Minuten pro Content-Stueck)
1. Schau in `outputs/3-plan.md`, welches Thema heute ansteht.
2. Sende `prompts/4a-content-briefing-und-schema.xml.md` mit dem Titel des Themas.
3. Claude fuehrt den Live-SERP-Check durch, generiert das Schema.org JSON-LD und speichert das redaktionsfertige Briefing unter `outputs/briefings/briefing-[slug].md`.
4. Bei Landingpages: Sende `prompts/4b-landingpage-html.xml.md`, um die fertige HTML-Seite fuer den Entwickler zu erhalten.

---

## 4. Problembehebung (Troubleshooting)

| Problem / Meldung | Ursache | Loesung |
|---|---|---|
| `ERROR_MANIFEST_MISSING` | `manifest.json` liegt nicht im Projektordner. | Schritt 0 (`prompts/0-kickoff.xml.md`) zuerst ausfuehren. |
| `ERROR_AGENTSEO_FETCH_FAILED` | API-Key fehlt, Quota erschoepft oder kein Internet. | API-Key in `claude_desktop_config.json` pruefen und Guthaben aufladen. |
| `ERROR_SCREENSHOT_MISSING` | Kein Screenshot fuer Schritt 1c hochgeladen. | Screenshot der Kunden-Startseite im Chat hochladen oder unter `inputs/` ablegen. |
| Werkzeuge (Tools) erscheinen nicht in Claude Desktop | Node.js fehlt oder fehlerhafter JSON-Syntax in der Config. | `node -v` im Terminal pruefen; JSON-Syntax in `claude_desktop_config.json` validieren. |
