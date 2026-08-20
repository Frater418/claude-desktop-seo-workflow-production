# Stage C Integration Simulators Review Fix

Date: 2026-08-20
Author: Raphael Rechberger
Status: implementation and validation complete

## Scope

This bundled Stage C correction addresses every finding in report 50 within the allowed Notion and n8n simulator, V2 contract, fixture, and test boundary. Report 49 and report 50 were not changed.

## Report 50 Findings Addressed

- `S-P0-01`: `simulate_n8n` now invokes `validate_context_package` before `validate_llm_request`, using caller-injected exact source bytes, current records, workflow graph, releases, revision inputs, prompt registry, runtime validator, and deterministic state time. Forged package hashes, missing current records, source drift, stale records, and cross-identity packages fail before dispatch.
- `S-P0-02`: the closed simulation-state contract now requires `tenant_id` and `project_id`. Every command is bound to state tenant, project, and simulation before dispatch, wait, retry, DLQ, resume, or checkpoint work.
- `S-P1-01` and `S-P1-02`: Notion now orders by RFC3339 instant and event ID, resolves revision per projected subject, preserves stale subject attempts as typed conflicts, materializes lower-revision new subjects, and maps `integration.conflict_detected` to a provenance-bearing `integration_status` record plus a schema-valid snapshot conflict.
- `S-P1-03`: exact predecessor verification now binds tenant, project, run, step, artifact ID, SHA-256, revision, gate, and released status against current context evidence and release records. Bare or cross-tenant release mappings fail.
- `S-P1-04`: Step 3b accepts only days 30, 60, or 90 and requires both an exact released Step 4b predecessor and a released immutable Step 3 plan source and release. Plan hash and revision drift are rejected.
- `S-P2-01`: gate subject IDs now derive only from gate identity. `gate.ready` and `gate.approved` update one gate record, while the replaced event remains represented by the permitted conflict evidence.
- `Q-P1-01`: Python 3.11 remains unavailable in this environment. The exact unavailable command and result are recorded below. Python 3.12.3 validation was run instead.
- `Q-P1-02`: the complete `positive-workflow-events.json` fixture is materialized and graph-validated by the Notion simulator test.
- `Q-P2-01`: retry state queue entries retain immutable `first_failed_at`; retry and DLQ contracts require it and require `original_command_sha256`, computed from canonical command bytes. Terminal `failed_at` remains the final attempt time.
- `Q-P2-02`: one n8n matrix executes dispatch, wait, retry to DLQ, resume, and Step 3b for all ten neutral archetype tenant and project identities.

## Changed Artifacts

- `services/integrations/notion_simulator.py`
- `services/integrations/n8n_simulator.py`
- `tests/test_notion_simulator.py`
- `tests/test_n8n_simulator.py`
- `tests/contracts/test_integration_contracts_v2.py`
- `standards/integrations/n8n-simulation-state.schema.json`
- `standards/integrations/n8n-retry-entry.schema.json`
- `standards/integrations/n8n-dlq-entry.schema.json`
- `tests/fixtures/integrations/v2/positive-n8n-simulation-state.json`
- `tests/fixtures/integrations/v2/positive-n8n-retry-entry.json`
- `tests/fixtures/integrations/v2/positive-n8n-dlq-entry.json`

No `services/integrations/__init__.py` change was required.

## Contract Version Impact

The existing V2 schema IDs and `schema_version: 2.0.0` remain unchanged. The closed V2 state contract now requires tenant and project identity. Closed retry and DLQ contracts now require immutable first-failure and canonical original-command-hash provenance. V1 schemas and fixtures remain covered by the V2 contract compatibility test and pass unchanged.

## TDD And Validation Evidence

### RED

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_n8n_simulator.N8nSimulatorTests.test_rejects_cross_scope_wait_before_state_queueing tests.test_n8n_simulator.N8nSimulatorTests.test_rejects_forged_context_hash_before_dispatch tests.test_n8n_simulator.N8nSimulatorTests.test_rejects_forged_cross_tenant_predecessor_before_dispatch tests.test_n8n_simulator.N8nSimulatorTests.test_preserves_first_failure_timestamp_in_terminal_dlq tests.test_notion_simulator.NotionSimulatorTests.test_materializes_every_schema_valid_v2_event_and_conflict tests.test_notion_simulator.NotionSimulatorTests.test_projects_one_canonical_gate_with_prior_event_conflict_evidence tests.test_notion_simulator.NotionSimulatorTests.test_keeps_new_subjects_from_lower_revisions_and_audits_stale_subjects -v
```

Result: exit 1. Ran 7 tests with 5 failures and 2 errors. Failures demonstrated accepted cross-scope waits, forged all-zero context hashes, forged cross-tenant releases, terminal-time overwrite of `first_failed_at`, and duplicate gate records. Errors demonstrated the global Notion revision rollback rejection for the complete event fixture and lower-revision materialization case.

### GREEN Focused Stage C And V2 Contracts

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v
```

Result: exit 0 under Python 3.12.3. Ran 38 tests, `OK`.

The focused tests cover full V2 event materialization, conflict projection, deterministic shuffled materialization, one canonical ready-plus-approved gate, forged hashes, missing exact records, cross-tenant wait and release rejection, exact Step 3b Step 4b and Step 3 plan lineage, days 30/60/90 plus rejected day 120, retry first-failure timeline, all four technical-session decisions, no input mutation, no I/O static guards, V1 compatibility, and all ten n8n archetypes.

### Schema Meta-validation

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python -c "import json; from pathlib import Path; from jsonschema import Draft202012Validator; paths=sorted((Path('standards/integrations')).glob('*.schema.json')); [Draft202012Validator.check_schema(json.loads(path.read_text(encoding='utf-8'))) for path in paths]; print(f'meta_validated={len(paths)}')"
```

Result: exit 0. `meta_validated=12`.

### Host Python 3.11 Focused Suite

Discovery command:

```text
command -v python3.11
```

Result: exit 1 with no output. Python 3.11 is not installed.

Required focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python3.11 -m unittest tests.test_notion_simulator tests.test_n8n_simulator tests.contracts.test_integration_contracts_v2 -v
```

Result: exit 127. `/usr/bin/bash: line 1: python3.11: command not found`.

### OMO Python 3.12 Focused Suite

Interpreter command:

```text
python --version
```

Result: exit 0. `Python 3.12.3`.

The GREEN focused command above was run with this available OMO Python 3.12.3 interpreter and passed 38 tests.

### Full Suite

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py
```

Result: exit 1 under Python 3.12.3. Acceptance passed 7/7. Root unittest discovery ran 241 tests and reported one error in the pre-existing `tests.test_operator_error_routing.OperatorErrorRoutingTests.test_every_emitted_runtime_error_code_is_canonical_and_routed`: its AST helper passes a `None` return value to `ast.walk`. The failure is outside the allowed Stage C write boundary. The Stage C focused and V2 contract suite remains green.

### Pure API Probes

- Full Notion event fixture: `records=23,conflicts=83,gate_records=2`. The two gates are distinct GATE-1 and GATE-4A identities; ready plus approved remains one GATE-1 record in its focused regression.
- Valid n8n dispatch: `dispatches=1,session=fresh_required,state_scope=tenant-demo/project-demo`.

## Stage D Exclusion

Stage D was excluded. No API, Core, routing, prompt, output, workflow, UI, or Stage D artifact was changed. No network, provider, deployment, credential, external-service, or live-integration call was made.
