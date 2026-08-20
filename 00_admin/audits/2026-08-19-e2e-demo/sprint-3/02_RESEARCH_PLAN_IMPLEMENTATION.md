# Sprint 3 Lane B: Research and Plan Implementation

## Scope

Implemented Tasks 3.4 through 3.6 within the Lane B allowlist only.

## Delivered Contracts

- `standards/providers/research-request.schema.json`
- `standards/providers/research-response.schema.json`
- `standards/outputs/step-2-keyword-evidence.schema.json`
- `standards/outputs/step-3-plan.schema.json`

All four contracts declare JSON Schema Draft 2020-12, use `additionalProperties: false`, and require schema version, artifact or request identity, run, project, deployment, revision, source artifacts, evidence, decisions and candidate status. The provider contracts bind geo, language, device, idempotency, cost and SHA-256 hashes. DataForSEO and conditional AgentSEO are represented as contracts only.

## Services

- `services/provider_gateway/core.py` validates completed provider evidence without network behavior. It consolidates location and metadata mismatch, missing raw response, quota, timeout, unknown cost and missing job ID into one `ERROR_PROVIDER_GATEWAY` operator error.
- `services/step2_preflight/validator.py` requires at least 25 verified raw-evidence rows for every approved pillar and emits one `ERROR_STEP2_PREFLIGHT` error.
- `services/step3_preflight/validator.py` requires a deterministic 17-week plan, capacity up to 15 hours, mandatory work, backlog, both link graphs and input/output hashes. It emits one `ERROR_STEP3_PREFLIGHT` error.

`services/agentseo_gateway/core.py` was not changed. The new provider-neutral gateway owns the shared boundary, so changing the legacy AgentSEO adapter was unnecessary.

## Prompt Migration

`prompts/2-cluster-recherche.xml.md` and `prompts/3-120-tage-plan.xml.md` now declare version `2.0.0`. Both read Project V2, a released predecessor and the closed output schema. They prohibit direct provider calls, Human Approval creation, completion, next-step startup and legacy-manifest mutation. Their only allowed state submission is `awaiting_gate` through `transition_service`.

## TDD Evidence

RED command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_step2_contract tests.test_step3_contract
```

RED result: 3 import errors because the three Lane B service boundaries did not yet exist.

GREEN command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_step2_contract tests.test_step3_contract
```

GREEN result: `Ran 6 tests in 0.000s`, `OK`.

## Genericity Amendment

The prior Lane B report was incomplete because it did not prove reusable, non-AHD positive behavior. This amendment closes that gap with three contrasting fixtures and focused schema plus service tests:

- `tests/fixtures/provider_gateway/non-ahd-agentseo-fr-ca.json`: French Canadian solar research using mobile AgentSEO metadata. It contrasts with the original German care-oriented test values while proving that provider, language, deployment and geo flow from fixture data through the provider gateway.
- `tests/fixtures/step2/non-ahd-solar-fr-ca.json`: French Canadian solar keyword evidence with a different pillar and 25 verified rows. It validates both the closed Step 2 schema and the row-count preflight.
- `tests/fixtures/step3/non-ahd-solar-fr-ca.json`: French Canadian solar plan with a different deployment, item namespace, pillar and graph identifiers. It validates both the closed Step 3 schema and the 17-week preflight.

The focused tests no longer hardcode a German market, `de` language, care pillar, deployment, provider result, capacity, or link target. They load data from the contrasting fixtures, validate both provider schemas and both output schemas, and pass the same data through the gateway and preflights. The schemas, prompts and validators remain data-driven: none contain AHD market, language, deployment, geo, pillar, link or claim literals. DataForSEO remains the provider-neutral primary policy and AgentSEO remains conditional through `provider_gateway`.

Amendment RED result: the new fixture-backed tests failed with nine expected `FileNotFoundError` results while the contrasting fixtures were absent.

Amendment GREEN command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_provider_gateway tests.test_step2_contract tests.test_step3_contract
```

Amendment GREEN result: `Ran 9 tests in 0.055s`, `OK`.

## Diagnostics and Constraints

LSP diagnostics were invoked for every changed Python file. `basedpyright` is not installed and was previously declined, so no diagnostics result was available. No network, provider invocation, browser, crawl, deployment, full suite, review or commit was run.

The tests use Given/When/Then BDD comments. Module and public API docstrings document service boundaries and the single operator-error behavior.

## Changed Paths

- `standards/providers/research-request.schema.json`
- `standards/providers/research-response.schema.json`
- `standards/outputs/step-2-keyword-evidence.schema.json`
- `standards/outputs/step-3-plan.schema.json`
- `services/provider_gateway/__init__.py`
- `services/provider_gateway/core.py`
- `services/step2_preflight/__init__.py`
- `services/step2_preflight/validator.py`
- `services/step3_preflight/__init__.py`
- `services/step3_preflight/validator.py`
- `prompts/2-cluster-recherche.xml.md`
- `prompts/3-120-tage-plan.xml.md`
- `tests/test_provider_gateway.py`
- `tests/test_step2_contract.py`
- `tests/test_step3_contract.py`
- `tests/fixtures/step2/approved-pillar.json`
- `tests/fixtures/step3/deterministic-plan.json`
- `tests/fixtures/provider_gateway/non-ahd-agentseo-fr-ca.json`
- `tests/fixtures/step2/non-ahd-solar-fr-ca.json`
- `tests/fixtures/step3/non-ahd-solar-fr-ca.json`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-3/02_RESEARCH_PLAN_IMPLEMENTATION.md`
