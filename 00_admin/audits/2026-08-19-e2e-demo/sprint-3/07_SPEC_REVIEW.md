# Sprint 3 Specification Review

Date: 2026-08-19

Scope: Fresh read-only review of Tasks 3.1 through 3.10 against the current schemas, prompts, validators, renderers, fixtures, tests, output contract, and worktree diff. Prior implementation reports were used only to locate task scope, not as evidence.

## Verdict

REQUEST_CHANGES

## Findings

### P0

No finding verified.

### P1

1. **Canonical Step 2 and Step 3 candidates are not the objects their preflights and renderers validate.** The closed Step 2 schema requires a V2 envelope with `pillars`, while its validator reads a separate `approved_pillar_ids` plus `rows` projection and its renderer directly indexes `rows`. [Step 2 schema:6-8](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-2-keyword-evidence.schema.json:6) [Step 2 validator:18-30](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:18) [Step 2 renderer:16-20](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/render.py:16) The closed Step 3 schema requires the V2 lifecycle fields and solver binding, but its validator only checks operational plan fields and hash lengths. [Step 3 schema:3-5](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-3-plan.schema.json:3) [Step 3 validator:17-47](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:17) This violates the canonical-candidate and fail-fast boundary promised by the prompts. [Step 2 prompt:23-29](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/2-cluster-recherche.xml.md:23) [Step 3 prompt:19-24](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3-120-tage-plan.xml.md:19)

2. **Released-predecessor and gate eligibility are declared but not enforced by the Step 1C, Step 2, Step 3, Step 4A, or Step 4B preflights.** Each prompt requires a released predecessor before preflight and an `awaiting_gate` submission. [Step 1C prompt:18-32](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1c-pillar-template.xml.md:18) [Step 4A prompt:18-35](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4a-content-briefing-und-schema.xml.md:18) [Step 4B prompt:18-29](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4b-landingpage-html.xml.md:18) However, the affected validators take only local artifacts and never validate predecessor artifact identity, release status, revision, hash, or gate record. [Step 1C validator:61-68](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/validator.py:61) [Step 2 validator:18-41](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/validator.py:18) [Step 3 validator:17-47](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/validator.py:17) [Step 4A validator:18-32](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:18) [Step 4B validator:18-34](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:18) The later transition service has independent gate coverage, but a direct preflight or renderer caller can receive a false success first.

3. **The Step 1C renderer discards every valid template after the first one.** The prompt requires one canonical template per pillar and a deterministic HTML derivation. [Step 1C prompt:27-31](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/1c-pillar-template.xml.md:27) `render_step1c` validates the full list, then selects only `templates[0]` and returns one `html` value. [Step 1C renderer:14-18](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:14) [Step 1C renderer:21-51](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:21) A two-template read-only driver rendered no content from the second valid template.

4. **Step 3B does not enforce the promised new revision and new hash for the proposed plan.** The prompt requires a proposed revision with a new artifact ID, revision, and hash. [Step 3B prompt:18-21](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3b-performance-check.xml.md:18) The schema and validator require a distinct artifact ID only, allowing the source revision and content hash to be reused. [Step 3B schema:3-5](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-3b-adjustment.schema.json:3) [Step 3B validator:14-18](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3b_preflight/validator.py:14) This weakens Step 3 plan immutability and the auditability of a claimed replacement.

### P2

1. **Service-area safety is not bound to Project V2 or evidence.** The Step 4B schema allows arbitrary non-empty area names, and the preflight rejects only physical-address claims for `service_area`. [Step 4B schema:11-13](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-4b-page-spec.schema.json:11) [Step 4B validator:24-33](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:24) The prompt makes the physical-address rule conditional on Project V2 evidence, but the preflight never receives or consults Project V2. [Step 4B prompt:19-23](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/4b-landingpage-html.xml.md:19) Unsupported service areas can pass, while an evidenced physical location is still rejected when mode remains `service_area`.

2. **Declared output paths are not enforced by the derived-view writers.** Step 2 and Step 3 declare `outputs/2-cluster-themen-agentseo.csv` and `outputs/3-plan.md`. [Step 2 prompt:28-29](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/2-cluster-recherche.xml.md:28) [Step 3 prompt:23-24](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/prompts/3-120-tage-plan.xml.md:23) Their writers accept any output path and create its parent. [Step 2 renderer:33-38](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step2_preflight/render.py:33) [Step 3 renderer:39-44](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step3_preflight/render.py:39) Step 1C likewise writes generic `design-system.css` and `template.html` beneath any caller-supplied directory, conflicting with the per-pillar path contract. [Output contract:50-56](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/dateinamen-und-output-vertrag.md:50) [Step 1C renderer:54-61](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:54)

