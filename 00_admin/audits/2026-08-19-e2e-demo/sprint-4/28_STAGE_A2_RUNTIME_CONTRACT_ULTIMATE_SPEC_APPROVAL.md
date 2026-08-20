# Sprint 4 Stage A2 Package A2.1 Ultimate Specification Approval

Date: 2026-08-20
Reviewer: Reviewer A, independent read-only approval audit
Scope: Package A2.1 runtime contracts and official registries only, after report 27.

## Final Verdict

REQUEST_CHANGES

The local schema-first validator and its 19 focused tests reject all rerun historical mutation families, both project-context kind swaps, and all six selected-project-source trust and lifecycle probes. However, the required `context-package.schema.json` is not a valid JSON Schema Draft 2020-12 schema. Both host and local OMO `Draft202012Validator.check_schema()` execution fail at the same malformed conditional. A2.1 cannot be approved while one of its six claimed Draft 2020-12 contracts fails its own meta-schema validation.

## Scope And Evidence

This audit read `AGENTS.md`, DEC-0019 in `00_admin/DECISIONS.md`, plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`, and every Sprint 4 report from 15 through 27 before assessment. It inspected these live A2.1 files:

- `standards/runtime/logical-project-session.schema.json`
- `standards/runtime/official-prompt-registry.schema.json`
- `standards/runtime/official-prompt-registry.json`
- `standards/runtime/worker-profile.schema.json`
- `standards/runtime/context-package.schema.json`
- `standards/runtime/llm-run-request.schema.json`
- `standards/runtime/llm-run-result.schema.json`
- `services/runtime_contracts/llm_records.py`
- `tests/contracts/test_llm_runtime_contracts.py`
- `tests/test_llm_runtime_invariants.py`
- `tests/fixtures/context_builder/`

The validator call path is `RuntimeContractValidator.validate()` to Draft 2020-12 validation and then record-local invariant validation. The inspected A2.1 surface has no builder, resolver, source-byte lookup, canonical hash construction, graph or release lookup, cache eligibility policy, routing, dispatch, API, event, integration, UI, provider, or workflow-state mutation implementation. No A2.2 scope violation was found.

## Validation Matrix

| Check | Command or probe | Result |
| --- | --- | --- |
| Focused A2.1 gate | `python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v` | PASS: 19 tests in 0.476s. |
| Local OMO focused gate | `docker exec -w /workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow opencode-omo python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v` | PASS: 19 tests in 0.506s. |
| Host per-schema Draft 2020-12 validation | `Draft202012Validator.check_schema()` for the six A2.1 schemas | FAIL: five schemas valid; `context-package` raises `SchemaError`. |
| OMO Draft 2020-12 validation | Same six-schema `check_schema()` command in `opencode-omo` | FAIL: same `context-package` `SchemaError`. |
| Prompt and output cryptographic registry check | Local SHA-256 and metadata comparison against all active entries | PASS: 9 prompts and 12 output bindings. Step 0 is `1.5.0`; all other prompts are `2.0.0`. |
| Prior mutation families | Nine focused invariant mutation groups | PASS: 9 tests in 0.264s. |
| Project-context kind swaps | In-memory Step 0 intake to official-prompt and Step 1+ Project V2 to released-predecessor substitutions | PASS: both reject with `LLM_RUNTIME_CONTEXT_INVALID` at `/project_context/source_id`. |
| Selected-source trust and lifecycle probes | Step 0 intake values `operator_asserted`, `not_applicable`, `untrusted`; Step 1 Project V2 values `active`, `rejected`, `historical` | PASS: all six reject with `LLM_RUNTIME_CONTEXT_INVALID` at the selected source trust or status field. |

Host runtime was Python 3.12.3. `python3.11 --version` could not run because `python3.11` is not installed. Windows PowerShell validation could not run because `pwsh` is not installed. The local OMO container was available and was used for both the focused suite and the failing schema meta-validation.

## Findings

| Severity | Finding | Evidence and required action |
| --- | --- | --- |
| P0 | None. | No P0 finding identified. |
| P1 | `context-package.schema.json` is meta-schema invalid. | In `standards/runtime/context-package.schema.json`, the third `source.allOf` conditional places `"required": ["source_kind"]` inside `if.properties`. `Draft202012Validator.check_schema()` rejects it with `SchemaError: ['source_kind'] is not of type 'object', 'boolean'`, identifying `$defs.source.allOf[2].if.properties.required`. Correct the Draft 2020-12 conditional, add a regression that calls `check_schema()` for every six-schema A2.1 contract, and rerun the full matrix. |
| P2 | None. | No P2 finding identified. |
| P3 | Python 3.11 and native Windows validation coverage are unavailable locally. | Python 3.11 and `pwsh` are absent. This is not the basis for the verdict because the host and OMO failures reproduce independently on the available Python 3.12 runtime. |

## Prior Report Closure Assessment

| Report | Closure assessment | Evidence |
| --- | --- | --- |
| 19 | Behavioral findings closed, package approval condition not closed. | Missing Project V2, superseded source, equal revision, wrong prompt/output, invalid ordering, worker and request mismatches, result revision/token/time errors, session drift, and registry drift all reject in the rerun mutation groups. The six-schema Draft contract requirement remains unfulfilled because Context Package is meta-invalid. |
| 20 | Behavioral findings closed, package approval condition not closed. | Source ownership, cardinality and ordering, logical-reference ambiguity, registry drift, result provenance, and profile/cache local invariants reject. The report's required valid Draft 2020-12 contract surface is still not satisfied. |
| 22 | Closed for the reported project-context kind-swap defect. | Both direct kind swaps reject deterministically at `/project_context/source_id`. The independent meta-schema failure is separate and prevents final approval. |
| 25 | Closed for the reported selected project-source policy defect. | All six selected-source trust and lifecycle values reject at the exact selected descriptor fields. The independent meta-schema failure is separate and prevents final approval. |

## Exclusions

No network, provider, crawl, deployment, browser, API, event, integration, workflow-state, or git-write action was performed. No A2.2 work was assessed as delivered or approved. Source resolution, source-byte and canonical hash verification, freshness, graph and release lookup, stored-record projection comparison, idempotency, cache eligibility, technical-session policy, routing, and dispatch remain explicit A2.2 or later exclusions.

## Approval Condition

Correct the invalid Context Package schema conditional and add the six-schema Draft 2020-12 meta-validation regression to the A2.1 focused gate. Then rerun the 19 focused tests, host and OMO schema meta-validation, the registry hash check, all prior mutation groups, both kind swaps, and all six selected-source trust and lifecycle probes. Until that evidence passes, the final A2.1 verdict remains `REQUEST_CHANGES`.
