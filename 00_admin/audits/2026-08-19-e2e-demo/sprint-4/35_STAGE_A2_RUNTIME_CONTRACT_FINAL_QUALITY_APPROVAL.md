# Sprint 4 Stage A2 Package A2.1 Final Runtime Contract Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Reviewer: Reviewer B, new independent read-only terminal audit after report 33
Scope: Package A2.1 runtime contracts and official registries only. This report does not approve A2.2 or later work.

## Final Verdict

APPROVED

The report-33 repair is present in the production boundary, not merely in a test. `RuntimeContractValidator.__init__` meta-validates every injected schema before it creates or retains any instance validator, then stores the injected prompt registry only after validator construction. The exact prior malformed Context Package conditional raises `SchemaError` during constructor execution before a `validate` call and before any observed instance validator is created on both host and local OMO. The complete current 20-test focused A2.1 gate and all required independent probes pass.

## Evidence Read And Current Surface

Read before decision: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; reports 19, 20, 22, 25, 28, 29, 30, 31, 32, and 33; all six runtime schemas; official-prompt registry schema and data; linked A2.1 fixtures; `services/runtime_contracts/llm_records.py`; and both focused A2.1 test modules.

The live path is focused tests to `RuntimeContractValidator.__init__` and `validate`, then Draft 2020-12 instance validation, then pure record-local semantic checks. The constructor loop calls `Draft202012Validator.check_schema(schema)` for all injected schemas before the `_validators` comprehension. Therefore a meta-invalid schema prevents the cache field from being assigned. The current valid construction creates exactly six cached instance validators, one per runtime record kind.

DEC-0019 and plan 17 require a stateful project with replaceable workers, exact prompt and source bindings, no provider session as authority, Step 0 trusted intake, Step 1 through 4b released Project V2, deterministic local record invariants, and fail-fast behavior. The current 8 contract tests plus 12 invariant tests cover the required A2.1 local boundary.

## Commands And Results

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v
```

Host result: PASS. `Ran 20 tests in 0.854s`, `OK`.

```sh
docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v'
```

Local OMO result: PASS. `Ran 20 tests in 0.814s`, `OK`.

The focused suite reran all prior mutation families from reports 19 and 20: Project V2 presence, duplicate intake, source ownership, stale source, revision equality, prompt and output binding, ordering, logical-reference grammar, registry identity, worker and request local consistency, result provenance and arithmetic, and logical-session binding. It also reran both project-context kind swaps from report 22, all six selected-source trust and lifecycle probes from report 25, and the allowed nonselected-source policy probe.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import copy, json
from pathlib import Path
from jsonschema import Draft202012Validator as RealValidator
from jsonschema.exceptions import SchemaError
import services.runtime_contracts.llm_records as records
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
runtime = Path('standards/runtime')
schemas = {name: json.loads((runtime / f'{name}.schema.json').read_text(encoding='utf-8')) for name in names}
registry = json.loads((runtime / 'official-prompt-registry.json').read_text(encoding='utf-8'))
for schema in schemas.values(): RealValidator.check_schema(schema)
assert set(records.RuntimeContractValidator(schemas, registry)._validators) == set(names)
invalid = copy.deepcopy(schemas)
condition = invalid['context-package']['$defs']['source']['allOf'][2]['if']
condition['properties']['required'] = condition.pop('required')
created = []
class ObservedValidator(RealValidator):
    def __init__(self, *args, **kwargs):
        created.append(args[0].get('$id')); super().__init__(*args, **kwargs)
records.Draft202012Validator = ObservedValidator
try:
    records.RuntimeContractValidator(invalid, registry)
except SchemaError:
    assert created == [], created
else:
    raise AssertionError('expected SchemaError during RuntimeContractValidator constructor')
finally:
    records.Draft202012Validator = RealValidator
print('CONSTRUCTOR_META_PRECONDITION_PASS valid_schemas=6 cached_validators=6 invalid_instance_validators=0 validate_calls=0')
PY
```

Host result: PASS. `HOST_CONSTRUCTOR_META_PRECONDITION_PASS valid_schemas=6 cached_validators=6 invalid_instance_validators=0 validate_calls=0`.

The same command body was executed through `docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc`.

OMO result: PASS. `OMO_CONSTRUCTOR_META_PRECONDITION_PASS valid_schemas=6 cached_validators=6 invalid_instance_validators=0 validate_calls=0`.

This is a production-boundary proof because it imports and invokes `services.runtime_contracts.llm_records.RuntimeContractValidator` directly with an in-memory reconstruction of the exact report-28 defect. It neither calls the test helper nor calls `validate`. The observing class saw no instance construction when `check_schema` raised. The only emitted diagnostic was jsonschema's documented validator-subclass deprecation warning, which did not affect the assertions.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import dataclasses, hashlib, json, os, re, socket
from pathlib import Path
from unittest.mock import patch
from services.runtime_contracts.llm_records import RuntimeContractValidator
root = Path('.')
runtime, fixtures = root / 'standards/runtime', root / 'tests/fixtures/context_builder'
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
registry = load(runtime / 'official-prompt-registry.json')
validator = RuntimeContractValidator({name: load(runtime / f'{name}.schema.json') for name in names}, registry)
records = (('logical-project-session', load(fixtures / 'positive-logical-session-intake.json')), ('official-prompt-registry', registry), ('worker-profile', load(fixtures / 'positive-worker-profile.json')), ('context-package', load(fixtures / 'positive-context-step1-next.json')), ('llm-run-request', load(fixtures / 'positive-request-fresh.json')), ('llm-run-result', load(fixtures / 'positive-result-success.json')))
def forbidden(*args, **kwargs): raise AssertionError('unexpected I/O or fallback call')
with patch('builtins.open', forbidden), patch.object(os, 'getenv', forbidden), patch.object(socket, 'socket', forbidden):
    assert all(validator.validate(kind, value).valid for kind, value in records)
