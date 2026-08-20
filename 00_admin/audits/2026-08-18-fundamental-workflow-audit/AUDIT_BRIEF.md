# Fundamental Heartweb Workflow Audit Brief

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Auditmodus: Read-only fuer bestehende Source-Dateien
- Repository: `/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow`
- Reale Use-Case-Matrix: `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md`

## Auftrag

Auditiere das gesamte Repository und den Workflow fundamental gegen den realen Heartweb-Einsatz. Beurteile nicht nur, ob Dateien vorhanden sind oder Tests gruen werden. Beurteile, ob die Architektur alle realen Kundentypen professionell, reproduzierbar, internationalisierbar, automatisierbar und mit konsistent hoher Endergebnisqualitaet abbildet.

## Zielbild

Die Zielruntime ist nicht Claude Desktop und nicht OpenCode OMO.

- Eine eigene UI startet, genehmigt und ueberwacht Workflows.
- n8n orchestriert den automatisierten Workflow und die Provideraufrufe.
- Notion ist das zentrale operative Steuerelement fuer Kunden, Assessments, Phasen, Freigaben, Outputs und Aufgabenverteilung.
- Das Repository liefert die fachliche Domainlogik, Datenvertraege, Promptvertraege, deterministische Tools, Validierungen und Qualitaetsgates.
- OpenCode OMO bleibt Entwicklungs-, Audit- und Review-Werkzeug fuer Raphael und Hermes.
- PostgreSQL wird nicht als neue zentrale Source of Truth vorausgesetzt.
- DataForSEO ist bevorzugte Rohdatenquelle fuer Keywords, Labs, SERPs und skalierbare Abfragen.
- AgentSEO wird selektiv eingesetzt, wenn sein semantischer Mehrwert die Kosten rechtfertigt.
- Keine Integration darf Hermes-spezifisch sein.

## Nicht verhandelbare Regeln

1. Autor aller Artefakte ist Raphael Rechberger.
2. Keine Em-Dashes oder En-Dashes.
3. Keine Source-Datei veraendern.
4. Keine Commits, Pushes, Deployments oder Providerkosten erzeugen.
5. Keine Credentials lesen oder ausgeben.
6. Keine gruenen Tests mit Produktionsreife gleichsetzen.
7. Fakten, Interpretation und Empfehlung strikt trennen.
8. Jeder Befund benoetigt mindestens eine konkrete Datei- oder Codeevidenz, bevorzugt mit Zeile.
9. Widersprueche zwischen README, PROJECT_STATE, CHANGELOG, Prompts, Schema und Tests explizit erfassen.
10. Lokale uncommitted Aenderungen sind Kandidatenstand und muessen getrennt vom Git-Baseline-Stand beurteilt werden.

## Verbindliche Auditdimensionen

### A. Use-Case-Fit

- lokale, regionale, nationale und internationale Projekte
- ein oder mehrere Zielmaerkte
- ein oder mehrere Sprachen
- Leistungsort versus Suchmarkt versus Suchregion
- Marktphasen und Expansion
- B2B, B2C, Travel, YMYL Medizin, Pflege, Finanzen, sensible Themen
- langsame Skalierung versus Programmatic Local
- mehrere Domains, Satelliten, Marken und GBPs
- SEO versus Recruiting, OTA, Social, PR und weitere Nebenworkstreams

### B. Workflow und State Machine

- Sequenz 0, 1, 1b, 1c, 2, 3, 4a, 4b und 3b
- explizite Inputs, Outputs, Preconditions und Postconditions pro Schritt
- Human Gates und maschinelle Gates
- State-Uebergaenge und erlaubte Statuswerte
- Resume, Retry, Idempotenz, Versionierung und Rollback
- konsolidierte Operatornachrichten
- Fehlerschemata und Remediation

### C. Datenmodell und Vertraege

