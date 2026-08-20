# Lane 3: n8n, Notion und UI Architektur Audit

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Auditmodus: Read-only-Pruefung bestehender Source-Dateien und Architekturplaene
- Zielruntime: Eigene UI, n8n und Notion

## 1. Executive Verdict

**No-Go fuer Deployment und produktive Kundenlaeufe.** Das Zielbild ist fachlich sinnvoll: Die eigene UI soll Bedienoberflaeche sein, n8n soll orchestrieren, Notion soll das zentrale operative Steuerelement bilden und das Repository soll die versionierte Domainlogik liefern. Diese Rollentrennung ist im Migrationsplan klar beschrieben (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:20-31`, `:63-104`). Der vorliegende Stand ist jedoch ein vorgeschlagener Plan, keine deploybare Architektur. Der Plan ist selbst mit `status: proposed` und `mode: plan-only` markiert (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:5-6`).

Die Produktionsblocker liegen an den Systemgrenzen. Es gibt keinen kanonischen, atomar durchsetzbaren Zustandsvertrag fuer UI, Notion und n8n, keine nachgewiesene Mandanten- und Credential-Isolation, keine Idempotenz- und Revisionslogik, keine Queue- und Kostensteuerung, keinen festgelegten Artefaktspeicher und keinen nachgewiesenen Retry-, Dead-Letter- oder Recovery-Pfad. Gerade Notion-Webhooks sind laut offizieller Evidenz verspaetet, aggregiert und nicht geordnet. Ohne erneutes Lesen, Deduplizierung und Compare-and-Swap koennen Freigaben und Status ueberschrieben oder doppelt verarbeitet werden (`00_admin/audits/2026-08-18-fundamental-workflow-audit/OFFICIAL_PLATFORM_EVIDENCE.md:63-72`).

Die Architektur passt in ihrer aktuellen Form auch nicht zu den zehn realen Kundenfaellen. Diese verlangen mehrere Maerkte, Sprachen, Phasen, Domains, Marken, GBPs, Workstreams und regulatorische Regeln (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:10-34`). Das aktuelle Manifest fuehrt dagegen genau ein `country`, einen `location_code` und eine `language` (`standards/manifest.schema.json:142-145`, `:617-630`). Eine UI oder Notion-Datenbank kann dieses fehlende Domainmodell nicht durch zusaetzliche Ansichten reparieren.

## 2. Scope und gelesene Evidenz

### 2.1 Primaerevidenz

- `AGENTS.md:10-28`, `:49-73`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/AUDIT_BRIEF.md:9-147`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/HOST_GIT_BASELINE.md:7-39`
- `00_admin/audits/2026-08-18-fundamental-workflow-audit/OFFICIAL_PLATFORM_EVIDENCE.md:7-97`
- `.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:1-875`
- `docs/04-entscheidungslog.md:26-123`
- `docs/05-human-in-the-loop.md:22-120`
- `standards/manifest.schema.json:1-722`
- `standards/dateinamen-und-output-vertrag.md:10-68`
- `prompts/0-kickoff.xml.md:86-140`
- `prompts/4a-content-briefing-und-schema.xml.md:60-121`
- `services/agentseo_gateway/core.py:24-446`
- `03_research/provider-strategy-2026-08-18/worker_synthesis.md:6-51`
- `00_admin/PROJECT_STATE.md:26-100`
- `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:1-49`

### 2.2 Baselinebehandlung und Aussagegrenze

Als alleinige Baseline-Evidenz gilt `HOST_GIT_BASELINE.md`. Danach entspricht `master` dem Host-Stand bei Commit `5e78679` (`HOST_GIT_BASELINE.md:7-10`). Der Migrationsplan unter `.hermes/` und der Gateway unter `services/` gehoeren zu den vor dem Audit vorhandenen untracked Kandidatenbereichen (`HOST_GIT_BASELINE.md:21-29`). Sie werden deshalb als Kandidatenstand und nicht als ausgelieferter Produktionsnachweis bewertet. Container-Git-Metadaten sind ausdruecklich unzulaessig (`HOST_GIT_BASELINE.md:35-39`).

Es wurden auftragsgemaess keine Provider-, Netzwerk-, Deployment-, Credential-, Browser-, Test-, Build- oder Git-Operationen ausgefuehrt. Dieser Bericht bewertet Vertrags- und Dateievidenz. Er behauptet keine Laufzeiteigenschaft aufgrund gruen gemeldeter Tests.

### 2.3 Abdeckung der realen Kundenfaelle

| Use-Case-Gruppe | Erforderliche Runtime-Faehigkeit | Auditbewertung |
|---|---|---|
| AHD, Pflegedienst Sauerlach, LS Wohntraum | Physischer Ort, Leistungsgebiet und Suchregion getrennt; langsame Skalierung; Recruiting separat | Nicht vertraglich abbildbar. Die Matrix warnt explizit, dass ein Zielgebiet keinen physischen Standort beweist (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:12`, `:18`, `:20`, `:36-45`). |
| Ayurveda Shunyata Villa, Daniela Landgraf, Epargne Plurielle, Shunyata Villas Bali | Mehrere Maerkte, Sprachen, Jurisdiktionen und zeitliche Expansionsphasen | Nicht vertraglich abbildbar. Das Manifest besitzt nur skalare Markt- und Sprachfelder (`standards/manifest.schema.json:131-145`, `:617-630`). |
| CL Performance | Nationales B2B ohne Local-SEO-Fehlklassifikation; CAD-Datenschutz; Upload und Quote | Kein Archetyp-, Conversion-, Datenschutz- oder Upload-Artefaktvertrag. Der reale Bedarf steht in `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:14`. |
| Holistic Tantra | Sensible Sprache, Video-zu-Artikel, getrennte Intent-Stufen | Kein markt- und workstreambezogener Claims- oder Medienprozessvertrag. Der reale Bedarf steht in `/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:17`. |
| MobilePhysiotherapie24 | Programmatic Local, Satellitendomains, Marken, GBPs, Recruiting und PR | Keine Entity- und Workspace-Hierarchie fuer diese Skalierung. Die Matrix nennt dies ausdruecklich als Schema-Risiko (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:19`, `:42-45`). |

## 3. Was wirklich stark ist

1. **Klare Rollenabsicht:** UI, n8n, Notion, Artefaktspeicher und fachliche Repository-Logik werden als unterschiedliche Komponenten benannt (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:20-31`, `:145-176`). Das verhindert konzeptionell eine Hermes- oder OpenCode-spezifische Produktionsruntime.
2. **Notion wird nicht als Blob-Speicher missverstanden:** Der Plan legt grosse Briefings, CSVs, HTMLs und Logs in einen Artefaktspeicher und nur Steuerdaten sowie Links in Notion (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:217-242`). Das entspricht der offiziellen Plattformfolgerung (`OFFICIAL_PLATFORM_EVIDENCE.md:86-97`).
3. **Human Gates sind fachlich sichtbar:** Der vorhandene Workflow benennt sieben fachliche Kontrollpunkte vom Strategieentscheid bis zum Performance-Review (`docs/05-human-in-the-loop.md:22-39`). Der Migrationsplan sieht Freigabe und Ablehnung in UI und Notion vor (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:63-82`, `:579-596`).
4. **Fail-fast und Fehlertransparenz sind richtige Leitlinien:** Der Plan verlangt Fehlercode, Remediation, Verantwortlichen und kontrollierten Retry statt stillem Fallback (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:544-556`). Der AgentSEO-Kandidat behandelt fehlende Job-ID, Providerfehler und Timeout explizit (`services/agentseo_gateway/core.py:355-398`).
5. **Providerstrategie ist fachlich weiter als der alte Desktop-Pfad:** Die Recherche empfiehlt DataForSEO als Raw-first-Quelle und AgentSEO nur fuer selektive semantische Mehrwerte (`03_research/provider-strategy-2026-08-18/worker_synthesis.md:24-45`). Das passt zum Zielbild des Audit-Briefs (`AUDIT_BRIEF.md:20-25`).
6. **Die Abschaltung von Claude Desktop ist an einen echten Pilot geknuepft:** Der Plan verlangt alle neun Schritte, funktionierende Gates, vollstaendige Artefakte, einen echten Kundenpilot und getesteten Rollback (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:730-742`). Das ist die richtige Abnahmelogik.

