# Deferred Change and Integration Backlog

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Created:** 2026-08-20
**Status:** Active capture log
**Canonical file:** `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`

## Purpose

This file is the canonical intake for findings, problems, UI feedback, SEO and GEO improvements, integration needs, and quality refinements discovered while the current base system is being completed.

Capturing an item here does not authorize immediate implementation. The current base workflow must first be completed, independently verified, and proven stable. Backlog items are then triaged and implemented coherently in a dedicated integration sprint.

## Protected Current Scope

This backlog does not defer or replace requirements that are already part of the active base implementation.

Current binding sources remain:

- `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- `.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md`
- `.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md`
- `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
- `standards/workflow/workflow-graph.json`
- `standards/quality/quality-gate-registry.json`

Examples of active scope that must not be demoted to this backlog:

- real local workflow from Step 0 through Step 4b
- German single-admin Operator Console
- artifact content readback, editing, revisions, comparison, validation, approval, rejection, and rerun
- deterministic delivery packages and exports
- final task-based browser QA and completion audit
- deterministic manual Notion import and complete task matrix for the first local release; live one-way project creation remains PR-003 and does not block M10

## Activation Gate

Backlog implementation starts only when all of the following are true:

1. The current Sprint 5 and Sprint 5E base implementation is complete.
2. The local Step-0-through-Step-4b Golden Path is independently verified.
3. The German single-admin interface passes task-based QA.
4. Delivery and export paths pass deterministic and security verification.
5. There are no open P0 or P1 base defects.
6. Raphael explicitly authorizes the integration sprint.

## Intake Rules

1. Record findings immediately, but do not silently implement them.
2. Preserve Raphael's intent and wording in the source note.
3. Link every item to concrete files, sessions, screenshots, or observed behavior when available.
4. Separate defects from enhancements and strategic changes.
5. Do not create a second workflow state authority or duplicate an existing contract.
6. Prefer extending existing schemas, services, UI workspaces, and gates.
7. Mark conflicts and supersession explicitly.
8. A backlog item is not complete until its acceptance criteria are verified.
9. Current production blockers remain in `PROJECT_STATE.md`; this backlog is not a place to hide active blockers.
10. Secrets, credentials, and raw tokens must never be copied into this file.

## Status Lifecycle

- `captured`: Recorded but not yet analyzed.
- `triaged`: Scope, dependencies, and affected architecture identified.
- `approved_for_integration`: Raphael approved implementation in the integration sprint.
- `in_progress`: Implementation has started.
- `verification`: Implementation exists and is undergoing independent verification.
- `verified`: Acceptance criteria are proven.
- `rejected`: Deliberately not implemented, with rationale.
- `superseded`: Replaced by another backlog item or decision.

## Categories

- `SEO_GEO_QUALITY`
- `UI_UX`
- `WORKFLOW`
- `COPYWRITER_HANDOFF`
- `DEVELOPER_HANDOFF`
- `NOTION`
- `N8N`
- `PROVIDER`
- `DELIVERY_EXPORT`
- `MEASUREMENT_PERFORMANCE`
- `SECURITY_RELIABILITY`
- `DOCUMENTATION`
- `REPOSITORY_HYGIENE`
- `OBSERVABILITY_DIAGNOSTICS`
- `PROMPT_OUTPUT_QUALITY`

## Priority

- `P0`: Active production or data-integrity emergency. Must not wait in this backlog.
- `P1`: Blocks the accepted base product. Promote to current blocker.
- `P2`: Mandatory integration-sprint requirement.
- `P3`: Valuable enhancement.
- `P4`: Optional idea or experiment.

## Backlog Index

