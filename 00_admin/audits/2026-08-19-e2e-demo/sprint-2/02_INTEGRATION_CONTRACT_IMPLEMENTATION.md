# Sprint 2 Integration Contract Implementation

## Scope

Implemented Sprint 2 Tasks 2.7 through 2.9 only. The contracts define append-only workflow events, a Notion operative projection, and n8n orchestration commands. Notion remains the central operative interface and is not an atomic state writer. All current positive fixtures use `simulated` integration mode.

## Created Files

- `standards/integrations/workflow-event.schema.json`
- `standards/integrations/event-catalog.json`
- `standards/integrations/notion-projection.schema.json`
- `standards/integrations/n8n-command.schema.json`
- `docs/integrations/notion-operating-model.md`
- `docs/integrations/n8n-orchestration-model.md`
- `tests/contracts/test_integration_contracts.py`
- `tests/fixtures/integrations/workflow-events/project-created.json`
- `tests/fixtures/integrations/workflow-events/run-started.json`
- `tests/fixtures/integrations/workflow-events/step-blocked.json`
- `tests/fixtures/integrations/workflow-events/artifact-created.json`
- `tests/fixtures/integrations/workflow-events/gate-ready.json`
- `tests/fixtures/integrations/workflow-events/gate-approved.json`
- `tests/fixtures/integrations/workflow-events/gate-rejected.json`
- `tests/fixtures/integrations/workflow-events/task-created.json`
- `tests/fixtures/integrations/workflow-events/task-resolved.json`
- `tests/fixtures/integrations/workflow-events/defect-created.json`
- `tests/fixtures/integrations/workflow-events/escalation-created.json`
- `tests/fixtures/integrations/workflow-events/run-resumed.json`
- `tests/fixtures/integrations/workflow-events/release-created.json`
- `tests/fixtures/integrations/notion/project-projection.json`
- `tests/fixtures/integrations/n8n/wait-for-gate-command.json`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-2/02_INTEGRATION_CONTRACT_IMPLEMENTATION.md`

## RED Evidence

Command:

```bash
python -m unittest tests.contracts.test_integration_contracts -v
```

Outcome: failed before implementation. `IntegrationContractTests.setUpClass` raised `FileNotFoundError` for `standards/integrations/workflow-event.schema.json`. The command reported `Ran 0 tests` and `FAILED (errors=1)`.

## GREEN Evidence

Focused command:

```bash
python -m unittest tests.contracts.test_integration_contracts -v
```

Outcome: six tests passed in 0.104s. The suite verified the exact 13-event catalog, Draft 2020-12 stable schema IDs, closed event payloads, valid simulated fixtures, simulated-to-live masquerade rejection, Notion transition-service authority after a projected field edit, and n8n rejection of `approve_gate` and `complete_run` command types.

Full command:

```bash
python tests/run_full_suite.py
```

Outcome: passed. The acceptance runner reported `7/7 Tests erfolgreich bestanden`. Unittest discovery reported `Ran 103 tests in 2.899s` and `OK`. The runner ended with `[FULL SUITE PASSED] Acceptance and unittest discovery completed successfully.`

## Contract Decisions

- Workflow events are append-only records with event ID, typed catalog entry, correlation ID, idempotency key, stable identity bindings, and closed event-specific payloads.
- `simulated` requires `simulation_id`, while `live` requires `live_connection_id`. The modes are mutually exclusive, so changing a current simulated fixture to live is invalid.
- Notion projections have `state_authority: transition_service` and `atomic_state_writer: false`. Field edits remain proposals until a versioned command passes transition validation.
- n8n commands require idempotency, correlation, expected revision, and mode. They can dispatch, wait, retry, resume, or enter a DLQ but cannot approve gates or complete runs.
- The operating-model documents define wait, retry, resume, DLQ, duplicate delivery, out-of-order delivery, and Notion conflict behavior.

## Integration Mode Correction Evidence

The Notion projection root schema previously required `simulation_id` unconditionally, which contradicted the valid `live` conditional path. The unconditional requirement was removed. The existing `simulated` conditional still requires `simulation_id` and rejects `live_connection_id`. The existing `live` conditional still requires `live_connection_id` and rejects `simulation_id`. Authority locks remain `state_authority: transition_service` and `atomic_state_writer: false`.

Focused tests now construct live Notion and n8n variants from the simulated fixtures by setting `integration_mode` to `live`, removing `simulation_id`, and adding `live_connection_id`. Both variants validate. Mode-only changes remain invalid, so simulated fixtures cannot masquerade as live.

Correction RED command:

```bash
python -m unittest tests.contracts.test_integration_contracts -v
```

Correction RED outcome: failed as expected before the schema correction. The live Notion projection variant failed with `'simulation_id' is a required property`. The command reported `Ran 6 tests in 0.121s` and `FAILED (failures=1)`.

Correction GREEN command:

```bash
python -m unittest tests.contracts.test_integration_contracts -v
```

Correction GREEN outcome: passed. All six focused tests passed in 0.109s, including valid live-mode Notion and n8n variants and the existing anti-masquerade checks.

Correction full-suite command:

```bash
python tests/run_full_suite.py
```

Correction full-suite outcome: passed. The acceptance runner reported `7/7 Tests erfolgreich bestanden`. Unittest discovery reported `Ran 103 tests in 2.925s` and `OK`. The runner ended with `[FULL SUITE PASSED] Acceptance and unittest discovery completed successfully.`

## External Systems

No network, provider, crawler, deployment, live Notion, live n8n, or other external system was invoked. No existing file was modified.
