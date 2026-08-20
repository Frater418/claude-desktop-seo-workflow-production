# Sprint 4 Stage A2 Package A2.1 Runtime Contract Quality Review

Date: 2026-08-20
Reviewer: Independent read-only quality gate
Scope: Package A2.1 only. This review covers the six new runtime schemas, official prompt registry, A2.1 fixtures, and focused contract tests. It does not approve or require the A2.2 context-builder, cross-record resolver, canonical hash builder, cache policy evaluator, API, provider, event, simulator, UI, or routing work.

## Decision

REQUEST_CHANGES

The delivered files are additive and the recorded registry currently binds all nine prompts and their output contracts correctly. However, the A2.1 schemas and tests accept several malformed record shapes that contradict the controller's stated closed-runtime-contract boundary. These are structural false greens, not deferred A2.2 semantic behavior. A2.2 can enforce repository lookup, byte verification, graph edges, cache equality, freshness, and source resolution. It cannot retroactively make an already schema-valid package unambiguous when the A2.1 record omits source ownership, permits duplicate required slots, or permits ambiguous logical references.

## Evidence Reviewed

- Governing decision: `00_admin/DECISIONS.md`, DEC-0019.
- Prior A2 reports: `15_STAGE_A2_RUNTIME_CONTRACT_RESEARCH.md`, `16_STAGE_A2_CONTEXT_BUILDER_RESEARCH.md`, `17_STAGE_A2_IMPLEMENTATION_PLAN.md`, and `18_STAGE_A2_RUNTIME_CONTRACT_IMPLEMENTATION.md`.
- Current diff and untracked A2.1 inventory. No source files were modified by this review.
- All nine files under `prompts/`, the workflow graph, `standards/manifest.schema.json`, all eleven output schemas, every new runtime schema and registry, all eleven A2.1 fixtures, and `tests/contracts/test_llm_runtime_contracts.py`.

## Validation Evidence

1. `python -m unittest tests/contracts/test_llm_runtime_contracts.py -v` passed all 7 tests on Python 3.12.3.
2. Independent Draft 2020-12 meta-validation passed for all six schemas. The registry validated with 0 errors.
3. Independent registry inspection found 9 entries, 9 active entries, all workflow steps `0, 1, 1b, 1c, 2, 3, 3b, 4a, 4b`, no missing local prompt or output-contract paths, no SHA-256 mismatch, and prompt metadata versions `1.5.0` for Step 0 and `2.0.0` for every other step.
4. The runtime schemas, registry, and A2.1 fixtures are ASCII and contain no AHD/client constant or forbidden dash. `python3.11` is unavailable in this environment, so Python 3.11 execution was not independently verified. The source uses Python 3.10-compatible syntax, including `zip(..., strict=True)`.
5. Direct schema mutations produced the accepted values documented in the findings below. These probes used in-memory copies only.

## Findings

### P0

None.

### P1: Context Package permits ambiguous source ownership, cardinality, and ordering

Files: `standards/runtime/context-package.schema.json`, `tests/contracts/test_llm_runtime_contracts.py`

The controller requires every source descriptor to carry tenant/project identity, exactly one Step 0 intake or Step 1+ Project V2 binding as applicable, and deterministic ordered sources. The `source` definition has no `tenant_id` or `project_id`. `sources` has only `uniqueItems`, which compares complete JSON values rather than source identity or `include_order`. Neither the Step 0 conditional nor the next-step conditional constrains required-source cardinality or binds `project_context` to the corresponding source descriptor.

Direct probes against the current schema were accepted:

- A Step 0 package with a second `project_intake` source and duplicate `include_order: 1`.
- A next-step package after removing every `project_v2` source while retaining `project_context.binding_mode: project_v2`.
- A next-step package with an operational source changed to `source_status: superseded`.

This is a structural false green. Require source tenant/project fields, schema-level source-kind/cardinality constraints for the controller-required slots, unique and contiguous ordering representation, and tests for each negative case. A2.2 must still validate identity against stored records and ordering canonicalization, but it must receive an unambiguous record shape.

### P1: Logical-reference grammar accepts ambiguous separator forms

Files: `standards/runtime/logical-project-session.schema.json`, `standards/runtime/context-package.schema.json`, `standards/runtime/llm-run-result.schema.json`

