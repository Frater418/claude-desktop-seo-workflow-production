# Sprint 4 Stage A2 Package A2.1 Ultimate Quality Approval

Date: 2026-08-20
Author: Raphael Rechberger
Reviewer: Reviewer B, independent read-only quality audit
Scope: Final Package A2.1 approval after report 27. No A2.2 work is approved by this report.

## Final Verdict

REQUEST_CHANGES

The focused 19-test suite, registry byte bindings, all historical mutation groups, both project-context kind swaps, all six selected-source trust/lifecycle probes, deterministic-error probe, and guarded no-I/O probe pass. The package is nevertheless not approvable: host and local OMO Draft 2020-12 meta-validation both reject `standards/runtime/context-package.schema.json`. A schema that declares Draft 2020-12 but is not a valid Draft 2020-12 schema is a P0 contract-boundary failure and creates a false green because the focused tests validate instances without first validating the schema itself.

## Required Inputs Read

Read before assessment: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; and every Sprint 4 A2 report from 15 through 27. Independently inspected the six A2.1 schemas, official registry, validator, fixtures, and both focused test modules.

The relevant implementation path is `RuntimeContractValidator.validate()` in `services/runtime_contracts/llm_records.py`: it runs a Draft 2020-12 instance validator first, then pure local invariant checks. The validator receives schemas and registry data by injection. Its source contains no file, environment, socket, provider, routing, dispatch, or state-mutation call path.

## Evidence And Result Matrix

| Check | Command or probe | Result |
| --- | --- | --- |
| Focused A2.1 gate | `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v` | PASS: 19 tests, 0.476s. |
| Historical mutation groups | Eight named invariant test methods covering reports 19, 20, 22, and 24 | PASS: 8 tests, 0.271s. Missing Project V2, stale source, wrong prompt/output, duplicate/noncontiguous ordering, registry drift, policy mismatch, result mismatch, and session mismatch reject. |
| Official prompt/output binding | Local SHA-256 and metadata inspection | PASS: 9 active prompts and 12 output bindings. Step 0 is 1.5.0, all others are 2.0.0. |
| Selected-source policy | Six in-memory probes | PASS: selected Step 0 intake with `operator_asserted`, `not_applicable`, or `untrusted` rejects at `/sources/0/trust_level`; selected Step 1 Project V2 with `active`, `rejected`, or `historical` rejects at `/sources/0/source_status`. |
| Nonselected-source policy | Focused invariant test | PASS: `operator_asserted` plus `active` and `not_applicable` plus `rejected` remain valid only on a nonselected predecessor descriptor. |
| Project-context kind swaps | Focused invariant test | PASS: Step 0 intake to official prompt and Step 1 Project V2 to released predecessor reject deterministically. |
| Deterministic errors | Repeated invalid result validation plus frozen-record mutation attempt | PASS: equal ordered errors for token total and reverse timestamp; mutation raises `FrozenInstanceError`. |
| No I/O or fallback | Guarded `open`, `getenv`, and `socket.socket` after dependency injection | PASS: five valid record kinds remain valid. Schema errors return before semantic validation; no fallback path was observed. |
| Client neutrality | Focused surface test plus registry/fixture inspection | PASS: ASCII fixtures and registry, with no AHD/client constant, credential, endpoint, raw handle, or forbidden dash. |
| A2.2 exclusions | Source inspection and `services/context_builder/**` inventory | PASS: no context builder exists. No resolver, source-byte loading, canonical hashing, graph/release lookup, cache policy, routing, API, event, integration, UI, provider, dispatch, or state mutation was introduced. |
| Host Draft 2020-12 schema validation | `Draft202012Validator.check_schema(...)` for all six schemas | FAIL: `context-package.schema.json` is invalid. |
| Local OMO Draft 2020-12 schema validation | Same command through local `docker exec opencode-omo` | FAIL: same invalid schema and same diagnostic. |

## Findings

### P0: `context-package.schema.json` is not a valid Draft 2020-12 schema

File: `standards/runtime/context-package.schema.json`

Both host and local OMO meta-validation fail with:

```text
jsonschema.exceptions.SchemaError: ['source_kind'] is not of type 'object', 'boolean'
On schema['$defs']['source']['allOf'][2]['if']['properties']['required']
```

The third conditional in `$defs.source.allOf` places `required: ["source_kind"]` inside `properties`. Under Draft 2020-12, every member of `properties` must itself be a schema, but this member is an array. The intended `required` keyword must be a sibling of `properties`, not a property entry.

This invalidates the package's claimed Draft 2020-12 contract surface. The focused tests are falsely green because they create `Draft202012Validator(schema)` for instance validation but do not call `Draft202012Validator.check_schema(schema)` first. That permits this malformed keyword location to escape the normal A2.1 gate.

Required correction: repair the conditional using valid Draft 2020-12 syntax, add six-schema meta-validation to the focused automated gate, then rerun the complete matrix in this report. Do not begin A2.2 until the meta-validation is green on the corrected schema.

### P1

None after the selected-source and lifecycle probes. The policy is correctly limited to the descriptor selected by `project_context`; nonselected descriptor policy values are not incorrectly treated as project authority.

### P2

None identified in the A2.1 local boundary after the executed mutation matrix. Cross-record source resolution, byte verification, canonical hash construction, freshness, graph/release checks, stored-record projection comparison, idempotency comparison, and cache eligibility remain deliberate A2.2 responsibilities.

### P3: Windows execution is unavailable locally

`python --version` reports Python 3.12.3. `python3.11` is unavailable. No `powershell` or `pwsh` executable is available, so a native Windows validation command could not run. The locally available `opencode-omo` container was used for the OMO-compatible schema command and reproduced the same P0 failure. This platform evidence gap is not the basis of the verdict.

## Scope And Exclusion Conclusion

The inspected code remains a pure A2.1 schema-plus-local-invariant boundary and does not perform A2.2 work. Its valid-record behavior correctly preserves client neutrality, selected-versus-nonselected source policy, deterministic failures, and no-I/O/no-fallback behavior. The invalid Draft 2020-12 schema prevents approval despite those passing checks. The only permitted repository mutation made during this audit is this report.
