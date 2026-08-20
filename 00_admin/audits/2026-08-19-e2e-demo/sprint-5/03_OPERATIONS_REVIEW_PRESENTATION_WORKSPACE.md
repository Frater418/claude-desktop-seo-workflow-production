# Sprint 5 Package 3 Operations, Review, and Presentation Workspace

Date: 2026-08-20
Author: Raphael Rechberger
Status: complete and controller verified

## Scope Boundary

This package implements master-plan Tasks 5.8 through 5.11 only. It adds the remaining visible Operator Console features for task and ticket handling, human review previews, simulated integration status, workflow presentation, and baseline capability comparison.

The work stops after Sprint 5 Package 3. Sprint 6 was not started.

## Changed Paths

- `apps/operator-console/src/features/tasks/TaskQueue.tsx`
- `apps/operator-console/src/features/tasks/TicketDetail.tsx`
- `apps/operator-console/src/features/reviews/ReviewCenter.tsx`
- `apps/operator-console/src/features/integrations/IntegrationStatus.tsx`
- `apps/operator-console/src/features/presentation/WorkflowMatrix.tsx`
- `apps/operator-console/src/features/presentation/BaselineComparison.tsx`
- `apps/operator-console/src/dev/neutralDemo.ts`
- `apps/operator-console/src/App.tsx`
- `apps/operator-console/src/styles.css`
- `apps/operator-console/src/App.test.tsx`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-5/03_OPERATIONS_REVIEW_PRESENTATION_WORKSPACE.md`

No package, lockfile, configuration, generated type, API client, backend, contract, Project State, master-plan, Control Map, prior report, or customer workspace file was changed for Package 3.

## Demo and Real API Boundaries

Exact `?mode=demo` activation is preserved. Demo mode now presents four workspaces in this order:

1. `Workflow`
2. `Artifacts & runs`
3. `Operations`
4. `Presentation`

The existing Workflow and Artifacts & runs branches retain their selected-step and selected-artifact behavior. Package 3 state is local to the demo surface and survives workspace switching.

Real API mode remains unchanged. It performs the existing readiness and project-list transport checks, does not parse the generated `unknown` projection into Package 3 records, and never falls back to Northwind demo data.

## Operations Workspace

The Task Queue contains client-neutral Northwind records for missing input, blocker resolution, revision request, workflow defect, escalation, and waiver request. Each queue entry presents type, severity, status, owner role, assignee, due date, source step, next action, and dependency in plain language.

Selecting a queue entry updates Ticket Detail. The detail view presents route classification, evidence and findings, remediation checklist, expected resolution, escalation path, and source links. No record is represented as completed. Technical task IDs, correlation IDs, and raw routes remain inside a closed `Technical details` disclosure.

## Review Center

Review Center presents the active Step 1b human gate against the current navigation artifact revision 3. The exact artifact hash remains secondary inside the closed technical disclosure. Machine-gate evidence, human findings, reviewer role, deadline, escalation path, and source links remain visible for operator review.

The six allowed local decisions are approve, reject, request revision, request input, escalate, and request waiver. Selecting a decision updates a structured live preview containing the expected revision and consequence. Approval does not claim success while the navigation blocker remains open.

Final submission is disabled and visibly requires the Transition Service/API. No selection mutates canonical state, dispatches a command, or calls the API.

## Integration Status

The visible integration labels are exactly:

- `Notion simulated`
- `n8n simulated`
- `Production disabled`

The status table shows the latest source and revision, delivery, replay, conflict, retry, DLQ, wait and resume state, and next operator action. It states that Transition Service remains authoritative. No live or production-ready integration claim is made. Raw events, routes, and delivery references remain inside a closed technical disclosure.

## Presentation Workspace

Workflow Matrix presents the initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`. Every row contains the goal, canonical input, output, machine gate, human gate, current status, and next action. Step 3b is rendered separately as a post-publication sideflow and remains `not_due`.

Baseline Comparison contrasts documented manual and chat-based operating risks with current Core-backed contracts for context, gates, tasks, contracts, and integration simulation. It is explicitly a capability comparison, not measured performance evidence or a production-readiness conclusion.

## Behavioral Tests Added

`apps/operator-console/src/App.test.tsx` adds focused Package 3 coverage for:

- Operations and Presentation tabs after the two preserved workspaces
- queue selection updating Ticket Detail
- six selectable Review Center decisions
- decision selection changing the consequence preview
- polite announcement of the updated preview
- disabled Transition Service/API submission
- Operations selections surviving workspace switches
- exact simulated and disabled integration labels
- exact initial matrix route with separate 3b sideflow
- closed Ticket Detail technical disclosure

The Package 1 and Package 2 tests remain unchanged in intent.

## Static Verification

The primary session re-read every Package 3 source and test file after delegated implementation. It confirmed:

- all writes stay inside the allowed Package 3 paths
- no AHD or other customer-specific constant is present
- the Northwind demo does not enter real API mode
- no enabled canonical submit or Package 3 transport call exists
- IDs, hashes, raw events, and routes remain secondary
- semantic tables, labelled regions, radio controls, native disabled state, focus styles, long-text wrapping, contained table overflow, and responsive breakpoints are present
- no unsupported performance or production claim is present
- no Em Dash or En Dash was introduced

TypeScript and CSS LSP diagnostics could not run because the corresponding language servers are not installed and installation was previously declined. No language server installation was attempted.

## Controller Verification Required

No npm command, generated-contract command, browser QA, live integration, commit, push, or deployment was run by this implementation session. The controller must run:

```text
cd apps/operator-console && npm test
cd apps/operator-console && npm run build
python scripts/generate_operator_api_contracts.py --check
```

Browser QA is required for exact `?mode=demo` at desktop, tablet, and mobile widths. Verify keyboard navigation, all four workspace tabs, queue selection, review radio selection and consequence announcement, disabled final submission, closed technical disclosures, contained matrix and integration tables, long-text wrapping, and zero page-level horizontal overflow.

## Controller Verification

The stable Package 3 workspace was verified after Sisyphus completed and collected the delegated implementation:

```text
cd apps/operator-console && npm test
Exit 0. 1 test file passed, 23 tests passed.

cd apps/operator-console && npm run build
Exit 0. TypeScript passed. Vite 8.2.2 built 31 modules.

cd apps/operator-console && npm audit --audit-level=moderate
Exit 0. 0 vulnerabilities.

python scripts/generate_operator_api_contracts.py --check
Exit 0.
```

One worker test used an ambiguous text query for integration labels that intentionally appear once in the visible table and again inside closed Technical Details. The controller changed only those assertions to semantic `rowheader` queries. Product behavior did not change.

Local Chrome CDP opened the actual Vite demo and selected Operations and Presentation at desktop 1440 by 1100 and mobile 390 by 844. Assertions confirmed:

- exact active workspace tabs
- desktop and mobile document scrollWidth within viewport bounds
- Operations and Presentation panels within viewport bounds
- zero open Technical Details disclosures by default
- disabled Transition Service/API submission
- exact Notion simulated, n8n simulated, and Production disabled labels
- visible review consequence preview
- exact initial matrix route and separate 3b sideflow
- Baseline Comparison present as a capability comparison

Desktop and mobile screenshots passed visual inspection. Mobile matrix tables use contained horizontal scrolling without page-level overflow.

## Exclusions

- no dependency or lockfile change
- no npm install, npm ci, or npm audit
- no generated type or OpenAPI change
- no backend or contract change
- no real Notion or n8n connection
- no canonical state mutation
- no live integration or deployment
- no measured performance conclusion
- no Project State, plan, Control Map, or prior report update
- no commit or push
- no Sprint 6 work
