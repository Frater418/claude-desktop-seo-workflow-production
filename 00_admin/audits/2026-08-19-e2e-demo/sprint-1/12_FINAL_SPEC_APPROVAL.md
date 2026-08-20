# Sprint 1 Final Specification Approval Review

Author: Raphael Rechberger

Audit date: 2026-08-19

Scope: Fresh independent read-only review of Sprint 1 Tasks 1.1 through 1.6, current source and tests, the Sprint 1 audit series through report 11, and the current local worktree. No network, provider, crawler, deployment, AHD runtime, or external system was invoked. The sole file written by this review is this report.

## Acceptance Basis

Tasks 1.1 through 1.6 require transition enforcement, registry applicability, crawl disposition, canonical persisted-artifact binding, complete error routing, and the integration commands at `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:314`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:341`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:354`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:382`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:393`, and `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:406`. The stated gate is no open P0 or P1 finding: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:415`.

## Findings

### P0

No P0 finding verified.

### P1

No P1 finding verified.

### P2

No P2 finding verified.

### P3

No P3 finding verified.

## Task Verification

- Task 1.1: The central service validates identity, revision, predecessor, artifact, retry, machine gates, human approval, and completion gates before returning an unchanged deep copy on error: `services/transition_service/service.py:181`, `services/transition_service/service.py:263`, `services/transition_service/service.py:303`, and `services/transition_service/service.py:317`. The CLI holds an exclusive durable ledger lock, records only successful non-replays atomically, and returns the stable contention code: `services/transition_service/service.py:53`, `services/transition_service/service.py:349`, and `services/transition_service/service.py:366`.
- Task 1.2: `when_configured` requires an explicit not-applicable decision or an available configured tool: `services/quality_gate_registry/evaluator.py:49`. Passed machine gate runs require the active registry version, declared evidence, and a raw-evidence hash for external evidence: `services/quality_gate_registry/evaluator.py:97`, `services/quality_gate_registry/evaluator.py:147`, and `services/quality_gate_registry/evaluator.py:170`.
- Task 1.3: Crawl output is derived from the controlled root and validated identifiers, with resolved containment enforced: `services/quality_gate_runner/screaming_frog.py:205`. A nonempty derived run folder fails before preflight, mkdir, or subprocess execution: `services/quality_gate_runner/screaming_frog.py:536` and `tests/test_screaming_frog_quality_gate.py:102`. The direct test asserts the stable error and that all mutation or execution seams were untouched: `tests/test_screaming_frog_quality_gate.py:119`.
- Task 1.4: The preflight rejects absolute, traversing, and resolved-escaping storage keys, requires the supplied path to equal the declared canonical path, then reads and hashes only that canonical file: `services/step1_preflight/validator.py:493`, `services/step1_preflight/validator.py:521`, and `services/step1_preflight/validator.py:532`. The same-name copied-file rejection passed in the prescribed suite: `tests/test_step1_contract_v2.py:483`.
- Task 1.5: The independent canonical catalog includes current AgentSEO, transition, crawler, waiver, and registry runtime codes: `services/operator_routing/router.py:8`. Policy validation rejects duplicate, unknown, and missing mappings: `services/operator_routing/router.py:74`. The AST inventory scans only `services/**/*.py`, not tests, standards, policies, or audit files: `tests/test_operator_error_routing.py:29`. It extracts literal codes only from runtime emission contexts, namely raises, calls to functions returning code payloads, append calls, and literal `code` dictionaries: `tests/test_operator_error_routing.py:33`, `tests/test_operator_error_routing.py:39`, and `tests/test_operator_error_routing.py:58`. The regression compares discovered emissions to the independent catalog and routes every discovered code through the policy: `tests/test_operator_error_routing.py:111`.
- Task 1.6: Both required integration commands passed in this review. Results are recorded below.

## Prior Finding Closure Status

| Prior finding | Status | Current evidence |
| --- | --- | --- |
| 01 P1-01: Task 1.5 deliverables absent | Closed | Schema, policy, router, and routing tests exist. The policy is loaded at `services/operator_routing/router.py:67` and its catalog validation is at `services/operator_routing/router.py:74`. |
| 01 P1-02 and 02 P1-01: copied Step 1 artifact accepted | Closed | Canonical-root resolution, exact path equality, byte read, and hash validation are at `services/step1_preflight/validator.py:493` and `services/step1_preflight/validator.py:506`; copied-file regression is at `tests/test_step1_contract_v2.py:483`. |
| 01 P1-03: registry evidence and active version unenforced | Closed | Required version, evidence, and external raw-evidence binding are enforced at `services/quality_gate_registry/evaluator.py:147`; negative coverage is `tests/test_quality_gate_registry_evaluator.py:117`. |
| 02 P1-02: uncontrolled crawler root and overwrite | Closed | The controlled derived root is at `services/quality_gate_runner/screaming_frog.py:205`, and the CLI exposes controlled identity rather than caller output or overwrite options at `services/quality_gate_runner/screaming_frog.py:625`. |
| 02 P2-01: ledger idempotency only in memory | Closed | The CLI requires a ledger and uses lock, load, atomic replace, replay, and conflict handling at `services/transition_service/service.py:53` and `services/transition_service/service.py:366`. |
| 02 P2-02: runnable waiver route absent | Closed | The controlled waiver CLI resolves inputs, derives output, validates identity, and writes the derived result at `services/quality_gate_runner/waiver_resolution.py:161`. |
| 05 P1-01 and 06 P1-02: ledger contention code not routed | Closed | The emitted lock code is `services/transition_service/service.py:45`; it is cataloged at `services/operator_routing/router.py:42`; the real CLI contention route is tested at `tests/test_operator_error_routing.py:172`. |
| 06 P1-01: waiver resolution could overwrite raw evidence | Closed | Inputs must resolve in-root, output is derived and distinct, existing output is rejected, and exclusive creation is used at `services/quality_gate_runner/waiver_resolution.py:45`, `services/quality_gate_runner/waiver_resolution.py:62`, `services/quality_gate_runner/waiver_resolution.py:91`, and `services/quality_gate_runner/waiver_resolution.py:173`. Raw-evidence preservation is asserted at `tests/test_crawl_waiver_resolution.py:133`. |
| 06 P2-01: real reparse escape coverage absent | Closed | The platform helper creates a Windows junction through `mklink /J` with `check=True` and `shell=False`, or a POSIX directory symlink: `tests/test_screaming_frog_quality_gate.py:31` and `tests/test_crawl_waiver_resolution.py:22`. The crawler reparse test asserts rejection before mkdir, preflight, and subprocess while retaining the outside sentinel: `tests/test_screaming_frog_quality_gate.py:124`. |
| 09 and 10 P1-01: 14 AgentSEO and validation emissions omitted from routing | Closed | The 14 codes are now cataloged at `services/operator_routing/router.py:12` and `services/operator_routing/router.py:27`; the AST production-emission comparison and per-code routing test is at `tests/test_operator_error_routing.py:111`. |
| 10 P2-01: no direct crawler output-collision test | Closed | The direct `run_crawl()` regression seeds the correctly derived output and proves `ERROR_SCREAMING_FROG_OUTPUT_NOT_EMPTY` occurs before mutation or execution: `tests/test_screaming_frog_quality_gate.py:102`. |
| 10 P3-01: derived-path test name overstated link coverage | Closed | The derived-path-only test has the accurate name `test_evidence_output_is_derived_beneath_controlled_root`: `tests/test_screaming_frog_quality_gate.py:93`. The separate real reparse test remains at `tests/test_screaming_frog_quality_gate.py:124`. |

## Commands Executed In This Linux Review

| Command | Outcome |
| --- | --- |
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 -v` | PASS: 53 tests in 2.340 seconds. This is the Task 1.6 prescribed focused command. |
| `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 tests.test_operator_error_routing tests.test_crawl_waiver_resolution -v` | PASS: 69 tests in 2.631 seconds. This additionally covers AST routing completeness, real ledger contention routing, immutable waiver resolution, collision, and reparse controls. |
| `python tests/run_full_suite.py` | PASS: 7 of 7 acceptance tests and 103 discovered unit tests in 3.059 seconds. |
| `git status --short --branch` | Completed. Broad pre-existing tracked and untracked worktree changes were observed. This review did not modify them. |
| `git diff --check -- services standards/operator standards/quality standards/runtime tests/test_transition_service.py tests/test_quality_gate_registry_evaluator.py tests/test_crawl_disposition.py tests/test_screaming_frog_quality_gate.py tests/test_step1_contract_v2.py tests/test_operator_error_routing.py tests/test_crawl_waiver_resolution.py` | PASS: no output for scoped Sprint 1 paths. |
| `rg -n "..." services tests standards/operator/error-routing-policy.json` | Not run successfully: `rg` is unavailable in this Linux environment. The required codegraph and repository read interfaces were used for source inspection instead. |

## Windows Evidence And Residual Limits

Supplied Windows Host evidence is accepted as evidence, not as a command executed in this Linux review: focused Windows results were 19 of 19 passing, and Windows full results were 7 of 7 acceptance tests plus 103 of 103 unit tests passing. Supplied OMO full results were also 7 of 7 acceptance tests plus 103 of 103 unit tests passing. This supports the Windows junction branch defined at `tests/test_screaming_frog_quality_gate.py:31` and `tests/test_crawl_waiver_resolution.py:22`.

This reviewer executed only Linux commands. The local reparse tests exercised the POSIX symlink branch, not native Windows junction creation, Windows `Path.resolve()`, exclusive file creation, `os.replace()`, or cleanup. No real Screaming Frog executable, live crawl, provider, AHD runtime, deployment, or external approval store was invoked. The broad dirty worktree prevents this review from independently proving a repository-wide unchanged AHD baseline. These are residual verification limits, not open Sprint 1 specification findings.

## Verdict

APPROVED
