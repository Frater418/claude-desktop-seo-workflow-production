# Sprint 4 Stage A Integration V2 Review Fix

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Stage A review fixes only.

## Implemented Contract Fixes

- Added the closed Draft 2020-12 Notion record-map V2 contract at the stable URI `https://heartweb.example/schema/integrations/notion-record-v2.schema.json`.
- The record map is keyed by stable ID. Its 17 prefix-specific patterns require the matching typed `record_type`; record values do not contain `record_id` and require title, projected status, source event, source revision, and unique typed relations.
- Projection and snapshot records now both reference the same stable shared contract through a local `referencing.Registry`. Projection remains simulated or live exclusive. Snapshot remains simulated-only, Transition Service-authoritative, and non-atomic.
- Fixed retry delivery to three attempts: simulation policy and retry maximum are 3, retry attempts are 1 or 2, and DLQ maximum and attempt are both 3. Retry and DLQ require step and expected revision. DLQ retains command, delivery, correlation, idempotency, tenant, project, run, failure, first-failure, and final-failure provenance.
- Added keyed positive records and named negative fixtures for arrays, unknown keys, key/type mismatches, source revision, retry bounds, and DLQ provenance. Duplicate record IDs are structurally impossible in the map and duplicate semantic fixture input is rejected by the focused test without duplicate JSON keys.

## Runtime

`python --version`

Observed: `Python 3.12.3`

## RED Evidence

Command run before schema or fixture changes:

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
```

Observed: 14 tests ran, 3 failures, exit code 1.

- `test_n8n_retry_and_dlq_entries_require_bounded_provenance` failed because simulation state accepted `retry_policy.max_attempts: 5`.
- `test_projection_uses_a_shared_stable_record_map_contract` failed because projection records had no shared stable-URI reference.
- `test_snapshot_rejects_array_and_untyped_records` failed because an array snapshot validated.

## GREEN Evidence

Focused V2 contract command:

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
```

Observed: 14 tests ran, all passed, exit code 0.

Modified V2-schema meta-validation command:

```text
python -c "import json; from pathlib import Path; from jsonschema import Draft202012Validator; paths = ('notion-record-v2.schema.json', 'notion-projection-v2.schema.json', 'notion-snapshot.schema.json', 'n8n-simulation-state.schema.json', 'n8n-retry-entry.schema.json', 'n8n-dlq-entry.schema.json'); [Draft202012Validator.check_schema(json.loads((Path('standards/integrations') / path).read_text(encoding='utf-8'))) for path in paths]; print(f'Meta-validated {len(paths)} modified V2 schemas')"
```

Observed: `Meta-validated 6 modified V2 schemas`.

Full-suite command:

```text
python tests/run_full_suite.py
```

Observed: 229 tests passed: acceptance 7, root unittest discovery 171, contract unittest discovery 51. Exit code 0.

## Scope Confirmation

- No V1 schema, fixture, service, prompt, state, decision, plan, requirements, Docker, or report 01 through 06 was modified.
- The V2 archetype matrix remains 10 client-neutral archetypes. The 30/60/90 cadence, simulated/live separation, and absence of AHD or live customer constants remain covered.