- `manifest.schema.json`
- internationale Geo- und Sprachmodellierung
- Entities, Wikidata, Evidence und GEO
- Mengenregeln
- zusaetzliche Properties
- Outputvertraege und Dateinamen
- Notion-Kompatibilitaet versus echte Notion-Datenbankstruktur
- Schema-Migration und Backward Compatibility

### D. Prompt- und Agentenarchitektur

- deterministisch erzwingbare Regeln versus reine Prompt-Hoffnung
- Halluzinations- und Klassifikationsrisiken
- Trennung von Research, Entscheidung, Generierung und Verifikation
- Modellrollen und Review-Unabhaengigkeit
- Promptgroesse, Wiederholungen und widerspruechliche Instruktionen
- Portabilitaet von Claude Desktop zu n8n und API-Workern

### E. Tools und Provider

- DataForSEO versus AgentSEO-Aufgabenteilung
- Geo-Validierung
- asynchrone Jobs
- Fehler, Retries, Timeouts und Kostenkontrolle
- Ahrefs, Screaming Frog, GSC, GBP und Analytics als Verifikationsquellen
- Providerabstraktion und transportneutraler Gateway
- keine stillen Fallbacks

### F. Implementierung und Tests

- Solver, JSON-LD-Validator und Gateway-Code
- Unit-, Contract-, Integration-, Live- und Acceptance-Tests
- Testtiefe und False-Green-Risiko
- synthetische Fixtures versus reale Briefings
- Scheinvaliditaet versus semantische Invaliditaet
- Regressionen ueber alle neun Schritte
- Dokumentationsdrift

### G. Endergebnisqualitaet

- Pillar- und Clusterstrategie
- Suchintention und Kannibalisierung
- Seitenarchitektur
- Designsystem und HTML
- Notion-Briefings fuer Copywriter
- Schema.org und GEO-Evidenz
- lokale Landingpages
- YMYL- und Compliance-Qualitaet
- technische Umsetzbarkeit in WordPress und Elementor
- Messbarkeit und Performance-Loop

### H. n8n, Notion und UI-Zielarchitektur

- fachliche State Machine in n8n
- Mandantenisolation
- Credentials und Least Privilege
- Queueing, Concurrency, Rate Limits und Kostenbudgets
- Webhooks, Subworkflows, Idempotency Keys und Run IDs
- Human Approval in UI und Notion
- Notion als zentrale Steuerung ohne Race Conditions
- Artefaktspeicher und Dateipfade
- Observability, Audit Log, Retry, Dead Letter und Recovery
- Migration weg von Claude Desktop

## Severity

- P0: Gefahr falscher Kundenoutputs, Datenverlust, Compliance-Verstoss oder nicht kontrollierbare Produktion.
- P1: blockiert professionelle Automatisierung oder reproduzierbare Qualitaet.
- P2: relevante Qualitaets-, Wartungs- oder Kostenschwaeche.
- P3: Dokumentation, Ergonomie oder spaetere Optimierung.

## Pflichtformat jedes Teilreports

1. Executive Verdict
2. Scope und gelesene Evidenz
3. Was wirklich stark ist
4. Befunde nach P0 bis P3
5. Widersprueche und False-Green-Risiken
6. Sollarchitektur beziehungsweise Korrekturempfehlung
7. Maschinenpruefbare Acceptance Criteria
8. Go, Conditional Go oder No-Go
9. Exakte Dateien, Tests und naechste Fix-Reihenfolge

## Ausgabedateien

- `00_admin/audits/2026-08-18-fundamental-workflow-audit/01_DOMAIN_AND_PROMPT_AUDIT.md`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/02_IMPLEMENTATION_AND_TEST_AUDIT.md`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/03_N8N_NOTION_UI_ARCHITECTURE_AUDIT.md`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/04_TRACEABILITY_OUTPUT_REDTEAM_AUDIT.md`

Der finale Masterreport wird erst nach unabhaengiger Hermes-Sol-Verifikation erstellt.
