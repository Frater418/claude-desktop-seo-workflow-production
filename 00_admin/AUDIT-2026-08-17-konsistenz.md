# Konsistenz-Audit Framework-Repo

**Projekt:** Heartweb Claude Desktop SEO Workflow Framework
**Autor:** Raphael Rechberger
**Auditdatum:** 17. August 2026
**Auditbasis:** Commit `65a5f21` (master), vollstaendiger Klon, 38 Dateien
**Methode:** Drei parallele Audit-Durchlaeufe (Prompts, Standards/Tools/Tests, Doku), anschliessend Nachpruefung der schwerwiegenden Findings direkt an den Dateien und durch echte Ausfuehrung der Python-Tools

---

## 1. Ergebnis in Zahlen

| Schweregrad | Anzahl | Kernaussage |
| --- | --- | --- |
| BLOCKER | 4 | Zwei Quality Gates sind faktisch wirkungslos, ein Prompt kann Zahlen erfinden, der Kundenpfad ist nicht erreichbar |
| HOCH | 15 | Fail-Fast-Doktrin im Code nicht umgesetzt, Datenvertraege dreifach abweichend, Testprotokoll nicht reproduzierbar |
| MITTEL | 26 | Versionsdrift, Pfad- und Namensvarianten, fehlende Felder, Doku-Luecken |
| NIEDRIG | 13 | Kosmetik, ungenutzte Token und Imports, Wortlautfehler |

Das Framework ist strukturell sauber gebaut: Sequenzkette geschlossen, Autorenschaft durchgaengig, Typografie-Regel eingehalten, Manifest-Fixture validiert fehlerfrei, Pflichtstandorte werden zu 100 Prozent verplant. Die Probleme liegen konzentriert an zwei Stellen: die Fail-Fast-Doktrin ist in den Python-Tools nicht implementiert, und die Doku beschreibt einen Zustand, den ein echter Lauf nicht reproduziert.

---

## 2. BLOCKER

### B1: Der Schema-Validator ist nicht aufrufbar, das Quality Gate fuer Schritt 4a existiert nur auf Papier

`mcp/tools/validate_schema_jsonld.py:103-104`

```python
if __name__ == "__main__":
    print("Schema JSON-LD Validator v1.0.0 bereit.")
```

Kein argparse, kein `sys.argv`, keine Datei- oder stdin-Uebergabe, `import sys` ungenutzt. Der in `CLAUDE.md:47`, `AGENTS.md:64`, `docs/betriebshandbuch-claude-desktop.md:108` und `standards/dateinamen-und-output-vertrag.md:54` dokumentierte Befehl `python mcp/tools/validate_schema_jsonld.py` prueft nichts und endet mit Exit 0. Zusaetzlich ruft kein einziger Prompt den Validator auf.

**Soll:** CLI mit `--input` (Datei oder Glob), Exit-Code ungleich 0 bei Fehlern, verbindlicher Aufruf in Prompt 4a und 4b.

### B2: Der Solver verwirft nicht platzierbare Deliverables stillschweigend

`mcp/tools/capacity_matrix_solver.py:144-145`

```python
if not placed:
    pass
```

Nachgepruefter Testlauf mit 40 Pillar-Pages (je 8.0h): 17 von 40 Items zugeteilt, 23 Items lautlos verschwunden, Exit 0, keine Warnung, keine Backlog-Sektion. `prompts/3-120-tage-plan.xml.md:88` verlangt aber ausdruecklich einen Backlog fuer Tag 121 und folgende, und `CLAUDE.md` Regel 3 verbietet stille Fallbacks. Mit der Referenz-Fixture schlaegt der Bug nicht zu (61 von 61 Items verplant), im Kundenfall mit vielen Pillars sofort.

**Soll:** Nicht platzierbare Items in eine ausgewiesene Backlog-Sektion schreiben oder mit explizitem Fehlercode abbrechen.

### B3: Prompt 4a hat keine einzige Abbruchbedingung, kann also Metriken erfinden und via Notion ausliefern

`prompts/4a-content-briefing-und-schema.xml.md` enthaelt keinen einzigen `ERROR_`-Code (nachgepruefte grep-Suche ueber alle 9 Prompts: nur `0-kickoff` und `4a` sind leer). Gleichzeitig verlangt das Frontmatter harte Zahlen, Zeile 87 bis 88: `search_volume: 70`, `difficulty: 12`. Faellt der SERP-Call aus oder ist das Thema nicht im Plan, gibt es keine Stoppregel. Das Ergebnis geht direkt an Regina, Katja und Alexander.