| ID | Category | Title | Priority | Status | Activation | Detail |
|---|---|---|---|---|---|---|
| DIB-001 | SEO_GEO_QUALITY | Restore approved GEO requirements to V2 Step 4a and 4b contracts | P1 | verification | Local contract and renderer restoration complete; real output proof remains in M10 | `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` |
| DIB-002 | DOCUMENTATION | Reconcile AGENTS, CLAUDE and README with the V2 runtime and product architecture | P2 | verified | Entry documents align with active V2 and DEC-0031 authority | `AGENTS.md`, `CLAUDE.md`, `README.md` |
| DIB-003 | DOCUMENTATION | Classify and reconcile the complete docs corpus | P2 | verified | All 18 registry entries classified and documentation QA passed | `docs/` |
| DIB-004 | REPOSITORY_HYGIENE | Execute repository hygiene and legacy cleanup from the full tree audit | P2 | triaged | Post-release at a stable checkpoint | `00_admin/audits/2026-08-21-repository-hygiene/` |
| DIB-005 | OBSERVABILITY_DIAGNOSTICS | Add a shared local diagnostic trace and timestamped run history | P2 | verified | Implemented and evidenced under M07 | `00_admin/audits/2026-08-22-m07-diagnostic-trace/` |
| DIB-006 | PROMPT_OUTPUT_QUALITY | Restore only release-critical Promptworkflow quality before first production | P1 | verification | Local PQ-0, PQ-1, PQ-2 and PQ-4 closure complete; real-output proof remains in M10 | `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md` |
| DIB-007 | SECURITY_RELIABILITY | Make local Operator Console process ownership and shutdown unambiguous | P3 | captured | Post-consolidation lifecycle hardening unless it blocks M10 | `scripts/start_operator_console.py`, local PID record and Windows launcher behavior |

## DIB-001: Restore approved GEO requirements to V2 Step 4a and 4b contracts

- **Status:** `verification`
- **Priority:** `P1`
- **Category:** `SEO_GEO_QUALITY`
- **Captured:** 2026-08-20
- **Source:** Session `20260817_151731_bc9488`, ADR-011, repository comparison on 2026-08-20
- **Problem:** The GEO architecture remains present, but concrete approved Copywriter and Developer quality requirements are not fully enforced by the current executable V2 Step-4a and Step-4b schemas, prompts, validators, and renderers.
- **Required outcome:** Restore the Hero Direct Answer, Semantic Triples, Evidence Containers, evidence-bearing data points, definitive-language guidance, enhanced entity bindings, semantic sections, GEO markup, and related admin review functions without replacing the current workflow architecture.
- **Detailed plan:** `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`
- **Dependencies:** Stable base workflow, stable admin interface, stable artifact review and revision surfaces.
- **Current evidence:** Local typed contracts, validators, renderers, gates and Console review were restored under M08 PQ-4. The item remains in `verification` until a real M10 output proves the professional Copywriter and Developer result.
- **Acceptance:** Defined in the detailed plan and requires a real controlled-project quality proof.

## DIB-002: Reconcile AGENTS, CLAUDE and README with the V2 runtime and product architecture

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `DOCUMENTATION`
- **Captured:** 2026-08-21
- **Source:** Raphael observation and repository verification on 2026-08-21
- **Current behavior:** AGENTS, CLAUDE, README, CHANGELOG, current architecture and generated onboarding reflect the V2 runtime and active DEC-0031 authority. The superseded DEC-0022 merge-timing sentence was replaced through the protected-file consent gate.
- **Problem:** Resolved. Entry documents no longer preserve an active pre-V2 or superseded merge-timing claim.
- **Expected outcome:** Update all three documents from verified repository facts, preserve stable global rules, separate current implementation from planned or simulated capability, add accurate navigation, and remove obsolete commands or architectural claims.
- **Affected workflow steps:** Repository onboarding, every agent session, product presentation, final handoff, branch consolidation.
- **Affected files or services:** `AGENTS.md`, `CLAUDE.md`, `README.md`, linked project-state, decision, architecture, integration, UI, and delivery documents.
- **Dependencies:** Promoted into the DEC-0031 master consolidation from the stable M09 and current M10 implementation state.
- **Risks and conflicts:** Updating too early can create repeated churn. Waiting beyond the Final-Gate would publish misleading agent instructions and public documentation.
- **Acceptance criteria:** Current architecture and commands are factually correct; implemented, simulated, planned, and deferred capabilities are distinguished; all primary links resolve; no obsolete v1.2 or no-CLI claims remain; documentation review passes before `master` fast-forward.
- **Resolution Evidence:** Protected AGENTS edit approved by Raphael on 2026-08-26; `00_admin/ONBOARDING_REFERENCE.md`; `python -m unittest tests.test_repository_index`; `hermes verify --json`.
- **Supersedes:** none
- **Superseded by:** none

