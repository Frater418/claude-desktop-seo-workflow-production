# Sprint 4 Stage A Integration V2 Quality Review

Date: 2026-08-19
Scope: Read-only independent review of Stage A contracts, fixtures, tests, domain support, and current worktree diff.
Governing decision: DEC-0018. This report is navigation only and does not prescribe edits.

## Verdict

REQUEST_CHANGES

## Findings

### P0

None observed.

### P1

1. Snapshot records are not constrained to the approved V2 record vocabulary or stable record-ID grammar. `notion-snapshot.schema.json` accepts arbitrary non-empty `record_type` and `record_id` values, despite the Stage A requirement for 17 typed operational record types and source provenance. A direct mutation of the positive snapshot to `record_type: unbounded_type` and `record_id: arbitrary-id` validated successfully. The focused suite only validates the positive snapshot and live-mode rejection, so it is a false green for this boundary.

2. Projection record IDs are not unique within a projection. `notion-projection-v2.schema.json` applies `uniqueItems` to relations only and has no collection-level uniqueness constraint for `records[].record_id`. A direct mutation that appended a second record with the same ID but a different title validated successfully. This leaves a non-deterministic materialization identity despite the required source event and revision provenance.

3. DLQ integrity does not require retry exhaustion. `n8n-dlq-entry.schema.json` accepts a DLQ entry with `attempt: 1` and `max_attempts: 3`. The retry entry fixes `max_attempts` to 3, while simulation state independently permits retry policies from 1 through 10. The focused suite validates positive entries but does not mutate attempt versus maximum-attempt semantics, so it is a false green for bounded retry and DLQ exhaustion.

### P2

None observed.

### P3

1. Python 3.11 execution could not be observed locally because `python3.11` is unavailable. The suite ran under Python 3.12.3. The inspected Stage A schemas and test module use no syntax that is visibly incompatible with Python 3.11, but this remains an unexecuted compatibility check.

## Observed Conforming Evidence

- All 34 reviewed integration, workflow, runtime, operator, and domain schemas passed `Draft202012Validator.check_schema`; all have unique stable `$id` values and closed root objects.
- The focused V2 contract suite passed 11 of 11 tests. It confirmed V1 fixture compatibility, V2 event catalog parity, 21 event types, 17 projection record types in the positive fixture, simulated/live mode separation, source-revision requirements, and ten client-neutral archetype references.
- Direct negative mutation checks confirmed that an extra V2 event payload field is rejected, a Notion proposal with `canonical_status: completed` is rejected, and an n8n `approve_gate` command is rejected.
- No direct state-write or n8n approval/completion path was observed in the Stage A contract surface. The projection authority is `transition_service`; `atomic_state_writer` is false; the n8n command vocabulary excludes approval and completion.
- The full local suite passed: acceptance 7, root unittest 171, contract unittest 48, total 226. This includes workflow, runtime, operator, domain, V1, V2, transition, retry-limit, and ten-real-domain-fixture coverage.
- The ten real domain fixtures were read and the domain test suite validates all ten. The V2 archetype matrix references all ten without customer names or IDs.
- The current diff was inspected with `git status --short`, `git diff --stat`, `git diff --no-ext-diff`, and `git diff --check`. It contains the additive Stage A contract and fixture surface plus unrelated tracked and untracked Sprint work. `git diff --check` reported only existing CRLF conversion warnings, not whitespace errors.
- A scan of all V2 integration schemas, V2 fixtures, and the V2 test found no Em-Dash or En-Dash characters. The only AHD text in that scope is the intentional negative assertion in `test_integration_contracts_v2.py`; no V2 schema or fixture contains an AHD constant.

## Validation Commands Run

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
python tests/run_full_suite.py
python -c "... Draft202012Validator.check_schema(...) across standards/integrations, workflow, runtime, operator, and domain ..."
python -c "... schema mutation probes for snapshot typing, duplicate projection IDs, and pre-exhaustion DLQ ..."
python -c "... event payload, Notion direct-write, and n8n approval mutation probes ..."
GIT_MASTER=1 git status --short
GIT_MASTER=1 git diff --stat
GIT_MASTER=1 git diff --no-ext-diff -- . ':!00_admin/audits/2026-08-19-e2e-demo/sprint-4/06_INTEGRATION_V2_QUALITY_REVIEW.md'
GIT_MASTER=1 git diff --check
python3.11 --version
python --version
```

Results: focused V2 suite 11/11 passed; full suite 226/226 passed; 34 schemas parsed and meta-validated; three mutation probes unexpectedly validated as described in P1; Python 3.11 was unavailable; active runtime was Python 3.12.3.
