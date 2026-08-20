# Predecessor Lineage Fix

## Scope

Added `services/preflight_common` as the reusable runtime artifact and release lineage boundary. The boundary rejects non-awaiting-gate candidates, missing predecessor records, runtime-schema-invalid records, release status or gate mismatches, identity mismatches, and omitted predecessor source artifacts.

## TDD Evidence

RED command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common -v
```

Initial result: import failure for the not-yet-created `services.preflight_common.boundary` module.

GREEN command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common -v
```

Result: 2 tests passed.

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_preflight_common tests.test_step1b_contract tests.test_step1c_contract tests.test_step2_contract tests.test_step3_contract tests.test_step3b_contract tests.test_step4a_contract tests.test_step4b_contract tests.test_operator_error_routing -v
```

Result: 39 tests passed.

Full command:

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: acceptance 7, root discovery 150, contract discovery 37, total 194 tests passed.

## Routing

The five `ERROR_PREFLIGHT_*` codes are canonical and each has one `revision_required` operator mapping.

## Environment Limits

Python 3.12 was available. Python 3.11 and basedpyright were unavailable in this environment.
