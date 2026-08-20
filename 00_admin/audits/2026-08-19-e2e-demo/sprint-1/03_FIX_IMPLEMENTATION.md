# Sprint 1 Fix Implementation

- Author: Raphael Rechberger
- Date: 2026-08-19
- Scope: Sprint 1 Tasks 1.1 through 1.6 and the current specification and quality review findings.

## Changed Files

- `standards/operator/error-routing-policy.schema.json`
- `standards/operator/error-routing-policy.json`
- `standards/runtime/quality-gate-run.schema.json`
- `services/operator_routing/__init__.py`
- `services/operator_routing/router.py`
- `services/quality_gate_registry/evaluator.py`
- `services/quality_gate_runner/screaming_frog.py`
- `services/quality_gate_runner/waiver_resolution.py`
- `services/step1_preflight/validator.py`
- `services/transition_service/service.py`
- `tests/test_crawl_waiver_resolution.py`
- `tests/test_operator_error_routing.py`
- `tests/test_quality_gate_registry_evaluator.py`
- `tests/test_screaming_frog_quality_gate.py`
- `tests/test_step1_contract_v2.py`
- `tests/test_transition_service.py`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-1/03_FIX_IMPLEMENTATION.md`

## Implemented Controls

- Added a versioned error-routing policy and router with deterministic rejection of duplicate, missing, and unknown mappings.
- Replaced the policy-derived routing inventory with an independent catalog of canonical runtime error codes emitted by the allowed runtime services and operator router.
- Bound Step 1 persisted artifacts to a required controlled storage root and the resolved `artifact.storage_key` location.
- Required quality-gate evidence and active registry versions while preserving separate gate policy versions.
- Derived crawl output below the controlled evidence root from validated tenant, project, and run identifiers before preflight, directory creation, or subprocess execution. The crawl CLI no longer accepts an output folder or overwrite flag.
- Added a flock-protected durable local transition ledger for CLI replay and same-key conflict handling. This implements durable local file semantics only.
- Added immutable post-crawl waiver resolution that reads crawl evidence, validates contracts and bindings, and emits a resolved disposition with a bound quality-gate run without writing raw crawl evidence.

## Red-Green Evidence

- `python -m unittest tests.test_operator_error_routing -v` was red before the routing package existed with `ModuleNotFoundError`, then green with 5 tests.
- `python -m unittest tests.test_step1_contract_v2.Step1ContractV2Tests.test_persisted_artifact_rejects_same_name_copy_outside_storage_root -v` was red before the storage-root parameter existed with `TypeError`, then green with 1 test.
- `python -m unittest tests.test_quality_gate_registry_evaluator.QualityGateRegistryEvaluatorTests.test_missing_required_evidence_and_stale_registry_are_rejected -v` was red because the evaluator accepted the records, then green after evidence and registry-version checks.
- `python -m unittest tests.test_transition_service.TransitionServiceTests.test_cli_persists_identical_replay_and_rejects_conflicting_payload -v` was red because `--ledger` was unknown, then green with 1 test.
- `python -m unittest tests.test_screaming_frog_quality_gate.ScreamingFrogQualityGateTests.test_evidence_output_is_derived_beneath_controlled_root_and_rejects_symlink_escape -v` was red because the resolver did not exist, then green with 1 test.
- `python -m unittest tests.test_crawl_waiver_resolution -v` was red because the waiver-resolution command module did not exist, then green with 2 tests.
- `python -m unittest tests.test_operator_error_routing.OperatorErrorRoutingTests.test_policy_addition_cannot_redefine_inventory_and_is_rejected_as_unknown -v` was red because a policy-only code produced `ERROR_OPERATOR_ROUTING_MISSING` instead of an unknown-mapping rejection, then green after the independent inventory and `ERROR_OPERATOR_ROUTING_UNKNOWN_MAPPING` check.

## Executed Commands And Outcomes

- `python -m unittest tests.test_operator_error_routing -v`: PASS, 6 tests.
- `python -m unittest tests.test_transition_service tests.test_quality_gate_registry_evaluator tests.test_crawl_disposition tests.test_screaming_frog_quality_gate tests.test_step1_contract_v2 tests.test_operator_error_routing tests.test_crawl_waiver_resolution -v`: PASS, 56 tests.
- `python tests/run_full_suite.py`: PASS. Acceptance runner: 7 of 7. Unittest discovery: 90 tests.
- `lsp_diagnostics` was requested for every changed Python file. The environment reported that `basedpyright` is not installed and had previously been declined, so no LSP diagnostic result was available.
