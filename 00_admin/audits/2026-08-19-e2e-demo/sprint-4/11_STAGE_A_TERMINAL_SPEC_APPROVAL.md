# Sprint 4 Stage A Terminal Specification Approval

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Independent terminal approval audit of Sprint 4 Stage A only. This review used local read-only inspection and test execution. It modified only this report. Stage A2 and later stages are excluded.

## Governing Baseline

DEC-0018 requires a locally executable Core and reserves canonical workflow status, hashes, revisions, and gate decisions to the local Core and Transition Service. n8n is the transport and orchestration boundary. Notion is the non-authoritative operational projection.

The Stage A build-plan scope is the additive Integration Contract V2 delivery: V2 workflow event and catalog, V2 Notion projection, proposal, snapshot, n8n simulation state, wait subscription, retry entry, DLQ entry, and simulated positive and negative fixtures. V1 contracts and fixtures must remain valid.

## Audit Inputs

- `AGENTS.md` and DEC-0018 in `00_admin/DECISIONS.md`.
- Sprint 4 reports 01 through 10. Reports 01 through 04 were navigation only. Every P1 from reports 05, 06, and 09 was rechecked against the current filesystem and by local execution.
- Current V1 and V2 integration contracts, all V2 fixtures, focused tests, `services/integration_contracts/notion_graph.py`, workflow graph, runtime transition command, operator task contract, domain project contract, and ten-archetype matrix.
- Current worktree state and diff. The worktree contains extensive pre-existing tracked and untracked Sprint material. `git diff --check` returned success. Git emitted only CRLF conversion warnings for pre-existing tracked files.

## Requirement Closure

