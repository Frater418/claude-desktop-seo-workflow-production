# Sprint 1 Final Specification Gate Review

Author: Raphael Rechberger

Audit date: 2026-08-19

Scope: Fresh independent read-only final review of Sprint 1 Tasks 1.1 through 1.6, the current source, policies, schemas, tests, prior reports 01, 02, 05, and 06, and the current worktree state. No network, provider, crawler, deployment, AHD runtime, or external system was invoked.

## Acceptance Basis

Sprint 1 requires the transition service, registry applicability, crawl disposition, canonical persisted-artifact preflight, error routing, and the integration suite in Tasks 1.1 through 1.6: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:314-415`. The gate requires no open P0 or P1 findings: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:415`.

## P0

No P0 finding verified. The central transition service rejects invalid state, identity, revision, predecessor, artifact, gate, approval, and retry conditions before returning a deep-copied unchanged run: `services/transition_service/service.py:181-327`. It records a release only for valid complete or publish operations: `services/transition_service/service.py:329-346`.

## P1

### P1-01: Task 1.5 does not route every emitted runtime error code

Task 1.5 requires exactly one default route and owner type for every error code: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:393-404`. The routing validator checks only the manually maintained `CANONICAL_RUNTIME_ERROR_CODES` inventory: `services/operator_routing/router.py:8-39` and `services/operator_routing/router.py:69-83`. The policy supplies mappings only for that inventory: `standards/operator/error-routing-policy.json:4-91`.

The local inventory comparison executed during this review found 101 quoted `ERROR_*` or `ERR_*` codes emitted under `services/`, 87 canonical codes, and 14 emitted codes missing from the routing inventory and policy:

- `ERROR_AGENTSEO_API_KEY_MISSING`
- `ERROR_AGENTSEO_FETCH_FAILED`
- `ERROR_AGENTSEO_HTTP`
- `ERROR_AGENTSEO_JOB_ID_MISSING`
- `ERROR_AGENTSEO_NETWORK`
- `ERROR_AGENTSEO_RESPONSE_INVALID`
- `ERROR_AGENTSEO_TIMEOUT`
- `ERROR_KEYWORD_INPUT_INVALID`
- `ERROR_LOCATION_MISMATCH`
- `ERROR_LOCATION_MISSING`
- `ERROR_LOCATION_TABLE_INVALID`
- `ERROR_LOCATION_TABLE_MISSING`
- `ERROR_LOCATION_UNKNOWN`
- `ERROR_SERP_INPUT_INVALID`

These are active gateway error codes, not hypothetical values. For example, the gateway emits location, table, and keyword validation errors: `services/agentseo_gateway/core.py:46-109`. The current catalog cannot route any omitted code because `route_error()` first accepts only a policy that exactly covers its own canonical inventory, then raises the unknown-code error if a requested code has no mapping: `services/operator_routing/router.py:86-93`.

Required change: make the canonical runtime inventory complete for all emitted runtime services, add exactly one validated policy mapping and owner type for each missing code, and add a regression test that compares the emitted-code inventory with the routing catalog before routing each code.

### P1 Closure Confirmed: `ERROR_TRANSITION_LEDGER_LOCKED`

The P1 finding in reports 05 and 06 is closed. Durable-ledger contention emits `ERROR_TRANSITION_LEDGER_LOCKED`: `services/transition_service/service.py:45-65` and `services/transition_service/service.py:366-395`. The current canonical inventory includes it: `services/operator_routing/router.py:35-38`; its policy maps it once to `retryable_technical` with `workflow_maintainer`: `standards/operator/error-routing-policy.json:5-14`. The direct contention test invokes the real transition CLI entry point while holding the ledger lock and verifies the code, route, and owner: `tests/test_operator_error_routing.py:90-113`.

## P2

No open P2 finding verified.

- Canonical storage binding: the Step 1 preflight rejects absolute, traversal, and escaping storage keys, resolves the artifact below the controlled root, requires exact equality with the supplied path, and hashes only the resolved bytes: `services/step1_preflight/validator.py:493-559`. A same-name copy outside the storage root is rejected: `tests/test_step1_contract_v2.py:483-500`.
- Registry evidence and active version binding: required configured-source decisions are explicit: `services/quality_gate_registry/evaluator.py:49-68`. Passed gate records must bind the active registry version, declared evidence, and the raw-evidence hash for external evidence: `services/quality_gate_registry/evaluator.py:97-180`. Missing evidence and stale registry-version cases are tested: `tests/test_quality_gate_registry_evaluator.py:117-130`.
- Controlled crawl root and reparse resistance: crawl output is derived from controlled root plus validated tenant, project, and run identifiers, then required to remain inside the root: `services/quality_gate_runner/screaming_frog.py:205-229`. The real directory-link escape test verifies rejection before directory creation, preflight, or subprocess invocation and preserves the external sentinel: `tests/test_screaming_frog_quality_gate.py:102-132`.
- Durable local idempotency: the transition CLI requires a ledger, takes exclusive-create lock ownership, loads it while locked, atomically records successful new fingerprints, and releases the lock in `finally`: `services/transition_service/service.py:53-65` and `services/transition_service/service.py:349-397`. Replay, conflicting payload, lock contention, and cleanup behavior are covered by the passing transition tests, including `tests/test_operator_error_routing.py:90-113`.
- Immutable waiver resolution: all CLI inputs must resolve below the controlled root: `services/quality_gate_runner/waiver_resolution.py:32-59`. The output is derived from controlled identity, distinct from inputs, and created with exclusive mode: `services/quality_gate_runner/waiver_resolution.py:62-97` and `services/quality_gate_runner/waiver_resolution.py:161-200`. The CLI test proves raw crawl-evidence bytes remain unchanged, while collision, traversal, absolute path, directory-link escape, and pre-existing-output cases fail: `tests/test_crawl_waiver_resolution.py:133-237`.

## P3

No P3 finding verified. `git status --short --branch` shows a broad pre-existing dirty worktree, including tracked baseline modifications and untracked implementation directories. The scoped `git diff --check` command for Sprint 1 service, standard, and test paths produced no output. The unscoped `git diff --check` run reported trailing whitespace in unrelated baseline changes, so it is not evidence of a clean repository-wide worktree.

## Closure Status For Prior Findings

| Prior finding | Status | Current evidence |
| --- | --- | --- |
| 01 P1-01: Task 1.5 deliverables absent | Closed | The schema, policy, router, and tests now exist: `standards/operator/error-routing-policy.json:1-93`, `services/operator_routing/router.py:8-93`, and `tests/test_operator_error_routing.py:26-113`. P1-01 above is a separate remaining completeness failure. |
| 01 P1-02: copied Step 1 artifact accepted | Closed | Controlled storage-key resolution and exact path comparison: `services/step1_preflight/validator.py:493-531`; same-name-copy rejection: `tests/test_step1_contract_v2.py:483-500`. |
| 01 P1-03: registry evidence and active version not enforced | Closed | Enforcement: `services/quality_gate_registry/evaluator.py:147-179`; negative coverage: `tests/test_quality_gate_registry_evaluator.py:117-130`. |
| 02 P1-01: copied Step 1 artifact accepted | Closed | Same current evidence as 01 P1-02. |
| 02 P1-02: uncontrolled crawler output root and overwrite | Closed | The root and run-scoped output are derived before operational work: `services/quality_gate_runner/screaming_frog.py:536-571`; the CLI exposes controlled identity and root, not output-folder or overwrite: `services/quality_gate_runner/screaming_frog.py:625-664`. |
| 02 P2-01: idempotency was only in-memory | Closed | Durable local lock and atomic ledger replacement: `services/transition_service/service.py:53-65` and `services/transition_service/service.py:366-397`; replay and conflict test passed in the prescribed suite. |
| 02 P2-02: runnable waiver path absent | Closed | The post-crawl waiver CLI loads controlled inputs and writes a derived immutable result: `services/quality_gate_runner/waiver_resolution.py:161-200`; CLI behavior is covered at `tests/test_crawl_waiver_resolution.py:133-237`. |
| 05 P1-01: lock-contention error omitted from routing | Closed | Current catalog, policy, and real contention routing test: `services/operator_routing/router.py:35-38`, `standards/operator/error-routing-policy.json:13`, and `tests/test_operator_error_routing.py:90-113`. |
| 06 P1-01: waiver resolution could overwrite raw evidence | Closed | Derived exclusive output and collision prevention: `services/quality_gate_runner/waiver_resolution.py:62-97` and `services/quality_gate_runner/waiver_resolution.py:173-195`; preservation test: `tests/test_crawl_waiver_resolution.py:133-154`. |
| 06 P1-02: lock-contention error omitted from routing | Closed | Same current evidence as 05 P1-01. |
| 06 P2-01: real reparse escape coverage absent | Closed | The tests use a POSIX directory symlink or a real Windows `mklink /J` junction fixture: `tests/test_screaming_frog_quality_gate.py:31-46` and `tests/test_crawl_waiver_resolution.py:22-37`; the crawler escape test asserts no mkdir, preflight, or subprocess: `tests/test_screaming_frog_quality_gate.py:102-132`. |

## Task Coverage

- Task 1.1: Verified transition state, approval, gate, immutable error return, release, and durable idempotency behavior: `services/transition_service/service.py:181-397`.
- Task 1.2: Verified explicit applicability and active-registry evidence enforcement: `services/quality_gate_registry/evaluator.py:27-180`.
- Task 1.3: Verified controlled crawl output derivation and all required export/finding collection including H2, redirects, structured data, hreflang, security, HTML 4xx, and resource 4xx: `services/quality_gate_runner/screaming_frog.py:313-434` and `services/quality_gate_runner/screaming_frog.py:536-622`.
- Task 1.4: Verified canonical persisted bytes, storage-key binding, and the negative copied-file case: `services/step1_preflight/validator.py:493-559` and `tests/test_step1_contract_v2.py:420-500`.
- Task 1.5: Deliverables and the formerly omitted ledger-lock route are present, but P1-01 means the stated every-error-code requirement is not fully met: `services/operator_routing/router.py:8-93` and `standards/operator/error-routing-policy.json:4-91`.
- Task 1.6: The required five-module command is specified by the plan: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:406-415`; it passed in this review.

