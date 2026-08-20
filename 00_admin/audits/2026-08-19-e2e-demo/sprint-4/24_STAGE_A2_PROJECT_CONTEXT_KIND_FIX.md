# Sprint 4 Stage A2 Project Context Source Kind Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Post-report-22 P1 local Context Package invariant remediation only.

## Verdict

PASS

The schema-first production `RuntimeContractValidator` now requires the source selected by `project_context.source_id`, revision, logical reference, and content SHA-256 to have the source kind required by `project_context.binding_mode`.

`project_intake` binds only a `project_intake` source. `project_v2` binds only a `project_v2` source. The validator returns the deterministic immutable `LLM_RUNTIME_CONTEXT_INVALID` error at `/project_context/source_id` when that selected source kind is inconsistent.

## RED Evidence

The two direct regressions were added before production validation changed. Both invoke the production validator against schema-valid, in-memory fixture mutations.

```sh
python -m unittest -v tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_project_context_source_kind_swaps
```

Observed RED result: 1 test ran in 0.109s and failed at the Step 0 assertion because the validator returned `valid=True` for a `project_intake` binding pointing to an `official_prompt` source while the valid intake source remained present. The Step 1+ `released_predecessor` case is in the same direct regression method and retains the valid `project_v2` source.

## GREEN Evidence

```sh
python -m unittest -v tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_project_context_source_kind_swaps
```

Observed GREEN result: 1 test ran in 0.155s and passed. Both source-kind swaps returned exactly one `LLM_RUNTIME_CONTEXT_INVALID` error at `/project_context/source_id`. Repeating the Step 0 validation returned an equal result, and assigning to its error code raised `FrozenInstanceError`.

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Observed focused result: 17 tests ran in 0.389s and passed. Legitimate distinct runtime records, including the valid Step 0 and Step 1+ Context Packages, remain valid.

```sh
python tests/run_full_suite.py
```

Observed OMO full-suite result: 253 tests passed. Acceptance runner: 7 tests. Root unittest discovery: 188 tests. Contract unittest discovery: 58 tests.

## Boundary

This change is local invariant validation only. It adds no source resolution, canonical package construction, cache or provider policy, I/O, external lookup, routing, or A2.2 behavior.

## Diagnostics

Diagnostics were requested for both modified Python files. The local `basedpyright` language server is not installed and was previously declined, so no LSP diagnostics could run. The focused and OMO full suites passed on the available local Python runtime.
