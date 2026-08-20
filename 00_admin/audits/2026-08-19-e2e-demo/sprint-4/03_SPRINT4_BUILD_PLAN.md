# Sprint 4 Build Plan

Date: 2026-08-19
Author: Raphael Rechberger
Status: approved for execution

## Goal

Build a fully executable local Heartweb Core API with append-only events, a transport-faithful n8n simulator, and a Notion project, task, assignment, review, approval, metric and 30/60/90 tracking simulator. Live Notion and n8n connectivity remains disabled.

## Governing Architecture

- Local Core runs without Notion or n8n.
- Transition Service remains the only atomic workflow state authority.
- Routing Service remains the canonical error-to-owner authority.
- n8n later orchestrates the complete workflow through versioned commands and events.
- Notion remains the central operative customer, project, task and tracking surface.
- Operator Console remains a subordinate specialist view.
- Confirmed performance checkpoints are day 30, 60 and 90.
- AHD is only the Golden Path fixture. Production contracts remain client-neutral.
- The project is stateful. Every technical LLM worker and provider session is replaceable.
- A technical session may be reused as a cache but is never the project source of truth.

## Stage A: Integration Contract V2

Create additive v2 contracts while preserving v1 compatibility:

- workflow event v2 and event catalog v2
- Notion projection v2
- Notion human-intent proposal
- Notion projection snapshot/query result
- n8n simulation state, wait subscription, retry entry and DLQ entry
- valid and negative simulated fixtures

Required Notion record types:

- customer
- project
- run
- step
- task
- assignment
- artifact
- gate
- review
- approval
- blocker
- defect
- escalation
- performance_checkpoint
- metric
- adjustment_proposal
- integration_status

Required additional events:

- assignment.created
- approval.recorded
- blocker.resolved
- performance.checkpoint_due
- metric.recorded
- adjustment.proposed
- integration.delivery_failed
- integration.conflict_detected

Gate:

- closed Draft 2020-12 contracts
- simulated and live identities are mutually exclusive
- v1 fixtures remain valid against v1
- no live database IDs or credentials
- ten client-neutral domain archetypes remain supported

## Stage A2: Context and LLM Run Contracts

Create closed runtime contracts and deterministic builders before the Operator API:

- `standards/runtime/logical-project-session.schema.json`
- `standards/runtime/official-prompt-registry.schema.json`
- `standards/runtime/official-prompt-registry.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/context-package.schema.json`
- `standards/runtime/llm-run-request.schema.json`
- `standards/runtime/llm-run-result.schema.json`
- `services/context_builder/builder.py`
- `services/context_builder/validator.py`
- `services/context_builder/session_policy.py`
- focused positive and negative fixtures and tests

Context Package requirements:

- tenant, project, run, step, trigger and target revision
- official prompt ID, version, path and SHA-256
- exact Project Intake reference and hash for Step 0
- exact released Project V2 reference and hash for Steps 1 through 4b
- exact released predecessor artifact IDs, revisions and hashes
- current rejected artifact and findings for revision runs
- Evidence, Decisions, Gate and Operator Instruction references
- active, released, rejected, superseded and historical source states
- explicit untrusted-evidence labels
- deterministic include order and package SHA-256
- no arbitrary caller filesystem paths

LLM Run requirements:

- worker profile, provider, model and model policy
- tool policy and allowed operations
- context package ID and hash
- run mode: initial step, next step, revision, retry or resume
- optional technical session reference and explicit reuse policy
- default fresh execution for each step and substantial revision
- input, output, artifact and result hashes
- start, finish, status, error and token usage metadata
- no completion, approval or release authority

Revision package requirements:

- official step prompt
- released predecessors
- rejected current artifact
- machine findings and human findings
- operator revision instruction
- immutable fields and forbidden changes
- expected output contracts and new revision

Gate:

- a complete run can be reconstructed without an old provider session
- all nine official prompts are registry-bound by path, version and SHA-256
- multi-output Steps bind every output contract instead of selecting one
- missing, stale, superseded, hash-invalid or cross-tenant context fails before dispatch
- technical session reuse cannot change package inputs or bypass validation
- Context Package contents are deterministic and client-neutral
- every run is auditable by prompt, model, worker, tools, context, hashes and token use

## Stage B: Local Operator API and Event Store

Create:

- `services/operator_api/models.py`
- `services/operator_api/repository.py`
- `services/operator_api/event_store.py`
- `services/operator_api/app.py`
- `tests/test_operator_api.py`
- `tests/test_operator_event_store.py`

Read endpoints:

- projects
- workflow
- steps
- artifacts
- gates
- tasks
- tickets
- assignments
- performance checkpoints
- metrics
- adjustment proposals
- integration status
- logical project session
- context packages
- LLM run history and run details

Command endpoints:

- start
- request revision
- request input
- create defect
- escalate
- request waiver
- approve
- reject
- resolve
- resume

Rules:

- no direct status write
- route and body identity must match
- transition commands delegate to Transition Service
- errors delegate to Routing Service
- event append must succeed before success response
- only a validated Context Package can create an LLM Run Request
- technical session reuse is optional and policy-controlled
- a missing technical session rebuilds from files instead of losing project context
- append-only JSONL, idempotent replay and conflicting replay protection
- server-side tenant/project workspace registry
- path containment, no symlink or reparse escape
- Windows and Linux compatible locking

Gate:

- health and readiness endpoints
- startup fails on invalid graph, policy, schema or workspace
- tenant isolation and no mutation on failed commands
- OpenAPI generated from FastAPI only

## Stage C: Notion and n8n Simulators

Create:

- `services/integrations/notion_simulator.py`
- `services/integrations/n8n_simulator.py`
- local simulation fixtures and stores
- `tests/test_notion_simulator.py`
- `tests/test_n8n_simulator.py`

Notion simulator behavior:

- materialize v2 records from accepted events
- maintain relations, source revision and source event
- assign copywriter, designer, developer and reviewer work
- preserve stale edits as conflicts
- translate human intents to typed Core commands
- never write canonical run state directly

n8n simulator behavior:

- orchestrate 0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b
- wait for gates and tasks
- retry with original correlation and idempotency identity
- create DLQ entries after bounded exhaustion
- request resume through the Core
- create performance checkpoints at day 30, 60 and 90
- request immutable Step 3b adjustment proposals
- dispatch only validated LLM Run Requests and retain their Context Package identity
- use fresh technical sessions by default and treat reused sessions only as cache hints
- never approve gates or complete runs directly

Gate:

- parameterized tests across all ten domain archetypes
- replay, out-of-order, stale edit, retry, DLQ and resume tests
- no simulated fixture can masquerade as live

## Stage D: OpenAPI, Type Generation and Integration Suite

Create:

- OpenAPI snapshot
- generated `apps/operator-console/src/generated/api-types.ts`
- local API integration tests
- Golden Path and negative path fixtures

Scenarios:

- Golden Path
- rejection
- missing input
- workflow defect
- escalation
- waiver
- idempotent replay
- role assignment
- Notion tracking
- 30/60/90 metrics
- Step 3b adjustment proposal
- lost technical session recovery
- deterministic Context Package reproduction
- revision and rerun package preview
- stale or cross-tenant context rejection
- technical session cache reuse without authority
- wait and resume
- retry and DLQ

## Review Sequence

1. Contract spec review
2. Contract quality review
3. API spec review
4. API quality review
5. Simulator spec review
6. Simulator quality review
7. Host full suite
8. OMO full suite
9. `hermes verify --json`
10. Sprint 4 integration approval

## Explicit Exclusions

- live Notion API
- live n8n instance
- Notion database IDs
- credentials
- provider calls
- crawling
- deployment
- direct Notion or n8n canonical status mutation
- AHD-specific production constants
