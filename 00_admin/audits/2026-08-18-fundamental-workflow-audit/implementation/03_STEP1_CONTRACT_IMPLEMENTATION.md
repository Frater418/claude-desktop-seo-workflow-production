# Step 1 Contract V2 Implementation

Autor: Raphael Rechberger

## Scope

Step 1 now produces one closed Draft 2020-12 canonical JSON topic inventory. The Markdown topic view is derived from this JSON and cannot be used as an independent source of truth.

The canonical source is ASCII JSON serialized with sorted keys and compact separators. Its SHA-256 is calculated over the exact serialized bytes. The inventory carries its artifact, run, project and deployment identities plus all source, competitor, existing URL and crawl evidence references.

## Inventory Requirements

- `schema_version` is `2.0.0`.
- The inventory contains 3 to 8 pillars.
- Every pillar contains 8 to 15 cluster candidates.
- Every candidate and intent remains a `hypothesis` until the later evidence workflow proves it.
- Every candidate requires content type, hypothesized intent, information-gain score from 1 to 5, conversational query patterns, GEO engine targets, regional scope and source evidence IDs.
- The contract has no fields for provider defaults, search volume or invented evidence.
- Gaps and decisions are separate, identified records with evidence references.
- `site_applicability.site_status` is explicit. `existing_site` requires crawl references. `non_existing_site` requires an explicit no-crawl decision and permits no crawl references.

## Preflight

`services.step1_preflight.validate_step1_preflight(bundle)` returns one structured result with `valid` and a consolidated `errors` list. It uses `jsonschema.Draft202012Validator`, `FormatChecker`, `referencing.Registry` and `Resource` to resolve versioned local contracts.

The preflight validates Project V2, the Step-1 run envelope, a distinct immutable Step-0 source artifact, Gate-0 release and approval, inventory source bytes, Step-1 artifact records, transition command, quality-gate records, evidence records and Screaming Frog snapshots. IDs must cover the current tenant, project, run and deployment. The current artifact record, run output hash and quality-gate hash must equal the SHA-256 over exact canonical inventory bytes. The current artifact must list the Step-0 artifact in `parent_artifact_ids`.

An explicitly declared `existing_site` requires a passed Screaming Frog snapshot with matching run, project and deployment, no reached URL limit, and a passed `qg-step1-crawl-snapshot` record. Missing or invalid evidence returns `ERROR_STEP1_CRAWL_EVIDENCE_INVALID`.

`quality_gate_run.schema.json` uses `quality_gate_run_id` values in the `qgr-*` namespace and identifies the registry gate through `quality_gate_id`, with `human_gate_id` in the `GATE-*` namespace. `approval-record.schema.json` and `run-envelope.schema.json` use `GATE-*` gate IDs. The preflight uses these actual namespaces. The runtime transition schema explicitly supports `submit_for_gate` and `complete`; submission requires `awaiting_gate`, while completion requires external approval, matching policy version, a passed `qgr-*` Gate-1 approval quality run, and an explicit evaluation timestamp within the approval window.

## Gate Lifecycle

Prompt 1 only submits an `awaiting_gate` run through `submit_for_gate`. It does not create a Gate-1 approval or request completion.

Completion requires an external `GATE-1` approval record. Its tenant, run, artifact ID, artifact SHA-256 and artifact revision must match the current inventory artifact. A changed hash or revision invalidates approval and returns `ERROR_GATE1_APPROVAL_INVALID`.

## Operator Errors

- `ERROR_STEP1_INVENTORY_NOT_CANONICAL`: serialize the JSON canonically before hashing.
- `ERROR_STEP1_ARTIFACT_HASH_MISMATCH`: rebuild all artifact and run bindings from exact inventory bytes.
- `ERROR_STEP1_DEPLOYMENT_INVALID`: select a deployment declared by Project V2.
- `ERROR_STEP1_CRAWL_EVIDENCE_INVALID`: run and retain the required Screaming Frog evidence.
- `ERROR_GATE1_APPROVAL_INVALID`: obtain a new external approval for the current artifact revision and SHA-256.
- `ERROR_GATE1_APPROVAL_STALE`: the approval hash or revision no longer binds the current artifact.

## Verification Environment

The requested `python -m pytest -q tests/test_step1_contract_v2.py` command remains unavailable in this container because the active Python reports `No module named pytest`. No dependency was changed.
