# Sprint 4 Integration Simulation Research

**Date:** 2026-08-19
**Scope:** Research only. This report proposes no live connection, credential, database ID, provider call, or implementation.

## Evidence-Based Baseline

DEC-0018 requires a fully executable local Core, with n8n later acting only as the full workflow transport and orchestrator. It requires Notion to be the central customer, project, task, assignment, review, approval, deadline, blocker, metric, and tracking surface, while the Operator Console remains a subordinate specialist view. The Core retains protected workflow status, hashes, revisions, and gate decisions. [00_admin/DECISIONS.md:81-89](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:81)

The existing integration documents already place atomic authority exclusively in the Transition Service. Notion is an append-only-event projection and cannot write canonical state. [docs/integrations/notion-operating-model.md:3-7](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:3) n8n is likewise transport only, and may dispatch, wait, retry, dead-letter, and request a resume. [docs/integrations/n8n-orchestration-model.md:3-7](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:3)

The executable Transition Service currently protects identity, revision, input hash, allowed state transitions, predecessor release, artifact identity and hash, quality gates, and revision-bound approval before returning a next run. [services/transition_service/service.py:203-315](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:203) It returns a no-op replay for an identical idempotency fingerprint and rejects a different command reusing that key. [services/transition_service/service.py:205-217](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:205)

### Currently Implemented Contracts

| Area | Evidence | Present capability |
|---|---|---|
| Workflow route | [standards/workflow/workflow-graph.json:5-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/workflow/workflow-graph.json:5) | Initial route is `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`; `3b` is a repeatable post-publication sideflow at days 30, 60, and 90 that creates a new revision. |
| Workflow event | [standards/integrations/workflow-event.schema.json:7-19](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:7) | Closed v1 event envelope with correlation, idempotency, identity, simulated/live mode, and payload. The only current event vocabulary is enumerated at [workflow-event.schema.json:10](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:10). |
| Notion projection | [standards/integrations/notion-projection.schema.json:7-28](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection.schema.json:7) | Closed v1 projection with only `project`, `run`, `task`, `gate`, `artifact`, and `review` record types. It expressly fixes authority to `transition_service` and `atomic_state_writer` to false. |
| n8n command | [standards/integrations/n8n-command.schema.json:7-30](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:7) | Closed v1 command envelope and five command types: dispatch, wait, retry, resume, and dead-letter. `approve_gate` and `complete_run` are absent. |
| Simulated mode | [standards/integrations/notion-projection.schema.json:22-24](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection.schema.json:22), [standards/integrations/n8n-command.schema.json:25-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:25) | `simulated` requires `simulation_id` and forbids a live connection. `live` has the inverse requirement. |
| Contract coverage | [tests/contracts/test_integration_contracts.py:52-124](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts.py:52) | Schemas and sample simulated fixtures validate, false live claims fail, and forbidden n8n command types fail. This is contract validation, not a simulator execution test. |
| Local runtime plan | [requirements-app.txt:2-20](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/requirements-app.txt:2) | The declared runtime is FastAPI, Pydantic, Uvicorn, HTTPX, and JSON Schema. It declares no Notion or n8n SDK. |

**Finding:** The repository has schemas, fixture examples, and authority rules, but this inspection found no `services/notion_simulator` or `services/n8n_simulator` source module and no test that drives either a simulator. Therefore a transport-faithful simulator is required Sprint 4 work, not an implemented capability. The existing positive fixture is one simulated Notion projection with one project record. [tests/fixtures/integrations/notion/project-projection.json:1](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/fixtures/integrations/notion/project-projection.json:1)

## Required Simulator Boundary

The following is an **unverified design decision for implementation review**. Both adapters should be local, file-backed test doubles behind the existing versioned JSON envelopes. They must not emulate undocumented provider internals or make HTTP calls. The local Core remains executable without either adapter.

