# Stage B Operator API and Event Store Specification Review

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Read-only specification and implementation conformance audit of Sprint 4 Stage B only.

## Decision Basis

DEC-0018 requires an independently executable local Core, with n8n as later transport and Notion as an operational projection. Canonical status, hashes, revisions and gate decisions remain protected by the local Core or Transition Service: `00_admin/DECISIONS.md:81-93`. DEC-0019 makes the durable project state, append-only events, artifacts, evidence, decisions, gates and revisions authoritative, and expressly prohibits Notion or the Operator Console from directly writing canonical status: `00_admin/DECISIONS.md:95-105`.

Tasks 4.3 through 4.5 require the specified read API, the ten command verbs, no direct status write, Transition or Routing Service delegation, append-before-success, a server-side workspace registry, contained append-only JSONL, replay protection, and portable locking: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:621-645`. The approved Stage B plan repeats those constraints and makes health, readiness, startup failure, tenant isolation, and FastAPI-only OpenAPI part of the gate: `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md:136-199`. The Stage A2 plan establishes that Stage B must consume the completed runtime contracts and must not include simulators or UI work: `00_admin/audits/2026-08-19-e2e-demo/sprint-4/17_STAGE_A2_IMPLEMENTATION_PLAN.md:12-18`, `391-400`.

## Verified Conformance

### API surface and transport closure

- `create_app` publishes liveness and readiness routes, project list/detail, logical session, workflow, steps/list and detail, all required collection families, run detail/history, and one command route: `services/operator_api/app.py:89-159`. This covers the Stage B list, including context packages and LLM run history/details, not just the older architecture report list.
- The body model is closed at the HTTP-envelope boundary with `extra="forbid"`, a literal union of all ten verbs, and exactly-one transition-or-record validation: `services/operator_api/models.py:10-41`. Nested transition, operator-record and Event V2 payloads are then validated against their closed Draft 2020-12 source contracts before persistence: `services/operator_api/app.py:242-250`, `289-293`; `standards/runtime/transition-command.schema.json:4-18`; `standards/integrations/workflow-event-v2.schema.json:5-64`.
- The exact verb inventory is closed in `_EVENT_FOR_VERB`. `start`, `approve`, and `resume` are transition verbs, and the other seven verbs have an explicit allowed typed-record family mapping: `services/operator_api/app.py:24-35`. `_assert_command_identity` rejects unknown verbs, route/body tenant-project mismatch, Event V2 identity mismatch, correlation or idempotency mismatch, and an event type not mapped to the verb: `services/operator_api/app.py:202-219`.
- The registry is server-owned and accepts only syntactically valid tenant/project identities. It resolves one configured existing non-symlink root and does not take any filesystem path from an HTTP request: `services/operator_api/repository.py:40-74`. Repository and EventStore containment reject link/reparse traversal: `services/operator_api/repository.py:154-166`; `services/operator_api/event_store.py:127-165`.

### Authority, event store, replay, and projections

- Transition commands call the real `process_transition` with loaded workflow graph and quality registry. Transition failures are passed to `route_error`; no API endpoint accepts a direct run-status write: `services/operator_api/app.py:16-17`, `234-276`. The only run write uses `result["run"]` after Transition Service succeeds: `services/operator_api/app.py:269-276`.
- Non-transition commands validate their mapped record contract, append an Event V2 record, then write the typed record projection: `services/operator_api/app.py:279-301`. The Event V2 contract is closed and requires event ID, type, timestamp, correlation, idempotency, full identity, integration identity, and typed payload: `standards/integrations/workflow-event-v2.schema.json:5-64`.
- The EventStore uses the required contained path `v2/operator/events/events.jsonl`, validates each event and existing history, locks with create-only files, writes canonical UTF-8 JSONL with newline, flush and fsync, and rejects partial tails, malformed history and duplicate event IDs: `services/operator_api/event_store.py:17-18`, `40-78`, `99-149`.
- API replay is checked before calling Transition Service, so a matching replay cannot trigger a second transition. The store independently applies the same idempotency protection: `services/operator_api/app.py:151-158`, `222-231`; `services/operator_api/event_store.py:59-78`. The transition path appends before writing the derived run/release projection and marks readiness false if that contained projection write raises `RepositoryError`: `services/operator_api/app.py:265-276`, `93-97`.
- Workflow is a stored projection, and the Stage B test verifies that its `3b` entry is only a `sideflows` entry with `not_due`, consistent with the post-publication sideflow rather than an initial edge: `tests/test_operator_api.py:57-81`; `standards/workflow/workflow-graph.json:25-27`.
- Dependency construction parses and checks all local schemas, workflow graph, routing policy completeness, Event V2 catalog parity, gate registry and each configured EventStore history before the app becomes ready: `services/operator_api/app.py:173-192`. Public OpenAPI contains 21 unique operation IDs, including `submitOperatorCommand` for the parameterized command route, from FastAPI only: `services/operator_api/app.py:89-159`.
- No Stage C implementation was found. `services/integrations/` and `apps/operator-console/` do not exist. This matches the Stage B scope and does not prematurely add Notion, n8n, UI, generated TypeScript, provider, or deployment work.

## Findings

### P1: Operator-record persistence key is caller-order dependent, not the record identity

`ProjectRepository.write_operator_record` selects the first input mapping key ending in `_id` as the filename identity: `services/operator_api/repository.py:125-129`. JSON object insertion order is user-controlled through the public request body. The contracts accept records independently of key order, so a valid `operator-task` whose `tenant_id` is first persists to `operator-records/operator-task/tenant-demo.json` instead of its required `task_id` path. This violates the stated controlled layout of `<record_type>/<record_id>.json` in `00_admin/audits/2026-08-19-e2e-demo/sprint-4/42_STAGE_B_OPERATOR_API_IMPLEMENTATION.md:21-24`, breaks deterministic record addressing, and permits unrelated records of the same type and tenant to overwrite each other.

Required change: use a fixed, record-type-specific canonical identifier field, validate its expected prefix, and add public API coverage for reordered valid record objects and distinct same-tenant records.

### P1: Nested Transition Command identity is not bound to the accepted command envelope

The adapter checks the route against outer body identities and Event V2 identities, but it does not compare `transition_command.command_id` to `command_id` before delegating: `services/operator_api/app.py:202-219`, `242-260`. A public request with an outer `command_id` different from the otherwise-valid nested transition command is accepted with HTTP 200 and returns the outer ID. This violates the implementation's claimed command-envelope identity agreement: `00_admin/audits/2026-08-19-e2e-demo/sprint-4/42_STAGE_B_OPERATOR_API_IMPLEMENTATION.md:37-40`, and weakens the required route/body/event audit identity even though Transition Service still protects its own transition state.

Required change: bind every shared transition field to the envelope before delegation, at minimum command ID, tenant ID, project ID, run ID, expected revision and idempotency key. Add negative API tests for each mismatch.

## Test and Probe Evidence

Focused repository tests were executed without network or production mutation:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store tests.test_operator_error_routing tests.contracts.test_operator_records -v
Result: Ran 20 tests in 2.001s, OK.
```

