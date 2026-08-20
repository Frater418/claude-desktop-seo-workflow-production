# Sprint 4 Stage A2 Context Package Meta-Schema Fix

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Reports 28 and 29 meta-schema finding only

## Finding

`context-package.schema.json` placed the JSON Schema keyword `required` inside the `properties` map of one source conditional. Draft 2020-12 requires each `properties` value to be a schema, so the array value made the Context Package schema meta-schema invalid.

## RED

The focused contract gate was first extended to run:

```python
Draft202012Validator.check_schema(schema)
```

for every one of the six Stage A2 runtime schemas.

Command:

```text
python -m unittest tests.contracts.test_llm_runtime_contracts.LlmRuntimeContractTests.test_schemas_are_unique_closed_draft_2020_12_contracts -v
```

Observed result: one test errored with the exact `SchemaError` from reports 28 and 29 at `$defs.source.allOf[2].if.properties.required`.

## Fix

Moved `required: ["source_kind"]` from inside `if.properties` to the `if` object, as required by Draft 2020-12.

No runtime behavior, source policy, fixture, service, provider, API, event, integration, UI or workflow state was changed.

## GREEN

Commands and observed results:

```text
python -m unittest tests.contracts.test_llm_runtime_contracts.LlmRuntimeContractTests.test_schemas_are_unique_closed_draft_2020_12_contracts -v
Result: 1 test passed.

python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v
Result: 19 tests passed.

docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v'
Result: 19 tests passed.
```

The new regression prevents future instance-only false greens by meta-validating all six schemas before their closure, ID and fixture assertions.

## Boundary

A2.1 remains a closed schema plus pure local invariant boundary. A2.2 still owns source resolution, exact bytes, canonical package hashing, workflow/release lookup, repository freshness, request/result cross-record comparison, idempotency and technical-session decisions.
