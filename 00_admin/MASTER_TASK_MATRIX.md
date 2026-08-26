# Heartweb Master Task Matrix

**Author:** Raphael Rechberger
**Status:** Current project task router
**Updated:** 2026-08-26
**Machine source:** `00_admin/MASTER_TASK_MATRIX.json`
**Binding test policy:** `standards/testing/PROTOTYPE_TEST_POLICY.md`

## 1. What this file solves

This is the stable project hierarchy from the current implementation to the first controlled local production output.

The canonical product roadmap remains `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`. It contains Sprint 0 through Sprint 11. The inserted Sprint 5E creates 13 actual execution stages. The M01 through M10 list below is only a Production-first status overlay and does not replace or renumber the canonical Sprint roadmap.

Root-Sisyphus may split one Main Task into more or fewer internal todos. Those internal counts are execution detail and may change. They do not change the fixed project denominator.

The stable pre-release progress is always reported as:

```text
completed Main Tasks / 10 fixed Main Tasks
current Main Task
completed current subtasks / current subtask total
active subtask
next Main Task
```

New defects are added under the affected Main Task. They do not create a new overall denominator.

## 1A. Canonical 13-stage Sprint roadmap

| Stage | Canonical Sprint | Scope | Status |
|---|---|---|---|
| 1 | Sprint 0 | Freeze candidate baseline | completed |
| 2 | Sprint 1 | Stabilize runtime candidates | completed |
| 3 | Sprint 2 | Operator, ticket and event contracts | completed |
| 4 | Sprint 3 | V2 output contracts and prompt migration | completed |
| 5 | Sprint 4 | Local Workflow API and simulators | completed |
| 6 | Sprint 5 | German Operator Console | completed |
| 7 | Sprint 5E | Local Delivery and export foundation | completed |
| 8 | Sprint 6 | AHD Step 0 and Step 1 | pending |
| 9 | Sprint 7 | AHD Step 1B and Step 1C | pending |
| 10 | Sprint 8 | AHD Step 2 and Step 3 | pending |
| 11 | Sprint 9 | AHD Step 4A and Step 4B | pending |
| 12 | Sprint 10 | Presentation matrix and Jesse demo | pending |
| 13 | Sprint 11 | Final integration and maturity gate | pending |

Current canonical position: **7 of 13 execution stages completed**. Sprint 5E Tasks 1 through 8 and the bounded interstage gates M07, M08, M08L and M09 are complete in their documented scopes. M10 is active on the real CL pilot. Step 0 is released and Step 1 is `in_progress`; the complete real Step-0-through-Step-4B route and first customer package are still open.

## 2. Current executive snapshot

**Snapshot:** 2026-08-26 during M10 and the DEC-0031 repository consolidation. This section records the latest material gate. Exact Git refs are read directly from Git and are not cached here.

```text
Release Main Tasks: 9/10 completed
Current Main Task: M10 first controlled local production output
Current real route: CL Step 0 released; Step 1 in_progress without Production Execution or Agent Evidence
Repository: DEC-0031 consolidation authorized; it does not close M10 or Production Acceptance
Next Main Task: no further pre-release Main Task after M10
Runtime: intentionally stopped during repository freeze
```

The prior 563-test green run is retained baseline evidence. Current Task-6 changes use only the affected dependency closure. No automatic full repository rerun or repeated five-lane review is authorized.

## 3. Stable pre-release Main Tasks

| ID | Main Task | Current status | Owner | Estimate remaining | User-visible result |
|---|---|---|---|---|---|
| M01 | Core and workflow foundation | completed | Root Sisyphus | 0h | Project V2, transitions, artifacts, gates, revisions, events and Local API foundation |
| M02 | German Operator Console and browser gate | completed | Root Sisyphus | 0h | German Single-Admin Console with previously verified core actions and responsive Desktop surface |
| M03 | Delivery foundation Tasks 1 through 5 | completed | Root Sisyphus | 0h | contracts, inventory, role packages, manual Notion import pack and secure deterministic ZIP builder |
| M04 | Close Task 6 Local Delivery API | completed | Root Sisyphus | 0h | stable Preview, Create, History, Record, Download, Replay and Recovery API |
| M05 | Activate the existing Uebergabe und Export workspace | completed | Root Sisyphus | 0h | existing verified Console shell now provides typed Delivery preview, create, history, record and ZIP actions |
| M06 | Focused neutral Delivery E2E | completed | Root Sisyphus | 0h | live local UI/API/persistence route produced checkpoint and final ZIP evidence with exact replay |
| M07 | Minimal shared diagnostic trace DIB-005 | completed | Root Sisyphus | 0h | timestamped trace under gitignored `var/operator-diagnostics/v1/`, current pointer, append-only history and real browser evidence |
| M08 | Release-critical output quality restoration | completed | Root Sisyphus | 0h | PQ-0, PQ-1, PQ-2 and PQ-4 locally complete; professional Step 4A/4B output sets and Console review are restored without external execution claims |
| M09 | Route-based Production Release audit | completed in its recorded scope | Root Sisyphus and Hermes | 0h | PT-01 through PT-10 and Desktop Chrome evidence are retained; later real-pilot route defects were corrected separately and require the final affected-closure verification |
| M10 | First controlled local production output | in progress: Step 0 released, Step 1 awaiting production | Raphael, Hermes and Root Sisyphus | 3h to 8h plus external inputs | first approved downloadable customer package and real operator evidence |

