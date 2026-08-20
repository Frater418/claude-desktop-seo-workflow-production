# Sprint 4 Stage B Operator API Implementation

Date: 2026-08-20
Author: Raphael Rechberger
Status: implemented and locally validated

## Scope

This implementation adds the Stage B local FastAPI adapter and its contained JSONL EventStore without changing an existing contract, workflow authority, simulator, UI, deployment artifact, or provider integration.

The adapter delegates transition evaluation to `services.transition_service.process_transition` and routes canonical transition failures through `services.operator_routing.route_error`. The API has no direct status endpoint. Transition success appends the supplied valid Workflow Event V2 before atomically writing the derived run projection. A failed projection write preserves the event and makes readiness fail until a rebuild is performed.

## Public Layout

All project records are rooted beneath one server-configured workspace at `<workspace>/v2/operator/`:

- `project.json`: required controlled project projection.
- `logical-session.json`: required logical-project-session projection.
- `workflow.json`: required workflow projection. Step `3b` is represented only in its `sideflows` projection.
- `runs/<run_id>.json`: required run projection.
- `steps.json`, `artifacts.json`, `gates.json`, `tasks.json`, `tickets.json`, `assignments.json`, `context-packages.json`, `llm-runs.json`, `performance-checkpoints.json`, `metrics.json`, `adjustment-proposals.json`, and `integrations-status.json`: optional projection collections that return an empty array when absent.
- `releases/<release_id>.json`: controlled returned release projection only.
- `operator-records/<record_type>/<record_id>.json`: controlled typed operator record projection only.
- `events/events.jsonl`: the sole EventStore log.

`WorkspaceRegistry` owns the tenant and project to workspace mapping. HTTP requests never include a filesystem path. The registry and repository validate identity syntax, resolved existing roots, containment, and existing symlink or reparse-point components before read or write access. Physical paths are not included in a response or error.

## EventStore

`EventStore` uses the repository Event V2 schema with a real `Draft202012Validator` and `FormatChecker`. It emits canonical UTF-8 JSON with sorted keys, compact separators, one newline, flush, and `fsync`. The existing log is read and validated under one create-only portable lock before append. Malformed JSON, invalid history records, duplicate event IDs, and partial tails fail closed. A matching idempotency key and identical canonical event replays without append. A changed event produces `ERR_IDEMPOTENCY_CONFLICT`. The lock uses only `pathlib` and standard-library file creation, never `fcntl` or shell execution.

## HTTP Surface

- Liveness and readiness: `GET /healthz`, `GET /readyz`.
- Project reads: list/get project, logical session, workflow, steps/list and detail, artifacts, gates, tasks, tickets, assignments, context packages, run detail/history, performance checkpoints, metrics, adjustment proposals, and integration status.
- Commands: `POST /v1/tenants/{tenant_id}/projects/{project_id}/commands/{verb}` for `start`, `request-revision`, `request-input`, `create-defect`, `escalate`, `request-waiver`, `approve`, `reject`, `resolve`, and `resume`.
- OpenAPI: FastAPI generated only at `/openapi.json`, with stable operation IDs and typed response envelopes.

The command envelope is closed Pydantic transport validation. It requires route, body, correlation, idempotency, tenant, project, run, step, revision, and Event V2 identity agreement. It accepts exactly one transition command or explicitly typed operator record. The adapter validates the existing transition and operator-record schemas rather than reproducing their rules.

## Test-First Evidence

Negative RED runs preceded production modules:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_event_store -v
Result before EventStore: Ran 1 test, ERROR, ModuleNotFoundError for services.operator_api.

PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api -v
Result before adapter: Ran 1 test, ERROR, ModuleNotFoundError for services.operator_api.app.
```

The final focused command was:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store -v
Result: Ran 6 tests, OK.
```

The focused routing regression command was:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store tests.test_operator_error_routing -v
Result: Ran 15 tests, OK.
```

Focused coverage exercises Event V2 invalid-event rejection, append, identical replay, idempotency conflict, malformed partial tail, duplicate event ID, contained read families, Step 3b sideflow projection, unknown and cross-tenant access, traversal rejection, route/body identity mismatch, transition delegation, append-before-run-projection, and replay without a second transition.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
Host: PASS. Acceptance 7, root 211, contracts 59, total 277 tests.

docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py'
OMO: PASS. Acceptance 7, root 211, contracts 59, total 277 tests.

PYTHONDONTWRITEBYTECODE=1 python -c "... ast.parse(..., feature_version=(3, 11)) ..."
Result: PYTHON_311_AST_PASS 5 modules.
```

`basedpyright` diagnostics could not run because the server is not installed and its installation was previously declined. No commit or push was performed.

## Limitations

- Host and OMO use Python 3.12. Python 3.11 syntax was checked with the Python 3.11 AST feature mode, but no Python 3.11 interpreter is installed.
- Native Windows reparse-point behavior was not executed in this Linux environment. The implementation uses only portable `pathlib` and `os` primitives and rejects resolved-link traversal.
- FastAPI TestClient emitted the installed Starlette HTTPX deprecation warning. It did not affect any test result.
