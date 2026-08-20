# Sprint 4 Stage A2 Package A2.1 Runtime Contract Specification Review

Date: 2026-08-20
Author: Raphael Rechberger
Scope: Independent, read-only approval review of Sprint 4 Stage A2 Package A2.1 only.
Decision: REQUEST_CHANGES

## Decision Summary

Package A2.1 has the intended six Draft 2020-12 schemas, an official nine-step prompt registry, neutral fixtures, and a focused green suite. The exact runtime-contract gate is not approvable because materially invalid Context Package, worker/request, and result records validate successfully. These gaps violate the controller A2.1 TDD gate and DEC-0019 fail-fast requirements before the deferred A2.2 builder can be trusted as a compensating control.

## Review Evidence

Reviewed: `AGENTS.md`; `DEC-0019` in `00_admin/DECISIONS.md`; reports `15_STAGE_A2_RUNTIME_CONTRACT_RESEARCH.md` through `18_STAGE_A2_RUNTIME_CONTRACT_IMPLEMENTATION.md`; controller plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; all six new runtime schemas; registry schema and registry; all eleven A2.1 fixtures; `tests/contracts/test_llm_runtime_contracts.py`; all nine official prompts; `standards/workflow/workflow-graph.json`; `standards/manifest.schema.json`; all eleven `standards/outputs/*.schema.json`; and the current tracked diff plus all untracked A2.1 files.

The current diff is additive for A2.1 contracts, fixtures, tests, registry, and reports. No Stage B, provider, API, event, simulator, UI, routing, workflow-graph, or prompt implementation change was found in the A2.1 artifacts.

Validation commands and observed results:

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py
# Ran 7 tests in 0.200s
# OK

python -c "import json,pathlib; from jsonschema import Draft202012Validator; files=sorted(pathlib.Path('standards/runtime').glob('*.schema.json')); [Draft202012Validator.check_schema(json.loads(p.read_text())) for p in files]; print('META_VALIDATION_PASS',len(files),'schemas')"
# META_VALIDATION_PASS 16 schemas

