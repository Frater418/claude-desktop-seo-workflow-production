# Notion operating model

**Author:** Raphael Rechberger
**Status:** Current integration authority
**Updated:** 2026-08-26
**Decision:** DEC-0025

## Product purpose

Notion is Heartweb's central operative workspace for Jesse and the implementation team. Heartweb delivers a complete customer concept and implementation project to Notion after the Step-0-to-Step-4B workflow is approved.

The Notion project contains:

- customer and project context
- approved strategy and architecture
- 120-day roadmap
- Copywriter briefings
- Developer specifications
- artifact references
- implementation tasks
- assignees, priorities and deadlines
- relations and performance checkpoints

## Lifecycle boundary

### Before handoff

The Heartweb Core and Operator Console create, validate, revise and approve the customer concept. Core-internal tasks, blockers, reviews and Human Gates exist only to complete Step 0 through Step 4B.

Only the Transition Service changes canonical workflow state.

### After handoff

The Delivery release creates the Notion customer project and its implementation task matrix. Copywriter, design, development, review and launch work is then owned and managed in Notion.

Post-handoff Notion task status, comments, assignees, priorities and deadlines do not:

- update Core workflow state
- resume a Core run
- approve a Core gate
- create an artifact revision
- mutate released content

Stable Heartweb IDs and released artifact hashes remain attached for traceability only.

## Allowed automated re-entry

The only planned post-handoff Core re-entry is Step 3B at day 30, 60 and 90.

At each checkpoint, n8n combines:

- released strategy and 120-day plan
- publication registry and actual URLs
- publication dates
- verified Google Search Console, Ahrefs and applicable local metrics

The Core excludes content that has not reached the required observation window, compares plan and actual results and creates a versioned adjustment proposal. The original plan remains immutable.

After explicit strategy approval, the accepted adjustment may update future planning and future Notion tasks.

## First release

The first local Production release creates a manual Notion import pack. It does not require a live Notion connection.

The import pack separates:

- read-only concept provenance
- Notion-owned implementation execution
- scheduled performance checkpoints

It contains no inbound Core callback for daily staff tasks.

## Future live adapter

A live adapter may create or update customer, project, strategy, artifact references, tasks, assignments, priorities, deadlines, relations and performance checkpoints.

Delivery must be idempotent by stable external ID and source revision. Duplicate delivery must not create duplicate projects or tasks. Conflicts fail visibly.

## Explicit non-goals

- no Copywriter completion callback to the Core
- no Developer completion callback to the Core
- no Core resume from post-handoff task status
- no continuous synchronization of comments, assignees or deadlines into Core state
- no automatic quality judgment of final human copy or implementation in the first operating model
- no second workflow engine inside Notion

The Core automates concept production. Notion controls human implementation. Step 3B is the planned performance feedback loop.
