# Sprint 4 Stage A Terminal Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Independent terminal-only quality and false-green-resistance audit of Sprint 4 Stage A Integration Contract V2 and the Stage A Notion graph validator. DEC-0018 is the governing decision. Reports 01 through 10 were used only for navigation. Stage A2, Stage B, and later stages are excluded.

## Terminal Verdict

`REQUEST_CHANGES`

Focused tests, the full suite, schema meta-validation, and nearly all direct mutation probes pass. Approval is blocked by one P1 false green in the injected-schema failure path. An invalid injected schema produces an unstructured Python exception rather than the stable structured validator error promised by the implementation.

## Findings

### P0

None observed.

### P1

1. Missing injected schema identifiers bypass the declared structured-error contract.
   - Evidence: [`notion_graph.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/integration_contracts/notion_graph.py:70) retrieves `schema["$id"]` before the following string check. Removing `$id` independently from each injected `record_map`, `projection`, and `snapshot` schema and calling `validate_notion_graph()` produced `KeyError: '$id'` in all three cases.
   - Expected behavior: the nearby `NOTION_GRAPH_SCHEMA_ID_INVALID` structured error path should represent an invalid or absent injected schema ID. It is unreachable for an absent key.
   - Impact: callers cannot reliably handle malformed injected schemas through the documented `NotionGraphValidationError` and stable `NOTION_GRAPH_*` error namespace. The current focused suites do not exercise this boundary, so all tests remain green despite the failure-contract violation.

### P2

None observed.

### P3

1. Native Python 3.11 execution could not be performed because `python3.11` is not installed. The graph module parsed successfully using Python 3.11 grammar mode under the installed Python 3.12.3 runtime.

## Confirmed Evidence

- DEC-0018 keeps protected workflow state, hashes, revisions, and gate decisions in the local Core and Transition Service. Stage A correctly remains contract and graph-validation work, not an API, event-store, or simulator implementation.
- The Stage A validator accepts caller-injected schemas only and builds a local `referencing.Registry`. It has no filesystem, network, provider, subprocess, state, or fallback imports or calls.
- Schema validation is performed before semantic graph checks. A combined mutation with an additional record field and a dangling relation returned `NOTION_GRAPH_SCHEMA_INVALID` first and also reported `NOTION_GRAPH_RELATION_TARGET_MISSING`.
- Positive projection and snapshot fixtures validate. The validator deterministically returns target kind, record count, and ordered structured errors.
- Direct mutations rejected dangling references, relation target-family mismatches, copied subject identity, and duplicate relation edges. A valid distinct entity with a changed map key and matching `subject_id` was accepted.
- Target-kind selection was exercised: the positive snapshot fails when validated as a projection. The external record-map reference resolves through the injected local registry for both real targets.
- V2 event catalog parity, 17 record types, closed payloads, simulated/live separation, n8n authority exclusions, retry/DLQ bounds, 30/60/90 cadence, V1 compatibility, and the ten client-neutral archetype references passed the focused suite.
- `NOTION_GRAPH_*` does not collide with the canonical runtime `ERROR_*` namespace. The Stage A source and fixtures contain no filesystem or network behavior, forbidden dash characters, AHD constants, or live client constants. The V2 test's intentional negative string assertions were excluded from this content check.
- Full discovery includes the graph-validator tests and passes on the current OMO-style runner. The current tracked diff has broad unrelated changes; Stage A files are untracked and were inspected directly. Within the Stage A implementation surface, the only service module is [`notion_graph.py`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/integration_contracts/notion_graph.py), with its package initializer, schemas, fixtures, and focused tests. No additional Stage A source, configuration, Docker, decision, plan, state, or requirement edit was observed.

## Commands And Observed Results

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
Result: 14 tests passed.

python -m unittest tests.test_notion_graph_validator -v
Result: 6 tests passed.

python tests/run_full_suite.py
Result: exit 0. Acceptance: 7 tests. Root discovery: 177 tests. Contract discovery: 51 tests. Total: 235 tests.

Direct meta-validation probe: load every `*.schema.json` in `standards/integrations`, `standards/workflow`, `standards/runtime`, `standards/operator`, and `standards/domain`; call `Draft202012Validator.check_schema(schema)` for each.
Result: 35 schemas meta-validated.

Direct injected-schema probe: for each of `record_map`, `projection`, and `snapshot`, deep-copy the three injected schemas, delete that schema's `$id`, then call `validate_notion_graph(positive_projection, NotionGraphTarget.PROJECTION, schemas)`.
Result: every probe raised `KeyError: '$id'`, not NotionGraphValidationError with NOTION_GRAPH_SCHEMA_ID_INVALID.

Direct graph probe: validate positive projection and snapshot; validate snapshot as projection; then mutate a combined schema-invalid and dangling record, a dangling target, target-family mismatch, copied subject identity, duplicate edge, and a distinct key plus matching subject_id.
Result: the correct target accepts each positive document; wrong target fails; schema error precedes semantic error; invalid graph mutations are rejected; the valid distinct entity is accepted.

Direct static probe: inspect `notion_graph.py` for filesystem, network, subprocess, fallback, and `ERROR_` tokens; parse it with `ast.parse(..., feature_version=(3, 11))`; scan Stage A schemas, fixtures, and validator source for forbidden dash characters, AHD, and live client constants.
Result: no prohibited behavior or content found, no runtime error namespace collision found, and Python 3.11 grammar parsing passed.

python3.11 --version
Result: command not found.

git status --short --untracked-files=all
git diff --check
git diff --no-ext-diff --stat
git diff --no-ext-diff --name-only
Result: no diff whitespace error. The worktree contains broad pre-existing tracked and untracked Sprint material. Stage A artifacts are untracked, so their current filesystem contents were audited directly.
```

## Required Closure

Repair the injected-schema ID lookup so absent or non-string `$id` values deterministically return `NotionGraphValidationError` containing `NOTION_GRAPH_SCHEMA_ID_INVALID`, then add focused regression coverage for record-map, projection, and snapshot injection failures. Re-run this Stage A-only audit after that change.

## Scoped Exclusion

This decision does not assess or begin Stage A2, Stage B, Stage C, Stage D, live Notion, live n8n, provider connectivity, crawling, deployment, or any later implementation work.