Estimates are focused engineering time ranges, not guarantees. They assume no new external blocker, no scope expansion and compliance with the affected-closure test policy.

## 4. Completed M04 detail record

Sections 4 through 9 preserve the completed M04 through M09 task definitions and evidence boundaries. They are historical execution records, not the current queue. M10 in section 10 is the active Main Task.

| ID | Task-6 subtask | Status | Required verification |
|---|---|---|---|
| M04.1 | Delivery API remediation baseline with prior 563-green evidence | completed | retained baseline only |
| M04.2 | Four focused edge regressions | completed | exact red reproducers exist or are being created |
| M04.3 | Canonical role ordering before hashing and persistence | completed | `tests/test_delivery_api_role_order.py` and direct role persistence closure |
| M04.4 | Resolve completed replay and exact recovery before mutable source reads | completed | `tests/test_delivery_api_replay_source_independence.py` and direct replay/recovery closure focused-green |
| M04.5 | Make repeated OpenAPI generation identical | completed | `tests/test_delivery_openapi.py` and direct response-contract closure focused-green |
| M04.6 | Reject symlink/nonregular recovery paths and sort sidecars canonically | completed | `tests/test_delivery_api_recovery_inventory_safety.py` and direct Recovery Inventory closure focused-green |
| M04.7 | Affected-closure gate and Task-6 closeout | completed | direct Delivery admission regressions corrected and rechecked; no 563 rerun and no five-lane review |

### M04 completion result

Task 6 is complete when the five Delivery API operations and their exact replay/recovery paths are focused-green and Root-Sisyphus records the selected tests and excluded baseline areas.

## 5. M05 activate the existing Uebergabe und Export workspace

The German Console, navigation destination, route shell, responsive layout and visual design already existed and had passed the 24-cell visual browser matrix. M05 was not a new Console or route build. At the start of M05, the route intentionally rendered a contract-gate placeholder and issued no Delivery requests. M05 replaced only that placeholder with functional Delivery content wired to the Task-6 API.

### Subtasks

1. Preserve the existing Operator Shell, navigation, responsive layout and route design.
2. Replace the `delivery-contract-gate` placeholder in `OperatorShell.tsx`.
3. Add typed Delivery methods to the existing API client.
4. Show checkpoint and final eligibility.
5. Show included, missing, draft and released items.
6. Show source revision, package size, checksum and unresolved assignees.
7. Add Preview, Create and Download actions for checkpoint and final ZIP.
8. Add Copywriter, Developer and Notion package downloads.
9. Add export history and individual record view.
10. Preserve canonical readback and run only the affected Delivery route cells.

### User-visible gate

Raphael can open and judge the existing Console design and information architecture now. After M05, he can additionally operate the real Delivery Preview, Create, History, Record and Download flow on that existing surface. This should not wait for DIB-005 or full output-quality restoration.

## 6. M06 focused neutral Delivery E2E

### Subtasks

1. Create one neutral project fixture.
2. Preview checkpoint without writes.
3. Create checkpoint package with open blockers clearly reported.
4. Reject premature final export.
5. Create eligible final export.
6. Read history and exact record.
7. Download and extract ZIP.
8. Revalidate checksums.
9. Replay identical export without duplication.
10. Verify Copywriter, Developer and Notion package boundaries.
11. Verify no credentials or absolute host paths.
12. Exercise the exact Delivery Center browser route.

### User-visible gate

After M06, Raphael can perform a controlled local test flow and inspect a real generated package. This is the recommended minimum cutline for the first hands-on session tomorrow.

## 7. M07 diagnostic trace

### Subtasks

1. One timestamped trace ID per run or retry.
2. Append-only historical run index.
3. Stable `current` pointer.
4. Last successful and first failing operation.
5. Project, run, step, gate, route, action, API result and error code.
6. Transition, event and canonical readback references.
7. Same format for automated smoke and Raphael manual walkthrough.
8. No dashboard, new database, external telemetry or hidden model reasoning.

