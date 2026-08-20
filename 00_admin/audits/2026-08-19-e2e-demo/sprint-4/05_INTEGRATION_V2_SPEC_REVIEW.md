# Sprint 4 Stage A Integration V2 Specification Review

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Read-only Stage A contract review. This report is navigation only and records no implementation direction.

## Verdict

`REQUEST_CHANGES`

The V2 contract set has strong coverage for the required event vocabulary, projection authority, simulated mode, V1 compatibility, 30/60/90 cadence, and the ten-archetype reference matrix. The two P1 contract gaps below prevent a complete Stage A approval because accepted V2 instances can lose required n8n delivery provenance and bypass the typed Notion record model in snapshot output.

## Findings

### P0

None observed.

### P1

1. n8n retry policy and DLQ provenance are not internally sufficient for the documented orchestration semantics.
   - Observed fact: the simulation state allows `retry_policy.max_attempts` from 1 through 10, while a retry entry accepts only `max_attempts: 3`. A local probe accepted a simulation state with `max_attempts: 5` and rejected the matching retry entry with `max_attempts: 5`. See [n8n-simulation-state.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-simulation-state.schema.json:13) and [n8n-retry-entry.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-retry-entry.schema.json:9).
   - Observed fact: the DLQ contract requires command, correlation, idempotency, attempt, and failure fields, but does not carry `expected_revision` or `step_id`. See [n8n-dlq-entry.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-dlq-entry.schema.json:7).
   - Concern: this conflicts with the orchestration model requirement that a DLQ record preserves expected revision, and it permits a valid simulation retry policy that cannot produce a matching valid retry entry. See [n8n-orchestration-model.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/docs/integrations/n8n-orchestration-model.md:23).

2. The Notion snapshot contract does not retain the V2 projection's closed 17-record vocabulary or typed relations.
   - Observed fact: the V2 projection defines exactly 17 record types and closed typed relations. See [notion-projection-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection-v2.schema.json:21).
   - Observed fact: the snapshot record definition accepts any nonempty `record_type` and `record_id`, with no relations field. A local probe accepted a snapshot record with `record_type: untyped_external_record` and `record_id: opaque-record`. See [notion-snapshot.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-snapshot.schema.json:11).
   - Concern: a snapshot or query result can therefore materialize an untyped record that cannot be verified against the operational projection model required by the Stage A build plan. See [03_SPRINT4_BUILD_PLAN.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/audits/2026-08-19-e2e-demo/sprint-4/03_SPRINT4_BUILD_PLAN.md:33).

### P2

None observed.

### P3

None observed.

## Confirmed Evidence

- DEC-0018 keeps Transition Service as the protected local authority, while n8n is orchestration and Notion is the operational projection. See [DECISIONS.md](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/00_admin/DECISIONS.md:81).
- V2 enumerates the 13 V1 event types plus the eight required new types, and the catalog has exact parity. See [workflow-event-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event-v2.schema.json:10) and [event-catalog-v2.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/event-catalog-v2.json:6).
- The V2 projection has all 17 required record types, source-event and source-revision provenance, `state_authority: transition_service`, and `atomic_state_writer: false`. See [notion-projection-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-projection-v2.schema.json:7).
- Human proposals are simulated-only, version-bound intents and reject direct canonical status, hash, and revision fields. See [notion-proposal.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-proposal.schema.json:7).
- The simulation state fixes confirmed checkpoints to exactly 30, 60, and 90. The workflow graph keeps Step 3b outside the initial route as a repeatable post-publication sideflow. See [n8n-simulation-state.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/n8n-simulation-state.schema.json:9) and [workflow-graph.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/workflow/workflow-graph.json:25).
- Simulated and live identities are mutually exclusive in V2 events and projections. The targeted masquerading probe was rejected. See [workflow-event-v2.schema.json](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/workflow-event-v2.schema.json:17).
- V1 event, projection, and n8n fixtures remain validated by their V1 schemas. The V2 test also checks the ten client-neutral archetype references and excludes AHD and customer-specific constants from V2 contracts. See [test_integration_contracts_v2.py](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_integration_contracts_v2.py:169).

## Validation Commands Run

```text
git status --short
git diff --check
git diff --no-ext-diff
git diff -- standards/integrations/... tests/fixtures/integrations/v2 tests/contracts/test_integration_contracts_v2.py
python -m unittest tests.contracts.test_integration_contracts_v2
python tests/run_full_suite.py
python - <<'PY' ... Draft202012Validator probes for missing identity, unknown payload, duplicate relation, simulated-to-live masquerade, direct proposal write, and invalid cadence ... PY
python - <<'PY' ... Draft202012Validator probes for retry-policy consistency and untyped snapshot records ... PY
```

Results: focused V2 contracts passed 11/11. Full suite passed 226 tests: 7 acceptance, 171 root discovery, and 48 contract discovery. The first local probe rejected every required negative boundary. The second produced the two P1 observations above.

## Current Diff Inspection

The working tree contains extensive pre-existing modified and untracked Sprint work. `git diff --check` reported no whitespace error. The Stage A V2 schemas, fixtures, and test module are untracked in the current diff, so they were inspected directly as the current filesystem artifacts. No live connection, credential, database ID, provider call, crawler, deployment, commit, or push was observed in the reviewed Stage A artifacts.
