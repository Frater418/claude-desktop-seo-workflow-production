# Sprint 4 Stage C Integration Simulators Implementation

Date: 2026-08-20
Author: Raphael Rechberger
Status: implemented and locally verified

## Scope

Stage C adds pure deterministic Notion and n8n simulators. Both modules accept only caller-injected mappings and schemas. They do not read or write files, inspect environment variables, use a system clock, open a socket, start a subprocess, call a provider, or change Core workflow state.

## Public APIs

- `services.integrations.notion_simulator.NotionContracts`: injected V2 event, catalog, proposal, and Notion graph contracts.
- `materialize_events(events, contracts)`: validates the V2 event stream and returns a schema-valid simulated Notion snapshot.
- `materialize_projection(events, contracts)`: returns the corresponding schema-valid non-authoritative Notion projection.
- `translate_proposal(proposal, current_revision, proposal_schema)`: validates a simulated human proposal and returns one typed Core command request. A stale revision returns `NOTION_SIMULATION_STALE_PROPOSAL` without changing a projection.
- `services.integrations.n8n_simulator.N8nContracts`: injected command, state, wait, retry, DLQ, graph, runtime-validator, and worker-profile dependencies.
- `N8nSimulationRequest` and `simulate_n8n(request, contracts)`: validate and deterministically return dispatch intents, wait subscriptions, retry entries, DLQ entries, resume command requests, and a new simulated state.

## Behavior

- Notion validates Draft 2020-12 schemas before events or proposals, requires exact V2 catalog parity, rejects live and masquerading identities, deduplicates equal event IDs, rejects changed replays, orders by occurrence instant and event ID, rejects revision rollback, and enforces one tenant, project, and simulation.
- Notion records retain canonical subject IDs, event and revision provenance, relations, simulation identity, and the immutable `transition_service` plus `atomic_state_writer: false` authority constants. Every requested V2 record type has a typed event mapping or a deterministic supporting projection record. Assignments retain their explicit copywriter, designer, developer, or reviewer role and never infer an owner.
- n8n validates command and state contracts, requires matching simulated identity, validates stored Context Package and LLM Run Request bindings before dispatch, defaults to fresh technical sessions, and treats reuse only as a policy decision. Lost cache returns `recover_fresh` with the same package binding.
- n8n permits the initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b` only with the matching released predecessor. Step `3b` requires a released `4b` predecessor and an explicit day 30, 60, or 90 checkpoint. Waits can target gate or task events. Resume returns a typed Core request and leaves simulation state unchanged.
- Delivery replays are deterministic, changed idempotency keys conflict, retries preserve identity and are bounded at three attempts, and exhaustion emits a schema-valid provenance-complete DLQ entry. Neither simulator creates approval, completion, release, or canonical-state authority.

## TDD And Tests

The first focused execution was intentionally red because the new `services.integrations` package did not yet exist. The import failures confirmed the missing behavior before implementation.

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_notion_simulator tests.test_n8n_simulator -v
```

Focused result: `Ran 14 tests` and `OK`.

Focused coverage includes V2 projection and snapshot graph validation, relation integrity, every typed assignment role, proposal staleness, authority constants, equal and changed replay, event ordering and revision rollback, all ten neutral domain archetypes, no-I/O static boundary checks, the full initial route, gate and task waits, cache-loss recovery, retry to DLQ, resume non-mutation, and 30/60/90-only Step 3b.

Host command:

```text
python tests/run_full_suite.py
```

Host result: acceptance `7/7`, root `231`, contract `59`, total `297`, all passing. The existing Starlette HTTPX deprecation warning was emitted without test impact.

OMO command:

```text
docker exec opencode-omo sh -lc 'cd /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow && python tests/run_full_suite.py'
```

OMO result: acceptance `7/7`, root `231`, contract `59`, total `297`, all passing. The same existing Starlette HTTPX deprecation warning was emitted without test impact.

The Host and OMO suites were rerun after the final Review projection, explicit unassigned-task refinement, and resolved-blocker projection. Both final executions remained green at the same total of `297` tests.

## Stage D Exclusions

This change does not create OpenAPI output, generated TypeScript types, API integration fixtures, UI work, live Notion or n8n connectivity, provider calls, credentials, deployment, persistence, or Core transition changes. Stage D remains excluded.

## Post-write Review

Each implementation file is under 200 pure lines and owns one transform boundary. Inputs are parsed at the injected JSON Schema boundary, no tagged variants use incomplete fallback discrimination, no type escape comments or raw session handles are present, and focused tests fail when the new behavior is removed. No new logging or defensive I/O layer was introduced.
