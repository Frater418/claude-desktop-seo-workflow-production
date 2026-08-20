# Sprint 4 Stage A2 Package A2.1 Terminal Specification Approval

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Fresh independent read-only terminal approval review after report 24. Package A2.1 only.

## Decision

REQUEST_CHANGES

The six required schemas, repository-owned prompt registry, fixtures, focused tests, and pure schema-first `RuntimeContractValidator` are present. The prior report 19, 20, and 22 mutations are now deterministically rejected. A new P1 remains: a Step 0 Context Package accepts a `project_intake` source marked `operator_asserted` or `not_applicable`, and a next-step Context Package accepts its selected `project_v2` source with `active` or `rejected` status. Plan 17 requires exactly one trusted intake for Step 0 and exactly one released Project V2 source for Steps 1 through 4b. These are locally representable A2.1 contract violations and cannot be deferred to A2.2 repository resolution.

No source, test, schema, fixture, configuration, plan, existing report, provider, network, browser, or git state was modified by this review. The only created file is this report.

## Inspection Scope

Read `AGENTS.md`, DEC-0019 in `00_admin/DECISIONS.md`, plan 17, and every Sprint 4 report 15 through 24. Independently inspected all six A2.1 schemas, the registry schema and data, all eleven A2.1 fixtures, both A2.1 test modules, `services/runtime_contracts/__init__.py`, `services/runtime_contracts/llm_records.py`, the nine prompt files through registry byte and metadata verification, the workflow graph, and every registered output schema through registry byte verification.

The relevant current call path is `LlmRuntimeContractTests` and `LlmRuntimeInvariantTests` -> `RuntimeContractValidator.validate` -> Draft 2020-12 schema validation -> `_semantic_errors` -> record-specific local invariant checks. The validator has no file, environment, network, provider, clock, repository, or state mutation path. A2.2 remains responsible for controlled source resolution, exact source-byte verification, canonical hash construction, graph and release lookup, stored-record projection comparison, cache policy, routing, and dispatch.

## Findings

### P0

None.

### P1: Context Package accepts source trust and lifecycle values forbidden by the controller plan

Evidence paths:

- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/17_STAGE_A2_IMPLEMENTATION_PLAN.md:24-27` requires exactly one trusted `project_intake` source for Step 0 and exactly one released `project_v2` source for Steps 1 through 4b.
- `standards/runtime/context-package.schema.json:17-18` requires one intake source but does not constrain its trust level.
- `standards/runtime/context-package.schema.json:30` requires one Project V2 source but does not constrain its lifecycle to `released`.
- `standards/runtime/context-package.schema.json:56` excludes only `superseded` and `historical` sources.
- `standards/runtime/context-package.schema.json:64` permits non-evidence sources to use `trusted`, `operator_asserted`, or `not_applicable`, and permits `active` and `rejected` lifecycle values.
- `services/runtime_contracts/llm_records.py:147-178` checks source identity, ordering, project-context descriptor equality, registry bindings, and revision equality, but not required intake trust or Project V2 lifecycle.
- `tests/test_llm_runtime_invariants.py:63-212` has no negative test for either requirement.

Exact terminal probe command:

```sh
python - <<'PY'
import json
from pathlib import Path
from services.runtime_contracts.llm_records import RuntimeContractValidator

root = Path('.')
runtime = root / 'standards' / 'runtime'
fixtures = root / 'tests' / 'fixtures' / 'context_builder'
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
validator = RuntimeContractValidator({name: load(runtime / f'{name}.schema.json') for name in names}, load(runtime / 'official-prompt-registry.json'))

for label, fixture, mutate in (
    ('INITIAL_INTAKE_OPERATOR_ASSERTED', 'positive-context-step0-initial.json', lambda value: value['sources'][0].update(trust_level='operator_asserted')),
    ('INITIAL_INTAKE_NOT_APPLICABLE', 'positive-context-step0-initial.json', lambda value: value['sources'][0].update(trust_level='not_applicable')),
    ('NEXT_PROJECT_V2_ACTIVE', 'positive-context-step1-next.json', lambda value: value['sources'][0].update(source_status='active')),
    ('NEXT_PROJECT_V2_REJECTED', 'positive-context-step1-next.json', lambda value: value['sources'][0].update(source_status='rejected')),
):
    value = load(fixtures / fixture)
    mutate(value)
    result = validator.validate('context-package', value)
    print(label, result.valid, tuple((error.code, error.path) for error in result.errors))