**Soll:** Codes analog `prompts/2-cluster-recherche.xml.md:54` (`ERROR_AGENTSEO_FETCH_FAILED`), plus Verbot, Metriken ohne Quelle in das Frontmatter zu schreiben.

### B4: Der Filesystem-MCP-Root zeigt nicht auf den kanonischen Kunden-Workspace

Kanonisch bestaetigt: `C:\Users\offic\Documents\Projekte\Heartweb\Kunden\<slug>\`. Im Repo steht an sieben Stellen ein Pfad ohne die Ebene `Heartweb`, in einer davon eine dritte Variante:

| Datei:Zeile | Ist |
| --- | --- |
| `mcp/claude_desktop_config.template.json:21` | `Projekte\\Kunden` |
| `docs/02-research-und-technische-spezifikation.md:50` | `Projekte\\Kunden` |
| `CLAUDE.md:18` | `Projekte\Kunden\<client-slug>\` |
| `AGENTS.md:20` | `Projekte\Kunden\simcura-pflegedienst\` |
| `AGENTS.md:39` | `C:\Projekte\Kunden\simcura\` (dritte Variante) |
| `docs/betriebshandbuch-claude-desktop.md:83` | `Projekte\Kunden\simcura-pflegedienst\` |
| `00_admin/PROJECT_STATE.md:67` | `Projekte\Kunden\<kunde-slug>\` |
| `docs/betriebshandbuch-claude-desktop.md:52` | Root `Projekte` (vierte Variante) |

Steht der Workspace unter `Projekte\Heartweb\Kunden`, sieht der Server ihn mit dem Template nicht, und die in `CLAUDE.md` Abschnitt 2 beschriebene dateibasierte Kontext-Persistenz bricht beim ersten Kundenlauf.

**Soll:** Zwei Roots eintragen: den Framework-Pfad unter `Projekte\Hermes\04_projects\active\Heartweb-Claude-Desktop-SEO-Workflow` (die Prompts lesen `standards/design-system.css` und `standards/manifest.schema.json`) und `Projekte\Heartweb\Kunden`. Alle acht Fundstellen vereinheitlichen.

---

## 3. HOCH

**H1: Die 17-Wochen-Behauptung ist nicht reproduzierbar.** Nachgepruefter Lauf mit `tests/fixtures/sample_cluster_keywords.json`: `**Gesamtumfang:** 61 Content-Stuecke | **Gesamtaufwand:** 123.5 Stunden ueber 9 aktive Wochen.` Die Wochen 10 bis 17 sind leer, Phase 4 ist reine Puffer-Phase. Der Greedy-Algorithmus saettigt vorne. Betroffene Behauptungen: `README.md:20`, `CHANGELOG.md:27`, `00_admin/PROJECT_STATE.md:45`, `AGENTS.md:61`, `docs/06-pilot-abnahme-checkliste.md:46`, `docs/05-human-in-the-loop.md:79`, `docs/03-sprint-plan.md:110`, `docs/02-research-und-technische-spezifikation.md:124`, `tests/acceptance-tests.md:15`. **Soll:** entweder Verteilung ueber alle 17 Wochen im Algorithmus oder durchgehend die Formulierung "17 Wochen Planungshorizont, davon X aktive Wochen".

**H2: Die Kapazitaets-Garantie ist ein statischer Satz.** `capacity_matrix_solver.py:85` nimmt `hours_min=10.0` an und verwendet den Wert nirgends im Algorithmus (nachgepruefte grep-Suche: nur Signatur Zeile 85 und Uebergabe Zeile 245). Geprueft wird ausschliesslich `hours_max`. Bei einem Input von zwei FAQ-Items (2.0h in Woche 1) druckt der Plan trotzdem: `**Kapazitaets-Garantie:** Jede aktive Woche liegt strikt zwischen 10.0 und 15.0 Arbeitsstunden.` `prompts/3-120-tage-plan.xml.md:74` deklariert diese Untergrenze als garantiert.

**H3: Der Solver ersetzt fehlende Metriken durch Defaults.** `capacity_matrix_solver.py:91-92,100`: fehlendes Suchvolumen und fehlende Difficulty werden 0, ein unbekannter Content-Typ bekommt via `EFFORT_WEIGHTS.get(c_type, 2.5)` pauschal 2.5 Stunden. Der Wert 2.5 kommt in keinem Prompt und keinem Benchmark vor. `prompts/3-120-tage-plan.xml.md` fordert wortwoertlich `Fehlen Werte, stoppe sofort mit ERROR_DATA_INCOMPLETE`. Das Tool, das die Arithmetik deterministisch machen soll, implementiert die eigene Regel nicht.

**H4: Der Solver meldet Erfolg, wo er scheitert.** Nachgepruefte Faelle: Aufruf ohne `--input` gibt den Usage-Text und Exit 0. Input `{"keywords": [...]}` ohne `items`-Key erzeugt Exit 0 und einen Plan mit `0 Content-Stuecke` (`capacity_matrix_solver.py:69-74`, kein `else`-Zweig). Ein leerer 120-Tage-Plan, der wie ein Erfolg aussieht, ist die gefaehrlichste Form des stillen Fallbacks. Positiv: fehlende Datei und nicht unterstuetzte Endung brechen korrekt mit Exit 1 ab.

**H5: Prompt 3 ruft den Solver nie auf.** `prompts/3-120-tage-plan.xml.md:17` sagt nur, dass die Logik des Solvers genutzt wird. Es folgt kein Befehl und keine Flags, Schritt 2 des Prompts laesst das Modell selbst rechnen. Der korrekte Aufruf steht ausschliesslich in `docs/betriebshandbuch-claude-desktop.md:105`. Damit ist der deterministische Solver in der Praxis optional.

**H6: Drei verschiedene Spaltensaetze fuer `outputs/3-plan.md`.** Prompt 3 Zeile 60 deklariert `Woche, Content-Typ, Titel/Thema, Ziel-Keyword, Suchvolumen, Wortzahl-Ziel, Aufwand (Std), Prioritaet`. Der Solver schreibt `capacity_matrix_solver.py:212` mit `KD` statt `Wortzahl-Ziel` (der Wert wird in Zeile 113 berechnet und nie ausgegeben). Prompt 4a Zeile 36 bis 39 erwartet zusaetzlich `Region` und `Difficulty`, `Region` existiert in keiner Variante. Prompt 3b Zeile 46 fuegt eine vierte Spalte `Aenderung_Status` ein und ueberschreibt dieselbe Datei. 4a liest anschliessend aus einer Datei mit unbekanntem Spaltensatz.

**H7: Die Position von Schritt 3b ist in beide Richtungen inkonsistent.** `prompts/3-120-tage-plan.xml.md:10` zeigt `next_step` auf 3b, `prompts/4a-...:9` zeigt `previous_step` auf Schritt 3. 3b ist unmittelbar nach Schritt 3 fachlich unausfuehrbar, weil `prompts/3b-performance-check.xml.md:32` mindestens 21 Tage Live-Zeit fordert. Umgekehrt lassen `CLAUDE.md:35` und `README.md:158` 3b in der Sequenz komplett aus, waehrend das Schema `step_3b_performance_check` als Pflichtphase fuehrt und `docs/betriebshandbuch-claude-desktop.md` Abschnitt 4 den Schritt nirgends erwaehnt.

**H8: Das Manifest-Schema laesst Tippfehler und Fantasiefelder durch.** Nachgepruefte Zaehlung: `additionalProperties` kommt in `standards/manifest.schema.json` genau null Mal vor, 13 Objektknoten sind offen. Ein Manifest mit `"buisness_goal"`, `"voellig_erfunden"`, `"artifacts": {"tippfehler_artifact": ...}` und `"phases": {"step_0_kickoff": {"statuss": "faked"}}` validiert mit null Fehlern. Zusaetzlich ist `status` in keinem `step_*` `required`, leere Phasenobjekte sind gueltig. Damit kann sich kein Prompt auf `phases.step_X.status` verlassen, und die dateibasierte Persistenz driftet unbemerkt.

**H9: Prompt 0 erzeugt bei wortgetreuer Befolgung ein invalides Manifest.** Ein Manifest exakt aus den Feldern des `<input_briefing>` von `prompts/0-kickoff.xml.md` erzeugt 10 Validierungsfehler, darunter `'created_at' is a required property`, `'author' is a required property`, `'artifacts' is a required property` und sieben fehlende Phasen-Keys. Prompt 0 verlangt selbst 100 Prozent Schema-Konformitaet, erhebt diese Felder aber nicht.

**H10: Das Abnahmeprotokoll ist nicht reproduzierbar.** `tests/acceptance-tests.md:28` sagt "Kapazitaets-Solver auf 40 Realdaten", die Fixture hat 61 Items. Zeile 31 sagt 17 Wochen, es sind 9. Zeile 32 sagt 12.5 Stunden Durchschnitt in Phase 1, nachgerechnet sind es 14.875 (59.5h auf 4 Wochen). TEST-03 ist nicht reproduzierbar, weil das Skript keine CLI hat (siehe B1). TEST-05 ist fuer 2 von 9 Prompts widerlegt (siehe B3). Der Status "5 von 5 bestanden" ist damit nicht haltbar. Zusaetzlich existiert kein Testrunner (kein pytest, kein conftest, keine CI), sonst waere die Drift sofort aufgefallen.

**H11: Die Pilot-Abnahme ist als erteilt dokumentiert, obwohl kein Pilot gelaufen ist.** `docs/06-pilot-abnahme-checkliste.md:78-80` meldet drei Bereiche als "Bestanden", abgenommen durch Jesse Jensen am 16.08.2026, waehrend alle Checkboxen in Abschnitt 1 und 2 leer sind und `00_admin/PROJECT_STATE.md:66` den Pilotlauf erst als naechsten Schritt fuehrt. Zeile 13 bestaetigt einen verifizierten AgentSEO-Key, `PROJECT_STATE.md:65` listet ihn als von Jesse einzuholen. Das ist ein Governance-Risiko im Kundenkontext.

**H12: Das Config-Template funktioniert so nicht und widerspricht dem eigenen Sicherheitskriterium.** `mcp/claude_desktop_config.template.json:9` nutzt `"--header", "x-api-key:${AGENTSEO_API_KEY}"` plus separaten `env`-Block. MCP-Server werden ohne Shell gestartet, `${...}` in `args` bleibt Literal. `docs/betriebshandbuch-claude-desktop.md:44` und `README.md:140` zeigen deshalb die hartkodierte Variante, was `docs/03-sprint-plan.md:86` ("ohne Hardcoding von Secrets") verletzt. Beide Formen stehen unversoehnt nebeneinander.

**H13: `standards/design-system.css` deckt die von 1c und 4b geforderten Komponenten nicht ab.** Nachgepruefte Suche: keine einzige `@media`-Query, keine Tabelle, kein Akkordeon, keine Breadcrumb, keine NAP-Box, keine Sticky-CTA, kein Testimonial. Prompt 4b fordert genau NAP-Box, Breadcrumb-Leiste, Sticky Mobile CTA und lokale Kundenstimme, Prompt 1c fordert Vergleichstabelle, FAQ-Akkordeon, Prozessschritte und Social Proof, und Regel 2 in 1c verlangt vollstaendige Nutzung der Tokens. Der Checkpoint "teste die Responsivitaet" ist gegen ein CSS ohne Breakpoints nicht bestehbar. Positiv: die Datei ist in sich widerspruchsfrei, 64 Token, keine Dubletten, keine undefinierten `var()`, keine externen Abhaengigkeiten.

**H14: Die Fixtures widersprechen sich und dem Tool-Vertrag.** `tests/fixtures/sample_manifest.json:38-39` sagt 45 Keywords und listet 7 Zielregionen, `sample_cluster_keywords.json` hat 61 Items mit 17 verschiedenen Regionen, davon 11 nicht im Manifest. `sample_serp_briefing.json` validiert nicht gegen `mcp/tool-contracts/serp_gap_analyzer.json` (`'outline' is a required property`, Keys `competitor_sections` statt `competitor_headers`). Eine Ende-zu-Ende-Reproduktion des Pilotfalls simCura ist damit nicht moeglich.

**H15: Tool-Vertraege und tatsaechliche Aufrufe passen nicht zusammen.** Aufgerufen werden `agentseo_domain_competitors` (Prompt 1), `agentseo_keyword_metrics_overview` (Prompt 2), `agentseo_analyze_serp` und `agentseo_content_serp_outline` (Prompt 4a). Vertraege existieren fuer `agentseo_keyword_metrics_overview`, `agentseo_content_serp_outline` und `agentseo_content_schema_plan`. Damit fehlen zwei Vertraege, einer ist ungenutzt, und Prompt 4a Zeile 44 nennt zwei Tools alternativ ohne Parameter, obwohl der Vertrag `keyword` als Pflichtparameter fuehrt. Positiv: die Parameter in Prompt 2 stimmen exakt mit dem Vertrag.

---

## 4. MITTEL

1. **Versionsdrift.** Hoechster `CHANGELOG.md`-Eintrag ist 1.1.0, `README.md:5`, `CLAUDE.md:6`, `docs/betriebshandbuch-claude-desktop.md:6`, `00_admin/PROJECT_STATE.md:45` sagen 1.2.0. Alles nach 1.1.0 (Solver v1.2, AGENTS.md, CLAUDE.md, PROJECT_STATE, Handbuch, Memo-PDF, scripts/) ist nicht versioniert.
2. **`CHANGELOG.md:33` sagt 40 Keywords**, die Fixture hat 61.
3. **"61 verifizierte Keywords" ist sachlich falsch.** `scripts/generate_sample_keywords.py:21` berechnet `"Suchvolumen": 80 + len(loc) * 10`. Das sind synthetische Formelwerte, keine API-Daten. Betrifft `README.md:117`, `00_admin/PROJECT_STATE.md:57`, `CHANGELOG.md:33`. Die Bezeichnung "verifiziert" widerspricht der Fail-Fast-Doktrin.
4. **Tote Referenz:** `docs/01-review-abgleich.md:32` nennt `mcp/tool-contracts/agentseo_keyword_enricher.md`, existiert nur als `.json`. Einzige nicht auflösbare Repo-Referenz im ganzen Repo.
5. **Dateinamen-Platzhalter dreifach verschieden** pro Dateityp: Pillar (`pillar-[slug]` / `pillar-[pillar-thema-slug]` / `pillar-[thema-slug]`), Landingpage (`[slug]-[ort]` / `[leistung-slug]-[stadt-slug]` / `[thema-slug]-[ort-slug]`), Briefing (`briefing-[slug]` / `briefing-[thema-slug]`), jeweils zwischen `standards/dateinamen-und-output-vertrag.md:50-67` und den Prompts.
6. **Ort-Duplikat im Landingpage-Namen.** Wendet man Prompt 4b auf sein eigenes Beispiel an, entsteht `landingpage-pflegedienst-frankfurt-bornheim-frankfurt-bornheim.html`, weil der Thema-Slug den Ort schon enthaelt.
7. **Der Ort-Slug hat keine Datenquelle.** Das 4a-Frontmatter (Zeile 81 bis 94) hat kein `region` und kein `word_count`, obwohl 4a die Region ermittelt und 4b sie fuer Dateiname, NAP-Box und Breadcrumb braucht. Synchron in `docs/copywriter-handoff-guidelines.md:24-37` nachzuziehen.
8. **4a aktualisiert das Manifest nicht.** Der Zaehler `briefings_completed` (`standards/manifest.schema.json:190`) wird nie erhoeht, 4b pflegt sein Gegenstueck korrekt.
9. **`logs/validation_errors.log` wird von nichts geschrieben.** Prompt 0 legt den Ordner an, der Vertrag deklariert die Datei, kein Prompt und kein Tool schreibt hinein. Ein Audit-Log, das nur behauptet wird.
10. **Gate-Nummerierung kollidiert.** Die Prompts fuehren neun schrittbezogene IDs (GATE-0 bis GATE-4B), `docs/05-human-in-the-loop.md:22` definiert sieben durchnummerierte Gates, `docs/06` referenziert "Quality Gate 1 bis 6". "GATE-3" bezeichnet damit zwei verschiedene Dinge.
11. **`README.md` Abschnitt 3 nennt fuenf existierende Artefakte nicht:** `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `00_admin/PROJECT_STATE.md`, Verzeichnis `scripts/`. Positiv: keine Doku-Stelle nennt noch die zurueckgenommene Cockpit-UI, der Revert ist sauber.
12. **`docs/03-sprint-plan.md:26-66`** stellt einen Repo-Baum als verbindlich dar, in dem 8 heute existierende Artefakte fehlen.
13. **Copywriter-Guidelines Abschnitt 2.2** beschreibt 4 Kern-Abschnitte, Prompt 4a erzeugt 5 Bloecke. Nicht abgebildet: EEAT-Vorgaben und der JSON-LD-Codeblock. Positiv: das YAML-Frontmatter ist zeichengenau deckungsgleich.
14. **Prompt 2 liest ein Feld, das das Schema nicht hat.** `prompts/2-cluster-recherche.xml.md:39` erwartet `location` (Land) aus dem Manifest, das Schema kennt nur `target_regions` und `language`, Prompt 0 erhebt kein Land.
15. **Content-Typ "Vergleich"** ist in der Taxonomie von Prompt 1 und 4a definiert, hat aber in Prompt 3 und im Solver keinen Aufwandswert und laeuft in den 2.5h-Default.
16. **Drei CSV-Pflichtspalten werden nie ausgewertet.** `Region`, `CPC` und `Business_Relevanz_Faktor` liest der Solver nicht, den Relevanzfaktor berechnet er selbst neu aus `Kategorie`. Die Sibling-Verlinkung matcht nur auf Pillar und Kategorie, die in Prompt 3 Zeile 65 geforderte Standort-Nachbarschaft ueber `Region` ist nicht implementiert.
17. **Mengenlogik in Schritt 2 ist in sich unerfuellbar.** 25 bis 40 Ideen pro Pillar, danach Filter auf Suchvolumen, danach Regel "mindestens 25 validierte Zeilen", ohne Nachrecherche-Schleife und ohne Fehlercode. Zusaetzlich unklar, wie sich die 25 bis 40 neuen Ideen zur in Gate 1 freigegebenen Architektur (8 bis 15 Cluster pro Pillar) verhalten.
18. **1c liest die Pillar-Liste aus der falschen Quelle.** `prompts/1c-pillar-template.xml.md:21` erwartet sie aus `manifest.json`, das Schema fuehrt dort nur `pillars_count`. Die Liste liegt in `outputs/1-pillar-themen.md`, das 1c nicht als required_file fuehrt.
19. **Der zweite Output von 3b fehlt im Vertrag.** 3b schreibt auch eine ueberarbeitete `outputs/3-plan.md`, `standards/dateinamen-und-output-vertrag.md:53` nennt nur den Performance-Report. Ein Schritt, der ein Vorgaenger-Artefakt ueberschreibt, muss im Vertrag stehen.
20. **`scripts/generate_sample_keywords.py`** ist aus dem Klon nicht ausfuehrbar (hartkodierte `C:/`-Pfade, Zeile 107 bis 111, `FileNotFoundError`, kein argparse) und das einzige Python-File ohne Autorenangabe. Damit ist die 61-Keyword-Fixture nicht regenerierbar. `generate_memo_pdf.py` hat dieselben hartkodierten Pfade, aber die Autorenangabe.
21. **`format: uri` prueft faktisch nichts.** `"domain": "das ist keine url"` validiert fehlerfrei, weil `jsonschema` das Format nur mit optionalem Zusatzpaket prueft und keine `requirements.txt` existiert. Ein `pattern` gehoert dazu.
22. **`capacity_hours_per_week` erlaubt `min > max`** und negative Werte (kein `minimum`, keine Relationspruefung).
23. **Der Validator stirbt an gueltigem JSON-LD.** Ein Array im `<script>`-Tag erzeugt `AttributeError: 'list' object has no attribute 'get'` (`validate_schema_jsonld.py:90-95`). Praxisrelevant, sobald B1 behoben ist.
24. **Der Validator meldet Ungeprueftes als gueltig.** Ein `@type` ausserhalb von `REQUIRED_FIELDS` (etwa `Recipe`) liefert `valid: True` ohne jede Pruefung. Ausserdem verschluckt Zeile 41 bis 42 `JSONDecodeError` mit `pass` und meldet "kein Block gefunden" statt Syntaxfehler, und Zeile 34 verwirft alle Folgeblocke nach dem ersten.
25. **`docs/jesse-walkthrough-memo.md:39`** sagt "bis zu 100 Keywords pro Pillar", der Vertrag sagt 25 bis 40 pro Pillar, die 100 sind das API-Limit pro Call.
26. **Governance-Widerspruch.** `docs/03-sprint-plan.md:134` sperrt jede Ausfuehrung bis zur Freigabe des Plans, `PROJECT_STATE.md:7` und das Jesse-Memo melden alle vier Sprints als abgeschlossen und veroeffentlicht. Auch der Titel von Jesse weicht ab (`PROJECT_STATE.md:19` "Co-Founder & Lead" gegen "Lead & Strategie" im aktuellen Stand), und "Copywriting Lead" in `docs/06:80` ist keine definierte Rolle.

