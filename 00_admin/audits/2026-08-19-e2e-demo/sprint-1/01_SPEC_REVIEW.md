# Sprint 1 Specification Compliance Review

- Author: Raphael Rechberger
- Audit date: 2026-08-19
- Scope: Sprint 1 Tasks 1.1 through 1.6 only, including all prior P0 and P1 findings from the two Step 1 reviews.
- Verification method: Read-only inspection of the Sprint plan, candidate classification, every current file in the required service and standards directories, the Step 1 inventory schema, relevant tests, and local test execution. No network, provider, crawler, deployment, AHD runtime, or external service was invoked.

## Acceptance Basis

Sprint 1 requires a transition-service review, registry applicability enforcement, crawl disposition coverage, persisted-artifact Step 1 preflight, error-envelope operator routing, and the listed integration suite. The gate also requires no open P0 or P1 findings: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:314`, `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:393`, and `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:415`.

The candidate checkpoint remains authoritative for this audit. It classifies the reviewed runtime components as candidate-only and specifically says that the Step 1 preflight still needs Crawl 005, gate context, and storage-binding migration: `00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md:23` and `00_admin/checkpoints/2026-08-19-pre-e2e/CANDIDATE_CLASSIFICATION.md:27`.

## Executed Tests

- `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 -v`: passed, 43 tests in 2.004 seconds.
- `python tests/run_full_suite.py`: passed, acceptance 7 of 7 and unittest discovery 77 tests in 2.154 seconds.
- Both commands are local-only for this audit. The full-suite runner starts only the acceptance runner and local unittest discovery: `tests/run_full_suite.py:25`.
- The inspected acceptance runner invokes local validators and fixture files only: `tests/run_acceptance_tests.py:24`.

## Findings

### P0

No P0 findings identified.

### P1-01: Task 1.5 error-routing deliverables are absent

Task 1.5 mandates the error-routing policy schema, policy document, router, and routing test: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:399`. None of the required paths exists: `standards/operator/error-routing-policy.schema.json` (absent), `standards/operator/error-routing-policy.json` (absent), `services/operator_routing/router.py` (absent), and `tests/test_operator_error_routing.py` (absent). This leaves no contract proving that each runtime error code has exactly one default operator route and owner type, as required by the Task 1.5 validation: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:404`.

Required fix: Create all four mandated Task 1.5 deliverables. Validate every emitted runtime error code against exactly one route and owner type, then add positive coverage for each default route and negative coverage for duplicate, missing, and unknown codes.

### P1-02: Step 1 preflight accepts an arbitrary same-named file instead of resolving the artifact storage key

The persisted-artifact entrypoint receives an operator-supplied inventory path and reads it directly: `services/step1_preflight/validator.py:493`. Its only storage-key check compares the declared key's basename with that supplied path's basename: `services/step1_preflight/validator.py:509`. Therefore a copied `topic-inventory.v1.json` at any location can satisfy the check even when it is not the canonical artifact at the artifact record's declared `storage_key`, contrary to Task 1.4's requirement to validate stored bytes and storage binding: `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md:384`.

Required fix: Resolve the canonical artifact exclusively from the declared `artifact.storage_key` using the configured tenant storage root. Reject a supplied path that is not that resolved path, and add a negative CLI test using byte-identical copied content at a same-named noncanonical location.

### P1-03: The registry evaluator treats a bare passed gate record as satisfying registry evidence requirements

The registry declares concrete evidence required for the configured independent-search gate: `standards/quality/quality-gate-registry.json:51`. The evaluator accepts a record based only on gate identity, tenant, step, human gate, result, and artifact binding: `services/quality_gate_registry/evaluator.py:121`. It never evaluates the selected gate's `evidence_required` fields or confirms that the record policy version is the active registry version. The current positive evaluator test supplies minimal records without those evidence fields and still expects validity: `tests/test_quality_gate_registry_evaluator.py:41`.

Required fix: Extend the quality-gate-run contract and evaluator so each applicable blocking gate verifies its declared evidence requirements and active policy version before a `passed` record can satisfy the gate. Add negative tests for missing evidence, stale policy version, and configured-source evidence that has no raw-evidence binding.

### P2

No P2 findings identified.

### P3

No P3 findings identified.

## Prior P0 and P1 Closure Status

| Prior finding | Status | Current evidence |
| --- | --- | --- |
| 04 P0-01, no transition service enforcing Gate 1 lifecycle | Closed | The transition service validates approval identity and currentness before approval: `services/transition_service/service.py:97`; completion also requires a passed human gate run: `services/transition_service/service.py:278`. |
| 04 P1-01, missing Step 1 preflight CLI | Closed | The persisted-artifact CLI requires bundle and inventory inputs and returns a result-based exit code: `services/step1_preflight/validator.py:542`. |
| 04 P1-02, incomplete crawl checks | Closed | The crawl schema requires final URL and all required finding classes: `standards/quality/screaming-frog-crawl.schema.json:7` and `standards/quality/screaming-frog-crawl.schema.json:48`. |
| 04 P1-03, registry policy not evaluated by preflight | Partially closed | Preflight now calls the registry evaluator: `services/step1_preflight/validator.py:436`; P1-03 above remains because required gate evidence and policy-version binding are not evaluated. |
| 04 P1-04, copied bundle bytes instead of stored artifact | Partially closed | Byte and hash comparison exists: `services/step1_preflight/validator.py:518`; P1-02 above remains because the canonical storage key is not resolved. |
| 05 P1-01, blocking crawl gate passes recorded critical findings | Closed | The disposition policy blocks internal HTML 4xx and requires a revision-bound waiver for resource 4xx: `standards/quality/crawl-disposition-policy.json:6`. |
| 05 P1-02, direct Step 1 provider path | Closed | Prompt 1 forbids direct provider, AgentSEO, and web-search calls and requires a versioned gateway record: `prompts/1-pillar-identifikation.xml.md:43`. |

## Positive Controls

- The transition service preserves the input run on errors by returning a deep copy rather than a partial mutation: `services/transition_service/service.py:292`.
- The evaluator requires an explicit not-applicable decision when no configured source is present: `services/quality_gate_registry/evaluator.py:49`.
- Crawl evidence uses a versioned policy disposition and makes a blocked disposition fail the crawl evidence: `services/quality_gate_runner/screaming_frog.py:436`.
- Step 1 preflight verifies canonical JSON, immutable Step 0 lineage, gate context, crawl disposition, and external Gate 1 separation: `services/step1_preflight/validator.py:107`, `services/step1_preflight/validator.py:252`, and `services/step1_preflight/validator.py:486`.
- The Step 1 inventory schema closes identity, evidence, pillar count, and cluster count: `standards/outputs/step-1-topic-inventory.schema.json:7` and `standards/outputs/step-1-topic-inventory.schema.json:37`.

## Verdict

REQUEST_CHANGES

Sprint 1 cannot pass its gate while P1-01 through P1-03 remain open. The green local suites are positive evidence only and do not close the missing Task 1.5 delivery, canonical storage-key resolution, or registry evidence-enforcement gaps.
