# Official Platform Evidence for Target Architecture

- Autor: Raphael Rechberger
- Datum: 18. August 2026
- Zweck: Primaerquellen fuer den fundamentalen Heartweb-Workflow-Audit

## n8n

### Concurrency

Quelle: https://docs.n8n.io/deploy/host-n8n/configure-n8n/scaling/control-concurrency

- Im regulaeren Self-Hosted-Modus ist Production-Concurrency ohne explizite Konfiguration unbegrenzt.
- Zu viele parallele Runs koennen Event Loop Thrashing, Performanceverlust und Unresponsiveness verursachen.
- `N8N_CONCURRENCY_PRODUCTION_LIMIT` muss fuer einen kontrollierten Betrieb explizit gesetzt werden.
- Das Limit gilt fuer Production Executions aus Triggern und Webhooks, nicht automatisch fuer Manual Runs, Subworkflows, Error Workflows oder CLI-Runs.
- Queue Mode besitzt eine separate Worker-Concurrency und benoetigt eigene Betriebsarchitektur.

### Error Workflows

Quelle: https://docs.n8n.io/build/flow-logic/handle-errors-gracefully

- Jeder produktive Workflow kann einen eigenen Error Workflow verwenden.
- Error Workflows starten mit dem Error Trigger.
- Der Fehlerkontext kann Execution-ID, Retry-Bezug, letzte Node und Stack enthalten.
- Fachlich erzwungene Fail-fast-Abbrueche koennen ueber Stop And Error ausgeloest werden.

### Human Gates und Resume

Quelle: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.wait/

- Wait Nodes koennen einen Run pausieren und Execution-Daten in die n8n-Datenbank auslagern.
- Resume kann ueber Zeit, eindeutigen Webhook oder Formular erfolgen.
- Jede Wait-Execution besitzt eine eigene Resume-URL.
- Resume-Webhooks koennen Basic Auth, Header Auth oder JWT verwenden.
- Wait Gates brauchen ein Zeitlimit und einen definierten Timeout-Pfad.
- Partial Executions veraendern die Resume-URL und duerfen nicht als Production-Resume-Mechanismus missverstanden werden.

### Queue Mode

Quelle: https://docs.n8n.io/deploy/host-n8n/configure-n8n/scaling/enable-queue-mode

- Queue Mode verwendet Main- und Worker-Instanzen sowie Redis als Broker.
- n8n speichert Execution-Daten in seiner eigenen Datenbank.
- SQLite ist fuer verteilten Queue Mode nicht empfohlen beziehungsweise nicht unterstuetzt.
- Alle Worker benoetigen denselben Encryption Key fuer Credentials.
- Binaerdaten brauchen eine gemeinsame Storage-Strategie, bevorzugt S3 oder Azure bei skalierter Runtime.

## Notion

### Request- und Groessenlimits

Quelle: https://developers.notion.com/reference/request-limits

- Durchschnittlich drei Requests pro Sekunde pro Connection.
- Zusaetzliches Workspace-weites Limit, geteilt durch alle Connections.
- 429 und 529 muessen `Retry-After`, Backoff, Jitter und ein Retry-Limit beachten.
- 500, 502, 503 und 504 duerfen fuer nicht-idempotente Writes nicht ohne eigene Idempotenzlogik wiederholt werden.
- Maximale Request-Groesse: 500 KB und 1000 Bloecke.
- Rich-Text-Inhalte pro Objekt sind auf 2000 Zeichen begrenzt.
- Relations-, Multi-Select- und People-Arrays haben Request-Limits.

### Webhook-Semantik

Quelle: https://developers.notion.com/reference/webhooks-events-delivery

- Webhook Events enthalten nicht den vollstaendigen aktuellen Inhalt.
- Nach jedem relevanten Event muss der aktuelle Stand erneut ueber die API gelesen werden.
- Events koennen aggregiert, verspaetet oder in anderer Reihenfolge eintreffen.
- Events besitzen Event-ID, Timestamp und Attempt Number.
- Consumer muessen deduplizieren, anhand Timestamps reconciliieren und den aktuellen API-Stand als Wahrheit lesen.
- Die Zustellung ist nicht als exakt-einmalige Transaktion zu behandeln.

### Datenquellen

Quellen:

- https://developers.notion.com/reference/data-source
- https://developers.notion.com/reference/property-object

- Notion-Datenbankzeilen sind Pages in einer Data Source.
- Properties muessen dem expliziten Data-Source-Schema entsprechen.
- YAML-Frontmatter allein erzeugt keine Notion-Properties und ist kein API-Vertrag.
- Notion empfiehlt maximal 500 Properties oder 50 KB Schemagroesse pro Data Source.

## Architekturfolgerungen fuer Heartweb

1. Notion kann das zentrale operative Steuerelement sein, aber nicht der einzige transaktionale Execution-State von n8n.
2. n8n muss seine eigene Execution-Datenbank behalten. Das widerspricht nicht dem Ziel, keine separate fachliche PostgreSQL-Source-of-Truth fuer Kundendaten einzufuehren.
3. Jeder Heartweb-Run braucht eine eigene Run-ID und Idempotency Keys.
4. Notion-Webhooks sind Signale. n8n muss danach den aktuellen Page- oder Data-Source-Stand erneut lesen.
5. Human Gates brauchen authentifizierte Resume-URLs, Timeout, Deduplizierung und erlaubte Zustandsuebergaenge.
6. Notion-Writes brauchen eine gemeinsame Queue und zentrale Retry-Policy.
7. Grosse Briefings, CSVs, HTMLs und Evidenzdateien gehoeren in einen Artefaktspeicher. Notion speichert Referenzen, Status, Metadaten und Freigaben.
8. n8n-Concurrency muss mandanten- und providerbewusst begrenzt werden.
9. Subworkflows brauchen definierte Inputschemas. `Accept all data` ist fuer Production-Domainlogik nicht ausreichend.
10. Error Workflows und Dead-Letter-Verhalten sind Pflicht, nicht spaetere Optimierung.
