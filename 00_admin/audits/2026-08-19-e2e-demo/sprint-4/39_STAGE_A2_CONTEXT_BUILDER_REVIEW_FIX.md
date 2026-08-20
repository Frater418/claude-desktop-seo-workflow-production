# Sprint 4 Stage A2 Package A2.2 Context Builder Review Fix

Date: 2026-08-20
Author: Raphael Rechberger
Branch: `feature/e2e-operator-workflow-system`
Scope: Bounded pure Context Builder remediation for reports 37 and 38 only. Report 36 is a historical predecessor and was not modified.

## Delivered Remediation

- Added pre-sort source revision parsing. String, bool, float, missing, and values below one now raise immutable `ContextBuildError` with `ERROR_CONTEXT_SCHEMA_INVALID` at `/sources/<index>/revision`. Integer revisions remain unchanged.
- Added a pure RFC3339 parser that accepts `Z` and signed offsets, normalizes to UTC, and rejects malformed or naive input with immutable Context Builder errors. Source `valid_until <= evaluation_at` is stale and available-cache `expires_at <= now` is expired.
- Required exact current-record equality for `source_id`, `tenant_id`, `project_id`, `revision`, `content_sha256`, and `source_status`. Predecessors also require graph-valid `step_id` and package-lineage `run_id`. The selected Project V2 therefore accepts only an exactly released current record.
- Required predecessor release tenant, project, released status, graph step, artifact ID, revision, hash, and current predecessor record `run_id` equality.
- Restricted technical reuse to exactly matching available caches. Known unavailable states `missing`, `lost`, `expired`, and `invalid` recover fresh. Unknown or malformed states deny fail closed.
- Added one canonical result-record hash calculation over the entire result mapping excluding only `result_sha256`. Succeeded, failed, and cancelled records reject forged hashes.

## TDD Evidence

RED command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
```

RED result: 23 tests ran in 4.106 seconds with 13 failures and 3 errors. The failures reproduced accepted substituted source ID, Project V2 lifecycle drift for active, rejected, superseded, and historical states, wrong predecessor release run, lexical offset equality and before-expiry false greens, unknown cache reuse, malformed timestamps, and invalid source revisions. The succeeded, failed, and cancelled forged result-hash assertions also failed before the integrity check existed.

GREEN focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
```

GREEN result: 23 tests passed in 4.594 seconds.

Host full suite command:

```sh
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Host result: passed. Acceptance: 7 tests. Root unittest discovery: 205 tests. Contract unittest discovery: 59 tests. Total: 271 tests.

OMO full suite command:

```sh
docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py'
```

OMO result: passed. Acceptance: 7 tests. Root unittest discovery: 205 tests. Contract unittest discovery: 59 tests. Total: 271 tests.

Compilation command:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m py_compile services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py tests/test_context_builder.py
```

Compilation result: exit status 0.

Diagnostics were requested for every changed Python file. The local `basedpyright` language server is unavailable because installation was previously declined. Python 3.11 is unavailable: `python3.11 --version` returned `command not found`. All listed tests ran with the available Python 3.12 interpreter.

## Changed Files

- `services/context_builder/builder.py`
- `services/context_builder/validator.py`
- `services/context_builder/session_policy.py`
- `tests/test_context_builder.py`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-4/39_STAGE_A2_CONTEXT_BUILDER_REVIEW_FIX.md`

`services/context_builder/__init__.py` was not changed because the existing public canonical JSON hash helper lets tests construct semantically correct result hashes without a new export.

## Boundary and Exclusions

The remediated product code remains pure injected-data validation and policy logic. It contains no filesystem, provider, network, socket, subprocess, environment, clock, persistence, API, event, dispatch, cache-storage, workflow-state, or mutation behavior.

Stage B remains excluded: no persistence model, database, API, Event Store, event emission, provider dispatch, adapter, UI, Notion, n8n, technical-session storage, release mutation, routing change, schema change, fixture change, commit, push, or deployment was introduced.

## Freshness Check

After this report write, run:

```sh
stat -c '%Y %n' 00_admin/audits/2026-08-19-e2e-demo/sprint-4/39_STAGE_A2_CONTEXT_BUILDER_REVIEW_FIX.md services/context_builder/builder.py services/context_builder/validator.py services/context_builder/session_policy.py tests/test_context_builder.py
```

The report timestamp must be strictly later than every changed source and test file.
