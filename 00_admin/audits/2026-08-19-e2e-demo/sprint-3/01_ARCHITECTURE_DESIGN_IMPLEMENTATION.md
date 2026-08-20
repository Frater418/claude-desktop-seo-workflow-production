# Sprint 3 Lane A: Architecture and Design Implementation

## Scope

Implemented Tasks 3.1 through 3.3 within the assigned allowlist only.

Changed paths:

- `standards/outputs/step-1b-architecture.schema.json`
- `standards/outputs/step-1c-design-system.schema.json`
- `standards/outputs/step-1c-template.schema.json`
- `services/step1b_preflight/__init__.py`
- `services/step1b_preflight/validator.py`
- `services/step1b_preflight/render.py`
- `services/step1c_preflight/__init__.py`
- `services/step1c_preflight/validator.py`
- `prompts/1b-seitenarchitektur.xml.md`
- `prompts/1c-pillar-template.xml.md`
- `tests/test_step1b_contract.py`
- `tests/test_step1c_contract.py`
- `tests/fixtures/step1b/positive-architecture.json`
- `tests/fixtures/step1b/non-ahd-outdoor-architecture.json`
- `tests/fixtures/step1c/positive-design-system.json`
- `tests/fixtures/step1c/positive-template.json`
- `tests/fixtures/step1c/non-ahd-outdoor-design-system.json`
- `tests/fixtures/step1c/non-ahd-outdoor-template.json`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-3/01_ARCHITECTURE_DESIGN_IMPLEMENTATION.md`

## Delivered Contracts and Services

All three new output contracts declare JSON Schema Draft 2020-12 and reject undeclared properties. They require schema_version, artifact_id, run_id, project_id, deployment_id, const step_id, revision, source_artifact_ids, evidence_ids, decision_records, and candidate status.

Step 1B preflight validates exact approved-content decision coverage, permitted decision values, URL and canonical consistency, active URL conflicts, orphan link targets, vertical cluster coverage, and horizontal links for every pillar when multiple pillars exist. Its Markdown and HTML renderers consume the same canonical architecture JSON tree and sort their source data deterministically.

Step 1C preflight validates design tokens, template family, architecture and design-system lineage, accessibility, JSON-LD references, and physical-location versus service-area claims. A service-area template is rejected when it includes physical_address, nap, or gbp_claim.

Both prompts now declare version 2.0.0, read Project V2, the released predecessor, and the closed schemas. They prohibit approval creation, completed status, next-step starts, legacy-manifest mutation, provider calls, and external submission. The only stated submission is the Transition Service submit_for_gate command with awaiting_gate. Both use the consolidated `ERROR_STEP1B_1C_OPERATOR_ACTION_REQUIRED` operator error.

## TDD Evidence

RED command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step1b_contract tests.test_step1c_contract
```

Result: 2 import errors, `ModuleNotFoundError` for `services.step1b_preflight` and `services.step1c_preflight`. This demonstrated the tests failed before implementation for the intended missing-service reason. A second focused RED test then demonstrated missing horizontal-pillar coverage before that rule was added.

GREEN command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v tests.test_step1b_contract tests.test_step1c_contract
```

Result: 11 tests passed in 0.158 seconds.

## Reusable-Framework Amendment

The prior Lane A report was incomplete because it did not prove genericity with contrasting non-AHD positive fixtures. This amendment passed only after the focused verification recorded above.

The contrasting architecture fixture is `tests/fixtures/step1b/non-ahd-outdoor-architecture.json`. It models an outdoor retail product site with two primary pillars, a product-safety cluster, a different domain, and both vertical and horizontal navigation links. It contrasts with an AHD service workflow without adding any market, language, pillar, navigation, or URL assertion to schemas, prompts, validators, renderers, or tests.

The contrasting design fixture is `tests/fixtures/step1c/non-ahd-outdoor-design-system.json`. Its tokens are declared only with `evidence-outdoor-screenshot-0001` and `evidence-outdoor-brand-0001`. The focused evidence test verifies that its decision and accessibility evidence reference exactly the fixture project evidence set.

The contrasting template fixture is `tests/fixtures/step1c/non-ahd-outdoor-template.json`. It models a physical retail showroom with physical-location evidence, address, NAP, and LocalBusiness JSON-LD. This contrasts with the service-area fixture while proving the same generic location-safety contract accepts supported physical-location claims.

The amended tests derive approved content IDs and renderer assertions from fixture data. No AHD-specific market, language, pillar, navigation, URL, visual, location, claim, or template assertion is hardcoded in Lane A schemas, prompts, validators, renderers, or tests.

## Verification and Constraints

- Focused tests cover successful candidates, missing architecture decisions, URL conflicts, orphan links, deterministic views, service-area address rejection, and required accessibility and JSON-LD fields.
- `lsp_diagnostics` was requested for every changed Python file. Basedpyright is not installed and was previously declined, so no diagnostics result was available.
- No full suite, provider, network, browser, crawl, deployment, review, commit, registry, runtime, quality, output-path, state, plan, AHD, or shared-service modification was performed.
- No created or edited text uses an em dash or en dash.

## Architectural Review

- Single responsibility: Step 1B owns architecture validation and derived views. Step 1C owns design and template validation.
- Boundary purity: JSON Schema performs artifact-shape parsing before semantic preflight rules run.
- Variant discrimination: no tagged-union discrimination was introduced.
- Escape hatches and defensive layers: none introduced.
- Tests: each new behavior is covered by focused red-to-green tests.
- Parameter bloat, redundant verification, negative names, and logging changes: none introduced.