---

## 5. NIEDRIG

1. Zwei echte Umlaute in den Prompts, wo das Repo sonst transliteriert: `3b-performance-check.xml.md:15` "veröffentlichter", `4b-landingpage-html.xml.md:81` "Responsivität". Es sind die einzigen beiden Non-ASCII-Zeichen in allen 9 Prompts.
2. Umlaute in `AGENTS.md:15-55` und `docs/02-...:245`, waehrend alle anderen Dokumente transliterieren.
3. Alle 9 Prompts stehen auf `<version>1.0.0</version>`, ebenso `design-system.css:4`, `dateinamen-und-output-vertrag.md:5`, `acceptance-tests.md:5`, `validate_schema_jsonld.py:5`, waehrend das Framework 1.2.0 fuehrt.
4. Ungenutzte Imports: `sys` und `os` im Solver, `sys` im Validator (Letzteres ist die Spur der nie fertiggestellten CLI).
5. `--json-out` zusammen mit `--output plan.md` schreibt JSON in eine `.md`-Datei, ohne Warnung.
6. Die Puffer-Phasen-Meldung im Plan behauptet "alle Themen in Phase 1 bis 2 verplant", obwohl 12.0h in Phase 3 liegen. Statischer Text.
7. `Region` ist fuer 20 Fixture-Items pauschal "Rhein-Main", obwohl die Items konkrete Staedte adressieren (Wiesbaden, Mainz, Darmstadt, Hanau und weitere). Fuer Local-SEO-Tests unbrauchbar.
8. 12 CSS-Token werden nie per `var()` genutzt, 8 Token sind wertgleich, 3 Farben sind ausserhalb `:root` hartkodiert (`#ffffff` in `.btn-primary`, zwei `rgba()` in `.card-trust` und `.hero`). Bei einem Kunden mit hellem Corporate Design bleiben diese Werte stehen.
9. `author` im Schema hat einen `default`, aber keine Wertebeschraenkung. Wenn die Autorenschaft maschinell gelten soll, braucht das Feld `const`.
10. `prompts/4a-...:41` fordert die Bestaetigung von "6 Kennzahlen", die Liste darueber enthaelt 6 Bulletpoints mit 10 Einzelwerten.
11. Widerspruechliche Mengenangaben: "mindestens 3 bis 8 Core Pillars" und "mindestens 25 bis 40 Cluster-Ideen" mischen Mindestwert und Spanne, die Obergrenze 15 Cluster aus dem Vertrag fehlt in der Validierungsregel von Prompt 1.
12. 3b sichert in der Validierungsregel nur die Obergrenze 15.0h ab, im Instruktionstext stehen 10 bis 15.
13. Mehrere als `required_file` deklarierte Inputs werden nicht geprueft: `manifest.json` in 1b und 1c, `outputs/1b-seitenarchitektur.md` in 1c, `outputs/3-plan.md` in 3b. 1c weicht die Screenshot-Pflicht zusaetzlich auf ("oder ein im Chat hochgeladener Screenshot").