## Commands Executed And Outcomes

| Command | Outcome |
| --- | --- |
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 -v` | PASS: 52 tests in 2.099 seconds. This is the exact Task 1.6 prescribed command. |
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 tests.test_operator_error_routing tests.test_crawl_waiver_resolution -v` | PASS: 67 tests in 2.532 seconds. This additionally covers routing, durable lock contention, immutable waiver resolution, and reparse escape rejection. |
| `python tests/run_full_suite.py` | PASS: 7 of 7 acceptance tests and 101 discovered unit tests in 2.528 seconds. |
| `python -c "... emitted-code versus canonical-routing-inventory comparison ..."` | FAIL AS A GATE CONTROL: 101 emitted codes, 87 canonical codes, and the 14 unmapped codes listed in P1-01. |
| `git status --short --branch` | Broad pre-existing dirty worktree observed. |
| `git diff --check -- services standards/operator standards/quality standards/runtime tests/test_transition_service.py tests/test_quality_gate_registry_evaluator.py tests/test_crawl_disposition.py tests/test_screaming_frog_quality_gate.py tests/test_step1_contract_v2.py tests/test_operator_error_routing.py tests/test_crawl_waiver_resolution.py` | PASS: no whitespace output for scoped Sprint 1 paths. |

## Windows Evidence And Residual Limits

The following is direct Windows Host evidence supplied by the user, not a command executed by this Linux review: real junction/reparse tests passed 18 of 18, and the Windows Host full suite passed 7 of 7 acceptance tests plus 101 of 101 unit tests. The same user-supplied OMO full-suite evidence reports 7 of 7 acceptance tests plus 101 of 101 unit tests. The Windows branch is meaningful because it invokes `cmd /c mklink /J` with `check=True` and `shell=False`: `tests/test_screaming_frog_quality_gate.py:31-39` and `tests/test_crawl_waiver_resolution.py:22-30`.

This review executed only on Linux, where the real POSIX directory-symlink branches ran. It did not directly execute Windows junction creation, native Windows `Path.resolve()`, exclusive file creation, `os.replace()`, or lock cleanup. No real Screaming Frog executable, crawl, provider, AHD runtime, deployment, or external approval store was invoked. These are verification limits, not additional findings.

## Verdict

REQUEST_CHANGES

P1-01 violates Task 1.5's every-error-code routing requirement. All findings recorded in reports 01, 02, 05, and 06 are closed, including `ERROR_TRANSITION_LEDGER_LOCKED`, but the new independent inventory comparison identifies 14 other emitted runtime codes without a canonical route and owner type.
