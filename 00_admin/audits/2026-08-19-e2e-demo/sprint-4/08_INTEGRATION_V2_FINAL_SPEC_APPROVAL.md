# Sprint 4 Stage A Integration V2 Final Specification Approval

Date: 2026-08-19

Scope: Independent read-only re-review of the current Stage A Integration V2 contracts, V1 compatibility, fixtures, tests, and working-tree evidence after report 07. DEC-0018 is the governing decision.

## Terminal Decision

`APPROVED`

Stage A is approved as an additive Integration Contract V2 delivery. This decision approves contracts and fixtures only. Stage B and Stage C remain explicitly unstarted and are not implied by this approval.

## Findings

### P0

No findings.

### P1

No findings.

The three P1 findings in reports 05 and 06 are closed by current contracts and independent mutation probes:

1. Shared typed record-map contract and exact reuse: `notion-projection-v2.schema.json` and `notion-snapshot.schema.json` both reference the same stable `notion-record-v2.schema.json` URI for `records`. The focused suite asserts reference equality. A snapshot records array and an untyped external record were independently rejected.
2. ID-prefix/type binding and duplicate record identity: the shared record map is an object with closed prefix-specific keys. Each key prefix selects a definition whose `record_type` is the corresponding constant. Unknown keys and a `project-*` key carrying `record_type: customer` were independently rejected. A record map has one value per object key, so a second record with the same identity cannot coexist in the materialized map. Typed relations remain separately protected with `uniqueItems: true`.
3. Retry and DLQ integrity: simulation retry policy, retry entries, and DLQ entries all fix `max_attempts` at three. Retry entries accept only attempts one and two. DLQ entries require attempt three. Independent mutations for policy value five, retry attempt three, and DLQ attempt two were rejected. Retry and DLQ schemas require `step_id` and `expected_revision`; DLQ additionally requires original command, delivery, correlation, idempotency, tenant, project, run, failure code, first-failure, and final-failure provenance.

### P2

No findings.

### P3

No findings.

## Requirement Closure Evidence

| Requirement | Current evidence | Result |
|---|---|---|
| DEC-0018 authority boundary | The local Core retains protected status, hash, revision, and gate decisions. V2 projection requires `state_authority: transition_service` and `atomic_state_writer: false`. V2 n8n command vocabulary excludes approval and completion. | Closed |
| Additive V2 with V1 compatibility | Current V1 workflow-event, Notion projection, and n8n-command schemas remain present. The V2 suite validates each current V1 fixture against its V1 schema. | Closed |
| 21 event types and closed payloads | V2 event schema and catalog have exact parity for the 13 V1 and eight approved V2 event types. Focused test validates every simulated event and all event payload definitions are closed. | Closed |
| 17 Notion record types | The shared record map defines and binds customer, project, run, step, task, assignment, artifact, gate, review, approval, blocker, defect, escalation, performance checkpoint, metric, adjustment proposal, and integration status. | Closed |
| Source provenance | Records require source event and source revision. Projections require source event and revision. Snapshots require projection revision and source-event watermark. Retry and DLQ entries require identity and delivery provenance. | Closed |
| Simulated/live exclusivity | V2 events and projections require exactly the appropriate simulation or live identifier. Snapshots and local n8n state are simulated-only. Focused tests reject simulated-to-live mutations. | Closed |
| Retry before exhaustion and DLQ at exhaustion | Retry attempt enum is `[1, 2]`; DLQ attempt and maximum are both `3`. Direct mutations confirmed the prohibited boundaries fail schema validation. | Closed |
| Required retry/DLQ provenance | Retry requires delivery, correlation, idempotency, tenant, project, run, step, and expected revision. DLQ requires those fields plus original command, failure code, first failure, and final failure timestamps. Direct removal probes rejected every required field checked. | Closed |
| 30/60/90 and Step 3b | Simulation state permits only `[30, 60, 90]`. Workflow graph defines Step 3b as repeatable, post-publication, outside the initial route, and creating a new revision. | Closed |
| Ten client-neutral archetypes | V2 matrix references exactly the ten current domain fixtures, has standard, international multilingual, and regulated local variants, and contains no customer name or customer ID fields. | Closed |
| Client neutrality and exclusions | V2 schemas and catalog contain neither `ahd` nor `customer-national-b2b`. Review found no live connection, credential, database ID, provider call, crawler, deployment, commit, or push in the Stage A surface. | Closed |
| Workflow, runtime, operator, and domain compatibility | Current workflow graph preserves the exact initial route and protected 3b sideflow. Transition commands require identity, revision, idempotency, operation, and hashes. Operator task contracts require artifact and evidence lineage. Domain fixtures validate across all ten archetypes in the full suite. | Closed |

## Review Inputs Inspected

- `AGENTS.md` and DEC-0018 in `00_admin/DECISIONS.md`.
- Sprint 4 reports 01 through 07. Reports 01 through 04 were used only as navigation. Findings from reports 05 and 06 were revalidated against the current schemas, fixtures, and tests.
- Current V1 integration schemas: workflow event, Notion projection, and n8n command.
- Current V2 schemas: workflow event, event catalog, shared Notion record map, projection, proposal, snapshot, simulation state, wait subscription, retry entry, and DLQ entry.
- All 28 current V2 fixtures and the focused V2 integration contract suite.
- Relevant workflow, runtime, operator, and domain contracts, including workflow graph, transition command, operator task, and project domain schemas.
- Current working tree, including relevant untracked Stage A schemas, fixtures, tests, and audit material.

## Validation Executed

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
```

Result: 14 tests passed.

```text
python tests/run_full_suite.py
```

Result: 229 tests passed: 7 acceptance, 171 root unittest discovery, and 51 contract unittest discovery.

```text
python - <<'PY' ... Draft202012Validator registry/meta-validation and direct mutations ... PY
```

Result: all nine V2 schemas meta-validated; all 28 V2 fixtures parsed; every independent closure mutation was rejected. Probes covered unknown record keys, key/type mismatch, array snapshots, untyped snapshot records, retry policy other than three, retry at exhaustion, pre-exhaustion DLQ, and removal of `step_id`, `expected_revision`, `original_command_id`, `delivery_id`, `correlation_id`, and `idempotency_key` from DLQ entries. Every negative V2 fixture was also rejected by its declared schema.

```text
git status --short --untracked-files=all
git diff --no-ext-diff --stat
```

Result: the worktree contains substantial pre-existing modified and untracked Sprint material, including the Stage A contract surface. `git diff --check` reported no whitespace error. CRLF conversion warnings were emitted for pre-existing tracked files. No source, test, fixture, schema, state, decision, plan, requirement, Docker, or configuration file was changed by this review.

## Residual Scope Note

This is not approval of an implemented local API, append-only event store, Notion simulator, n8n simulator, live Notion, live n8n, or any Stage B or Stage C behavior. Those stages require their own implementation and review gates.
