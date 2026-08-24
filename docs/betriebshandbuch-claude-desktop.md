# Betriebshandbuch: Claude Desktop SEO Workflow

> **Lifecycle: historical.** Dieses Handbuch beschreibt die alte Claude-Desktop-Bedienung. Aktuelle Bedienoberflaeche ist die deutsche Single-Admin Console. Aktuelle Architektur und Session-Reihenfolge: `docs/00-current-production-architecture.md` und `00_admin/SESSION_BOOTSTRAP.md`.

**Projekt:** Modernisierung des Claude Desktop SEO-Workflows  
**Autor & Architektur:** Raphael Rechberger  
**Zielgruppe:** Jesse Jensen, Raphael Rechberger & Heartweb Projekt-Teams  
**Version:** 1.3.0  
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
        "x-api-key:HIER_AGENTSEO_API_KEY_EINTRAGEN"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\offic\\Documents\\Projekte",
        "C:\\Users\\offic\\Desktop\\Heartweb"
      ]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "HIER_GITHUB_PERSONAL_ACCESS_TOKEN_EINTRAGEN"
      }
    }
  }
}
```

*Hinweise:*
- Die beiden `filesystem`-Roots muessen sowohl die Kunden-Workspaces unter
  `Documents\Projekte\Heartweb\Kunden\` als auch das Framework-Repo abdecken, weil die Prompts
  `standards/manifest.schema.json`, `standards/location-codes.json` und `standards/design-system.css`
  lesen. Ein Root, der nur auf die Kundenordner zeigt, laesst Schritt 0 ins Leere laufen.
- Der AgentSEO-Key steht direkt im Header-Argument. Eine Schreibweise wie `${AGENTSEO_API_KEY}` in
  `args` wird nicht aufgeloest und landet wortwoertlich im HTTP-Header.

### Schritt 2.2b: GitHub-Server (fuer direkte Repo-Zugriffe)

Der Block `github` im Template bindet den GitHub-MCP-Server ein. Am 17.08.2026 live verifiziert:
26 Werkzeuge, darunter `push_files`, `create_branch`, `create_pull_request` und `get_file_contents`.

1. **Token erstellen:** github.com, Settings, Developer settings, Personal access tokens,
   Fine-grained tokens, Generate new token.
   - Resource owner: `Frater418`
   - Repository access: Only select repositories, `claude-desktop-seo-workflow-production`
   - Permissions, Repository permissions: `Contents: Read and write`, optional
     `Pull requests: Read and write`
2. **Token einsetzen:** In `claude_desktop_config.json` im Block `github` unter `env` den Platzhalter
   `HIER_GITHUB_PERSONAL_ACCESS_TOKEN_EINTRAGEN` ersetzen. Der Token bleibt auf dem eigenen Rechner
   und taucht in keinem Chat auf.
3. **Warum hier `env` funktioniert und bei AgentSEO nicht:** Werte unter `env` werden als echte
   Umgebungsvariablen an den Serverprozess uebergeben. Eine Schreibweise wie `${VARIABLE}` innerhalb
   von `args` wird dagegen nicht aufgeloest und landet wortwoertlich im HTTP-Header. Deshalb steht der
   AgentSEO-Key direkt im Header-Argument.
4. **Alternative:** GitHub bietet zusaetzlich einen gehosteten Remote-Server unter
   `https://api.githubcopilot.com/mcp/`, einzubinden ueber `mcp-remote` mit dem Header
   `Authorization:Bearer <PAT>`. Beide Wege sind gleichwertig, der lokale Server oben ist der
   verifizierte Stand.
5. **Grenze:** Ein MCP-Server in Claude Desktop wirkt in Claude Desktop. Eine Cowork-Session in der
   Cloud erreicht ihn nur bei aktiver Bruecke zum Desktop und arbeitet dann ueber die GitHub-API,
   nicht per `git push` aus dem Cloud-Container.

---

### Schritt 2.3: Claude Desktop neu starten & Pruefen
1. Beende Claude Desktop vollstaendig (auch im Windows System-Tray unten rechts).
2. Starte Claude Desktop neu.
3. Im Eingabefeld unten rechts erscheint nun ein **Hammer-Symbol**. Klicke darauf: Es muessen die Tools von `agentseo` (48 Tools, Stand 17.08.2026), `filesystem` und, falls eingerichtet, `github` gelistet sein.

---

## 3. Einrichten des Projekts in Claude Desktop (Projects)

1. Klicke in Claude Desktop links auf **Projects** -> **Create Project** (Name: `Heartweb SEO Engine`).
2. **Project Knowledge hochladen:** Lade diese Dateien hoch:
   - `standards/manifest.schema.json`
   - `standards/design-system.css`
   - `standards/dateinamen-und-output-vertrag.md`
   - `standards/location-codes.json`
   - `docs/copywriter-handoff-guidelines.md`
