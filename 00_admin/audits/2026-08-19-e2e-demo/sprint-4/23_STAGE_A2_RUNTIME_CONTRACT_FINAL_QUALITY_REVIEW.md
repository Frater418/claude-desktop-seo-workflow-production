# Sprint 4 Stage A2 Package A2.1 Final Quality Review

Date: 2026-08-20
Reviewer: Independent read-only final quality gate
Scope: Package A2.1 runtime contracts and official registries only, after report 21.

## Verdict

APPROVED

The report 20 structural false greens are closed by the six closed schemas and the schema-first, injected `RuntimeContractValidator`. The validator rejects local record and registry invariants before it returns a valid record. This approval does not approve A2.2 work.

## Reviewed Facts

- Read `AGENTS.md`, DEC-0019, plan 17, and reports 15 through 21 before this decision.
- Inspected all six A2.1 schemas, the registry schema and live registry, all 11 A2.1 fixtures, both A2.1 test modules, and every source file in `services/runtime_contracts/`.
- The reviewed runtime surface is additive. No provider, API, event, simulator, UI, routing, workflow-state, prompt, output-contract, or external lookup implementation was introduced by this package.
- The live registry contains exactly the nine workflow steps `0`, `1`, `1b`, `1c`, `2`, `3`, `3b`, `4a`, and `4b`, with 12 ordered output-contract bindings. Step 0 metadata is `1.5.0`; all other prompt metadata is `2.0.0`.

## Validation Evidence

```sh
python -m unittest tests/contracts/test_llm_runtime_contracts.py tests/test_llm_runtime_invariants.py -v
# Ran 16 tests in 0.375s
# OK

python -c "... Draft202012Validator.check_schema(...) for the six A2.1 schemas ..."
# META_VALIDATION_PASS 6 schemas

python -c "... verify live prompt metadata, prompt SHA-256, and output-contract SHA-256 ..."
# PROMPT_OUTPUT_HASH_PASS 9 prompts 12 output-bindings
```

The 11 shipped fixtures are ASCII and client-neutral. The focused tests validate all positive records through both JSON Schema and the production `RuntimeContractValidator`.

## Adversarial Evidence

All probes used in-memory fixture or registry copies and the production validator. No files, providers, network resources, or external systems were changed or called.

| False-green class and adjacent variant | Result |
| --- | --- |
| Source tenant ownership, duplicate source identity/cardinality, duplicate and noncontiguous order | Rejected by schema or `LLM_RUNTIME_CONTEXT_INVALID`. |
| Project-context source binding | Rejected by `LLM_RUNTIME_CONTEXT_INVALID`. |
| Double separator, trailing separator, and encoded traversal logical references | Rejected by `LLM_RUNTIME_SCHEMA_INVALID`. |
| Duplicate registry step/parity and cross-step prompt ID | Rejected by `LLM_RUNTIME_REGISTRY_INVALID`. |
| Prompt hash drift and output-contract hash drift | Rejected by `LLM_RUNTIME_CONTEXT_INVALID`. |
| Logical-session source-kind and binding-mode mismatch | Rejected by `LLM_RUNTIME_SESSION_INVALID`. |
| Default model outside the allowlist | Rejected by `LLM_RUNTIME_WORKER_INVALID`. |
| Request input hash mismatch and cache-hint provider mismatch | Rejected by `LLM_RUNTIME_REQUEST_INVALID`. |
| Result token arithmetic, output revision, and reverse timestamp | Rejected by `LLM_RUNTIME_RESULT_INVALID`. |
| Unknown schema injection and missing source tenant ID | Rejected by `LLM_RUNTIME_SCHEMA_INVALID`. |
| Immutable structured exception record | Assignment raised `FrozenInstanceError`. |
| No I/O or hidden fallback in the production validator | Five valid record kinds remained valid after guards blocked `open`, `getenv`, and socket construction: `PURE_VALIDATOR_NO_IO_PASS 5 records`. |

The validator performs Draft 2020-12 validation first. Schema failures return `LLM_RUNTIME_SCHEMA_INVALID` without a semantic fallback. Schema-valid records then receive deterministic, ordered immutable `ValidationError` values. Repeating every rejected mutation produced the same error tuple.

## Findings

### P0

None.

### P1

None.

### P2

None.

### P3

None.

## Residual Risks And Deliberate A2.2 Boundary

- A2.1 does not resolve logical references, load source bytes, verify canonical package or source-manifest hashes, or inspect repository freshness. These require the controlled repository adapter and canonical builder assigned to A2.2.
- A2.1 does not compare a request or result to stored package, profile, release, graph, idempotency, or cache records. A2.2 owns those cross-record checks and technical-session policy decisions.
- This audit did not require external lookup, canonical package construction, provider access, crawl, deployment, or any other A2.2 or later capability.