## 4. Befunde nach P0 bis P3

Die Liste ist innerhalb jeder Severity nach Risiko priorisiert.

### P0

#### P0-1: Kein atomarer Kontrollzustand zwischen Notion, UI und n8n

**Fakt:** Der Plan sagt, dass UI und Notion denselben zentralen Notion-Zustand schreiben und Statuswechsel n8n starten koennen (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:59-82`). Das vorgeschlagene Projektmodell enthaelt zwar `Run-ID` und `Status`, aber keine Revision, keinen erwarteten Vorzustand, keinen Event-Offset und keinen Compare-and-Swap-Wert (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:285-322`). Notion-Events koennen verspaetet, aggregiert oder ungeordnet eintreffen und muessen nach Event-ID dedupliziert sowie durch erneutes API-Lesen reconciliert werden (`OFFICIAL_PLATFORM_EVIDENCE.md:63-72`).

**Interpretation:** Zwei nahezu gleichzeitige Freigaben, ein wiederholtes Webhook-Event oder ein UI-Retry koennen denselben Schritt doppelt starten, eine Ablehnung ueberschreiben oder einen alten Stand als neuen akzeptieren. Notion kann operative Steuerzentrale sein, aber nicht alleiniger transaktionaler Execution-State. n8n braucht seine eigene Execution-Datenbank, ohne dass damit eine neue fachliche PostgreSQL-Source-of-Truth fuer Kundendaten eingefuehrt wird (`OFFICIAL_PLATFORM_EVIDENCE.md:86-93`).

**Empfehlung:** Jede Mutation muss ueber genau einen Command-Endpunkt laufen. Der Command enthaelt `tenant_id`, `project_id`, `step_id`, `expected_revision`, `command_id`, `actor_id`, `decision`, `run_id` und `occurred_at`. n8n akzeptiert die Transition nur bei passender Revision, schreibt ein unveraenderliches Audit-Event, aktualisiert Notion und gibt die neue Revision zurueck. Notion-Webhooks sind nur Signale und nie die vollstaendige Mutation.

#### P0-2: Mandantenisolation, Rollenmodell und Credential-Grenzen sind nicht spezifiziert

**Fakt:** Die reale Matrix verlangt Mandantenisolation (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:23-34`). Der Plan nennt Kunden-ID, Projekt-ID und UI-Authentifizierung, laesst Hosting, Authentifizierung, Benutzerzuordnung und Credential-Betrieb jedoch offen (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:744-783`). Die heutige Dateistruktur isoliert Kunden lediglich durch einen lokalen Ordner (`AGENTS.md:19-28`). Fuer n8n Queue Mode muessen alle Worker denselben Encryption Key besitzen und Binaerdaten eine gemeinsame Storage-Strategie haben (`OFFICIAL_PLATFORM_EVIDENCE.md:39-48`).

**Interpretation:** Ein falscher Notion-Page-Identifier, ein globales n8n-Credential oder ein ungescopter Artefaktpfad kann Daten und Providerzugriffe zwischen Kunden vermischen. Bei Medizin-, Pflege-, Finanz- und sensiblen Kunden ist dies ein Compliance- und Vertraulichkeitsrisiko. Ein gemeinsamer n8n-Encryption-Key ist betriebsnotwendig, ersetzt aber keine tenantbezogene Autorisierung.

**Empfehlung:** Definiere ein verpflichtendes Tenant- und RBAC-Modell. Jeder Run, Credential-Alias, Notion-Datensatz, Providerjob und Artefakt-Key traegt `tenant_id`. UI-Rollen werden auf konkrete Actions abgebildet. Worker erhalten nur referenzierte Secret-Aliase, niemals Secrets im Manifest, Notion oder Log. Artefaktzugriffe verwenden tenantgebundene, kurzlebige URLs. Cross-Tenant-IDs werden vor jedem I/O abgelehnt.

#### P0-3: Human Approval kann derzeit nicht revisionssicher und einmalig bewiesen werden

