# Heartweb Prototype Test Policy and Final Test Matrix

**Author:** Raphael Rechberger
**Status:** Binding project-local test authority
**Version:** 1.0.0
**Effective:** 2026-08-22
**Scope:** Heartweb local prototype, implementation fixes, regression verification and Production Release audit

## 1. Binding instruction

Every agent, orchestrator, reviewer and new session MUST read this file before selecting or running tests.

This policy has higher project-local authority than generic skills, generic CI habits, worker defaults or previous plans that prescribe a complete suite after every change.

The latest explicit instruction from Raphael remains the highest authority.

The objective is the fastest safe path to an operable local Heartweb system. Testing protects that objective. Testing must not replace delivery.

## 2. Core rule

A green test result remains valid baseline evidence for the exact code and behavior it previously covered.

After a code change, only the proven affected dependency closure loses direct current-state evidence:

```text
changed symbol
-> changed module
-> shared contract or persisted shape
-> affected route
-> affected flow
-> affected gate
```

Test that closure. Do not restart unrelated test areas.

## 3. Prohibited defaults

Without a new explicit Raphael authorization, agents MUST NOT:

1. Run `python tests/run_full_suite.py`.
2. Run all discovered repository tests.
3. Repeat the complete suite after a small or bounded fix.
4. Restart a previously passed end-to-end flow from its first step when only a later cell failed.
5. Launch multiple broad review lanes after each correction.
6. Re-run unrelated solver, prompt, workflow, UI, browser, archive or integration tests only because files changed elsewhere.
7. Treat a prior green baseline as invalid without naming the exact dependency that the new change can affect.
8. Expand a focused test scope merely because broader testing is convenient.
9. Use test count as a proxy for customer usefulness or production readiness.
10. spend model tokens on repeated review synthesis when deterministic evidence already answers the question.

A complete suite requires separate explicit authorization from Raphael in the current conversation. A prior general instruction to "verify" or "test thoroughly" is not authorization for a full suite.

## 4. Baseline plus delta evidence

Heartweb uses cumulative evidence:

```text
validated baseline H0
+ changed delta D1
+ focused verification V1 for the affected closure
= current evidence H1
```

Unchanged areas retain their baseline evidence. The delta record must name:

- changed files and symbols
- observable defect or requested behavior
- affected route, flow and gate
- selected tests
- reason each test belongs to the closure
- tests deliberately not repeated
- result
- next product action

A new error does not erase unrelated previous evidence.

## 5. Mandatory test selection algorithm

For every defect or bounded change:

1. Assign one defect or change identifier.
2. Reproduce the exact failure at the highest stable public seam.
3. Add or identify the smallest red regression test that proves the failure.
4. List changed symbols and direct callers.
5. Trace only the affected contract, route, flow and gate.
6. Select the matching matrix row below.
7. Run the red reproducer.
8. Apply the smallest safe fix.
9. Run the reproducer again.
10. Run the smallest directly affected integration set.
11. If an unexpected failure appears, expand exactly one dependency ring outward.
12. Do not jump from one unexpected failure to the complete repository suite.
13. Record the commands, counts and results.
14. Continue to the next product task as soon as the affected closure is green.

## 6. Incremental regression matrix

| Change class | Required focused evidence | Conditional evidence | Explicitly excluded by default |
|---|---|---|---|
| Pure normalization, sorting or helper behavior | exact unit regression plus direct caller test | persistence or hash test only when output bytes or identity change | unrelated API, UI, workflow, prompt and solver tests |
| Request or response model | model validation plus exact route success and failure case | OpenAPI and generated client only when public schema changes | unrelated service and browser suites |
| API error translation | exact failing route plus advertised error envelope | neighboring methods on the same route family when they share the handler | all other API routes and repository suite |
| Persistence or immutable record shape | write, readback, idempotency and conflict tests for that record family | replay or recovery only when they consume the changed shape | UI, prompt, solver and unrelated repositories |
| Replay or recovery ordering | exact completed replay, interrupted recovery and changed-source case | authorization and sidecar cleanup when touched | fresh project creation, unrelated steps and browser matrix |
| Filesystem safety | exact traversal, symlink or nonregular-file regression at the changed boundary | one authorized positive case for the same boundary | every other security or archive test |
| OpenAPI override | repeated `app.openapi()` equality plus exact affected response contract | codegen drift check when snapshot bytes change | full API suite and frontend build when generated types do not change |
| Generated API client | exact codegen drift check plus TypeScript compile of affected client | frontend build only when application imports changed generated types | Python full suite |
| UI component behavior | affected component test plus exact operator action | one browser route and affected viewport when rendering changes | all routes, all viewports and backend suite |
| Shared layout or CSS | exact affected surfaces and viewports identified from the shared selector | one neighboring surface to prove the shared rule | automatic 24-cell visual rerun |
| Workflow transition | exact legal transition, exact illegal transition and immediate predecessor or successor | persistence/readback if event or state shape changes | all unrelated workflow steps |
| Prompt, schema, validator or renderer | exact workflow step fixture, validator and rendered output | immediate downstream consumer of that artifact | complete Step 0 to 4B rerun |
| Provider adapter | exact capability, request binding, error and evidence contract | one consuming step with deterministic provider fixture | unrelated providers and workflow steps |
| Diagnostic trace | exact action to trace, persisted trace and readback | one failure reconstruction for the same route | full smoke matrix and unrelated logging |
| Broad shared service | changed public seam plus every proven caller in its dependency closure | expand one caller ring when an unexpected failure proves it necessary | complete repository suite unless Raphael explicitly authorizes it |