M07 is required before the formal release audit, but it does not need to block Raphael from first seeing and clicking the Console after M05/M06.

## 8. M08 release-critical output quality

### Subtasks

1. PQ-0: map every first-route output requirement to current authority.
2. PQ-1: restore professional Step 1B architecture presentation.
3. PQ-1: restore Step 1C Pillar-template depth and usable design specification.
4. PQ-2: restore Step-2 metrics and research breadth needed for planning.
5. PQ-2: prove the real Step-2 to Step-3 deterministic solver bridge.
6. PQ-4 plus DIB-001: restore Step-4A Copywriter and GEO briefing quality.
7. PQ-4 plus DIB-001: restore Step-4B Developer, HTML, JSON-LD and GEO quality.
8. Verify only the affected step, direct consumer and output cells.

Step 3B semantics, broad real-output parity and multi-archetype expansion remain post-release.

### M08 completion result

PQ-4 closes with 12 locally verified requirement rows and 2 separated external rows. Local fixtures prove contract shape, deterministic rendering, immutable identity, provenance handling, and Console review behavior. Google Rich Results, Screaming Frog, Lighthouse, axe, visual comparison, staging, production, provider, and customer execution remain unsatisfied by local evidence. The requested GitHub WIP snapshot is verified at `wip/m08-output-quality-2026-08-23`, commit `568bb497e57af4f7ec6dc8a13438681bbf423a55`.

## 8A. M08L Hermes Gateway LLM execution adapter

M08L is a release prerequisite on the existing M08 to M09 edge. It does not add an eleventh Main Task or a fourteenth Sprint stage.

Approved Option A ownership:

1. Root Sisyphus implements only the thin Heartweb Hermes-Runs adapter, the smallest fixture-versus-Hermes injection seam, reuse of existing validation and persistence, stable failure translation and focused repository tests.
2. Hermes performs the installed Gateway capability probe, isolated `heartweb-runtime` profile setup, Hermes-managed shared OAuth-pool verification, model and reasoning policy verification, live neutral Gateway proof and independent acceptance review.
3. Heartweb remains the only workflow, artifact, revision and gate authority.
4. OAuth tokens never enter Heartweb, agent prompts, traces, artifacts or Git.
5. M09 begins only after one neutral real LLM call reaches a valid Heartweb artifact candidate and invalid calls fail before canonical persistence.

Production-first cutline: General backend registry, separate execution-record persistence, direct Multi-Provider adapters, delegation contracts, subagent routing and broad benchmark infrastructure are Post-M10. Existing Heartweb runtime authorities are reused before M09.

### M08L completion result

M08L passed a real neutral Step-0 Heartweb runtime call through the isolated Hermes Gateway. The schema-valid Manifest candidate, Context Package and LLM records were atomically persisted in an ephemeral workspace. Provider Run ID, model and token usage were present, no tools were used, and Detailed Health returned zero active runs and agents. Evidence: `00_admin/audits/2026-08-23-m08l-hermes-llm-adapter/SECTION_11_REPORT.md`.

Authority: `.hermes/plans/2026-08-23_141332-hermes-gateway-llm-execution-adapter.md` and DEC-0028.

## 9. M09 route-based Production Release audit

The final prototype uses `standards/testing/PROTOTYPE_TEST_POLICY.md` cells PT-01 through PT-10.

### Required route cells

1. app startup and project selection
2. intake and provisioning
3. sequential Step 0 through Step 4B route
4. revision and Human-Gate route
5. Delivery Preview and Create
6. history, record, ZIP and replay
7. one-way Notion handoff
8. Recovery and fail-fast
9. shared diagnostic trace
10. release-critical Desktop browser smoke

Each cell runs once. A failed cell and its named direct dependents are rerun after a fix. The matrix is not restarted from PT-01.

## 10. M10 first controlled local production output

### Subtasks

1. Chosen pilot and exact CL Project V2 inputs confirmed.
2. Search Deployment, Provider Target `agentseo-de-country`, `DE / 2276 / de`, region and 10 weekly hours confirmed.
3. Step 0 Manifest V2 Revision 3 produced, reviewed, approved, completed and released.
4. Step 1 Run `run-next-7f7e2b778f4521b9` created and held at `in_progress` without fabricated Evidence.
5. Produce Step 1 through the canonical Hermes and Provider Gateway route after the repository freeze.
6. Continue 1B, 1C, 2, 3, 4A and 4B with required provider execution, fail-fast behavior, revisions and Human Gates.
7. Create final Copywriter, Developer, Project Management and Notion packages.
8. Download, extract and inspect the final ZIP and deterministic checksums.
9. Review the professional output with Raphael and obtain the explicit M10 decision.
10. Record concrete corrections from the first real use as new bounded deltas.