**Fakt:** Gate 0 kennt nur Status, Reviewer, Zeit und Warnungen (`standards/manifest.schema.json:238-278`). Fuer die uebrigen Schritte enthaelt das Manifest keine Gate-Objekte, keine Entscheidungs-ID und keine Bindung an einen Artefakt-Hash (`standards/manifest.schema.json:326-581`). Der Plan nennt zwar Freigeber und Zeitpunkt fuer Workflow-Schritte (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:304-322`), aber keine Signatur der geprueften Artefaktversion. Wait-Resume benoetigt authentifizierte Resume-URLs, Timeout und einen definierten Timeout-Pfad (`OFFICIAL_PLATFORM_EVIDENCE.md:28-37`).

**Interpretation:** Eine Freigabe kann auf Output Version A erfolgen, waehrend ein Retry Version B unter demselben Link erzeugt. Ein alter Resume-Link kann einen neuen Lauf fortsetzen. Damit ist die behauptete Human-in-the-Loop-Kontrolle fuer YMYL, Finanzen, lokale Standortclaims und sensible Inhalte nicht revisionssicher.

**Empfehlung:** Eine Approval-Entscheidung muss unveraenderlich an `gate_id`, `run_id`, `artifact_id`, `sha256`, `policy_version`, `reviewer_id`, `decision`, `reason`, `decided_at` und `expires_at` gebunden sein. Jede neue Artefaktversion invalidiert eine offene Freigabe. Resume-Tokens sind einmalig, kurzlebig, authentifiziert und an genau diese Gate-Revision gebunden. UI und Notion verwenden denselben Approval-Command.

#### P0-4: Das Domainmodell kann die Zielruntime fuer reale Kunden nicht sicher versorgen

**Fakt:** Die Matrix fordert beliebig viele Zielmaerkte und Sprachen sowie getrennte Marken, Leistungsorte, Suchregionen, Domains, GBPs und Marktphasen (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:23-34`, `:36-45`). Das Manifest verlangt skalare Felder fuer `country`, `location_code` und `language` (`standards/manifest.schema.json:6-32`, `:142-145`, `:617-630`). Der Migrationsplan erkennt selbst, dass internationale und mehrsprachige Projekte nicht in dieses Single-Country-Modell passen (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:614-640`).

**Interpretation:** Selbst eine technisch perfekte n8n-Orchestrierung wuerde fuer Ayurveda Shunyata Villa, Epargne Plurielle, Daniela Landgraf, MobilePhysiotherapie24 und Shunyata Villas Bali entweder falsche Daten oder manuelle Sonderlogik erzeugen. UI-Felder und Notion-Properties koennen einen unzureichenden kanonischen Vertrag nicht kompensieren.

**Empfehlung:** Vor Runtime-Bau einen versionierten Domainvertrag fuer Tenant, Kunde, Marke, Domain, physische Entitaet, Leistungsgebiet, Search Deployment, Markt, Sprache und Locale, Jurisdiktion, Phase, GBP und Workstream erstellen. n8n und Notion duerfen nur IDs dieses Vertrags transportieren, nicht eigene Interpretationen der Kundengeografie.

### P1

#### P1-1: Es existiert kein deploybarer n8n-, Notion- oder UI-Vertrag

**Fakt:** Der Migrationsplan ist `plan-only` (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:1-9`) und sagt ausdruecklich: Kein Build vor Aufnahme des realen Notion-Prozesses (`:642-677`). Zentrale Entscheidungen zu vorhandenen Datenbanken, Properties, Triggern, Hosting, Artefaktspeicher und Authentifizierung sind offen (`:744-759`). Die Host-Baseline fuehrt `.hermes/` und `services/` nur als untracked Kandidatenbereiche (`HOST_GIT_BASELINE.md:21-29`).

**Interpretation:** Die benannten Workflows WF-00 bis WF-99 sind Beschreibungen, keine importierbaren und versionierten n8n-Workflows. Ebenso fehlen ein Notion-Property-Mapping, ein UI-API-Vertrag und eine deploybare Runtime. Ein Deploymentverdict kann nicht auf Architekturprosa gestuetzt werden.

**Empfehlung:** Nach Abschluss der Notion-Aufnahme zuerst Contracts und einen vertikalen Pilot erstellen. Workflow-Exporte, Subworkflow-Inputs, Credentials, Error Workflows und Deployments werden versioniert. UI und Notion greifen ausschliesslich ueber die definierte API beziehungsweise Commands auf den Prozess zu.

#### P1-2: Run-ID und Idempotenz sind benannt, aber nicht durchsetzbar

**Fakt:** Der Plan verlangt fuer jeden Schritt eine eindeutige Run-ID (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:114-125`) und nennt eindeutige Run- und Task-IDs im Rollback (`:854-863`). Der AgentSEO-Kandidat startet jedoch bei jedem Aufruf ein neues POST und persistiert weder Idempotency-Key noch Request-Hash (`services/agentseo_gateway/core.py:355-376`). Die Provider-Job-ID erscheint erst im Rueckgabeobjekt (`services/agentseo_gateway/core.py:400-445`).

**Interpretation:** UI-Retry, n8n-Retry, Webhook-Duplikat und Worker-Neustart koennen jeweils einen neuen kostenpflichtigen Providerjob oder doppelte Notion-Tasks erzeugen. Eine sichtbare Run-ID allein macht den Seiteneffekt nicht idempotent.

**Empfehlung:** Definiere je Seiteneffekt einen stabilen Key, zum Beispiel `tenant_id:project_id:step_id:input_hash:operation`. Vor jedem Provider-POST, Notion-Write, Artefakt-Write oder Task-Create wird das Idempotenzregister gelesen. Wiederholung liefert das bestehende Ergebnis oder setzt den bestehenden Providerjob fort. Run-ID bezeichnet eine Ausfuehrung, Idempotency-Key eine fachliche Operation.

#### P1-3: Queueing, Concurrency, Rate Limits und Kostenbudgets fehlen als Betriebsvertrag

**Fakt:** Self-hosted n8n hat ohne explizite Konfiguration unbegrenzte Production-Concurrency. Das normale Limit deckt Manual Runs, Subworkflows, Error Workflows und CLI-Runs nicht automatisch ab (`OFFICIAL_PLATFORM_EVIDENCE.md:9-17`). Notion erlaubt im Mittel drei Requests pro Sekunde pro Connection und verlangt fuer 429/529 `Retry-After`, Backoff, Jitter und ein Retry-Limit (`OFFICIAL_PLATFORM_EVIDENCE.md:49-61`). Der Migrationsplan beschreibt Provideraufrufe und Polling, nennt aber weder per-Tenant-Queue, globale Limits, Kostenreservierung noch Budgetabbruch (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:433-556`).

**Interpretation:** Programmatic Local fuer MobilePhysiotherapie24 kann langsame regionale Kunden verdraengen, Notion ueberlasten und Providerkosten vervielfachen. Manual- oder Subworkflow-Runs koennen ein globales n8n-Limit umgehen. Ein harter AgentSEO-Plan oder DataForSEO-Pay-as-you-go benoetigt unterschiedliche Budgetregeln.

**Empfehlung:** Fuehre getrennte Queues fuer Notion Writes, Provider, LLM, Tool Runner und Artefakte ein. Setze globale, per-Tenant-, per-Provider- und per-Operation-Concurrency. Reserviere vor Dispatch ein Kostenbudget, verbuche Ist-Kosten und stoppe bei `budget_remaining < worst_case_cost`. Notion-Retries beachten `Retry-After`, Jitter und maximale Versuche. Manual Runs nutzen dieselben Guards.

#### P1-4: Artefaktspeicher, Pfade, Versionierung und Integritaet sind offen

