# Sprint 4 Stage A Integration Contract V2 Implementation

Date: 2026-08-19
Author: Raphael Rechberger
Status: completed contract stage

## Scope Delivered

This Stage A delivery adds V2 integration contracts without modifying V1 contracts, fixtures, tests, services, prompts, state, or configuration.

- `workflow-event-v2.schema.json` preserves the 13 V1 event types and adds the eight approved V2 event types. Every event requires correlation, idempotency, tenant, project, run, step, revision, and a closed event-specific payload.
- `event-catalog-v2.json` has exact event parity with the event schema and documents non-authoritative event purposes.
- `notion-projection-v2.schema.json` defines the 17 approved operational record types, typed closed relations, event provenance, `transition_service` authority, and `atomic_state_writer: false`.
- `notion-proposal.schema.json` accepts only human intents and rejects direct canonical state, hash, and revision writes outside `expected_revision`.
- `notion-snapshot.schema.json` defines non-authoritative local materialization output with projection revision, source watermark, records, and conflicts.
- The four n8n schemas define deterministic local clock state, a bounded retry policy, a command queue, wait subscriptions, retry entries, and DLQ provenance. Their command vocabulary excludes gate approval and run completion. Confirmed performance checkpoints are exactly 30, 60, and 90.
- V2 fixtures contain simulated positive examples, all required negative boundary examples, and a client-neutral reference matrix for all ten existing domain archetypes.

All V2 root schemas declare Draft 2020-12, a unique stable integration `$id`, and closed root objects. Contracts that are local simulator state are explicitly simulated and accept no live identifier. The projection retains the required simulated or live exclusivity.

## TDD Evidence

RED command:

```text
python -m unittest tests.contracts.test_integration_contracts_v2
```

Actual RED result: `Ran 0 tests` with one `FileNotFoundError` for the intentionally absent `standards/integrations/workflow-event-v2.schema.json`. This demonstrated the new test module failed before V2 contract files existed.

GREEN command:

```text
python -m unittest tests.contracts.test_integration_contracts_v2
```

Actual GREEN result: `Ran 11 tests in 0.152s`, `OK`.

The test module uses `Draft202012Validator` and `FormatChecker`. It validates positive V2 fixtures, all negative fixture boundaries, exact catalog parity, V1 schema and fixture compatibility, all ten archetype references, closed schema roots, stable IDs, closed payload definitions, Notion authority constants, and n8n command restrictions.

## Full Verification

Full OMO command:

```text
python tests/run_full_suite.py
```

Actual result: passed. Acceptance runner: 7 tests. Root unittest discovery: 171 tests. Contract unittest discovery: 48 tests. Total: 226 tests.

Diagnostic command was run for `tests/contracts/test_integration_contracts_v2.py`. The environment reported that `basedpyright` is not installed and that installation had previously been declined. No Python diagnostics were available from that tool. The focused tests and full suite passed with the repository Python runtime.

## Limitations

This Stage A work intentionally supplies contracts and fixtures only. It does not implement the Stage B API or event store, and it does not implement the Stage C Notion or n8n simulators. No live Notion or n8n connection, credentials, database IDs, provider call, crawler, deployment, or customer-specific production constant was introduced.
