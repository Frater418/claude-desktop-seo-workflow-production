# Notion Operating Model

## Product Purpose

Notion is Heartweb's central operative workspace for Jesse and the implementation team. Heartweb delivers a complete customer concept and implementation project to Notion after the Step-0-to-Step-4B production workflow is approved.

The Notion project contains the customer context, strategy, architecture, roadmap, Copywriter briefings, Developer specifications, artifacts, implementation tasks, responsibilities, priorities, deadlines and relations required to execute the concept.

## Lifecycle Boundary

### Before handoff

The Heartweb Core and Operator Console create, validate, revise and approve the customer concept. Core-internal tasks, blockers, reviews and Human Gates exist only to complete the Step-0-to-Step-4B production workflow. The Transition Service remains the atomic authority for that workflow.

### After handoff

The Delivery release creates the Notion customer project and its implementation task matrix. Copywriter, design, development, review and launch tasks are then owned and managed in Notion. Their status, comments, assignees, deadlines and daily execution do not update the Core, resume a Core run, approve a Core gate or create artifact revisions.

Stable Heartweb IDs and released artifact hashes remain attached for traceability, but post-handoff Notion task execution is not a projection of an active Core run.

## Allowed Automated Re-entry

The only planned post-handoff re-entry into the Core is the Step-3B performance cycle at day 30, 60 and 90.

At each checkpoint, n8n combines:

- the released core strategy and 120-day plan;
- the publication registry and actual URLs;
- verified Google Search Console, Ahrefs and applicable local performance data;
- publication dates so content younger than the approved observation window is excluded.

The Core compares plan and actual results, classifies performance, produces a versioned adjustment proposal and preserves the original plan. After explicit strategy approval, the accepted adjustment updates future planning and can create or revise future Notion tasks.

## Integration Modes

`simulated` means local fixture or simulator transport only. It requires a `simulation_id` and cannot carry a `live_connection_id`.

`live` means a future explicitly configured transport. It requires a `live_connection_id` and cannot carry a `simulation_id`. The current local release has no live Notion write path.

## Delivery Semantics

The first release produces a manual Notion import pack. The future live adapter creates or updates the customer, project, strategy, artifact references, task matrix and performance checkpoints idempotently.

Duplicate delivery is deduplicated by stable external ID and source revision. Delivery conflicts fail visibly. Notion execution fields are not reconciled back into Core workflow state.

## Explicit Non-goals

- no Copywriter completion callback to the Core;
- no Developer completion callback to the Core;
- no Core resume from post-handoff task status;
- no ongoing synchronization of comments, assignees or deadlines into Core state;
- no automatic quality judgment of final human copy or implementation in the initial operating model;
- no second workflow engine inside Notion.

The Core automates concept production. Notion controls human implementation. Step 3B is the planned performance feedback loop.
