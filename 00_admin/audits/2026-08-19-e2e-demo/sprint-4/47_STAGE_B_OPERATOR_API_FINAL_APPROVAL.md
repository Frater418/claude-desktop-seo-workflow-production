# Stage B Operator API Final Approval Audit

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Independent local, read-only Stage B approval audit. DEC-0018 keeps canonical workflow authority in the local Core and Transition Service. DEC-0019 makes durable files and append-only events authoritative. The Stage B gate requires readiness, startup validation, tenant isolation, no mutation on failed commands, and FastAPI-only OpenAPI: `00_admin/DECISIONS.md:81-109`, `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md:136-198`.

## Spec Findings

### P0

None observed.

### P1

**P1-S1: A pending recovery in one registered workspace can be hidden by a successful repair in another workspace.** Startup correctly discovers pending sidecars across all registrations at `services/operator_api/app.py:68-71`, but `_repair_operator_record` replaces the process-wide `projection_rebuild_needed` flag using only the workspace currently being repaired at `services/operator_api/app.py:356-361`. `/readyz` trusts that global flag at `services/operator_api/app.py:97-101`.

Observed public ASGI result with two registered temporary workspaces: an injected post-append finalization failure for tenant A returned `503`; `/readyz` returned `503`; a valid tenant B record command returned `200`; then `/readyz` returned `200` while tenant A's recovery sidecar remained. This violates the Stage B readiness and no-partial-command gate because the original accepted event still lacks its required projection. Approval requires readiness to remain derived from pending recoveries across every registry workspace, with a two-workspace regression test.

### P2

None observed.

### P3

None observed.

## Quality Findings

### P0

None observed.

### P1

**P1-Q1: Regression coverage does not protect the process-wide recovery invariant.** `tests/test_operator_api.py:175-218` exercises recovery, replay, restart, and conflict only for one workspace. The full suite passed while the two-workspace probe reproduced P1-S1, so the current tests cannot detect the readiness regression created by the global mutable flag in `services/operator_api/app.py:63`, `356-359`.

### P2

None observed.

### P3

None observed.

## Verified Evidence

1. Command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_operator_api tests.test_operator_event_store tests.test_operator_error_routing tests.contracts.test_operator_records -v`
   Outcome: exit 0, `Ran 25 tests in 9.516s`, `OK`. This covers reordered same-tenant distinct records, all nested transition identity fields, sidecar recovery, restart pending state, conflict preservation, replay repair with one event, append-failure cleanup, EventStore replay/conflict/partial-tail/duplicate-history behavior, and routing-policy completeness.

2. Command: `PYTHONDONTWRITEBYTECODE=1 python - <<'PY'` with the local inline TestClient and EventStore audit probe executed in the audit terminal.
   Outcome: `NESTED_IDENTITY command_id=409 tenant_id=409 project_id=409 run_id=409 expected_revision=409 idempotency_key=409 operation=409 step_id=422 no_event=True`; all nine allowed verb/record-type pairs returned `200`, covering all seven allowlists; `OPENAPI operations=21 unique=21 command=True`; `EVENTSTORE append=False replay=True conflict=ERR_IDEMPOTENCY_CONFLICT lock=ERROR_TRANSITION_LEDGER_LOCKED malformed=ERROR_CONTEXT_SOURCE_INVALID`; `MULTI_WORKSPACE_READINESS first=503 pending_ready=503 other_success=200 after_other_ready=200`.

3. Command: `PYTHONDONTWRITEBYTECODE=1 python - <<'PY'` with the local inline Linux directory-symlink containment and replay-repair probe executed in the audit terminal.
   Outcome: `LINUX_SYMLINK_FAILURE http=503 code=ERR_TENANT_ISOLATION sidecar=True events=1 ready=503`; after obstacle removal, `REPLAY_REPAIR http=200 replay=True sidecar=False events=1 ready=200`. The Windows-portable mock change in report 46 therefore does not weaken Linux containment evidence.

4. Command: `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Outcome: exit 0. Acceptance `7/7`, root discovery `216`, contracts `59`, total `282` tests passed. The installed FastAPI TestClient emitted the existing Starlette HTTPX deprecation warning only.

## Unexecuted Or Blocked Checks

Native Windows reparse-point execution was not available on this Linux host. This is explicitly distinct from the observed Linux symlink containment result above. No provider, network, deployment, or remote tooling was used.

REQUEST_CHANGES