python -c "...verify all active registry entries against prompt metadata and prompt/output SHA-256 bytes..."
# PROMPT_METADATA_HASH_PASS 9 prompts 12 output-bindings
```

The live registry contains exactly the required active entries `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`. Live prompt metadata versions and prompt bytes match: Step 0 is `1.5.0`; every other step is `2.0.0`. All 12 registered output bindings hash-match their source files, including both bindings for 1c, 4a, and 4b. The focused test also confirms the six runtime schema IDs are unique, every declared object boundary is closed, and shipped registry/fixtures are ASCII and do not contain AHD/client constants, credentials, endpoints, or raw session handles.

## Findings

### P1: Context Package accepts invalid mandatory source, lifecycle, prompt/output, ordering, and revision bindings

`standards/runtime/context-package.schema.json` validates the structural presence of several fields but does not enforce the exact record invariants required by DEC-0019 and the controller plan. The A2.1 tests in `tests/contracts/test_llm_runtime_contracts.py` do not cover these mutations.

In-memory Draft 2020-12 adversarial mutations of the positive fixtures were accepted:

```text
ACCEPTED_INVALID next step accepts no project-v2 source descriptor
ACCEPTED_INVALID operational context accepts superseded project source
ACCEPTED_INVALID revision accepts expected revision equal rejected revision
ACCEPTED_INVALID context accepts wrong prompt id for step
ACCEPTED_INVALID context accepts wrong output contract for step
ACCEPTED_INVALID context accepts duplicate include_order
ACCEPTED_INVALID context accepts noncontiguous include_order
```

Relevant requirements are explicit: Step 0 must bind intake while Steps 1 through 4b require released Project V2, all output contracts must bind exactly, stale/superseded context must fail before dispatch, source order must be deterministic and contiguous, and a revision must produce a new revision. See `00_admin/DECISIONS.md` DEC-0019, `17_STAGE_A2_IMPLEMENTATION_PLAN.md` sections "Step 0 Project Source", "Multiple Output Contracts", and "Semantic Validation", plus `context-package.schema.json` lines 8-65.

Required correction: make these invariants rejectable at the A2.1 runtime-contract validation boundary and add focused negative tests. A deferred A2.2 cross-record validator may own external record lookup, but A2.1 must not present structurally valid invalid records as compliant or leave locally representable equality, ordering, and conditional requirements untested.

### P1: Worker, request, and result contracts do not enforce core policy and result conditionals

The schemas accept several violations of requirements explicitly listed in the A2.1 controller TDD gate:

```text
ACCEPTED_INVALID worker accepts default model outside allow-list
ACCEPTED_INVALID request accepts input hash unequal package hash
ACCEPTED_INVALID cache hint accepts provider mismatch
ACCEPTED_INVALID success accepts output revision unequal target
ACCEPTED_INVALID result accepts invalid token arithmetic
ACCEPTED_INVALID result accepts finished timestamp before start
```

These are contrary to `17_STAGE_A2_IMPLEMENTATION_PLAN.md` lines 94-116 and 168-203, and to `15_STAGE_A2_RUNTIME_CONTRACT_RESEARCH.md` lines 159-164, 234-245, and 267-277. The relevant incomplete contracts are `worker-profile.schema.json` line 8, `llm-run-request.schema.json` lines 7-12, and `llm-run-result.schema.json` lines 7-8. Current tests only test cache prohibition for fresh modes and success versus failure output presence. They do not test default-model membership, request input-hash equality, cache-provider equality, result target revision, token arithmetic, or timestamp ordering.

Required correction: encode or validate these exact invariants in the approved A2.1 validation surface and add negative tests that prove rejection. Preserve A2.2 ownership only for external-record resolution and stateful cache comparison, not for these directly represented contract relationships.

### P2: Logical-session and registry schemas permit drift that the runtime schema itself cannot reject

The logical-session schema does not relate `binding_mode` to `project_source`: an intake-mode session whose logical reference points to Project V2 was accepted. This undermines the Step 0 intake versus Project V2 distinction in `17_STAGE_A2_IMPLEMENTATION_PLAN.md` lines 22-29 and `logical-project-session.schema.json` lines 13-25.

The registry schema accepts a duplicate active entry in memory. The live registry is correct, and `test_official_registry_matches_current_prompts_outputs_and_workflow_steps` would catch an extra active entry through its active-entry count. However, `official-prompt-registry.schema.json` lines 6-12 has no exact cardinality or per-step uniqueness rule, so schema-only registry validation accepts this drift. Its schema correctly rejects an entry whose entire `output_contracts` array is removed, and the focused test correctly catches a missing or wrong live output binding, including multi-output steps.

Required correction: add direct conditional coverage for session binding mode and explicit registry uniqueness/cardinality validation with adversarial registry tests. If JSON Schema alone cannot express the unique-by-step rule, the registry validator must be part of the A2.1 contract gate and tested as such.

## Confirmed Compliant Areas

- Six required schemas exist with the required unique stable runtime IDs, Draft 2020-12 meta-schema URI, and closed declared object boundaries.
- The current registry has all nine official prompt entries, exact current metadata versions and byte hashes, and all required output-contract bindings. The 1c, 4a, and 4b multi-output arrays are present in the registry and in the corresponding positive fixtures.
- Request schemas forbid raw technical-session fields by closure and enforce fresh/no-cache representation for initial, next-step, and revision modes. Result schemas enforce success requires output and no error, while failed/cancelled require error and no output.
- Shipped A2.1 fixtures are synthetic, ASCII, and client-neutral. No raw provider handle, credential, endpoint, or authority field is present in the reviewed positive records.

## Test Environment Limitations

None affected these findings. The host Python environment ran the focused suite and Draft 2020-12 validation successfully. The reported implementation limitation that Python 3.11 was unavailable is a compatibility coverage gap, not the cause of the confirmed schema-valid invalid records above.

## Approval Condition

Do not approve A2.1 or begin A2.2 until the P1 findings are corrected and focused adversarial tests prove rejection of the listed invalid records. Re-run the focused contract suite, schema meta-validation, live prompt/output metadata and SHA-256 verification, and the same mutation matrix after correction.
