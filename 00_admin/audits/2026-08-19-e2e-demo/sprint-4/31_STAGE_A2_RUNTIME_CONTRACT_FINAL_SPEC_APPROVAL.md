# Sprint 4 Stage A2 Package A2.1 Final Specification Re-Approval

Date: 2026-08-20
Author: Raphael Rechberger
Reviewer: Reviewer A, new independent read-only terminal audit
Scope: Package A2.1 only, after report 30. This report is the sole file created by this audit.

## Final Verdict

REQUEST_CHANGES

Report 30's narrow Draft 2020-12 syntax correction is present and the six current schemas independently pass `Draft202012Validator.check_schema()` on both host and local OMO. The 19-test focused suite, all prior mutation families, source-policy probes, project-context kind swaps, registry hashes, and guarded no-I/O probes pass. However, the claimed meta-schema regression does not run before any instance-only assertion in the focused suite: `setUpClass()` constructs six instance validators before the regression, and unittest runs `test_schemas_are_unique_closed_draft_2020_12_contracts` seventh. This leaves the suite vulnerable to the exact false-green ordering that reports 28 and 29 required it to prevent. A2.1 therefore cannot receive final approval until meta-validation is a precondition of all instance validation.

## Inputs And Scope Evidence

Read before assessment: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; reports 19, 20, 22, 25, 28, 29, and 30; all six runtime schemas; the official-prompt registry schema and data; all A2.1 fixtures; both focused test modules; the live validator; the nine prompts; the workflow graph; and all registered output contracts.

The evaluated call path is `LlmRuntimeContractTests` and `LlmRuntimeInvariantTests` to `RuntimeContractValidator.validate()` to `Draft202012Validator(...).iter_errors()` and then pure record-local checks in `services/runtime_contracts/llm_records.py`. The validator receives loaded schemas and registry data by injection. No context builder, resolver, source-byte reader, canonical hash builder, graph or release lookup, cache-policy evaluator, routing, API, event, integration, UI, provider, dispatch, or workflow-state mutation was found. Those remain strict A2.2 or later exclusions.

The repository index does not contain the A2.1 files. `git status --short` reports the runtime schemas, registry, validator, fixtures, tests, and reports 15 through 30 as untracked. Consequently, no historical Git patch exists from which to isolate report 30. The exact live correction was nevertheless inspected: `standards/runtime/context-package.schema.json` places `required: ["source_kind"]` as an `if` sibling to `properties` in `$defs.source.allOf[2]`, matching report 30. The report-30 claim is accurate for that narrow syntax fix, but its claimed test ordering is not.

## Verification Matrix

| Check | Exact command or evidence | Result |
| --- | --- | --- |
| Focused current-runtime suite, host | `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v` | PASS: 19 tests in 0.569s. |
| Focused current-runtime suite, local OMO | `docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo sh -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.contracts.test_llm_runtime_contracts tests.test_llm_runtime_invariants -v'` | PASS: 19 tests in 0.568s. |
| Host six-schema Draft 2020-12 meta-validation | `PYTHONDONTWRITEBYTECODE=1 python -c "import json,pathlib; from jsonschema import Draft202012Validator; names=('logical-project-session','official-prompt-registry','worker-profile','context-package','llm-run-request','llm-run-result'); [Draft202012Validator.check_schema(json.loads((pathlib.Path('standards/runtime')/(name+'.schema.json')).read_text(encoding='utf-8'))) for name in names]; print('HOST_META_VALIDATION_PASS',len(names),'schemas')"` | PASS: `HOST_META_VALIDATION_PASS 6 schemas`. |
| Local OMO six-schema Draft 2020-12 meta-validation | Same command through `docker exec ... opencode-omo` | PASS: `OMO_META_VALIDATION_PASS 6 schemas`. |
| Report-30 regression placement | `tests/contracts/test_llm_runtime_contracts.py`: `setUpClass` lines 75-84 creates `Draft202012Validator` instances; `test_schemas_are_unique_closed_draft_2020_12_contracts` lines 102-110 calls `check_schema`. Verbose suite order executes the latter after six other contract tests. | FAIL: meta-validation is not a suite-wide precondition. |
| Reports 19 and 20 mutation families | Focused invariant tests for missing Project V2, duplicate intake, source ownership, stale source, wrong prompt/output, revision equality, ordering, logical-reference grammar, registry drift, worker/request mismatch, result mismatch, and session mismatch. | PASS: all named tests passed on host and OMO. |
| Report 22 project-context kind swaps | `test_context_rejects_project_context_source_kind_swaps` tests Step 0 intake to official prompt and Step 1 Project V2 to released predecessor. | PASS: both reject deterministically. |
| Report 25 selected-source trust and lifecycle probes | `test_context_rejects_selected_project_source_policy_values` tests three Step 0 trust values and three Step 1 Project V2 lifecycle values. | PASS: all six reject at the selected descriptor. |
| Nonselected-source policy | `test_context_accepts_nonselected_source_policy_values`. | PASS: `operator_asserted/active` and `not_applicable/rejected` remain valid only for a nonselected predecessor descriptor. |
| Prompt and output bytes | Host SHA-256 and prompt-metadata script against active registry entries. | PASS: `HOST_PROMPT_OUTPUT_HASH_PASS 9 prompts 12 output-bindings`. Step 0 is `1.5.0`; all others are `2.0.0`. |
| Guarded no-I/O, host | Inject schemas and registry, then replace `builtins.open`, `os.getenv`, and `socket.socket` with raising guards before validating six positive record kinds. | PASS: `HOST_NO_IO_PASS 6 record-kinds`. |
| Guarded no-I/O, local OMO | Same injected dependency and guarded validation probe through `docker exec ... opencode-omo`. | PASS: `OMO_NO_IO_PASS 6 record-kinds`. |

