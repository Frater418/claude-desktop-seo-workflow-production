# n8n orchestration model

**Author:** Raphael Rechberger
**Status:** Current integration authority
**Updated:** 2026-08-26
**Decision:** DEC-0025

## Product purpose

n8n is Heartweb's future transport and automation layer. It may automate the Step-0-to-Step-4B concept workflow, deliver the approved customer project to Notion and later run Step-3B performance checkpoints.

n8n is not workflow state authority and is not a continuous feedback bridge for daily staff tasks.

## Phase A: concept production

During Step 0 through Step 4B, n8n may:

- receive start and approval triggers from the Heartweb UI
- call versioned Core commands
- dispatch LLM, provider and deterministic tool runs
- wait for Core-internal Human Gates
- retry failed technical delivery
- route exhausted failures visibly
- request continuation through the Transition Service
- create the final Delivery release

The Core validates every transition, artifact, revision, gate and release. n8n cannot approve a gate or complete a run directly.

## Phase B: Notion handoff

After final release, n8n creates the complete Notion customer project from the approved Delivery package.

It creates:

- project and strategy records
- artifact references
- implementation tasks
- assignments
- priorities and deadlines
- relations
- performance checkpoints

The handoff is one-way with respect to Core workflow state. Post-handoff staff task changes remain in Notion and do not become `resume_run`, gate, revision or artifact commands.

## Phase C: performance re-entry

At day 30, 60 and 90, n8n starts the only planned post-handoff Core loop:

1. Load released strategy and 120-day plan.
2. Load publication dates and actual URLs.
3. Collect verified metrics from approved sources.
4. Submit a typed Step-3B run to the Core.
5. Receive a versioned adjustment proposal.
6. After explicit strategy approval, update future planning and applicable future Notion tasks.

Missing, stale or incomplete metrics stop the checkpoint. n8n does not estimate results.

## Commands and modes

Commands used during active Core runs include:

- `dispatch_tool_run`
- `wait_for_gate`
- `retry_delivery`
- `resume_run`
- `dead_letter`

They carry tenant, project, run, step, correlation, idempotency and expected revision fields.

`task.resolved` and `blocker.resolved` refer only to Core-internal production tasks before final handoff. They never refer to post-handoff staff tasks in Notion.

`simulated` commands require a simulation ID and cannot declare a live connection. `live` commands require a live connection ID and cannot declare a simulation. n8n is not part of the first local release; existing simulator records prove command contracts only and are not live integration Evidence.

## Error and replay behavior

- duplicate commands with one idempotency key are replay, not new work
- out-of-order events do not overwrite newer state
- retries are bounded
- exhausted delivery enters a visible dead-letter path
- integration failure never creates false canonical success

## Explicit non-goals

- no monitoring of daily Notion task status for Core progression
- no Copywriter or Developer submission callback
- no automatic Core review of human implementation work
- no bidirectional synchronization of Notion comments, assignees or deadlines
- no n8n-owned business rules
- no task-driven loop after handoff except scheduled Step 3B