| Component | Required responsibility | Prohibited responsibility |
|---|---|---|
| Local Core | Validate and durably apply canonical transition commands, produce artifacts, gate records, approval validation, releases, and append-only events. | Calling Notion or n8n directly. |
| Local n8n simulator | Accept valid `n8n-command` envelopes, preserve command delivery metadata, dispatch Core work, wait for typed events, schedule retries and DLQ, and issue resume requests. | Approving gates, completing runs, or mutating canonical run state. These prohibitions match [docs/integrations/n8n-orchestration-model.md:13-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:13). |
| Local Notion simulator | Materialize queryable records from accepted events and receive human intents as proposals that become versioned Core commands. | Writing a run status, approval, revision, artifact reference, or gate decision directly. [docs/integrations/notion-operating-model.md:15-19](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:15) |
| Operator Console | Deep-link or filter the Notion-derived operational records for artifact comparison, protected approval submission, and specialist troubleshooting. | Replacing Notion as the operational system of record or bypassing the Core. [00_admin/DECISIONS.md:81-88](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:81) |

### Local Store and Isolation

**Unverified design decision:** make every simulator run self-contained under `tests/fixtures/integrations/simulations/<simulation_id>/` when used by tests, and under an explicit caller-supplied local workspace path for manual demos. Store immutable inbound commands and events separately from materialized records, retry state, and DLQ entries. Do not put simulator output in the real customer workspace contract until an approved output-path contract exists.

Every record and queue entry must carry `tenant_id`, `project_id`, `run_id` when applicable, `correlation_id`, `idempotency_key`, `integration_mode`, and exactly one of `simulation_id` or `live_connection_id`. This preserves the current identity and mode requirements. [standards/integrations/n8n-command.schema.json:7-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:7) No live identifiers, credentials, or database IDs should be added to local fixtures.

## Proposed Local Notion Data Model

The record types below are **required schema expansions, not current schema fields**. The present projection allows only six types, so all types marked `new` require a v2 schema and migration of fixtures. [standards/integrations/notion-projection.schema.json:27-28](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection.schema.json:27)

| Record type | Status | Required relations and minimum transport fields |
|---|---|---|
| Customer | new | `customer_id`, tenant, customer name, Projects. Source from fixture customer object, not a live Notion database. |
| Project | existing, expand | Customer, Runs, Tasks, Artifacts, Gates, Metrics, Integration Status; canonical project and tenant identity. |
| Run | existing, expand | Project, Step, predecessor Release, Artifacts, Gates, Blockers, `revision`, `expected_revision`, `status`, `input_hash`. |
| Step | new | Project, Runs, Gate, workflow order, predecessor Step, due policy. The valid step set is already fixed by the contracts. [standards/integrations/workflow-event.schema.json:40-42](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:40) |
| Task | existing, expand | Project, Run, Step, Assignment, Artifact, Blocker, Review, due date, priority, blocking flag, status. |
| Assignment | new | Task, role, assignee reference, assigned and due timestamps, acceptance criteria. |
| Artifact | existing, expand | Project, Run, Step, Gate, Reviews, source path, immutable `artifact_id`, revision, SHA-256. Existing event payload already binds these fields. [standards/integrations/workflow-event.schema.json:43-49](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:43) |
| Gate | existing, expand | Run, Step, Artifact, Review, Approval, gate state, bound artifact SHA-256. |
| Review | existing, expand | Artifact, Gate, reviewer Assignment, requested/decided timestamps, comments as context only. |
| Approval | new | Gate, Review, Artifact, approver, policy version, decision, expiry, revision and SHA-256 binding. The Core already requires this binding. [services/transition_service/service.py:122-140](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:122) |
| Blocker | new | Project, Run, Step, Task, Defect or Escalation, type, reason, opened/resolved timestamps. Existing `step.blocked` payload specifies blocker id, type, and reason. [standards/integrations/workflow-event.schema.json:46](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:46) |
| Defect | new | Project, Run, related Task or Blocker, severity, status, DLQ provenance. |
| Escalation | new | Project, Run, Task or Blocker, decision owner, decision status. The existing event contract limits decision owners to business owner or compliance reviewer. [standards/integrations/workflow-event.schema.json:54](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:54) |
| Performance Checkpoint | new | Project, released Step 4b artifact or publication reference, related Step 3b run, due day 30/60/90, completion state. |
| Metric | new | Performance Checkpoint, metric name/value/unit/source evidence, observed timestamp. No provider collection is implied. |
| Adjustment Proposal | new | Performance Checkpoint, source Step 3 plan, new Step 3b artifact, evidence, Gate, Approval, supersession relation. Step 3b requires a new immutable artifact and hash, not mutation of the original plan. [prompts/3b-performance-check.xml.md:13-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:13) |
| Integration Status | new | Project, simulation identity, adapter, delivery status, last event and source revision, retry attempt, DLQ reference, conflict status. |

