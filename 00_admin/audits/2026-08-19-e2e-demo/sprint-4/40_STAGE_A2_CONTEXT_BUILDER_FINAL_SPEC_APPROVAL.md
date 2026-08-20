# Sprint 4 Stage A2 Package A2.2 Final Specification Approval

Date: 2026-08-20
Reviewer: Reviewer A, independent fresh local audit
Scope: Stage A2 Package A2.2 deterministic Context Builder and session policy only.

## Verdict

APPROVED

The Report 37 and Report 38 defects are closed in the live pure injected-data boundary. The observed implementation satisfies DEC-0019's fail-fast reproducible Context Package requirement without adding Stage B behavior.

## Evidence Read

Read before this decision: `AGENTS.md`; DEC-0019 in `00_admin/DECISIONS.md`; controller plan `17_STAGE_A2_IMPLEMENTATION_PLAN.md`; Reports 36, 37, 38, and 39; complete A2.1 implementation at `services/runtime_contracts/__init__.py` and `services/runtime_contracts/llm_records.py`; complete A2.2 implementation at `services/context_builder/__init__.py`, `builder.py`, `validator.py`, and `session_policy.py`; `services/operator_routing/router.py`; `tests/contracts/test_llm_runtime_contracts.py`; `tests/test_context_builder.py`; and `tests/test_operator_error_routing.py`.

DEC-0019 requires immutable exact source, revision, hash, prompt, and output bindings that stop stale, wrong-hash, and cross-identity inputs before an LLM call. Plan 17 expressly excludes Stage B from A2 and requires pure injected-data modules, deterministic canonicalization, source ordering, semantic validation, session policy, and one canonical route for each A2.2 error code.

## Plan 17 A2.2 Requirement Verification

| Requirement | Observed evidence | Result |
| --- | --- | --- |
| Required A2.2 module and focused-test surface | `services/context_builder/__init__.py`, `builder.py`, `validator.py`, `session_policy.py`, and `tests/test_context_builder.py` exist and expose the specified builder, validation, request/result, and policy public APIs. | Pass |
| Pure boundary, plan lines 240-250 | The four Context Builder modules import only standard-library modules plus the injected A2.1 validator. No filesystem, environment, clock, socket, provider, dispatch, persistence, or workflow-state mutation call is present. | Pass |
| Canonicalization, plan lines 252-265 | `builder.py` uses JSON-only validation, ASCII, sorted keys, compact separators, `allow_nan=False`, UTF-8, lower-case SHA-256, deterministic rank/tie-break sorting, contiguous `include_order`, and excludes only `package_sha256` from its package hash. `test_step_zero_build_is_canonical_and_does_not_mutate_inputs` passed. | Pass |
| Ordered source model, plan lines 267-277 | `SOURCE_RANKS` and `TRUST_RANKS` in `builder.py` order prompt, registry contracts, project, predecessors, revision sources, gates, evidence, and permitted historical comparison data. Builder caller order is ignored. | Pass |
| Semantic validation, plan lines 279-297 | `validator.py` runs A2.1 first, then checks hashes, exact source/current-record fields, RFC3339 freshness, prompt/output bytes, graph/release predecessor lineage, revision binding, trust policy, and package hashes without input mutation. | Pass |
| Session policy, plan lines 299-314 | `session_policy.py` returns only `fresh_required`, `reuse_permitted`, `recover_fresh`, or `denied`; fresh modes require fresh sessions; exact available retry/resume cache reuse is bounded by every projected field; lost cache recovers fresh; drift denies. | Pass |
| Error routing, plan lines 316-334 | Direct local route probe found exactly one mapping for each of all 13 required codes: `ERROR_CONTEXT_SCHEMA_INVALID`, `ERROR_CONTEXT_IDENTITY_MISMATCH`, `ERROR_CONTEXT_SOURCE_INVALID`, `ERROR_CONTEXT_PROMPT_BINDING_INVALID`, `ERROR_CONTEXT_OUTPUT_CONTRACT_INVALID`, `ERROR_CONTEXT_PREDECESSOR_INVALID`, `ERROR_CONTEXT_REVISION_BINDING_INVALID`, `ERROR_CONTEXT_TRUST_POLICY_INVALID`, `ERROR_CONTEXT_PACKAGE_HASH_MISMATCH`, `ERROR_LLM_REQUEST_INVALID`, `ERROR_LLM_REQUEST_IDEMPOTENCY_CONFLICT`, `ERROR_LLM_RESULT_INVALID`, and `ERROR_TECHNICAL_SESSION_POLICY_DENIED`. | Pass |
| Behavioral TDD gate, plan lines 336-369 | The focused suite exercised Step 0, Step 1, Step 1c multi-output, revision, canonical parity, source/package hashes, prompt/output drift, predecessor and revision bindings, cache policy, request idempotency, all result statuses, and routing parity. | Pass |
| A2.1 compatibility | `RuntimeContractValidator` validates Draft 2020-12 contracts before A2.2 semantic checks. The A2.1 test surface binds all nine workflow steps and exact prompt/output bytes. | Pass |

## Independent Execution

Executed locally without network, provider, crawl, deploy, git write, or environment modification:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_context_builder tests.test_operator_error_routing -v
Ran 23 tests in 4.737s
OK
```

The 23 passing tests include the two focused modules named by the package. `test_context_builder_codes_have_exactly_one_canonical_route` and the direct route probe independently verify the 13-route closure.

## Report 37 and 38 Closure Probes

All probes used in-memory copies and public Context Builder functions only.

| Probe | Observed local result | Closure |
| --- | --- | --- |
| Source `valid_until` before, equal to, and after evaluation instant using `+01:00` offsets | `00:30+01:00`: invalid; `01:00+01:00`: invalid; `02:00+01:00`: valid at `00:00Z`. | Report 38 freshness false green closed. |
| Available cache `expires_at` before, equal to, and after current instant using `+01:00` offsets | `00:30+01:00`: `recover_fresh`; `01:00+01:00`: `recover_fresh`; `02:00+01:00`: `reuse_permitted`. | Report 38 expiry false green closed. |
| Unknown cache state with otherwise exact bound fields | `denied`. | Report 37 unknown-state false green closed. |
| Project V2 current record lifecycle | `active` and `rejected`: `ERROR_CONTEXT_IDENTITY_MISMATCH`; `superseded` and `historical`: identity mismatch plus source-invalid. | Report 37 current lifecycle drift closed. |
| Project V2 current record source ID changed | `ERROR_CONTEXT_IDENTITY_MISMATCH`. | Report 38 current-record identity gap closed. |
| Predecessor Release Record wrong `run_id` | `ERROR_CONTEXT_PREDECESSOR_INVALID`. | Report 38 release-lineage gap closed. |
| Forged all-zero result hash for `succeeded`, `failed`, and `cancelled` result records | Each returned `ERROR_LLM_RESULT_INVALID`. | Report 38 result integrity gap closed. |
| Malformed descriptor revisions: string, bool, float, missing, and zero | Each raised immutable `ContextBuildError` with `ERROR_CONTEXT_SCHEMA_INVALID` at `/sources/0/revision`. | Report 38 structured fail-fast diagnostic gap closed. |

## Findings

### P0

None.

### P1

None.

### P2

None.

### P3

None.

## Stage B Boundary

No Stage B work was performed, observed, initiated, or required by this approval. The approved A2.2 surface contains no API, persistence, database, Event Store, event emission, provider dispatch, adapter, technical-session storage, UI, Notion, n8n, simulator, deployment, or workflow-state authority behavior.

VERDICT: APPROVED