## DIB-003: Classify and reconcile the complete docs corpus

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `DOCUMENTATION`
- **Captured:** 2026-08-21
- **Source:** Raphael observation and complete `docs/` inventory on 2026-08-21
- **Current behavior:** All 18 registered `docs/` records are explicitly classified. Current authorities were reconciled, historical and superseded Markdown files have visible lifecycle labels, the historical HTML map has a visible banner, and the two Evidence PDFs remain immutable and opt-in.
- **Problem:** Several files still claim direct AgentSEO operation, Solver v1.2, a missing JSON-LD CLI, seven prose gates, manual Claude Desktop prompt execution, manifest status authority, direct Notion MCP writes, or full production readiness. These claims conflict with the current V2 Core, Provider Gateway, Transition Service, machine/human gate registry, single-admin Console, Delivery plan, and open completion gates.
- **Expected outcome:** Classify every file as current authority, current strategy, historical baseline, superseded plan, external handoff, or generated artifact. Update current documents, add explicit supersession headers to historical sources, regenerate or archive stale PDFs, preserve evidence history, and create one accurate cross-linked docs index.
- **Affected workflow steps:** Repository onboarding, external review, Jesse presentation, operator training, Copywriter and Developer handoff, final release.
- **Affected files or services:** All 18 registered `docs/` sources, README navigation, generated lifecycle indexes and canonical state/decision links.
- **Dependencies:** Promoted into the DEC-0031 master consolidation; current runtime, Delivery and integration boundaries are defined by active Decisions and the Production Architecture.
- **Risks and conflicts:** Deleting historical evidence would damage traceability. Leaving old files unlabeled would mislead agents, auditors, Jesse, and future operators.
- **Acceptance criteria:** Every docs file has an explicit lifecycle classification; current operational claims match tested behavior; superseded plans are clearly labeled and excluded from current setup instructions; PDFs match their canonical source or are archived; all links resolve; documentation QA passes before `master` fast-forward.
- **Resolution Evidence:** `00_admin/audits/2026-08-26-repository-consolidation/DOCUMENT_LIFECYCLE_RECONCILIATION.md`; `00_admin/ONBOARDING_REFERENCE.md`; `python -m unittest tests.test_repository_index` with 16 of 16 tests passing.
- **Supersedes:** none
- **Superseded by:** none

## DIB-004: Execute repository hygiene and legacy cleanup from the full tree audit

- **Status:** `triaged`
- **Priority:** `P2`
- **Category:** `REPOSITORY_HYGIENE`
- **Captured:** 2026-08-21
- **Source:** `00_admin/audits/2026-08-21-repository-hygiene/REPOSITORY_HYGIENE_AND_AUTHORITY_AUDIT.md`
- **Current behavior:** The active core coexists with a 21.4 MB stale native binding, a stale preview PID, one exact duplicate 1.17 MB plan image, 16 production-unreachable files from the rejected demo UI, three legacy direct-AgentSEO contracts, historical generators, mixed-lifecycle plans, and unindexed audit evidence.
- **Problem:** These items increase project-tree noise, confuse source authority, and can be accidentally committed or presented as current functionality. Deleting them during active browser or delivery work could still remove useful evidence or a hidden dependency.
- **Expected outcome:** After the active gates, prove each candidate unused, remove or archive it deliberately, preserve immutable audit/checkpoint history, add plan/docs/audit indexes, reconcile CHANGELOG and entry documents, and leave a clean final repository tree.
- **Affected workflow steps:** Browser QA, Sprint 5E Delivery, final audit, documentation QA, final branch consolidation.
- **Affected files or services:** `.gitignore`, `apps/operator-console/src/dev`, `apps/operator-console/src/features`, `.hermes/plans`, `mcp/tool-contracts`, `scripts`, `00_admin/audits`, `CHANGELOG.md`.
- **Dependencies:** Stable browser evidence, Delivery completion, final TypeScript import graph, final Python/runtime reference sweep, DIB-001 through DIB-003 decisions.
- **Risks and conflicts:** Removing audit history, active fixtures, Package 4 code, or OMO continuation state is prohibited. Cleanup must be path-specific and evidence-backed.
- **Acceptance criteria:** No stale dependency/PID artifacts; no unreachable rejected demo code; one canonical architecture image; legacy contracts and generators classified; current plan/docs/audit indexes present; no secret or path leakage; the affected cleanup dependency closure and applicable release-matrix cells are green; final Git tree and links are verified before `master` fast-forward.
- **Supersedes:** none
- **Superseded by:** none

## DIB-005: Add a shared local diagnostic trace and timestamped run history

