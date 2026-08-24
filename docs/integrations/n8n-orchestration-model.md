# n8n Orchestration Model

## Product Purpose

n8n is Heartweb's future transport and automation layer. It automates the Step-0-to-Step-4B concept workflow, delivers the approved customer project to Notion and later runs the Step-3B performance checkpoints. It is not a workflow state authority and it is not a continuous feedback bridge for daily team tasks.

## Automation Phase A: Concept Production

During Step 0 through Step 4B, n8n may:

- receive start and approval triggers from the Heartweb UI;
- call versioned Core commands;
- dispatch LLM, provider and deterministic tool runs;
- wait for Core-internal Human Gates;
- retry failed technical delivery;
- route exhausted failures visibly;
- request continuation through the Transition Service;
- create the final Delivery release.

The Core validates every transition, artifact, revision, gate and release. n8n cannot approve a gate or complete a run directly.

## Automation Phase B: Notion Handoff

After the final concept release, n8n creates the complete Notion customer project from the approved Delivery package. It creates the strategy records, artifact references, implementation tasks, assignments, priorities, deadlines and relations required by Jesse and the team.

This handoff is one-way with respect to Core workflow state. Post-handoff Copywriter, design, development, review and launch task changes remain in Notion. n8n does not translate those task changes into `resume_run`, gate, revision or artifact commands.

## Automation Phase C: Performance Re-entry

At day 30, 60 and 90, n8n starts the only planned post-handoff Core loop:

1. Load the released strategy and 120-day plan.
2. Load publication dates and actual URLs from the Notion project or tracking registry.
3. Collect verified performance metrics from approved sources.
4. Submit a typed Step-3B performance run to the Core.
5. Receive a versioned adjustment proposal.
6. After explicit strategy approval, update the future plan and applicable future Notion tasks.

The original plan remains immutable. Missing, stale or incomplete performance data stops the checkpoint instead of producing an estimated adjustment.

## Commands and Modes

Commands used during active Core runs include `dispatch_tool_run`, `wait_for_gate`, `retry_delivery`, `resume_run` and `dead_letter`. They require the existing identity, correlation, idempotency and revision fields.

`task.resolved` and `blocker.resolved` waits refer only to Core-internal production tasks before the final handoff. They never refer to post-handoff staff tasks in Notion.

`simulated` commands require a `simulation_id` and cannot declare a live connection. `live` commands require a `live_connection_id` and cannot declare a simulation. The current local release remains simulated.

## Explicit Non-goals

- no monitoring of daily Notion task status for Core progression;
- no Copywriter or Developer submission callback;
- no automatic Core review of human implementation work;
- no bidirectional synchronization of Notion comments, assignees or deadlines;
- no n8n-owned business rules or canonical workflow state;
- no task-driven loop after handoff except the scheduled Step-3B performance cycle.

Retries remain bounded and idempotent. Exhausted integration failures are recorded visibly and never create false canonical success.
