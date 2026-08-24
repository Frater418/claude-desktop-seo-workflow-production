# Local Delivery, Export and Notion Handoff Implementation Plan

> **For implementation:** Hermes communicates only with Sisyphus. Hermes supplies the approved outcome, architecture boundary, hard constraints and Definition of Done. Sisyphus owns every internal implementation decision and delegation.

**Author:** Raphael Rechberger
**Date:** 2026-08-20
**Status:** Approved production-first Sprint 5E insertion. Handoff boundary clarified by DEC-0025.

**Goal:** Make every Heartweb project locally deliverable without live Notion or n8n by producing deterministic checkpoint and final handoff folders, ZIP downloads, role-specific packages and a Notion import pack that creates a complete customer concept and implementation project for Jesse and the team.

**Architecture:** The Heartweb Core and customer workspace remain the source of truth. The delivery layer reads released or explicitly included draft records, builds derived export views, writes an immutable delivery manifest and produces deterministic ZIP files. It never changes workflow state, approves a gate, overwrites an artifact or requires Notion/n8n.

**Tech Stack:** Python 3.11/3.12 standard library, JSON Schema Draft 2020-12, existing FastAPI Operator API, existing React/Vite Operator Console, CSV, Markdown, JSON, HTML and ZIP.

---

## 1. Recommendation

Do not postpone the complete delivery capability until after all real AHD sprints. Do not reopen and redesign Sprints 1 through 4 either.

Insert one bounded package after the current Sprint 5 action wiring:

```text
Sprint 5
  Packages 1-3: visible Operator Console
  Package 4: real Local API and Transition Service actions
  Package 5E: Local Delivery and Export Foundation

Sprint 6-9
  execute real AHD Golden Path
  create checkpoint exports after each released stage

Sprint 9
  create first real final handoff package after Step 4b

Sprint 10
  use final package, workflow matrix and UI for Jesse presentation

Sprint 11
  verify export integrity, extraction, portability and complete E2E operation
```

This keeps the current product architecture stable while ensuring Sprint 6 begins with an operational manual fallback.

## 2. Why This Belongs Before Sprint 6

Sprint 6 starts the real AHD pilot. If export is postponed until Sprint 10, the project can generate real outputs but still cannot hand them to Heartweb teams without ad hoc manual collection.

The local delivery foundation should exist before real pilot execution so every gate can produce a usable snapshot:

- Step 1 release: strategy checkpoint package
- Step 1b/1c release: architecture and design checkpoint package
- Step 2/3 release: research and roadmap checkpoint package
- Step 4a release: copywriter handoff package
- Step 4b release: complete final handoff package

## 3. What Earlier Sprints Already Provide

### Sprint 1 and 2 foundations already available

- tenant, project, run and step identities
- Artifact Records
- Evidence Records
- Approval and Release Records
- Operator Tasks
- Revision Requests
- Defects, Escalations and Resolutions
- assignments and role types
- structured errors and routing

### Sprint 3 foundations already available

- closed output contracts for Steps 1b through 4b
- canonical JSON outputs
- deterministic Markdown, CSV and HTML renderers
- predecessor lineage
- provider evidence
- safe output paths

### Sprint 4 foundations already available

- Local Operator API
- Workspace Registry
- repository containment
- append-only workflow events
- Context Packages and LLM Run Records
- Notion projection contracts and simulator
- n8n command contracts and simulator
- generated OpenAPI and TypeScript types

### Sprint 5 foundations already available

- Project Dashboard
- Workflow Timeline and Step Detail
- Artifact Preview and Revision Diff
- Run History and Context Package Summary
- Task Queue and Ticket Detail
- Review Center
- Integration Status
- Workflow Matrix and Baseline Comparison

The new work must reuse these records. It must not create a parallel task model, second artifact registry or second project state.

## 4. What Should Have Been Prepared Earlier

The following contract surfaces would ideally have been added during Sprints 2 and 4:

- Delivery Package Record
- Export Request and Export Result contracts
- deterministic package manifest
- role handoff manifest
- Notion import manifest
- delivery preview and download API endpoints

