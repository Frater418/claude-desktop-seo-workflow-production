# Stage B Operator API Review Fix

Date: 2026-08-20
Author: Raphael Rechberger
Status: complete
Scope: Stage B operator-record recovery only.

## Decision Basis

This repair implements the three P1 changes requested by reports 43 and 44 within the Stage B boundary. DEC-0018 keeps workflow authority in the local Core and Transition Service. DEC-0019 makes durable files and append-only events authoritative. Master-plan Tasks 4.3 through 4.5 require the read API, routed commands, contained append-only events, idempotency, and no direct status write.

## TDD Evidence

Negative regressions were added to `tests/test_operator_api.py` before production changes. The initial RED command was:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api -v
Result: Ran 8 tests in 7.202s, FAILED with 4 failures and 1 error.
```

The pre-fix failures established the requested defects: nested `command_id` and `idempotency_key` mismatches returned 200, reordered operator records were not written under `task_id`, and symlink-blocked post-append projections returned 404 rather than 503. The recovery tests also demonstrated that the prior replay path could not repair the accepted event.

## Implemented Recovery Transaction

`ProjectRepository` now owns one fixed canonical identity map. It never derives an identifier from mapping iteration order:

| Contract record type | Canonical field | Required prefix | Run field |
| --- | --- | --- | --- |
| `operator-task` | `task_id` | `task-` | `run_id` |
| `blocker-record` | `blocker_id` | `blocker-` | `run_id` |
| `revision-request` | `revision_request_id` | `revision-` | `run_id` |
| `workflow-defect` | `defect_id` | `defect-` | `affected_run_id` |
| `escalation-record` | `escalation_id` | `escalation-` | `run_id` |
| `resolution-record` | `resolution_id` | `resolution-` | `run_id` |

The existing Draft 2020-12 record schema validates the full record. The repository independently rejects a missing, non-string, or prefix-invalid canonical identifier. This fixes both key-order dependence and same-tenant identifier collisions, including the `workflow-defect` contract's distinct `affected_run_id` field.

Before an operator-record event append, the API atomically writes this contained recovery sidecar:

```text
<workspace>/v2/operator/projection-recovery/
  <record_type>--<record_id>.json
    record_type
    record_id
    command_id
    record
```

The sidecar contains the complete schema-valid record and receives no caller-controlled path. On a valid append, the canonical projection is atomically replaced at:

```text
<workspace>/v2/operator/operator-records/<record_type>/<record_id>.json
```

Only after that projection finalization does the repository remove the sidecar. Any finalization failure retains the sidecar, marks `projection_rebuild_needed`, returns the original safe canonical error code with HTTP 503, and makes `/readyz` return 503. Startup scans each registered workspace for pending sidecars and begins unready when any exist.

A matching replay first validates the stored sidecar identity, command ID, canonical record identity, complete record schema, and canonical record bytes. It then retries finalization without calling EventStore append. A successful repair deletes the sidecar, clears rebuild-needed only when no sidecars remain, returns `replay: true`, and leaves exactly one event. A conflicting replay returns 409 before touching the sidecar. If EventStore validation or append fails before durable acceptance, the newly created sidecar is removed and no canonical projection is written.

`_assert_transition_envelope` now binds the nested transition command's `command_id`, `tenant_id`, `project_id`, `run_id`, `expected_revision`, `idempotency_key`, optional `step_id`, and verb-to-operation mapping before `process_transition`. The one parameterized unittest matrix covers every mismatch with the existing 409 or 422 semantics and verifies no event or run mutation.

## Regression Coverage

The focused test module exercises these public ASGI requests in `TemporaryDirectory` workspaces:

- Reordered operator record plus two distinct same-tenant `task_id` values.
- The eight-field nested transition mismatch matrix.
- Symlink containment failure with one event, one sidecar, HTTP 503, and `/readyz` 503.
- Obstacle removal followed by matching replay, one event only, canonical projection, sidecar removal, and `/readyz` 200.
- Restart against a pending sidecar, remaining unready.
- Event validation failure with no retained sidecar or projection.
- Conflicting replay that returns 409 and leaves the sidecar intact.
- All seven operator-record command allowlists: `request-revision`, `request-input`, `create-defect`, `escalate`, `request-waiver`, `reject`, and `resolve`.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store tests.test_operator_error_routing tests.contracts.test_operator_records -v
PASS: Ran 25 tests in 10.586s.

PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
Host PASS: acceptance 7, root 216, contracts 59, total 282 tests.

docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py'
OMO PASS: acceptance 7, root 216, contracts 59, total 282 tests.

PYTHONDONTWRITEBYTECODE=1 python -c "... ast.parse(..., feature_version=(3, 11)) ..."
PASS: PYTHON_311_AST_PASS 3.
```

The changed-file LSP diagnostic requests were made for `services/operator_api/app.py`, `services/operator_api/repository.py`, and `tests/test_operator_api.py`. The local basedpyright server is not installed and had already been declined, so diagnostics were unavailable. The executed focused and full suites provide the available executable verification. The installed Starlette TestClient emitted its existing HTTPX deprecation warning without affecting results.

Pure non-comment LOC measurements are `app.py` 308, `repository.py` 205, and `test_operator_api.py` 199. The API composition root is above the general 250-line warning threshold because it retains the pre-existing full Stage B FastAPI route surface plus the required recovery boundary. No new module could be introduced without violating the mandated Stage B write allowlist. The changed production responsibilities remain singular: HTTP operator-command composition in `app.py` and contained workspace persistence in `repository.py`.

No contracts, EventStore implementation, routing, read endpoints, OpenAPI behavior, Stage C files, provider path, network call, deployment artifact, commit, or push changed. The internal implementation checklist is empty.