## A2.1 Requirement And Closure Assessment

| Requirement or prior report | Status | Evidence |
| --- | --- | --- |
| Six required schemas, registry schema/data, fixtures, and focused tests | Verified except regression ordering | All artifacts exist and direct host/OMO meta-validation passes, but the automated regression is late. |
| Closed Draft 2020-12 schemas and unique IDs | Verified directly | Six direct `check_schema()` calls pass on host and OMO. The focused closure and ID test also passes. |
| Nine official prompt entries, exact bytes, versions, and multi-output contracts | Verified | Nine active entries and 12 output bindings hash-match live files. |
| Logical session, worker profile, request, and result local contracts | Verified locally | Focused records and all relevant report 19 and 20 mutations pass or reject as required. |
| Context source identity, ordering, binding, trust, lifecycle, and revision rules | Verified locally | Historical mutation groups, both kind swaps, selected and nonselected policy tests, and six selected-source probes pass. |
| Report 19 closure | Closed behaviorally | All listed context, worker, request, result, session, and registry mutations reject. The meta-schema regression-ordering defect is separate. |
| Report 20 closure | Closed behaviorally | Source ownership, cardinality, ordering, reference grammar, registry, result, and local profile/cache mutations reject. |
| Report 22 closure | Closed | Both project-context kind swaps reject. |
| Report 25 closure | Closed | All six selected-source trust and lifecycle violations reject. |
| Reports 28 and 29 schema-invalid finding | Syntax correction closed, regression closure incomplete | Direct host and OMO meta-validation pass, but the focused gate does not run that check before instance validation. |

## Findings

### P0

None.

### P1: Meta-schema validation is not a precondition to instance validation

Files: `tests/contracts/test_llm_runtime_contracts.py`, `services/runtime_contracts/llm_records.py`

The regression introduced after reports 28 and 29 is located only in `test_schemas_are_unique_closed_draft_2020_12_contracts`. In contrast, `setUpClass()` first constructs `Draft202012Validator` instances for every schema, and the unittest sort order runs the meta-schema test after instance-oriented contract tests. The host and OMO suites pass only because the currently corrected schema happens to be valid. A future malformed schema could again be instantiated and exercised by earlier tests without a precondition check, recreating the report-28 and report-29 instance-only false-green risk.

Required correction: execute `Draft202012Validator.check_schema()` for all six schemas before constructing any `Draft202012Validator` instance or executing any fixture assertion, for example as the first action in `setUpClass()`. Keep the existing explicit regression test if desired, then rerun the full matrix in this report.

### P2

None.

### P3

Python 3.11 and native Windows execution are unavailable locally. `python --version` is `Python 3.12.3`; `python3.11 --version` and `pwsh --version` return command-not-found. Local OMO was available and independently passed the focused suite, schema meta-validation, and no-I/O probe. This limitation is not the basis for the verdict.

## Exclusions And Audit Integrity

No network, provider, crawl, deployment, browser, API, event, integration, workflow-state, git-write, commit, push, or source/test/schema/configuration modification was performed. No A2.2 work was added, repaired, assessed as delivered, or approved. The only audit mutation is this report.
