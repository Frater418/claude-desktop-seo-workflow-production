# Notion Operating Model

## Authority and Scope

Notion is Heartweb's central operative interface under DEC-0012. It presents projects, runs, tasks, gates, artifacts, reviews, and approvals in the daily operating view. The Operator Console is a specialized view reachable from that operating model. Neither Notion nor the Operator Console is the atomic state writer.

The Transition Service is the only atomic state authority. It validates tenant, project, run, step, revision, artifact hash, quality gate, approval, and workflow graph rules before it changes a run. A Notion projection is created from accepted append-only workflow events. Every projection carries `source_event_id`, `source_revision`, `state_authority: transition_service`, and `atomic_state_writer: false`.

## Modes

`simulated` means local fixture or simulator transport only. It requires a `simulation_id` and cannot carry a `live_connection_id`.

`live` means a future explicitly configured transport. It requires a `live_connection_id` and cannot carry a `simulation_id`. The current local wave has no live fixture, connection, credential, or write path. DEC-0015 therefore requires every current positive fixture to be `simulated`.

## Field Edit and Conflict Semantics

A Notion field edit is an operator proposal, comment, assignment, or display preference until it is translated to a versioned command and accepted by the Transition Service. Editing a projected status, approval label, revision, artifact reference, or gate field does not change canonical state. A projection must never emit an atomic state write.

When a Notion edit conflicts with a newer projection, the newer accepted event and source revision win. The stale edit is retained as operator context and is not silently merged into canonical state. The UI must show the conflict, require an explicit next action, and submit that action with the current expected revision. A stale command fails fast and leaves the run unchanged.

## Delivery Semantics

Projection delivery is at least once. Duplicate event delivery is deduplicated by `event_id` and projection source revision. An out-of-order event is retained for audit but does not overwrite a projection produced from a newer revision. The projector waits for missing predecessor events where ordering is required, then retries with the same idempotency key. Exhausted retries enter the dead-letter queue with the event, failure reason, attempt count, and correlation ID.

## Gate and Resume Semantics

Notion may show a wait state for a human gate or missing input. It cannot approve a gate directly. The approved or rejected decision becomes a command that the Transition Service validates against the current artifact revision and SHA-256. A resolved task or accepted approval can create a resume request, but only the Transition Service may resume the run after revision and workflow checks pass.