### P3

No finding verified.

## Task-by-Task Verification Matrix

| Task | Current artifacts inspected | Result | Evidence |
|---|---|---|---|
| 3.1 | Step 1B schema, prompt, validator, renderer | Pass | Closed V2 envelope and decision/link validation are present. [Schema:6-16](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-1b-architecture.schema.json:6) [Validator:79-86](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1b_preflight/validator.py:79) |
| 3.2 | Step 1C design-system schema, prompt, validator, renderer | Request changes | Service-area physical-claim guard exists, but predecessor validation and multi-template rendering are incomplete. [Validator:31-42](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/validator.py:31) [Renderer:38-51](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step1c_preflight/render.py:38) |
| 3.3 | Step 1C template schema and derived output contract | Request changes | The template contract is closed and evidence-bound, but the renderer produces one generic file rather than all per-pillar views. [Template schema:7-15](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/outputs/step-1c-template.schema.json:7) [Output contract:51](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/dateinamen-und-output-vertrag.md:51) |
| 3.4 | Provider-neutral request/response schemas and gateway | Pass | Both provider values are contractually supported and the gateway is contract-only. [Request schema:7-18](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/standards/providers/research-request.schema.json:7) [Gateway:60-73](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/provider_gateway/core.py:60) |
| 3.5 | Step 2 schema, prompt, preflight, CSV renderer | Request changes | Canonical V2 candidate and preflight/renderer inputs do not align. |
| 3.6 | Step 3 schema, prompt, preflight, Markdown renderer | Request changes | Canonical lifecycle and released-predecessor assertions are not preflight-enforced. |
| 3.7 | Step 4A briefing and claim-ledger schema, prompt, preflight | Request changes | Provider-gateway and YMYL checks work, but released Step 3 predecessor binding is not enforced. [YMYL and provider checks:25-31](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4a_preflight/validator.py:25) |
| 3.8 | Step 4B page/staging schemas, prompt, preflight, renderer | Request changes | Address-claim protection and staging checks work, but predecessor and supported service-area binding are absent. [Validator:24-33](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/services/step4b_preflight/validator.py:24) |
| 3.9 | Step 3B adjustment schema, prompt, preflight, renderer | Request changes | Source and proposal IDs must differ, but new revision and hash are not enforced. |
| 3.10 | V2 meta-contract, eight V2 prompts, derived-view integration | Request changes | All eleven output schemas share the common V2 envelope, but renderer integration and path enforcement have the P1/P2 gaps above. [Meta-contract test:11-35](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_output_contracts_v2.py:11) [Meta-contract test:61-100](/workspace/hermes-active/Heartweb-Claude-Desktop-SEO-Workflow/tests/contracts/test_output_contracts_v2.py:61) |

## Evidence Commands and Results

1. `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step1_contract_v2 tests.test_step1b_contract tests.test_step1c_contract tests.test_step2_contract tests.test_step3_contract tests.test_step3b_contract tests.test_step4a_contract tests.test_step4b_contract tests.contracts.test_output_contracts_v2 -v`
   Result: 47 tests passed.

2. `PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_step1c_renderer tests.test_step2_renderer tests.test_step3_renderer tests.test_step3b_renderer tests.test_step4a_renderer tests.test_step4b_renderer -v`
   Result: 7 tests passed.

3. `PYTHONDONTWRITEBYTECODE=1 python tests/run_full_suite.py`
   Result: acceptance 7/7, root discovery 143, contract discovery 37, total 187 passed.

4. Read-only Python driver using current fixtures and in-memory mutations.
   Result: canonical Step 2 candidate raised `KeyError: 'rows'`; Step 3 rendered with `candidate_status` changed to `completed`; a valid second Step 1C template was absent from rendered HTML.

5. `lsp_diagnostics services`
   Result: unavailable because `basedpyright` is not installed and installation was previously declined.

6. `git diff --check`
   Result: reported pre-existing trailing whitespace in unrelated tracked files. No Sprint 3 source was changed by this review.

## Residual Risks

1. The full suite proves its asserted cases but does not cover canonical Step 2 rendering, invalid Step 3 lifecycle metadata, a multi-template Step 1C render, predecessor release rejection in the affected preflights, or reused Step 3B revision/hash.

2. The non-AHD fixtures and focused tests demonstrate data-driven behavior for outdoor retail, solar, B2B analytics, and product cases. No AHD-specific hardcoding was verified in the inspected Sprint 3 schemas, prompts, validators, renderers, or relevant tests.

3. Provider neutrality, YMYL evidence plus reviewer-policy checks, and physical-address rejection for service-area pages were verified, subject to the unsupported-service-area gap above.

REQUEST_CHANGES