## 7. Current Task 6 affected closure

The current four Task 6 defects use this bounded matrix.

| Defect | Primary regression | Directly affected closure | Tests not repeated |
|---|---|---|---|
| Canonical role order | `tests/test_delivery_api_role_order.py` | role requests, request hash, persisted role order, idempotent replay | solver, prompts, workflow transitions, UI and unrelated Delivery files |
| Source-independent replay and recovery | `tests/test_delivery_api_replay_source_independence.py` | completed replay, exact recovery, mutable source independence | fresh workflow runs, browser routes and unrelated artifact revisions |
| Repeatable OpenAPI generation | `tests/test_delivery_openapi.py` | repeated `app.openapi()`, affected Delivery response contract, codegen only if bytes changed | all Delivery persistence, workflow and UI tests when generated types stay unchanged |
| Recovery Inventory safety and ordering | `tests/test_delivery_api_recovery_inventory_safety.py` | sidecar discovery, regular-file enforcement, symlink rejection, canonical order | archive suite, provider suite, prompt suite and unrelated API routes |

After these four regressions and their direct closure are green, Task 6 proceeds to Task 7. Another complete 563-plus run and another five-lane review are prohibited without separate Raphael authorization.

## 8. Review proportionality

### Default for bounded fixes

- implementer focused red and green proof
- one direct code and evidence check by Root-Sisyphus
- no multi-lane review

### Additional review only when justified

One additional independent review may be used only when the change creates or alters:

- an irreversible data migration
- a new external side effect
- a new authorization boundary
- a new public contract with customer-visible consequences

The review scope remains limited to that boundary. Repeated five-lane review rounds are not a default acceptance gate.

## 9. Final prototype route matrix

The final prototype is accepted through the following customer and operator route matrix. This matrix replaces an automatic complete repository suite.

Each cell runs once on the release candidate. If one cell fails, rerun that cell and only its direct downstream dependents after the fix. Do not restart the matrix at PT-01.

| ID | Prototype route or gate | Required observable evidence | Direct downstream cells |
|---|---|---|---|
| PT-01 | Local app startup and project selection | Operator Console loads, correct tenant and project are visible, no hidden fallback | PT-02 |
| PT-02 | Intake, validation and provisioning | accepted Project V2 identity, workspace readback, invalid intake fails before writes | PT-03 |
| PT-03 | Sequential production route 0 -> 1 -> 1B -> 1C -> 2 -> 3 -> 4A -> 4B | each required artifact exists with correct identity, predecessor, revision, validation and visible status | PT-04, PT-05 |
| PT-04 | Human review, revision and gate route | edit, save, canonical readback, revision request, rejection, approval and stale-approval protection | PT-05 |
| PT-05 | Delivery Preview and Create | preview has no writes, create binds approved revisions, warnings and policy are visible | PT-06, PT-07 |
| PT-06 | Delivery history, record, ZIP and replay | history and record read back canonical completion, ZIP downloads, exact replay remains identical | PT-07 |
| PT-07 | One-way Notion handoff | deterministic import package, assignments, priorities and deadlines, no staff-task callback into Core | none |
| PT-08 | Recovery and fail-fast route | interrupted Delivery is recoverable, unauthorized or unsafe recovery is blocked without writes | PT-05, PT-06 |
| PT-09 | Shared diagnostic trace | first failing operation, last successful operation, IDs, timestamps, error code and artifact evidence are directly readable | affected failed cell only |
| PT-10 | Release-critical operator browser smoke | exact Desktop actions for project, workflow, artifact, review and Delivery Center succeed in Chrome | affected UI cell only |
| PT-11 | Controlled real customer output | one approved local customer route produces professional downloadable packages without live integration claims | none |

### Matrix retry rule

Examples:

- PT-06 fails after ZIP download: fix and rerun PT-06. Rerun PT-07 only if package bytes or Notion inputs changed. Do not rerun PT-01 through PT-05.
- PT-04 fails on stale approval: fix and rerun the stale-approval scenario plus PT-05 if approval identity changed. Do not rerun research steps.
- PT-10 fails on Delivery Center layout: rerun the exact Delivery Center action and viewport. Do not rerun backend solvers or the full visual matrix.
- PT-03 fails in Step 2 metrics: rerun Step 2 and the Step 2 -> Step 3 dependency. Do not restart Step 0, Step 1 or unrelated Delivery.

## 10. Release decision

The release decision uses:

- the retained green baseline
- all focused delta evidence since that baseline
- the final prototype route matrix
- open P0 and P1 findings
- actual customer-facing outputs

Production acceptance does not require rerunning every historical test after every delta.

A full repository suite remains available as an optional diagnostic or explicitly authorized release action. It is not the default Heartweb prototype gate.

## 11. Required Root-Sisyphus report after each fix

Root-Sisyphus reports:

```text
Change ID:
Observed failure:
Changed files and symbols:
Affected route, flow and gate:
Focused red test:
Direct closure tests selected:
Why each test is in scope:
Unrelated tests deliberately retained from baseline:
Result:
Remaining blocker:
Next product task:
```

Reports must distinguish:

- previous baseline evidence
- new focused evidence
- not assessed areas

They must not describe a focused regression pass as a complete Full-System test.

## 12. Enforcement for new sessions

`AGENTS.md` and `CLAUDE.md` point to this file. New sessions must read it before:

- creating a test plan
- adding a test todo
- running a test command
- requesting independent review
- declaring a gate complete

If another plan, skill, review template or worker instruction conflicts with this file, this file wins unless Raphael explicitly changes the policy.
