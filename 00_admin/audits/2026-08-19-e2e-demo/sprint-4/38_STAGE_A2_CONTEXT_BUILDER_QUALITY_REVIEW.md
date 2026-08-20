# Sprint 4 Stage A2 Package A2.2 Context Builder Quality and Security Review

Date: 2026-08-20
Reviewer: Independent read-only adversarial quality and security review
Scope: Package A2.2 pure Context Builder and technical-session policy only.

## Decision Summary

REQUEST_CHANGES

The package is appropriately narrow: its public API is injected-data only and introduces no persistence, API, event, provider, network, subprocess, filesystem, clock, or workflow-state behavior. Focused and full tests pass. However, public-API adversarial probes found false greens in timezone-aware expiration, current-record and release identity binding, and result-record hash verification. These violate the A2.2 fail-fast reproducibility boundary in DEC-0019 and controller plan 17.

## Evidence Read

Reviewed before this decision: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; controller plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; Sprint 4 reports 15 through 36; the final A2.1 runtime validator and Context Package contract; all four files under `services/context_builder/`; relevant routing inventory and policy; `tests/test_context_builder.py`; `tests/test_operator_error_routing.py`; and the A2.1 focused contract and invariant tests executed by the full suite.

The reviewed public boundary is `build_context_package`, `validate_context_package`, `build_llm_request`, `validate_llm_request`, `validate_llm_result`, and `decide_technical_session`. The builder canonicalizes JSON with ASCII, sorted keys, compact separators, UTF-8, and `allow_nan=False` at [builder.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/builder.py:45). It ranks sources deterministically at [builder.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/builder.py:16), assigns contiguous order at [builder.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/builder.py:67), verifies package/source hashes at [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/validator.py:117), and routes the 13 declared A2.2 codes once through the existing canonical routing inventory at [router.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/operator_routing/router.py:25).

## Test Execution

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
PASS: 20 tests in 2.717s

PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
PASS: acceptance 7, root 202, contracts 59, total 268 tests
```

The passing focused coverage includes unsupported bytes and non-finite JSON, cache mismatches for every implemented cache-bound field, shuffled-source canonical parity, duplicate derived-field rejection, source and package hash checks, specialized prompt/output binding errors, predecessor revision/hash checks, historical comparison-only evidence, revision package construction, request idempotency full-payload comparison, output-byte verification, failed/cancelled output prohibition, deterministic immutable A2.1 errors, and routing-policy parity. The source itself contains no imports for I/O, environment, time, socket, subprocess, or provider clients. Python 3.11 was not available locally. The code uses Python 3.11-compatible syntax, but this audit could only execute on Python 3.12.

## Adversarial Public API Evidence

All probes constructed in-memory inputs and called only `services.context_builder` public functions with injected A2.1 validation dependencies. No files, network resources, providers, or repositories were modified or called.

| Probe | Observed behavior | Assessment |
| --- | --- | --- |
| `valid_until` of `2026-08-20T01:00:00+01:00` at evaluation time `2026-08-20T00:00:00Z` | `validate_context_package(...).valid == True` | False green: these instants are equal, so `valid_until <= evaluation_at` must be stale. |
| Exact matching cache with `expires_at` of `2026-08-20T01:00:00+01:00` at `now` of `2026-08-20T00:00:00Z` | `decide_technical_session(...).decision == reuse_permitted` | False green: the cache is expired at equality and must not be reused. |
| Current Project V2 record `source_id` changed to `project-substituted`; matching predecessor release `run_id` changed to `wrong-run` | `validate_context_package(...).valid == True` | False green: immutable current-record and release identity are not fully bound. |
| Valid success result with `result_sha256` replaced by 64 zeroes | `validate_llm_result(...).valid == True` | False green: result-record integrity is not checked. |
| Source descriptor `revision` changed to `not-an-integer` before package construction | raw `ValueError`, no structured Context Builder error | Fail-fast diagnostic gap. |

## Findings

### P0

None.

### P1: Offset-aware source freshness and cache expiry are compared lexically

Files: [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/validator.py:150), [session_policy.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/session_policy.py:35)

Both checks compare timestamp strings rather than parsed, normalized instants. The adversarial equal-instant offset inputs above remained valid and permitted cache reuse. This lets a stale source participate in a package and lets an expired technical-session cache be reused, contrary to plan 17 freshness and cache rules. Parse RFC 3339 timestamps to timezone-aware UTC instants, reject invalid or naive values, and add equality plus before/after offset regression cases for `valid_until` and `expires_at`.

### P1: Current-record, release, and result integrity bindings are incomplete

Files: [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/validator.py:142), [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/validator.py:177), [validator.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/validator.py:96)

The source-record loop compares tenant, project, run, and revision but not the record's own source ID or exact current lifecycle status. The predecessor release match validates tenant/project, artifact ID/hash/revision, step, and status, but not its run identity. The observed substituted current record plus wrong-release-run probe was accepted. Separately, `validate_llm_result` verifies success output bytes but never recomputes or compares `result_sha256`, so a forged result hash was accepted.

Bind every current record's ID, step where applicable, revision, content hash, and lifecycle status to its descriptor. Bind release identity according to the source record's run lineage rather than accepting an unrelated release run. Define and verify the canonical result-hash payload before accepting any result status. Add negative public-API tests for each identity field, release run mismatch, and forged result hashes on succeeded, failed, and cancelled results.

### P2: Malformed numeric source revisions escape as a raw exception

File: [builder.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/context_builder/builder.py:131)

`_source_key` calls `int(source["revision"])` before the A2.1 schema gate. A string such as `not-an-integer` raises an unstructured `ValueError`. This does not cause I/O or state mutation, but it violates the stated structured fail-fast error contract. Validate or safely normalize the value before sorting and return `ContextBuildError` with `ERROR_CONTEXT_SCHEMA_INVALID` and a stable source path. Cover malformed string, bool, and float revision inputs.

### P3

None.

## Scope Separation

These findings are A2.2 pure-builder responsibilities. They do not require, fault, or authorize deferred Stage B persistence, APIs, Event Store work, dispatch, providers, routers beyond the existing code inventory, or event emission. No finding requires a database, filesystem resolver, HTTP endpoint, technical-session storage, or workflow-state mutation. The existing A2.1 local schema and invariant boundary remains separately approved and was treated as injected input validation here.

## Verdict

REQUEST_CHANGES
