# Sprint 4 Stage A2 Package A2.1 Runtime Contract Terminal Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Fresh independent read-only terminal approval review after report 24. Package A2.1 only.

## Decision

APPROVED

The current A2.1 package is an additive, pure, schema-first local runtime-contract validation boundary. It rejects the prior structural false greens, both project-context source-kind swaps, and local immutable-record invariant violations before returning a valid record. This approval does not begin or approve A2.2.

## Inputs And Current Surface Inspected

Read: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; every Sprint 4 report 15 through 24; all six A2.1 runtime schemas; `official-prompt-registry.json`; all A2.1 context-builder fixtures; `services/runtime_contracts/__init__.py` and `services/runtime_contracts/llm_records.py`; `tests/contracts/test_llm_runtime_contracts.py`; and `tests/test_llm_runtime_invariants.py`.

The actual validation call path is `RuntimeContractValidator.validate()` in `services/runtime_contracts/llm_records.py`: Draft 2020-12 validation occurs first, then the record-kind-specific local invariant function. The validator receives schemas and registry mappings by injection. It has no imports or calls for filesystem access, environment access, network access, provider access, clocks, routing, dispatch, or state mutation.

## Terminal Evidence

Focused 17-test set:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Observed: `Ran 17 tests in 0.502s`, `OK`.

Six-schema Draft 2020-12 meta-validation:

```sh
python -c "import json,pathlib; from jsonschema import Draft202012Validator; names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); [Draft202012Validator.check_schema(json.loads((pathlib.Path('standards/runtime')/(name+'.schema.json')).read_text(encoding='utf-8'))) for name in names]; print('META_VALIDATION_PASS',len(names),'schemas')"
```

Observed: `META_VALIDATION_PASS 6 schemas`.

Exact Report 22 Step 1+ project-context kind-swap probe:

```sh
python -c "import json,pathlib; from services.runtime_contracts.llm_records import RuntimeContractValidator; root=pathlib.Path('.'); runtime=root/'standards/runtime'; fixture=root/'tests/fixtures/context_builder/positive-context-step1-next.json'; load=lambda path: json.loads(path.read_text(encoding='utf-8')); names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); validator=RuntimeContractValidator({name:load(runtime/(name+'.schema.json')) for name in names},load(runtime/'official-prompt-registry.json')); value=load(fixture); source=value['sources'][1]; value['project_context']={'binding_mode':'project_v2','source_id':source['source_id'],'revision':source['revision'],'logical_ref':source['logical_ref'],'content_sha256':source['content_sha256']}; result=validator.validate('context-package',value); print('PROJECT_CONTEXT_KIND_SWAP_VALID',result.valid,tuple((error.code,error.path) for error in result.errors))"
```

Observed: `PROJECT_CONTEXT_KIND_SWAP_VALID False (('LLM_RUNTIME_CONTEXT_INVALID', '/project_context/source_id'),)`. The rejected descriptor is the released predecessor while a valid Project V2 source remains present. This is deterministic rejection of the former Report 22 false green.

Previous mutation matrix rerun, including the post-report-24 source-kind regression:

```sh
python -m unittest -v tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_missing_project_v2_duplicate_intake_and_invalid_order tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_stale_bindings_and_revision_equality tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_ambiguous_logical_references_and_project_binding tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_project_context_source_kind_swaps tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_registry_rejects_duplicate_and_cross_step_entries tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_worker_and_request_reject_local_policy_mismatches tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_result_rejects_output_token_and_timestamp_mismatches tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_session_rejects_binding_mode_mismatch
```

Observed: `Ran 8 tests in 0.226s`, `OK`. Every case rejected:

| Mutation case | Current result |
| --- | --- |
| Missing Project V2 source | Rejected |
| Superseded source | Rejected |
| Equal rejected and target revision | Rejected |
| Wrong prompt binding | Rejected |
| Wrong output contract binding | Rejected |
| Duplicate include order | Rejected |
| Noncontiguous include order | Rejected |
| Duplicate Step 0 intake | Rejected |
| Missing source tenant ownership | Rejected |
| Double logical-reference separator | Rejected |
| Trailing logical-reference separator | Rejected |
| Step 0 intake context points to official-prompt source kind | Rejected exactly as `LLM_RUNTIME_CONTEXT_INVALID` at `/project_context/source_id` |
| Step 1+ Project V2 context points to released-predecessor source kind | Rejected exactly as `LLM_RUNTIME_CONTEXT_INVALID` at `/project_context/source_id` |
| Default model outside allow-list | Rejected |
| Request input hash differs from package hash | Rejected |
| Cache-hint provider differs from request provider | Rejected |
| Success output revision differs from target revision | Rejected |
| Token arithmetic mismatch | Rejected |
| Reverse result timestamps | Rejected |
| Logical-session binding reference or source-kind mismatch | Rejected |
| Cross-step registry prompt ID | Rejected |
| Duplicate registry identifier | Rejected |

Deterministic immutable error probe:

