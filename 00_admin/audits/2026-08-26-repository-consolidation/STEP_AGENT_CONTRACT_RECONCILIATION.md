# Step Agent, Worker Profile and Tool Policy Reconciliation

**Author:** Raphael Rechberger
**Date:** 2026-08-26
**Scope:** All 8 active Step agents, worker profiles and agent tool policies

## Result

The production loader accepted the complete registry and returned canonical registry SHA-256 `51abe7de0fdf44a8b4f459999fcb7b754751de35e1f08a5e63cbf0158e7ecbe4`.

For every Step, the loader verified:

- the registry, worker profile and tool policy against their JSON schemas
- the canonical self-hash of the registry, every profile and every policy
- exact Step ID, agent contract, profile and policy identity bindings
- one active official prompt and all output contracts
- required operations as a subset of allowed operations
- unique operation IDs and valid confirmation scopes
- valid bounded-delegation profile references
- `fail_closed` as inference fallback and output failure mode

## Active matrix

| Step | Agent contract | Worker profile | Reasoning | Tool policy | Required and allowed operations | Max calls | Result |
|---|---|---|---|---|---|---|---|
| `0` | `heartweb-step-0-agent@1.3.0` | `worker-profile-step-0-agent@1.3.0` | low | `tool-policy-step-0-agent@1.2.0` | `prepare_kickoff_preflight` | 1 | PASS |
| `1` | `heartweb-step-1-agent@1.2.0` | `worker-profile-step-1-agent@1.3.0` | medium | `tool-policy-step-1-agent@1.2.0` | `run_screaming_frog_crawl`, `request_serp_intent_evidence` | 1, 2 | PASS |
| `1b` | `heartweb-step-1b-agent@1.3.0` | `worker-profile-step-1b-agent@1.4.0` | high | `tool-policy-step-1b-agent@1.4.0` | `request_serp_intent_evidence` | 2 | PASS |
| `1c` | `heartweb-step-1c-agent@1.1.0` | `worker-profile-step-1c-agent@1.2.0` | medium | `tool-policy-step-1c-agent@1.1.0` | `read_design_evidence` | 4 | PASS |
| `2` | `heartweb-step-2-agent@1.3.0` | `worker-profile-step-2-agent@1.4.0` | low | `tool-policy-step-2-agent@1.4.0` | `request_keyword_metrics` | 2 | PASS |
| `3` | `heartweb-step-3-agent@1.1.0` | `worker-profile-step-3-agent@1.2.0` | medium | `tool-policy-step-3-agent@1.1.0` | `solve_capacity_matrix` | 2 | PASS |
| `4a` | `heartweb-step-4a-agent@1.3.0` | `worker-profile-step-4a-agent@1.4.0` | high | `tool-policy-step-4a-agent@1.4.0` | `request_serp_briefing_evidence`, `validate_jsonld` | 2, 3 | PASS |
| `4b` | `heartweb-step-4b-agent@1.2.0` | `worker-profile-step-4b-agent@1.3.0` | high | `tool-policy-step-4b-agent@1.2.0` | `validate_jsonld`, `run_staging_validation` | 3, 1 | PASS |

## Semantic checks

- Every required operation appears in its matching active prompt.
- Prompts prohibit direct provider, browser, shell, filesystem, approval, release and transition side effects outside the registered Heartweb operations.
- Step 1 binds one customer crawl and one or two deployment-bound SERP requests.
- Step 2 binds provider keyword metrics and forbids estimated missing metrics.
- Step 3 copies the deterministic capacity solver output rather than recalculating machine fields.
- Steps 4a and 4b require JSON-LD validation; Step 4b also requires one staging validation.
- No policy permits a provider credential or raw authorization value to enter an agent prompt.

## Verification

Commands:

```text
python -m unittest tests.contracts.test_llm_runtime_contracts.LlmRuntimeContractTests.test_official_registry_matches_current_prompts_outputs_and_workflow_steps
python -m unittest tests.test_hermes_runtime_provider tests.test_agent_tool_call_scope
```

Results:

- official prompt and output binding: 1 of 1 PASS
- Hermes runtime and tool-call scope: 14 of 14 PASS

The direct Runtime closure initially exposed stale test assumptions about provisioned workspace layout, active Step-0 source paths, deployment binding, atomic output sets and the typed Step-agent validation error. The test fixture and assertions were corrected at the public runtime seam. Production fail-closed logic was not weakened.