PY
```

Observed result:

```text
INITIAL_INTAKE_OPERATOR_ASSERTED True ()
INITIAL_INTAKE_NOT_APPLICABLE True ()
NEXT_PROJECT_V2_ACTIVE True ()
NEXT_PROJECT_V2_REJECTED True ()
```

Required correction: require the selected Step 0 `project_intake` descriptor to have `trust_level: trusted`, and require the selected Step 1 through 4b `project_v2` descriptor to have `source_status: released`. Add direct production-validator negative tests for all four accepted mutations. Re-run the focused gate and this report's probes.

### P2

None.

### P3

Python 3.11 execution remains unverified because `python3.11 --version` returned `python3.11: command not found`. `python --version` returned `Python 3.12.3`. This is the compatibility evidence gap already recorded in reports 18, 20, 22, and 24. It is not the basis for the P1 decision.

## Required Test And Probe Reruns

Focused A2.1 test command:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Observed: 17 tests ran in 0.506s. Exit status 0. `OK`.

Schema meta-validation command:

```sh
python -c "import json,pathlib; from jsonschema import Draft202012Validator; names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); [Draft202012Validator.check_schema(json.loads((pathlib.Path('standards/runtime')/(name+'.schema.json')).read_text(encoding='utf-8'))) for name in names]; print('META_VALIDATION_PASS',len(names),'schemas')"
```

Observed: `META_VALIDATION_PASS 6 schemas`.

Live registry prompt and output byte command:

```sh
python -c "import hashlib,json,pathlib,re; root=pathlib.Path('.'); registry=json.loads((root/'standards/runtime/official-prompt-registry.json').read_text(encoding='utf-8')); expected={'0':'0-kickoff.xml.md','1':'1-pillar-identifikation.xml.md','1b':'1b-seitenarchitektur.xml.md','1c':'1c-pillar-template.xml.md','2':'2-cluster-recherche.xml.md','3':'3-120-tage-plan.xml.md','3b':'3b-performance-check.xml.md','4a':'4a-content-briefing-und-schema.xml.md','4b':'4b-landingpage-html.xml.md'}; active=[entry for entry in registry['entries'] if entry['active']]; assert len(active)==9 and {entry['step_id'] for entry in active}==set(expected); [(assertion for assertion in ()).throw(AssertionError()) if pathlib.Path(entry['prompt_path']).name!=expected[entry['step_id']] or hashlib.sha256((root/entry['prompt_path']).read_bytes()).hexdigest()!=entry['prompt_sha256'] or re.search(r'<version>\s*([^<]+)\s*</version>',re.search(r'<prompt_metadata>(.*?)</prompt_metadata>',(root/entry['prompt_path']).read_text(encoding='utf-8'),re.S).group(1)).group(1)!=entry['prompt_version'] else None for entry in active]; [(assertion for assertion in ()).throw(AssertionError()) if hashlib.sha256((root/binding['contract_path']).read_bytes()).hexdigest()!=binding['contract_sha256'] else None for entry in active for binding in entry['output_contracts']]; print('PROMPT_OUTPUT_HASH_PASS',len(active),'prompts',sum(len(entry['output_contracts']) for entry in active),'output-bindings')"
```

Observed: `PROMPT_OUTPUT_HASH_PASS 9 prompts 12 output-bindings`. Step 0 is version `1.5.0`; all other steps are version `2.0.0`.

Exact Report 22 project-context kind-swap command:

```sh
python -c "import json,pathlib; from services.runtime_contracts.llm_records import RuntimeContractValidator; root=pathlib.Path('.'); runtime=root/'standards/runtime'; fixture=root/'tests/fixtures/context_builder/positive-context-step1-next.json'; load=lambda path: json.loads(path.read_text(encoding='utf-8')); names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); validator=RuntimeContractValidator({name:load(runtime/(name+'.schema.json')) for name in names},load(runtime/'official-prompt-registry.json')); value=load(fixture); source=value['sources'][1]; value['project_context']={'binding_mode':'project_v2','source_id':source['source_id'],'revision':source['revision'],'logical_ref':source['logical_ref'],'content_sha256':source['content_sha256']}; result=validator.validate('context-package',value); print('PROJECT_CONTEXT_KIND_SWAP_VALID',result.valid,tuple((error.code,error.path) for error in result.errors))"
```

Observed: `PROJECT_CONTEXT_KIND_SWAP_VALID False (('LLM_RUNTIME_CONTEXT_INVALID', '/project_context/source_id'),)`. The Report 22 kind swap is deterministically rejected.

Prior mutation-group command:

```sh
python -m unittest -v tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_missing_project_v2_duplicate_intake_and_invalid_order tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_stale_bindings_and_revision_equality tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_context_rejects_ambiguous_logical_references_and_project_binding tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_registry_rejects_duplicate_and_cross_step_entries tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_worker_and_request_reject_local_policy_mismatches tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_result_rejects_output_token_and_timestamp_mismatches tests.test_llm_runtime_invariants.LlmRuntimeInvariantTests.test_session_rejects_binding_mode_mismatch
```

Observed: 7 tests ran in 0.207s. Exit status 0. `OK`.

## Prior Mutation Matrix Results

All cases below used in-memory copies and the production validator. `Rejected` means `valid=False` with the listed deterministic error.

| Report | Mutation | Result |
| --- | --- | --- |
| 19 | Missing next-step Project V2 source | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /sources` |
| 19 | Superseded operational source | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /` |
| 19 | Rejected artifact revision equals target revision | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /revision_context` |
| 19 | Wrong prompt ID for step | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /prompt` |
| 19 | Wrong output contract | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /output_contracts` |
| 19 | Duplicate include order | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /sources` |
| 19 | Noncontiguous include order | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /sources` |
| 19 | Default model outside allow-list | Rejected: `LLM_RUNTIME_WORKER_INVALID /model_policy/default_model_id` |
| 19 | Request input hash differs from package hash | Rejected: `LLM_RUNTIME_REQUEST_INVALID /input_sha256` |
| 19 | Cache-hint provider mismatch | Rejected: `LLM_RUNTIME_REQUEST_INVALID /technical_session_cache_hint/provider_id` |
| 19 | Success output revision differs from target | Rejected: `LLM_RUNTIME_RESULT_INVALID /output/revision` |
| 19 | Invalid token arithmetic | Rejected: `LLM_RUNTIME_RESULT_INVALID /token_usage/total_tokens` |
| 19 | Finished timestamp precedes start | Rejected: `LLM_RUNTIME_RESULT_INVALID /finished_at` |
| 19 | Logical-session binding reference mismatch | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /project_source/logical_ref` |
| 19 | Logical-session source-kind mismatch | Rejected: `LLM_RUNTIME_SESSION_INVALID /project_source/logical_ref` |
| 20 | Duplicate Step 0 intake | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /sources` |
| 20 | Missing source tenant ownership | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /sources/0` |
| 20 | Double logical-reference separator | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /sources/0/logical_ref` |
| 20 | Trailing logical-reference separator | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /sources/0/logical_ref` |
| 20 | Cross-step registry prompt ID | Rejected: `LLM_RUNTIME_REGISTRY_INVALID /entries/0/prompt_id`, `LLM_RUNTIME_REGISTRY_INVALID /entries` |
| 20 | Duplicate registry identifier | Rejected: `LLM_RUNTIME_SCHEMA_INVALID /entries` |
| 20 | Project-context descriptor mismatch | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /project_context` |
| 22 | Project-context source-kind swap to released predecessor | Rejected: `LLM_RUNTIME_CONTEXT_INVALID /project_context/source_id` |

