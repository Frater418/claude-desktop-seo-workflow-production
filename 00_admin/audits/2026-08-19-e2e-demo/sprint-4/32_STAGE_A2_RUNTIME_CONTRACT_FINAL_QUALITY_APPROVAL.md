# Sprint 4 Stage A2 Package A2.1 Final Runtime Contract Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Reviewer: Reviewer B, fresh independent read-only terminal audit after report 30
Scope: Package A2.1 runtime contracts and official registries only. This report does not approve A2.2 or later work.

## Final Verdict

APPROVED

Report 30's Draft 2020-12 correction is present and independently verified. The complete current A2.1 surface passes the focused 19-test gate on the host and local OMO, explicit six-schema meta-validation on both runtimes, the regression-execution probe, historical mutation families, both project-context kind swaps, selected and nonselected source-policy probes, live registry prompt and output hashes, deterministic-error checks, and guarded no-I/O validation. No A2.2 implementation or scope expansion was found.

## Required Evidence Read And Current Surface

Read before the decision: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; reports 19, 20, 22, 25, 28, 29, and 30; the six live runtime schemas; official registry schema and data; `services/runtime_contracts/llm_records.py`; the two focused test modules; and the A2.1 fixtures.

The live path is `LlmRuntimeContractTests` or `LlmRuntimeInvariantTests` to `RuntimeContractValidator.validate()` to Draft 2020-12 instance validation and then record-local invariant checks. The validator receives schemas and registry data by injection. Its source has no filesystem, environment, clock, socket, provider, routing, dispatch, repository, or workflow-state mutation path.

The current A2.1 inventory contains six closed Draft 2020-12 schemas, a nine-entry active official prompt registry for steps `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`, eleven positive fixtures, and the 7 contract plus 12 invariant focused tests.

The report 30 fix is visible in `standards/runtime/context-package.schema.json`: the affected source conditional now places `required: ["source_kind"]` as a sibling of `properties` inside `if`. The current working-tree entries are untracked, so ordinary `git diff` has no tracked base diff for this file. Direct source inspection confirmed the corrected live content and `test_schemas_are_unique_closed_draft_2020_12_contracts` now calls `Draft202012Validator.check_schema(schema)` before its schema URI, ID, closure, and fixture or instance assertions.

## Commands And Results

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Host result: PASS, 19 tests in 0.566s, exit status 0.

```sh
docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python - <<'"'"'PY'"'"'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
names = ("logical-project-session", "official-prompt-registry", "worker-profile", "context-package", "llm-run-request", "llm-run-result")
for name in names:
    Draft202012Validator.check_schema(json.loads((Path("standards/runtime") / f"{name}.schema.json").read_text(encoding="utf-8")))
print("OMO_META_VALIDATION_PASS", len(names), "schemas")
PY
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v'
```

OMO result: PASS, `OMO_META_VALIDATION_PASS 6 schemas`; focused suite PASS, 19 tests in 0.636s, exit status 0.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
for name in names:
    Draft202012Validator.check_schema(json.loads((Path('standards/runtime') / f'{name}.schema.json').read_text(encoding='utf-8')))
print('META_VALIDATION_PASS', len(names), 'schemas')
PY
```

Host result: PASS, each named schema meta-validated and `META_VALIDATION_PASS 6 schemas` printed.

An independent execution probe substituted an observing Draft 2020-12 validator into `LlmRuntimeContractTests`, invoked `test_schemas_are_unique_closed_draft_2020_12_contracts`, and recorded `check_schema()` for all six expected runtime schema IDs. This proves the focused regression executes the meta-validation calls before its later URI, closure, and instance-oriented assertions, rather than merely accepting valid fixture instances.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import importlib
module = importlib.import_module('tests.contracts.test_llm_runtime_contracts')
original = module.Draft202012Validator
calls = []
class ObservedDraft202012Validator(original):
    @classmethod
    def check_schema(cls, schema, format_checker=original.FORMAT_CHECKER):
        calls.append(schema['$id'])
        return super().check_schema(schema, format_checker=format_checker)
module.Draft202012Validator = ObservedDraft202012Validator
case = module.LlmRuntimeContractTests('test_schemas_are_unique_closed_draft_2020_12_contracts')
module.LlmRuntimeContractTests.setUpClass()
case.test_schemas_are_unique_closed_draft_2020_12_contracts()
print('META_REGRESSION_EXECUTED_BEFORE_POST_META_ASSERTIONS', tuple(calls))
PY
```

Result: PASS, all six expected schema IDs were recorded in test iteration order. The instrumentation emitted Python's documented validator-subclass deprecation warning only; it did not affect the successful regression execution.

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

Result: PASS, 10 tests in 0.287s. This reran all prior mutation families: project source cardinality and ordering, stale source, revision equality, prompt and output binding, logical-reference grammar, registry identity, worker and request policy, result token and timestamp invariants, and logical-session binding. It also verified both project-context kind swaps reject, all six selected source probes reject at deterministic source fields, and permitted nonselected predecessor values remain valid.