This exercised read projections and `3b`, unknown/cross-tenant/traversal reads, `start` delegation, append and replay, invalid Event V2 rejection, partial-tail and duplicate-event rejection, routing-policy completeness, and closed operator-record contracts: `tests/test_operator_api.py:66-109`; `tests/test_operator_event_store.py:40-83`; `tests/test_operator_error_routing.py:102-182`; `tests/contracts/test_operator_records.py:12-93`.

Adversarial public ASGI and EventStore probes ran in `tempfile.TemporaryDirectory()` workspaces only and cleaned themselves up:

```text
Unknown top-level command field: HTTP 422, extra_forbidden.
Nested transition command_id mismatch: HTTP 200, replay false, response carried the different outer command_id.
PUT to workflow status path: HTTP 405.
EventStore append/replay/conflict: false, true, ERR_IDEMPOTENCY_CONFLICT.
Valid request-input record with tenant_id inserted first: HTTP 200; stored as operator-task/tenant-demo.json.
Malformed event history at app construction: RuntimeError.
Append followed by injected temporary containment failure: HTTP 404, one persisted event line, /readyz HTTP 503.
OpenAPI: 21 operation IDs, all unique; command operation ID submitOperatorCommand.
```

The projection-failure probe confirms append occurs before projection and that readiness correctly becomes unavailable for a caught `RepositoryError`. It does not cure either P1 identity defect above. No verification was blocked. The FastAPI TestClient emitted the installed Starlette HTTPX deprecation warning during tests and probes; it did not affect outcomes.

Decision: REQUEST_CHANGES
