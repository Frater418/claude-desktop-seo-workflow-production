# Sprint 1 Independent Specification Re-review

- Author: Raphael Rechberger
- Audit date: 2026-08-19
- Scope: Read-only re-review of Sprint 1 Tasks 1.1 through 1.6, all P1 and P2 findings in `01_SPEC_REVIEW.md` and `02_QUALITY_REVIEW.md`, and the historical Windows `fcntl` failure.
- Method: Current source, schemas, tests, worktree inspection, and local tests only. No network, provider, crawler, deployment, or AHD runtime tool was invoked.

## P0

No P0 finding verified.

## P1

### P1-01: Error-routing policy omits an emitted transition error code

Task 1.5 requires exactly one default route and owner type for every runtime error code: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:393` and `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:404`.

The transition CLI emits stable `ERROR_TRANSITION_LEDGER_LOCKED` on durable-ledger contention: `services/transition_service/service.py:45` through `services/transition_service/service.py:50` and `services/transition_service/service.py:393` through `services/transition_service/service.py:395`. That code is absent from the independent canonical inventory: `services/operator_routing/router.py:8` through `services/operator_routing/router.py:39`, and therefore absent from the policy mappings: `standards/operator/error-routing-policy.json:4` through `standards/operator/error-routing-policy.json:91`. The routing test validates only codes already present in that inventory: `tests/test_operator_error_routing.py:24` through `tests/test_operator_error_routing.py:31`.

Direct local check outcome: `ledger_code_in_inventory=False`, `ledger_code_in_policy=False`, `policy_valid=True`. The policy is internally consistent but incomplete against emitted runtime behavior. This leaves Task 1.5 noncompliant.

## P2

All prior P2 findings are closed.

- 02 P2-01, durable local idempotency: Closed. The CLI requires a ledger, exclusively creates a lock file, loads it while locked, atomically records a successful non-replay fingerprint, and returns a defined contention error: `services/transition_service/service.py:53` through `services/transition_service/service.py:65` and `services/transition_service/service.py:366` through `services/transition_service/service.py:397`. CLI replay, conflict, contention, and exception-cleanup tests pass: `tests/test_transition_service.py:243` through `tests/test_transition_service.py:270` and `tests/test_transition_service.py:298` through `tests/test_transition_service.py:322`.
- 02 P2-02, controlled post-crawl waiver: Closed. Resolution validates immutable crawl evidence and waiver contracts, binds the raw-evidence hash to the crawl artifact, then evaluates only the supplied waiver against the active policy: `services/quality_gate_runner/waiver_resolution.py:20` through `services/quality_gate_runner/waiver_resolution.py:51`. It returns a derived disposition and bound quality-gate run: `services/quality_gate_runner/waiver_resolution.py:52` through `services/quality_gate_runner/waiver_resolution.py:78`. The command reads raw evidence bytes and writes only its separate output: `services/quality_gate_runner/waiver_resolution.py:89` through `services/quality_gate_runner/waiver_resolution.py:99`. Valid, expired, hash-mismatched, and disallowed cases are covered: `tests/test_crawl_waiver_resolution.py:37` through `tests/test_crawl_waiver_resolution.py:51`.

Task coverage confirmed outside the outstanding routing gap:

- 1.1: State transitions, unchanged error returns, gate enforcement, approval binding, and durable local replay semantics are implemented at `services/transition_service/service.py:181` through `services/transition_service/service.py:346` and `services/transition_service/service.py:366` through `services/transition_service/service.py:397`.
- 1.2: Applicability requires explicit configured-source decisions, and gate runs require active registry versions, declared evidence, and external raw-evidence binding: `services/quality_gate_registry/evaluator.py:49` through `services/quality_gate_registry/evaluator.py:68` and `services/quality_gate_registry/evaluator.py:97` through `services/quality_gate_registry/evaluator.py:180`.
- 1.3: Crawl output is derived below a validated controlled root: `services/quality_gate_runner/screaming_frog.py:205` through `services/quality_gate_runner/screaming_frog.py:229` and `services/quality_gate_runner/screaming_frog.py:536` through `services/quality_gate_runner/screaming_frog.py:622`. The regression suite covers containment and symlink escape: `tests/test_screaming_frog_quality_gate.py` as executed below.
- 1.4: Step 1 resolves the artifact only from `storage_key` beneath the supplied controlled storage root, rejects supplied-path mismatch, then hashes the resolved bytes: `services/step1_preflight/validator.py:493` through `services/step1_preflight/validator.py:559`. The same-name out-of-root copy is tested: `tests/test_step1_contract_v2.py` as executed below.
- 1.6: The prescribed five-suite command is defined at `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:406` through `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:415`; the expanded current Sprint command and full suite both passed.

Prior P1 closure status:

| Prior finding | Status | Current evidence |
| --- | --- | --- |
| 01 P1-01, Task 1.5 deliverables absent | Partially closed | Schema, policy, router, and tests now exist: `standards/operator/error-routing-policy.json:1`, `services/operator_routing/router.py:8`, and `tests/test_operator_error_routing.py:20`. P1-01 above remains because one emitted code lacks a route. |
| 01 P1-02 and 02 P1-01, arbitrary copied Step 1 artifact | Closed | Canonical storage-key resolution and exact supplied-path comparison: `services/step1_preflight/validator.py:493` through `services/step1_preflight/validator.py:531`. |
| 01 P1-03, gate evidence and active registry version not enforced | Closed | Active registry-version, evidence, and raw-evidence checks: `services/quality_gate_registry/evaluator.py:147` through `services/quality_gate_registry/evaluator.py:179`. |
| 02 P1-02, unrestricted crawler output root and overwrite path | Closed | Run-scoped derivation occurs before output creation, and the crawl CLI exposes no output-folder or overwrite argument: `services/quality_gate_runner/screaming_frog.py:556` through `services/quality_gate_runner/screaming_frog.py:571` and `services/quality_gate_runner/screaming_frog.py:625` through `services/quality_gate_runner/screaming_frog.py:664`. |

## P3

No Sprint 1 P3 finding verified. `git status --short` showed a broad pre-existing dirty worktree. `git diff --check` reported trailing whitespace in unrelated tracked baseline files, so it cannot serve as a clean-worktree assertion for this review.

## Local Commands And Outcomes

- `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 tests.test_operator_error_routing tests.test_crawl_waiver_resolution -v`: PASS, 59 tests.
- `python tests/run_full_suite.py`: PASS, acceptance 7 of 7 and unittest discovery 93 of 93.
- `grep -R -n --include='*.py' 'fcntl' services tests`: only the deliberate unavailable-`fcntl` test seam and test name appeared at `tests/test_transition_service.py:20` through `tests/test_transition_service.py:24` and `tests/test_transition_service.py:233`.
- `python -c "..."` routing inventory check: `ERROR_TRANSITION_LEDGER_LOCKED` absent from both inventory and policy while `validate_policy(policy).valid` returned true.
- `git diff --check`: reported trailing whitespace in unrelated existing tracked files.

The historical `fcntl` import failure is closed for portable-source behavior. `services/transition_service/service.py:8` through `services/transition_service/service.py:19` contains no `fcntl` import, and the import-blocking regression test passes: `tests/test_transition_service.py:20` through `tests/test_transition_service.py:24` and `tests/test_transition_service.py:233` through `tests/test_transition_service.py:241`. Native Windows execution was not observed. All commands ran on this Linux host, so native Windows runtime behavior remains an external verification limit.

## Final Verdict

REQUEST_CHANGES