invalid = load(fixtures / 'positive-result-success.json')
invalid['token_usage']['total_tokens'] = 16
invalid['started_at'] = '2026-08-20T00:00:02Z'
first, second = validator.validate('llm-run-result', invalid), validator.validate('llm-run-result', invalid)
expected = (('LLM_RUNTIME_RESULT_INVALID', '/token_usage/total_tokens'), ('LLM_RUNTIME_RESULT_INVALID', '/finished_at'))
assert first == second and tuple((error.code, error.path) for error in first.errors) == expected
try: first.errors[0].code = 'changed'
except dataclasses.FrozenInstanceError: pass
else: raise AssertionError('validation errors are mutable')
expected_prompts = {'0': '0-kickoff.xml.md', '1': '1-pillar-identifikation.xml.md', '1b': '1b-seitenarchitektur.xml.md', '1c': '1c-pillar-template.xml.md', '2': '2-cluster-recherche.xml.md', '3': '3-120-tage-plan.xml.md', '3b': '3b-performance-check.xml.md', '4a': '4a-content-briefing-und-schema.xml.md', '4b': '4b-landingpage-html.xml.md'}
active = [entry for entry in registry['entries'] if entry['active']]
assert len(active) == 9 and {entry['step_id'] for entry in active} == set(expected_prompts)
for entry in active:
    prompt = root / entry['prompt_path']
    metadata = re.search(r'<prompt_metadata>(.*?)</prompt_metadata>', prompt.read_text(encoding='utf-8'), re.S).group(1)
    assert prompt.name == expected_prompts[entry['step_id']]
    assert hashlib.sha256(prompt.read_bytes()).hexdigest() == entry['prompt_sha256']
    assert re.search(r'<version>\s*([^<]+)\s*</version>', metadata).group(1) == entry['prompt_version']
    for binding in entry['output_contracts']:
        assert hashlib.sha256((root / binding['contract_path']).read_bytes()).hexdigest() == binding['contract_sha256']
print('HOST_HASH_NO_IO_DETERMINISM_PASS prompts=9 output_bindings=12 records=6 errors=2')
PY
```

Host result: PASS. `HOST_HASH_NO_IO_DETERMINISM_PASS prompts=9 output_bindings=12 records=6 errors=2`.

The identical probe was run through local OMO.

OMO result: PASS. `OMO_HASH_NO_IO_DETERMINISM_PASS prompts=9 output_bindings=12 records=6 errors=2`.

The guarded probe proves validation uses no file open, environment lookup, socket, or fallback after dependencies are injected. It validated all six record kinds. The repeated invalid result was equal and immutable, with stable ordered errors: `LLM_RUNTIME_RESULT_INVALID /token_usage/total_tokens`, then `LLM_RUNTIME_RESULT_INVALID /finished_at`. The hash portion verified nine active prompts, twelve output bindings, all exact SHA-256 values, expected filenames, Step 0 version `1.5.0`, and every other prompt version `2.0.0`.

## Requirement Assessment

| Requirement | Result | Evidence |
| --- | --- | --- |
| Production meta-validation precondition | PASS | Direct host and OMO constructor injection raised `SchemaError` before any instance construction or `validate` call. |
| Valid schema initialization and cache ordering | PASS | All six current schemas meta-validated; successful construction retained exactly six validators. Failed construction observed zero instance validators. |
| Reports 19 and 20 mutation closure | PASS | All focused mutation tests passed on host and OMO. |
| Report 22 kind swaps | PASS | Both Step 0 and Step 1 project-context kind swaps reject. |
| Report 25 selected and nonselected source policy | PASS | Three selected intake trust values and three selected Project V2 lifecycle values reject; permitted nonselected predecessor values validate. |
| Prompt and output immutability | PASS | Nine prompt bytes, metadata, and twelve output-contract hashes match the active registry. |
| Deterministic pure validation | PASS | Guarded no-I/O probe passed for six kinds; repeated errors were equal and frozen. |
| Client neutrality | PASS | Focused neutral-surface test passed. Registry and A2.1 fixtures are ASCII and exclude AHD, credentials, endpoints, raw session handles, and forbidden dash characters. |
| Strict A2.2 exclusion | PASS | `services/context_builder/` is absent. No resolver, source-byte reader, canonical hash builder, freshness, graph or release lookup, cache-policy evaluator, routing, API, Event Store, integration, UI, provider, dispatch, deployment, or workflow-state mutation is present in the A2.1 runtime-contract path. |

## Findings

### P0

None.

### P1

None.

### P2

None.

### P3

None.

## Platform Limitations And Audit Integrity

Host runtime is Python 3.12.3. Python 3.11 and native Windows execution could not be run because `python3.11` and `pwsh` are unavailable. Local OMO independently passed the full focused suite, constructor precondition proof, and guarded hash/no-I/O/determinism probe. This is coverage limitation only and is not a finding.

No network, provider, crawl, deployment, browser, API, Event Store, integration, workflow-state, git-write, commit, push, source, test, schema, fixture, configuration, plan, or prior-report mutation was performed. No A2.2 work was started, assessed as delivered, or approved. The sole audit mutation is this report.