- **Status:** `verified`
- **Priority:** `P2`
- **Category:** `OBSERVABILITY_DIAGNOSTICS`
- **Captured:** 2026-08-21
- **Source:** Raphael clarification on 2026-08-21. The automated final smoke test and Raphael's later manual operator walkthrough must write the same directly readable diagnostic evidence. Raphael must not export, package, collect, or upload logs for Hermes.
- **Goal:** When either the automated smoke test or Raphael's manual flow encounters an error, missing action, wrong blocker, bottleneck, false success, or later inconsistency, Hermes can immediately read the current or historical local trace, reproduce or verify the problem, and prepare a concrete diagnosis and fix proposal. If implementation is required, Hermes gives root Sisyphus the trace ID and evidence path. Root Sisyphus reads the same files and works from the same facts.
- **Required sequence:** Sprint 5E completes first. The minimal diagnostic trace is then implemented before the Sprint-5 final smoke test and audit. The final automated smoke test must already use it. The same mechanism remains active for Raphael's later manual walkthrough and the real AHD pilot.
- **Minimum implementation:** Write one small structured trace per automated smoke-test or operator run to one stable shared local path that both Hermes on the host and root Sisyphus through the mounted workspace can read directly. Keep an append-only timestamped run index plus a simple `current` pointer to the latest run. Closing a run makes its trace immutable; a retry or later test receives a new trace ID. Use existing event, error, API, and browser evidence instead of adding a new database, service, dashboard, or external observability platform.
- **Minimum trace content:** Run start and end timestamps; ordered event timestamps; trace ID; build/version; tenant, project, run, step, gate, revision, artifact and route when available; expected server-authorized actions; actually rendered, disabled, and missing actions; operator or test action; API method and status; stable error code and remediation; Transition Service result; emitted event reference; canonical readback result; browser console and classified network failure; last successful operation; first failing operation; and screenshot path only when useful.
- **Direct diagnostic workflow:** Raphael reports the approximate step, action, or time of the problem. Hermes reads the `current` trace or searches the timestamped run history by time, project, run, step, action, trace ID, or error code. Hermes verifies the mismatch, compares it with earlier runs when useful, explains the causal chain, and proposes the smallest safe fix. Hermes contacts only root Sisyphus when implementation is needed. No OMO child session is inspected or controlled.
- **Affected workflow steps:** Automated Sprint-5 final smoke test, final audit, Raphael's manual operator walkthrough, real AHD pilot, and all Operator Console actions from intake through Delivery and recovery.
- **Affected files or services:** Existing Operator Console action seam, Operator API, Transition Service, event store, stable error catalog, browser smoke-test harness, and one shared local diagnostic path.
- **Non-goals:** No new observability platform, dashboard, distributed tracing stack, log server, second state store, external telemetry, manual export flow, hidden model reasoning, full prompt capture, or broad instrumentation of every internal development action.
- **Dependencies:** Stable Sprint-5 UI and action surface, Sprint 5E Delivery actions, current event catalog, and stable error routing.
- **Risks and conflicts:** Diagnostic files are evidence only and never change canonical state. They must exclude credentials, tokens, authorization headers, unrestricted customer documents, cross-tenant records, and OMO child-session data. History retention and file size must remain bounded without overwriting or silently rewriting retained closed runs.
- **Acceptance criteria:**
  1. The automated final smoke test creates the shared trace automatically and requires no manual log collection.
  2. Raphael's later manual walkthrough writes the same trace format and updates the stable `current` pointer automatically.
  3. Every closed run remains immutable in a timestamped index; `current` points to the latest run without replacing historical evidence.
  4. Hermes can read the latest or a historical trace directly from the shared workspace and identify the last success, first failure, relevant action, API result, transition/event evidence, and canonical readback.
  5. Root Sisyphus can read the same trace and evidence path when Hermes assigns a verified fix, without any child-session inspection.
  6. An expected-versus-rendered action check identifies an allowed action missing from the UI, an unexpected action, and a disabled action with the wrong or missing blocker reason.
  7. One success, one validation failure, one stale-confirmation conflict, one missing-action mismatch, one server error, one QA-harness error, and one regression between two timestamped runs are reconstructable from the retained traces.
  8. No secrets, unrestricted customer documents, cross-tenant data, hidden reasoning, or external telemetry are recorded.
  9. The implementation remains small, uses existing evidence seams, and keeps the affected diagnostic dependency closure plus applicable prototype-matrix cells green under `standards/testing/PROTOTYPE_TEST_POLICY.md`.