| Requirement | Independent evidence | Result |
|---|---|---|
| Closed Draft 2020-12 V2 contracts | 35 integration, workflow, runtime, operator, and domain schema files passed `Draft202012Validator.check_schema`. The focused suite confirms the nine V2 root schemas are closed and have distinct stable IDs. | Closed |
| Additive V2 and V1 compatibility | `test_v1_schemas_and_fixtures_remain_compatible` validated the current V1 event, Notion projection, and n8n command fixtures against their V1 schemas. | Closed |
| 21 event types and closed payloads | Static check found 21 V2 event types and exact event-catalog/purpose parity. Focused tests validated one simulated fixture for each event and verified closed payload definitions. | Closed |
| 17 Notion record types | Static check found 17 prefix-specific record-map entries. The positive projection contains exactly the approved record vocabulary. | Closed |
| Shared projection and snapshot record schema | Projection and snapshot both reference the same stable `notion-record-v2.schema.json` URI. The focused suite asserts the reference equality and accepts valid projection and snapshot fixtures through a registry. | Closed |
| Structural relation type and target-prefix binding | The record-map relation definition uses closed `oneOf` branches for every relation type and target prefix. A production-validator probe changing a `project` relation target to `customer-00000001` was rejected. | Closed |
| Required `subject_id` | Every record value requires `subject_id`. A production-validator probe deleting it was rejected. | Closed |
| Map-key and subject equality through production validation | `validate_notion_graph` compares each records-map key with its `subject_id`. A copied record under `project-copy00001` retaining the original subject was rejected with `NOTION_GRAPH_SUBJECT_ID_MISMATCH`. | Closed |
| Local relation target existence | `validate_notion_graph` checks every relation target against the same records map after schema validation. A well-formed absent target was rejected with `NOTION_GRAPH_RELATION_TARGET_MISSING`. | Closed |
| Duplicate-edge detection independent of object order | `validate_notion_graph` deduplicates `(relation_type, target_record_id)` pairs. A duplicate edge with reversed JSON member order was rejected with `NOTION_GRAPH_DUPLICATE_EDGE`. | Closed |
| Legitimate distinct records remain accepted | A probe changed both the project map key and `subject_id` to `project-distinct01`, updated incoming relations, and the production validator accepted the graph. | Closed |
| Notion authority boundary | V2 projection fixes `state_authority` to `transition_service` and `atomic_state_writer` to `false`. Snapshot has the same non-authoritative constants. Proposal tests reject direct canonical writes. | Closed |
| n8n authority boundary | V1 and V2 n8n command vocabularies exclude approval and completion. Focused tests reject `approve_gate` and `complete_run`. | Closed |
| Retry and DLQ P1 closure from report 05 | Simulation policy and retry/DLQ contracts fix maximum attempts to three. Retry is limited to attempts one and two. DLQ requires attempt three plus `step_id`, `expected_revision`, original command, delivery, identity, correlation, idempotency, and failure timestamps. | Closed |
| Snapshot typing P1 closure from reports 05 and 06 | Snapshot now uses the shared closed V2 record map. Focused tests reject an array snapshot and an untyped external record. | Closed |
| Projection identity P1 closure from report 06 | Map keys provide unique syntactic record identity. Required `subject_id` plus production map-key equality rejects copied semantic content retained under a different key. | Closed |
| Relation graph P1 closure from report 09 | The production validator rejects unresolved targets, target-family mismatches, and unordered duplicate edges. | Closed |
| Simulated/live separation and no live state | V2 event and projection schemas require exactly one appropriate mode identity. Snapshot and n8n local state are simulated-only. Focused tests reject a simulated-to-live mutation. | Closed |
| 30/60/90 cadence and Step 3b position | Simulation state fixes checkpoints to `[30, 60, 90]`. Workflow graph retains initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b` and limits 3b to the repeatable post-publication sideflow. | Closed |
| Ten client-neutral archetypes | Static check found ten archetypes and the three required variants. Focused tests confirm exact source-fixture parity and absence of customer name and customer ID fields. | Closed |
| Client neutrality | Focused tests found no `ahd` or `customer-national-b2b` value in V2 contracts or catalog. No live database ID, credential, provider, crawl, deployment, or external integration was used in this audit. | Closed |

## Commands and Observed Results

```text
git status --short --untracked-files=all
git diff --check
```

Observed: the tree has broad pre-existing modified and untracked work, including the Stage A surface. `git diff --check` exited successfully. The tracked-file warnings were CRLF conversion warnings only.

```text
python -m unittest tests.contracts.test_integration_contracts_v2 tests.test_notion_graph_validator -v
```

Observed: 20 tests passed. This included 14 V2 contract tests and 6 direct production graph-validator tests.

```text
python tests/run_full_suite.py
```

Observed: exit code 0. Acceptance runner: 7 tests. Root unittest discovery: 177 tests. Contract unittest discovery: 51 tests. Total: 235 tests.

```text
python -c "... Draft202012Validator.check_schema(...) over standards/integrations, standards/workflow, standards/runtime, standards/operator, and standards/domain ..."
```

Observed: `META_VALIDATED=35`.

```text
python - <<'PY'
# Loads the current projection, snapshot, and injected V2 schemas.
# Calls services.integration_contracts.notion_graph.validate_notion_graph.
# Mutates map-key/subject mismatch, missing local target, relation prefix mismatch,
# reordered duplicate edge, missing subject_id, and a legitimate distinct record.
PY
```

Observed: map-key/subject mismatch, missing local target, relation-prefix mismatch, reordered duplicate edge, and missing `subject_id` were all rejected. The legitimate distinct record and the positive snapshot were accepted.

```text
python - <<'PY'
# Counts V2 event types and record-map entries; asserts catalog parity, shared record-map
# reference, ten archetypes, three variants, and no customer name or ID matrix fields.
PY
```

Observed: `events:21`, catalog parity passed, `record_types:17`, shared record map passed, `archetypes:10`, and client-neutral matrix checks passed.

## Findings

### P0

None.

### P1

None. The P1s raised in reports 05, 06, and 09 are closed by the current shared schema and production-validator behavior, with the direct probes recorded above.

### P2

None.

### P3

None.

## Scoped Exclusion

This approval covers Stage A contracts, fixtures, and validation behavior only. It does not assess or begin Stage A2, Stage B, Stage C, Stage D, live Notion, live n8n, provider connectivity, crawling, deployment, or any API or simulator implementation.

## Terminal Verdict

`APPROVED`
