# Sprint 2 Quality, Security, and Maintainability Review

**Author:** Raphael Rechberger
**Date:** 2026-08-19
**Scope:** Fresh read-only review of the current Sprint 2 operator and integration contracts, fixtures, tests, integration operating models, full-suite runner, and relevant runtime identity conventions.

## Audit Basis

- The six operator schema names are enumerated in `tests/contracts/test_operator_records.py:12-19`. The contract test asserts Draft 2020-12, stable Heartweb IDs, and `additionalProperties: false` for each at `tests/contracts/test_operator_records.py:60-68`. The actual `operator-task` schema requires tenant, project, run, step, artifact, evidence, status, and a structured operator action at `standards/operator/operator-task.schema.json:4-16`.
- The integration contract test loads the event, Notion, and n8n schemas at `tests/contracts/test_integration_contracts.py:34-43`, then asserts closed Draft 2020-12 contracts at `tests/contracts/test_integration_contracts.py:52-56`.
- The event contract requires event ID, typed event name, occurrence time, correlation ID, idempotency key, identity, mode, and payload at `standards/integrations/workflow-event.schema.json:7-20`. Its conditional mapping applies distinct identity and closed payload definitions to all 13 event types at `standards/integrations/workflow-event.schema.json:21-56`.
- The runtime transition command retains the canonical tenant, project, run, expected-revision, and idempotency identity convention at `standards/runtime/transition-command.schema.json:4-18`. The n8n command preserves the same routing identity and excludes approval and completion command types at `standards/integrations/n8n-command.schema.json:7-30`.

## P0 Findings

No P0 findings. No current evidence shows an unauthorised state transition, unbounded data exposure, or a contract failure that blocks the Sprint 2 simulated operating path.

## P1 Findings

No P1 findings. Notion is schema-locked to `state_authority: transition_service` and `atomic_state_writer: false` at `standards/integrations/notion-projection.schema.json:17-20`. The integration test confirms that a projected-status field edit remains valid only as a projection and that claiming Notion as authority is rejected at `tests/contracts/test_integration_contracts.py:82-105`.

## P2 Findings

No P2 findings. Event fixtures cover the exact typed catalog and reject unknown payload fields and invalid identity binding at `tests/contracts/test_integration_contracts.py:58-80`. The schema's closed, event-specific payload definitions prevent payload-field false greens at `standards/integrations/workflow-event.schema.json:44-56`.

## P3 Findings

No P3 findings. The runner separates root discovery from contract discovery at `tests/run_full_suite.py:39-70`, fails either unittest phase on zero discovered tests at `tests/run_full_suite.py:59-63`, and totals the separately executed phase counts at `tests/run_full_suite.py:127-143`. The regression test launches the contracts-only subprocess, requires a nonzero count, and checks the real output for both `test_operator_records` and `test_integration_contracts` at `tests/test_full_suite_runner.py:19-37`.

## Security and Operational Assessment

- Event correlation and idempotency are mandatory and format-constrained at `standards/integrations/workflow-event.schema.json:7-14`. The append-only contract is explicit in the event title at `standards/integrations/workflow-event.schema.json:4`; duplicate-event and out-of-order handling are specified without canonical overwrite in `docs/integrations/n8n-orchestration-model.md:19-23` and `docs/integrations/notion-operating-model.md:21-23`.
- Simulated and live transports are mutually exclusive in all three integration schemas: event `standards/integrations/workflow-event.schema.json:21-23`, Notion `standards/integrations/notion-projection.schema.json:22-24`, and n8n `standards/integrations/n8n-command.schema.json:25-27`. The integration tests validate simulated fixtures, reject mode-only live masquerading, and validate correctly identified live-shaped variants at `tests/contracts/test_integration_contracts.py:62-71`, `tests/contracts/test_integration_contracts.py:98-105`, and `tests/contracts/test_integration_contracts.py:107-124`.
- n8n cannot issue `approve_gate` or `complete_run` because its closed command enum contains only dispatch, wait, retry, resume, and dead-letter operations at `standards/integrations/n8n-command.schema.json:22-30`; this negative path is executed at `tests/contracts/test_integration_contracts.py:107-124`.
- Retry, resume, duplicate, out-of-order, and DLQ semantics are explicit: retry preserves correlation and idempotency, resume is a Transition Service request, duplicates are replays, and exhausted retries enter DLQ without direct run mutation at `docs/integrations/n8n-orchestration-model.md:13-23`. Notion field edits, conflicts, delivery duplicates, and resume requests remain subject to Transition Service validation at `docs/integrations/notion-operating-model.md:15-27`.
- Portability and maintainability are supported by `sys.executable`, argument-list subprocess calls, isolated discovery functions, and count parsing in `tests/run_full_suite.py:18-23`, `tests/run_full_suite.py:39-50`, and `tests/run_full_suite.py:73-113`.

## Executed Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_operator_records -v`: exit 0, `Ran 5 tests in 0.082s`, `OK`.
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_integration_contracts -v`: exit 0, `Ran 6 tests in 0.143s`, `OK`.
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_full_suite_runner -v`: exit 0, `Ran 1 test in 0.794s`, `OK`. This execution invoked the contracts-only child runner and verified nonzero discovery plus both required contract modules, not static source markers alone.
- `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`: exit 0. Acceptance phase: 7 of 7. Root unittest discovery excluding `tests/contracts`: 104. Contract unittest discovery: 35. Reported total: 146. The contract-phase verbose output executed all 5 `test_operator_records` tests and all 6 `test_integration_contracts` tests.

## Residual Verification Limits

- This review executed only local simulated contracts and tests. No live Notion, n8n, provider, credential, queue, persistence, or network transport was invoked. The documentation itself states that the current local wave has no live fixture, connection, credential, or write path at `docs/integrations/notion-operating-model.md:9-13`.
- JSON Schema and fixture tests validate message shape and documented semantics. They cannot by themselves demonstrate a production event store's append-only enforcement, duplicate suppression, ordering, retry bounds, DLQ retention, authentication, or authorization. Those controls are described in the operating models at `docs/integrations/n8n-orchestration-model.md:19-23` and `docs/integrations/notion-operating-model.md:21-27` but have no live adapter surface in this Sprint 2 scope.

## Scope Discipline

The reviewed Sprint 2 artifacts remain limited to operator records, integration contracts, fixtures, operating models, and full-suite discovery. This review made no source, schema, fixture, test, state, plan, AHD, or documentation change.

## Verdict

APPROVED
