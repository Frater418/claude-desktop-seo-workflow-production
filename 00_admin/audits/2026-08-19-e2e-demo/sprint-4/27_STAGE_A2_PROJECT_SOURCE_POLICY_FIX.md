# Sprint 4 Stage A2 Project Source Policy Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Narrow A2.1 selected-project-source validation correction from Report 25.

## Changed Boundary

`RuntimeContractValidator.validate` still validates the Draft 2020-12 schema before running local production invariants. After schema validation, `_context_errors` resolves the one descriptor selected by `project_context` and applies only these cross-field rules:

- Selected `project_intake` requires `trust_level: trusted`.
- Selected `project_v2` requires `source_status: released`.

Violations return exactly one `LLM_RUNTIME_CONTEXT_INVALID` error at `/sources/<index>/trust_level` or `/sources/<index>/source_status`. The schema now permits an untrusted intake descriptor and a historical descriptor to reach this selected-source invariant. It continues to reject malformed structures before production invariants and continues to prohibit superseded sources at the schema boundary. Untrusted evidence still requires its reason and permitted-use fields.

The invariant does not constrain values on non-selected source descriptors. Direct tests keep `operator_asserted` plus `active`, and `not_applicable` plus `rejected`, valid on the non-selected released-predecessor source.

## TDD Evidence

RED command:

```sh
python -m unittest -v tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_selected_project_source_policy_values tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_accepts_nonselected_source_policy_values
```

RED outcome: 2 tests ran in 0.155s. The six negative subtests failed for the correct pre-fix behavior. `operator_asserted`, `not_applicable`, `active`, and `rejected` incorrectly returned valid. `untrusted` and `historical` were incorrectly stopped by generic `LLM_RUNTIME_SCHEMA_INVALID` errors instead of the required selected-source context error. The non-selected-source test passed.

The direct production-validator probes now cover:

- Step 0 selected intake: `operator_asserted`, `not_applicable`, and `untrusted` reject with `LLM_RUNTIME_CONTEXT_INVALID /sources/0/trust_level`.
- Step 1 selected Project V2: `active`, `rejected`, and `historical` reject with `LLM_RUNTIME_CONTEXT_INVALID /sources/0/source_status`.

GREEN targeted command: the same exact command. Result: 2 tests ran in 0.156s, `OK`.

GREEN focused command:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Result: 19 tests ran in 0.522s, `OK`.

OMO full-suite command:

```sh
python tests/run_full_suite.py
```

Result: `FULL SUITE PASSED`. Acceptance runner: 7 tests. Root unittest discovery: 190 tests. Contract unittest discovery: 58 tests. Total: 255 tests.

## Explicit A2.2 Exclusions

No external source lookup, builder or resolver, session policy, routing, API, provider, cache or freshness resolution, dispatch, graph lookup, release lookup, state mutation, fixture modification, network activity, or git write was added. This correction remains a pure A2.1 schema-plus-local-validator boundary.