All projected records must retain `source_event_id`, `source_revision`, `state_authority: transition_service`, and `atomic_state_writer: false`, matching the current operating model. [docs/integrations/notion-operating-model.md:5-7](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:5)

### Role Assignment

This is an **unverified assignment policy** to be encoded as typed Task and Assignment projections, not as a change to canonical approval authority:

| Role | Receives work | Completion evidence | May not do |
|---|---|---|---|
| Copywriter | A released Step 4a briefing Task after its gate is approved. | Draft and checklist completion, then `task.resolved` proposal. The existing handoff names Regina, Katja, and Alexander and defines the Notion stages. [docs/copywriter-handoff-guidelines.md:5-15](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/copywriter-handoff-guidelines.md:5), [docs/copywriter-handoff-guidelines.md:64-68](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/copywriter-handoff-guidelines.md:64) | Approve Gate 4a or alter artifact hash/revision. |
| Designer | Step 1c design-token or template revision Task. | Versioned artifact proposal and evidence. | Release or approve the associated gate. |
| Developer | Step 4b HTML implementation or delivery Task. | Versioned HTML artifact and validation evidence. | Mark a canonical run completed. |
| Reviewer | Gate-ready review Task for the applicable artifact. | A revision-bound approval or rejection proposal. | Modify the reviewed artifact or directly change run state. |

The current operator task contract has only `operator`, `workflow_maintainer`, `business_owner`, `compliance_reviewer`, and `incident_responder` owner roles. [standards/operator/operator-task.schema.json:12-16](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/operator/operator-task.schema.json:12) Supporting copywriter, designer, developer, and reviewer as assignments therefore requires either an expanded owner-role enum or a separate `assigned_role` in the Notion projection. Prefer the latter to avoid changing the current Core routing semantics.

## n8n Simulator Choreography

The following is the requested **unverified design choreography**. It deliberately uses the existing command types and never treats n8n as an approver.

1. Start with a simulated `dispatch_tool_run` command for Step 0. The Core accepts the transition, emits `project.created`, `run.started`, and any resulting artifact or gate events, and the Notion projector creates Customer, Project, Run, Step, Artifact, and Gate records.
2. For every initial edge `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b`, dispatch the next step only after the prior release. This mirrors the graph's released predecessor, artifact, and gate requirements. [standards/workflow/workflow-graph.json:16-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/workflow/workflow-graph.json:16)
3. After a Core artifact event, dispatch the gate evaluation path, project `gate.ready`, create a Reviewer Task and wait using `wait_for_gate`. A wait is not a state transition. [docs/integrations/n8n-orchestration-model.md:13-17](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:13)
4. A human decision is entered in simulated Notion as a proposal. The adapter creates a versioned Core approval or rejection action bound to current artifact revision and SHA-256. The Core alone evaluates it and then emits `gate.approved` or `gate.rejected`; a valid complete or publish path produces `release.created`. [services/transition_service/service.py:281-345](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:281)
5. On `gate.rejected`, `step.blocked`, missing input, or a technical failure, project Blocker plus typed Task. The simulator must halt successor dispatch until a resolved task or accepted approval produces a valid `resume_run` request. The Core rejects stale resume requests rather than changing state. [docs/integrations/notion-operating-model.md:25-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:25), [docs/integrations/n8n-orchestration-model.md:15-17](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:15)
6. For a retryable delivery, submit `retry_delivery` with the original correlation and idempotency key. Make bounded attempts. Once exhausted, issue `dead_letter`, persist an Integration Status entry, and create a Defect or Escalation through normal event routing. [docs/integrations/n8n-orchestration-model.md:19-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:19)
7. On confirmed post-publication days 30, 60, and 90, create a Performance Checkpoint and dispatch repeatable Step 3b only from a released Step 4b predecessor. Step 3b consumes stored evidence only, generates a new immutable adjustment candidate, and waits at its own gate. [standards/workflow/workflow-graph.json:25-27](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/workflow/workflow-graph.json:25), [prompts/3b-performance-check.xml.md:18-28](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:18)