**Fakt:** Der aktuelle Outputvertrag setzt lokale relative Kundenpfade (`standards/dateinamen-und-output-vertrag.md:10-40`, `:44-56`). Der Migrationsplan nennt einen Remote-Artefaktraum, legt dessen Technologie aber nicht fest (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:451-465`, `:744-755`). n8n Queue Mode benoetigt fuer Binaerdaten gemeinsamen Storage, bevorzugt S3 oder Azure (`OFFICIAL_PLATFORM_EVIDENCE.md:39-48`).

**Interpretation:** Lokale Workerpfade funktionieren nicht bei mehreren n8n-Workern. Gleichnamige Dateien, 3b-Ueberschreibung von `outputs/3-plan.md` und parallele Runs koennen Daten verlieren. Ein Notion-Link ohne Hash und Version beweist nicht, welcher Output freigegeben wurde.

**Empfehlung:** Nutze einen abstrakten Object-Store-Vertrag mit unveraenderlichen Keys: `tenants/<tenant_id>/projects/<project_id>/runs/<run_id>/artifacts/<artifact_id>/<filename>`. Jede Version erhaelt Content-Type, Groesse, SHA-256, Schema-Version, Erzeuger, Quellartefakte und Retention-Klasse. Kanonische Pfade sind Aliase auf freigegebene Versionen, keine ueberschreibbaren Originale.

#### P1-5: Observability, Audit Log, Retry, DLQ und Recovery sind nur als Wunsch beschrieben

**Fakt:** Der Plan beschreibt einen Error Handler mit Notion-Eintrag, Blocker und Retry-Option (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:544-556`). Offizielle n8n-Evidenz erlaubt Error Workflows mit Execution-ID, Retry-Bezug und letzter Node (`OFFICIAL_PLATFORM_EVIDENCE.md:19-26`). Der Plan definiert aber weder Audit-Event-Schema, Korrelationsfelder, Retry-Klassen, DLQ-Datensatz, Alarm-Schwelle, Replay-Regel noch Restore-Test.

**Interpretation:** Ein Notion-Fehlereintrag ist keine belastbare Telemetrie. Wenn Notion selbst gestoert ist, kann der Error Handler seinen einzigen sichtbaren Fehlerkanal verlieren. Ohne DLQ und Replay-Schutz kann ein Operator einen nicht-idempotenten Schritt erneut ausloesen.

**Empfehlung:** Schreibe strukturierte Events ausserhalb des Notion-Write-Pfads mit `tenant_id`, `run_id`, `execution_id`, `step_id`, `operation_id`, `attempt`, `error_code`, `retry_class`, `provider_job_id` und Zeitstempeln. Trenne `retryable`, `blocked_by_input`, `policy_denied` und `terminal`. Nach maximalen Versuchen geht die Operation in eine DLQ. Replay benoetigt Actor, Grund, neue Run-ID und denselben Idempotency-Key.

#### P1-6: Claude-Desktop-Migration und Rollback erlauben einen unsicheren Mischbetrieb

**Fakt:** Der Plan will Schritte einzeln aktivieren und nicht migrierte Schritte weiter im bisherigen Prozess ausfuehren (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:854-863`). Der heutige Desktop-Zustand ist dateibasiert und liegt in lokalen Kundenordnern (`AGENTS.md:19-45`). Gleichzeitig soll Notion im Zielsystem den uebergeordneten Prozess steuern (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:217-242`).

**Interpretation:** Ohne Ownership-Lease und Reconciliation koennen Desktop und n8n denselben Manifest- oder Artefaktstand unabhaengig aendern. Der als Rollback gedachte Mischbetrieb erzeugt dann Split-Brain statt Sicherheit.

**Empfehlung:** Definiere pro Projekt und Schritt genau einen `execution_owner` mit Lease und Cutover-Zeitpunkt. Legacy-Schritte sind nach Cutover read-only. Vor Umschaltung werden Manifest, Artefakte, offene Gates und Providerjobs importiert und gehasht. Rollback ist eine getestete State-Transition mit Freeze, Export, Reconciliation und neuem Owner, kein paralleles Schreiben.

### P2

#### P2-1: Das Notion-Modell ist eine Feldliste, kein API- und Synchronisationsvertrag

**Fakt:** Der Plan listet Datenbanken und Pflichtfelder fuer Kunden, Assessments, Projekte, Schritte, Tasks, Access Requests und Fehler (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:244-370`). Notion-Properties muessen jedoch einem expliziten Data-Source-Schema entsprechen. YAML-Frontmatter erzeugt keine Notion-Properties und ist kein API-Vertrag (`OFFICIAL_PLATFORM_EVIDENCE.md:74-85`). Prompt 4a bezeichnet sein YAML dennoch als fuer Notion-Import ausgelegt (`prompts/4a-content-briefing-und-schema.xml.md:67-70`, `:81-102`).

**Interpretation:** Property-Typen, Relationsrichtung, stabile externe IDs, Select-Werte, Null-Semantik, Schema-Version und Migrationsregeln fehlen. Eine manuelle YAML-Uebergabe ist nicht identisch mit bidirektionaler operativer Steuerung.

**Empfehlung:** Lege fuer jede Data Source einen versionierten Vertrag mit Property-ID, Typ, Pflichtstatus, Enum, Relation, Owner, Schreibrichtung und Domainpfad an. Der Adapter mappt Property-IDs, nicht Anzeigenamen. Schema-Drift blockiert Writes und erzeugt einen technischen Blocker statt automatische Feldanlage.

#### P2-2: Die UI ist funktional beschrieben, aber Sicherheits- und Interaktionsvertraege fehlen

**Fakt:** Dashboard, Kundenansicht, Assessment, Workflow, Tasks und Error Center sind als Screens aufgezaehlt (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:558-613`). Authentifizierung und die Frage, ob Lesen direkt oder ueber einen Backend-Adapter erfolgt, sind offen (`:744-756`).

**Interpretation:** Es fehlen Autorisierung je Aktion, Session- und CSRF-Modell, Request-ID, Optimistic-Locking-UX, Doppelclick-Schutz, Upload-Limits, Dateityppruefung, barrierearme Fehlerdarstellung und sichere Artefaktlinks. Ein Button `erneut versuchen` ohne sichtbare Run- und Artefaktrevision ist betrieblich gefaehrlich.

**Empfehlung:** Definiere eine schmale Operations-API. Die UI liest Projektionen und sendet Commands mit `expected_revision` und `command_id`. Sie schreibt weder direkt in Notion noch startet sie beliebige n8n-Webhook-URLs. Jede destructive oder kostenpflichtige Aktion zeigt Tenant, Projekt, Schritt, Budgetwirkung und aktuelle Revision und verlangt serverseitige Autorisierung.

#### P2-3: Webhook- und Subworkflow-Vertraege sind nicht festgelegt

