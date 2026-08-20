# Sprint 4 Stage A2 Package A2.1 Final Specification Approval

Date: 2026-08-20
Author: Raphael Rechberger
Reviewer: Reviewer A, new independent read-only final audit after report 33
Scope: Package A2.1 runtime contracts and official registries only. This report is the sole mutation made by this audit.

## Final Verdict

APPROVED

Report 33's production-boundary correction is present and independently proven. `RuntimeContractValidator.__init__` meta-validates every injected schema before constructing or caching any Draft 2020-12 instance validator, then stores the injected registry. The exact report-28 malformed Context Package schema raises `SchemaError` during construction before any `validate` call, with zero validator instances constructed. The six valid schemas construct and cache successfully only after all checks pass.

The current A2.1 surface passes the focused 20-test suite on the host and local OMO, host and OMO six-schema meta-validation, all prior mutation families, both project-context kind swaps, selected and nonselected source-policy checks, all six selected-source trust and lifecycle probes, live prompt and output hash verification, and the guarded no-I/O check. No A2.2 implementation or scope expansion was found.

## Required Evidence And Live Surface

Read before decision: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; reports 19, 20, 22, 25, 28, 29, 30, 31, 32, and 33; all six runtime schemas; the official registry schema and data; all A2.1 fixtures; both focused test modules; and the live `services/runtime_contracts/llm_records.py` surface.

The inspected production path is `RuntimeContractValidator.__init__` to `Draft202012Validator.check_schema()` for every injected schema, then construction of `self._validators`, followed by `RuntimeContractValidator.validate()` to schema errors and pure record-local invariants. The constructor ordering is explicit in `llm_records.py`: the meta-validation loop precedes the validator-cache comprehension and registry assignment.

The A2.1 inventory contains six closed Draft 2020-12 schemas, a nine-entry active official prompt registry for steps `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`, eleven positive fixtures, eight contract tests, and twelve invariant tests. `services/context_builder/**` has no files. No resolver, source-byte loader, canonical hash builder, cache-policy evaluator, routing, API, event, integration, UI, provider, dispatch, deployment, or workflow-state behavior was found.

## Commands And Results

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v
```

Host result: PASS, 20 tests in 0.802s, exit status 0.

```sh
docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v'
```

Local OMO result: PASS, 20 tests in 0.844s, exit status 0.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
for name in names:
    Draft202012Validator.check_schema(json.loads((Path('standards/runtime') / f'{name}.schema.json').read_text(encoding='utf-8')))
print('HOST_META_VALIDATION_PASS', len(names), 'schemas')
PY
```

Host result: `HOST_META_VALIDATION_PASS 6 schemas`.

The same six-schema command in local OMO printed `OMO_META_VALIDATION_PASS 6 schemas`.

### Mandatory Adversarial Constructor Proof

The following in-memory proof loaded the six current schemas and registry before instrumenting the injected validator dependency. It reconstructed the exact report-28 malformed conditional by moving `required: ["source_kind"]` from the `if` object into `if.properties.required`. The command only constructed `RuntimeContractValidator`; it never invokes `validate`. The temporary validator proxy delegates `check_schema()` to the real Draft 2020-12 implementation and counts instance construction.

```text
META_INVALID_CONSTRUCTOR_SCHEMA_ERROR_PASS validate_calls=0 validator_instances_created=0 cached_validators=0
```

Result: PASS. `SchemaError` was raised from construction. Zero instance validators were created before the failure, so no validator cache could exist and no document or semantic validation could begin. This proves the report-31 ordering defect is closed at the production boundary, not only in test setup.

A separate valid-construction probe created one `RuntimeContractValidator` with all six current schemas, asserted the cache order and size, and validated a positive record for every kind including the live registry:

```text
VALID_CONSTRUCTION_AND_CACHE_PASS 6 schemas 6 record-kinds
```

