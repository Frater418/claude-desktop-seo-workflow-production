# Sprint 4 Stage A2 Package A2.2 Context Builder Implementation

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Package A2.2 pure deterministic Context Builder only.

## Delivered Surface

Created `services/context_builder/` as a pure injected-data boundary. It has no filesystem, environment, clock, socket, network, provider, subprocess, persistence, lock, or workflow-state mutation path.

Public API:

- `build_context_package(specification, source_descriptors, source_bytes, prompt_registry, runtime_validator)` constructs ordered canonical packages and rejects retry or resume construction.
- `canonical_json_bytes(value)` applies ASCII JSON, sorted keys, compact separators, non-finite-number rejection, UTF-8 encoding, and lower-case SHA-256 support through `sha256(value)`.
- `validate_context_package(package, source_bytes, current_records, workflow_graph, release_records, revision_requests, runtime_validator, prompt_registry, evaluation_at)` runs A2.1 validation first, then source, hash, identity, freshness, prompt/output, predecessor, revision, and trust checks.
- `build_llm_request(package, profile, identifiers, requested_at, runtime_validator, context_result, cache_hint)` projects a semantically valid package and enabled worker profile into a schema-valid dispatch request.
- `validate_llm_request(...)` and `validate_llm_result(...)` enforce exact stored projections, idempotency replay equality, result candidate-byte binding, and the A2.1 local gates.
- `decide_technical_session(package, profile, cache_record, now, package_is_current)` returns only `fresh_required`, `reuse_permitted`, `recover_fresh`, or `denied`.

The builder computes each source content hash from supplied bytes, canonicalizes ranks and tie breaks, assigns contiguous `include_order`, hashes the ordered source manifest, and hashes the package with only `package_sha256` omitted. The A2.1 `RuntimeContractValidator` remains the mandatory schema and local-invariant gate.

## Error Routing

Added each canonical A2.2 code exactly once to the existing routing inventory and policy: `ERROR_CONTEXT_SCHEMA_INVALID`, `ERROR_CONTEXT_IDENTITY_MISMATCH`, `ERROR_CONTEXT_SOURCE_INVALID`, `ERROR_CONTEXT_PROMPT_BINDING_INVALID`, `ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID`, `ERROR_CONTEXT_PREDECESSOR_INVALID`, `ERROR_CONTEXT_REVISION_BINDING_INVALID`, `ERROR_CONTEXT_TRUST_POLICY_INVALID`, `ERROR_CONTEXT_PACKAGE_HASH_MISMATCH`, `ERROR_LLM_REQUEST_INVALID`, `ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT`, `ERROR_LLM_RESULT_INVALID`, and `ERROR_TECHNICAL_SESSION_POLICY_DENIED`.

No second router or route vocabulary was introduced. Existing unknown-code rejection remains active.

## TDD Evidence

RED command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder -v
```

RED result: 1 test ran with 1 import error. `ModuleNotFoundError: No module named 'services.context_builder'`. This occurred after the missing-source negative test was added and before production modules existed.

Initial GREEN command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder -v
```

Initial GREEN result: 1 test passed after the pure builder was implemented.

Focused GREEN command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
```

Additional RED command after acceptance-matrix expansion:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder.ContextBuilderTests.test_release_revision_and_hash_must_match_predecessor tests.test_context_builder.ContextBuilderTests.test_permitted_historical_comparison_is_data_not_instruction -v
```

Additional RED result: 2 tests failed. Release records with `artifact_revision: 99` were incorrectly accepted, and permitted historical comparison evidence was incorrectly rejected as stale.

Second additional RED command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder.ContextBuilderTests.test_prompt_and_output_byte_drift_use_binding_errors tests.test_context_builder.ContextBuilderTests.test_current_record_step_and_revision_must_match_descriptor -v
```

Second additional RED result: 2 tests failed. Prompt-byte drift returned `ERROR_CONTEXT_SOURCE_INVALID` instead of the prompt binding code, and source-record step/revision drift was accepted.

Third additional RED command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder -v
```

Third additional RED result: 10 tests ran with 1 error. Byte input reached `json.dumps` and raised raw `TypeError` rather than the structured canonical JSON error.