**Fakt:** Der Plan nennt Trigger aus UI und Notion sowie Subablaeufe WF-00 bis WF-99 (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:84-104`, `:433-556`). Offizielle Evidenz verlangt definierte Inputschemas fuer Subworkflows und bewertet `Accept all data` als unzureichend (`OFFICIAL_PLATFORM_EVIDENCE.md:86-97`). Notion-Webhook-Events enthalten nicht den vollstaendigen aktuellen Inhalt (`OFFICIAL_PLATFORM_EVIDENCE.md:63-72`).

**Interpretation:** Ohne signierten Envelope, Schema-Version und Dedupe-Key kann ein manipuliertes, altes oder unvollstaendiges Event den falschen Tenant oder Schritt ausloesen. Lose Subworkflow-Daten erzeugen stille Contract-Drift.

**Empfehlung:** Jeder externe Webhook prueft Signatur, Zeitfenster, Event-ID und Tenant-Bindung. Danach liest der Adapter den aktuellen Notion-Stand. Jeder Subworkflow akzeptiert ein geschlossenes JSON Schema mit `additionalProperties: false` und liefert einen versionierten Result-Envelope. Direkte Resume-URLs werden nie in Notion-Textfeldern oder Browserlogs gespeichert.

#### P2-4: DataForSEO-first und AgentSEO-selektiv sind im Migrationsplan noch nicht umgesetzt

**Fakt:** Der Audit-Brief setzt DataForSEO als bevorzugte Rohdatenquelle und AgentSEO selektiv (`AUDIT_BRIEF.md:20-25`). Die Providerrecherche bestaetigt Raw-first und getrennte Adapter (`03_research/provider-strategy-2026-08-18/worker_synthesis.md:24-45`). Der Migrationsplan beschreibt WF-03 dagegen ausschliesslich als AgentSEO Async Handler (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:488-496`).

**Interpretation:** Providerkosten, Rohdatenprovenienz und Skalierung waeren weiterhin an AgentSEO gekoppelt. Das trifft besonders Programmatic Local, internationale SERPs und wiederkehrende Performance-Loops.

**Empfehlung:** n8n ruft einen providerneutralen Research-Gateway auf. Der Request nennt Capability, Search Deployment, Device, Freshness, maximale Kosten und Raw-Payload-Policy. DataForSEO ist Default fuer Keywords, Labs und SERP-Rohdaten. AgentSEO wird nur nach expliziter Routingregel fuer semantische Mehrwerte zugeschaltet. Beide Antworten werden unveraendert gespeichert und gegen ein kanonisches Evidence-Schema normalisiert.

### P3

#### P3-1: Sequenz und Gate-Identitaeten sind dokumentarisch widerspruechlich

**Fakt:** Der Migrationsplan fuehrt `3b` innerhalb der linearen Sequenz vor `4a` (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:106-125`, `:467-486`). Das Betriebshandbuch fuer Gates beschreibt 3b als zeitversetzten Zyklus ab Tag 30 (`docs/05-human-in-the-loop.md:113-120`). AGENTS schreibt `3 -> (3b) -> 4a`, waehrend README 3b erst nach 4b zyklisch nennt (`AGENTS.md:49-58`, `README.md:188`).

**Interpretation:** n8n kann aus diesen Dokumenten keinen eindeutigen Graphen generieren. Unterschiedliche Gate-IDs in Prompt und Handbuch erhoehen die Gefahr falscher UI-Labels und Transitionen.

**Empfehlung:** Verwalte einen einzigen maschinenlesbaren Workflowgraphen. 3b ist ein wiederholbarer, zeitgesteuerter Seitenprozess nach Publikationsdatum und nicht Teil des initialen Pfads zu 4a. Anzeigenamen werden aus stabilen Step- und Gate-IDs generiert.

#### P3-2: Produktionsreife-Claims sind nicht mit dem Migrationsstatus vereinbar

**Fakt:** README bezeichnet den Desktop-Workflow als aktiven und validierten Produktionsstandard (`README.md:1-7`). `PROJECT_STATE.md` nennt Version 1.3.0 in Arbeit und eine Vorbereitung der GEO-Erweiterung (`00_admin/PROJECT_STATE.md:1-8`). Der Zielruntime-Plan bleibt `proposed` und `plan-only` (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:1-9`).

**Interpretation:** Stakeholder koennen Desktop-Prototyp, Kandidatenstand und Zielruntime faelschlich als denselben freigegebenen Release verstehen.

**Empfehlung:** Fuehre getrennte Reifegrade `legacy_reference`, `candidate`, `pilot` und `production` pro Runtime ein. Nur ein signiertes Release-Manifest darf Produktionsreife behaupten und muss Workflow-, Contract-, UI-, Notion- und Infrastrukturversionen referenzieren.

## 5. Widersprueche und False-Green-Risiken

