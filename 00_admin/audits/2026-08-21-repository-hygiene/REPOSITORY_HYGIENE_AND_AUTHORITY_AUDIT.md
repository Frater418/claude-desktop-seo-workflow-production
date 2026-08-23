# Repository Hygiene and Authority Audit

**Project:** Heartweb Claude Desktop SEO Workflow
**Author:** Raphael Rechberger
**Audit date:** 2026-08-21
**Scope:** Complete project directory excluding `.git`, active `node_modules`, build outputs, Python caches, and virtual environments
**Mode:** Non-destructive read and classification audit

## Executive Verdict

The repository contains a substantial and coherent V2 runtime, test, contract, and Operator Console implementation. The core project is not redundant as a whole. The main problem is authority and lifecycle drift around that core:

- current and historical documentation are mixed without labels
- the canonical project state and central Hermes registry lag behind implementation
- a rejected demo frontend remains as unreachable production source
- local runtime and dependency artifacts are visible in the project tree
- older direct-AgentSEO contracts and generators remain beside the Provider Gateway and V2 architecture
- audit evidence is intentionally append-only but lacks a compact index
- plans are not classified as current, completed, deferred, or superseded

No destructive cleanup is authorized by this audit. Cleanup candidates must be handled after the active Sprint 5 and Sprint 5E flow reaches a safe gate.

## Method and Evidence

The audit combined:

- full filesystem inventory and SHA-256 grouping
- `git ls-files` and full porcelain status
- top-level and extension size aggregation
- relative Markdown link scan
- TypeScript production import reachability from `apps/operator-console/src/main.tsx`
- Python import/reference searches
- plan, docs, audit, checkpoint, state, decision, and registry inspection
- current Sisyphus root status and known Sprint 5 evidence

Machine-readable summary:

`00_admin/audits/2026-08-21-repository-hygiene/INVENTORY_SUMMARY.json`

## Inventory Summary

| Metric | Result |
|---|---:|
| Files scanned | 1,023 |
| Bytes scanned | 40,294,577 |
| Git tracked files | 555 |
| Current Git change paths | 125 |
| Inaccessible entries | 0 |
| Exact duplicate groups | 1 |
| Potential duplicate bytes | 1,174,811 |
| Suspicious runtime or temporary artifacts | 6 |
| Files at least 1 MB | 5 |
| Empty files | 2, both intentional Python package markers |
| Confirmed broken relative Markdown links | 0 |
| TypeScript source files | 48 |
| Productively reachable TypeScript files | 17 |
| Unreachable production candidates | 16 |

## Top-Level Classification

| Area | Files | Classification | Required treatment |
|---|---:|---|---|
| `standards/` | 70 | Current authority | Keep, validate, document accurately |
| `services/` | 91 | Current runtime plus active Package 4 code | Keep, complete current audit before cleanup |
| `tests/` | 200 | Current tests, fixtures, historical acceptance evidence | Keep; classify old test documents separately |
| `apps/` | 56 | Current Admin Console plus rejected demo and stale binary | Keep current app; later remove confirmed dead demo and stale binary |
| `00_admin/audits/` | 121 | Append-only implementation and review evidence | Keep; add lifecycle index, do not rewrite history |
| `00_admin/checkpoints/` | 25 | Immutable checkpoint evidence | Keep unchanged |
| `.hermes/plans/` | 10 | Mixed current, deferred, completed, and superseded plans | Add lifecycle classification and deduplicate image |
| `docs/` | 16 | Mixed current architecture, strategy, historical and stale operations docs | Execute DIB-003 before master merge |
| `03_research/` | 5 | Raw research evidence and synthesis | Keep; add compact source index later |
| `prompts/` | 9 | Current V2 prompt contracts with known deferred GEO drift | Keep; execute DIB-001 after stable base |
| `mcp/tools/` | 2 source files | Current deterministic tools | Keep |
| `mcp/tool-contracts/` | 3 | Legacy direct-AgentSEO contracts | Mark legacy or archive after proving no current runtime dependency |
| `scripts/` | 4 source files | One current generator, three historical fixture/PDF generators | Keep current OpenAPI generator; classify old generators before archive |
| `.omo/` | 390 | Local OMO continuation state | Keep during OMO operation; already ignored |
| `.codegraph/` | 6 | Local CodeGraph database and daemon state | Keep local only; add portable root ignore |

## Current Authority Map