## Plan 17 A2.1 Requirement Evidence

| Requirement | Status | Current evidence |
| --- | --- | --- |
| Required six schemas, registry schema/data, fixtures, and contract tests | Verified | All artifacts named in plan 17 exist. Six-schema meta-validation passed. |
| Closed Draft 2020-12 schemas and stable unique runtime IDs | Verified | `test_schemas_are_unique_closed_draft_2020_12_contracts` passed. |
| Nine official prompts, exact metadata and bytes, every output contract, multi-output coverage | Verified | Live hash command passed for 9 prompts and 12 output bindings. Fixtures and registry include multi-output 1c, 4a, and 4b. |
| Logical session identity, revisions, binding modes, local Core authority, cache-only policy, prohibited authority fields | Verified locally | Schema closure plus session binding/reference/source-kind mutation rejection passed. |
| Worker profile identity/hash, capability reference, model, steps, safe tool policy, no direct provider call | Verified locally | Closed schema and default-model mutation rejection passed. Stored-profile lookup is correctly deferred to A2.2. |
| Context identity, session binding, exact prompt, worker reference, ordered sources, output arrays, hash fields, provenance | Verified locally except source lifecycle/trust | Shape, ordering, prompt/output binding, source ownership, logical references, kind binding, and revision equality reject. Required Step 0 trusted intake and Step 1+ released Project V2 do not reject. |
| Step 0 intake versus Step 1+ released Project V2 | REQUEST_CHANGES | The kind distinction is fixed, but the mandatory trust and released lifecycle values remain accepted as invalid local records. |
| LLM request identity, run mode, package input hash, output array, fresh-mode cache prohibition | Verified locally | Focused tests and mutation matrix reject hash mismatch and cache-provider mismatch; fresh modes forbid cache hints. Stored package/profile/cache equality is A2.2. |
| LLM result provenance, success/failure exclusivity, candidate-only output, token arithmetic, timestamps | Verified locally | Focused tests and mutation matrix reject output revision, token, and timestamp violations. Request/result stored-record projection is A2.2. |
| TDD gate unknown fields, malformed IDs/hashes/references, forbidden authority data, neutral ASCII surface | Verified locally | Focused suite passed. Contract surface test covers shipped registry and fixtures. |
| Python 3.11 and 3.12 compatibility | Partially verified | Python 3.12.3 focused suite passed. Python 3.11 is unavailable in this terminal. |
| No A2.2 builder/resolver/policy, API, event, integration, UI, provider, or state work | Verified | Current implementation is schema plus pure local validator only. |

