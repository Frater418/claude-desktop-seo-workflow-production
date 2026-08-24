# M08L Hermes Gateway LLM Adapter - Section 11 Report

**Autor:** Raphael Rechberger
**Datum:** 2026-08-23
**Status:** PASS
**Evidence-Level:** Live-provider smoke plus real local Heartweb runtime integration
**Nicht bewiesen:** realer Kunden-Golden-Path, externe Produktion, M09 Release-Audit, M10 Kundenoutput

## 1. Ziel

M08L verbindet den bestehenden Heartweb `LLMRunRequest` minimal mit dem isolierten Hermes Runs API Backend, ohne eine allgemeine LLM-Plattform vor M10 zu bauen.

## 2. Verwendete Runtime

- Hermes-Profil: `heartweb-runtime`
- Provider: OpenAI Codex OAuth ueber den Hermes-verwalteten Shared Auth Pool
- Modell: `gpt-5.6-sol`
- API Server: Loopback-only
- API-Authentifizierung: separater lokaler Bearer-Key, Wert nicht gespeichert
- Built-in `MEMORY.md`: aktiv und profilisoliert
- `USER.md`: deaktiviert
- Hindsight oder anderer externer Memory-Provider: deaktiviert
- API-Server-Toolsets: alle deaktiviert
- MCP: deaktiviert
- Gateway-Autostart: deaktiviert

## 3. Implementierte Minimalgrenze

- `HermesRunsClient` fuer `POST /v1/runs` und gebundenes Polling
- exakte Behandlung von `started`, `running`, `completed`, `failed`, `cancelled` und Interaktionszustaenden
- `HermesRuntimeProvider` fuer kanonisches Context Package, offizielle Promptbytes und exakt gebundene Source-Inhalte
- unveraendertes simuliertes Fixture-Verhalten
- bestehende Output-Contracts, Runtime-Persistenz, Idempotency und Recovery werden wiederverwendet
- Provider-Run-ID, Modell, Timestamps und Token Usage werden im bestehenden LLM Result persistiert
- kein Router-Marktplatz, kein separater Execution Store, keine Subagent- oder Multi-Provider-Plattform

## 4. Reale API-Vertraege

Die Live-Probes fanden und belegten diese Werte:

- Create: `{run_id, status=started}`
- Intermediate: `status=running`
- Intermediate object: `hermes.run`
- Terminal last event: `run.completed`
- Terminal: Output plus Usage und gebundene Session-/Run-Identitaet

Die urspruenglichen Mockannahmen `object=run` und `last_event=completed` wurden fokussiert korrigiert.

## 5. Source-Envelope-Befund

Der erste echte Step-0-Versuch enthielt nur Context-Referenzen und Hashes, aber keine tatsächlichen Intake- und Contract-Inhalte. Da das isolierte Profil keine File Tools besitzt, reagierte das Modell korrekt mit `ERROR_BRIEFING_INCOMPLETE` und erfand keine Kundendaten. Heartweb lehnte die Fehlerantwort korrekt am Manifest-Schema ab.

Der Minimalfix bindet nun die bereits von Heartweb validierten Source-Bytes deterministisch in den Hermes-Input-Envelope. Unbekannte Refs, Hashabweichungen und nicht dekodierbare Inhalte stoppen vor dem HTTP-Aufruf.

## 6. Fokussierte Verifikation

Controller-eigene OMO-Verifikation:

```text
python -m unittest tests.test_hermes_runs_client tests.test_hermes_runtime_provider tests.test_local_runtime
Ran 26 tests
OK
```

Python-Compile der betroffenen Client-, Provider-, Runtime- und Testdateien: PASS.

Die Windows-Host-Ausfuehrung der Runtime-Testmodule war wegen eines bestehenden `mcp.tools` Namespace-Konflikts nicht importierbar. Dieser Host-PASS wird nicht behauptet. Die kanonische OMO-Closure ist gruen.

Keine komplette Repository-Suite und kein `hermes verify --json` wurden ausgefuehrt.

## 7. Finaler echter neutraler Heartweb-Lauf

```text
status: PASS
execution_mode: real
step_id: 0
candidate_is_object: true
candidate_sha256: 52bd4bf522e43978a4934b958c0354ca33c6984e593f13477d841564c830ff52
context_package_persisted: true
llm_records_persisted: true
provider_run_id_present: true
model_id: gpt-5.6-sol
input_tokens: 13477
output_tokens: 1823
total_tokens: 15300
result_status: succeeded
output_contract: https://heartweb.example/schema/manifest.schema.json
workspace_ephemeral: true
tool_call_count: 0
```

Der Output bestand das registrierte Manifest-Schema und wurde ueber die bestehende Heartweb Runtime atomar in einem temporaeren neutralen Workspace persistiert. Der temporaere Workspace wurde nach dem Lauf entfernt.

## 8. Abschlusszustand

Detailed Health nach dem Lauf:

```text
status: ok
readiness: ok
active_api_runs: 0
active_agents: 0
gateway_busy: false
gateway_drainable: true
```

M08L ist damit abgeschlossen. M09 darf beginnen. Der reale AHD-Kundenoutput bleibt M10 und benoetigt weiterhin echte Pilotdaten und Providerzugang.
