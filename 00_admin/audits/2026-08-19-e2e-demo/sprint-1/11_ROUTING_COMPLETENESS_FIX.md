# Sprint 1 Routing Completeness Fix

Author: Raphael Rechberger

Date: 2026-08-19

## Scope

This fix closes the routing-completeness finding from reports 09 and 10 and adds direct execution evidence for the existing Screaming Frog output-collision guard. No provider, real crawler, deployment, AHD runtime, or external system was invoked.

## Changed Files

- `services/operator_routing/router.py`: Added the 14 currently emitted AgentSEO, keyword, SERP, and location runtime codes to the independent `CANONICAL_RUNTIME_ERROR_CODES` catalog.
- `standards/operator/error-routing-policy.json`: Added exactly one route and owner mapping for each of the 14 catalog additions.
- `tests/test_operator_error_routing.py`: Added an AST-based production-services inventory regression. It scans only `services/**/*.py`, accepts literals only in runtime emission contexts, requires each discovered code to belong to the independent canonical catalog, and routes every discovered code through the policy.
- `tests/test_screaming_frog_quality_gate.py`: Added a direct `run_crawl()` nonempty derived-output regression and renamed the derived-path-only test without changing the separate real reparse escape test.
- `00_admin/audits/2026-08-19-e2e-demo/sprint-1/11_ROUTING_COMPLETENESS_FIX.md`: This report.

## Red-Green Evidence

### Routing Completeness

Red command:

```text
python -m unittest tests.test_operator_error_routing.OperatorErrorRoutingTests.test_every_emitted_runtime_error_code_is_canonical_and_routed -v
```

Outcome: FAIL, 1 test in 0.157 seconds. The AST inventory found exactly these 14 emitted codes missing from the canonical catalog: `ERROR_AGENTSEO_API_KEY_MISSING`, `ERROR_AGENTSEO_FETCH_FAILED`, `ERROR_AGENTSEO_HTTP`, `ERROR_AGENTSEO_JOB_ID_MISSING`, `ERROR_AGENTSEO_NETWORK`, `ERROR_AGENTSEO_RESPONSE_INVALID`, `ERROR_AGENTSEO_TIMEOUT`, `ERROR_KEYWORD_INPUT_INVALID`, `ERROR_LOCATION_MISMATCH`, `ERROR_LOCATION_MISSING`, `ERROR_LOCATION_TABLE_INVALID`, `ERROR_LOCATION_TABLE_MISSING`, `ERROR_LOCATION_UNKNOWN`, and `ERROR_SERP_INPUT_INVALID`.

Green command:

```text
python -m unittest tests.test_operator_error_routing -v
```

Outcome: PASS, 8 tests in 0.221 seconds. The policy schema passed, every canonical code had one mapping, and every AST-discovered runtime emission routed through the policy.

### Direct Crawler Collision Coverage

Command:

```text
python -m unittest tests.test_screaming_frog_quality_gate.ScreamingFrogQualityGateTests.test_run_crawl_rejects_nonempty_derived_output_before_mutation_or_execution -v
```

Outcome: PASS, 1 test in 0.003 seconds. The seeded, correctly derived nonempty output folder raised `ERROR_SCREAMING_FROG_OUTPUT_NOT_EMPTY`; patched `preflight`, `Path.mkdir`, and `subprocess.run` were not called.

The collision test was green on its first execution because report 10 correctly identified a test-evidence gap, not a missing production guard. No false red phase was manufactured and no crawler production code was changed.

Focused suite command:

```text
python -m unittest tests.test_screaming_frog_quality_gate -v
```

Outcome: PASS, 11 tests in 0.033 seconds. The independent real intermediate reparse escape test remains present and passing.

## Full Verification

```text
python tests/run_full_suite.py
```

Outcome: PASS. Acceptance suite: 7 of 7 tests. Unit discovery: 103 tests in 2.923 seconds.

`lsp_diagnostics` was requested for each changed Python file. The environment could not run it because basedpyright is not installed and installation was previously declined.
