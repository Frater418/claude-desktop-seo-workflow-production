# Sprint 4 Stage A2 Package A2.2 Context Builder Specification Review

Date: 2026-08-20
Scope: Independent read-only review of Package A2.2 only.
Branch checked: `feature/e2e-operator-workflow-system`

## Decision Summary

`REQUEST_CHANGES`

The delivered Context Builder is a suitably narrow, injected-data implementation: it constructs canonical JSON packages, binds the live registry, validates package/request/result projections, evaluates technical-session policy, and introduces the specified routed errors without provider, filesystem, persistence, API, event, or workflow-state behavior. The focused 20-test gate and full 268-test suite pass.

Two P1 semantic false greens prevent approval. `validate_context_package` accepts a package whose selected released Project V2 descriptor no longer matches the lifecycle of its exact current record, and `decide_technical_session` permits reuse for an unrecognized cache state. Both violate A2.2's required exact-current-record and cache-policy validation before a retry or resume can proceed.

## Inputs Reviewed

Read: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; Sprint 4 reports 15 through 36; controller plan 17; the final A2.1 schemas, registry, validator, fixtures, and tests; all four `services/context_builder/` files; routing inventory and policy changes; `tests/test_context_builder.py`; `tests/test_operator_error_routing.py`; `tests/contracts/test_llm_runtime_contracts.py`; workflow graph; current prompt and output registry bindings.

The relevant A2.2 path is `build_context_package` in `services/context_builder/builder.py` to `RuntimeContractValidator.validate`, then `validate_context_package`, `build_llm_request`, `validate_llm_request`, `validate_llm_result`, and `decide_technical_session`. The public modules contain no filesystem, environment, clock, socket, provider, dispatch, persistence, or workflow-state mutation operation. This conforms to plan 17 lines 240-250.

## Verified Requirements

| Requirement | Evidence | Result |
| --- | --- | --- |
| Pure canonical builder and no input mutation | `builder.py:45-89`; `test_context_builder.py:92-102` | Pass |
| ASCII, sorted, compact JSON; source hash, manifest hash, package hash; caller-order independence | `builder.py:45-51, 67-89, 121-161`; focused canonical/hash tests | Pass |
| Exact active prompt and ordered output-contract registry binding | `builder.py:92-119`; `validator.py:157-165`; runtime-contract registry test | Pass |
| Step 0 intake, Step 1+ Project V2, Step 1c multi-output, revision construction | `context-package.schema.json:8-56`; `test_context_builder.py:212-229` | Pass |
| Source byte, identity, graph, release, predecessor, revision, trust, freshness, and package checks | `validator.py:68-72, 117-192` | Partial: finding P1-1 |
| Request/result projection, idempotency conflict, candidate-byte and token/result validation | `validator.py:32-54, 75-114`; `test_context_builder.py:192-210` | Pass |
| Technical-session decisions and exact cache binding fields | `session_policy.py:23-50`; `test_context_builder.py:115-124, 174-190` | Partial: finding P1-2 |
| All 13 canonical runtime codes have exactly one route | `router.py:25-29`; `test_operator_error_routing.py:121-132` | Pass |
| No Stage B persistence, API, Event Store, event, adapter, dispatch, provider, UI, Notion, n8n, or state authority | Context Builder source inspection and report 36 lines 108-114 | Pass |

## Test Evidence

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
Ran 20 tests in 2.760s
OK

PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
Acceptance: 7 tests; root discovery: 202; contracts: 59; total: 268
FULL SUITE PASSED
```

All probes below used in-memory copies and only the public Context Builder API. No files, network services, providers, or repository state were altered.

## Findings

### P0

None.

### P1-1: Current-record lifecycle drift for selected Project V2 is accepted

`validate_context_package` treats a source record as stale only when the record status is `superseded` or `historical`, or its `valid_until` has expired. It does not require the current record's `source_status` to equal the package descriptor's required lifecycle. See `services/context_builder/validator.py:140-153`. A2.1 correctly requires the selected package descriptor to be a released Project V2 in `services/runtime_contracts/llm_records.py:173-179`, but this does not validate the A2.2 current-record lookup.

I built the public Step 1 package, changed only `current_records['runtime:project/project-demo']['source_status']` from `released` to `active`, and called `validate_context_package` with the matching graph, release, registry, and source bytes. Observed result:

```text
CURRENT_PROJECT_RECORD_STATUS_DRIFT True ()
```

This violates DEC-0019's requirement that stale or superseded inputs stop before an LLM call, and plan 17 lines 279-297 requiring exact current records plus lifecycle and freshness validation. An active current Project V2 record conflicts with a package frozen as released and must produce a structured context error before request construction. Add a current-record lifecycle equality check for required project context, and regression probes for active, rejected, superseded, and historical current-record drift.

### P1-2: Unknown technical-session state is treated as reusable

`decide_technical_session` treats only `missing`, `expired`, and `invalid` as unavailable. Any other state reaches the exact-field comparison and can return `reuse_permitted`. See `services/context_builder/session_policy.py:30-41`. No public-cache schema is accepted by this function, and the test matrix covers only known available, missing, and field-drift cases in `tests/test_context_builder.py:115-124, 174-190`.

I constructed a public retry package and an otherwise exact cache record with `session_state: 'unknown_state'` and a future expiration. Observed result:

```text
UNKNOWN_CACHE_STATE reuse_permitted cache exactly matches the immutable package and profile
```

Plan 17 lines 308-314 permits reuse only for an exact retry or resume with an available, unexpired technical cache. Unknown state cannot prove availability and must fail closed as `denied` or recover as `recover_fresh`, not authorize reuse. Require `session_state == 'available'` for the reuse branch and add an unknown-state regression probe.

### P2

None.

### P3

None.

## Stage B Boundary

These findings do not require or fault deferred Stage B work. No persistence model, API endpoint, Event Store append, provider dispatch, adapter, Notion/n8n projection, UI, or technical-session storage implementation is expected in A2.2. The defects are entirely within its specified pure, injected-record semantic validation and technical-session decision boundary.

## Required Recheck

1. Add focused public-API tests for both observed P1 mutations.
2. Re-run the focused 20-test Context Builder and routing gate.
3. Re-run `python tests/run_full_suite.py` and the two in-memory probes above.

VERDICT: REQUEST_CHANGES