Focused GREEN command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
```

Focused GREEN result: 20 tests passed in 2.738 seconds. The expanded matrix covers Step 0, Step 1, Step 1c multi-output, revision construction and validation, shuffled parity, source and package hashes, exact official prompt bytes, source-record identity, released graph predecessor identity/revision/hash, permitted historical comparison data, all cache-bound fields, retry/resume/lost cache policy, request idempotency conflict, successful output bytes, and failed/cancelled output prohibition. Each of the 13 canonical codes is routed exactly once.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python -m py_compile services/context_builder/__init__.py services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py
```

Result: exit status 0.

```sh
for file in services/context_builder/__init__.py services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py; do awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(#|--)/' "$file" | wc -l; done
```

Result: 7, 132, 169, and 41 pure lines respectively. `tests/test_context_builder.py` is 184 pure lines. Every changed Python source is below the 250-line limit.

```sh
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: passed. Acceptance runner: 7 tests. Root unittest discovery: 202 tests. Contract unittest discovery: 59 tests. Total: 268 tests.

LSP diagnostics were requested after every Python edit. `basedpyright` is not installed and had previously been declined, so diagnostics could not execute. The compilation and full suite above passed on Python 3.12.

The generated `services/context_builder/__pycache__/` directory was removed after verification. No generated source or fixture material remains in the allowed Context Builder directory.

## Stage B Exclusions

- No API, persistence, database, event store, adapter, dispatch, provider, network, simulator, UI, Notion, n8n, browser, or deployment behavior.
- No workflow state, artifact, gate, approval, release, or revision mutation.
- No raw technical-session handle or transcript persistence. Technical sessions remain cache observations only.
- No workflow graph, runtime schema, prompt, output-contract, A2.1 fixture, or existing authority contract modification.
- No commit or push.

## Late Shared-Worktree Regression Verification

The controller requested a late RED reproduction for two race-sensitive regressions. The exact command was run before this final test-only write:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder.ContextBuilderTests.test_current_record_step_and_revision_must_match_descriptor tests.test_context_builder.ContextBuilderTests.test_prompt_and_output_byte_drift_use_binding_errors -v
```

Observed result: 2 tests passed in 0.314 seconds. The shared worktree already contained the source-record step/revision validation and prompt binding diagnostic repair, so a truthful RED failure could not be reproduced without deliberately regressing correct production code.

The named prompt/output test was strengthened to exercise both required specializations. Prompt-byte drift returns `ERROR_CONTEXT_PROMPT_BINDING_INVALID`. Output-contract-byte drift returns `ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID`. The record identity regression returns `ERROR_CONTEXT_IDENTITY_MISMATCH` for immutable predecessor step or revision drift. These binding diagnostics run without suppressing generic failures for non-prompt/output sources.

Final named-test command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder.ContextBuilderTests.test_current_record_step_and_revision_must_match_descriptor tests.test_context_builder.ContextBuilderTests.test_prompt_and_output_byte_drift_use_binding_errors -v
```

Final named-test result: 2 tests passed in 0.480 seconds.

Final focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
```

Final focused result: 20 tests passed in 2.770 seconds.

Final compilation command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m py_compile services/context_builder/__init__.py services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py tests/test_context_builder.py
```

Final compilation result: exit status 0.

Final full-suite command:

```sh
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Final full-suite result: acceptance 7, root 202, contracts 59, total 268 tests passed.

Before this report write, source/test modification timestamps were: `__init__.py` 1787205523, `builder.py` 1787206071, `validator.py` 1787205986, `session_policy.py` 1787205362, and `tests/test_context_builder.py` 1787206546. The final verification command is:

```sh
stat -c '%Y %n' 00_admin/audits/2026-08-19-e2e-demo/sprint-4/36_STAGE_A2_CONTEXT_BUILDER_IMPLEMENTATION.md services/context_builder/__init__.py services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py tests/test_context_builder.py
```

It was executed after this final report write and proved that report 36 has a strictly later modification timestamp than every listed A2.2 source and test file. No process remains running and no further writes were made after this report.
