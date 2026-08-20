# Stage B Operator API and Event Store Quality Review

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Read-only adversarial quality and operational-conformance review of Sprint 4 Stage B. The sole repository change made for this review is this report. All runtime probes used automatically cleaned `tempfile.TemporaryDirectory()` workspaces. No provider, network, production workspace, deployment, or repository source/test/contract mutation was used.

## Decision Basis

DEC-0018 requires an independently executable local Core, with canonical workflow status, hashes, revisions, and gate decisions protected by the Core or Transition Service: `00_admin/DECISIONS.md:81-93`. DEC-0019 makes durable files and append-only events authoritative and prohibits direct canonical writes from the Operator Console or Notion: `00_admin/DECISIONS.md:95-105`.

The reviewed implementation was assessed against the Stage B architecture research, approved build plan, Stage A2 boundary, implementation report, and independent specification review: `00_admin/audits/2026-08-19-e2e-demo/sprint-4/01_API_ARCHITECTURE_RESEARCH.md:41-107`; `03_SPRINT4_BUILD_PLAN.md:136-199`; `17_STAGE_A2_IMPLEMENTATION_PLAN.md:8-18`; `42_STAGE_B_OPERATOR_API_IMPLEMENTATION.md:7-39`; `43_STAGE_B_OPERATOR_API_SPEC_REVIEW.md:13-70`. Master-plan Tasks 4.3 through 4.5 require the specified read/command surfaces, no direct status write, Transition or Routing Service delegation, and workspace-contained append-only events with ID, idempotency, timestamp, and correlation fields: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:621-645`.

## Verified Behavior

- `CommandRequest` is a closed Pydantic transport envelope with all ten verbs and exactly one transition or typed record shape: `services/operator_api/models.py:10-41`. The command route binds outer route/body/Event V2 tenant, project, run, step, revision, correlation, idempotency, and verb/event-type values before dispatch: `services/operator_api/app.py:147-158`, `202-219`.
- Transition commands call `process_transition`, route returned canonical failures, append the event before derived projection writes, and set the readiness rebuild flag when a transition projection write raises `RepositoryError`: `services/operator_api/app.py:234-276`. A stale nested transition revision probe returned `409 ERR_STALE_REVISION` and created no event file.
- EventStore validates against the closed Event V2 schema, emits canonical compact sorted UTF-8 JSONL, flushes and `fsync`s, and scans/validates the whole history under a create-only lock: `services/operator_api/event_store.py:43-78`, `90-125`. The Event V2 contract requires the identity, event ID, correlation ID, idempotency key, timestamp, mode, and event-specific payload: `standards/integrations/workflow-event-v2.schema.json:5-64`.
- In a temporary EventStore workspace, first append was `replay=False`, an identical append was `replay=True`, a changed payload under the same idempotency key raised `ERR_IDEMPOTENCY_CONFLICT`, a pre-created lock raised `ERROR_TRANSITION_LEDGER_LOCKED`, and removal of that lock restored history access. Focused repository coverage additionally rejects invalid events before log creation, partial tails, and duplicate history event IDs: `tests/test_operator_event_store.py:40-83`.
- Existing workspace roots, identifiers, and every extant path component are checked for containment and links before repository or EventStore access: `services/operator_api/repository.py:40-74`, `154-166`; `services/operator_api/event_store.py:127-165`. Public unknown, cross-tenant, and encoded traversal reads are rejected: `tests/test_operator_api.py:83-91`. Error messages used by these boundaries contain no physical workspace path: `services/operator_api/repository.py:22-28`; `services/operator_api/event_store.py:20-29`.
- Startup validates schemas, workflow graph, routing policy completeness, catalog parity, gate registry, and every registered EventStore history before readiness: `services/operator_api/app.py:173-192`. A malformed temporary history made strict construction raise `RuntimeError("Operator API dependencies are unavailable.")`; `allow_unready=True` exposed `/readyz` as `503`.
- `/openapi.json` is FastAPI-generated and the temporary ASGI probe found 21 unique operation IDs including `submitOperatorCommand`: `services/operator_api/app.py:61`, `89-159`.
- The reviewed Stage B modules contain no `fcntl`, subprocess, shell, or `os.system` use. Parsing all five Stage B Python modules with `ast.parse(..., feature_version=(3, 11))` succeeded. This is syntax compatibility evidence, not execution on a Python 3.11 interpreter.

## Findings

### P1: Typed-record projection failure commits an unrecoverable partial command while reporting failure and remaining ready

`_operator_record` appends the event before writing the typed projection, but unlike `_transition`, it neither marks `projection_rebuild_needed` nor restores a coherent public state after `RepositoryError`: `services/operator_api/app.py:279-301`, compared with `265-275`. The exception handler maps that containment failure to `404`: `services/operator_api/app.py:79-82`.

An adversarial public ASGI probe created only a temporary workspace whose `v2/operator/operator-records/operator-task` was a symlink to another temporary directory. A valid `request-input` returned `404 ERR_TENANT_ISOLATION`, yet `events.jsonl` contained one accepted event and `/readyz` returned `200`. Retrying the identical command cannot repair the record because `_replay` returns before `_operator_record` calls `write_operator_record`: `services/operator_api/app.py:151-158`, `222-231`, `297-301`. The persisted Event V2 `step.blocked` payload contains only blocker ID and reason, not the full typed operator record required to reconstruct its projection: `standards/integrations/workflow-event-v2.schema.json:46`.

This violates the Stage B gate requiring tenant isolation and no mutation on failed commands: `03_SPRINT4_BUILD_PLAN.md:193-199`. It creates an acknowledged durable event without its required operator-record projection, reports that request as failed, and leaves the process falsely ready. Required change: make command acceptance atomic from the public perspective, or persist enough canonical record data for deterministic recovery; on every post-append projection failure, set rebuild-needed before surfacing a retryable unavailable response. Add a regression test that verifies event, projection, retry, and readiness behavior for each record command.

### P1: Operator-record filename is controlled by JSON member order rather than the record-type identity

`write_operator_record` chooses the first input key ending in `_id` as its filename, rather than a fixed ID field for the schema-selected record type: `services/operator_api/repository.py:125-129`. JSON member order is caller-controlled and schemas accept equivalent mappings regardless of that order. The operator-task contract requires `task_id` but also contains tenant, project, and run IDs: `standards/operator/operator-task.schema.json:5-16`.

The public ASGI probe sent a schema-valid `request-input` record with `tenant_id` inserted first. It returned `200` and wrote `operator-records/operator-task/tenant-demo.json`; the expected `task-00000001.json` was absent. This permits distinct tasks for one tenant to overwrite the same projection path and defeats deterministic record addressing. The defect independently reproduces the specification review's finding: `43_STAGE_B_OPERATOR_API_SPEC_REVIEW.md:34-38`.

Required change: map every allowlisted record type to one explicit canonical identity field and validate its type/prefix before the write. Add API coverage for reordered records and distinct records from the same tenant.

### P1: Nested transition command is not fully bound to the public command identity

The outer envelope and Event V2 identities are checked, but the nested transition command is only schema-validated and operation-checked before `process_transition`: `services/operator_api/app.py:202-219`, `242-260`. The transition service checks tenant, project, run, revision, input hash, and state rules, but does not check its nested `command_id` against the outer API `command_id`: `services/transition_service/service.py:203-243`.

In a temporary public ASGI probe, a valid `start` request with outer `command_id=command-00000001` and nested `transition_command.command_id=command-00000099` returned `200`, `replay=false`, and response `command_id=command-00000001`. This produces conflicting audit identities for one accepted command. The defect independently reproduces the specification review's finding: `43_STAGE_B_OPERATOR_API_SPEC_REVIEW.md:40-44`.

Required change: bind the nested command's shared identity and idempotency fields to the envelope before delegation, at minimum command ID, tenant ID, project ID, run ID, expected revision, and idempotency key. Add mismatch tests for each field.

## Focused Test and Probe Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store tests.test_operator_error_routing tests.contracts.test_operator_records -v
Result: Ran 20 tests in 2.091s, OK.

PYTHONDONTWRITEBYTECODE=1 python - <<'PY' ... temporary EventStore append/replay/conflict/lock probe ... PY
Result: EVENTSTORE False True ERR_IDEMPOTENCY_CONFLICT ERROR_TRANSITION_LEDGER_LOCKED event-00000001.

PYTHONDONTWRITEBYTECODE=1 python - <<'PY' ... temporary public ASGI record/containment/transition/OpenAPI probes ... PY
Result: reordered valid record: 200, tenant-demo.json exists, task-00000001.json absent.
Result: record projection containment failure: 404 ERR_TENANT_ISOLATION, one event line, /readyz 200.
Result: stale transition: 409 ERR_STALE_REVISION, event file absent.
Result: extra top-level field: 422, FastAPI extra_forbidden detail.
Result: OpenAPI: 21 operation IDs, unique, submitOperatorCommand present.

PYTHONDONTWRITEBYTECODE=1 python - <<'PY' ... nested transition command_id mismatch public ASGI probe ... PY
Result: HTTP 200, response command-00000001, replay false.

PYTHONDONTWRITEBYTECODE=1 python - <<'PY' ... malformed temporary history startup probe ... PY
Result: strict startup RuntimeError; allow_unready /readyz 503.

PYTHONDONTWRITEBYTECODE=1 python - <<'PY' ... ast.parse feature_version=(3, 11) ... PY
Result: PYTHON_311_AST_PASS 5.
```

The FastAPI TestClient emitted the installed Starlette HTTPX deprecation warning during focused tests and probes. It did not affect outcomes. Native Windows reparse-point behavior and execution with a Python 3.11 interpreter were not available in this Linux Python 3.12 environment. Linux symlink containment, portable lock contention, and Python 3.11 grammar compatibility were exercised. No other verification was blocked.

Decision: REQUEST_CHANGES
