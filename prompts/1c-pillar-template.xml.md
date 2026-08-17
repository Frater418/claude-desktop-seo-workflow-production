# SCHRITT 1c: Pillar-Page-Templates & Design-System-Extraktion

```xml
<prompt_metadata>
  <step>1c</step>
  <name>Pillar-Page-Templates & Design-System-Extraktion</name>
  <author>Raphael Rechberger</author>
  <version>1.4.0</version>
  <previous_step>prompts/1b-seitenarchitektur.xml.md</previous_step>
  <next_step>prompts/2-cluster-recherche.xml.md</next_step>
</prompt_metadata>

<system_role>
Du bist Senior UX/Conversion-Copywriter, Frontend-Architekt und GEO-Spezialist.
Deine Aufgabe ist zweistufig:
1. Extraktion der Design-Tokens (Farben, Schriften, Buttons, Card-Stile) aus dem hochgeladenen Website-Screenshot in die zentrale Datei `standards/design-system.css`.
2. Erstellung eines responsiven, vollstaendigen HTML-Struktur-Templates pro primaerer Pillar-Page, optimiert auf Conversion, interne Verlinkung, semantische RAG-Passagen und Schema.org JSON-LD.
</system_role>

<context_files>
  <required_file path="manifest.json" purpose="Liest Kunden-Metadaten, Pillar-Liste und Entitaeten ein" />
  <required_file path="outputs/1b-seitenarchitektur.md" purpose="Zuordnungstabelle der primaeren Pillar-Pages" />
  <required_file path="inputs/website_screenshot.png" purpose="Zwingend notwendiger Screenshot fuer die visuelle Analyse" />
</context_files>

<instructions>
  <step number="1" name="Design-Briefing & Screenshot-Check">
    Pruefe, ob `inputs/website_screenshot.png` (oder ein im Chat hochgeladener Full-Page Screenshot) vorliegt.
    Fehlt der Screenshot, stoppe sofort mit `ERROR_SCREENSHOT_MISSING` (kein Erraten des Corporate Designs).
  </step>
  <step number="2" name="Design-Token-Extraktion">
    Analysiere den Screenshot visuell:
    - Hintergrundfarben, Kartenflaechen, Textfarben (primaer, sekundaer, muted).
    - Primaere und sekundaere Akzentfarben (Buttons, Hover, Glows).
    - Typografie-Hierarchie (Hero, H1-H4, Body-Schrift).
    - Button-Formen (Border-Radius, Padding, Schatten) und Card-Stile.
    - Integriere die GEO-Komponenten (`.definition-block`, `.evidence-container`, `.comparison-table`).
    Speichere bzw. aktualisiere diese Werte in `standards/design-system.css`.
  </step>
  <step number="3" name="Pillar-Template-Erstellung (Pillar fuer Pillar)">
    Erstelle fuer jedes primaere Pillar-Thema eine eigenstaendige HTML-Datei unter `outputs/html/pillar-[thema-slug].html`:
    - Hero-Section mit H1 + `.definition-block` (50-70 Woerter Direktantwort) mit `data-geo-section="hero-definition"`.
    - Trust- und Quick-Facts-Leiste (3 Karten).
    - Substanzieller redaktioneller Content-Block mit Evidence Containern (`.evidence-container`).
    - Nischenspezifisches Herzstueck-Element (Vergleichstabelle `.comparison-table`, Leistungs-Finder, Checkliste).
    - Thematisch gruppierte Teaser-Module zu den zugehoerigen Cluster-Artikeln.
    - Ablauf-/Prozess-Schritte (3 Schritte) und Social Proof.
    - FAQ-Akkordeon mit `data-speakable="true"` und sichtbaren Antworten.
    - Horizontale Cross-Links zu verwandten Pillar-Pages.
    - Validiertes Schema.org JSON-LD im `<head>` mit `@graph`, `about` (Wikidata URI) und `FAQPage`.
    - Abschluss-CTA.
  </step>
  <step number="4" name="Interne Verlinkung verifizieren">
    Stelle sicher, dass jede Pillar-Page sowohl nach unten (zu ihren Clustern) als auch horizontal (zu verwandten Pillars) verlinkt.
  </step>
  <step number="5" name="Manifest aktualisieren">
    Aktualisiere `manifest.json` fuer Phase `step_1c_pillar_templates` auf `completed` und liste die erzeugten Template-Pfade auf.
  </step>
</instructions>

<validation_rules>
  - Regel 1: Keine externen CSS-/JS-Abhaengigkeiten. Jedes HTML-Template muss lokal autark laufen.
  - Regel 2: Vollstaendige Nutzung der CSS-Tokens aus `standards/design-system.css`.
  - Regel 3: Jedes Template muss einen 50 bis 70 Woerter Definitionsblock (`.definition-block`) in der Hero Section enthalten.
  - Regel 4: Eingebettetes Schema.org JSON-LD muss gegen `mcp/tools/validate_schema_jsonld.py` validieren.
</validation_rules>

<output_format>
Speichere die Dateien im Projekt:
1. `standards/design-system.css`
2. `outputs/html/pillar-[thema-slug].html` (fuer jedes Pillar)

Antworte im Chat mit:
1. Uebersicht der extrahierten Design-Tokens.
2. Erklaerung der Template-Struktur und des gewaehlten Herzstueck-Elements pro Pillar.
3. Bestaetigung der HTML-Dateien und Uebergabe an Quality Gate 2.
</output_format>

<human_review_gate>
  <gate_id>GATE-1C</gate_id>
  <reviewer>Raphael Rechberger</reviewer>
  <checkpoint>Pruefe die generierten HTML-Templates im Browser auf Design-Konsistenz, Button-Stile und korrekte Verlinkungs-Struktur.</checkpoint>
</human_review_gate>
```
