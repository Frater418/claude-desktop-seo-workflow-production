# Sprint 1 Final Quality, Security And Portability Review

Author: Raphael Rechberger

Audit date: 2026-08-19

Scope: Fresh independent read-only final gate review of current Sprint 1 source, tests, policies, prior reports, and working-tree state. No network, provider, crawler, deployment, AHD runtime, or external system was invoked. The only file created by this review is this report.

## Gate Basis

Sprint 1 requires exactly one default route and owner type for every runtime error code, no open P0 or P1 findings, and an unchanged AHD baseline: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:393-415`.

## P0

No P0 findings identified.

The current crawler accepts only validated identifiers, resolves the derived output below the controlled root, and rejects resolved escapes before any crawler preflight or subprocess can run: `services/quality_gate_runner/screaming_frog.py:205-229` and `services/quality_gate_runner/screaming_frog.py:536-571`. Waiver resolution accepts only relative, resolved in-root inputs, derives a separate run-scoped output, rejects existing output, and creates it with exclusive mode: `services/quality_gate_runner/waiver_resolution.py:45-70` and `services/quality_gate_runner/waiver_resolution.py:91-97`.

## P1

### P1-01: Operator routing is incomplete for current emitted service errors

The required routing inventory is incomplete even after the prior ledger-contention fix. The canonical set contains the transition lock code at `services/operator_routing/router.py:8-38`, and the policy maps it at `standards/operator/error-routing-policy.json:5-15`. However, the current AgentSEO gateway emits seven `ERROR_AGENTSEO_*` codes at `services/agentseo_gateway/core.py:285-295`, `services/agentseo_gateway/core.py:321-352`, and `services/agentseo_gateway/core.py:355-398`; it also emits seven location, keyword, and SERP validation codes at `services/agentseo_gateway/core.py:46-111`, `services/agentseo_gateway/core.py:114-170`, and `services/agentseo_gateway/core.py:173-236`.

None of these 14 codes appears in the canonical inventory at `services/operator_routing/router.py:8-38` or its mappings at `standards/operator/error-routing-policy.json:4-91`. The current test only establishes coverage for the self-defined canonical set at `tests/test_operator_error_routing.py:30-37`; it does not discover or compare emitted codes. The local static inventory check recorded all 14 as missing from the catalog: `ERROR_AGENTSEO_API_KEY_MISSING`, `ERROR_AGENTSEO_FETCH_FAILED`, `ERROR_AGENTSEO_HTTP`, `ERROR_AGENTSEO_JOB_ID_MISSING`, `ERROR_AGENTSEO_NETWORK`, `ERROR_AGENTSEO_RESPONSE_INVALID`, `ERROR_AGENTSEO_TIMEOUT`, `ERROR_KEYWORD_INPUT_INVALID`, `ERROR_LOCATION_MISMATCH`, `ERROR_LOCATION_MISSING`, `ERROR_LOCATION_TABLE_INVALID`, `ERROR_LOCATION_TABLE_MISSING`, `ERROR_LOCATION_UNKNOWN`, and `ERROR_SERP_INPUT_INVALID`.

This leaves Task 1.5 noncompliant and prevents a final gate pass. Add each actual runtime code to the independent catalog and policy with exactly one route and owner, then make the test compare emitted service codes against that catalog.

## P2

### P2-01: Crawler output-collision rejection has source coverage but no direct execution test

`run_crawl()` rejects a pre-existing nonempty run output before preflight, directory creation, or subprocess execution at `services/quality_gate_runner/screaming_frog.py:556-564`. The current crawler tests cover hostile identifiers and an intermediate real link escape at `tests/test_screaming_frog_quality_gate.py:102-147`, but do not invoke `run_crawl()` with a nonempty correctly derived output folder or assert `ERROR_SCREAMING_FROG_OUTPUT_NOT_EMPTY`. The error is nevertheless advertised and routed at `services/operator_routing/router.py:29-32` and `standards/operator/error-routing-policy.json:27-33`.

Add a direct run-path regression that seeds the derived output, then asserts failure before preflight and subprocess execution. This is a test-evidence gap, not a demonstrated collision bypass.

## P3

### P3-01: One crawler test name overstates what it exercises

`test_evidence_output_is_derived_beneath_controlled_root_and_rejects_symlink_escape` only creates an ordinary root and asserts the derivation at `tests/test_screaming_frog_quality_gate.py:93-100`. Its name claims symlink rejection, but no link is created there. The actual reparse coverage is the separate test at `tests/test_screaming_frog_quality_gate.py:102-132`, so this does not reduce the real containment coverage. Rename the first test to state derived-path coverage only.

## Re-Verified Controls And Prior-Review Status

- Prior waiver raw-evidence overwrite finding is closed. The CLI hashes the exact raw evidence bytes, validates that hash against the crawl artifact, rejects input and output collisions, and writes only a derived exclusive output: `services/quality_gate_runner/waiver_resolution.py:108-158` and `services/quality_gate_runner/waiver_resolution.py:173-195`. The successful CLI test confirms unchanged raw bytes at `tests/test_crawl_waiver_resolution.py:133-154`; collision, traversal, symlink escape, and pre-existing-output rejection are covered at `tests/test_crawl_waiver_resolution.py:156-260`.
- Durable local idempotency is implemented with exclusive lock creation, `finally` cleanup, locked ledger loading, atomic replacement, and deterministic replay or conflict handling: `services/transition_service/service.py:53-65`, `services/transition_service/service.py:203-217`, and `services/transition_service/service.py:349-397`. The real CLI contention route is exercised at `tests/test_operator_error_routing.py:90-113`.
- Quality-gate records bind to tenant, step, human gate, artifact identity, run, active registry version, required evidence, and raw external-evidence hash where applicable: `services/quality_gate_registry/evaluator.py:121-179`. Missing evidence and stale registry rejection are exercised at `tests/test_quality_gate_registry_evaluator.py:117-130`.
- The Windows link helper takes the Windows branch through `cmd /c mklink /J` using an argument vector, `check=True`, and `shell=False`: `tests/test_crawl_waiver_resolution.py:22-30` and `tests/test_screaming_frog_quality_gate.py:31-39`. Cleanup calls `rmdir()` only on the link in the Windows branch: `tests/test_crawl_waiver_resolution.py:33-37` and `tests/test_screaming_frog_quality_gate.py:42-46`. The escape tests preserve external files after cleanup: `tests/test_crawl_waiver_resolution.py:195-220` and `tests/test_screaming_frog_quality_gate.py:102-132`. This is a real Windows junction mechanism that does not require Developer Mode or administrative rights. The supplied Windows Host evidence reports the 18 of 18 targeted tests and 7 of 7 plus 101 of 101 full suite results, including this branch. This review did not independently execute Windows and no persisted Host transcript was available to inspect.

## Commands Executed

| Command | Outcome |
| --- | --- |
| `git status --short && git diff --stat && git diff --name-only` | Completed. The worktree is broadly dirty with tracked documentation and framework changes plus untracked Sprint runtime, standards, tests, and audit content. This review did not modify those files. |
| `rg --files 00_admin/audits/2026-08-19-e2e-demo/sprint-1 services standards tests | sort` | Could not run because `rg` is not installed in this Linux environment. File inspection used the required repository read interface instead. |
| `python -m unittest tests.test_crawl_waiver_resolution tests.test_screaming_frog_quality_gate -v` | PASS: 18 tests in 0.166 seconds. This Linux run exercised the real POSIX symlink branch. |
| `python tests/run_full_suite.py` | PASS: 7 of 7 acceptance tests and 101 discovered unit tests in 2.652 seconds. |
| Static Python comparison of `services/**/*.py` emitted `ERR_*` and `ERROR_*` literals against `CANONICAL_RUNTIME_ERROR_CODES` | Found the 14 missing P1-01 codes listed above. |
| `git diff --check` | Failed because the broad pre-existing tracked diff contains trailing whitespace outside this review's Sprint 1 runtime scope, including `standards/manifest.schema.json` and `tests/acceptance-tests.md`. |

## Residual Limits

- The executed commands ran on Linux. Supplied Windows Host outcomes are accepted as Host evidence only, not as an independently reproducible execution in this review. No real Screaming Frog executable, crawl, provider, deployment, AHD runtime, or external approval system was run.
- The broad dirty worktree prevents this read-only review from independently proving the required unchanged AHD baseline. The gate basis remains at `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:406-415`.
- Test success is fixture and mocked-process evidence for crawler execution paths. It does not establish live CLI capability compatibility or production filesystem behavior beyond the supplied Windows Host results.

## Verdict

REQUEST_CHANGES
