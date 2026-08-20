# Sprint 2 Full Suite Discovery Fix

## Scope

Corrected the local full-suite runner so it runs exactly three fail-fast phases: the acceptance runner, root `tests` unittest discovery excluding `tests/contracts`, and `tests/contracts` unittest discovery. Each unittest phase reports its actual test count and fails if it discovers zero tests or if any test fails.

## Modified Paths

- `tests/run_full_suite.py`
- `tests/test_full_suite_runner.py`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-2/03_FULL_SUITE_DISCOVERY_FIX.md`

## Implementation

- `tests/run_full_suite.py` uses `sys.executable` and argument lists for all subprocesses, preserving Windows and Linux portability.
- The root suite is discovered from `tests` and filters all loaded test cases whose module file is beneath `tests/contracts`. The contracts suite is discovered only from `tests/contracts`.
- The isolated unittest phase subprocesses use `unittest.TextTestRunner`, which supplies actual execution counts. The parent parses each child phase result and prints the exact total from those executed phase counts.
- An empty root or contract suite prints an actionable `[PHASE FAILED]` message and exits nonzero. Acceptance failures and unittest failures stop subsequent phases.

## RED Evidence

Command:

```bash
python -m unittest tests/test_full_suite_runner.py -v
```

Outcome before the runner implementation: exit code 1. The new subprocess regression failed because the old runner ignored `--unittest-phase contracts` and emitted no `[PHASE PASSED] Contract unittest discovery: <count> tests` record. The assertion reported `unexpectedly None`. The old child runner still showed only acceptance plus root discovery, and its root discovery ran 104 tests with the regression skipped by its recursion guard.

## GREEN Evidence

Focused regression command:

```bash
python -m unittest tests/test_full_suite_runner.py -v
```

Outcome: exit code 0. One test passed in 0.790s. It starts the actual runner subprocess with its contracts-only phase, asserts a nonzero parsed count, and verifies real verbose unittest output includes both `test_operator_records` and `test_integration_contracts`.

OMO local container workspace command:

```bash
python tests/run_full_suite.py
```

Outcome: exit code 0. The executable reported by the runner was `/opt/heartweb-python/bin/python`, and all three phases passed:

- Acceptance runner: 7 tests.
- Root unittest discovery excluding `tests/contracts`: 104 tests in 3.691s.
- Contract unittest discovery: 35 tests in 0.517s.
- Full-suite total: 146 tests.

The contract phase verbose output included all five `test_operator_records` tests and all six `test_integration_contracts` tests. The root phase did not list either contract module.

## External Systems And Scope Control

No network, provider, crawler, deployment, worker, reviewer, commit, or external service was invoked. No Docker command was needed because the local OMO container workspace executed the suite directly. No files outside the three listed paths were created or modified.
