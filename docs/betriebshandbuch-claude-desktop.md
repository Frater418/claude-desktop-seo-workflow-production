# Betriebshandbuch: Claude Desktop SEO Workflow

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor & Architektur:** Raphael Rechberger  
**Zielgruppe:** Jesse Jensen, Raphael Rechberger & Heartweb Projekt-Teams  
**Version:** 1.2.0  
**Status:** Aktiv  

---

## 1. Uebersicht & Voraussetzungen

Dieses Handbuch beschreibt die vollstaendige Inbetriebnahme und den operativen Alltag mit dem modernisierten SEO-Workflow in der **Claude Desktop App**.

### Technische Systemvoraussetzungen
1. **Claude Desktop App:** Installiert auf Windows 10/11 oder macOS.
2. **Node.js (LTS Version):** Erforderlich fuer die MCP-Server (`npx mcp-remote` und `@modelcontextprotocol/server-filesystem`).  
   *Pruefung im Terminal:* `node -v` und `npx -v`
3. **Python (3.9 bis 3.12):** Erforderlich fuer den deterministischen Solver (`capacity_matrix_solver.py`) und den Schema-Validator.  
   *Pruefung im Terminal:* `python --version`

---

## 2. Einmalige Einrichtung der Claude Desktop App

### Schritt 2.1: Konfigurationsdatei oeffnen
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
  *(Pfad im Explorer: `C:\Users\<DeinBenutzer>\AppData\Roaming\Claude\claude_desktop_config.json`)*
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

### Schritt 2.2: MCP-Server konfigurieren
Fuege den Inhalt aus `mcp/claude_desktop_config.template.json` ein:

```json
{
  "mcpServers": {
    "agentseo": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://www.agentseo.dev/mcp",
        "--header",
        "x-api-key:DEIN_AGENTSEO_API_KEY"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\offic\\Documents\\Projekte"
      ]
    }
  }
}
```

*Hinweis:* Passe den Pfad unter `filesystem` an das Hauptverzeichnis deiner Kundenprojekte an.

### Schritt 2.3: Claude Desktop neu starten & Pruefen
1. Beende Claude Desktop vollstaendig (auch im Windows System-Tray unten rechts).
2. Starte Claude Desktop neu.
3. Im Eingabefeld unten rechts erscheint nun ein **Hammer-Symbol**. Klicke darauf: Es muessen die Tools von `agentseo` (45 Tools) und `filesystem` gelistet sein.

---

## 3. Einrichten des Projekts in Claude Desktop (Projects)

1. Klicke in Claude Desktop links auf **Projects** -> **Create Project** (Name: `Heartweb SEO Engine`).
2. **Project Knowledge hochladen:** Lade diese Dateien hoch:
   - `standards/manifest.schema.json`
   - `standards/design-system.css`
   - `standards/dateinamen-und-output-vertrag.md`
   - `docs/copywriter-handoff-guidelines.md`
3. **Project Instructions (System-Prompt):** Kopiere den Inhalt aus [`AGENTS.md`](https://github.com/Frater418/claude-desktop-seo-workflow-production/blob/master/AGENTS.md) in das Instruktionsfeld.

---

## 4. Schritt-fuer-Schritt Ablauf fuer einen neuen Kunden

### Phase 1: Projekt-Start & Architektur (Schritte 0 bis 1c)
1. **Ordner anlegen:** Erstelle z.B. `C:\Users\offic\Documents\Projekte\Kunden\simcura-pflegedienst\`.
2. **Schritt 0 senden (`prompts/0-kickoff.xml.md`):** Fuelle im `<input_briefing>` Kundenname, Domain und Konkurrenten aus. Claude schreibt `manifest.json`.
3. **Schritt 1 senden (`prompts/1-pillar-identifikation.xml.md`):** Claude scannt Domain & Konkurrenz und erzeugt `outputs/1-pillar-themen.md`.
4. **Schritt 1b senden (`prompts/1b-seitenarchitektur.xml.md`):** Claude erzeugt `outputs/1b-seitenarchitektur.md` und das interaktive HTML-Menuediagramm `outputs/1b-menuestruktur.html`.
5. **Schritt 1c senden (`prompts/1c-pillar-template.xml.md`):** Lade einen Screenshot der Kunden-Website im Chat hoch. Claude sichert die CSS-Tokens in `design-system.css` und generiert die HTML-Pillar-Vorlagen.

### Phase 2: Keyword-Recherche & 120-Tage-Plan (Schritte 2 bis 3)
1. **Schritt 2 senden (`prompts/2-cluster-recherche.xml.md`):** Claude ruft AgentSEO per MCP auf und schreibt die vollstaendige CSV `outputs/2-cluster-themen-agentseo.csv`.
2. **Schritt 3 senden (`prompts/3-120-tage-plan.xml.md`):** Claude nutzt den deterministischen Solver und generiert den fertigen 17-Wochen-Plan `outputs/3-plan.md` inkl. Verlinkungs-Maps.

### Phase 3: Tagesgeschaeft & Redaktions-Briefing (Schritt 4a & 4b)
1. **Schritt 4a senden (`prompts/4a-content-briefing-und-schema.xml.md`):** Nenne das anstehende Thema. Claude prueft live Google, generiert das Schema.org JSON-LD und speichert das fertige Briefing mit Notion-Frontmatter unter `outputs/briefings/briefing-[slug].md`.
2. **Schritt 4b senden (`prompts/4b-landingpage-html.xml.md`):** Nur fuer Landingpages: Claude baut die autarke HTML-Seite unter `outputs/html/`.

---

## 5. Lokale Hilfstools im Terminal

Falls du Berechnungen oder Validierungen unabhaengig von Claude Desktop ausfuehren moechtest:

```bash
# 120-Tage Kapazitaets-Solver manuell starten:
python mcp/tools/capacity_matrix_solver.py --input outputs/2-cluster-themen-agentseo.csv --output outputs/3-plan.md

# Schema.org JSON-LD Validator ausfuehren:
python mcp/tools/validate_schema_jsonld.py
```

---

## 6. Problembehebung (Troubleshooting)

| Fehlermeldung / Problem | Ursache | Sofort-Massnahme |
|---|---|---|
| `ERROR_MANIFEST_MISSING` | `manifest.json` existiert nicht im Projektordner. | Schritt 0 (`prompts/0-kickoff.xml.md`) zuerst ausfuehren. |
| `ERROR_AGENTSEO_FETCH_FAILED` | API-Key fehlt, Quota erschoepft oder kein Netzwerk. | API-Key in `claude_desktop_config.json` pruefen und Guthaben aufladen. |
| `ERROR_SCREENSHOT_MISSING` | Kein Screenshot fuer Schritt 1c hochgeladen. | Screenshot der Kunden-Startseite im Chat hochladen oder unter `inputs/` ablegen. |
| Hammer-Symbol erscheint nicht in Claude Desktop | Node.js fehlt oder fehlerhafter JSON-Syntax in der Konfiguration. | `node -v` pruefen; JSON-Syntax in `claude_desktop_config.json` validieren und Claude neu starten. |
