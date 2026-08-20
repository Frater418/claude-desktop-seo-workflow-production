# Sprint 4 Stage A Injected Schema ID Fix

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Terminal Stage A quality finding from report 12 only

## Finding

The Notion graph registry accessed each injected schema ID with `schema["$id"]`. A missing `$id` therefore raised an unstructured Python `KeyError` before the intended `NOTION_GRAPH_SCHEMA_ID_INVALID` error contract could execute.

## TDD RED

Command:

```text
python -m unittest tests.test_notion_graph_validator.NotionGraphValidatorTests.test_missing_injected_schema_ids_raise_structured_error -v
```

Observed result before the production fix:

- one test method executed
- three subtests failed
- affected injected schemas: `record_map`, `projection`, `snapshot`
- each failure raised `KeyError: '$id'`
- exit code 1

## Implementation

`services/integration_contracts/notion_graph.py` now uses `schema.get("$id")` before the existing string check.

The existing structured path now handles both missing and non-string IDs:

- error type: `NotionGraphValidationError`
- code: `NOTION_GRAPH_SCHEMA_ID_INVALID`
- path: `(schema_name, "$id")`

No fallback, filesystem access, network access, state mutation or additional error namespace was introduced.

## TDD GREEN

Targeted command:

```text
python -m unittest tests.test_notion_graph_validator.NotionGraphValidatorTests.test_missing_injected_schema_ids_raise_structured_error -v
```

Observed:

- 1 test passed
- all three schema subtests passed
- exit code 0

Focused command:

```text
python -m unittest tests.test_notion_graph_validator tests.contracts.test_integration_contracts_v2 -v
```

Observed:

- 21 tests passed
- exit code 0

## Full Verification

Windows:

```text
python tests/run_full_suite.py
```

Observed:

- Acceptance: 7
- Root discovery: 178
- Contract discovery: 51
- Total: 236 passed

OMO:

```text
docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python tests/run_full_suite.py'
```

Observed:

- Acceptance: 7
- Root discovery: 178
- Contract discovery: 51
- Total: 236 passed

Diff check:

```text
git diff --check
```

Observed: exit 0 with line-ending conversion warnings only and no whitespace error.

## Files Changed

- `services/integration_contracts/notion_graph.py`
- `tests/test_notion_graph_validator.py`
- this report

## Scope Confirmation

- No Stage A2 implementation started.
- No API or simulator implementation started.
- No V1 contract changed.
- No Docker or auth file is part of this code fix.
- No commit or push was performed.