3. **Project Instructions (System-Prompt):** Kopiere den Inhalt aus [`AGENTS.md`](https://github.com/Frater418/claude-desktop-seo-workflow-production/blob/master/AGENTS.md) in das Instruktionsfeld. `CLAUDE.md` gehoert nicht zusaetzlich hinein, das ist die Kurzfassung fuer CLI-Agenten.

---

## 4. Schritt-fuer-Schritt Ablauf fuer einen neuen Kunden

### Phase 1: Projekt-Start & Architektur (Schritte 0 bis 1c)
1. **Ordner anlegen:** Erstelle den Kundenordner unter dem kanonischen Pfad, z.B. `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\simcura-pflegedienst\`.
2. **Schritt 0 senden (`prompts/0-kickoff.xml.md`):** Fuelle im `<input_briefing>` Kundenname, Domain, Konkurrenten und das Land aus. Claude schreibt `manifest.json` inklusive `country` und `location_code`.
3. **Schritt 1 senden (`prompts/1-pillar-identifikation.xml.md`):** Claude scannt Domain & Konkurrenz und erzeugt `outputs/1-pillar-themen.md`.
4. **Schritt 1b senden (`prompts/1b-seitenarchitektur.xml.md`):** Claude erzeugt `outputs/1b-seitenarchitektur.md` und das interaktive HTML-Menuediagramm `outputs/1b-menuestruktur.html`.
5. **Schritt 1c senden (`prompts/1c-pillar-template.xml.md`):** Lade einen Screenshot der Kunden-Website im Chat hoch. Claude sichert die CSS-Tokens in `design-system.css` und generiert die HTML-Pillar-Vorlagen. Ohne Screenshot bricht der Schritt mit `ERROR_SCREENSHOT_MISSING` ab und wird nicht uebersprungen.

### Phase 2: Keyword-Recherche & 120-Tage-Plan (Schritte 2 bis 3)
1. **Schritt 2 senden (`prompts/2-cluster-recherche.xml.md`):** Claude ruft AgentSEO per MCP auf und schreibt die vollstaendige CSV `outputs/2-cluster-themen-agentseo.csv`. Der Aufruf laeuft asynchron (`sync: false` plus `agentseo_job_status`), weil synchrone Aufrufe nach 60 Sekunden abbrechen. Zielmarkt kommt aus `country` und `location_code` im Manifest.
2. **Schritt 3 senden (`prompts/3-120-tage-plan.xml.md`):** Claude nutzt den deterministischen Solver und generiert `outputs/3-plan.md` inkl. Verlinkungs-Maps. Horizont sind 17 Wochen, die Zeile `Kapazitaets-Messung` im Plankopf nennt die Anzahl belegter Wochen und die gemessene Spanne.

### Phase 2b: Performance-Zyklus (Schritt 3b, ab Tag 30)
1. **Voraussetzung:** Die ersten Inhalte sind seit mindestens 21 Tagen online.
2. **Export ablegen:** Lege den Ranking- oder GSC-Export als `inputs/performance_export.csv` im Kundenordner ab.
3. **Schritt 3b senden (`prompts/3b-performance-check.xml.md`):** Claude erzeugt `outputs/3b-performance-check.md` und schreibt die angepasste `outputs/3-plan.md` zurueck. Der Schritt wiederholt sich an Tag 30, 60 und 90 und laeuft ausserhalb der Erstsequenz.

### Phase 3: Tagesgeschaeft & Redaktions-Briefing (Schritt 4a & 4b)
1. **Schritt 4a senden (`prompts/4a-content-briefing-und-schema.xml.md`):** Nenne das anstehende Thema. Claude prueft live Google, generiert das Schema.org JSON-LD und speichert das fertige Briefing mit Notion-Frontmatter unter `outputs/briefings/briefing-[slug].md`. Achtung: `agentseo_content_serp_outline` loest deutsche Maerkte falsch auf, verwertbar sind nur die SERP-Signale (rankende Domains, SERP-Features, Wettbewerbsniveau).
2. **Schritt 4b senden (`prompts/4b-landingpage-html.xml.md`):** Nur fuer Landingpages: Claude baut die autarke HTML-Seite unter `outputs/html/`.

---

## 5. Lokale Hilfstools im Terminal

Falls du Berechnungen oder Validierungen unabhaengig von Claude Desktop ausfuehren moechtest:

```bash
# 120-Tage Kapazitaets-Solver manuell starten:
python mcp/tools/capacity_matrix_solver.py --input outputs/2-cluster-themen-agentseo.csv --output outputs/3-plan.md

# Schema.org JSON-LD Validator:
# Achtung, offener Punkt: das Skript hat noch keine Kommandozeilen-Schnittstelle.
# Der Aufruf unten gibt nur eine Bereitschaftsmeldung aus und prueft nichts.
# Bis zum Nachbau der CLI ist die Pruefung ueber die Google Rich Results Test Seite zu machen.
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
| `ERROR_BRIEFING_INCOMPLETE` | Eine Pflichtangabe im `<input_briefing>` von Schritt 0 fehlt, z.B. das Land. | Fehlendes Feld ergaenzen und Schritt 0 erneut senden. |
| `ERROR_LOCATION_UNKNOWN` | `country` fehlt im Manifest oder ist nicht in `standards/location-codes.json` hinterlegt. | Land in die Tabelle aufnehmen (Regel fuer Laender: 2000 plus ISO-3166-numerisch) und Schritt 0 erneut senden. |
| `ERROR_LOCATION_MISMATCH` | Die AgentSEO-Antwort ist mit einem anderen Markt beschriftet als im Manifest steht. | `location` und `location_code` gemeinsam uebergeben und den Aufruf wiederholen. Keine Daten in die CSV uebernehmen. |
| `ERROR_INSUFFICIENT_CLUSTER_COVERAGE` | Nach zwei Recherche-Runden hat eine Pillar-Page weniger als 25 validierte Zeilen. | Seed-Phrasen erweitern oder die Pillar-Struktur aus Schritt 1 nachschaerfen. Schritt 2 darf nicht als completed eingetragen werden. |
| Tool-Call bricht nach 60 Sekunden ab | Der Aufruf lief synchron (`sync: true`, Default). | Mit `sync: false` aufrufen und das Ergebnis ueber `agentseo_job_status` abholen. |