```sh
python -c "import dataclasses,json,pathlib; from services.runtime_contracts.llm_records import RuntimeContractValidator; root=pathlib.Path('.'); runtime=root/'standards/runtime'; fixtures=root/'tests/fixtures/context_builder'; load=lambda path: json.loads(path.read_text(encoding='utf-8')); names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); validator=RuntimeContractValidator({name:load(runtime/(name+'.schema.json')) for name in names},load(runtime/'official-prompt-registry.json')); value=load(fixtures/'positive-result-success.json'); value['token_usage']['total_tokens']=16; value['started_at']='2026-08-20T00:00:02Z'; first=validator.validate('llm-run-result',value); second=validator.validate('llm-run-result',value); assert first==second and first.errors[0].code=='LLM_RUNTIME_RESULT_INVALID' and dataclasses.is_dataclass(first.errors[0]) and dataclasses.is_dataclass(first); immutable=False
try: first.errors[0].code='changed'
except dataclasses.FrozenInstanceError: immutable=True
assert immutable; print('DETERMINISTIC_IMMUTABLE_ERROR_PASS',[(error.code,error.path) for error in first.errors])"
```

Observed: `DETERMINISTIC_IMMUTABLE_ERROR_PASS [('LLM_RUNTIME_RESULT_INVALID', '/token_usage/total_tokens'), ('LLM_RUNTIME_RESULT_INVALID', '/finished_at')]`. Repeated validation compared equal and attempted error mutation raised `FrozenInstanceError`.

Guarded no-I/O and no-fallback execution probe:

```sh
python -c "import builtins,json,os,pathlib,socket; from services.runtime_contracts.llm_records import RuntimeContractValidator; root=pathlib.Path('.'); runtime=root/'standards/runtime'; fixtures=root/'tests/fixtures/context_builder'; load=lambda path: json.loads(path.read_text(encoding='utf-8')); names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); validator=RuntimeContractValidator({name:load(runtime/(name+'.schema.json')) for name in names},load(runtime/'official-prompt-registry.json')); records=(('logical-project-session','positive-logical-session-intake.json'),('worker-profile','positive-worker-profile.json'),('context-package','positive-context-step1-next.json'),('llm-run-request','positive-request-fresh.json'),('llm-run-result','positive-result-success.json')); old_open,old_getenv,old_socket=builtins.open,os.getenv,socket.socket; deny=lambda *args,**kwargs: (_ for _ in ()).throw(AssertionError('forbidden I/O')); builtins.open=os.getenv=socket.socket=deny
try: results=[validator.validate(kind,load(fixtures/name)).valid for kind,name in records]
finally: builtins.open,os.getenv,socket.socket=old_open,old_getenv,old_socket
assert all(results); print('PURE_VALIDATOR_NO_IO_PASS',len(results),'records')"
```

Observed: `PURE_VALIDATOR_NO_IO_PASS 5 records`. With `open`, `getenv`, and socket construction denied after dependency injection, five valid record kinds still validated. Schema errors return immediately from the schema-first branch, and semantic validation has no fallback path.

## Quality Evidence Map

| Quality dimension | Current evidence | Verdict |
| --- | --- | --- |
| Closed schemas and stable IDs | Six schemas passed Draft 2020-12 meta-validation. Closure and ID checks pass in `tests/contracts/test_llm_runtime_contracts.py`. | Pass |
| Registry and output coverage | The focused suite verifies nine workflow steps, exact prompt metadata and hashes, and 12 ordered output-contract bindings including multi-output 1c, 4a, and 4b. | Pass |
| Schema and invariant false greens | The current invariant suite rejects all historical Report 19, 20, and 22 mutation families listed above. | Pass |
| Both project-context kind swaps | `test_context_rejects_project_context_source_kind_swaps` covers Step 0 intake to official prompt and Step 1+ Project V2 to released predecessor. The Report 22 command independently returns false with the required code and path. | Pass |
| Deterministic immutable errors | Frozen slotted `ValidationError` and `ValidationResult`, ordered schema errors, equal repeated results, and `FrozenInstanceError` are directly probed. | Pass |
| No I/O, fallback, provider, or state behavior | `llm_records.py` accepts injected data only; guarded execution passed with file, environment, and socket access denied. No provider, routing, dispatch, API, event, UI, or state-mutating call path is present. | Pass |
| Client neutrality | `test_contract_surface_is_ascii_client_neutral_and_has_no_forbidden_dash` passed for the registry and fixtures. It rejects AHD strings, credentials, endpoints, raw handles, and non-ASCII dash characters. | Pass |
| A2.2 boundary | Plan 17 and report 21 reserve source-byte resolution, canonical hashes, freshness, graph and release lookup, stored-record comparison, idempotency, cache eligibility, technical-session policy, builder, resolver, routing, and dispatch for A2.2 or later. None is implemented in A2.1. | Pass |

## Findings

### P0

None.

### P1

None.

### P2

None.

### P3

None.

## Approval Boundary

A2.1 approves only local closed-record schemas, the repository-owned registry, shipped neutral fixtures, and pure deterministic validation of local relationships. It does not claim that a logical reference resolves, that source bytes or canonical package hashes are verified, that stored records are fresh or graph-valid, that cache reuse is eligible, or that a provider may be called. Those exact capabilities remain excluded until A2.2 or later, as required by plan 17 sections 221 through 369 and report 21 sections 73 through 77.