They are missing, but retroactively rewriting completed sprints would add risk without value. Add them now as a compatibility extension named Sprint 5E.

## 5. Product Boundary

### Must work without external systems

```text
Operator Console
-> Local Operator API
-> Delivery Service
-> Customer Workspace
-> Handoff Folder
-> ZIP Download
```

### Optional future paths

```text
Delivery Service
-> Notion Import Pack
-> manual Notion import
```

```text
Delivery Service
-> live Notion adapter
-> automatic database and page creation
```

```text
n8n
-> scheduling, polling, wait/resume, retries, notifications and multi-project orchestration
```

Live Notion and n8n are not dependencies of local export.

## 5.1 Binding Handoff Boundary

Sprint 5E exports two distinct task classes and must never merge them:

1. **Core-internal production tasks:** Temporary blockers, reviews and Human-Gate work required to complete Step 0 through Step 4B. These remain Core records and may resume an active Core run before release.
2. **Notion implementation tasks:** Copywriter, design, development, review, launch and tracking work derived from the approved concept. These are created for operational execution after release and are owned by Notion.

After the final handoff:

- Notion owns implementation-task status, comments, assignees, priorities and deadlines;
- implementation-task completion does not call the Core;
- implementation-task completion does not resume a run, approve a gate, create a revision or mutate an artifact;
- no callback, webhook or command mapping for daily staff-task changes is included in the Notion import pack;
- stable Heartweb IDs and artifact hashes exist only for traceability to the approved concept.

The only planned automated post-handoff Core re-entry is Step 3B at day 30, 60 and 90. The Notion project therefore includes performance-checkpoint records and the source references required to compare the released core strategy with actual results. Step 3B remains post-release and is not implemented by Sprint 5E.

## 6. Export Types

### 6.1 Checkpoint Export

Available at any workflow point.

Includes:

- current project summary
- released artifacts
- drafts clearly marked as draft when explicitly requested
- current tasks and assignments
- open blockers and reviews
- current quality-gate status
- missing expected deliverables
- next permitted action

### 6.2 Final Handoff Export

Available only when Step 4b is released or `staging_ready` according to the final policy.

Includes:

- all required released outputs
- complete task and assignment map
- complete quality summary
- copywriter and developer packages
- Notion import pack
- delivery manifest and checksums

### 6.3 Role Packages

Derived subsets:

- Copywriter Package
- Developer Package
- Project Management Package
- Reviewer Package

### 6.4 Notion Import Pack

A portable manual import package that creates the complete customer concept and operational implementation project:

- projects.csv
- tasks.csv
- assignments.csv
- artifacts.csv
- reviews.csv
- approvals.csv
- blockers.csv
- priorities.csv
- deadlines.csv
- relations.csv
- IMPORT_ORDER.md
- PROPERTY_MAPPING.md
- USER_MAPPING_TEMPLATE.csv

The pack must distinguish read-only concept provenance from Notion-owned implementation execution. It must not contain an inbound Core callback configuration.

## 7. Deterministic Folder Layout

```text
<customer-slug>-<project-id>-<export-scope>-r<revision>/
  README.md
  PROJECT_SUMMARY.md
  export-manifest.json
  checksums.sha256
  project/
  strategy/
  architecture/
  design/
  keyword-research/
  roadmap/
  copywriter-handoff/
  developer-handoff/
  project-management/
  quality-reports/
  notion-import/
  performance/
```

All paths inside the manifest are relative POSIX-style paths. No absolute host path may appear in an exported file.

## 8. New Contracts

### Task 1: Delivery contract namespace

**Files:**

- Create: `standards/delivery/delivery-package-record.schema.json`
- Create: `standards/delivery/delivery-export-request.schema.json`
- Create: `standards/delivery/delivery-export-result.schema.json`
- Create: `standards/delivery/role-handoff-manifest.schema.json`
- Create: `standards/delivery/notion-import-manifest.schema.json`
- Test: `tests/contracts/test_delivery_contracts.py`

**Requirements:**