| Aussage | Gegen-Evidenz | False-Green-Risiko |
|---|---|---|
| Notion ist zentrale Steuerung, also ist der Zustand eindeutig. | Notion-Webhooks sind nicht geordnet oder exakt einmalig (`OFFICIAL_PLATFORM_EVIDENCE.md:63-72`); Revision und CAS fehlen im Plan (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:285-322`). | Veraltete Freigabe oder doppelter Lauf sieht erfolgreich aus. |
| Eine Run-ID macht den Ablauf idempotent. | Der Gateway fuehrt bei jedem Aufruf ein neues Provider-POST aus (`services/agentseo_gateway/core.py:355-376`). | Doppelte Kosten und Ergebnisse unter mehreren Run-IDs. |
| n8n-Concurrency schuetzt alle Ausfuehrungen. | Das Production-Limit gilt nicht automatisch fuer Manual Runs, Subworkflows, Error Workflows oder CLI (`OFFICIAL_PLATFORM_EVIDENCE.md:9-17`). | Nebenpfade umgehen Last- und Kostenkontrolle. |
| Notion-Frontmatter ist Notion-kompatibel. | YAML erzeugt keine Data-Source-Properties (`OFFICIAL_PLATFORM_EVIDENCE.md:74-85`); Prompt 4a liefert nur einen YAML-Block (`prompts/4a-content-briefing-und-schema.xml.md:67-102`). | Manueller Import wird mit sicherer Synchronisation verwechselt. |
| `completed` bedeutet fachlich und menschlich freigegeben. | Phasen verlangen nur `status`; Gates 1 bis 7 sind nicht im Manifest gebunden (`standards/manifest.schema.json:326-581`). | Ungepruefte Kundenoutputs koennen nachgelagerte Tasks starten. |
| Lokale Ordner sichern Mandantenisolation. | Die Ordnerkonvention ist Desktop-spezifisch (`AGENTS.md:19-28`); Zielhosting und Artefaktspeicher sind offen (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:744-755`). | Worker- oder Linkfehler legen fremde Kundenartefakte offen. |
| Error Handler plus Retry bedeutet Recovery. | Der Plan definiert keine Retry-Klassen, DLQ, Replay- oder Restore-Regel (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:544-556`). | Nicht-idempotente Schritte werden blind wiederholt. |
| Die lineare Sequenz ist eindeutig. | 3b steht im Plan vor 4a, im Gate-Handbuch aber als spaeter Zyklus (`.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md:106-125`; `docs/05-human-in-the-loop.md:113-120`). | Scheduler und UI zeigen oder starten den falschen Schritt. |
| Ein erfolgreicher DE-Pilot beweist Kundenfit. | Die Matrix verlangt Cross-Border, Multi-Market, YMYL, B2B und Programmatic Local (`/workspace/heartweb-data/Workflow-Lab/_audit_inputs/2026-08-18-real-customer-use-case-matrix.md:10-34`). | Ein einfacher Fixture-Pfad maskiert strukturelle Nichtabdeckung. |

## 6. Sollarchitektur beziehungsweise Korrekturempfehlung

### 6.1 Verbindliche Systemrollen

1. **Notion Control Plane:** Notion fuehrt Kunden, Assessments, Projekte, fachliche Statusprojektionen, Gates, Tasks, Verantwortliche und Artefaktlinks. Es ist das zentrale operative Steuerelement fuer Menschen. Notion ist nicht der einzige transaktionale Execution-State.
2. **Operations API:** Eine schmale, Hermes-neutrale API authentifiziert UI-Akteure, validiert Commands, erzwingt Tenant und RBAC, prueft `expected_revision` und liefert Projektionen. Sie enthaelt keine Providerlogik.
3. **n8n Orchestrator:** n8n konsumiert versionierte Commands, fuehrt den kanonischen Workflowgraphen aus, nutzt Wait Gates, Error Workflows und getrennte Queues. Seine eigene Execution-Datenbank bleibt technische Runtime-Voraussetzung. Es wird keine neue fachliche PostgreSQL-Source-of-Truth fuer Kundendaten vorausgesetzt.
4. **Domain und Transition Service:** Das Repository liefert geschlossene Schemas und deterministische Validatoren fuer Domainobjekte, Zustandsuebergaenge, Gates, Artefakte, Providerjobs, Audit-Events und Policies. UI, n8n und Notion-Adapter duerfen Zustandsregeln nicht duplizieren.
5. **Provider Gateway:** DataForSEO, AgentSEO, LLM, GSC, GBP, Analytics und weitere Quellen liegen hinter capability-basierten Adaptern. Raw Payload, Kosten, Geo, Sprache, Device, Abrufzeit und Response-Hash werden gespeichert.
6. **Artefaktspeicher:** Unveraenderliche, tenantgebundene Objekte mit Hash, Version, Provenienz und Retention. Notion enthaelt nur Metadaten und kontrollierte Links.
7. **Audit und Observability:** Append-only Audit-Events und technische Telemetrie liegen ausserhalb des Notion-Write-Pfads. Notion erhaelt eine bedienbare Projektion von Fehlern und DLQ-Status.

### 6.2 Kanonischer Ablauf

1. UI oder Notion erzeugt ein signiertes Signal mit `event_id`.
2. Der Adapter liest den aktuellen Notion-Datensatz erneut und baut einen Command.
3. Der Transition Service prueft Tenant, Rolle, Revision, Vorzustand, Gate, Budget und Policy.
4. n8n reserviert Operation und Kosten ueber einen Idempotency-Key.
5. Ein typisierter Subworkflow verarbeitet genau einen Schritt und schreibt unveraenderliche Artefakte.
6. Validatoren und Policies erzeugen maschinenlesbare Evidence.
7. n8n committet die Transition atomar, erzeugt ein Audit-Event und aktualisiert die Notion-Projektion.
8. Bei Human Gate wird ein revisionsgebundener Approval-Record angelegt. Resume erfolgt nur mit einmaligem Token und passender Revision.
9. Retry setzt dieselbe fachliche Operation fort. Nach Retry-Limit folgt DLQ statt neuer Seiteneffekt.
10. 3b wird nach Publikation und 30, 60 oder 90 Tagen separat terminiert. Es ist kein initialer Vorgaenger von 4a.

### 6.3 Mandanten-, Queue- und Kostenmodell

- Namespace und Autorisierung werden an jeder Boundary aus `tenant_id` und stabilen Ressourcen-IDs abgeleitet.
- Notion Writes laufen seriell pro Projektrevision und limitiert pro Connection.
- Provider- und LLM-Queues besitzen globale und tenantbezogene Fairness sowie per-Provider-Limits.
- Jeder geplante Call hat `estimated_cost`, `reserved_cost`, `actual_cost`, `currency`, `budget_id` und `budget_period`.
- Programmatic-Local-Batches benoetigen eine explizite Batchfreigabe, maximale Seitenzahl und Kill Switch.
- Credentials werden als Secret-Aliase referenziert, nach Environment und Scope getrennt, rotiert und nie in Notion, Artefakten oder Audit-Payloads gespeichert.

### 6.4 Migrationsprinzip

Zuerst Domain-, State-, Gate-, Notion- und Artefaktvertraege stabilisieren. Danach einen vertikalen Schritt mit Provider-Stub durch UI, Operations API, n8n, Artefaktspeicher und Notion fuehren. Anschliessend die neun Schritte einzeln migrieren. Pro Schritt wird ein Cutover mit nur einem Writer durchgefuehrt. Claude Desktop bleibt bis zum End-to-End-Pilot reine Legacy-Referenz, darf aber keinen bereits migrierten Zustand mehr schreiben.

## 7. Maschinenpruefbare Acceptance Criteria

| ID | Kriterium | Maschinenpruefbarer Nachweis |
|---|---|---|
| AC-ARCH-01 | Jeder Command enthaelt `tenant_id`, `command_id`, `expected_revision`, `actor_id`, `project_id`, `step_id` und `schema_version`. Unbekannte Felder werden abgelehnt. | Contract-Test validiert positive Envelope-Fixture und erwartet je fehlendem Pflichtfeld sowie bei Zusatzfeld HTTP 400 mit stabilem Fehlercode. |
| AC-ARCH-02 | Zwei Commands mit gleicher `command_id` oder gleichem Idempotency-Key erzeugen genau einen fachlichen Seiteneffekt. | Integrationstest sendet beide Commands parallel und zaehlt einen Provider-POST, ein Artefakt und eine Notion-Task. |
| AC-ARCH-03 | Zwei unterschiedliche Commands mit derselben `expected_revision` koennen nicht beide committen. | Race-Test erwartet einen Erfolg und einen `ERROR_REVISION_CONFLICT`; finale Revision erhoeht sich genau um eins. |
| AC-ARCH-04 | Notion-Events werden nach `event_id` dedupliziert, ungeordnet zugestellt und durch erneutes API-Lesen reconciliert. | Stub-Test liefert Event B vor A und A zweimal; genau der aktuelle API-Stand erzeugt einen Command. |
| AC-ARCH-05 | Kein Cross-Tenant-Zugriff ist ueber Projekt-ID, Notion-Page-ID, Artefakt-Key, Run-ID oder Providerjob moeglich. | Parametrisierte Negativtests erwarten HTTP 404 oder Policy-Deny ohne fremde Metadaten in Antwort und Log. |
| AC-ARCH-06 | Freigaben sind an Gate-, Run-, Artefakt- und Policy-Version sowie SHA-256 gebunden. | Test erzeugt Artefakt V2 nach Freigabe von V1; Resume wird mit `ERROR_APPROVAL_STALE` abgelehnt. |
| AC-ARCH-07 | Ein Resume-Token ist authentifiziert, laeuft ab und kann genau einmal genutzt werden. | Tests fuer falsche Signatur, Ablauf und Replay erwarten Ablehnung; Happy Path setzt genau eine Transition fort. |
| AC-ARCH-08 | Jede n8n- und Subworkflow-Eingabe validiert gegen ein geschlossenes Schema. | Export-Linter lehnt jeden Workflow mit unversioniertem Input oder `Accept all data` ab. |
| AC-ARCH-09 | Globale, tenantbezogene und providerbezogene Concurrency gelten auch fuer Manual-, Sub-, Error- und Replay-Pfade. | Lasttest mit kontrollierten Stubs misst, dass kein konfiguriertes Limit ueberschritten wird. |
| AC-ARCH-10 | Notion 429/529 respektieren `Retry-After`, Jitter und Retry-Limit; nicht-idempotente 5xx-Writes erzeugen keine Duplikate. | Clock-gesteuerter Adaptertest prueft Wartezeiten, Versuchszahl und genau einen Datensatz. |
| AC-ARCH-11 | Providerdispatch findet nicht statt, wenn das Restbudget kleiner als die maximalen Auftragskosten ist. | Budgettest erwartet `ERROR_COST_BUDGET_EXCEEDED` und null Providerrequests. |
| AC-ARCH-12 | DataForSEO ist Default fuer Keyword-, Labs- und SERP-Rohdaten; AgentSEO benoetigt eine explizite selektive Routingentscheidung. | Routing-Contract-Tests pruefen Providerwahl, Capability und gespeicherte Begruendung. |
| AC-ARCH-13 | Jeder Providerjob persistiert Request-Hash, Idempotency-Key, Provider-Job-ID, Status, Kosten und Retry-Zaehler. | Neustarttest setzt nach Prozessabbruch dieselbe Job-ID fort und erzeugt keinen zweiten POST. |
| AC-ARCH-14 | Jeder Artefakt-Key ist tenant- und rungebunden; Originale sind unveraenderlich und SHA-256 wird bei Lesen geprueft. | Storage-Contract-Test lehnt Ueberschreiben und Hashabweichung ab. |
| AC-ARCH-15 | Ein terminal gescheiterter Auftrag landet nach exakt dem konfigurierten Retry-Limit in der DLQ und kann nur auditiert replayt werden. | Fehlerworkflow-Test prueft Versuchszahl, DLQ-Record, Actor, Grund und neue Run-ID bei Replay. |
| AC-ARCH-16 | Ausfall von Notion verhindert weder technisches Error Logging noch DLQ-Aufnahme. | Integrationstest simuliert Notion-Ausfall und findet Event sowie DLQ-Record im unabhaengigen Auditpfad. |
| AC-ARCH-17 | Der kanonische Graph besitzt genau einen initialen Pfad `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`; 3b ist ein wiederholbarer post-publication Sideflow. | Graph-Linter prueft Kanten, Preconditions und verbotene Zyklen. |
| AC-ARCH-18 | Alle zehn realen Use Cases sind ohne freie Zusatzfelder und ohne manuelle Sonderlogik darstellbar. | Zehn anonymisierte Domain-Fixtures validieren; Cross-Border-, Multi-Market-, Multi-Brand-, GBP- und Programmatic-Local-Beziehungen werden explizit asserted. |
| AC-ARCH-19 | YMYL- und regulierte Outputs koennen ohne marktbezogene Evidence, Disclaimer-Policy und erforderliche Freigabe nicht publiziert werden. | Negative Policy-Tests fuer Medizin, Pflege und Finanzen erwarten terminalen Policy-Deny vor Task- oder Publish-Erzeugung. |
| AC-ARCH-20 | Die UI kann keine direkte Notion-Mutation oder rohe n8n-Resume-URL ausfuehren. | E2E-Sicherheitstest prueft ausschliesslich Operations-API-Calls, CSRF-Schutz, RBAC und maskierte Artefaktlinks. |
| AC-ARCH-21 | Cutover und Rollback erlauben pro Projekt und Schritt genau einen Writer. | Migrationsintegrationstest blockiert Legacy-Write nach Cutover und beweist Freeze, Export, Reconciliation und Owner-Wechsel beim Rollback. |
| AC-ARCH-22 | Ein echter anonymisierter Kunde durchlaeuft Intake bis Notion-Task ohne Claude Desktop und kann nach Worker-Neustart fortgesetzt werden. | End-to-End-Pilot protokolliert alle Runs, Gates, Artefakthashes, Notion-Revisionen, Kosten und Recovery-Schritte. |

## 8. Go, Conditional Go oder No-Go

**Deploymentverdict: No-Go.** Es darf kein produktiver UI-, n8n- oder Notion-Workflow fuer Kunden aktiviert werden. Insbesondere duerfen keine produktiven Providercredentials, Notion-Schreibrechte oder kostenpflichtigen Trigger an den beschriebenen Plan gebunden werden.

Ein **Conditional Go fuer einen isolierten, kostenfreien Vertical-Slice-Pilot mit Stubs** ist erst zulaessig, wenn AC-ARCH-01 bis AC-ARCH-08, AC-ARCH-14, AC-ARCH-16, AC-ARCH-17 und AC-ARCH-20 maschinell bestanden sind. Dieser Pilot ist kein Kundenbetrieb.

Ein **Conditional Go fuer genau einen realen Kundenpilot** ist erst zulaessig, wenn alle AC-ARCH-01 bis AC-ARCH-21 bestanden sind, der Kunde im neuen Domainmodell ohne Ausnahmen darstellbar ist, die Providerbudgets explizit freigegeben sind und Restore sowie Rollback in einer produktionsgleichen Umgebung nachgewiesen wurden.

Ein **Go fuer Produktion und Abschaltung von Claude Desktop** setzt zusaetzlich AC-ARCH-22, einen zweiten Kunden aus einem anderen Archetyp, dokumentierte Betriebsverantwortung, Alarmierung, Secret-Rotation, Backup-Restore und eine signierte Release-Freigabe durch Raphael Rechberger voraus.

## 9. Exakte Dateien, Tests und naechste Fix-Reihenfolge

Die folgenden Dateien sind die empfohlene naechste Umsetzung. Sie wurden in diesem Audit nicht angelegt.

### Fix 1: Kanonische Domain- und State-Vertraege

1. `standards/domain/customer-workspace.schema.json`
2. `standards/domain/search-deployment.schema.json`
3. `standards/domain/entity-domain-gbp.schema.json`
4. `standards/workflow/workflow-graph.yaml`
5. `standards/workflow/run-envelope.schema.json`
6. `standards/workflow/transition-command.schema.json`
7. `standards/workflow/approval-record.schema.json`
8. `standards/workflow/error-envelope.schema.json`
9. `tests/contracts/test_real_customer_domain_fixtures.py`
10. `tests/contracts/test_workflow_graph.py`
11. `tests/contracts/test_transition_contract.py`

Zuerst AC-ARCH-01, AC-ARCH-03, AC-ARCH-06, AC-ARCH-17 bis AC-ARCH-19 erfuellen. Erst danach Notion oder n8n bauen.

### Fix 2: Notion Control Model und Synchronisation

1. `integrations/notion/data-sources.v1.yaml`
2. `integrations/notion/property-mappings.v1.yaml`
3. `integrations/notion/status-mappings.v1.yaml`
4. `integrations/notion/webhook-envelope.schema.json`
5. `integrations/notion/sync-policy.md`
6. `tests/integration/notion/test_webhook_deduplication.py`
7. `tests/integration/notion/test_revision_conflict.py`
8. `tests/integration/notion/test_rate_limit_retry.py`
9. `tests/integration/notion/test_schema_drift.py`

Damit AC-ARCH-03, AC-ARCH-04 und AC-ARCH-10 erfuellen. Kein Workflow darf Property-Anzeigenamen hardcoden.

### Fix 3: Tenant, RBAC, Credentials und Operations API

1. `standards/security/tenant-access-policy.yaml`
2. `standards/security/credential-alias.schema.json`
3. `ui/openapi/heartweb-operations-api.yaml`
4. `ui/contracts/command-response.schema.json`
5. `tests/security/test_cross_tenant_access.py`
6. `tests/security/test_rbac_commands.py`
7. `tests/security/test_secret_redaction.py`
8. `tests/ui/test_command_idempotency.py`
9. `tests/ui/test_stale_revision_feedback.py`

Damit AC-ARCH-02, AC-ARCH-05 und AC-ARCH-20 erfuellen. Kein UI-Direktzugriff auf Notion und keine rohe n8n-Webhook- oder Resume-URL zulassen.

### Fix 4: Artefakt-, Audit-, Queue- und Kostenvertraege

1. `standards/runtime/artifact-record.schema.json`
2. `standards/runtime/audit-event.schema.json`
3. `standards/runtime/provider-job.schema.json`
4. `standards/runtime/cost-budget.schema.json`
5. `standards/runtime/dlq-record.schema.json`
6. `config/runtime/concurrency-limits.yaml`
7. `config/runtime/retry-policies.yaml`
8. `tests/integration/storage/test_artifact_immutability.py`
9. `tests/integration/runtime/test_concurrency_limits.py`
10. `tests/integration/runtime/test_cost_budget.py`
11. `tests/integration/runtime/test_dlq_replay.py`
12. `tests/integration/runtime/test_notion_outage_logging.py`

Damit AC-ARCH-09 und AC-ARCH-11 bis AC-ARCH-16 erfuellen. Der Artefaktspeicher bleibt implementierungsneutral, bis Hosting und Retention entschieden sind.

### Fix 5: Providerneutrales Gateway

1. `services/research_gateway/contracts/research-request.schema.json`
2. `services/research_gateway/contracts/research-evidence.schema.json`
3. `services/research_gateway/adapters/dataforseo.py`
4. `services/research_gateway/adapters/agentseo.py`
5. `services/research_gateway/routing.py`
6. `tests/contract/provider/test_dataforseo_contract.py`
7. `tests/contract/provider/test_agentseo_contract.py`
8. `tests/integration/provider/test_job_resume_idempotency.py`
9. `tests/integration/provider/test_geo_response_validation.py`
10. `tests/integration/provider/test_provider_routing.py`

Damit AC-ARCH-12 und AC-ARCH-13 erfuellen. `services/agentseo_gateway/core.py` wird erst nach bestandenem Contract-Test integriert oder ersetzt. Keine Hermes-spezifische Runtime-Abhaengigkeit einfuehren.

### Fix 6: n8n Vertical Slice und danach alle Schritte

1. `n8n/workflows/WF-00-intake-assessment.json`
2. `n8n/workflows/WF-01-project-initialization.json`
3. `n8n/workflows/WF-02-seo-geo-loop.json`
4. `n8n/workflows/WF-04-notion-task-distribution.json`
5. `n8n/workflows/WF-06-performance-loop.json`
6. `n8n/workflows/WF-99-error-handler.json`
7. `n8n/subworkflows/SW-transition-commit.json`
8. `n8n/subworkflows/SW-human-gate-wait.json`
9. `n8n/subworkflows/SW-provider-dispatch.json`
10. `n8n/subworkflows/SW-artifact-write.json`
11. `tests/n8n/test_export_contracts.py`
12. `tests/n8n/test_subworkflow_closed_inputs.py`
13. `tests/n8n/test_wait_timeout_and_replay.py`
14. `tests/n8n/test_error_workflow_dlq.py`

Zuerst nur einen vertikalen Stub-Pfad importieren und AC-ARCH-07, AC-ARCH-08 sowie AC-ARCH-16 beweisen. Danach Schritte 0, 1, 1b, 1c, 2, 3, 4a, 4b und zuletzt den separaten 3b-Scheduler migrieren.

### Fix 7: UI, Cutover und End-to-End-Abnahme

1. `ui/contracts/project-projection.schema.json`
2. `ui/contracts/approval-command.schema.json`
3. `ui/contracts/retry-command.schema.json`
4. `migration/claude-desktop-cutover-runbook.md`
5. `migration/legacy-state-import.schema.json`
6. `tests/e2e/test_ui_n8n_notion_vertical_slice.py`
7. `tests/e2e/test_approval_artifact_revision.py`
8. `tests/e2e/test_worker_restart_resume.py`
9. `tests/e2e/test_cutover_single_writer.py`
10. `tests/e2e/test_rollback_reconciliation.py`
11. `tests/e2e/test_real_customer_pilot.py`

Damit AC-ARCH-21 und AC-ARCH-22 erfuellen. Erst danach `README.md`, `00_admin/PROJECT_STATE.md`, `docs/04-entscheidungslog.md`, `docs/05-human-in-the-loop.md`, `standards/dateinamen-und-output-vertrag.md` und die neun Prompts auf den freigegebenen Runtime-Vertrag aktualisieren. Claude Desktop erst nach erfolgreichem zweiten Archetyp-Pilot aus dem Produktionspfad entfernen.
