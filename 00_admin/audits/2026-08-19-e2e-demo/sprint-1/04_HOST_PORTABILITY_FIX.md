# Sprint 1 Host Portability Fix

Autor: Raphael Rechberger

## Scope

The durable local idempotency-ledger lock now uses only the Python standard library. It acquires its lock file through atomic exclusive creation, fails immediately on contention, returns exit code 2 with `ERROR_TRANSITION_LEDGER_LOCKED`, and removes the lock in `finally` after normal or handled exceptional processing paths.

## Changed Files

1. `services/transition_service/service.py`
2. `tests/test_transition_service.py`
3. `tests/test_prompt0_contract.py`
4. `tests/test_step1_renderer.py`
5. `00_admin/audits/2026-08-19-e2e-demo/sprint-1/04_HOST_PORTABILITY_FIX.md`

## Red Evidence

Command executed before the production change:

```text
python -m unittest tests.test_transition_service.TransitionServiceTests.test_module_imports_when_fcntl_is_unavailable tests.test_transition_service.TransitionServiceTests.test_durable_ledger_lock_releases_after_processing_exception tests.test_transition_service.TransitionServiceTests.test_cli_fails_fast_when_ledger_lock_is_active tests.test_transition_service.TransitionServiceTests.test_cli_persists_identical_replay_and_rejects_conflicting_payload -v
```

Result: 2 failures and 2 errors. The guarded import raised `ModuleNotFoundError: fcntl`; the lock seam was absent; and replay/conflict execution under blocked `fcntl` import failed before CLI processing.

## Green Evidence

Commands executed after the production change:

```text
python -m unittest tests.test_transition_service tests.test_prompt0_contract tests.test_step1_renderer -v
python tests/run_full_suite.py
python -m services.transition_service.service --help
```

Results:

1. Focused run: 23 tests passed.
2. Full suite: 7 of 7 acceptance tests passed and 93 unittest-discovery tests passed.
3. CLI help rendered its request, output, and ledger options. It also emitted the existing `runpy` runtime warning caused by the package importing the service before module execution.
4. Regression coverage blocks `fcntl` imports for module import and CLI replay/conflict behavior, proves active lock contention returns exit code 2 with the stable error code, and proves lock cleanup after a processing exception.
5. Prompt 0 and Step 1 renderer dash assertions now use Unicode code points instead of literal dash characters.

## Host Limitation

These tests ran in a Linux container. Linux container tests cannot prove native Windows runtime behavior. The regression coverage proves the service no longer imports `fcntl` and uses only standard-library exclusive file creation, but native Windows execution still requires independent Windows host evidence.

## Diagnostics

`lsp_diagnostics` was requested for every changed Python file. The configured `basedpyright` server is not installed because installation was previously declined, so no LSP diagnostics were available.