## Prior Finding Closure Matrix

| Prior report finding | Current status | Evidence |
| --- | --- | --- |
| 19 P1: Context Package accepted missing Project V2, stale source, equal revision, wrong prompt/output, and invalid ordering | Reopened in part | Every listed mutation now rejects. The same mandatory source-boundary requirement still accepts a non-trusted Step 0 intake and active/rejected Step 1+ Project V2 source. |
| 19 P1: Worker, request, and result local policy/result violations | Closed | All six listed mutations reject in the matrix. |
| 19 P2: Logical-session and registry drift | Closed | Logical-session binding/source-kind, duplicate registry, and cross-step prompt mutations reject. |
| 20 P1: Source ownership, cardinality, and ordering | Reopened in part | Ownership, cardinality, and ordering mutations reject. Required trust/lifecycle semantics for the mandatory project source remain unbound. |
| 20 P1: Ambiguous logical-reference separators | Closed | Double and trailing separator probes reject. |
| 20 P1: Registry cross-field and duplicate-record drift | Closed | Cross-step prompt and duplicate entry probes reject. |
| 20 P1: Result output provenance and token totals | Closed | Output revision and token arithmetic probes reject. |
| 20 P2: Profile and cache local consistency | Closed for A2.1 local invariants | Default-model and cache-provider mutations reject. Stored-record/cache eligibility comparison remains A2.2. |
| 22 P1: `project_context` could select a released predecessor while retaining Project V2 | Closed | Exact Report 22 probe now returns one deterministic `LLM_RUNTIME_CONTEXT_INVALID` error at `/project_context/source_id`. |

## Approval Condition

Do not approve A2.1 or begin A2.2 until the P1 source trust and lifecycle requirements are enforced by the A2.1 schema-first validation boundary and direct negative tests. Re-run the 17-test focused suite, the exact Report 22 probe, the prior mutation group, and the four newly documented lifecycle/trust probes after correction.
