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
- final mandatory Notion production integration and assignment workflow when the stable target databases and mappings are available

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

## Priority

- `P0`: Active production or data-integrity emergency. Must not wait in this backlog.
- `P1`: Blocks the accepted base product. Promote to current blocker.
- `P2`: Mandatory integration-sprint requirement.
- `P3`: Valuable enhancement.
- `P4`: Optional idea or experiment.

## Backlog Index

| ID | Category | Title | Priority | Status | Activation | Detail |
|---|---|---|---|---|---|---|
| DIB-001 | SEO_GEO_QUALITY | Restore approved GEO requirements to V2 Step 4a and 4b contracts | P2 | triaged | After stable Sprint 5 and 5E base | `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md` |

## DIB-001: Restore approved GEO requirements to V2 Step 4a and 4b contracts

- **Status:** `triaged`
- **Priority:** `P2`
- **Category:** `SEO_GEO_QUALITY`
- **Captured:** 2026-08-20
- **Source:** Session `20260817_151731_bc9488`, ADR-011, repository comparison on 2026-08-20
- **Problem:** The GEO architecture remains present, but concrete approved Copywriter and Developer quality requirements are not fully enforced by the current executable V2 Step-4a and Step-4b schemas, prompts, validators, and renderers.
- **Required outcome:** Restore the Hero Direct Answer, Semantic Triples, Evidence Containers, evidence-bearing data points, definitive-language guidance, enhanced entity bindings, semantic sections, GEO markup, and related admin review functions without replacing the current workflow architecture.
- **Detailed plan:** `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`
- **Dependencies:** Stable base workflow, stable admin interface, stable artifact review and revision surfaces.
- **Acceptance:** Defined in the detailed plan and requires a real AHD quality proof.

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
| 2026-08-20 | Canonical deferred backlog created and DIB-001 registered | Raphael Rechberger and repository audit |