## 11. Historical 2026-08-21 hands-on cutline

This section preserves the original short-term sequencing assumptions. M04 through M09 are now complete in their recorded scopes. Current M10 status is defined in sections 2, 3 and 10.

### Target 0: Raphael sees the current Console design

Available now:

- German Single-Admin Console
- six navigation destinations
- Projects, Workflow, Tasks, Artifacts and Reviews workspaces
- visible `Uebergabe und Export` route shell
- previously passed responsive visual evidence

Historical limitation at that checkpoint: the `Uebergabe und Export` page still showed the intentional contract-gate placeholder before M05 replaced it with functional Delivery actions.

### Target A: Raphael uses functional Delivery on the existing product

Required:

- M04 complete
- M05 complete
- local services started
- X01 guided manual walkthrough

Expected remaining focused time from the current snapshot: approximately 3h to 7h.

### Target B: Raphael produces and inspects a controlled local package

Required:

- Target A
- M06 complete

Expected remaining focused time from the current snapshot: approximately 5h to 11h.

This is feasible by tomorrow if no new P0/P1 blocks the affected route and Sisyphus does not re-enter broad test or review loops.

### Target C: first release-quality real provider-backed customer output

Required:

- M07 through M10
- verified real inputs and provider access

Expected additional focused time after Target B: approximately 13h to 28h plus external input or provider delays.

A first hands-on and controlled local output should not wait for Target C.

## 12. Work outside the current Root-Sisyphus queue

| ID | Work | Owner | Activation | Estimate |
|---|---|---|---|---|
| X01 | Raphael hands-on Operator Console walkthrough | Raphael and Hermes | after M05, ideally after M06 | 1h to 2h |
| X02 | Confirm real pilot inputs, deployment, provider target and capacity | Raphael and Hermes | completed for the active CL pilot; repeat for each future pilot | 1h to 3h |
| X03 | Complete DEC-0031 documentation authority and deterministic onboarding consolidation | Hermes | completed and verified on 2026-08-26 | 2h to 5h |
| X04 | Commit, push, branch reconciliation, master fast-forward and Fresh Clone | Hermes with Raphael approval | in progress under DEC-0031 | 1h to 3h |
| X05 | Jesse walkthrough and delivery presentation | Raphael | after M10 | 1h to 3h |
| X06 | Live one-way Notion and n8n integration | future approved integration sprint | post-release | 16h to 40h |
| X07 | Deployment, CMS adapters, mobile polish and broad expansion | future approved phases | post-release | 24h to 80h |

## 13. Post-release queue that does not block tomorrow

- full Step-3B performance semantics
- full real-output parity after first AHD output
- live Notion project creation
- live n8n orchestration
- additional mobile polish
- repository cleanup
- broad archetype and international expansion
- Jesse presentation expansion
- WordPress, Elementor, CMS and deployment adapters

## 14. Stable status reporting rule

The Telegram status job must show:

```text
Release Main Tasks: N/10
Current: Mxx title
Current subtasks: N/M
Active subtask: exact Root todo
Next Main Task: Mxx title
Since last update: concrete completions and checkpoint delta
Blocker: exact Raphael blocker or none
```

It must not present raw Root-Todo totals as overall project completion.

If Sisyphus replaces or expands its Root todo list, the Main Task denominator remains 10.

## 15. Authority and update rule

- This file is the current stable project task router.
- `00_admin/MASTER_TASK_MATRIX.json` is the machine-readable mapping used by the status script.
- Root-Sisyphus todos are dynamic execution detail beneath these Main Tasks.
- `PROJECT_STATE.md` and active Decisions remain product-state authority.
- New findings attach beneath an existing Main Task or enter the deferred/post-release backlog.
- A new Main Task requires an explicit scope decision from Raphael.

## 16. Automation stop boundary

Root-Sisyphus may continue automatically through M07, M08, M08L, M09 and M10. After M10 first controlled local production output is complete, Root-Sisyphus stops and waits for Raphael.

PR-008 and every post-release item require a new explicit authorization. Live Notion, live n8n, deployment, repository cleanup, mobile polish, broad archetypes, international expansion and presentation expansion do not start automatically.

Root-Sisyphus stops earlier only for:

- a pending Root question
- `BLOCKED_NEEDS_RAPHAEL`
- fatal runtime or container failure
- a P0 or P1 that needs a user decision