- closed Draft 2020-12 schemas
- tenant and project identity
- export ID and export scope
- source snapshot revision
- source record IDs and hashes
- required/missing deliverables
- package SHA-256
- ZIP SHA-256
- role package references
- Notion import manifest reference
- created-at supplied by caller, never read from system clock inside deterministic builder
- no workflow status authority

**RED:** Contract tests fail because schemas do not exist.

**GREEN:** Positive checkpoint/final fixtures validate and negative cross-tenant, path escape, missing hash and premature-final fixtures fail.

## 9. Delivery Inventory and Policy

### Task 2: Deterministic project collector

**Files:**

- Create: `services/delivery/__init__.py`
- Create: `services/delivery/inventory.py`
- Create: `services/delivery/policy.py`
- Test: `tests/test_delivery_inventory.py`

**Behavior:**

- accept an injected workspace root and injected records
- collect Project V2, workflow, runs, artifacts, releases, gates, tasks, assignments, reviews, blockers and reports
- include only contained regular files
- reject symlinks, junctions, path traversal and absolute-path leaks
- calculate exact SHA-256 from file bytes
- sort records and files canonically
- classify deliverables by step, role and release status
- fail final export when required released deliverables are missing
- allow checkpoint export with an explicit missing-items report

**Do not:**

- read Notion
- call n8n
- mutate workflow status
- silently omit malformed records
- scan arbitrary folders outside the registered workspace

## 10. Role-Specific Handoff Builders

### Task 3: Copywriter and developer views

**Files:**

- Create: `services/delivery/role_packages.py`
- Create: `services/delivery/renderers.py`
- Test: `tests/test_delivery_role_packages.py`

**Copywriter package:**

- Step 4a briefings
- YAML frontmatter
- keyword and intent summary
- claim and evidence references
- link instructions
- assigned tasks, priorities and deadlines
- review requirements

**Developer package:**

- architecture and URL map
- redirects and internal links
- design system and page specifications
- Step 4b HTML and JSON-LD
- technical QA and staging requirements
- assigned tasks, priorities and deadlines

**Rule:** Role packages are filtered views of canonical records. They do not duplicate or own workflow status.

## 11. Notion Import Pack

### Task 4: Manual Notion transfer generator

**Files:**

- Create: `services/delivery/notion_import.py`
- Test: `tests/test_notion_import_pack.py`

**Behavior:**

- generate UTF-8 CSV with stable columns
- retain stable Heartweb IDs as external IDs
- export relations through stable IDs, never display titles alone
- separate Core-owned read-only fields from operator-editable fields
- include import order and property mapping
- include user mapping template when Notion User IDs are unknown
- mark unresolved assignees as unassigned, never guess
- label integration mode as manual import
- classify exported tasks as `core_history` or `notion_implementation`
- export Core-internal tasks only as immutable history when they are needed for audit context
- make Notion implementation-task status, assignee, priority, deadline and comments operationally editable in Notion
- include no `resume_run`, gate, revision, artifact mutation or task-completion callback mapping for Notion implementation tasks
- include performance checkpoint rows for day 30, 60 and 90 with released strategy, plan and publication-registry references
- state in `PROPERTY_MAPPING.md` that only the scheduled Step-3B performance integration may later re-enter the Core after handoff

**Recommended import order:**

1. customers
2. projects
3. workflow runs and steps
4. artifacts
5. tasks and assignments
6. reviews and approvals
7. blockers and escalations
8. relations
9. performance checkpoints

**Required negative proofs:**

- a Notion implementation task cannot be exported with a Core resume command;
- a Copywriter or Developer completion field cannot map to a gate or artifact mutation;
- a performance checkpoint without released strategy and plan references fails;
- a duplicate import retains stable external IDs and does not duplicate customer, project or implementation tasks.

## 12. Deterministic ZIP Builder

### Task 5: Portable archive generation

**Files:**

- Create: `services/delivery/archive.py`
- Test: `tests/test_delivery_archive.py`

**Requirements:**

