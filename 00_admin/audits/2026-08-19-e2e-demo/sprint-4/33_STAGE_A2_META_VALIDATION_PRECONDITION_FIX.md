# Sprint 4 Stage A2 Runtime Meta-Validation Precondition Fix

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Report 31 meta-validation ordering finding only

## Finding

The contract suite meta-validated all six schemas, but the check occurred in a test method after `setUpClass()` had already created instance validators. This did not make the current corrected schemas invalid, but it did not guarantee the required ordering for future injected schemas.

## Production Boundary Fix

`RuntimeContractValidator.__init__` now:

1. calls `Draft202012Validator.check_schema()` for every injected schema
2. creates and caches instance validators only after all meta-schema checks pass
3. stores the injected prompt registry only after validator construction

A meta-invalid injected schema therefore fails before any document, fixture or semantic invariant can be evaluated.

The contract-test `setUpClass()` also runs all six `check_schema()` calls before creating its local `Registry` or any instance validator.

## RED

Added a regression that reconstructs the exact report-28 malformed conditional in an in-memory copy and initializes `RuntimeContractValidator`.

Command:

```text
python -m unittest tests.contracts.test_llm_runtime_contracts.LlmRuntimeContractTests.test_runtime_validator_rejects_meta_invalid_schema_before_instance_validation -v
```

Pre-fix result: failed because `SchemaError` was not raised.

## GREEN

Post-fix results:

```text
Targeted production-boundary test: 1 passed
Host focused A2.1 suite: 20 passed
OMO focused A2.1 suite: 20 passed
```

## Scope

No Context Package semantics, registry value, fixture, source resolution, package hashing, cache decision, provider, API, event, simulator, UI, routing or workflow state behavior changed.