---

## 6. Empfohlene Fix-Reihenfolge

**Paket 1: Fail-Fast wirklich implementieren (B1, B2, B3, H2, H3, H4).** Solver: Backlog-Sektion, `hours_min` durchsetzen oder Garantie-Satz nur bei Beweis, `ERROR_DATA_INCOMPLETE` statt Nullen, Exit-Codes ungleich 0 bei fehlendem Argument und unbekannter Struktur. Validator: CLI, Array-Support, Blockweise Fehlermeldung, Warnung bei nicht abgedeckten Typen. Prompt 4a und Prompt 0: benannte Fehlercodes. Das ist der Kern, alles andere ist Kosmetik dagegen.

**Paket 2: Pfad-Vereinheitlichung (B4).** Acht Fundstellen plus zwei MCP-Roots. Klein, mechanisch, aber blockiert den Pilotlauf.

**Paket 3: Datenvertrag schliessen (H6, H8, H9, H14, Mittel 5 bis 8, 14, 16, 19).** Ein Spaltensatz fuer `3-plan.md`, `region` und `word_count` im Frontmatter, `additionalProperties: false` und `status` als required im Schema, Prompt 0 um die vom Schema geforderten Felder erweitern, Fixtures synchronisieren, ein Slug-Schema pro Dateityp.