The live registry SHA-256 and metadata probe passed: `PROMPT_OUTPUT_HASH_PASS 9 prompts 12 output-bindings step0 1.5.0`. All eight non-Step-0 prompt versions matched their registry entries as `2.0.0`.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import hashlib, json, re
from pathlib import Path
root = Path('.')
registry = json.loads((root / 'standards/runtime/official-prompt-registry.json').read_text(encoding='utf-8'))
expected = {'0': '0-kickoff.xml.md', '1': '1-pillar-identifikation.xml.md', '1b': '1b-seitenarchitektur.xml.md', '1c': '1c-pillar-template.xml.md', '2': '2-cluster-recherche.xml.md', '3': '3-120-tage-plan.xml.md', '3b': '3b-performance-check.xml.md', '4a': '4a-content-briefing-und-schema.xml.md', '4b': '4b-landingpage-html.xml.md'}
active = [entry for entry in registry['entries'] if entry['active']]
assert len(active) == 9 and {entry['step_id'] for entry in active} == set(expected)
for entry in active:
    prompt_path = root / entry['prompt_path']
    metadata = re.search(r'<prompt_metadata>(.*?)</prompt_metadata>', prompt_path.read_text(encoding='utf-8'), re.S).group(1)
    assert prompt_path.name == expected[entry['step_id']]
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == entry['prompt_sha256']
    assert re.search(r'<version>\s*([^<]+)\s*</version>', metadata).group(1) == entry['prompt_version']
    for binding in entry['output_contracts']:
        assert hashlib.sha256((root / binding['contract_path']).read_bytes()).hexdigest() == binding['contract_sha256']
print('PROMPT_OUTPUT_HASH_PASS', len(active), 'prompts', sum(len(entry['output_contracts']) for entry in active), 'output-bindings', 'step0', next(entry['prompt_version'] for entry in active if entry['step_id'] == '0'))
PY
```

A guarded five-record validation probe loaded dependencies before patching `builtins.open`, `os.getenv`, and `socket.socket` to raise. Logical session, worker profile, Context Package, LLM request, and LLM result positive records all remained valid: `NO_IO_NO_FALLBACK_PASS 5 record-kinds`. The same probe mutated token total and timestamp order twice and received equal frozen errors in the same deterministic order: `LLM_RUNTIME_RESULT_INVALID /token_usage/total_tokens`, then `LLM_RUNTIME_RESULT_INVALID /finished_at`; a mutation attempt raised `FrozenInstanceError`.

```sh
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import dataclasses, json, os, socket
from pathlib import Path
from unittest.mock import patch
from services.runtime_contracts.llm_records import RuntimeContractValidator
root = Path('.')
runtime, fixtures = root / 'standards/runtime', root / 'tests/fixtures/context_builder'
names = ('logical-project-session', 'official-prompt-registry', 'worker-profile', 'context-package', 'llm-run-request', 'llm-run-result')
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
validator = RuntimeContractValidator({name: load(runtime / f'{name}.schema.json') for name in names}, load(runtime / 'official-prompt-registry.json'))
records = (('logical-project-session', load(fixtures / 'positive-logical-session-intake.json')), ('worker-profile', load(fixtures / 'positive-worker-profile.json')), ('context-package', load(fixtures / 'positive-context-step1-next.json')), ('llm-run-request', load(fixtures / 'positive-request-fresh.json')), ('llm-run-result', load(fixtures / 'positive-result-success.json')))
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
print('NO_IO_NO_FALLBACK_PASS', len(records), 'record-kinds')
print('DETERMINISTIC_IMMUTABLE_ERROR_PASS', expected)
PY
```

## Findings

### P0

None. All six claimed Draft 2020-12 contracts pass `Draft202012Validator.check_schema()` on the host and local OMO. The prior meta-schema false green is closed by both the schema repair and the focused regression that executes meta-validation.

### P1

None. Every locally representable historical source, trust, lifecycle, project binding, registry, worker, request, and result mutation family reran as rejected where required. The selected authority descriptor is strict while nonselected descriptors retain their permitted policy values.

### P2

None. The registry's nine active prompts and 12 output contracts match local bytes, hashes, metadata, workflow steps, and required multi-output bindings. Error records are deterministic and immutable. The injected validator remains client-neutral and has no I/O or fallback behavior under guarded execution.

### P3

None. No quality defect was identified in the A2.1 boundary.

## Scope And Exclusion Evidence

Strict A2.2 exclusion is confirmed. `services/context_builder/**` does not exist. No source resolver, source-byte loader, canonical hash builder, lifecycle or freshness lookup, graph or release lookup, stored-record projection comparison, idempotency ledger, cache-eligibility or technical-session policy evaluator, routing integration, API, event store, simulator, UI, provider call, dispatch path, deployment behavior, or workflow-state mutation was introduced by A2.1.

Those operations remain planned A2.2 or later responsibilities. The approved A2.1 boundary is limited to closed records, the official registry, injected Draft 2020-12 validation, and pure locally representable invariant checks.

## Platform Limitations

Host runtime: Python 3.12.3. `python3.11` and `pwsh` are not installed, so Python 3.11 and native Windows execution could not be run. This is a coverage limitation only, not a finding: local OMO independently passed meta-validation and the full focused suite. No network, provider, crawl, deployment, browser, or git-write operation was performed. The only repository mutation during this audit is this report.
