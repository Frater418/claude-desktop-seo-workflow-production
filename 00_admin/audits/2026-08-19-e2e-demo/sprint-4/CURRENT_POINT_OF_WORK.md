# Sprint 4 Current Point of Work

Date: 2026-08-20
Author: Raphael Rechberger
Status: Sprint 4 complete, Sprint 5 next

## Read First After Any Compaction Or Session Change

1. `00_admin/PROJECT_STATE.md`
2. `00_admin/DECISIONS.md`
3. `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
4. `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md`
5. this file
6. `00_admin/audits/2026-08-19-e2e-demo/sprint-4/52_STAGE_C_INTEGRATION_SIMULATORS_TERMINAL_APPROVAL.md`
7. `00_admin/audits/2026-08-19-e2e-demo/sprint-4/53_STAGE_D_OPENAPI_INTEGRATION_IMPLEMENTATION.md`
8. `00_admin/checkpoints/2026-08-20-sprint-4/`

## Safety And Branch State

- Active Heartweb branch: `feature/e2e-operator-workflow-system`.
- Do not commit or push to `master`.
- Push only the feature branch. Keep `master` unchanged.
- OMO stack local branch: `feature/heartweb-sprint4-runtime`.
- OMO stack has no configured remote. Do not commit credential or environment backup files.
- No current Heartweb change is only inside Docker. The repository is a Windows host folder mounted into OMO.
- External verified snapshot:
  `C:\Users\offic\Documents\Projekte\Hermes\90_archive\project-snapshots\Heartweb-Claude-Desktop-SEO-Workflow\2026-08-19_20-26-39_-0400`
- Snapshot archive SHA-256:
  `38edf25bea7ec8b08b806bd48d6bf02b2eb2e7e42b5f1ac87ab7d51108d0df4c`
- Snapshot verification: 613 files reopened and matched against `FILE_MANIFEST.json`.
- GitHub feature branch: `feature/e2e-operator-workflow-system`.
- Stage A checkpoint commit: `a3b8ea1`.
- The feature branch is pushed and tracks `origin/feature/e2e-operator-workflow-system`.
- Local and remote `master` remain unchanged at `5e78679`.

## Completed Foundation And Sprint 4

- E2E Masterplan: active and approved.
- Sprint 0: completed.
- Sprint 1: completed and independently approved.
- Sprint 2: completed and independently approved.
- Sprint 3: completed and independently approved.
- Sprint 4 Stage A: Integration Contract V2 completed and terminally approved.
- Sprint 4 Stage A2: logical sessions, Context Packages, runtime records, Context Builder and session policy completed and approved.
- Sprint 4 Stage B: Local Operator API, Workspace Registry, Repository and append-only Event Store completed and terminally approved.
- Sprint 4 Stage C: Notion and n8n simulators completed and terminally approved.
- Sprint 4 Stage D: deterministic OpenAPI snapshot, generated TypeScript API types and local integration suite completed.
- Open findings for the Sprint-4 release boundary: P0 0, P1 0.

## Sprint 4 Final Evidence

- Stage-D focused suite:
  - Windows Python 3.11.15: 6 tests passed.
  - OMO Python 3.12.3: 6 tests passed.
- Full Suite:
  - Windows: Acceptance 7, Root 247, Contracts 59, total 313 passed.
  - OMO: Acceptance 7, Root 247, Contracts 59, total 313 passed.
- OpenAPI and TypeScript generator `--check`: passed on Host and OMO.
- TypeScript strict check: passed in OMO.
- `hermes verify --json`: `ok: true`, Acceptance 7 of 7.
- `git diff --check`: passed.
- Sprint-4 checkpoint: `00_admin/checkpoints/2026-08-20-sprint-4/` with 983 hashed files.

## Sprint 4 Delivered Interfaces

- `standards/api/operator-api.openapi.json`
- `apps/operator-console/src/generated/api-types.ts`
- `scripts/generate_operator_api_contracts.py`
- `services/context_builder/`
- `services/runtime_contracts/`
- `services/operator_api/`
- `services/integrations/notion_simulator.py`
- `services/integrations/n8n_simulator.py`
- `tests/test_sprint4_integration.py`

Notion and n8n remain simulated only. The Local Core is real and independent. The Transition Service remains the only atomic workflow status authority.

## Sprint 5 Boundary

Sprint 5 does not invent runtime behavior. It consumes the generated Stage-D API types and uses the Sprint-4 Core as authority.

Sprint 5 must display and operate:

- project dashboard
- workflow timeline
- step details
- artifacts and revision diff
- Context Package summary
- LLM run history and status
- provider, model, prompt version, worker profile, tool policy and token use
- revision run preview with findings, operator instruction, immutable fields and expected new revision
- task and ticket queue
- review center
- integration status
- presentation matrix

## Immediate Next Gates

1. Commit and push the complete Sprint-4 checkpoint to `feature/e2e-operator-workflow-system`.
2. Start Sprint 5 with the visible project dashboard and workflow timeline.
3. Add tasks, reviews, integration status and presentation matrix without duplicating Core contracts.
4. Keep `master` unchanged until the complete workflow and final audit are approved.

## Explicit Non-Actions

- no master commit
- no master push
- no force push
- no live Notion connection
- no live n8n connection
- no provider or crawl substitution
- no AHD hardcoding in production contracts
- no silent fallback
- no hand-written duplicate API contracts in Sprint 5
