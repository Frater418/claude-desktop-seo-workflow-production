# Sprint 4 Current Point of Work

Date: 2026-08-19
Author: Raphael Rechberger
Status: active controller handoff

## Read First After Any Compaction Or Session Change

1. `00_admin/PROJECT_STATE.md`
2. `00_admin/DECISIONS.md`
3. `.hermes/plans/2026-08-19-ahd-end-to-end-operator-workflow-system.md`
4. `00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md`
5. this file
6. `00_admin/audits/2026-08-19-e2e-demo/sprint-4/09_INTEGRATION_V2_FINAL_QUALITY_APPROVAL.md`
7. report 10 when it exists

## Safety And Branch State

- Active Heartweb branch: `feature/e2e-operator-workflow-system`.
- Do not commit or push to `master`.
- Push the feature branch only after the current Stage A fix, independent reviews, clean documentation and green verification.
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

## Completed Foundation

- E2E Masterplan: completed.
- Sprint 0: completed.
- Sprint 1: completed and independently approved.
- Sprint 2: completed and independently approved.
- Sprint 3: completed and independently approved.
- Sprint 3 checkpoint contains 226 file hashes and a byte-identical AHD Step-0 baseline.
- Current Stage A terminal full-suite evidence:
  - Windows: 236 tests passed.
  - OMO: 236 tests passed.
  - `hermes verify --json`: `ok: true`, acceptance 7 of 7.

## Sprint 4 Stage Map

### Task 4.1: Reproducible App Runtime

Status: completed.

- FastAPI, Starlette, Pydantic, Uvicorn, HTTPX and dependencies are pinned in `requirements-app.txt`.
- Linux Python 3.12 wheels are vendored in the OMO build context.
- OMO container is healthy with Restart Count 0.
- OpenCode 1.18.18 and OMO 4.19.4 are pinned.
- A real Codex smoke request returned `OK` after auth restoration.

### Stage A: Integration Contract V2

Status: completed and terminally approved.

Completed:

- workflow event V2 and catalog
- 17 Notion record types
- Notion proposal and snapshot
- n8n simulation, wait, retry and DLQ contracts
- 30/60/90 checkpoint contract
- V1 compatibility
- ten client-neutral archetypes
- focused and full-suite tests
- terminal specification review: `APPROVED`
- terminal quality review: `APPROVED`
- open findings: P0 0, P1 0, P2 0, P3 0

Closed findings:

1. relations to nonexistent records are rejected
2. relation type is bound to target record-key family
3. canonical `subject_id` equals the records-map key
4. duplicate edges are rejected independent of JSON field order
5. missing or invalid injected schema IDs return structured errors

Approval evidence:

- `10_NOTION_GRAPH_INTEGRITY_FIX.md`
- `11_STAGE_A_TERMINAL_SPEC_APPROVAL.md`
- `12_STAGE_A_TERMINAL_QUALITY_APPROVAL.md`
- `13_STAGE_A_SCHEMA_ID_FIX.md`
- `14_STAGE_A_FINAL_QUALITY_APPROVAL.md`

Current action:

- Stage A checkpoint, commit and feature-branch push are complete
- begin Stage A2 contract and deterministic Context Builder implementation
- do not begin Stage B before Stage A2 spec and quality approval

### Stage A2: Context Packages And Reproducible LLM Runs

Status: planned and canonically approved, not yet implemented.

Authority:

- `DEC-0019`
- Sprint 4 build plan Stage A2
- E2E Masterplan Task 4.2

Required implementation:

- logical project session contract
- worker profile contract
- context package contract
- LLM run request contract
- LLM run result contract
- deterministic Context Builder
- context freshness and supersession validator
- technical session reuse policy
- revision and rerun package
- complete prompt, model, worker, tool, hash and token provenance
- fresh LLM execution per step or substantial revision by default
- optional technical session reuse only as a cache
- recovery from a lost technical session using files and Context Package
- fail-fast on missing, stale, superseded, hash-invalid, untrusted-unmarked or cross-tenant context

### Stage B: Local Operator API And Event Store

Status: pending Stage A2 approval.

Required:

- read-only project and workflow API
- logical project session, Context Package and LLM run endpoints
- typed command API
- append-only JSONL event store
- idempotency and conflict protection
- tenant isolation and safe paths
- transition and routing delegation

### Stage C: Notion And n8n Simulators

Status: pending Stage B approval.

Required:

- Notion project, task, assignment, review, approval, blocker and tracking projection
- role routing to copywriters, designers, developers and reviewers
- complete n8n orchestration from 0 to 4b
- waits, retries, DLQ and resume
- Context Package and LLM Run dispatch
- Step 3b at day 30, 60 and 90

### Stage D: OpenAPI, Generated Types And Integration Suite

Status: pending Stage C approval.

Required:

- OpenAPI snapshot
- generated TypeScript API types
- Golden Path and negative integration scenarios
- lost technical session recovery
- revision rerun
- stale and cross-tenant context rejection
- role assignment and Notion tracking
- 30/60/90 metrics and Step 3b
- Host, OMO and `hermes verify --json`

## Sprint 5 Boundary

Sprint 5 does not invent runtime behavior. It starts only after Sprint 4 is fully approved.

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

1. Implement Stage A2 runtime contracts with negative tests first.
2. Implement deterministic Context Builder and session policy.
3. Verify Stage A2 on Windows and OMO.
4. Run independent Stage A2 specification and quality reviews.
5. Keep `master` unchanged until the complete workflow and final audit are approved.

## Explicit Non-Actions

- no master commit
- no master push
- no force push
- no live Notion connection
- no live n8n connection
- no provider or crawl substitution
- no AHD hardcoding in production contracts
- no silent fallback
- no Sprint 5 start before Sprint 4 approval