- ZIP only as the default portable format
- lexicographically sorted entries
- normalized ZIP timestamps
- normalized file permissions
- UTF-8 names
- no absolute paths
- no `..` entries
- no symlinks or junction targets
- no `.env`, credentials, tokens, caches, temp files or raw provider auth material
- manifest and checksums included before ZIP hash is finalized
- repeated build from identical inputs yields byte-identical ZIP
- extraction and checksum revalidation test

RAR is out of scope.

## 13. Local Delivery API

### Task 6: Preview, create and download endpoints

**Files:**

- Modify: `services/operator_api/models.py`
- Modify: `services/operator_api/repository.py`
- Modify: `services/operator_api/app.py`
- Modify: `scripts/generate_operator_api_contracts.py`
- Regenerate: `standards/api/operator-api.openapi.json`
- Regenerate: `apps/operator-console/src/generated/api-types.ts`
- Test: `tests/test_delivery_api.py`

**Endpoints:**

```text
GET  /v1/tenants/{tenant_id}/projects/{project_id}/delivery/preview?scope=checkpoint|final
POST /v1/tenants/{tenant_id}/projects/{project_id}/delivery/exports
GET  /v1/tenants/{tenant_id}/projects/{project_id}/delivery/exports
GET  /v1/tenants/{tenant_id}/projects/{project_id}/delivery/exports/{export_id}
GET  /v1/tenants/{tenant_id}/projects/{project_id}/delivery/exports/{export_id}/download
```

**Rules:**

- registry-contained workspace only
- preview performs no write
- create requires an explicit request and idempotency key
- identical replay returns existing export
- conflicting replay fails
- final scope fails when final policy is not satisfied
- export writes no run, gate, approval or release status
- file response uses a controlled filename
- package record persists under the project delivery namespace

Do not force the project-level delivery package into the existing step-scoped Artifact Record.

## 14. Activate the existing Operator Console Delivery workspace

### Task 7: Replace the verified contract-gate placeholder with functional Delivery wiring

The German `Uebergabe und Export` navigation destination, route shell, responsive design and visual browser evidence already exist. Task 7 must preserve that verified surface. It is limited to replacing the intentional contract-gate placeholder with typed Delivery API content and actions. Do not rebuild or redesign the Operator Console.

**Files:**

- Create: `apps/operator-console/src/features/delivery/DeliveryCenter.tsx`
- Create: `apps/operator-console/src/features/delivery/DeliveryPreview.tsx`
- Create: `apps/operator-console/src/features/delivery/ExportHistory.tsx`
- Modify: `apps/operator-console/src/api/client.ts`
- Modify: `apps/operator-console/src/App.tsx`
- Modify: `apps/operator-console/src/styles.css`
- Modify: `apps/operator-console/src/App.test.tsx`

**UI actions:**

```text
Open Project Folder
Preview Checkpoint Export
Download Checkpoint ZIP
Preview Final Handoff
Download Final Handoff ZIP
Download Copywriter Package
Download Developer Package
Download Notion Import Pack
Prepare Notion Transfer
```

`Prepare Notion Transfer` remains a preview until a live Notion adapter is configured. It must not silently perform external writes.

**Shows before export:**

- included files
- missing required outputs
- draft versus released status
- role assignments
- package size estimate
- export scope
- source revision
- checksum status
- unresolved assignees
- final-export eligibility

## 15. Local End-to-End Delivery Test

### Task 8: Neutral project export flow

**Files:**

- Create: `tests/test_delivery_e2e.py`
- Extend: `tests/test_sprint4_integration.py` only when a shared API fixture is required
- Add: `tests/fixtures/delivery/`

**Scenarios:**

1. checkpoint export during Step 1b
2. checkpoint export with open blockers
3. final export rejected before Step 4b release
4. final export after all required releases
5. copywriter and developer packages contain only role-relevant outputs
6. unassigned user remains explicit
7. repeated export is deterministic and idempotent
8. ZIP extraction matches checksums
9. no secrets or absolute paths
10. manual Notion import pack has stable IDs and relations

Use one representative neutral fixture for implementation. Real AHD acceptance happens in Sprints 6 through 10. Do not add another ten-archetype matrix here.

## 16. Integration Into Existing Sprints

### Sprint 5 completion

