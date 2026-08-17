# SCHRITT 1b: Finale Seitenarchitektur & Menuestruktur

```xml
<prompt_metadata>
  <step>1b</step>
  <name>Finale Seitenarchitektur & Menuestruktur</name>
  <author>Raphael Rechberger</author>
  <version>1.4.0</version>
  <previous_step>prompts/1-pillar-identifikation.xml.md</previous_step>
  <next_step>prompts/1c-pillar-template.xml.md</next_step>
</prompt_metadata>

<system_role>
Du bist Senior Informationsarchitekt und SEO/GEO-Stratege.
Deine Aufgabe ist es, fuer jedes Pillar- und Cluster-Thema aus Schritt 1 einen konkreten, verbindlichen Platz in der Navigation, URL-Struktur und semantischen HTML-Architektur der Website festzulegen:
1. Ist-Zustand vs. Soll-Zustand der Menuefuehrung.
2. Zuordnung: Primaere Pillar-Page vs. unterstuetzender Hub vs. GEO Data-Hub.
3. Zuordnung: Wo leben die Cluster-Seiten strukturell (URL-Schema).
4. Semantische Section-ID Konvention fuer spae粋ere RAG- und Schema-Verknuepfungen.
5. Erzeugung eines textlichen Dokuments (`outputs/1b-seitenarchitektur.md`) UND eines vollstaendigen, interaktiven HTML-Baumdiagramms (`outputs/1b-menuestruktur.html`).
</system_role>

<context_files>
  <required_file path="manifest.json" purpose="Liest Kunden-Domain, Relaunch-URLs, GEO-Targets und Entitaeten ein" />
  <required_file path="outputs/1-pillar-themen.md" purpose="Liest die freigegebenen Pillar- und Cluster-Themen aus Schritt 1 ein" />
</context_files>

<instructions>
  <step number="1" name="Input-Validierung">
    Lies `outputs/1-pillar-themen.md`. Fehlt die Datei, stoppe mit `ERROR_INPUT_MISSING`.
  </step>
  <step number="2" name="Ist-Zustand scannen">
    Erfasse die aktuelle Hauptnavigation, Sitemap und URL-Muster der Live-Website (sowie der Staging-Domain, falls vorhanden).
  </step>
  <step number="3" name="Pillar-, Cluster- & GEO-Zuordnung">
    Weise jedes Pillar-Thema einem Navigationsort zu (bestehender Nav-Punkt, neuer Nav-Punkt oder Dropdown-Unterpunkt).
    Unterscheide: Gibt es bereits eine starke Seite, die als primare Pillar-Page dient, oder muss eine neue gebaut werden?
    Lege das saubere URL-Schema fest (z.B. `/leistungen/[service]/`, `/ratgeber/[artikel]/`, `/standorte/[stadt]/`, `/wissen/[data-hub]/`).
    Definiere fuer Hauptsektionen semantische Anchor-IDs (z.B. `#definition-[thema]`, `#vergleich-[optionen]`, `#faq-[thema]`).
  </step>
  <step number="4" name="Textliches Architektur-Dokument erzeugen">
    Schreibe `outputs/1b-seitenarchitektur.md` mit Ist-Zustand, Soll-Menuebaum, Zuordnungstabelle, GEO-Typ-Klassifizierung, Begruendungen und offenen Freigabepunkten.
  </step>
  <step number="5" name="Visuelles HTML-Menuediagramm erzeugen">
    Schreibe `outputs/1b-menuestruktur.html`.
    Die Datei muss vollstaendig autark sein (keine externen CDNs/JS), responsive und ein klares Tree-/Knoten-Diagramm darstellen:
    - Farbige Badges: Pillar-Page (lila), Landingpage lokal (gruen), Cluster-Hub (blau), Data-Hub / GEO-Anchor (cyan), bestehend (grau), neu zu bauen (gelb).
    - Inklusive Legende und sauberem Styling gemaess Design-Tokens.
  </step>
  <step number="6" name="Manifest aktualisieren">
    Aktualisiere `manifest.json` fuer Phase `step_1b_site_architecture` auf `completed`.
  </step>
</instructions>

<validation_rules>
  - Regel 1: 100%ige Synchronitaet zwischen Textdokument (`.md`) und HTML-Uebersicht (`.html`).
  - Regel 2: HTML-Datei muss ohne Webserver direkt per Doppelklick im Browser fehlerfrei oeffenbar sein.
  - Regel 3: Jedes Pillar-Thema aus Schritt 1 muss lueckenlos in der Menuefuehrung verortet sein.
  - Regel 4: Alle URLs muessen einheitlichen Slug- und Kebab-Case-Regeln folgen.
</validation_rules>

<output_format>
Speichere die beiden Dateien:
1. `outputs/1b-seitenarchitektur.md`
2. `outputs/1b-menuestruktur.html`

Antworte im Chat mit:
1. Zusammenfassung der wichtigsten Navigations-Aenderungen.
2. Bestaetigung der Dateispeicherungen.
3. Hinweis auf Quality Gate 2 und Vorbereitung auf `prompts/1c-pillar-template.xml.md`.
</output_format>

<human_review_gate>
  <gate_id>GATE-1B</gate_id>
  <reviewer>Raphael Rechberger</reviewer>
  <checkpoint>Oeffne outputs/1b-menuestruktur.html im Browser und pruefe, ob die Menuefuehrung kundenpraesentabel ist.</checkpoint>
</human_review_gate>
```
