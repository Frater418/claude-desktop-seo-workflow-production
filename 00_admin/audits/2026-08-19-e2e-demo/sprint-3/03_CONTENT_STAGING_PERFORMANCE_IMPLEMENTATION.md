# Sprint 3 Lane C Content, Staging and Performance Implementation

**Author:** Raphael Rechberger
**Date:** 2026-08-19
**Scope:** Tasks 3.7, 3.8 and 3.9 only.

## Delivered Contracts

- `step-4a-briefing.schema.json` and `claim-ledger.schema.json` are closed Draft 2020-12 candidate contracts.
- `step-4b-page-spec.schema.json` and `staging-evidence.schema.json` are closed Draft 2020-12 candidate contracts.
- `step-3b-adjustment.schema.json` is a closed Draft 2020-12 candidate contract that binds a released Step 3 source plan and a distinct proposed replacement artifact.
- Every contract has schema version `2.0.0`, artifact, run and project identity, a const step ID, revision, source artifact IDs, evidence IDs, decision records and `awaiting_gate` candidate status. Deployment identity is included where the artifact is deployment scoped.

## Preflight Rules

- Step 4a validates both contracts, ledger linkage, evidence and reviewer policy for YMYL claims, and the provider-gateway-only SERP boundary.
- Step 4b validates page and staging contracts, service-area address safety, equal content hashes, form consent, tracking slots, and crawl, Lighthouse, axe and visual evidence references. It does not invoke those tools.
- Step 3b rejects an adjustment that writes over the released Step 3 source plan. The original is reference only and the proposed plan must have another artifact ID.

## Prompt Migration

- `3b-performance-check.xml.md`, `4a-content-briefing-und-schema.xml.md` and `4b-landingpage-html.xml.md` now declare version `2.0.0`.
- They read Project V2, a released predecessor and their closed schema. They create only `awaiting_gate` candidates and submit only `submit_for_gate` through the Transition Service.
- They prohibit direct providers, Human Approval creation, completion, next-step start, legacy manifest mutation, crawling, deployment and direct QA tool execution.
- Each prompt defines one consolidated operator error.

## TDD Evidence

- RED command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step4a_contract tests.test_step4b_contract tests.test_step3b_contract -v`
- RED result: 3 module-import errors because `services.step4a_preflight`, `services.step4b_preflight` and `services.step3b_preflight` did not exist.
- GREEN command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step4a_contract tests.test_step4b_contract tests.test_step3b_contract -v`
- GREEN result: 12 tests passed in 0.114 seconds.

## Changed Paths

- `standards/outputs/step-4a-briefing.schema.json`
- `standards/outputs/claim-ledger.schema.json`
- `standards/outputs/step-4b-page-spec.schema.json`
- `standards/outputs/staging-evidence.schema.json`
- `standards/outputs/step-3b-adjustment.schema.json`
- `services/step4a_preflight/__init__.py`
- `services/step4a_preflight/validator.py`
- `services/step4b_preflight/__init__.py`
- `services/step4b_preflight/validator.py`
- `services/step3b_preflight/__init__.py`
- `services/step3b_preflight/validator.py`
- `prompts/4a-content-briefing-und-schema.xml.md`
- `prompts/4b-landingpage-html.xml.md`
- `prompts/3b-performance-check.xml.md`
- `tests/test_step4a_contract.py`
- `tests/test_step4b_contract.py`
- `tests/test_step3b_contract.py`
- `tests/fixtures/step4a/positive-briefing.json`
- `tests/fixtures/step4a/positive-claim-ledger.json`
- `tests/fixtures/step4a/positive-bundle.json`
- `tests/fixtures/step4a/missing-reviewer-policy-bundle.json`
- `tests/fixtures/step4b/positive-page-spec.json`
- `tests/fixtures/step4b/positive-staging-evidence.json`
- `tests/fixtures/step4b/positive-bundle.json`
- `tests/fixtures/step4b/unsafe-service-area-bundle.json`
- `tests/fixtures/step3b/positive-adjustment.json`
- `tests/fixtures/step3b/positive-bundle.json`
- `tests/fixtures/step3b/overwrite-plan-bundle.json`
- `00_admin/audits/2026-08-19-e2e-demo/sprint-3/03_CONTENT_STAGING_PERFORMANCE_IMPLEMENTATION.md`

## Diagnostics and Boundaries

- `lsp_diagnostics` was invoked for all nine changed Python files. The configured basedpyright server is not installed, so no diagnostics could be produced.
- No files outside the Lane C allowlist were changed. No network, provider, browser, crawl, deployment, git commit or full-suite command was used.
- The implementation is a closed candidate workflow. It does not create approvals, complete a step, start a successor or mutate legacy state.

## Post-Write Review

- Each changed Python module owns one preflight boundary or its public import. Test modules own their focused contract assertions.
- Untrusted bundles are schema-validated at the preflight boundary before semantic linkage checks.
- No tagged variants, escape hatches, defensive fallbacks, parameter bloat or logging changes were introduced.
- The largest changed Python module is below 250 pure lines. Focused regression tests fail when the corresponding service package or required semantic rule is removed.

## Reusable Framework Amendment

The prior Lane C report was incomplete because it did not demonstrate acceptance beyond the AHD-oriented care fixtures. This amendment is complete only after the focused genericity suite passes.

- `tests/fixtures/step4a/non-ahd-b2b-bundle.json` is an English B2B analytics-platform briefing for `project-saas-001` and `deployment-canada-001`. It uses a factual product claim, an editorial reviewer policy and gateway-bound SERP evidence instead of a care-service YMYL claim.
- `tests/fixtures/step4b/non-ahd-product-bundle.json` is an English analytics-product page for the same Canadian deployment. It uses a product demonstration form, privacy-consent policy, product analytics slot, Ontario service area, no physical address claim and the required existing staging evidence references.
- `tests/fixtures/step3b/non-ahd-product-bundle.json` is an analytics-product roadmap adjustment for `project-saas-001`. It proves that a non-care Step 3 plan remains immutable while a distinct proposed revision is accepted.
- Focused tests invoke the actual preflights for all three contrasting fixtures. They retain the data-driven YMYL and service-area negative cases without making any market, language, service, location, design, tone, conversion, page, provider or evidence assertion specific to AHD.
- Prompt prose assertions were removed because the prompt text has no machine consumer. The contract tests now verify only schema and preflight behavior.

### Amendment Test Evidence

- Initial genericity run: 12 tests, 1 failure. The failure was `ERROR_STEP4B_PAGE_INVALID` because the non-AHD page fixture supplied an undeclared decision-record field. This confirmed the closed generic contract rather than an AHD-specific condition.
- Corrected genericity run: `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step4a_contract tests.test_step4b_contract tests.test_step3b_contract -v`
- Corrected genericity result: 12 tests passed in 0.158 seconds.

### Amendment Self Review

- Single responsibility: each changed test module owns one Step contract family, and each new fixture owns one contrasting candidate bundle.
- Boundary purity: no production boundary changed. Fixtures remain parsed by existing closed JSON-schema preflights.
- Variants and escape hatches: no new variants, `Any`, casts, suppressions or broad exception handling were added.
- Defensive layers and helper bloat: no new production helpers or defensive branches were added.
- Test lock: each added test would fail if its corresponding preflight stopped accepting the contrasting generic candidate.
- Parameter, destructive-action, negative-naming and logging review: no affected production code was added or changed.