**Paket 4: Doku auf Wahrheit ziehen (H1, H10, H11, H12, Mittel 1 bis 4, 11, 12, 26).** Testprotokoll mit echtem Lauf neu schreiben, Abnahme-Checkliste auf offen zuruecksetzen, 1.2.0 im Changelog, "verifiziert" durch "synthetisch" ersetzen, Config-Template und Handbuch auf eine funktionierende Form bringen.

**Paket 5: Sequenz und Gates (H7, Mittel 10).** Position von 3b festlegen (Empfehlung: `next_step` von Schritt 3 auf 4a, 3b als zeitversetzte Schleife nach 4b mit eigenem Gate), eine Gate-ID-Systematik, 3b im Handbuch ergaenzen.

**Paket 6: Design-System vervollstaendigen (H13).** Breakpoints plus NAP-Box, Breadcrumb, Sticky-CTA, Vergleichstabelle, Akkordeon, Testimonial als Token-basierte Komponenten.

Ein Testrunner (pytest plus die 5 Akzeptanztests als Code) haette H1, H10 und B3 vor dem Release gefunden. Empfehlung: Paket 1 und ein minimaler Runner zusammen.

---

## 7. Nachweisbar sauber

- **Typografie-Regel eingehalten.** Suche ueber alle Dateien nach U+2014, U+2013, U+2012, U+2015, U+2212 und U+FF0D: null Treffer, auch im dekomprimierten Content-Stream des Memo-PDF. Die zwei Fundstellen in `AGENTS.md:52` und `PROJECT_STATE.md:75` sind die regel-erklaerenden Zeilen selbst.
- **Autorenschaft durchgaengig Raphael Rechberger** in allen Markdown-Dateien, allen Prompt-Metadaten, beiden MCP-Tools und allen Commits. Einzige Luecke: `scripts/generate_sample_keywords.py`.
- **`sample_manifest.json` validiert mit 0 Fehlern** gegen das Schema, und das Schema ist selbst valides Draft 2020-12 (`check_schema` bestanden). TEST-01 ist reproduzierbar und korrekt.
- **100 Prozent Pflichtabdeckung bestaetigt:** 26 von 26 Items mit `Is_Mandatory_Location = true` werden verplant, alle in Phase 1 und 2. Keine Auslassung.
- **Wochenobergrenze wird gehalten,** keine aktive Woche ueber 15.0h, im Referenzlauf auch keine unter 12.0h. Die Zwischensummen (59.5 + 52.0 + 12.0 = 123.5h) stimmen exakt, keine Rundungsfehler.
- **Score-Formel und Aufwandsgewichte** stimmen zwischen Prompt 3, Solver, `docs/01:55` und `docs/02:145` ueberein (8.0 / 3.0 / 1.25 / 1.0, Relevanzfaktoren 4/3/2/2/1).
- **Sequenzkette geschlossen,** jede `previous_step`- und `next_step`-Verkettung loest auf, nur die Position von 3b ist strittig.
- **Manifest-Phasenschluessel** aller Prompts existieren im Schema.
- **36 relative Links in `README.md`** loesen auf existierende Dateien auf, ebenso alle Referenzen in `docs/`, mit der einen Ausnahme aus Mittel 4.
- **Der Revert der Cockpit-UI ist sauber,** keine Doku-Stelle nennt noch `ui/` oder das Cockpit.
- **`design-system.css` ist autark und widerspruchsfrei:** kein `@import`, kein `url()`, keine externen Fonts, keine Dubletten, keine undefinierte `var()`-Referenz.
- **4a-Frontmatter und Copywriter-Guidelines** sind zeichengenau feldgleich (10 Keys, gleiche Reihenfolge, gleiche Beispielwerte), inklusive Ausgabepfad und Statuswerten.
- **Alle drei Tool-Vertraege** referenzieren real existierende AgentSEO-Endpunkte und sind valides JSON.
- **Zahlenkonsistenz sonst in Ordnung:** 9 Prompts in allen 6 Inventarlisten, 5 Akzeptanztests, 45 AgentSEO-Endpunkte, 7 Quality Gates in Memo und `docs/05`, Datum 16.08.2026 ohne Widerspruch zur Commit-Historie.

---

## 8. Offene Entscheidungen fuer Raphael

1. **17 Wochen:** Algorithmus auf Verteilung ueber alle 17 Wochen umbauen, oder Doku auf "Planungshorizont 17 Wochen, aktive Wochen datenabhaengig" umstellen? Das entscheidet, ob H1 ein Code- oder ein Doku-Fix ist.
2. **Position von 3b:** zeitversetzte Schleife nach 4b (fachlich korrekt) oder formal zwischen 3 und 4a (wie die Prompt-Metadaten sagen)?
3. **MCP-Root:** ein Root auf `Projekte` (deckt Framework und Kunden ab, gibt dem Modell aber Zugriff auf alle Projekte) oder zwei explizite Roots?
4. **Abnahme-Checkliste:** auf offen zuruecksetzen, oder als Freigabe des Frameworks (nicht des Pilotlaufs) umformulieren?