Use this order when sources disagree:

1. latest explicit Raphael instruction
2. `00_admin/PROJECT_STATE.md`
3. `00_admin/DECISIONS.md`
4. current `.hermes/plans/` files identified below
5. machine-readable `standards/`
6. current `services/`, `apps/operator-console/src/app/`, API types, and tests
7. current integration documents under `docs/integrations/`
8. historical docs, old plans, old memos, and audit reports as evidence only

## Plan Classification

### Current active authority

- `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
- `.hermes/plans/2026-08-20-sprint-5-operational-completion-contract.md`
- `.hermes/plans/2026-08-20-sprint-5-operator-experience-spec.md`
- `.hermes/plans/2026-08-20_120727-local-delivery-export-notion-handoff.md`

### Current deferred authority

- `.hermes/plans/2026-08-20-deferred-geo-v2-contract-restoration.md`

### Historical or superseded planning sources

- `.hermes/plans/2026-08-18_082138-heartweb-operations-platform-plan.md`
- `.hermes/plans/2026-08-18_085500-heartweb-notion-n8n-ui-migrationsplan.md`
- `.hermes/plans/2026-08-19-foundation-gates-step1-readiness.md`

These historical plans remain useful for intent reconstruction but must not compete with the active plan set.

## Confirmed Cleanup Candidates

No candidate was deleted during this audit.

### C-001: Stale Windows native dependency copy

- Path: `apps/operator-console/.node_modules-stale-winbinding/`
- Size: 21,401,600 bytes
- Status: untracked and not ignored before this audit
- Assessment: local dependency repair residue, not source or evidence
- Recommendation: ignore now, delete only after the current frontend and browser gates no longer depend on it

### C-002: Stale preview PID

- Path: `00_admin/audits/2026-08-19-e2e-demo/sprint-5/operator-console-visual-qa/operator-api-preview.pid`
- Size: 7 bytes
- Assessment: process identity from an already cleaned QA server, not durable evidence
- Recommendation: ignore PID files and delete after Sprint 5 evidence reconciliation

### C-003: Exact duplicate architecture image

- Paths:
  - `.hermes/plans/heartweb-notion-n8n-ui-migration.png`
  - `.hermes/plans/heartweb-operations-platform-architecture.png`
- SHA-256: `e821aa1b0400f4571568a364e86cadb36f7286216e637ab4f22058604c469ad2`
- Size: 1,174,811 bytes each
- References found: none
- Recommendation: retain one canonical image, remove or replace the duplicate after checking intended labels

### C-004: Rejected demo frontend

Confirmed unreachable from the production entrypoint:

- `apps/operator-console/src/dev/neutralDemo.ts`
- 15 files under `apps/operator-console/src/features/`

These files implement the rejected Northwind/demo card interface. The current production entrypoint reaches `src/app/` workspaces instead.

Recommendation: run one final TypeScript import and test dependency check after browser QA. Then archive or delete the demo source and remove tests or styles that exist only for it.

### C-005: Legacy direct-AgentSEO contracts

- `mcp/tool-contracts/agentseo_keyword_enricher.json`
- `mcp/tool-contracts/serp_gap_analyzer.json`
- `mcp/tool-contracts/schema_jsonld_generator.json`

Current references are concentrated in stale entry docs, historical plans, old audits, checkpoints, and changelog history. The current V2 architecture uses provider-neutral contracts under `standards/providers/` and Provider Gateway boundaries.

Recommendation: mark these three contracts `legacy` or move them to a dated historical location after the final runtime reference sweep. Do not delete checkpoint references.

### C-006: Historical generators

Likely historical rather than current runtime:

- `scripts/generate_sample_keywords.py`
- `scripts/generate_memo_pdf.py`
- `scripts/generate_geo_research_pdf.py`

Current source generator:

- `scripts/generate_operator_api_contracts.py`

Recommendation: retain the OpenAPI generator. Link the other scripts explicitly to their historical outputs or archive them with those outputs after documentation consolidation.

## Intentional Non-Redundancy

The following are not cleanup targets:

- `00_admin/checkpoints/`: immutable checkpoint evidence
- prior audit findings and later approvals: append-only decision trail
- `tests/__init__.py` and `tests/support/__init__.py`: intentional package markers
- raw Exa and Firecrawl files: source evidence
- neutral Step fixtures: required deterministic lifecycle tests
- Package 4 modules: still active in runtime and tests
- `.omo/`: active external orchestrator continuation state
- `.codegraph/`: local cache that should remain outside Git, not project source

## Documentation Drift

### Entry documents

`AGENTS.md`, `CLAUDE.md`, and `README.md` are stale and are covered by DIB-002.

### Docs corpus

The 16-file `docs/` corpus is mixed and covered by DIB-003.

Current architecture authority:

- `docs/integrations/notion-operating-model.md`
- `docs/integrations/n8n-orchestration-model.md`

Partially current strategy:

- `docs/07-geo-architecture-specification.md`
- `docs/07-geo-research-und-copywriter-guidelines.pdf`
- `docs/copywriter-handoff-guidelines.md`
- `docs/operator-workflow-function-map.html`

Historical or operationally stale:

- `docs/01-review-abgleich.md`
- `docs/02-research-und-technische-spezifikation.md`
- `docs/03-sprint-plan.md`
- `docs/04-entscheidungslog.md`
- `docs/05-human-in-the-loop.md`
- `docs/06-pilot-abnahme-checkliste.md`
- `docs/08-geo-sprint-plan-and-multi-agent-orchestration.md`
- `docs/betriebshandbuch-claude-desktop.md`
- `docs/jesse-walkthrough-memo.md`
- `docs/jesse-walkthrough-memo.pdf`

## State and Registry Drift

Before this audit:

- `PROJECT_STATE.md` stopped at Sprint 5 Packages 1 through 3
- it still named Solver v1.2 and direct AgentSEO operations
- it still advertised the rejected `?mode=demo` URL
- it did not record Package 4 backend, 74 frontend tests, the browser gate, Chrome installation, the WIP checkpoint, or branch consolidation decision
- central `PROJECT_REGISTRY.md` still described Notion, n8n, and UI only as future target runtime
- central `INDEX.md` did not list Heartweb in its active contexts
- `CHANGELOG.md` ended at version 1.4.0 from 2026-08-17 and omitted all V2, Sprint 0 through 5, Operator API, integration simulator, and Admin Console work

The project state and central registry must be corrected now. Entry docs, docs corpus, and changelog must be reconciled before final master merge.

## Git and Branch State

At audit start:

- local branch: `feature/e2e-operator-workflow-system`
- local HEAD: `3ed76b1a7962db168dc5b5325adcdc8220aa1de5`
- real Git index: clean
- working-tree paths: 125
- WIP remote checkpoint: `wip/sprint5-operator-console-2026-08-21-0809`
- WIP commit: `7c844ba1aa2bf938b34d854578e6bfc0cda6a9a0`
- `master`, Feature, and WIP form a linear history
- final branch consolidation remains gated by DEC-0022

## Current Delivery Status

Verified before this audit:

- local neutral backend workflow releases through Step 4b with fixture providers
- Package 4 backend and typed Admin action surfaces exist
- German single-admin frontend implementation and automated matrix report 74 passing frontend tests and a clean build
- browser gate remains without new Sisyphus evidence after Chrome installation
- Sprint 5E Delivery remains pending
- final audit remains pending
- live Notion and n8n remain pending

## Safe Actions Applied By This Audit

- add portable ignore rules for `.codegraph/`, stale native dependency copies, and PID files
- update `PROJECT_STATE.md`
- update central Hermes `INDEX.md` and `PROJECT_REGISTRY.md`
- register repository hygiene as DIB-004
- preserve all evidence and active runtime state

## Deferred Actions Requiring A Stable Gate

1. remove stale native binding directory
2. remove stale preview PID
3. deduplicate architecture PNGs
4. remove or archive rejected demo UI source
5. classify or archive legacy direct-AgentSEO contracts
6. classify historical generators
7. create docs and audit indexes
8. update CHANGELOG through the final implementation state
9. execute DIB-001, DIB-002, and DIB-003
10. reconcile and fast-forward branches under DEC-0022

## Final Assessment

The repository is not a chaotic duplicate codebase. Its core runtime and tests are structured, but the project tree has accumulated historical and operational layers faster than its authority documents and cleanup policy were maintained.

The correct response is not a broad deletion wave. The correct response is:

- update current state now
- ignore local runtime residue now
- preserve historical evidence
- classify documents and plans
- remove confirmed dead code and duplicates only after the current browser and delivery gates
- complete documentation and branch consolidation before master release