The shared `logicalRef` pattern permits `runtime:artifact/a//b` and `runtime:artifact/a/`. The direct mutation probe confirmed both validate. It correctly rejected encoded traversal, literal traversal, Windows drive paths, POSIX absolute paths, `file:` URIs, and `runtime://unsafe`.

The accepted double and trailing separators create resolver-normalization ambiguity. A future A2.2 resolver that collapses separators could map distinct schema-valid logical references to the same local object. Tighten the grammar to the exact logical-reference segments used by the runtime contracts and add the accepted bypass cases to negative tests. This is not a request to implement a resolver in A2.1.

### P1: Prompt registry schema does not bind entry fields to one another or prevent duplicate configuration records

Files: `standards/runtime/official-prompt-registry.schema.json`, `tests/contracts/test_llm_runtime_contracts.py`

The registry schema accepts a syntactically valid entry with `step_id: "0"` and `prompt_id: "heartweb.step.1"`. The direct mutation probe validated successfully. Its array also has no uniqueness constraint for `step_id`, `prompt_id`, or active entry. The focused test verifies only the checked-in registry's current values, so it does not protect the contract from a future valid-but-contradictory registry edit.

Require a one-to-one step-to-prompt binding and exactly one active entry per workflow step through schema conditionals and/or a deterministic registry validation test that rejects duplicate active/inactive IDs, cross-step prompt IDs, duplicate contract paths, and unexpected paths. Hash and local path verification remain correctly exercised for the checked-in registry.

### P1: LLM result contract falsely accepts invalid output provenance and token totals

Files: `standards/runtime/llm-run-result.schema.json`, `tests/contracts/test_llm_runtime_contracts.py`

The A2.1 controller requires output revision equal to target revision and exact token arithmetic. The current schema and tests enforce only success/failure field presence. Direct probes accepted all of the following:

- `token_usage.total_tokens: 999` when input and output totals do not add to 999.
- A successful output with `revision: 999` for a target revision of 1.
- A result whose `started_at` is after `finished_at`.

The last condition is an A2.2 semantic time-order check. The token and output-revision gaps are nonetheless explicit A2.1 contract-test requirements and are currently false green. Add focused negative tests and the strongest feasible structural constraints. Where JSON Schema cannot express arithmetic or temporal comparison, the A2.1 test suite must state and exercise a small pure invariant checker rather than claim this is covered by schema validation.

### P2: Local profile and cache consistency invariants are not represented or tested

Files: `standards/runtime/worker-profile.schema.json`, `standards/runtime/llm-run-request.schema.json`, `tests/contracts/test_llm_runtime_contracts.py`

`default_model_id` is not constrained to `allowed_model_ids`. A cache-hint request can also contain a `technical_session_cache_hint.provider_id` different from the top-level `provider_id`; the direct mutation probe accepted this mismatch. The profile's allowed steps, request model, profile hash, tool policy, context hash, and cache identity are also not cross-checked by A2.1 tests.

The full cross-record comparison belongs to A2.2, as documented in report 18. At minimum, add local same-object model-membership coverage now and label the remaining stored-record equality checks as A2.2 acceptance criteria. Do not claim cache-hint safety from the present A2.1 green test.

### P3

None.

## Scope Separation

The following remain correctly excluded from this A2.1 approval gate: resolving source references under a workspace root, verifying source bytes and canonical package hashes, checking graph predecessor edges and release records, stale/superseded lifecycle decisions against stored records, cross-tenant record lookup, cache-match evaluation, result/request projection equality, idempotency comparison, routing new error codes, and all dispatch or provider behavior. Those are A2.2 or later responsibilities.

The P1 findings are not excused by that division. They concern record grammar, required descriptor identity, condition/cardinality shape, registry integrity, and explicitly promised A2.1 token/output negative coverage. They must be corrected before the contracts are a safe input boundary for A2.2.

## Required Recheck

1. Add negative coverage for each accepted mutation in this report, including duplicate include order, duplicate Step 0 intake, missing next-step `project_v2` source, superseded operational source, double/trailing logical separators, mismatched step/prompt ID, and duplicate registry identifiers.
2. Add A2.1 invariant coverage for token arithmetic and output revision. Keep non-schema comparisons visibly identified as invariant validation, not schema validation.
3. Re-run the focused suite, Draft meta-validation, registry prompt/output metadata and hash verification, and the adversarial mutations on Python 3.11 and Python 3.12 where available.
