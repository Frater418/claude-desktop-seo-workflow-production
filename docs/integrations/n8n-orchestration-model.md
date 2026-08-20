# n8n Orchestration Model

## Authority and Scope

n8n is transport and orchestration middleware, not a workflow state authority. Under DEC-0015, the local implementation is simulated only. It receives typed commands, dispatches local work, waits for events or gates, retries delivery, routes exhausted messages to a dead-letter queue, and requests resume through the Transition Service.

An n8n command must include `command_id`, `tenant_id`, `project_id`, `run_id`, `step_id`, `correlation_id`, `idempotency_key`, `expected_revision`, and `integration_mode`. The supported command types are `dispatch_tool_run`, `wait_for_gate`, `retry_delivery`, `resume_run`, and `dead_letter`. `approve_gate` and `complete_run` are intentionally not command types. n8n cannot directly approve a gate or complete a run.

## Modes

`simulated` commands require a `simulation_id` and cannot declare a live connection. `live` commands require a `live_connection_id` and cannot declare a simulation. No current positive fixture is live. A simulated command with only its mode changed to `live` is invalid because it lacks a live connection and retains its simulation identity.

## Wait, Retry, and Resume

`wait_for_gate` creates no state transition. It waits for a typed `gate.approved`, `gate.rejected`, task, or blocker event. `retry_delivery` reuses the original idempotency key and correlation ID. A retry never invents a new command for the same delivery.

`resume_run` is a request, not a state mutation. The Transition Service compares `expected_revision` with canonical state and rechecks the workflow graph, predecessor release, artifacts, gates, and approvals. A stale or invalid request fails fast and produces no run change.

## Duplicate, Out-of-Order, and DLQ Semantics

Delivery is at least once. Duplicate commands with the same idempotency key are recognized as replay, not a new action. Duplicate events are deduplicated by `event_id`. Out-of-order messages are retained for audit and delayed until their required predecessor is available. They must not overwrite newer canonical revisions.

Retries use bounded attempts. After the bounded retry policy is exhausted, n8n emits a `dead_letter` command and records the command ID, correlation ID, idempotency key, expected revision, attempt count, and failure reason. DLQ handling creates a typed task, defect, or escalation through the normal routing path. It never changes run state directly.
