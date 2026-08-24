# Section 11: M07/DIB-005 Baseline-Plus-Delta Evidence Report

Author: Raphael Rechberger

Change ID: M07-DIB-005

## Purpose and Observed Pre-M07 Failure

Before M07, automated and manual evidence had no shared, stable, timestamped current/history trace capable of reconstructing the preceding success and first failure. The legacy M06 trace remained active, non-automated, and without browser observation.

M07 adds the bounded diagnostic-trace closure for the existing Delivery flow. A closed run rejects further appends. An exact close replay preserves the run bytes and SHA-256 hash.

## M07 Implementation Scope

M07 changed these file groups only:

- Backend diagnostic models, storage, reconstruction, recovery, limits, policy, routes, application wiring, and error wiring.
- Backend OpenAPI contract and generated operator API types.
- Operator Console diagnostic client, provider, decorator, App integration, shell, styles, and focused tests.
- Focused Python diagnostic tests.
- M06 Delivery driver integration for the exact browser cell.
- Diagnostic reconstruction helper and gitignore entries.
- M07 audit files, including this report and the persisted result metadata.

No unrelated pre-existing worktree files are claimed as M07 work. No source, test, generated, runtime, or M06 evidence files were changed for this report.

## Affected Flow

The affected flow is `POST /diagnostic-traces` create, `POST /diagnostic-traces/{trace_id}/entries` entry append, and `POST /diagnostic-traces/{trace_id}/close` close. The Console exposes explicit action seams for this flow.

The focused browser coverage is the exact M06 Delivery cell: `DeliveryE2ETests.test_neutral_delivery_route_from_checkpoint_to_final`, including PT-09. This is not a claim for other browser cells.

## Red Evidence and Closure

The red evidence stages were:

1. Missing diagnostic modules.
2. Missing `AppConfig` and routes.
3. Missing Console client and provider.
4. Legacy M06 trace active, non-automated, and without browser observation.

Selected closure:

1. Python diagnostic models, store, limits, API, plus operator API codegen: 23 tests passed.
2. Frontend diagnostic client, provider, decorator, App, and API: 55 tests passed.
3. `npm run build`: passed.
4. Exact single `DeliveryE2ETests.test_neutral_delivery_route_from_checkpoint_to_final`: passed once green after isolated red proof.
5. `node --check apps/operator-console/src/test/deliveryE2EBrowser.mjs`: passed.

The Python closure verifies the diagnostic persistence and API boundary, including closed-run append rejection and byte-preserving close replay. The frontend closure verifies the Console action seams and their API integration. The build confirms the production Console bundle. The exact M06 cell proves the bounded Delivery path from checkpoint to final through the browser observation. The Node syntax check verifies the integrated browser driver can be parsed.

## Persisted M07 Result

- Trace ID: `trace-ddc25904b8354cf18c043cf975ec9b00`
- Relative run path: `runs/20260822T101530Z_trace-ddc25904b8354cf18c043cf975ec9b00.jsonl`
- Run SHA-256: `6649e74f1322ab431dfa0a044b3040b7809acf0551ea7ab14601e299a65bf5c8`
- Status: `closed`
- Last success: `operation-0004-browser-observation`
- First failure: `null`
- Checkpoint ZIP SHA-256: `81ddd22a1486153d348bc4a42300953f6fc9ae29e9bdf0425c55863679fd6897`
- Final ZIP SHA-256: `b41544273f480de57e57457153d006ccd6e56ef06d8637197ad007651afdf2e5`

The M06 audit files remained byte-identical. Runtime JSONL was not copied into audit evidence.

## Scope Exclusions and Evidence Classification

No full suite, M05 viewport matrix, other browser cells, broad reviews, or live integrations ran. Those activities are outside the demonstrated dependency closure for M07.

- M01 through M06: retained baseline evidence.
- M07: new focused evidence for the diagnostic trace and exact M06 Delivery browser cell.
- Unrelated prototype cells, live integrations, deployment, and customer output: not assessed.

## Status and Next Task

Remaining blocker: none.

Next product task: M08 release-critical bounded prompt quality restoration.
