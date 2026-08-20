# Mandatory Lineage Fix

Date: 2026-08-19

## Scope

Public operational preflights for Steps 1B, 1C, 2, 3, 3B, 4A, and 4B now always invoke the common lineage boundary. Omitted predecessor artifact or release records return `ERROR_PREFLIGHT_PREDECESSOR_RELEASE_INVALID` and cannot return `valid: true`.

Candidate-only validators now own closed output-schema validation, local semantics, and renderer input validation. Renderers call those candidate-only entrypoints and do not need runtime predecessor records.

The common boundary validates candidate output schemas with `FormatChecker`, canonical Project V2 identity and deployment resolution, runtime artifact and release schemas, released predecessor identity, revision, hash, source-artifact binding, and `awaiting_gate` status. It does not mutate transition state.

## TDD Evidence

RED command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common -v
```

RED result: 3 tests run, 3 failures. The first implementation returned `ERROR_PREFLIGHT_CANDIDATE_INVALID` before the required missing-predecessor error for Steps 3B, 4A, and 4B.

GREEN command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common -v
```

GREEN result: 4 tests passed. The table-driven regressions cover omitted predecessor records and complete non-AHD operational bundles for all seven public preflights.

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common tests.test_step1b_contract tests.test_step1c_contract tests.test_step2_contract tests.test_step3_contract tests.test_step3b_contract tests.test_step4a_contract tests.test_step4b_contract -v
```

Focused result: 33 tests passed.

Full command:

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Full result: acceptance 7 of 7, root discovery 158, contract discovery 37, total 202 tests passed.

## Files Changed

- `services/preflight_common/boundary.py`
- `services/step1b_preflight/validator.py`
- `services/step1b_preflight/render.py`
- `services/step1c_preflight/validator.py`
- `services/step1c_preflight/render.py`
- `services/step2_preflight/validator.py`
- `services/step2_preflight/render.py`
- `services/step3_preflight/validator.py`
- `services/step3_preflight/render.py`
- `services/step3b_preflight/validator.py`
- `services/step3b_preflight/render.py`
- `services/step4a_preflight/validator.py`
- `services/step4a_preflight/render.py`
- `services/step4b_preflight/validator.py`
- `services/step4b_preflight/render.py`
- `tests/test_preflight_common.py`
- `tests/test_step1b_contract.py`
- `tests/test_step1c_contract.py`
- `tests/test_step2_contract.py`
- `tests/test_step3_contract.py`
- `tests/test_step3b_contract.py`
- `tests/test_step4a_contract.py`
- `tests/test_step4b_contract.py`

## Limits

- Python 3.12 executed the tests. Python 3.11 was not available for execution.
- No network, provider, crawl, deployment, commit, or push operation was run.
- No language server diagnostics were run because the requested execution scope was limited to local Python unittest.