### Delivery, Replay, Ordering, and Conflict Rules

| Condition | Required simulator behavior | Evidence |
|---|---|---|
| Duplicate command | Use the same idempotency key. An equal fingerprint is a replay with no second transition. A different payload under the key fails. | [services/transition_service/service.py:203-217](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:203) |
| Duplicate event | Deduplicate by `event_id` and projection source revision. | [docs/integrations/notion-operating-model.md:21-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:21) |
| Out-of-order event | Retain for audit, wait for the required predecessor, and never overwrite a projection from a newer canonical revision. | [docs/integrations/n8n-orchestration-model.md:19-22](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:19) |
| Stale Notion edit | Preserve it as context, mark Integration Status as conflict, show the current revision, and require an explicit fresh command. Do not merge automatically. | [docs/integrations/notion-operating-model.md:15-19](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:15) |
| Stale command | Fail fast with no run mutation. | [services/transition_service/service.py:224-229](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/transition_service/service.py:224) |
| Exhausted delivery | Put immutable envelope and failure metadata in DLQ, then create a typed Task, Defect, or Escalation. | [docs/integrations/n8n-orchestration-model.md:21-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:21) |

## Fixture Matrix for Simulator Tests

Use the ten existing, non-hardcoded domain fixtures as parameterized inputs. The contract test asserts exactly ten files and validates each fixture against the closed domain contracts. [tests/contracts/test_real_customer_domain_fixtures.py:124-140](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_real_customer_domain_fixtures.py:124)

| Fixture path | Customer archetype | Simulator matrix focus |
|---|---|---|
| `tests/fixtures/domain/real-customer-matrix/cross-border-finance.json` | Cross-border finance | Compliance escalation, multi-market assignments, stale approval. |
| `tests/fixtures/domain/real-customer-matrix/english-international-resort-ota-social.json` | English international resort | International market tracking and Step 4a copywriter handoff. |
| `tests/fixtures/domain/real-customer-matrix/international-speaker-brand.json` | International speaker brand | Multi-market artifact and reviewer projections. |
| `tests/fixtures/domain/real-customer-matrix/local-medical.json` | Local medical | YMYL evidence blocker and compliance review. |
| `tests/fixtures/domain/real-customer-matrix/national-b2b.json` | National B2B | Standard happy path, duplicate command replay. |
| `tests/fixtures/domain/real-customer-matrix/programmatic-local-satellite-network.json` | Programmatic-local satellite network | High-volume Assignment and out-of-order projection behavior. |
| `tests/fixtures/domain/real-customer-matrix/regional-care.json` | Regional care | Compliance gate and due-date blocking. |
| `tests/fixtures/domain/real-customer-matrix/regional-solo-expert.json` | Regional solo expert | Minimal local path and review wait/resume. |
| `tests/fixtures/domain/real-customer-matrix/sensitive-education-retreat.json` | Sensitive education retreat | Escalation plus repeatable 3b checkpoints. |
| `tests/fixtures/domain/real-customer-matrix/sri-lankan-ayurveda-dach.json` | Sri Lankan Ayurveda DACH | Cross-market, cross-language tracking and 3b adjustment proposal. |

The matrix categories are proposed test scenarios, not claims about live customers. Fixture identity and all actual customer-domain values remain local test data at the paths listed above.

## Exact Contract and Test Work Required

