# Sprint 5 Operational Completion Contract

**Author:** Raphael Rechberger
**Date:** 2026-08-20
**Status:** Approved for implementation

## Goal

Complete the remaining Heartweb Sprint 5 product so a trained operator can run one complete client-neutral workflow locally through the Operator Console, retain canonical revision and gate control in the Local Core, and export operational handoff packages without requiring live Notion or n8n.

The current product has one interface role only: the Heartweb Admin Operator. This one person performs intake, execution, editing, review, approval and export. Copywriters, developers, reviewers and managers do not receive separate interfaces or accounts in Sprint 5. They receive exported outputs or later Notion records.

## Read First

1. `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
2. `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`
3. `00_admin/PROJECT_STATE.md`
4. `00_admin/DECISIONS.md`
5. `AGENTS.md`
6. `CLAUDE.md`

The first two plan files define the approved product. This contract states the Sprint 5 completion boundary. Sisyphus owns planning, decomposition, delegation, implementation order and internal verification.

## Binding test-policy update from 2026-08-22

`standards/testing/PROTOTYPE_TEST_POLICY.md` controls test selection and retry behavior. The broad verification list below is a coverage inventory for the complete product, not an instruction to rerun complete suites after every change. A previously passed cell retains baseline evidence. After a defect or change, run only the affected dependency closure. A complete repository suite requires new explicit authorization from Raphael.

## Required Operator Journey

A trained operator must be able to:

1. create a local project from a Markdown briefing by upload or paste
2. review the extracted project intake before accepting it
3. start the next legal workflow step through a typed Local API command
4. see exact prompt version, Context Package, run status and resulting artifact revision
5. inspect the machine-gate report and human-gate checklist
6. open a draft artifact in an operator editor
7. save edits only as a new immutable revision
8. compare revisions and re-run validation
9. preview and explicitly confirm approve, reject, request revision, request input, escalate and request waiver actions
10. refresh and display canonical state after every accepted or replayed command
11. proceed through the client-neutral initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`
12. keep Step 3b as a separate not-due 30/60/90 sideflow
13. generate checkpoint and final handoff folders and ZIP files
14. download copywriter, developer and manual Notion import packages
15. operate locally without live Notion or n8n

## Runtime Rules

- The Local Core, Transition Service, Quality Gates and append-only Event Store remain authoritative.
- UI, simulators and future adapters send typed commands only.
- No React component, API adapter or simulator may invent canonical workflow status.
- Human gates require an explicit human decision. Automated tests may use an explicitly labelled test actor only.
- Accepted artifacts are never overwritten. An edit produces a new revision with parent lineage and a fresh hash.
- Exact versioned prompts and validated Context Packages drive runs.
- Missing provider, input, schema, credential or evidence produces a visible fail-fast blocker. No fabricated output and no silent fallback.
- A transport-faithful local simulator may prove orchestration when a live external provider is intentionally absent, but the UI and evidence must label simulation honestly.
- Demo data never appears in real API mode.
- A successful POST is not sufficient. The UI must read back and render the affected canonical projection.
- Retry and replay use stable idempotency and cannot create duplicates.

## Delivery Boundary

Implement the approved Sprint 5E plan before Sprint 6:

- deterministic delivery contracts
- checkpoint and final package policy
- role-specific copywriter and developer packages
- manual Notion import pack
- deterministic ZIP builder
- preview, create, history and download API
- Delivery Center UI
- checksum, extraction, secret, containment and idempotency tests

Live Notion writes, live n8n orchestration, deployment and AHD-specific execution remain outside Sprint 5.

## Required coverage inventory

- focused negative tests first for unsafe and illegal operations
- retained backend baseline plus focused affected-closure delta evidence
- retained frontend baseline plus affected component and route evidence
- TypeScript and production build only when changed client or frontend inputs require them
- OpenAPI generation check only when public API bytes change
- clean-install frontend verification only when dependency or lockfile inputs change
- applicable prototype-matrix browser cells for the changed surface
- keyboard and action-confirmation QA for affected operator actions
- PT-03 neutral Step-0-to-4b route once at the release matrix, with cell-local retry
- checkpoint ZIP generation and extraction
- deterministic ZIP hash replay
- secret and absolute-path scan
- no Em Dash or En Dash characters
- `hermes verify --json` only at a stable gate after explicit Raphael authorization
- `git diff --check`

## Evidence

Write scoped implementation and review reports under:

`00_admin/audits/2026-08-19-e2e-demo/sprint-5/`

The final completion marker is:

`06_SPRINT5_OPERATIONAL_AND_DELIVERY_FINAL_AUDIT.md`

That audit must state exact tests, builds, E2E evidence, browser evidence, remaining external limitations and an honest Go or No-Go decision.

## Hard Stop Conditions

Stop and report exactly `BLOCKED_NEEDS_RAPHAEL: <reason>` only when a decision cannot be resolved from the approved plans, project contracts or existing code.

Do not stop for implementation choices that Sisyphus can resolve professionally.

## Exclusions

- no Sprint 6 or AHD execution
- no live Notion write
- no live n8n dependency
- no deployment
- no merge to master
- no commit or push
- no credential or OAuth work
- no OMO configuration change
- no parallel status authority
- no speculative enterprise expansion beyond the two approved plans
