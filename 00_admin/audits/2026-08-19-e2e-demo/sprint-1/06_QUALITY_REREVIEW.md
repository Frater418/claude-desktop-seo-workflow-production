# Sprint 1 Quality, Security And Portability Re-Review

Author: Raphael Rechberger

Audit date: 2026-08-19

Scope: Independent read-only review of the current Sprint 1 implementation, contracts, tests, and working-tree diff state. No network, provider, crawler, deployment, or AHD runtime was invoked.

## Findings

### P0

No P0 findings identified.

### P1-01: Waiver resolution can overwrite immutable raw crawl evidence

`waiver_resolution.main()` accepts an unrestricted `--output` path at `services/quality_gate_runner/waiver_resolution.py:87` and writes to it directly at `services/quality_gate_runner/waiver_resolution.py:98`. It does not reject an output equal to `--crawl-evidence`, constrain it beneath a controlled derived root, or use a non-overwriting creation mode. Thus an invocation can read and hash raw evidence, then replace that same raw-evidence file with the resolved result. This defeats the claimed post-crawl raw-evidence immutability despite hash and artifact binding checks at `services/quality_gate_runner/waiver_resolution.py:37` and `services/quality_gate_runner/waiver_resolution.py:89-96`.

Required change: derive a distinct resolution path beneath a controlled root, reject collisions with every input and existing raw-evidence location, and add CLI tests for same-path, symlink, traversal, and pre-existing-output rejection.

### P1-02: The error-routing catalog omits an emitted lock-contention error

The durable lock emits `ERROR_TRANSITION_LEDGER_LOCKED` at `services/transition_service/service.py:50` and returns it as the documented lock-contention outcome at `services/transition_service/service.py:393-395`. That code is absent from the independent canonical catalog at `services/operator_routing/router.py:8-38` and therefore absent from the one-to-one policy mappings at `standards/operator/error-routing-policy.json:4-90`. A valid policy cannot route this normal runtime failure because `route_error()` reaches its unknown-code path at `services/operator_routing/router.py:86-93`. The catalog-completeness claim is consequently false for an actual emitted code.

Required change: add the lock error to the independent catalog and policy with one owner and route, then add an end-to-end assertion that the real contention result is routed.

### P2-01: The claimed symlink-escape test does not exercise a symlink or crawler execution path

`test_evidence_output_is_derived_beneath_controlled_root_and_rejects_symlink_escape` creates only a normal directory and checks the derived path at `tests/test_screaming_frog_quality_gate.py:73-80`. It creates no symlink, calls no `run_crawl()`, and verifies neither preflight nor subprocess non-invocation. The hostile-ID test is a useful separate control at `tests/test_screaming_frog_quality_gate.py:82-95`, but it does not substantiate the symlink claim. Source containment is present in `services/quality_gate_runner/screaming_frog.py:205-229`, and operational writes are derived and reject nonempty output at `services/quality_gate_runner/screaming_frog.py:556-571`; this is a coverage and evidence-quality gap, not a demonstrated bypass.

Required change: construct intermediate symlink escapes and assert rejection before directory creation, preflight, and subprocess execution using a fake binary.

### P3

No P3 findings identified.

## Controls Re-Verified

- Step 1 resolves a relative storage key beneath a supplied controlled root, rejects absolute, traversal, and resolved escaping paths, and requires equality with the supplied inventory path: `services/step1_preflight/validator.py:493-531`. It then reads and hashes only that canonical path: `services/step1_preflight/validator.py:532-558`.
- The Screaming Frog CLI accepts a controlled evidence root and identifiers, not an operator output-folder or overwrite flag: `services/quality_gate_runner/screaming_frog.py:625-664`. The execution path does not request `--overwrite`: `services/quality_gate_runner/screaming_frog.py:563-571`.
- Durable local replay and conflict checks are protected by exclusive lock creation and cleanup in `finally`: `services/transition_service/service.py:53-65`, with the ledger atomically replaced while held: `services/transition_service/service.py:375-392`. There is no `fcntl` import in this module.
- Registry evaluation binds passed records to the active registry version, required evidence, and raw-evidence hash where required: `services/quality_gate_registry/evaluator.py:147-179`.

## Commands Executed

| Command | Result |
| --- | --- |
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 tests.test_operator_error_routing tests.test_crawl_waiver_resolution -v` | PASS: 59 tests in 2.295 seconds. |
| `python tests/run_full_suite.py` | PASS: 7 of 7 acceptance tests and 93 discovered unit tests in 2.782 seconds. |
| `git diff --no-index --check /dev/null services/transition_service/service.py` | No whitespace errors in the untracked transition-service file. |
| `git diff --no-index --check /dev/null services/quality_gate_runner/waiver_resolution.py` | No whitespace errors in the untracked waiver-resolution file. |
| `git diff --check` | Failed on pre-existing broad working-tree changes, reporting trailing whitespace in files outside the Sprint 1 runtime review scope. |

## Residual Risks And Verification Limits

- All executed tests ran in a Linux container. The blocked-`fcntl` import test demonstrates Linux-host portability coverage at `tests/test_transition_service.py:233-241`, but native Windows filesystem, path, exclusive-create, replace, and cleanup behavior remains unverified.
- No real Screaming Frog executable, crawl, provider, AHD runtime, deployment, or external approval store was invoked. The green suites are fixture and mocked local evidence only.
- The waiver-resolution tests exercise the pure resolver only at `tests/test_crawl_waiver_resolution.py:37-51`; they do not invoke its CLI or assert output containment and raw-file preservation.

## Verdict

REQUEST_CHANGES