1. Add a versioned v2 Notion projection schema. Expand `record_id` and `record_type` beyond the current six types and define relations plus source metadata for all 17 record types in this report. Preserve v1 fixture validation or explicitly version fixtures, because the current schema pins `schema_version` to `1.0.0`. [standards/integrations/notion-projection.schema.json:7-28](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection.schema.json:7)
2. Add typed payload definitions and catalog entries for `assignment.created`, `approval.recorded`, `blocker.resolved`, `performance.checkpoint_due`, `metric.recorded`, `adjustment.proposed`, `integration.delivery_failed`, and `integration.conflict_detected`. They are necessary to project the requested data model, but are not in the current closed event enum. [standards/integrations/workflow-event.schema.json:9-36](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event.schema.json:9)
3. Add a local n8n simulator contract for retry policy, queue entry, wait subscription, DLQ entry, and deterministic clock. Keep the existing command types unless a Core-approved transport requirement proves expansion is needed. [standards/integrations/n8n-command.schema.json:21-30](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:21)
4. Add local Notion simulator contracts for a proposal envelope and a projection snapshot/query result. Both must enforce mode separation, projection source revision, and the non-authority constants. [docs/integrations/notion-operating-model.md:9-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/notion-operating-model.md:9)
5. Add simulator unit tests for all 10 fixtures: successful 0 through 4b projection, each role assignment, duplicate command and event replay, out-of-order predecessor delay, stale edit conflict, retry then DLQ, resume only after current evidence, and Step 3b only at 30/60/90 with immutable Step 3 lineage. Add a local E2E test that drives the command queue, Core, event store, and Notion materialization without a provider.
6. Add negative tests proving a simulated envelope cannot become live by changing `integration_mode`, no live connection identifier exists in test fixtures, and neither simulator can create an atomic state write. Existing contract tests establish the first and third boundaries only at schema level. [tests/contracts/test_integration_contracts.py:62-124](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts.py:62)

## Contradictions and Risks

1. **Scope evolution requiring reconciliation:** The original Sprint 4 plan defines pilot, acceptance, and handoff documentation as its scope. [docs/03-sprint-plan.md:131-142](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/03-sprint-plan.md:131) DEC-0018 subsequently requires local integration simulators, event storage, and project operations. [00_admin/DECISIONS.md:81-93](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:81) Treat DEC-0018 as the active governing decision and update Sprint 4 acceptance criteria before implementation.
2. **Schema-model gap:** DEC-0018 names customer, assignment, approval, deadline, blocker, metrics, and adjustment tracking, while the current Notion schema supports only six record types. [00_admin/DECISIONS.md:86-89](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:86), [standards/integrations/notion-projection.schema.json:27-28](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection.schema.json:27) Implementation without a schema version strategy would violate closed-contract discipline.
3. **Transport-model gap:** Current tests validate static fixtures and schemas, not simulator behavior, queue ordering, retries, DLQ, projection conflicts, or 3b scheduling. [tests/contracts/test_integration_contracts.py:52-124](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts.py:52) Do not present a future simulator as integrated until the behavioral tests pass.
4. **Approval boundary ambiguity:** The operator task schema permits an operator action named `approve_gate`, while the n8n command schema correctly excludes it. [standards/operator/operator-task.schema.json:16](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/operator/operator-task.schema.json:16), [standards/integrations/n8n-command.schema.json:22](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-command.schema.json:22) Resolve it by documenting `approve_gate` as a human intent submitted to the Core, never as an n8n action or direct Notion write.

## Build Recommendation and Review Gates

**Recommendation:** Build the local Core event boundary first, then file-backed n8n and Notion simulators using only the current declared Python runtime. Version the schema expansion before writing simulator logic. Do not add live transports, credentials, database IDs, provider SDKs, or claims of live compatibility.

1. **Contract gate:** v2 schemas are closed Draft 2020-12 contracts, preserve mode exclusivity, and have valid and negative fixtures for every new record and event.
2. **Authority gate:** tests prove that simulator code cannot mutate a run, approve a gate, complete a run, or overwrite current status outside `process_transition`.
3. **Transport gate:** parameterized ten-fixture tests prove delivery replay, ordering delay, bounded retry, DLQ provenance, conflict display, and resume with current revision.
4. **Workflow gate:** an offline full `0 -> 4b` run creates projection records and typed assignments at each gate; Step 3b runs only for explicit 30/60/90 checkpoint dates and produces a new revision.
5. **Review gate:** Raphael and Jesse validate the Notion operational views, role routing, and Operator Console subordination against DEC-0018 before any live-integration design begins.
