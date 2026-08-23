# Deferred Change and Integration Backlog

**Author:** Raphael Rechberger
**Status:** Current backlog authority
**Updated:** 2026-08-22
**Canonical file:** `00_admin/DEFERRED_INTEGRATION_BACKLOG.md`

## Purpose

This file records mandatory corrections and deferred improvements without allowing them to disappear or silently expand the current release scope.

Capturing an item does not authorize implementation unless its status is `approved_for_integration` or it is promoted to an active P0/P1 blocker.

## Status

- `captured`
- `triaged`
- `approved_for_integration`
- `in_progress`
- `verification`
- `verified`
- `rejected`
- `superseded`

## Priority

- `P0`: active production or data-integrity emergency
- `P1`: blocks the accepted first Production product
- `P2`: mandatory integration or pre-master requirement
- `P3`: valuable enhancement
- `P4`: optional experiment

## Backlog index

| ID | Area | Work | Priority | Status | Activation |
|---|---|---|---|---|---|
| DIB-001 | SEO and GEO quality | Restore approved Step-4A and Step-4B quality contracts | P1 | approved_for_integration | Pre-release under bounded PQ-4 |
| DIB-002 | Entry documentation | Reconcile AGENTS, CLAUDE and README | P2 | verification | Isolated documentation branch complete, final refresh at integration gate |
| DIB-003 | Documentation corpus | Classify and reconcile all docs | P2 | verification | Isolated documentation branch complete, final refresh at integration gate |
| DIB-004 | Repository hygiene | Clean confirmed stale and legacy files | P2 | triaged | Post-release stable checkpoint |
| DIB-005 | Diagnostics | Minimal shared timestamped diagnostic trace | P2 | approved_for_integration | After Sprint 5E, before targeted Production audit |
| DIB-006 | Prompt output quality | Restore release-critical Promptworkflow parity | P1 | approved_for_integration | After DIB-005, before targeted Production audit |

## DIB-001: Step-4A and Step-4B quality restoration

- **Problem:** The V2 safety architecture exists, but approved Copywriter and Developer quality requirements are not fully enforced.
- **Required outcome:** Restore complete professional briefing and page-spec quality through existing schemas, prompts, validators, renderers, gates and Console review.
- **Includes:** Hero Direct Answer, Semantic Triples, Evidence Containers, evidence-bearing data, entity binding, semantic sections, safe Local SEO, schema correspondence and professional Developer output.
- **Plan:** `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`
- **Acceptance:** Machine checks, negative fixtures and representative human output review pass without weakening V2 safety.

## DIB-002: Entry documentation reconciliation

- **Problem:** AGENTS, CLAUDE and README described the pre-V2 Claude Desktop workflow and could mislead new agents.
- **Current work:** Build complete V2 replacements in branch `docs/repository-authority-index-2026-08-22`.
- **Acceptance:** Entry docs point to current architecture, Product State, Decisions, indexes, Production-first sequence, Delivery, Notion boundary, n8n role and extension rules. Final volatile facts are refreshed from the stable Feature commit.
- **Current result:** Full AGENTS, CLAUDE and README V2 replacements exist in the isolated branch. Final volatile facts and links are refreshed at the integration gate.

## DIB-003: Documentation corpus classification

- **Problem:** Current strategy, historical manuals, superseded plans, PDFs and audit Evidence were mixed.
- **Current work:** Deterministic lifecycle and authority registry, visible lifecycle banners, current architecture docs and area indexes.
- **Acceptance:** Every docs and plan source is current, deferred, needs reconciliation, historical, superseded or Evidence. Historical sources remain available but are excluded from default retrieval.

## DIB-004: Repository hygiene

- **Problem:** Stale dependency artifacts, rejected demo source, duplicate images, legacy provider contracts and historical generators increase confusion.
- **Activation:** Post-release at a stable checkpoint.
- **Acceptance:** Every deletion or archive action is evidence-backed, audit history remains intact, no live dependency is removed and the complete suite remains green.

## DIB-005: Minimal shared diagnostic trace

- **Goal:** Automated smoke tests and Raphael's manual walkthrough write the same directly readable local trace so Hermes and root Sisyphus can reconstruct a failure without manual log export.
- **Scope:** One small timestamped run history and a `current` pointer using existing API, event, transition and browser Evidence.
- **Required content:** trace ID, timestamps, build, project, run, step, action, route, expected and rendered actions, API result, stable error code, Transition result, event reference, canonical readback, last success and first failure.
- **Non-goals:** no dashboard, database, log server, distributed tracing, external telemetry or OMO child-session monitoring.
- **Acceptance:** One success, validation failure, stale conflict, missing action, server error, QA-harness error and cross-run regression can be reconstructed without secrets.
- **Clarification:** DIB-005 is not a Germany-to-international or broad Geo expansion task.

## DIB-006: Release-critical Promptworkflow quality

- **Problem:** The V2 migration improved safety but did not transfer every output-critical requirement from the original prompts.
- **Pre-release scope:**
  - PQ-0 bounded requirement matrix
  - PQ-1 Step-1B and Step-1C output fidelity
  - PQ-2 real Step-2 provider Evidence to Step-3 solver chain
  - PQ-4 Step-4A and Step-4B professional quality with DIB-001
- **Post-release:** PQ-3 performance semantics before day 30 and PQ-5 real-output parity after the first customer run.
- **Plan:** `.hermes/plans/2026-08-21-prompt-quality-preservation-v2-restoration.md` after final branch refresh.
- **Acceptance:** Professional outputs, real typed metric flow, positive and negative tests and no regression in identity, Evidence, revisions, gates or tenant safety.

## Intake rule

New findings record:

- source and date
- observed behavior
- expected behavior
- affected workflow step and files
- defect or enhancement classification
- dependency and risk
- acceptance scenario
- supersession links

New UI feedback is not converted directly into isolated cosmetic patches. It is evaluated against task value, the Production-first cut-line and the screen-action model.

## Integration procedure

1. Review active and deferred items.
2. Resolve duplicates through supersession, not deletion.
3. Separate release blockers from post-release enhancements.
4. Map approved work to existing architecture seams.
5. Implement one bounded package.
6. Run focused tests and an appropriate final gate.
7. Update Project State, Decisions, documentation registry and backlog status.
8. Request Raphael approval before commit, merge, deployment or external write.