Sprint 5 is complete only when:

- existing UI actions are connected to Local API and Transition Service
- a complete neutral Step-0-to-4b workflow can be operated locally
- Delivery Center can produce a checkpoint ZIP
- the local system remains independent of Notion and n8n

### Sprint 6

After AHD Step 1 release:

- produce strategy checkpoint ZIP
- verify tasks, blockers and review history are included
- verify missing future outputs are clearly listed

### Sprint 7

After AHD Step 1b and 1c releases:

- produce architecture/design checkpoint ZIP
- verify developer package contains architecture and design outputs

### Sprint 8

After AHD Step 2 and 3 releases:

- produce research/roadmap checkpoint ZIP
- verify keyword evidence and 120-day plan

### Sprint 9

After AHD Step 4a and 4b:

- create first real Final Handoff ZIP
- create Copywriter Package
- create Developer Package
- create Notion Import Pack
- verify all required files and hashes

### Sprint 10

- present the UI and final package to Jesse
- demonstrate manual handoff without live integrations
- record any stakeholder mapping decisions for later Notion adapter work

### Sprint 11

- repeat deterministic export on Host and clean runtime
- verify identical package hashes
- extract and revalidate checksums
- verify no secrets
- run the applicable PT matrix cells for the local UI and export gate with cell-local retry

## 17. Notion and n8n Boundary

### Local operation

No n8n is required for:

- briefing intake
- step execution
- artifact review
- human gates
- task management
- revisions
- checkpoint exports
- final ZIP download
- manual Notion import pack

### Live Notion integration

A later adapter can consume the same delivery manifest and stable IDs. Live sync should remain a separate explicit capability:

```text
Prepare Notion Transfer
-> Preview pages, tasks, assignments and relations
-> Confirm external write
-> Execute through authorized adapter
-> Record delivery result
```

### n8n

n8n remains optional for the single-operator local workflow. It becomes useful for:

- multiple projects
- schedules
- long waits
- provider polling
- retry and DLQ
- notifications
- live Notion orchestration
- 30/60/90 performance cycles

## 18. Security and Privacy Gate

Export must fail when:

- a path escapes the registered workspace
- a symlink or junction is encountered
- a source hash does not match bytes
- a required final deliverable is missing
- a credential-like file is selected
- an absolute host path appears in public manifests
- duplicate output paths occur
- an unresolved task is falsely marked completed
- an unapproved artifact is presented as released

## 19. Definition of Done

Sprint 5E is complete when an operator can:

1. open Delivery Center
2. preview a checkpoint package
3. see included and missing items
4. create a deterministic checkpoint ZIP
5. download and extract it
6. validate all checksums
7. open Copywriter and Developer subpackages
8. open a manual Notion Import Pack
9. repeat the same export with the same resulting package hash
10. perform all actions without Notion, n8n or a live provider

The full feature is finally accepted when the real AHD Step-4b project produces a complete Final Handoff ZIP in Sprint 9 and that package is presented in Sprint 10.

## 20. Recommended Execution Order

```text
1. Finish current Sprint 5 Local API and Transition Service action wiring
2. Implement Sprint 5E contracts and deterministic export service
3. Add Delivery API
4. Regenerate OpenAPI and UI types
5. Add Delivery Center
6. Prove neutral checkpoint export
7. Start Sprint 6 AHD pilot
8. Export at each real gate
9. Prove final AHD handoff in Sprint 9
10. Present in Sprint 10
11. Run final portability gate in Sprint 11
```

## 21. Explicit Non-Goals

- no RAR support
- no live Notion write in Sprint 5E
- no n8n dependency
- no email or Slack delivery
- no automatic user guessing
- no direct modification of released artifacts
- no new workflow state authority
- no second project database
- no deployment
- no AHD hardcoding in delivery services

## 22. Decision Summary

**Recommended decision:** Insert Sprint 5E immediately after the current Sprint 5 operational action wiring and before Sprint 6.

This is the smallest placement that provides immediate operational value, protects the real AHD pilot from manual handoff chaos and avoids reopening completed foundation sprints.