- **Verification evidence:** M07 implementation and real browser/persistence evidence under `00_admin/audits/2026-08-22-m07-diagnostic-trace/`; current trace root `var/operator-diagnostics/v1/` remains gitignored and directly readable.
- **Supersedes:** none
- **Superseded by:** none

## DIB-006: Preserve original Promptworkflow output quality in V2 contracts

- **Status:** `verification`
- **Priority:** `P1`
- **Category:** `PROMPT_OUTPUT_QUALITY`
- **Captured:** 2026-08-21
- **Source:** Raphael approval following `00_admin/audits/2026-08-21-prompt-quality-preservation/READ_ONLY_PROMPT_PARITY_AUDIT.md`
- **Behavior at capture:** The V2 migration improved Domain, State, Evidence, Provider, Revision, Gate, and Transition integrity, while several output-critical requirements were incomplete compared with the original Desktop Promptworkflow and master prompt baseline.
- **Current evidence:** PQ-0, PQ-1, PQ-2 and PQ-4 were restored and accepted in their local M08 scope. Typed fields, fixtures, validators, renderers, the Step-2-to-Step-3 solver seam and Console review are present. The item remains in `verification` because real provider-backed Step-2 quality, the complete M10 output chain and professional human review are not yet proven.
- **Problem:** The existing final audit could validate a technically safe but output-thin workflow. The final Heartweb product must preserve the original editorial, SEO, GEO, conversion, planning, presentation, and handoff requirements while keeping the current V2 architecture.
- **Required outcome:** Execute only the release-critical scope from `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md`: bounded PQ-0, PQ-1, PQ-2, and PQ-4. Map each original requirement needed for the first production route to one current authority, restore missing typed fields and behavior through existing schemas, validators, renderers, Quality Gates and Admin surfaces, prove the real Step-2-to-Step-3 solver path, and complete DIB-001 for Step 4A and Step 4B. PQ-3 and PQ-5 are post-release.
- **Required sequence:** Do not interrupt the current Browser-QA run or Sprint 5E. After a stable controller-verified Sprint-5E checkpoint, implement DIB-005, then bounded PQ-0, PQ-1, PQ-2, and PQ-4. Run a targeted Production Release audit immediately afterward.
- **Affected workflow steps:** Pre-release: Step 1B, Step 1C, Step 2, Step 3, Step 4A, Step 4B, Delivery handoff, and targeted production smoke. Post-release: Step 3B, real-output parity, broad rollout, and final maturity gate.
- **Dependencies:** Browser QA complete, Sprint 5E complete, stable checkpoint, DIB-005, preserved prompt baseline, and explicit package-by-package verification.
- **Risks and conflicts:** Do not copy old prompts wholesale into production, reintroduce prompt-controlled state, call providers directly, duplicate authorities, or weaken lineage and safety. Original prompts remain immutable requirement sources, not executable production authority.
- **Acceptance criteria:**
  1. PQ-0 classifies every output-critical original requirement as preserved, strengthened, restored, deferred with explicit approval, or not applicable.
  2. Step 1B and Step 1C produce professional customer and developer artifacts matching approved original intent.
  3. A real provider-backed Step-2 artifact supplies the actual deterministic solver with all required metrics and classifications without manual side data.
  4. DIB-001 restores complete Step-4A Copywriter and Step-4B Developer and GEO quality needed for the first output chain.
  5. Positive and negative fixtures fail or pass for the intended quality requirement, not only schema presence.
  6. No existing V2 Domain, State, Provider, Evidence, Revision, Approval, Transition or tenant-isolation invariant regresses.
  7. A targeted Desktop and core-action Production Release audit passes with deterministic Delivery and no open P0/P1.
  8. Step 3B semantics and the full real-output parity audit are recorded in `00_admin/POST_RELEASE_BACKLOG.md` and do not block the first controlled production output.
- **Supersedes:** none
- **Superseded by:** none

## DIB-007: Make local Operator Console process ownership and shutdown unambiguous

