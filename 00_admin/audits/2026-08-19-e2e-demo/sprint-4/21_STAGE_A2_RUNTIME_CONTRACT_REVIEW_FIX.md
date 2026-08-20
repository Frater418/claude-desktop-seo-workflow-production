# Sprint 4 Stage A2 Package A2.1 Runtime Contract Review Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Package A2.1 review corrections only. No provider, API, event, simulator, UI, routing, state, workflow graph, prompt, output contract, or external lookup implementation was changed.

## Delivered Boundary

The six A2.1 schemas now enforce local record shape, source ownership fields, source-slot cardinality, trigger conditionals, and unambiguous logical-reference grammar. The checked-in Context Package fixtures bind their prompt and output-contract values to the repository-owned registry bytes.

`services/runtime_contracts/llm_records.py` is the small pure schema-first invariant boundary. It receives schemas and the registry as injected mappings, does not read files or access network, environment, time, or mutable state, and returns ordered immutable `ValidationResult` and `ValidationError` records. `assert_valid` raises `RuntimeContractError` with the structured immutable result. Its library codes use the `LLM_RUNTIME_*` namespace and do not introduce routing codes.

Focused contract tests now apply the production validator to registry, logical session, worker profile, Context Package, request, and result fixtures. The adversarial suite covers missing Project V2, duplicate intake and include order, noncontiguous order, missing source ownership, superseded source, wrong prompt and output contract, equal revision, invalid model default, request hash mismatch, cache-provider mismatch, output revision mismatch, token arithmetic, reverse timestamps, session binding mismatch, duplicate and cross-step registry entries, and double or trailing logical separators.

## TDD Evidence

RED command:

```sh
python -m unittest tests/test_llm_runtime_invariants.py -v
```

RED result: `Ran 0 tests in 0.009s`, `FAILED (errors=1)`. The expected failure was `ModuleNotFoundError: No module named 'services.runtime_contracts'` from the new production-validator import before implementation.

GREEN command:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

GREEN result: `Ran 16 tests in 0.340s`, `OK`.

Additional session-binding RED command:

```sh
python -m unittest tests/test_llm_runtime_invariants.py -v
```

Additional RED result: `Ran 9 tests`, with the valid session fixtures rejected because `project_source.source_kind` was not yet a permitted field. This proved that binding mode could not yet agree with an explicit source kind.

Additional session-binding GREEN command:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Additional GREEN result: the focused suite passed after adding the required source kind and matching invariant check.

Schema meta-validation command:

```sh
python -c "import json, pathlib; from jsonschema import Draft202012Validator; paths=[pathlib.Path('standards/runtime') / (name + '.schema.json') for name in ('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result')]; [Draft202012Validator.check_schema(json.loads(path.read_text(encoding='utf-8'))) for path in paths]; print('META_VALIDATION_PASS', len(paths), 'schemas')"
```

Schema meta-validation result: `META_VALIDATION_PASS 6 schemas`.

Full-suite command:

```sh
python tests/run_full_suite.py
```

Full-suite result: acceptance `7`, root unittest `187`, contract unittest `58`, total `252`, all passed.

Python 3.11 command:

```sh
python3.11 -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
```

Python 3.11 result: not executed because this environment returned `python3.11: command not found`. The implementation uses Python 3.11-compatible stdlib syntax.

## Structural Versus Deferred Semantic Boundary

Implemented now: JSON Schema validates local shape, closure, source tenant/project presence, slot cardinality, lifecycle exclusion, conditionals, logical-session binding source kind, and logical-reference syntax. The pure invariant validator validates relationships represented within one supplied record and injected registry: registry parity, prompt/output binding, source identity/order/project-context binding, session binding mode/source kind/reference agreement, local revision agreement, worker default membership, request hash/cache provider equality, and result arithmetic, revision, cached-token, and timestamp rules.

Deferred to A2.2: external source lookup and byte resolution, canonical package or source-manifest hash construction, repository freshness, release and workflow-graph validation, tenant registry lookup, request-to-stored-context/profile/result projection comparisons, idempotency ledger comparison, cache equality evaluation, and technical-session policy decisions.