Result: PASS. Together with the failing malformed-schema proof and the constructor source ordering, this establishes that caching occurs only after all six meta-schema checks pass.

### Required Behavioral Reruns

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_missing_project_v2_duplicate_intake_and_invalid_order \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_stale_bindings_and_revision_equality \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_ambiguous_logical_references_and_project_binding \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_registry_rejects_duplicate_and_cross_step_entries \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_worker_and_request_reject_local_policy_mismatches \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_result_rejects_output_token_and_timestamp_mismatches \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_session_rejects_binding_mode_mismatch \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_selected_project_source_policy_values \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_accepts_nonselected_source_policy_values \
  tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_project_context_source_kind_swaps
```

Result: PASS, 10 tests in 0.326s. This reran every prior mutation family, both project-context kind swaps, selected authority policy, and permitted nonselected predecessor policy. The selected Step 0 intake rejects `operator_asserted`, `not_applicable`, and `untrusted`; the selected Step 1 Project V2 rejects `active`, `rejected`, and `historical`. Each selected-source probe produces the deterministic `LLM_RUNTIME_CONTEXT_INVALID` error at its selected descriptor field. The nonselected predecessor remains valid with `operator_asserted/active` and `not_applicable/rejected` values.

The independent live registry SHA-256 and metadata check printed:

```text
PROMPT_OUTPUT_HASH_PASS 9 prompts 12 output-bindings step0 1.5.0
```

Result: PASS. All eight non-Step-0 prompts match version `2.0.0`; every active prompt and output contract hash matches its current local bytes.

The guarded no-I/O probe injected schemas and registry first, then replaced `builtins.open`, `os.getenv`, and `socket.socket` with raising guards while validating the registry, logical session, worker profile, Context Package, request, and result:

```text
NO_IO_NO_FALLBACK_PASS 6 record-kinds
```

Result: PASS. No file, environment, socket, provider, or fallback path was reached.

## A2.1 Requirement And Prior-Report Closure

| Requirement or prior report | Status | Current evidence |
| --- | --- | --- |
| Six closed Draft 2020-12 schemas and unique stable IDs | Closed | Host and OMO `check_schema()` passed for all six; focused suite passed. |
| Meta-validation before instance validation and caching | Closed | Exact historical malformed schema raises `SchemaError` in constructor with zero instance validators; valid six-schema construction caches all six only after checks. |
| Nine prompts, exact metadata and byte hashes, all output contracts and multi-output coverage | Closed | Live check passed for 9 prompts and 12 output bindings; Step 0 is 1.5.0 and all others are 2.0.0. |
| Report 19 | Closed | Context, worker, request, result, session, and registry mutation families reject through the focused rerun. |
| Report 20 | Closed | Source ownership, cardinality, ordering, logical-reference grammar, registry integrity, result provenance, and profile/cache local-policy mutations reject. |
| Report 22 | Closed | Both Step 0 intake and Step 1 Project V2 project-context kind swaps reject deterministically at `/project_context/source_id`. |
| Report 25 | Closed | All six selected source trust and lifecycle violations reject; permitted nonselected source values remain valid. |
| Reports 28 and 29 | Closed | Context Package is valid Draft 2020-12 on host and OMO, and constructor meta-validation prevents an instance-only false green. |
| Report 31 | Closed | Meta-validation is now the production constructor precondition before validator creation and caching. |
| Strict A2.2 exclusion | Verified | No `services/context_builder/**` files and no A2.2 responsibility implemented in the inspected surface. |

## Findings

### P0

None.

### P1

None.

### P2

None.

### P3

None.

## Platform Limitations

Host runtime: Python 3.12.3. `python3.11` and `pwsh` are not installed, so Python 3.11 and native Windows execution could not be run. This is a coverage limitation only and is not a finding: local OMO independently passed the focused 20-test suite and six-schema meta-validation. No network, provider, crawl, deployment, browser, git-write, commit, push, or non-report mutation was performed by this audit.