- **Status:** `captured`
- **Priority:** `P3`
- **Category:** `SECURITY_RELIABILITY`
- **Captured:** 2026-08-26
- **Source:** Repository-freeze operation on Windows. Closing the browser did not itself prove that the locally started Console and Gateway processes had stopped. A stale PID record remained after the process was already absent.
- **Current behavior:** `scripts/start_operator_console.py` starts a persistent local service and records process metadata outside the repository. Browser-window closure is not the service shutdown authority. The existing fail-closed cleanup correctly refused to remove an unproven PID record until PID and listener absence were verified.
- **Problem:** The lifecycle is technically recoverable but not sufficiently obvious to the single operator. A stale record can look like project corruption even though it contains no project state.
- **Expected outcome:** Provide one explicit start, status and stop path that verifies the process tree and bound ports, removes only proven-stale metadata and reports a structured result. The browser should not be presented as the process owner unless the launcher is deliberately changed to make it one.
- **Non-goals:** Do not couple canonical workflow state to local PIDs, autostart the Hermes Gateway, kill unrelated Python processes, or hide shutdown failures.
- **Acceptance criteria:** Start creates one authoritative record; status distinguishes running, stopped and stale; stop terminates only the recorded process tree; stale cleanup requires process and listener absence; repeated stop is idempotent; Windows launcher tests and a real local smoke pass.
- **Activation:** Post-consolidation lifecycle hardening. Promote into M10 only if the launcher prevents the required operator run.
- **Supersedes:** none
- **Superseded by:** none

## UI and UX Findings Intake

Future UI observations from Raphael are added as individual `DIB-UI-NNN` items. Each item must record:

- exact screen or workflow step
- what the admin is trying to accomplish
- observed problem
- expected behavior
- screenshot or session evidence when available
- affected API or domain command, if any
- whether it is a defect, usability issue, or enhancement
- acceptance scenario from the admin's perspective

UI feedback must not be converted directly into isolated visual patches. It is reviewed against the screen-action map, current workflow authority, and overall information architecture during the integration sprint.

## New Item Template

```markdown
## DIB-NNN: Short title

- **Status:** `captured`
- **Priority:** `P2 | P3 | P4`
- **Category:** `<category>`
- **Captured:** `<YYYY-MM-DD>`
- **Source:** `<session, screenshot, file, user quote, test, or observed behavior>`
- **Current behavior:**
- **Problem or opportunity:**
- **Expected outcome:**
- **Affected workflow steps:**
- **Affected files or services:**
- **Dependencies:**
- **Risks and conflicts:**
- **Acceptance criteria:**
- **Supersedes:** `none | DIB-NNN`
- **Superseded by:** `none | DIB-NNN`
```

## Integration Sprint Procedure

When the activation gate is reached:

1. Review every `captured` and `triaged` item.
2. Remove duplicates by linking and superseding, never by deleting history.
3. Separate mandatory corrections from optional experiments.
4. Map each approved item to existing architecture seams.
5. Define package boundaries and regression tests.
6. Approve the integration-sprint scope with Raphael.
7. Implement one coherent package at a time.
8. Run specification, quality, security, and task-based UI reviews.
9. Update this log with exact evidence and final status.

## Change Log

| Date | Change | Source |
|---|---|---|
| 2026-08-26 | DIB-002 and DIB-003 promoted into DEC-0031 master consolidation; DIB-005 verified; DIB-001 and DIB-006 moved to real-output verification | DEC-0031 and current Project State |
| 2026-08-26 | DIB-007 captured for unambiguous Windows Console process ownership and shutdown | Repository-freeze runtime observation |
| 2026-08-21 | Production-first Cut-Line: DIB-001 and release-critical DIB-006 stay pre-release; Step 3B, real-output parity, integrations, mobile polish, docs and cleanup moved post-release | Raphael decision, DEC-0024 |
| 2026-08-21 | DIB-006 approved for full Promptworkflow quality preservation before the existing final audit | Raphael approval and read-only parity audit |
| 2026-08-21 | DIB-005 approved for a shared directly readable diagnostic trace and timestamped history in automated and manual smoke tests | Raphael request and clarifications |
| 2026-08-21 | DIB-004 registered from complete repository hygiene and authority audit | Raphael request and repository verification |
| 2026-08-21 | DIB-003 registered after complete docs-corpus freshness and authority audit | Raphael observation and repository verification |
| 2026-08-21 | DIB-002 registered for mandatory entry-document reconciliation before final master merge | Raphael observation and repository verification |
| 2026-08-20 | Canonical deferred backlog created and DIB-001 registered | Raphael Rechberger and repository audit |
