# Sprint 4 Stage A Notion Graph Integrity Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Stage A V2 Notion graph integrity only. Stage A2, Stage B, and review work were not started.

## Delivered

- `notion-record-v2.schema.json` now requires `subject_id` on every record value. It uses the same 17 stable prefix families as record-map keys.
- Closed relation objects now bind every `relation_type` to the matching target key prefix through Draft 2020-12 `oneOf` branches.
- `services/integration_contracts/notion_graph.py` provides an injected-schema, deterministic validator. It creates a local `referencing.Registry` that explicitly registers the record-map, projection, and snapshot V2 schemas, selects the Draft 2020-12 projection or snapshot root by `NotionGraphTarget`, and performs schema validation before graph checks.
- The structured `NotionGraphValidationResult` returns `valid`, target kind, record count, and stable `NotionGraphError` records. `assert_notion_graph_valid` raises `NotionGraphValidationError` with the first structured finding.
- The validator rejects key and `subject_id` mismatch, missing local relation targets, relation target family mismatch in defense in depth, and unordered duplicate edges identified by the relation-type and target-record-ID pair.
- Positive projection and snapshot fixtures now carry matching `subject_id` values. The snapshot now contains a complete two-record relation graph.
- Focused V2 contracts call the production validator for projection and snapshot graph behavior. Direct validator tests cover positive projection and snapshot validation, dangling targets, target-family mismatch, copied records retaining a `subject_id`, duplicate edges with reordered fields, and a distinct record whose key and `subject_id` both change.

## TDD Evidence

RED command:

```text
python -m unittest tests.test_notion_graph_validator -v
```

Actual RED result: `Ran 1 test in 0.001s`, `FAILED (errors=1)`, exit code 1. The test failed because `services.integration_contracts` did not exist: `ModuleNotFoundError: No module named 'services.integration_contracts'`.

GREEN commands:

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
python -m unittest tests.test_notion_graph_validator -v
```

Actual GREEN results: V2 contract suite `Ran 14 tests in 0.276s`, `OK`, exit code 0. Direct graph-validator suite `Ran 6 tests in 0.102s`, `OK`, exit code 0.

Full OMO command:

```text
python tests/run_full_suite.py
```

Actual final result: exit code 0. Acceptance runner: 7 tests. Root unittest discovery: 177 tests. Contract unittest discovery: 51 tests. Total: 235 tests.

The first OMO attempt found two integration defects from the new surface: contract discovery lacked the repository import root, and the Core runtime-code audit reserved the `ERROR_` namespace. The focused import path was made explicit and validator codes use the stable `NOTION_GRAPH_*` namespace. The final OMO run above passed all 235 tests.

## Why Deterministic Code Enforces Cross-Record Rules

Draft 2020-12 schemas express local object shape, closed fields, ID grammars, and relation type to target-prefix binding. Standard JSON Schema cannot portably require that a dynamic relation target exists as a key in the same map, compare a map key to a nested `subject_id`, or deduplicate relation edges independent of JSON object field order. The production validator performs those cross-record invariants after real Draft 2020-12 validation. No nonstandard JSON Schema keywords or extensions were introduced.

## Files Changed

- `standards/integrations/notion-record-v2.schema.json`
- `services/integration_contracts/__init__.py`
- `services/integration_contracts/notion_graph.py`
- `tests/fixtures/integrations/v2/positive-notion-projection.json`
- `tests/fixtures/integrations/v2/positive-notion-snapshot.json`
- `tests/contracts/test_integration_contracts_v2.py`
- `tests/test_notion_graph_validator.py`
- This report

## Limitations And Compliance

- Native Python 3.11 execution was not available: `python3.11 --version` returned `command not found`. The implementation uses Python 3.11-compatible syntax and was executed with the installed Python 3.12 runtime.
- `basedpyright` is not installed and was previously declined, so LSP diagnostics were unavailable for all changed Python files. Focused and full runtime tests passed.
- The validator has no filesystem reads, writes, path access, network calls, provider calls, state mutation, or fallback behavior. Schemas are injected by the caller and registered only in the local registry used for that validation.
- V1 contracts, event catalogs, cadence, archetype matrix, simulated/live separation, provenance, client neutrality, and forbidden-dash checks remain covered by the passing focused and full suites.
- Only the Stage A allowlist files above were changed. No commit, push, provider call, deployment, or live integration action was performed.
