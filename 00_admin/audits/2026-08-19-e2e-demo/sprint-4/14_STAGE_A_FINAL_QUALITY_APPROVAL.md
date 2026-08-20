# Sprint 4 Stage A Final Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Fresh, independent, read-only final quality audit of Sprint 4 Stage A only. This report evaluates the Integration Contract V2 and Notion graph validator after report 13. Stage A2 and all later stages are explicitly excluded.

## Governing Baseline

DEC-0018 requires the local Core and Transition Service to retain canonical workflow status, hashes, revisions, and gate decisions. n8n is the transport and orchestration boundary. Notion is a non-authoritative operational projection. Stage A therefore remains local contract and graph-validation work.

Audit inputs were `AGENTS.md`, DEC-0018 in `00_admin/DECISIONS.md`, Sprint 4 reports 09 through 13, the current worktree and diff, `services/integration_contracts/notion_graph.py`, `tests/test_notion_graph_validator.py`, and `tests/contracts/test_integration_contracts_v2.py`.

## Findings

### P0

None.

### P1

None. Report 12's injected-schema ID error-handling finding is fully closed.

### P2

None.

### P3

None.

## Report 12 P1 Closure Evidence

`_registry()` now obtains each injected ID with `schema.get("$id")` before its type check. It raises `NotionGraphValidationError` with code `NOTION_GRAPH_SCHEMA_ID_INVALID` and path `(schema_name, "$id")` before constructing the local `referencing.Registry`.

An independent local probe deep-copied the three production injected schemas and tested each `record_map`, `projection`, and `snapshot` schema separately. For each schema it deleted `$id`, then repeated the probe with `$id` set to `None`, `7`, and `[]`.

- Result: all 12 probes raised `NotionGraphValidationError`.
- Every exception contained exactly `NOTION_GRAPH_SCHEMA_ID_INVALID` and exactly `(schema_name, "$id")`.
- No probe exposed `KeyError`, a `referencing` exception, a JSON Schema exception, a generated ID, or a fallback schema path.

This independently confirms the report 12 P1 is closed for the specified malformed injected-schema cases.

## Previous Stage A Graph Integrity Evidence

The focused graph-validator tests remain green for valid projection and snapshot graphs, map-key and `subject_id` equality, valid distinct entities, dangling targets, relation type and target family mismatch, and unordered duplicate-edge rejection. The focused V2 contract tests also remain green for closed Draft 2020-12 contracts, shared record-map references, V1 compatibility, authority boundaries, retry and DLQ bounds, simulated-only behavior, 30/60/90 cadence, and ten client-neutral archetypes.

## Commands And Observed Results

```text
python - <<'PY'
# For record_map, projection, and snapshot independently:
# delete $id, then set it to None, 7, and [];
# call validate_notion_graph on the positive projection;
# require NotionGraphValidationError, NOTION_GRAPH_SCHEMA_ID_INVALID,
# and the exact (schema_name, "$id") path.
PY
Result: SCHEMA_ID_STRUCTURED_PROBES=12. Every probe passed.

python -m unittest tests.test_notion_graph_validator tests.contracts.test_integration_contracts_v2 -v
Result: Ran 21 tests in 0.345s. OK.

python tests/run_full_suite.py
Result: exit 0. Acceptance: 7 tests. Root unittest discovery: 178 tests. Contract unittest discovery: 51 tests. Total: 236 tests.

python - <<'PY'
# Scan 45 Stage A schemas, fixtures, and source/test files for U+2013/U+2014,
# AHD and client constants; parse notion_graph.py and its direct test with
# ast.parse(feature_version=(3, 11)); reject filesystem, network, subprocess,
# fallback, and ERROR_ tokens from the validator source.
PY
Result: STATIC_STAGE_A_PATHS_OK=45. PYTHON_3_11_GRAMMAR_OK=2.

git status --short --untracked-files=all
git diff --check
Result: git diff --check exited 0 with CRLF warnings only. The tracked diff has no Stage A paths. The Stage A delivery is untracked in this pre-existing worktree and was audited directly from the filesystem. Broad unrelated tracked and untracked changes exist outside Stage A and are excluded from this decision.
```

## Scoped Exclusion

This decision covers Stage A only. It does not assess, start, recommend, or approve Stage A2, Stage B, Stage C, Stage D, API or simulator implementation, live Notion, live n8n, provider connectivity, crawling, deployment, commits, or pushes.

## Terminal Verdict

`APPROVED`
