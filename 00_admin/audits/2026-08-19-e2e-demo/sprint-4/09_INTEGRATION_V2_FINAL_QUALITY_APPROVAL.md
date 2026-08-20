# Sprint 4 Stage A Integration V2 Final Quality Approval

Date: 2026-08-19
Author: Raphael Rechberger
Scope: Independent read-only final quality re-review after report 07. This report reviews Stage A contracts, fixtures, tests, governing contracts, and the current working tree. It does not start Stage A2 or Stage B.

## Terminal Decision

`REQUEST_CHANGES`

Stage A V2 passes its focused suite, the full configured suite, schema meta-validation, and the majority of adversarial boundary probes. Approval is blocked by three P1 false greens in the shared Notion record-map relation and identity model. A schema-valid projection or snapshot can contain a relation to a nonexistent record, a relation whose declared type conflicts with its target key type, or two records with duplicate semantic content under distinct stable keys.

## Governing Baseline

- DEC-0018 requires the local Core and Transition Service to retain protected workflow status, hashes, revisions, and gate decisions. n8n is transport and orchestration. Notion is an operational projection.
- The Stage A build plan requires closed Draft 2020-12 V2 contracts, typed closed relations for all 17 required operational record types, simulated and live exclusivity, V1 compatibility, 30/60/90 checkpoints, ten client-neutral archetypes, and no live credentials, database IDs, or AHD-specific production constants.
- Reports 01 through 04 were used only as navigation. Claims from reports 05 through 07 were revalidated against the current schemas, fixtures, tests, workflow graph, runtime transition command, operator contract, domain contract, and integration operating models.

## Findings

### P0

No P0 findings.

### P1

1. `notion-record-v2.schema.json` accepts unresolved record relations.
   - Evidence: the relation contract at [`notion-record-v2.schema.json`](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/integrations/notion-record-v2.schema.json:11) validates only the target key grammar. An in-memory mutation changed the customer relation target to the well-formed but absent `project-nonexistent`; the V2 projection validator accepted it.
   - Impact: a schema-valid Notion projection or snapshot can contain a dangling edge. This defeats the required typed operational record graph and leaves materialization behavior undefined.

2. `notion-record-v2.schema.json` does not bind `relation_type` to the target record-key type.
   - Evidence: the same relation contract permits `{"relation_type": "project", "target_record_id": "customer-00000001"}`. The direct V2 projection mutation validated successfully.
   - Impact: a relation declared as a project relation can point to a customer, or any other valid record-key family. The result is not a typed relation even though the schema presents it as one.

3. The V2 record map does not reject duplicate semantic records under distinct stable keys.
   - Evidence: object keys prevent duplicate literal keys, but the record value has no semantic identity discriminator beyond its map key. An in-memory mutation copied the complete `project-00000001` value, including title, status, source event, source revision, and relations, to `project-duplicate01`; the projection validator accepted it.
   - Impact: the map preserves syntactic key uniqueness but cannot protect a materializer from representing the same projected entity twice under different IDs. The focused test's duplicate check constructs a Python list and asserts that its duplicate keys are unequal. It does not submit a duplicate semantic projection to the validator.

### P2

No P2 findings.

### P3

No P3 findings.

## Confirmed Quality Evidence

- All 28 V2 fixtures were loaded. All positive fixtures validated through a `referencing.Registry` containing the nine V2 schemas. The external V2 record-map references in projection and snapshot resolved successfully. Validating the projection without that registry raised `Unresolvable`, so an absent registry does not produce a false green.
- V2 correctly rejected malformed map keys, top-level key and `record_type` mismatches, unknown record types, array snapshots, missing record source revision, direct projected canonical-state fields, Notion proposal direct writes, unknown event types, and simulated-to-live masquerading.
- Retry policy and retry entries reject maximum attempts of five. Retry entry attempt three is rejected. DLQ attempt one is rejected. DLQ entries missing `step_id` or `expected_revision` are rejected. Simulation checkpoint days other than exactly `[30, 60, 90]` are rejected.
- The V2 event contract contains the 13 V1 event types plus the eight required V2 events. The event catalog has exact event and purpose parity. The V2 record map contains all 17 required record types.
- V1 event, Notion projection, and n8n command fixtures remain valid against their V1 schemas. The V2 archetype matrix references exactly ten client-neutral domain fixtures. The workflow graph retains the initial route `0 -> 1 -> 1b -> 1c -> 2 -> 3 -> 4a -> 4b` and preserves Step 3b as the repeatable 30/60/90 post-publication sideflow.
- V2 simulation schemas and positive fixtures remain simulated-only. Projection authority remains `transition_service` and `atomic_state_writer` remains false. n8n command vocabulary excludes approval and completion.
- All reviewed integration, workflow, runtime, operator, and domain schemas passed `Draft202012Validator.check_schema`. The Stage A Python test file parsed under Python 3.11 grammar mode. Native `python3.11` is not installed, so execution occurred under Python 3.12.3 only.
- The V2 schemas, fixtures, and V2 test contain no forbidden En-Dash or Em-Dash characters. No V2 schema or fixture contains AHD or a live client constant. The V2 test contains only its intentional negative assertions for those strings.

## Commands And Probe Results

```text
python -m unittest tests.contracts.test_integration_contracts_v2 -v
Result: 14 tests passed.

python tests/run_full_suite.py
Result: 229 tests passed: 7 acceptance, 171 root unittest discovery, 51 contract unittest discovery.

python - <<'PY' ... Draft202012Validator and referencing.Registry V2 fixture and mutation probe ... PY
Result: 20 expected rejections or validations passed. Three false greens were accepted: unresolved relation target, relation type to target-key mismatch, and duplicate semantic record under a distinct key.

python - <<'PY' ... Draft202012Validator.check_schema across integration, workflow, runtime, operator, and domain schemas ... PY
Result: all reviewed schemas meta-validated.

python3.11 --version
Result: command not found.

python - <<'PY' ... ast.parse(feature_version=(3, 11)) for tests/contracts/test_integration_contracts_v2.py ... PY
Result: Python 3.11 grammar parse passed under Python 3.12.3.

python - <<'PY' ... scan V2 schemas, fixtures, and test for En-Dash, Em-Dash, AHD, and client constants ... PY
Result: no forbidden dash characters. No schema or fixture AHD or client constants. The test contains intentional negative assertions only.

GIT_MASTER=1 git status --short
GIT_MASTER=1 git diff --stat
GIT_MASTER=1 git diff --check
GIT_MASTER=1 git diff --no-ext-diff -- standards/integrations tests/fixtures/integrations/v2 tests/contracts/test_integration_contracts_v2.py 00_admin/audits/2026-08-19-e2e-demo/sprint-4
Result: current tracked and untracked work inspected. No diff whitespace error. The V2 Stage A artifacts are untracked and were inspected directly from the current filesystem.
```

## Scope And Worktree Notes

- No source, schema, fixture, test, state, decision, plan, requirement, Docker, configuration, provider, network, deployment, commit, or push action was performed by this review.
- The worktree already contains broad tracked and untracked Sprint material outside this report. This review does not attribute or alter it.
- Required remediation before approval: enforce relation target existence, bind each relation type to its target key family, and reject duplicate semantic records with a defined semantic identity invariant. Add regression tests that demonstrate each mutation fails.
